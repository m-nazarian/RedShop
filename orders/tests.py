from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from account.models import Address, ShopUser
from coupons.models import Coupon
from shop.models import Brand, Category, Product

from .models import Order, Transaction
from .services import OrderLifecycleService


class CheckoutSecurityTests(TestCase):
    def setUp(self):
        self.user = ShopUser.objects.create_user(
            phone="09120000001",
            password="StrongPass123!",
            first_name="علی",
            last_name="آزمایشی",
        )
        self.other_user = ShopUser.objects.create_user(
            phone="09120000002",
            password="StrongPass123!",
            first_name="رضا",
            last_name="دیگر",
        )
        self.address = Address.objects.create(
            user=self.user,
            first_name="علی",
            last_name="آزمایشی",
            phone="09120000001",
            province="تهران",
            city="تهران",
            postal_code="1234567890",
            address_line="خیابان نمونه، پلاک ۱",
        )
        self.other_address = Address.objects.create(
            user=self.other_user,
            first_name="رضا",
            last_name="دیگر",
            phone="09120000002",
            province="فارس",
            city="شیراز",
            postal_code="0987654321",
            address_line="آدرس متعلق به کاربر دیگر",
        )
        category = Category.objects.create(name="کالای دیجیتال", slug="digital")
        brand = Brand.objects.create(
            name="برند آزمایشی",
            About_the_company="توضیحات برند",
            established="1400",
        )
        self.product = Product.objects.create(
            category=category,
            brand=brand,
            name="محصول آزمایشی",
            slug="test-product",
            inventory=10,
            price=1_000_000,
            off=100_000,
            weight=200,
        )
        self.coupon = Coupon.objects.create(
            code="TEST10",
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1),
            discount=10,
            active=True,
        )
        self.client.force_login(self.user)

    def _prepare_checkout_session(self, address_id=None, with_coupon=True):
        session = self.client.session
        session["cart"] = {
            str(self.product.id): {
                "quantity": 2,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session["checkout_address_id"] = address_id or self.address.id
        if with_coupon:
            session["coupon_id"] = self.coupon.id
        session.save()

    def test_profile_does_not_accept_post_or_staff_fields(self):
        response = self.client.post(
            reverse("account:profile"),
            {"is_staff": "on", "is_superuser": "on"},
        )
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 405)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_checkout_review_rejects_another_users_address(self):
        self._prepare_checkout_session(address_id=self.other_address.id)
        response = self.client.get(reverse("orders:checkout_review"))
        self.assertEqual(response.status_code, 404)

    def test_order_creation_is_post_only(self):
        self._prepare_checkout_session()
        response = self.client.get(reverse("orders:checkout_create"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_payment_method_does_not_create_order(self):
        self._prepare_checkout_session()
        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "invalid"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_stores_product_snapshot_and_discount(self):
        self._prepare_checkout_session()
        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "cod"},
        )

        self.assertRedirects(response, reverse("orders:checkout_complete"))
        order = Order.objects.get(user=self.user)
        item = order.items.get()
        self.product.refresh_from_db()

        expected_subtotal = self.product.new_price * 2
        expected_discount = expected_subtotal * 10 // 100
        expected_shipping = 65_000

        self.assertEqual(item.title, self.product.name)
        self.assertEqual(item.price, self.product.new_price)
        self.assertEqual(order.subtotal, expected_subtotal)
        self.assertEqual(order.discount_amount, expected_discount)
        self.assertEqual(order.coupon_code, self.coupon.code)
        self.assertEqual(
            order.total,
            expected_subtotal - expected_discount + expected_shipping,
        )
        self.assertEqual(self.product.inventory, 8)

class PaymentLifecycleTests(CheckoutSecurityTests):
    def _create_online_order(self):
        self._prepare_checkout_session(with_coupon=False)
        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "online"},
        )
        self.assertEqual(response.status_code, 302)
        return Order.objects.get(user=self.user, payment_method="online")

    def test_cancel_unpaid_order_restores_stock_once(self):
        order = self._create_online_order()
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 8)

        canceled_order, changed = OrderLifecycleService.cancel_unpaid_order(
            order.id,
            reason="لغو آزمایشی پرداخت",
        )
        self.assertTrue(changed)
        self.assertEqual(canceled_order.status, "canceled")
        self.assertTrue(canceled_order.stock_released)

        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 10)

        OrderLifecycleService.cancel_unpaid_order(
            order.id,
            reason="لغو آزمایشی پرداخت",
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 10)

    def test_payment_callback_cancel_releases_stock(self):
        order = self._create_online_order()
        payment_transaction = Transaction.objects.create(
            order=order,
            transaction_id="A000000000000000000000000000000001",
            provider="zarinpal",
            amount=order.total,
            status="pending",
            success=False,
        )

        response = self.client.get(
            reverse("payment:verify"),
            {"Authority": payment_transaction.transaction_id, "Status": "NOK"},
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        payment_transaction.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(order.status, "canceled")
        self.assertTrue(order.stock_released)
        self.assertEqual(payment_transaction.status, "canceled")
        self.assertEqual(self.product.inventory, 10)

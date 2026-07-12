from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.account.models import Address, ShopUser
from apps.coupons.models import Coupon
from apps.shop.models import Brand, Category, Product

from apps.orders.models import Order
from apps.orders.session_keys import (
    CART_SESSION_KEY,
    CHECKOUT_ADDRESS_SESSION_KEY,
    CHECKOUT_ORDER_SESSION_KEY,
    COUPON_SESSION_KEY,
    PAYMENT_ORDER_SESSION_KEY,
)


class RedShopTestBase:
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
        session[CART_SESSION_KEY] = {
            str(self.product.id): {
                "quantity": 2,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session[CHECKOUT_ADDRESS_SESSION_KEY] = address_id or self.address.id
        if with_coupon:
            session[COUPON_SESSION_KEY] = self.coupon.id
        session.save()

    def _choose_cash_payment_method(self):
        field = Order._meta.get_field("payment_method")
        choices = [key for key, _label in field.choices]

        for candidate in ("cash_on_delivery", "cod", "cash", "cash_delivery"):
            if candidate in choices:
                return candidate

        for key in choices:
            if "online" not in str(key).lower():
                return key

        return choices[0] if choices else "cash_on_delivery"

    def _sample_value_for_required_order_field(self, field):
        from decimal import Decimal
        import uuid

        from django.db import models
        from django.utils import timezone

        if isinstance(field, models.CharField):
            if field.name == "order_number":
                return f"TEST-{uuid.uuid4().hex[:12]}"
            if field.choices:
                return list(field.choices)[0][0]
            return "test"

        if isinstance(field, models.TextField):
            return "test"

        if isinstance(field, models.EmailField):
            return "test@example.com"

        if isinstance(field, models.DecimalField):
            return Decimal("0.00")

        if isinstance(field, models.IntegerField):
            return 0

        if isinstance(field, models.BooleanField):
            return False

        if isinstance(field, models.DateTimeField):
            return timezone.now()

        if isinstance(field, models.DateField):
            return timezone.now().date()

        return None

    def _create_paid_stale_order(self):
        from django.db import models
        from django.db.models.fields import NOT_PROVIDED

        payment_method = self._choose_cash_payment_method()

        order_kwargs = {
            "user": self.user,
            "payment_method": payment_method,
            "paid": True,
        }

        for field in Order._meta.fields:
            if field.primary_key:
                continue

            if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                continue

            if field.name in order_kwargs:
                continue

            if field.name == "user":
                order_kwargs["user"] = self.user
                continue

            if field.name == "address":
                order_kwargs["address"] = self.address
                continue

            if field.name == "status" and field.choices:
                choices = [key for key, _label in field.choices]
                order_kwargs["status"] = "pending" if "pending" in choices else choices[0]
                continue

            if field.name == "stock_released":
                order_kwargs["stock_released"] = False
                continue

            if field.name == "coupon_released":
                order_kwargs["coupon_released"] = False
                continue

            if field.default is not NOT_PROVIDED:
                continue

            if field.null:
                continue

            if isinstance(field, models.ForeignKey):
                continue

            order_kwargs[field.name] = self._sample_value_for_required_order_field(field)

        return Order.objects.create(**order_kwargs), payment_method

    def _put_single_product_cart_in_session(self, session):
        session[CART_SESSION_KEY] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.new_price),
                "weight": str(self.product.weight),
            }
        }

class CheckoutSecurityTests(RedShopTestBase, TestCase):

    def test_stale_paid_checkout_session_is_ignored_before_new_order(self):
        old_order, payment_method = self._create_paid_stale_order()

        session = self.client.session
        self._put_single_product_cart_in_session(session)
        session[CHECKOUT_ORDER_SESSION_KEY] = old_order.id
        session[PAYMENT_ORDER_SESSION_KEY] = old_order.id
        session[CHECKOUT_ADDRESS_SESSION_KEY] = self.address.id
        session.save()

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": payment_method},
        )

        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertNotEqual(session.get(CHECKOUT_ORDER_SESSION_KEY), old_order.id)
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 2)

    def test_invalid_payment_session_is_cleared(self):
        session = self.client.session
        session[PAYMENT_ORDER_SESSION_KEY] = 999999
        session[CHECKOUT_ORDER_SESSION_KEY] = 999999
        session.save()

        response = self.client.get(reverse("payment:process"))

        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)


    def test_payment_process_clears_session_for_already_paid_order(self):
        order, _payment_method = self._create_paid_stale_order()
        order.payment_method = "online"
        order.paid = True
        order.stock_released = False
        order.save(update_fields=["payment_method", "paid", "stock_released", "updated"])

        session = self.client.session
        session[PAYMENT_ORDER_SESSION_KEY] = order.id
        session[CHECKOUT_ORDER_SESSION_KEY] = order.id
        session.save()

        response = self.client.get(reverse("payment:process"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/success.html")

        session = self.client.session
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)

    def test_payment_process_clears_session_for_stock_released_order(self):
        order, _payment_method = self._create_paid_stale_order()
        order.payment_method = "online"
        order.paid = False
        order.stock_released = True
        order.save(update_fields=["payment_method", "paid", "stock_released", "updated"])

        session = self.client.session
        session[PAYMENT_ORDER_SESSION_KEY] = order.id
        session[CHECKOUT_ORDER_SESSION_KEY] = order.id
        session.save()

        response = self.client.get(reverse("payment:process"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/failure.html")

        session = self.client.session
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)

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

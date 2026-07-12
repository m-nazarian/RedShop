from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.account.models import Address, ShopUser
from apps.coupons.models import Coupon
from apps.shop.models import Brand, Category, Product

from .models import Order, Transaction
from .services import OrderLifecycleService


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
        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.new_price),
                "weight": str(self.product.weight),
            }
        }

class ProjectSettingsTests(TestCase):
    def test_logging_configuration_is_available(self):
        from django.conf import settings

        self.assertIn("version", settings.LOGGING)
        self.assertEqual(settings.LOGGING["version"], 1)
        self.assertIn("handlers", settings.LOGGING)
        self.assertIn("loggers", settings.LOGGING)
        self.assertIn("apps", settings.LOGGING["loggers"])
        self.assertIn("django.request", settings.LOGGING["loggers"])


class CheckoutSecurityTests(RedShopTestBase, TestCase):

    def test_stale_paid_checkout_session_is_ignored_before_new_order(self):
        old_order, payment_method = self._create_paid_stale_order()

        session = self.client.session
        self._put_single_product_cart_in_session(session)
        session["checkout_order_id"] = old_order.id
        session["order_id"] = old_order.id
        session["checkout_address_id"] = self.address.id
        session.save()

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": payment_method},
        )

        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertNotEqual(session.get("checkout_order_id"), old_order.id)
        self.assertNotIn("order_id", session)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 2)

    def test_invalid_payment_session_is_cleared(self):
        session = self.client.session
        session["order_id"] = 999999
        session["checkout_order_id"] = 999999
        session.save()

        response = self.client.get(reverse("payment:process"))

        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertNotIn("order_id", session)
        self.assertNotIn("checkout_order_id", session)


    def test_cart_mutation_views_are_post_only(self):
        update_response = self.client.get(reverse("cart:update_quantity"))
        remove_response = self.client.get(reverse("cart:remove_item"))

        self.assertEqual(update_response.status_code, 405)
        self.assertEqual(remove_response.status_code, 405)

    def test_read_only_cart_pages_accept_get(self):
        response = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(response.status_code, 200)


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


    def test_shop_index_and_product_detail_smoke_after_query_optimization(self):
        index_response = self.client.get(reverse("shop:index"))
        self.assertEqual(index_response.status_code, 200)

        detail_response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(detail_response.status_code, 200)



    def test_cart_update_rejects_invalid_action(self):
        session = self.client.session
        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session.save()

        response = self.client.post(
            reverse("cart:update_quantity"),
            {"item_id": self.product.id, "action": "invalid"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_cart_update_rejects_missing_item(self):
        response = self.client.post(
            reverse("cart:update_quantity"),
            {"item_id": self.product.id, "action": "add"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_cart_update_rejects_quantity_over_inventory(self):
        session = self.client.session
        session["cart"] = {
            str(self.product.id): {
                "quantity": self.product.inventory,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session.save()

        response = self.client.post(
            reverse("cart:update_quantity"),
            {"item_id": self.product.id, "action": "add"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_cart_remove_rejects_missing_item(self):
        response = self.client.post(
            reverse("cart:remove_item"),
            {"item_id": self.product.id},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_cart_remove_existing_item(self):
        session = self.client.session
        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session.save()

        response = self.client.post(
            reverse("cart:remove_item"),
            {"item_id": self.product.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["item_count"], 0)

class PaymentLifecycleTests(RedShopTestBase, TestCase):
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


    def test_plain_status_change_does_not_touch_inventory(self):
        order = self._create_online_order()
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 8)

        order.status = "canceled"
        order.save(update_fields=["status", "updated"])

        self.product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(self.product.inventory, 8)
        self.assertFalse(order.stock_released)

        OrderLifecycleService.cancel_unpaid_order(
            order.id,
            reason="لغو آزمایشی بعد از تغییر وضعیت دستی",
        )

        self.product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(self.product.inventory, 10)
        self.assertTrue(order.stock_released)


    def test_cancel_paid_order_does_not_release_stock(self):
        order = self._create_online_order()

        order.paid = True
        order.status = "processing"
        order.save(update_fields=["paid", "status", "updated"])

        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 8)

        updated_order, changed = OrderLifecycleService.cancel_unpaid_order(
            order.id,
            reason="تلاش برای لغو سفارش پرداخت‌شده",
        )

        self.product.refresh_from_db()
        updated_order.refresh_from_db()

        self.assertFalse(changed)
        self.assertEqual(self.product.inventory, 8)
        self.assertFalse(updated_order.stock_released)
        self.assertEqual(updated_order.status, "processing")

    def test_admin_cancel_action_uses_lifecycle_service(self):
        order = self._create_online_order()

        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 8)

        from apps.orders.admin import cancel_unpaid_orders

        class DummyAdmin:
            def __init__(self):
                self.messages = []

            def message_user(self, request, message, level=None):
                self.messages.append((message, level))

        dummy_admin = DummyAdmin()

        cancel_unpaid_orders(
            dummy_admin,
            request=None,
            queryset=Order.objects.filter(id=order.id),
        )

        self.product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(self.product.inventory, 10)
        self.assertTrue(order.stock_released)
        self.assertEqual(order.status, "canceled")
        self.assertTrue(dummy_admin.messages)


    def test_coupon_usage_count_increases_when_order_created(self):
        self._prepare_checkout_session(with_coupon=True)

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "cod"},
        )

        self.assertRedirects(response, reverse("orders:checkout_complete"))

        self.coupon.refresh_from_db()
        order = Order.objects.get(user=self.user)

        self.assertEqual(self.coupon.used_count, 1)
        self.assertEqual(order.coupon_code, self.coupon.code)
        self.assertFalse(order.coupon_released)

    def test_coupon_usage_limit_prevents_extra_discount(self):
        self.coupon.usage_limit = 1
        self.coupon.used_count = 1
        self.coupon.save(update_fields=["usage_limit", "used_count"])

        self._prepare_checkout_session(with_coupon=True)

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "cod"},
        )

        self.assertRedirects(response, reverse("orders:checkout_complete"))

        order = Order.objects.get(user=self.user)

        self.coupon.refresh_from_db()

        self.assertEqual(order.discount_amount, 0)
        self.assertEqual(order.coupon_code, "")
        self.assertEqual(self.coupon.used_count, 1)

    def test_cancel_unpaid_order_releases_coupon_usage_once(self):
        self._prepare_checkout_session(with_coupon=True)

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "online"},
        )

        self.assertEqual(response.status_code, 302)

        order = Order.objects.get(user=self.user, payment_method="online")
        self.coupon.refresh_from_db()

        self.assertEqual(self.coupon.used_count, 1)
        self.assertFalse(order.coupon_released)

        OrderLifecycleService.cancel_unpaid_order(
            order.id,
            reason="لغو آزمایشی برای آزادسازی کوپن",
        )

        self.coupon.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(self.coupon.used_count, 0)
        self.assertTrue(order.coupon_released)

        OrderLifecycleService.cancel_unpaid_order(
            order.id,
            reason="تلاش تکراری برای آزادسازی کوپن",
        )

        self.coupon.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(self.coupon.used_count, 0)
        self.assertTrue(order.coupon_released)

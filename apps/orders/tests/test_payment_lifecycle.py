from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, Transaction
from apps.orders.services import OrderLifecycleService
from apps.orders.tests.helpers import RedShopTestBase


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

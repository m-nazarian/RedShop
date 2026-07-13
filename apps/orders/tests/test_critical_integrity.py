
from unittest.mock import patch

from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, OrderItem, Transaction
from apps.orders.services import OrderLifecycleService
from apps.orders.tests.helpers import RedShopTestBase


class CriticalPaymentIntegrityTests(RedShopTestBase, TestCase):
    def _create_online_order(self):
        self._prepare_checkout_session(with_coupon=False)

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": Order.PAYMENT_METHOD_ONLINE},
        )

        self.assertEqual(response.status_code, 302)

        return Order.objects.get(
            user=self.user,
            payment_method=Order.PAYMENT_METHOD_ONLINE,
        )

    @staticmethod
    def _create_payment_transaction(order, authority):
        return Transaction.objects.create(
            order=order,
            transaction_id=authority,
            provider="zarinpal",
            amount=order.total,
            status=Transaction.STATUS_PENDING,
            success=False,
        )

    @patch("apps.payment.views.ZarinPalService.verify_payment")
    def test_successful_callback_marks_order_and_transaction_paid(self, verify_payment):
        verify_payment.return_value = {
            "status": True,
            "code": 100,
            "ref_id": "123456789",
        }

        order = self._create_online_order()
        payment_transaction = self._create_payment_transaction(
            order,
            "A000000000000000000000000000000101",
        )

        response = self.client.get(
            reverse("payment:verify"),
            {"Authority": payment_transaction.transaction_id, "Status": "OK"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/success.html")

        order.refresh_from_db()
        payment_transaction.refresh_from_db()

        self.assertTrue(order.paid)
        self.assertEqual(order.status, Order.STATUS_PROCESSING)
        self.assertFalse(order.stock_released)
        self.assertTrue(payment_transaction.success)
        self.assertEqual(payment_transaction.status, Transaction.STATUS_PAID)
        self.assertEqual(payment_transaction.ref_id, "123456789")

    @patch("apps.payment.views.ZarinPalService.verify_payment")
    def test_success_after_stock_release_moves_order_to_payment_review(self, verify_payment):
        verify_payment.return_value = {
            "status": True,
            "code": 100,
            "ref_id": "987654321",
        }

        order = self._create_online_order()
        payment_transaction = self._create_payment_transaction(
            order,
            "A000000000000000000000000000000102",
        )

        OrderLifecycleService.cancel_unpaid_order(
            order.pk,
            reason="Canceled before callback",
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 10)

        response = self.client.get(
            reverse("payment:verify"),
            {"Authority": payment_transaction.transaction_id, "Status": "OK"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/failure.html")

        order.refresh_from_db()
        payment_transaction.refresh_from_db()
        self.product.refresh_from_db()

        self.assertTrue(order.paid)
        self.assertTrue(order.stock_released)
        self.assertEqual(order.status, Order.STATUS_PAYMENT_REVIEW)
        self.assertEqual(self.product.inventory, 10)
        self.assertTrue(payment_transaction.success)
        self.assertEqual(payment_transaction.status, Transaction.STATUS_PAID)
        self.assertIn("Payment was verified after", order.notes)

    @patch("apps.payment.views.ZarinPalService.verify_payment")
    def test_repeated_successful_callback_is_idempotent(self, verify_payment):
        verify_payment.return_value = {
            "status": True,
            "code": 100,
            "ref_id": "111222333",
        }

        order = self._create_online_order()
        payment_transaction = self._create_payment_transaction(
            order,
            "A000000000000000000000000000000103",
        )

        callback_data = {
            "Authority": payment_transaction.transaction_id,
            "Status": "OK",
        }

        first_response = self.client.get(reverse("payment:verify"), callback_data)
        second_response = self.client.get(reverse("payment:verify"), callback_data)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        self.assertEqual(
            Transaction.objects.filter(order=order, success=True).count(),
            1,
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 8)

    def test_provider_authority_is_unique(self):
        order = self._create_online_order()
        authority = "A000000000000000000000000000000104"

        self._create_payment_transaction(order, authority)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_payment_transaction(order, authority)


class FinancialHistoryIntegrityTests(RedShopTestBase, TestCase):
    def _create_order(self):
        self._prepare_checkout_session(with_coupon=False)

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": Order.PAYMENT_METHOD_COD},
        )

        self.assertEqual(response.status_code, 302)

        return Order.objects.get(user=self.user)

    def test_deleting_user_preserves_order_history(self):
        order = self._create_order()
        user_id = self.user.pk

        self.user.delete()

        order.refresh_from_db()

        self.assertIsNone(order.user_id)
        self.assertFalse(Order.objects.filter(pk=order.pk, user_id=user_id).exists())

    def test_deleting_product_preserves_order_item_snapshot(self):
        order = self._create_order()
        order_item = OrderItem.objects.get(order=order)
        original_title = order_item.title
        original_price = order_item.price

        self.product.delete()

        order_item.refresh_from_db()

        self.assertIsNone(order_item.product_id)
        self.assertEqual(order_item.title, original_title)
        self.assertEqual(order_item.price, original_price)

    def test_order_admin_blocks_direct_financial_state_editing(self):
        order_admin = admin.site._registry[Order]
        transaction_admin = admin.site._registry[Transaction]

        self.assertNotIn("status", getattr(order_admin, "list_editable", ()))
        self.assertNotIn("paid", getattr(order_admin, "list_editable", ()))
        self.assertIn("status", order_admin.readonly_fields)
        self.assertIn("paid", order_admin.readonly_fields)
        self.assertIn("raw_response", transaction_admin.readonly_fields)


from __future__ import annotations

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.orders.audit import (
    ORDER_AUDIT_ADMIN_NOTE,
    ORDER_AUDIT_PAYMENT_REVIEW_EXPORT,
    log_order_audit,
)
from apps.orders.admin import export_payment_review_orders
from apps.orders.models import Order, OrderAuditLog
from apps.orders.tests.test_payment_review_admin import create_order, create_user


class OrderAuditLogTests(TestCase):
    def setUp(self):
        self.user = create_user("09124440601")
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.request = RequestFactory().get("/admin/orders/order/")
        self.request.user = self.user
        self.request.request_id = "req-admin-audit-001"

    def test_log_order_audit_records_actor_request_id_and_metadata(self):
        order = create_order(
            self.user,
            order_number="AUDIT-ORDER-001",
            status=getattr(Order, "STATUS_PAYMENT_REVIEW", "payment_review"),
        )

        log = log_order_audit(
            order=order,
            action=ORDER_AUDIT_ADMIN_NOTE,
            actor=self.user,
            request_id="req-manual-001",
            message="Manual audit note",
            metadata={"source": "test"},
        )

        self.assertEqual(log.order, order)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.request_id, "req-manual-001")
        self.assertEqual(log.metadata["source"], "test")

    def test_payment_review_csv_export_creates_audit_log_for_review_orders_only(self):
        review = create_order(
            self.user,
            order_number="AUDIT-EXPORT-001",
            status=getattr(Order, "STATUS_PAYMENT_REVIEW", "payment_review"),
        )
        normal = create_order(
            self.user,
            order_number="AUDIT-EXPORT-002",
            status=getattr(Order, "STATUS_PROCESSING", "processing"),
        )

        order_admin = admin.site._registry[Order]
        response = export_payment_review_orders(
            order_admin,
            self.request,
            Order.objects.filter(pk__in=[review.pk, normal.pk]),
        )

        self.assertEqual(response.status_code, 200)

        logs = OrderAuditLog.objects.filter(
            action=ORDER_AUDIT_PAYMENT_REVIEW_EXPORT,
        )

        self.assertEqual(logs.count(), 1)

        log = logs.get()
        self.assertEqual(log.order, review)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.request_id, "req-admin-audit-001")
        self.assertEqual(log.metadata["order_number"], review.order_number)
        self.assertEqual(log.metadata["admin_action"], "export_payment_review_orders")

    def test_order_audit_log_admin_is_registered_and_read_only(self):
        audit_admin = admin.site._registry[OrderAuditLog]

        self.assertFalse(audit_admin.has_add_permission(self.request))
        self.assertFalse(audit_admin.has_change_permission(self.request))
        self.assertFalse(audit_admin.has_delete_permission(self.request))
        self.assertIn("request_id", audit_admin.search_fields)

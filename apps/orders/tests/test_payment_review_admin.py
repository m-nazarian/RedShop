
from __future__ import annotations

import csv
from io import StringIO

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.account.models import ShopUser
from apps.orders.admin import PaymentReviewStatusFilter, export_payment_review_orders
from apps.orders.models import Order


def _order_field_names():
    return {field.name for field in Order._meta.fields}


def _safe_required_value(field):
    internal_type = field.get_internal_type()

    if internal_type in {"CharField", "TextField", "SlugField"}:
        return "Test"
    if internal_type in {"IntegerField", "PositiveIntegerField", "SmallIntegerField", "PositiveSmallIntegerField"}:
        return 1
    if internal_type in {"DecimalField", "FloatField"}:
        return 1
    if internal_type == "BooleanField":
        return False

    return None


def create_user(phone):
    return ShopUser.objects.create_user(
        phone=phone,
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )


def create_order(user, *, order_number, status, paid=True):
    field_names = _order_field_names()
    values = {}

    if "user" in field_names:
        values["user"] = user
    if "order_number" in field_names:
        values["order_number"] = order_number
    if "paid" in field_names:
        values["paid"] = paid
    if "status" in field_names:
        values["status"] = status
    if "payment_method" in field_names:
        values["payment_method"] = getattr(Order, "PAYMENT_METHOD_ONLINE", "online")

    common_values = {
        "first_name": "Ali",
        "last_name": "Test",
        "phone": "09125557777",
        "email": "test@example.com",
        "province": "Tehran",
        "city": "Tehran",
        "postal_code": "1234567890",
        "address": "Test address",
        "address_line": "Test address",
        "subtotal": 1000,
        "discount_amount": 0,
        "shipping_price": 0,
        "post_price": 0,
        "total": 1000,
        "total_price": 1000,
        "weight": 1000,
        "notes": "payment review note",
    }

    for name, value in common_values.items():
        if name in field_names:
            values.setdefault(name, value)

    for field in Order._meta.fields:
        if field.name in values:
            continue
        if field.primary_key or field.auto_created or field.has_default() or field.null or field.blank:
            continue

        safe_value = _safe_required_value(field)
        if safe_value is not None:
            values[field.name] = safe_value

    return Order.objects.create(**values)


class PaymentReviewAdminTests(TestCase):
    def setUp(self):
        self.user = create_user("09124440501")
        self.request = RequestFactory().get("/admin/orders/order/")

    def test_payment_review_admin_tools_are_registered(self):
        order_admin = admin.site._registry[Order]

        list_display = tuple(order_admin.get_list_display(self.request))
        list_filter = tuple(order_admin.get_list_filter(self.request))
        actions = order_admin.get_actions(self.request)

        filter_names = {
            getattr(item, "__name__", str(item))
            for item in list_filter
        }

        self.assertIn("payment_review_badge", list_display)
        self.assertIn("PaymentReviewStatusFilter", filter_names)
        self.assertIn("export_payment_review_orders", actions)

    def test_payment_review_filter_returns_review_orders_only(self):
        review = create_order(
            self.user,
            order_number="REVIEW-ADMIN-001",
            status=getattr(Order, "STATUS_PAYMENT_REVIEW", "payment_review"),
        )
        normal = create_order(
            self.user,
            order_number="REVIEW-ADMIN-002",
            status=getattr(Order, "STATUS_PROCESSING", "processing"),
        )

        order_admin = admin.site._registry[Order]
        filter_instance = PaymentReviewStatusFilter(
            self.request,
            {"payment_review": "1"},
            Order,
            order_admin,
        )

        queryset = filter_instance.queryset(self.request, Order.objects.all())

        self.assertIn(review, queryset)
        self.assertNotIn(normal, queryset)

    def test_payment_review_export_contains_only_review_orders(self):
        review = create_order(
            self.user,
            order_number="REVIEW-ADMIN-CSV-001",
            status=getattr(Order, "STATUS_PAYMENT_REVIEW", "payment_review"),
        )
        create_order(
            self.user,
            order_number="REVIEW-ADMIN-CSV-002",
            status=getattr(Order, "STATUS_PROCESSING", "processing"),
        )

        order_admin = admin.site._registry[Order]
        response = export_payment_review_orders(
            order_admin,
            self.request,
            Order.objects.all(),
        )

        content = response.content.decode("utf-8-sig")
        rows = list(csv.DictReader(StringIO(content)))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["order_number"], review.order_number)
        self.assertEqual(rows[0]["status"], getattr(Order, "STATUS_PAYMENT_REVIEW", "payment_review"))

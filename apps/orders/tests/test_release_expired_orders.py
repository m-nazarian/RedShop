
from __future__ import annotations

from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.account.models import ShopUser
from apps.orders.models import Order


def _order_field_names():
    return {field.name for field in Order._meta.fields}


def _created_field_name():
    for candidate in ("created", "created_at", "created_time"):
        if candidate in _order_field_names():
            return candidate
    raise AssertionError("Order has no known created timestamp field.")


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
    if internal_type in {"DateTimeField", "DateField"}:
        return timezone.now()

    return None


def create_user(phone):
    return ShopUser.objects.create_user(
        phone=phone,
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )


def create_order(user, *, minutes_old, payment_method=None, status=None, paid=False):
    field_names = _order_field_names()
    values = {}

    if "user" in field_names:
        values["user"] = user
    if "paid" in field_names:
        values["paid"] = paid
    if "payment_method" in field_names:
        values["payment_method"] = payment_method or getattr(Order, "PAYMENT_METHOD_ONLINE", "online")
    if "status" in field_names:
        values["status"] = status or getattr(Order, "STATUS_PENDING", "pending")

    common_values = {
        "first_name": "Ali",
        "last_name": "Test",
        "phone": "09125558888",
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
    }

    for name, value in common_values.items():
        if name in field_names:
            values.setdefault(name, value)

    if "order_number" in field_names:
        values["order_number"] = f"TEST-EXPIRED-{Order.objects.count() + 1:06d}"

    for field in Order._meta.fields:
        if field.name in values:
            continue
        if field.primary_key or field.auto_created or field.has_default() or field.null or field.blank:
            continue

        safe_value = _safe_required_value(field)
        if safe_value is not None:
            values[field.name] = safe_value

    order = Order.objects.create(**values)

    created_field = _created_field_name()
    Order.objects.filter(pk=order.pk).update(
        **{created_field: timezone.now() - timedelta(minutes=minutes_old)}
    )

    return Order.objects.get(pk=order.pk)


class ReleaseExpiredOrdersCommandTests(TestCase):
    def setUp(self):
        self.user = create_user("09124440401")

    def test_command_releases_only_expired_unpaid_online_pending_orders(self):
        expired = create_order(self.user, minutes_old=120)
        create_order(self.user, minutes_old=5)
        create_order(
            self.user,
            minutes_old=120,
            payment_method=getattr(Order, "PAYMENT_METHOD_COD", "cod"),
        )
        create_order(self.user, minutes_old=120, paid=True)

        out = StringIO()

        with mock.patch(
            "apps.orders.management.commands.release_expired_orders.OrderLifecycleService.cancel_unpaid_order"
        ) as mocked_cancel:
            call_command(
                "release_expired_orders",
                "--older-than-minutes",
                "30",
                stdout=out,
            )

        self.assertEqual(mocked_cancel.call_count, 1)
        self.assertEqual(mocked_cancel.call_args.args[0].pk, expired.pk)
        self.assertIn("Released 1 expired unpaid online order", out.getvalue())

    def test_dry_run_does_not_call_lifecycle_service(self):
        create_order(self.user, minutes_old=120)

        out = StringIO()

        with mock.patch(
            "apps.orders.management.commands.release_expired_orders.OrderLifecycleService.cancel_unpaid_order"
        ) as mocked_cancel:
            call_command(
                "release_expired_orders",
                "--older-than-minutes",
                "30",
                "--dry-run",
                stdout=out,
            )

        mocked_cancel.assert_not_called()
        self.assertIn("Dry run: 1 expired unpaid online order", out.getvalue())

    def test_limit_caps_number_of_processed_orders(self):
        create_order(self.user, minutes_old=120)
        create_order(self.user, minutes_old=120)
        create_order(self.user, minutes_old=120)

        with mock.patch(
            "apps.orders.management.commands.release_expired_orders.OrderLifecycleService.cancel_unpaid_order"
        ) as mocked_cancel:
            call_command(
                "release_expired_orders",
                "--older-than-minutes",
                "30",
                "--limit",
                "2",
            )

        self.assertEqual(mocked_cancel.call_count, 2)


from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import OrderLifecycleService


def _model_field_names(model):
    return {field.name for field in model._meta.get_fields() if hasattr(field, "attname")}


def _created_field_name():
    field_names = _model_field_names(Order)

    for candidate in ("created", "created_at", "created_time"):
        if candidate in field_names:
            return candidate

    raise RuntimeError("Order model has no known created timestamp field.")


def _online_payment_value():
    return getattr(Order, "PAYMENT_METHOD_ONLINE", "online")


def _pending_status_value():
    return getattr(Order, "STATUS_PENDING", "pending")


def _call_cancel_unpaid_order(order, reason):
    """Call the lifecycle service without depending on a fragile signature."""
    candidates = []

    class_method = getattr(OrderLifecycleService, "cancel_unpaid_order", None)
    if callable(class_method):
        candidates.append(class_method)

    try:
        instance_method = getattr(OrderLifecycleService(), "cancel_unpaid_order", None)
        if callable(instance_method):
            candidates.append(instance_method)
    except TypeError:
        pass

    last_error = None

    for method in candidates:
        for kwargs in ({"reason": reason}, {"note": reason}, {}):
            try:
                return method(order, **kwargs)
            except TypeError as exc:
                last_error = exc
                continue

    if last_error is not None:
        raise last_error

    raise RuntimeError("OrderLifecycleService.cancel_unpaid_order was not found.")


class Command(BaseCommand):
    help = (
        "Release inventory and coupon reservations for stale unpaid online orders. "
        "Run this from cron, Task Scheduler, or a periodic worker."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-minutes",
            type=int,
            default=30,
            help="Cancel unpaid online orders older than this many minutes. Default: 30.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=200,
            help="Maximum number of expired orders to process in one run. Default: 200.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report matching orders without changing them.",
        )

    def handle(self, *args, **options):
        older_than_minutes = max(int(options["older_than_minutes"]), 1)
        limit = max(int(options["limit"]), 1)
        dry_run = bool(options["dry_run"])

        created_field = _created_field_name()
        cutoff = timezone.now() - timedelta(minutes=older_than_minutes)

        filters = {
            "paid": False,
            "payment_method": _online_payment_value(),
            "status": _pending_status_value(),
            f"{created_field}__lte": cutoff,
        }

        orders = (
            Order.objects.filter(**filters)
            .select_related("user")
            .order_by(created_field, "pk")[:limit]
        )

        order_ids = list(orders.values_list("pk", flat=True))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {len(order_ids)} expired unpaid online order(s) would be released."
                )
            )
            return

        released = 0

        for order_id in order_ids:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=order_id)
                _call_cancel_unpaid_order(
                    order,
                    reason=(
                        "Released automatically because the online payment was "
                        f"not completed within {older_than_minutes} minutes."
                    ),
                )
                released += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Released {released} expired unpaid online order reservation(s)."
            )
        )

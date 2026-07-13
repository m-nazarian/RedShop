
import logging

from django.contrib import admin, messages
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import Order, OrderItem, Transaction
from .services import OrderLifecycleService

logger = logging.getLogger(__name__)


@admin.action(description="Safely cancel unpaid orders and release stock")
def cancel_unpaid_orders(modeladmin, request, queryset):
    """Route every cancellation through the order lifecycle service.

    Directly editing paid/status in Django admin is intentionally disabled. The
    service keeps inventory and coupon usage consistent with the order state.
    """
    counters = {"canceled": 0, "unchanged": 0, "paid": 0, "errors": 0}

    for order in queryset.only("id", "paid"):
        if order.paid:
            counters["paid"] += 1
            continue

        try:
            _order, changed = OrderLifecycleService.cancel_unpaid_order(
                order.id,
                reason="Canceled from admin",
            )
        except Exception:
            logger.exception("Safe admin cancellation failed. order_id=%s", order.id)
            counters["errors"] += 1
            continue

        counters["canceled" if changed else "unchanged"] += 1

    parts = []
    if counters["canceled"]:
        parts.append(f"{counters['canceled']} unpaid order(s) were canceled.")
    if counters["paid"]:
        parts.append(f"{counters['paid']} paid order(s) were not changed.")
    if counters["unchanged"]:
        parts.append(f"{counters['unchanged']} order(s) were already final.")
    if counters["errors"]:
        parts.append(f"{counters['errors']} order(s) failed.")
    if not parts:
        parts.append("No cancellable order was found.")

    level = messages.ERROR if counters["errors"] else messages.SUCCESS
    if not counters["errors"] and not counters["canceled"]:
        level = messages.WARNING

    modeladmin.message_user(request, " ".join(parts), level=level)


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    tab = True
    readonly_fields = ("product", "title", "price", "quantity", "weight", "get_cost")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "order_number",
        "customer_fullname",
        "phone",
        "status_badge",
        "payment_method_badge",
        "total_display",
        "paid_badge",
        "created_jalali",
    )
    list_filter = ("status", "payment_method", "created", "paid")
    search_fields = ("order_number", "phone", "last_name", "address")
    inlines = (OrderItemInline,)
    actions = (cancel_unpaid_orders,)
    readonly_fields = (
        "order_number",
        "user",
        "first_name",
        "last_name",
        "phone",
        "address",
        "province",
        "city",
        "postal_code",
        "address_line",
        "payment_method",
        "paid",
        "stock_released",
        "status",
        "subtotal",
        "discount_amount",
        "coupon_code",
        "coupon_released",
        "shipping_price",
        "post_price",
        "total",
        "created",
        "updated",
        "canceled_at",
        "notes",
    )
    list_per_page = 20
    list_filter_submit = True

    @display(
        description="Status",
        label={
            Order.STATUS_PENDING: "warning",
            Order.STATUS_PROCESSING: "info",
            Order.STATUS_PAYMENT_REVIEW: "danger",
            Order.STATUS_SHIPPED: "primary",
            Order.STATUS_DELIVERED: "success",
            Order.STATUS_CANCELED: "danger",
            Order.STATUS_REFUNDED: "secondary",
        },
    )
    def status_badge(self, obj):
        return obj.status

    @display(
        description="Payment method",
        label={
            Order.PAYMENT_METHOD_ONLINE: "success",
            Order.PAYMENT_METHOD_COD: "warning",
        },
    )
    def payment_method_badge(self, obj):
        return obj.payment_method

    @display(description="Paid", boolean=True)
    def paid_badge(self, obj):
        return obj.paid

    @display(description="Total", label=True)
    def total_display(self, obj):
        return f"{obj.total:,} toman"

    @admin.display(description="Customer")
    def customer_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description="Created")
    def created_jalali(self, obj):
        return obj.created.strftime("%Y/%m/%d %H:%M")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = (
        "order",
        "provider",
        "amount_display",
        "status_badge",
        "success_badge",
        "created_jalali",
    )
    list_filter = ("provider", "status", "success")
    search_fields = ("transaction_id", "ref_id", "order__order_number")
    readonly_fields = (
        "order",
        "transaction_id",
        "ref_id",
        "provider",
        "amount",
        "success",
        "status",
        "created_at",
        "updated_at",
        "raw_response",
    )

    @display(description="Amount", label=True)
    def amount_display(self, obj):
        return f"{obj.amount:,} toman"

    @display(
        description="Status",
        label={
            Transaction.STATUS_PENDING: "warning",
            Transaction.STATUS_PAID: "success",
            Transaction.STATUS_FAILED: "danger",
            Transaction.STATUS_CANCELED: "secondary",
        },
    )
    def status_badge(self, obj):
        return obj.status

    @display(description="Success", boolean=True)
    def success_badge(self, obj):
        return obj.success

    @admin.display(description="Created")
    def created_jalali(self, obj):
        return obj.created_at.strftime("%Y/%m/%d %H:%M")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in {"GET", "HEAD", "OPTIONS"}

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Payment review admin tools
# ---------------------------------------------------------------------------
# Orders can enter payment_review when a gateway callback succeeds after the
# original unpaid order reservation was already released. This is intentionally
# not auto-resolved: staff need a focused report to decide whether to re-reserve
# stock, contact the customer, or refund manually.

import csv

from django.contrib import admin as django_admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Order as _PaymentReviewOrder


def _payment_review_status_value():
    return getattr(_PaymentReviewOrder, "STATUS_PAYMENT_REVIEW", "payment_review")


def _payment_review_created_value(order):
    for field_name in ("created", "created_at", "created_time"):
        value = getattr(order, field_name, None)
        if value:
            return value
    return ""


def _payment_review_total_value(order):
    for field_name in ("total", "total_price", "payable_amount", "final_price"):
        value = getattr(order, field_name, None)
        if value is not None:
            return value

    method = getattr(order, "get_total_cost", None)
    if callable(method):
        return method()

    return ""


def _payment_review_user_phone(order):
    user = getattr(order, "user", None)

    if user is not None:
        return getattr(user, "phone", "") or ""

    return getattr(order, "phone", "") or ""


class PaymentReviewStatusFilter(django_admin.SimpleListFilter):
    title = "بازبینی پرداخت"
    parameter_name = "payment_review"

    def lookups(self, request, model_admin):
        return (
            ("1", "نیازمند بازبینی پرداخت"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(status=_payment_review_status_value())
        return queryset


def payment_review_badge(self, obj):
    if getattr(obj, "status", None) == _payment_review_status_value():
        return format_html(
            '<span style="background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;'
            'border-radius:999px;padding:2px 8px;font-size:12px;font-weight:700;">'
            "نیازمند بررسی پرداخت</span>"
        )

    return "-"


payment_review_badge.short_description = "وضعیت بازبینی پرداخت"


def export_payment_review_orders(modeladmin, request, queryset):
    review_orders = (
        queryset.filter(status=_payment_review_status_value())
        .select_related("user")
        .order_by("id")
    )

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="payment-review-orders.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow(
        [
            "order_id",
            "order_number",
            "user_id",
            "user_phone",
            "status",
            "paid",
            "payment_method",
            "total",
            "created",
            "notes",
        ]
    )

    for order in review_orders:
        writer.writerow(
            [
                order.pk,
                getattr(order, "order_number", ""),
                getattr(order, "user_id", "") or "",
                _payment_review_user_phone(order),
                getattr(order, "status", ""),
                getattr(order, "paid", ""),
                getattr(order, "payment_method", ""),
                _payment_review_total_value(order),
                _payment_review_created_value(order),
                getattr(order, "notes", "") or "",
            ]
        )

    return response


export_payment_review_orders.short_description = "خروجی CSV سفارش‌های نیازمند بازبینی پرداخت"


def _install_payment_review_admin_tools():
    model_admin = django_admin.site._registry.get(_PaymentReviewOrder)

    if model_admin is None:
        return

    admin_class = model_admin.__class__

    if not hasattr(admin_class, "payment_review_badge"):
        setattr(admin_class, "payment_review_badge", payment_review_badge)

    list_display = tuple(getattr(model_admin, "list_display", ()) or ())

    if "payment_review_badge" not in list_display:
        if "status" in list_display:
            insert_index = list_display.index("status") + 1
            list_display = (
                list_display[:insert_index]
                + ("payment_review_badge",)
                + list_display[insert_index:]
            )
        else:
            list_display = list_display + ("payment_review_badge",)

        model_admin.list_display = list_display

    list_filter = tuple(getattr(model_admin, "list_filter", ()) or ())
    filter_names = {
        getattr(item, "__name__", str(item))
        for item in list_filter
    }

    if "PaymentReviewStatusFilter" not in filter_names:
        model_admin.list_filter = list_filter + (PaymentReviewStatusFilter,)

    actions = tuple(getattr(model_admin, "actions", ()) or ())
    action_names = {
        item if isinstance(item, str) else getattr(item, "__name__", str(item))
        for item in actions
    }

    if "export_payment_review_orders" not in action_names:
        model_admin.actions = actions + (export_payment_review_orders,)


_install_payment_review_admin_tools()


# ---------------------------------------------------------------------------
# Order audit log admin integration
# ---------------------------------------------------------------------------

from .audit import ORDER_AUDIT_PAYMENT_REVIEW_EXPORT, log_order_audit
from .models import OrderAuditLog as _OrderAuditLog


class OrderAuditLogAdmin(django_admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "action",
        "order",
        "actor",
        "request_id",
    )
    list_filter = ("action", "created_at")
    search_fields = (
        "order__order_number",
        "request_id",
        "message",
        "actor__phone",
        "actor__email",
    )
    readonly_fields = (
        "order",
        "actor",
        "action",
        "request_id",
        "message",
        "metadata",
        "created_at",
    )
    ordering = ("-created_at", "-id")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


if _OrderAuditLog not in django_admin.site._registry:
    django_admin.site.register(_OrderAuditLog, OrderAuditLogAdmin)


try:
    _payment_review_export_without_audit = export_payment_review_orders
except NameError:
    _payment_review_export_without_audit = None


if _payment_review_export_without_audit is not None:
    def export_payment_review_orders(modeladmin, request, queryset):
        response = _payment_review_export_without_audit(modeladmin, request, queryset)

        request_id = getattr(request, "request_id", None)
        actor = getattr(request, "user", None)
        review_orders = queryset.filter(status=_payment_review_status_value()).order_by("id")

        for order in review_orders:
            log_order_audit(
                order=order,
                action=ORDER_AUDIT_PAYMENT_REVIEW_EXPORT,
                actor=actor,
                request_id=request_id,
                message="Payment review CSV exported from Django admin.",
                metadata={
                    "order_number": getattr(order, "order_number", ""),
                    "admin_action": "export_payment_review_orders",
                },
            )

        return response

    export_payment_review_orders.short_description = getattr(
        _payment_review_export_without_audit,
        "short_description",
        "خروجی CSV سفارش‌های نیازمند بازبینی پرداخت",
    )

    def _replace_payment_review_export_action_with_audited_version():
        model_admin = django_admin.site._registry.get(_PaymentReviewOrder)

        if model_admin is None:
            return

        actions = tuple(getattr(model_admin, "actions", ()) or ())
        new_actions = []
        replaced = False

        for action in actions:
            action_name = action if isinstance(action, str) else getattr(action, "__name__", str(action))

            if action_name == "export_payment_review_orders":
                if not replaced:
                    new_actions.append(export_payment_review_orders)
                    replaced = True
                continue

            new_actions.append(action)

        if not replaced:
            new_actions.append(export_payment_review_orders)

        model_admin.actions = tuple(new_actions)

    _replace_payment_review_export_action_with_audited_version()

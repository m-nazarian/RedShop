
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

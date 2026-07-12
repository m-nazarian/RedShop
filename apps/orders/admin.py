from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from .models import Order, OrderItem, Transaction

class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity', 'get_cost')
    can_delete = False
    tab = True

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['order_number', 'customer_fullname', 'phone', 'status', 'payment_method_badge', 'total_display',
                    'paid', 'created_jalali']
    list_filter = ['status', 'payment_method', 'created', 'paid']
    search_fields = ('order_number', 'phone', 'last_name', 'address')
    inlines = [OrderItemInline]
    list_editable = ('status', 'paid')
    readonly_fields = ('order_number', 'subtotal', 'total', 'created', 'updated')
    list_per_page = 20
    list_filter_submit = True

    # وضعیت سفارش رنگی
    @display(description="وضعیت", label={
        'pending': 'warning',
        'processing': 'info',
        'shipped': 'primary',
        'delivered': 'success',
        'canceled': 'danger',
        'refunded': 'secondary',
    })
    # def status_badge(self, obj):
    #     return obj.status

    # روش پرداخت رنگی
    @display(description="روش پرداخت", label={
        'online': 'success',
        'cod': 'warning',
    })
    def payment_method_badge(self, obj):
        return obj.payment_method

    @display(description="مبلغ کل", label=True)
    def total_display(self, obj):
        return f"{obj.total:,} تومان"

    def customer_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    customer_fullname.short_description = 'مشتری'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def created_jalali(self, obj):
        return obj.created.strftime("%Y/%m/%d %H:%M")
    created_jalali.short_description = 'تاریخ'

@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('order', 'provider', 'amount_display', 'success_badge', 'created_jalali')
    list_filter = ('provider', 'success')
    search_fields = ('transaction_id', 'ref_id', 'order__order_number')

    @display(description="مبلغ", label=True)
    def amount_display(self, obj):
        return f"{obj.amount:,} تومان"

    @display(description="وضعیت", label={
        True: 'success',
        False: 'danger'
    })
    def success_badge(self, obj):
        return obj.success

    def created_jalali(self, obj):
        # ✅ اصلاح شد: created_at به جای created
        return obj.created_at.strftime("%Y/%m/%d %H:%M")
    created_jalali.short_description = "تاریخ ایجاد"

# --- RedShop safe order admin actions ---

import logging

from django.contrib import admin as _redshop_admin
from django.contrib import messages as _redshop_messages

from .models import Order as _RedShopOrder
from .services import OrderLifecycleService as _RedShopOrderLifecycleService

_redshop_logger = logging.getLogger(__name__)


def cancel_unpaid_orders(modeladmin, request, queryset):
    """سفارش‌های پرداخت‌نشده را از مسیر امن Service لغو می‌کند."""
    canceled_count = 0
    unchanged_count = 0
    paid_count = 0
    error_count = 0

    for order in queryset.select_related("user"):
        if order.paid:
            paid_count += 1
            continue

        try:
            _updated_order, changed = _RedShopOrderLifecycleService.cancel_unpaid_order(
                order.id,
                reason="لغو از پنل مدیریت",
            )
        except Exception:
            _redshop_logger.exception(
                "لغو امن سفارش از پنل مدیریت با خطا روبه‌رو شد. order_id=%s",
                order.id,
            )
            error_count += 1
            continue

        if changed:
            canceled_count += 1
        else:
            unchanged_count += 1

    parts = []

    if canceled_count:
        parts.append(f"{canceled_count} سفارش پرداخت‌نشده لغو شد و موجودی آن برگشت.")

    if paid_count:
        parts.append(f"{paid_count} سفارش پرداخت‌شده تغییر نکرد.")

    if unchanged_count:
        parts.append(f"{unchanged_count} سفارش از قبل در وضعیت نهایی بود.")

    if error_count:
        parts.append(f"{error_count} سفارش به‌دلیل خطا پردازش نشد.")

    if not parts:
        parts.append("هیچ سفارشی برای لغو امن پیدا نشد.")

    if error_count:
        level = _redshop_messages.ERROR
    elif canceled_count:
        level = _redshop_messages.SUCCESS
    else:
        level = _redshop_messages.WARNING

    modeladmin.message_user(request, " ".join(parts), level=level)


cancel_unpaid_orders.short_description = "لغو امن سفارش‌های پرداخت‌نشده و برگشت موجودی"

try:
    _order_admin = _redshop_admin.site._registry.get(_RedShopOrder)
    if _order_admin is not None:
        _existing_actions = list(getattr(_order_admin, "actions", []) or [])
        _existing_names = {
            getattr(action, "__name__", str(action))
            for action in _existing_actions
        }

        if "cancel_unpaid_orders" not in _existing_names:
            _order_admin.actions = [*_existing_actions, cancel_unpaid_orders]
except Exception:
    _redshop_logger.exception("ثبت Admin Action لغو امن سفارش ناموفق بود.")

# --- End RedShop safe order admin actions ---

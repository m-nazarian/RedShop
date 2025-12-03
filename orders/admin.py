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
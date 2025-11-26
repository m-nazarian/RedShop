from django.contrib import admin
from .models import Order, OrderItem, Transaction


# Register your models here.


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ['product']
    readonly_fields = ('title', 'price', 'quantity', 'weight', 'get_cost')

    def get_cost(self, obj):
        return obj.get_cost()

    get_cost.short_description = 'قیمت کل'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_fullname', 'phone', 'status', 'payment_method', 'total_formatted',
                    'created_jalali']
    list_filter = ['status', 'payment_method', 'created', 'paid']
    search_fields = ('order_number', 'phone', 'last_name', 'address')
    inlines = [OrderItemInline]
    list_editable = ('status',)
    readonly_fields = ('order_number', 'subtotal', 'total', 'created', 'updated')
    list_per_page = 20

    # نمایش نام کامل مشتری
    def customer_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    customer_fullname.short_description = 'نام مشتری'

    # فرمت قیمت
    def total_formatted(self, obj):
        return f"{obj.total:,} تومان"

    total_formatted.short_description = 'مبلغ کل'

    # بهینه‌سازی کوئری (جلوگیری از N+1 اگر یوزر را صدا زدی)
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    # نمایش تاریخ
    def created_jalali(self, obj):
        return obj.created.strftime("%Y/%m/%d %H:%M")

    created_jalali.short_description = 'تاریخ ثبت'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'provider', 'amount', 'success', 'created_at')
    list_filter = ('provider', 'success')

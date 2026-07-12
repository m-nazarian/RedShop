from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = [
        'code',
        'valid_from',
        'valid_to',
        'discount_display',
        'usage_limit',
        'used_count',
        'active',
    ]
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']
    readonly_fields = ['used_count']

    def discount_display(self, obj):
        return f"{obj.discount}%"

    discount_display.short_description = 'درصد تخفیف'

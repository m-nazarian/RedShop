from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = ['code', 'valid_from', 'valid_to', 'discount_display', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']
    list_editable = ['active']

    @display(description="درصد تخفیف", label=True)
    def discount_display(self, obj):
        return f"{obj.discount}%"

    @display(description="وضعیت", boolean=True)
    def active_badge(self, obj):
        return obj.active
from django.apps import AppConfig


class CouponsConfig(AppConfig):
    label = 'coupons'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.coupons'
    verbose_name = 'تخفیف‌ها'  # ✅ نام فارسی

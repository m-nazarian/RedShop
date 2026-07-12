from django.apps import AppConfig


class CompareConfig(AppConfig):
    label = 'compare'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.compare'
    verbose_name = 'سیستم مقایسه'  # ✅ نام فارسی

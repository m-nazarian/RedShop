from django.apps import AppConfig


class ShopConfig(AppConfig):
    label = 'shop'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shop'
    verbose_name = 'مدیریت محصولات'


    def ready(self):
        import apps.shop.signals
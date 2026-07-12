from django.apps import AppConfig


class OrdersConfig(AppConfig):
    label = 'orders'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'مدیریت سفارشات'

    def ready(self):
        import apps.orders.signals
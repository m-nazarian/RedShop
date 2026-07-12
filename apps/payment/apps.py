from django.apps import AppConfig


class PaymentConfig(AppConfig):
    label = 'payment'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payment'

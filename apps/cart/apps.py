from django.apps import AppConfig


class CartConfig(AppConfig):
    label = 'cart'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cart'

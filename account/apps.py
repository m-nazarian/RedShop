from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "account"
    verbose_name = "مدیریت کاربران"

    def ready(self):
        from . import signals

        self.signals = signals
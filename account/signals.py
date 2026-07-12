from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Account, ShopUser


@receiver(post_save, sender=ShopUser)
def ensure_user_account(sender, instance, **kwargs):
    """برای هر کاربر یک رکورد حساب تکمیلی نگه می‌دارد."""
    Account.objects.get_or_create(user=instance)
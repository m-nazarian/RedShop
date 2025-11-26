from django.db.models.signals import post_save
from django.dispatch import receiver
from account.models import ShopUser, Account


@receiver(post_save, sender=ShopUser)
def create_user_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)

@receiver(post_save, sender=ShopUser)
def save_user_account(sender, instance, **kwargs):
    instance.account.save()
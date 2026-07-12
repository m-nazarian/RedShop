from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Order


@receiver(pre_save, sender=Order)
def send_order_status_update_email(sender, instance, **kwargs):
    """در صورت ارسال سفارش، ایمیل اطلاع‌رسانی ارسال می‌کند."""
    if not instance.pk:
        return

    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if old_order.status == instance.status:
        return

    if instance.status != "shipped":
        return

    if not instance.user.email:
        return

    subject = f"سفارش شما ارسال شد: {instance.order_number}"
    html_message = render_to_string("emails/order_shipped.html", {"order": instance})
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER

    try:
        send_mail(
            subject,
            plain_message,
            from_email,
            [instance.user.email],
            html_message=html_message,
        )
    except Exception:
        # ارسال ایمیل نباید ذخیره سفارش را خراب کند.
        return

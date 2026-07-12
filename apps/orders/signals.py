from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Order, OrderItem
from apps.shop.models import Product

# لیست وضعیت‌هایی که یعنی کالا در انبار موجود نیست (فروخته شده)
SOLD_STATUSES = ['pending', 'processing', 'shipped', 'delivered']
# لیست وضعیت‌هایی که یعنی معامله فسخ شده و کالا باید به انبار برگردد
RETURN_STATUSES = ['canceled', 'refunded']


# ==========================================
# 1. مدیریت موجودی انبار (Inventory) 📦
# ==========================================

@receiver(pre_save, sender=Order)
def update_inventory_on_status_change(sender, instance, **kwargs):
    """
    بررسی می‌کند اگر وضعیت سفارش تغییر کرده، موجودی انبار را آپدیت کند.
    """
    if not instance.pk:
        return

    try:
        old_order = Order.objects.get(pk=instance.pk)
        old_status = old_order.status
        new_status = instance.status
    except Order.DoesNotExist:
        return

    if old_status == new_status:
        return

    # سناریو ۱: سفارش لغو یا مرجوع شده -> بازگرداندن موجودی
    if old_status in SOLD_STATUSES and new_status in RETURN_STATUSES:
        restore_inventory(instance)

    # سناریو ۲: سفارش دوباره فعال شده -> کسر مجدد موجودی
    elif old_status in RETURN_STATUSES and new_status in SOLD_STATUSES:
        deduct_inventory(instance)


def restore_inventory(order):
    for item in order.items.all():
        Product.objects.filter(id=item.product.id).update(
            inventory=F('inventory') + item.quantity
        )


def deduct_inventory(order):
    for item in order.items.all():
        Product.objects.filter(id=item.product.id).update(
            inventory=F('inventory') - item.quantity
        )


@receiver(post_delete, sender=OrderItem)
def restore_inventory_on_delete(sender, instance, **kwargs):
    """
    اگر آیتمی کلاً از دیتابیس پاک شد، موجودی برگردد.
    """
    try:
        if instance.order.status in SOLD_STATUSES:
            Product.objects.filter(id=instance.product.id).update(
                inventory=F('inventory') + instance.quantity
            )
    except:
        pass


# ==========================================
# 2. مدیریت اطلاع‌رسانی (Notifications) 🔔
# ==========================================

@receiver(pre_save, sender=Order)
def send_order_status_update_email(sender, instance, **kwargs):
    """
    اگر وضعیت سفارش به 'ارسال شده' تغییر کرد، ایمیل ارسال کن.
    """
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)

            # فقط اگر وضعیت تغییر کرده بود
            if old_order.status != instance.status:

                # اگر وضعیت جدید "shipped" بود
                if instance.status == 'shipped':
                    if instance.user.email:
                        subject = f'سفارش شما ارسال شد: {instance.order_number}'
                        html_message = render_to_string('emails/order_shipped.html', {'order': instance})
                        plain_message = strip_tags(html_message)
                        from_email = settings.EMAIL_HOST_USER
                        to = instance.user.email

                        try:
                            send_mail(subject, plain_message, from_email, [to], html_message=html_message)
                            print(f"✅ Shipped Email sent to {to}")
                        except Exception as e:
                            print(f"❌ Error sending email: {e}")

        except Order.DoesNotExist:
            pass
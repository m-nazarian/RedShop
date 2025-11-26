from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import Order, OrderItem
from shop.models import Product

# لیست وضعیت‌هایی که یعنی کالا در انبار موجود نیست (فروخته شده)
SOLD_STATUSES = ['pending', 'processing', 'shipped', 'delivered']
# لیست وضعیت‌هایی که یعنی معامله فسخ شده و کالا باید به انبار برگردد
RETURN_STATUSES = ['canceled', 'refunded']


@receiver(pre_save, sender=Order)
def update_inventory_on_status_change(sender, instance, **kwargs):
    """
    این سیگنال قبل از ذخیره تغییرات سفارش اجرا می‌شود.
    بررسی می‌کند اگر وضعیت سفارش تغییر کرده، موجودی انبار را آپدیت کند.
    """
    if not instance.pk:
        # اگر سفارش تازه دارد ساخته می‌شود، کاری نداریم
        # (چون کسر موجودی اولیه را در views.py انجام دادیم)
        return

    try:
        # گرفتن وضعیت قبلی سفارش از دیتابیس (قبل از ذخیره شدن جدید)
        old_order = Order.objects.get(pk=instance.pk)
        old_status = old_order.status
        new_status = instance.status
    except Order.DoesNotExist:
        return

    # اگر وضعیت تغییر نکرده، کاری نکن
    if old_status == new_status:
        return

    # سناریو ۱: سفارش فعال بوده، الان لغو یا مرجوع شده است
    # (باید موجودی برگردد)
    if old_status in SOLD_STATUSES and new_status in RETURN_STATUSES:
        restore_inventory(instance)

    # سناریو ۲: سفارش لغو/مرجوع بوده، الان دوباره فعال (مثلا در حال پردازش) شده
    # (باید دوباره موجودی کم شود)
    elif old_status in RETURN_STATUSES and new_status in SOLD_STATUSES:
        deduct_inventory(instance)


def restore_inventory(order):
    """ بازگرداندن موجودی به انبار """
    for item in order.items.all():
        Product.objects.filter(id=item.product.id).update(
            inventory=F('inventory') + item.quantity
        )


def deduct_inventory(order):
    """ کسر مجدد موجودی از انبار (در صورت فعال‌سازی مجدد سفارش) """
    for item in order.items.all():
        # اینجا میشه چک کرد که آیا موجودی کافی هست یا نه، ولی چون ادمین داره انجام میده
        # فرض میکنیم ادمین میدونه چیکار میکنه و موجودی رو کم میکنیم حتی اگه منفی بشه
        Product.objects.filter(id=item.product.id).update(
            inventory=F('inventory') - item.quantity
        )


# ----------------------------------------------------------
# سیگنال حذف کامل سفارش (Delete)
# ----------------------------------------------------------
@receiver(post_delete, sender=OrderItem)
def restore_inventory_on_delete(sender, instance, **kwargs):
    """
    اگر آیتمی کلاً از دیتابیس پاک شد (مثلا دکمه Delete در ادمین)،
    باید موجودی‌اش برگردد، مگر اینکه سفارش خودش قبلاً لغو شده بوده باشد.
    """
    # چک میکنیم اگر سفارش مربوطه، وضعیتش "لغو/مرجوع" نبوده، موجودی رو برگردون
    # چون اگه لغو شده باشه، قبلاً موجودیش رو برگردوندیم، نباید دوباره اضافه کنیم.

    # نکته: وقتی OrderItem پاک میشه، ممکنه Order هنوز باشه یا اونم در حال پاک شدن باشه.
    try:
        if instance.order.status in SOLD_STATUSES:
            Product.objects.filter(id=instance.product.id).update(
                inventory=F('inventory') + instance.quantity
            )
    except:
        pass
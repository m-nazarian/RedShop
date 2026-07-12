from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from shop.models import Product
from shop.utils.shipping import calculate_post_price


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "در انتظار پرداخت/تایید"),
        ("processing", "در حال پردازش"),
        ("shipped", "ارسال شده"),
        ("delivered", "تحویل داده شده"),
        ("canceled", "لغو شده"),
        ("refunded", "مرجوع شده"),
    )

    PAYMENT_METHODS = (
        ("cod", "پرداخت در محل"),
        ("online", "درگاه بانکی"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
        verbose_name="کاربر",
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="شماره سفارش",
    )
    first_name = models.CharField(max_length=50, verbose_name="نام")
    last_name = models.CharField(max_length=50, verbose_name="نام خانوادگی")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    address = models.CharField(max_length=250, verbose_name="آدرس")
    province = models.CharField(max_length=100, verbose_name="استان")
    city = models.CharField(max_length=100, verbose_name="شهر")
    postal_code = models.CharField(max_length=20, verbose_name="کد پستی")
    address_line = models.TextField(blank=True, null=True, verbose_name="آدرس کامل")

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="cod",
        verbose_name="روش پرداخت",
    )
    paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت",
    )

    subtotal = models.PositiveIntegerField(default=0, verbose_name="جمع کالاها")
    discount_amount = models.PositiveIntegerField(default=0, verbose_name="مبلغ تخفیف")
    coupon_code = models.CharField(max_length=50, blank=True, verbose_name="کد تخفیف")
    shipping_price = models.PositiveIntegerField(default=0, verbose_name="هزینه حمل و نقل")
    post_price = models.PositiveIntegerField(default=0, verbose_name="هزینه پست")
    total = models.PositiveIntegerField(default=0, verbose_name="مبلغ قابل پرداخت")

    created = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created"]

    def __str__(self):
        return f"سفارش {self.order_number} - {self.first_name} {self.last_name}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_post_cost(self):
        weight = sum(item.get_weight() for item in self.items.all())
        return calculate_post_price(weight)

    def get_final_cost(self):
        subtotal = self.subtotal or self.get_total_cost()
        shipping = self.shipping_price or self.post_price or self.get_post_cost()
        discount = min(self.discount_amount or 0, subtotal)
        return max(0, subtotal - discount) + shipping

    @classmethod
    def generate_order_number(cls):
        """شماره‌ای کوتاه و با احتمال برخورد بسیار پایین تولید می‌کند."""
        local_now = timezone.localtime()
        return f"RS{local_now:%y%m%d}{uuid4().hex[:8].upper()}"

    def calculate_totals(self):
        subtotal = self.get_total_cost()
        shipping = self.shipping_price or self.post_price or 0
        discount = min(self.discount_amount or 0, subtotal)

        self.subtotal = subtotal
        self.shipping_price = shipping
        self.post_price = shipping
        self.discount_amount = discount
        self.total = max(0, subtotal - discount) + shipping
        return self.total

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سفارش",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="محصول",
    )
    title = models.CharField(max_length=255, verbose_name="عنوان")
    price = models.PositiveIntegerField(default=0, verbose_name="قیمت")
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    weight = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="وزن محصول",
    )

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.title} × {self.quantity}"

    def get_cost(self):
        return self.price * self.quantity

    def get_weight(self):
        return self.weight * self.quantity


class Transaction(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="سفارش",
    )
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="شناسه تراکنش (Authority)",
    )
    ref_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="کد پیگیری (RefID)",
    )
    provider = models.CharField(max_length=50, default="cod", verbose_name="درگاه پرداخت")
    amount = models.PositiveIntegerField(verbose_name="مبلغ (تومان)")
    success = models.BooleanField(default=False, verbose_name="موفق")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    raw_response = models.JSONField(blank=True, null=True, verbose_name="پاسخ خام بانک")

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.amount}"
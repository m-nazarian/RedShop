from django.conf import settings
from django.db import models, transaction
from account.models import ShopUser
from shop.models import Product
from django.utils import timezone
from shop.utils.shipping import calculate_post_price


User = settings.AUTH_USER_MODEL


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار پرداخت/تایید'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('canceled', 'لغو شده'),
        ('refunded', 'مرجوع شده'),
    )

    PAYMENT_METHODS = (
        ('cod', 'پرداخت در محل'),
        ('online', 'درگاه بانکی'),  # برای آینده
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True, blank=True,
        verbose_name='کاربر'
    )
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=50, verbose_name='نام')
    last_name = models.CharField(max_length=50, verbose_name='نام خانوادگی')
    phone = models.CharField(max_length=20, verbose_name='شماره تماس')
    address = models.CharField(max_length=250, verbose_name='آدرس')
    province = models.CharField(max_length=100, verbose_name='استان')
    city = models.CharField(max_length=100, verbose_name='شهر')
    postal_code = models.CharField(max_length=20, verbose_name='کد پستی')
    address_line = models.TextField(blank=True, null=True)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cod')
    paid = models.BooleanField(default=False, verbose_name='پرداخت شده')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    subtotal = models.PositiveIntegerField(default=0)
    shipping_price = models.PositiveIntegerField(default=0)
    post_price = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"سفارش {self.id} از {self.first_name} {self.last_name} - {self.order_number}"

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created']


    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


    def get_post_cost(self):
        weight = sum(item.get_weight() for item in self.items.all())
        return calculate_post_price(weight)


    def get_final_cost(self):
        price = self.get_post_cost() + self.get_total_cost()
        return price

    @classmethod
    def generate_order_number(cls):
        import datetime, random
        date = datetime.datetime.now().strftime("%Y%m%d")
        rnd = random.randint(10000, 99999)
        return f"ORD{date}{rnd}"

    def calculate_totals(self):
        subtotal = sum([item.price * item.quantity for item in self.items.all()])
        shipping = self.shipping_price or 0
        self.subtotal = subtotal
        self.total = subtotal + shipping
        return self.total


    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    title = models.CharField(max_length=255)  # نگهداری عنوان برای تاریخچه
    price = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)
    weight = models.DecimalField(max_digits=12, decimal_places=0,default=0)


    def __str__(self):
        return f"{self.title} x {self.quantity}"


    def get_cost(self):
        return self.price * self.quantity


    def get_weight(self):
        return self.weight * self.quantity


class Transaction(models.Model):
    # برای درگاه‌های آنلاین یا لاگ تراکنشِ COD
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    provider = models.CharField(max_length=50, default='cod')
    amount = models.PositiveIntegerField()
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.provider} - {self.amount}"
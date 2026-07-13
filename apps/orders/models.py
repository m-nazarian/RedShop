
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.shop.models import Product
from apps.shop.utils.shipping import calculate_post_price


class Order(models.Model):
    """Financial order snapshot.

    Orders are accounting records. They must survive user deletion and product
    deletion, because invoices, stock movements, payment callbacks, and support
    workflows depend on historical data remaining available.
    """

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_PAYMENT_REVIEW = "payment_review"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELED = "canceled"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending payment/approval"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PAYMENT_REVIEW, "Payment review required"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELED, "Canceled"),
        (STATUS_REFUNDED, "Refunded"),
    )

    PAYMENT_METHOD_COD = "cod"
    PAYMENT_METHOD_ONLINE = "online"

    PAYMENT_METHODS = (
        (PAYMENT_METHOD_COD, "Cash on delivery"),
        (PAYMENT_METHOD_ONLINE, "Online payment"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
        verbose_name="User",
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Order number",
    )
    first_name = models.CharField(max_length=50, verbose_name="First name")
    last_name = models.CharField(max_length=50, verbose_name="Last name")
    phone = models.CharField(max_length=20, verbose_name="Phone")
    address = models.CharField(max_length=250, verbose_name="Address")
    province = models.CharField(max_length=100, verbose_name="Province")
    city = models.CharField(max_length=100, verbose_name="City")
    postal_code = models.CharField(max_length=20, verbose_name="Postal code")
    address_line = models.TextField(blank=True, null=True, verbose_name="Full address")

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default=PAYMENT_METHOD_COD,
        verbose_name="Payment method",
    )
    paid = models.BooleanField(default=False, verbose_name="Paid")
    stock_released = models.BooleanField(
        default=False,
        verbose_name="Stock released",
        help_text="Prevents returning reserved inventory more than once.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name="Status",
    )

    subtotal = models.PositiveIntegerField(default=0, verbose_name="Subtotal")
    discount_amount = models.PositiveIntegerField(default=0, verbose_name="Discount")
    coupon_code = models.CharField(max_length=50, blank=True, verbose_name="Coupon code")
    coupon_released = models.BooleanField(
        default=False,
        verbose_name="Coupon usage released",
        help_text="Prevents decrementing coupon usage more than once.",
    )
    shipping_price = models.PositiveIntegerField(default=0, verbose_name="Shipping")
    post_price = models.PositiveIntegerField(default=0, verbose_name="Post price")
    total = models.PositiveIntegerField(default=0, verbose_name="Total")

    created = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    updated = models.DateTimeField(auto_now=True, verbose_name="Updated")
    canceled_at = models.DateTimeField(blank=True, null=True, verbose_name="Canceled at")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(discount_amount__lte=models.F("subtotal")),
                name="order_discount_lte_subtotal",
            ),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.first_name} {self.last_name}"

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
        """Generate a short human-readable order number with a low collision risk."""
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
        verbose_name="Order",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
        blank=True,
        verbose_name="Product",
    )
    title = models.CharField(max_length=255, verbose_name="Title")
    price = models.PositiveIntegerField(default=0, verbose_name="Price")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    weight = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="Weight",
    )

    class Meta:
        verbose_name = "Order item"
        verbose_name_plural = "Order items"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="orderitem_quantity_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(weight__gte=0),
                name="orderitem_weight_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.title} x {self.quantity}"

    def get_cost(self):
        return self.price * self.quantity

    def get_weight(self):
        return self.weight * self.quantity


class Transaction(models.Model):
    """Payment provider transaction attached to an immutable order record."""

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_CANCELED = "canceled"

    PAYMENT_STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELED, "Canceled"),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Order",
    )
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Authority",
    )
    ref_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="RefID",
    )
    provider = models.CharField(max_length=50, default="cod", verbose_name="Provider")
    amount = models.PositiveIntegerField(verbose_name="Amount")
    success = models.BooleanField(default=False, verbose_name="Success")
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated")
    raw_response = models.JSONField(blank=True, null=True, verbose_name="Raw response")

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["provider", "transaction_id"],
                name="orders_tran_provide_6d8575_idx",
            ),
            models.Index(
                fields=["order", "status"],
                name="orders_tran_order_i_3c7d44_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "transaction_id"],
                condition=(
                    models.Q(transaction_id__isnull=False)
                    & ~models.Q(transaction_id="")
                ),
                name="uniq_tx_provider_authority",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="paid", success=True)
                    | (~models.Q(status="paid") & models.Q(success=False))
                ),
                name="tx_paid_success_consistent",
            ),
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.amount}"

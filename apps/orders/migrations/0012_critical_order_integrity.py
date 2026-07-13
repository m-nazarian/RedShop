
from django.conf import settings
from django.db import migrations, models
from django.db.models import Count, F, Q
import django.db.models.deletion


def normalize_existing_financial_rows(apps, schema_editor):
    """Normalize historical rows before constraints are added."""
    Order = apps.get_model("orders", "Order")
    Transaction = apps.get_model("orders", "Transaction")

    Order.objects.filter(discount_amount__gt=F("subtotal")).update(
        discount_amount=F("subtotal")
    )

    Transaction.objects.filter(success=True).exclude(status="paid").update(
        status="paid"
    )
    Transaction.objects.filter(status="paid", success=False).update(success=True)

    duplicate_authorities = list(
        Transaction.objects.exclude(transaction_id__isnull=True)
        .exclude(transaction_id="")
        .values("provider", "transaction_id")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)[:10]
    )
    if duplicate_authorities:
        raise RuntimeError(
            "Duplicate payment authorities must be resolved before migration: "
            f"{duplicate_authorities}"
        )


def noop_reverse(apps, schema_editor):
    """The data normalization step is intentionally not reversible."""


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0011_order_coupon_released"),
        ("shop", "0021_align_product_fields"),
    ]

    operations = [
        migrations.RunPython(
            normalize_existing_financial_rows,
            reverse_code=noop_reverse,
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending payment/approval"),
                    ("processing", "Processing"),
                    ("payment_review", "Payment review required"),
                    ("shipped", "Shipped"),
                    ("delivered", "Delivered"),
                    ("canceled", "Canceled"),
                    ("refunded", "Refunded"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order_items",
                to="shop.product",
                verbose_name="Product",
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions",
                to="orders.order",
                verbose_name="Order",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(discount_amount__lte=F("subtotal")),
                name="order_discount_lte_subtotal",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="orderitem_quantity_gte_1",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=Q(weight__gte=0),
                name="orderitem_weight_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="transaction",
            constraint=models.UniqueConstraint(
                condition=Q(transaction_id__isnull=False) & ~Q(transaction_id=""),
                fields=("provider", "transaction_id"),
                name="uniq_tx_provider_authority",
            ),
        ),
        migrations.AddConstraint(
            model_name="transaction",
            constraint=models.CheckConstraint(
                condition=(
                    Q(status="paid", success=True)
                    | (~Q(status="paid") & Q(success=False))
                ),
                name="tx_paid_success_consistent",
            ),
        ),
    ]

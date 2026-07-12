from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0008_alter_orderitem_options_alter_transaction_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="coupon_code",
            field=models.CharField(blank=True, max_length=50, verbose_name="کد تخفیف"),
        ),
        migrations.AddField(
            model_name="order",
            name="discount_amount",
            field=models.PositiveIntegerField(default=0, verbose_name="مبلغ تخفیف"),
        ),
        migrations.AlterField(
            model_name="order",
            name="subtotal",
            field=models.PositiveIntegerField(default=0, verbose_name="جمع کالاها"),
        ),
        migrations.AlterField(
            model_name="order",
            name="total",
            field=models.PositiveIntegerField(default=0, verbose_name="مبلغ قابل پرداخت"),
        ),
    ]
# Generated manually during payment lifecycle hardening.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0009_order_coupon_code_order_discount_amount"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="stock_released",
            field=models.BooleanField(
                default=False,
                help_text="برای سفارش‌های لغوشده مشخص می‌کند موجودی کالاها قبلاً به انبار برگشته است.",
                verbose_name="موجودی آزاد شده",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="canceled_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="زمان لغو"),
        ),
        migrations.AddField(
            model_name="transaction",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "در انتظار نتیجه"),
                    ("paid", "پرداخت موفق"),
                    ("failed", "پرداخت ناموفق"),
                    ("canceled", "لغو شده"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
                verbose_name="وضعیت تراکنش",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی"),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["provider", "transaction_id"], name="orders_tran_provide_6d8575_idx"),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["order", "status"], name="orders_tran_order_i_3c7d44_idx"),
        ),
    ]

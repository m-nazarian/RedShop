
from django.db import migrations, models
from django.db.models import Count, F, Q


def normalize_product_domain_data(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    ProductFeatureValue = apps.get_model("shop", "ProductFeatureValue")

    Product.objects.filter(off__gt=F("price")).update(off=F("price"))
    Product.objects.filter(new_price__gt=F("price")).exclude(new_price=0).update(
        new_price=F("price")
    )

    duplicate_pairs = (
        ProductFeatureValue.objects.values("product_id", "feature_id")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
    )

    for pair in duplicate_pairs:
        rows = list(
            ProductFeatureValue.objects.filter(
                product_id=pair["product_id"],
                feature_id=pair["feature_id"],
            ).order_by("id")
        )

        keeper = rows[0]
        values = []

        for row in rows:
            value = (row.value or "").strip()
            if value and value not in values:
                values.append(value)

        if values:
            keeper.value = " | ".join(values)[:250]
            keeper.save(update_fields=["value"])

        ProductFeatureValue.objects.filter(id__in=[row.id for row in rows[1:]]).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0021_align_product_fields"),
    ]

    operations = [
        migrations.RunPython(normalize_product_domain_data, noop_reverse),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=Q(off__lte=F("price")),
                name="product_discount_lte_price",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=Q(new_price=0) | Q(new_price__lte=F("price")),
                name="product_new_price_valid",
            ),
        ),
        migrations.AddIndex(
            model_name="productfeaturevalue",
            index=models.Index(
                fields=["product", "feature"],
                name="shop_pfv_prod_feature_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="productfeaturevalue",
            constraint=models.UniqueConstraint(
                fields=["product", "feature"],
                name="uniq_product_feature_value",
            ),
        ),
        migrations.AddConstraint(
            model_name="productcomment",
            constraint=models.CheckConstraint(
                condition=Q(score__gte=1) & Q(score__lte=5),
                name="product_comment_score_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="productcomment",
            constraint=models.CheckConstraint(
                condition=Q(suggest__in=["yes", "no", "none"]),
                name="product_comment_suggest_valid",
            ),
        ),
    ]

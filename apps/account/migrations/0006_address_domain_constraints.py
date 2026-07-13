
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def normalize_default_addresses(apps, schema_editor):
    Address = apps.get_model("account", "Address")

    default_user_ids = (
        Address.objects.filter(is_default=True)
        .values_list("user_id", flat=True)
        .distinct()
    )

    for user_id in default_user_ids:
        defaults = list(
            Address.objects.filter(user_id=user_id, is_default=True)
            .order_by("id")
            .values_list("id", flat=True)
        )

        if len(defaults) > 1:
            Address.objects.filter(id__in=defaults[1:]).update(is_default=False)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("account", "0005_alter_shopuser_options_alter_shopuser_address_and_more"),
    ]

    operations = [
        migrations.RunPython(normalize_default_addresses, noop_reverse),
        migrations.AddIndex(
            model_name="address",
            index=models.Index(
                fields=["user", "is_default"],
                name="account_addr_user_def_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="address",
            constraint=models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="uniq_default_address_per_user",
            ),
        ),
    ]

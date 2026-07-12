from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F, Q
from django.utils import timezone


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='کد تخفیف')
    valid_from = models.DateTimeField(verbose_name='معتبر از')
    valid_to = models.DateTimeField(verbose_name='معتبر تا')
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='درصد تخفیف'
    )
    active = models.BooleanField(default=True, verbose_name='فعال')
    usage_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='سقف تعداد مصرف',
        help_text='اگر خالی باشد، محدودیت تعداد مصرف ندارد.'
    )
    used_count = models.PositiveIntegerField(default=0, verbose_name='تعداد مصرف‌شده')

    def __str__(self):
        return self.code

    @classmethod
    def usable_queryset(cls, now=None):
        now = now or timezone.now()
        return cls.objects.filter(
            active=True,
            valid_from__lte=now,
            valid_to__gte=now,
        ).filter(
            Q(usage_limit__isnull=True) | Q(used_count__lt=F('usage_limit'))
        )

    def has_remaining_uses(self):
        return self.usage_limit is None or self.used_count < self.usage_limit

    def is_usable(self, now=None):
        now = now or timezone.now()
        return (
            self.active
            and self.valid_from <= now <= self.valid_to
            and self.has_remaining_uses()
        )

    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django_resized import ResizedImageField

# Create your models here.

class ShopUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Users must have a valid phone number')

        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)


class ShopUser(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=11, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name='ایمیل')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = ShopUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.phone




class Account(models.Model):
    user = models.OneToOneField(ShopUser, on_delete=models.CASCADE, related_name="account", verbose_name="کاربر")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="تاریخ تولد")
    payment_card_number = models.CharField(max_length=250, null=True, blank=True, verbose_name="شماره حساب بانکی")
    photo = ResizedImageField(upload_to="account_images/", size=[500, 500], quality=75, crop=['middle', 'center'],blank=True, null=True, verbose_name="تصویر پروفایل")
    id_card = models.CharField(max_length=250, null=True, blank=True, verbose_name="کد ملی")

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name


    @property
    def display_name(self):
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.phone  # اگر نام و نام خانوادگی خالی بود شماره موبایل نمایش داده شود


    class Meta:

        verbose_name = "اکانت"
        verbose_name_plural = "اکانت ها"


class Address(models.Model):
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE, related_name="addresses")
    first_name = models.CharField(max_length=150, verbose_name="نام گیرنده")
    last_name = models.CharField(max_length=150, verbose_name="نام خانوادگی گیرنده")
    phone = models.CharField(max_length=11, verbose_name="شماره تماس")
    province = models.CharField(max_length=100, verbose_name="استان")
    city = models.CharField(max_length=100, verbose_name="شهر")
    postal_code = models.CharField(max_length=10, verbose_name="کد پستی")
    address_line = models.TextField(verbose_name="آدرس کامل")
    is_default = models.BooleanField(default=False, verbose_name="آدرس پیش‌فرض")

    def __str__(self):
        return f"{self.city} - {self.address_line[:20]}..."

    class Meta:
        verbose_name = "آدرس"
        verbose_name_plural = "آدرس‌ها"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
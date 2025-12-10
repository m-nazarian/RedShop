from django.conf import settings
from django.db import models
from django.urls import reverse
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from slugify import slugify
from django.apps import apps
from django.db.models import Avg


class Category(MPTTModel):
    name = models.CharField(max_length=100, verbose_name="نام دسته")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="اسلاگ (slug)")
    photo = models.ImageField(upload_to="category_images/",blank=True, null=True, verbose_name="تصویر دسته بندی")
    created = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="دسته والد"
    )

    class MPTTMeta:
        order_insertion_by = ['created']

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"



    def __str__(self):
        return self.name


    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='نام برند')
    About_the_company = models.TextField(max_length=6500, verbose_name="درباره کمپانی")
    established = models.CharField(max_length=100, verbose_name="زمان تاسیس")

    class Meta:
        verbose_name = 'برند'
        verbose_name_plural = 'برندها'

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='نام رنگ')
    hex_code = models.CharField(max_length=7,blank=True, null=True, verbose_name='کد رنگ')

    class Meta:
        verbose_name = 'رنگ'
        verbose_name_plural = 'رنگ‌ها'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='دسته بندی')
    name = models.CharField(max_length=250, verbose_name='نام')
    slug = models.SlugField(max_length=250, verbose_name='اسلاگ')
    description = models.TextField(max_length=6500, verbose_name='توضیحات')
    inventory = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    price = models.PositiveIntegerField(default=0, verbose_name='قیمت')
    weight = models.PositiveIntegerField(default=0, verbose_name='وزن')

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', verbose_name='برند')
    colors = models.ManyToManyField(Color, related_name='products', blank=True, verbose_name='رنگ‌ها')

    off = models.PositiveIntegerField(default=0, verbose_name='تخفیف')
    new_price = models.PositiveIntegerField(default=0, verbose_name='قیمت پس از تخفیف')
    created = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    def save(self, *args, **kwargs):
        if not self.slug:  # اگر هنوز اسلاگ وارد نشده بود
            # تبدیل عنوان فارسی به فینگلیش و ساخت اسلاگ
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_grouped_features(self):
        feature_values = self.feature_values.select_related(
            'feature', 'feature__group'
        ).order_by('feature__group__id')

        grouped_features = {}
        for fv in feature_values:
            group_name = fv.feature.group.name if fv.feature.group else "سایر مشخصات"
            if group_name not in grouped_features:
                grouped_features[group_name] = []
            grouped_features[group_name].append({
                'name': fv.feature.name,
                'value': fv.value
            })
        return grouped_features


    def get_average_score(self):
        """ محاسبه میانگین امتیاز نظرات تایید شده """
        avg = self.comments.filter(active=True).aggregate(Avg('score'))['score__avg']
        if avg is not None:
            return round(avg, 1)  # تا یک رقم اعشار گرد کن (مثلاً 4.5)
        return 0

    def get_review_count(self):
        """ تعداد نظرات تایید شده """
        return self.comments.filter(active=True).count()


    def get_discount_percent(self):
        """
        محاسبه درصد تخفیف بر اساس قیمت اصلی و مبلغ تخفیف
        """
        if self.price > 0 and self.off > 0:
            # فرمول: (تخفیف تقسیم بر قیمت) ضرب در ۱۰۰
            percent = (self.off / self.price) * 100
            return int(percent)  # برگرداندن عدد صحیح (مثلا 20)
        return 0


    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]
        verbose_name = 'محصول'
        verbose_name_plural = 'محصول‌ها'

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])

    def __str__(self):
        return self.name


class Image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name="محصول")
    file = models.ImageField(upload_to="product_image/%Y/%m/%d")
    title = models.CharField(max_length=250, verbose_name="عنوان", null=True, blank=True)
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created'])
        ]
        verbose_name = "تصویر"
        verbose_name_plural = "تصویر ها"

    def __str__(self):
        return self.title if self.title else f"تصویر {self.product.name}"


# ===============================
# 🔹 مدل‌های جدید برای ویژگی‌های پویا
# ===============================
class FeatureGroup(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='feature_groups',
        verbose_name='دسته'
    )
    name = models.CharField(max_length=250, verbose_name='نام گروه ویژگی')

    class Meta:
        verbose_name = 'گروه ویژگی'
        verbose_name_plural = 'گروه‌های ویژگی'
        ordering = ['id']

    def __str__(self):
        return f"{self.category} - {self.name}"



class CategoryFeature(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_features', verbose_name='دسته')
    group = models.ForeignKey(FeatureGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='features',
                              verbose_name='گروه ویژگی')
    name = models.CharField(max_length=250, verbose_name='نام ویژگی')
    created = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    class Meta:
        ordering = ['group', 'id']
        verbose_name = "ویژگی دسته"
        verbose_name_plural = "ویژگی‌های دسته"

    def __str__(self):
        return f"{self.category} - {self.name}"


class ProductFeatureValue(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='feature_values', verbose_name='محصول')
    feature = models.ForeignKey(CategoryFeature, on_delete=models.CASCADE, related_name='values', verbose_name='ویژگی')
    value = models.CharField(max_length=250, verbose_name='مقدار ویژگی')

    class Meta:
        verbose_name = "مقدار ویژگی محصول"
        verbose_name_plural = "مقادیر ویژگی‌های محصول"

    def __str__(self):
        return f"{self.product} - {self.feature}: {self.value}"



# ===============================
#           Likes
# ===============================
class CommentLike(models.Model):
    LIKE_STATUS = (
        (True, 'لایک'),
        (False, 'دیس‌لایک'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey('ProductComment', on_delete=models.CASCADE, related_name='likes')
    status = models.BooleanField(choices=LIKE_STATUS, default=True)  # فیلد جدید
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')  # هر کاربر فقط یک واکنش (لایک یا دیس‌لایک)
        verbose_name = 'واکنش به نظر'
        verbose_name_plural = 'واکنش‌های کاربران'

# ===============================
#           Comments
# ===============================
class ProductComment(models.Model):
    RATING_CHOICES = (
        (1, 'خیلی بد'),
        (2, 'بد'),
        (3, 'معمولی'),
        (4, 'خوب'),
        (5, 'عالی'),
    )

    # ✅ تغییر مهم: تبدیل پیشنهاد به ۳ حالت
    SUGGEST_CHOICES = (
        ('yes', 'پیشنهاد می‌کنم'),
        ('no', 'پیشنهاد نمی‌کنم'),
        ('none', 'نظری ندارم'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments', verbose_name='محصول')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments',
                             verbose_name='کاربر')

    score = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5, verbose_name='امتیاز')
    text = models.TextField(verbose_name='متن نظر')

    # ✅ فیلد پیشنهاد آپدیت شد
    suggest = models.CharField(max_length=10, choices=SUGGEST_CHOICES, default='none', verbose_name='پیشنهاد خرید')

    active = models.BooleanField(default=False, verbose_name='تایید شده')
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')

    # --- متدهای شمارشگر برای دسترسی راحت ---
    @property
    def likes_count(self):
        return self.likes.filter(status=True).count()

    @property
    def dislikes_count(self):
        return self.likes.filter(status=False).count()

    @property
    def is_buyer(self):
        Order = apps.get_model('orders', 'Order')
        OrderItem = apps.get_model('orders', 'OrderItem')
        return OrderItem.objects.filter(
            order__user=self.user,
            product=self.product,
            order__status__in=['processing', 'shipped', 'delivered']
        ).exists()

    @property
    def is_expert(self):
        current_category = self.product.category
        comment_count = ProductComment.objects.filter(
            user=self.user,
            product__category=current_category,
            active=True
        ).count()
        return comment_count >= 10

    class Meta:
        ordering = ['-created']
        verbose_name = 'نظر کاربر'
        verbose_name_plural = 'نظرات کاربران'

    def __str__(self):
        return f"{self.user} - {self.product.name}"


class ProductFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # جلوگیری از تکرار
        verbose_name = 'محصول مورد علاقه'
        verbose_name_plural = 'لیست علاقه‌مندی‌ها'

    def __str__(self):
        return f"{self.user} -> {self.product}"
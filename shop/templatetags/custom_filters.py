from django import template
from django.utils.text import slugify
from ..models import Product, Category

register = template.Library()

# ----------------------------------------------------------------------
# ۱. فیلتر add_prefix
# ----------------------------------------------------------------------

@register.filter
def add_prefix(value, prefix):
    """
    پیشوندی را به ابتدای یک رشته اضافه می‌کند.
    """
    return f"{prefix}{value}"


# ----------------------------------------------------------------------
# ۲. فیلتر slugify_fa
# ----------------------------------------------------------------------

@register.filter
def slugify_fa(value):
    """
    رشته را به اسلاگ تبدیل می‌کند و کاراکترهای فارسی را حفظ می‌کند.
    """
    # از تابع slugify داخلی جنگو استفاده می‌کنیم.
    return slugify(value, allow_unicode=True)

@register.filter
def money_format(value):
    """
    تبدیل عدد به فرمت سه رقم جدا شده با ارقام فارسی.
    مثال: 10000 -> ۱۰،۰۰۰
    """
    if value is None:
        return ""

    try:
        value = int(value)
        # ۱. ابتدا سه رقم سه رقم با کاما جدا می‌کنیم (فرمت انگلیسی)
        formatted = f"{value:,}"

        # ۲. جدول تبدیل اعداد انگلیسی به فارسی
        translation_table = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

        # ۳. اعمال تبدیل
        return formatted.translate(translation_table)

    except (ValueError, TypeError):
        # اگر مقدار ورودی عدد نبود، خودش را برگردان
        return value


@register.filter
def fa_number(value):
    """
    تبدیل اعداد انگلیسی به فارسی
    مثال: 123 -> ۱۲۳
    """
    if value is None:
        return ""

    value = str(value)
    translation_table = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return value.translate(translation_table)


@register.filter
def multiply(value, arg):
    """ضرب دو عدد"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def get_item(dictionary, key):
    """
    اجازه می‌دهد تا در تمپلیت به یک کلید دیکشنری با متغیر دسترسی پیدا کنیم.
    مثال: {{my_dict|get_item:my_key}}
    """
    if not dictionary:
        return None
    return dictionary.get(key)

@register.filter
def is_in_list(value, item_list):
    """
    بررسی می‌کند که آیا یک مقدار در لیست وجود دارد یا خیر.
    """
    if not item_list:
        return False
    # مقادیر value (مثل ID) را به رشته تبدیل می‌کنیم تا با لیست رشته‌ای AJAX مقایسه شود
    return str(value) in item_list


# ===== آخرین پست‌ها =====
@register.inclusion_tag("partials/latest_product.html")
def latest_product(count=5, category_slug=None):
    # ✅ بهینه‌سازی: استفاده از prefetch_related برای تصاویر
    l_products = Product.objects.prefetch_related('images').order_by("-created")
    if category_slug:
        l_products = l_products.filter(category__slug=category_slug)

    l_products = l_products[:count]
    context = {"l_products": l_products}
    return context



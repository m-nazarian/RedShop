from django.db.models import Q, Count
from .models import Brand, Color, ProductFeatureValue, Product
from collections import OrderedDict


# --------------------------------------------------------------------------
# توابع کمکی (Helpers)
# --------------------------------------------------------------------------

FILTER_ORDER = OrderedDict([
    ('price', 'بر اساس قیمت'),
    ('brand', 'بر اساس شرکت سازنده'),
    ('color', 'بر اساس رنگ'),

])


def get_dynamic_features(products_queryset):
    feature_values = ProductFeatureValue.objects.filter(
        product__in=products_queryset
    ).select_related('feature', 'feature__group', 'feature__category')

    dynamic_features = {}
    for fv in feature_values:
        feature_id = fv.feature.id
        feature_name = fv.feature.name
        feature_value = fv.value

        if feature_id not in dynamic_features:
            dynamic_features[feature_id] = {
                'name': feature_name,
                'values': set()
            }
        dynamic_features[feature_id]['values'].add(feature_value)

    for data in dynamic_features.values():
        data['values'] = sorted(list(data['values']))

    return dynamic_features


def assemble_filters(request, products, dynamic_features_data):
    brands = Brand.objects.filter(products__in=products).distinct()
    colors = Color.objects.filter(products__in=products).distinct()

    filter_data_static = {
        'price': {'min': 0, 'max': 500_000_000},
        'brand': brands,
        'color': colors,
    }

    dynamic_features_by_name = {
        data['name']: {'id': feature_id, 'values': data['values']}
        for feature_id, data in dynamic_features_data.items()
    }

    ordered_filters = []

    for key, title in FILTER_ORDER.items():
        if key in filter_data_static:
            ordered_filters.append({
                'key': key,
                'title': title,
                'data': filter_data_static.get(key),
                'type': 'static'
            })
        elif key in dynamic_features_by_name:
            feature_data = dynamic_features_by_name[key]
            ordered_filters.append({
                'key': f"feature_{feature_data['id']}",
                'title': title,
                'data': feature_data['values'],
                'type': 'dynamic'
            })

    return ordered_filters


def sort_products(products, sort_option):
    if sort_option == 'cheapest':
        return products.order_by('new_price')
    elif sort_option == 'expensive':
        return products.order_by('-new_price')
    elif sort_option == 'name':
        return products.order_by('name')
    else:
        return products.order_by('-created')


def is_staff(user):
    return user.is_staff


def apply_filters(products, data):
    # 1. فیلترهای ثابت
    if data.get("brand"):
        products = products.filter(brand__id__in=data["brand"])
    if data.get("color"):
        products = products.filter(colors__id__in=data["color"]).distinct()
    if data.get("max_price"):
        try:
            products = products.filter(new_price__lte=int(data["max_price"]))
        except (ValueError, TypeError):
            pass

    # 2. فیلترهای داینامیک
    for key, values in data.items():
        if key.startswith('feature_') and values:
            try:
                feature_id = int(key.replace('feature_', ''))
                products = products.filter(
                    feature_values__feature_id=feature_id,
                    feature_values__value__in=values
                ).distinct()
            except (ValueError, TypeError):
                pass

    return products


def global_search(query):
    """
    جستجوی همزمان محصولات و پیدا کردن دسته‌بندی مرتبط
    """
    if not query:
        return {'products': [], 'suggested_category': None}

    # ۱. جستجو در محصولات (نام، توضیحات یا برند)
    # از distinct استفاده می‌کنیم تا تکراری نیاید
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(brand__name__icontains=query)
    ).select_related('category', 'brand').prefetch_related('images').distinct()[:5]  # فقط ۵ تای اول

    # ۲. حدس زدن دسته‌بندی مرتبط 🧠
    # اگر محصولاتی پیدا کردیم، ببینیم بیشترشون مال کدوم دسته‌ن؟
    suggested_category = None

    if products.exists():
        # تمام دسته‌های محصولات پیدا شده را می‌گیریم
        # و پرتکرارترین دسته را پیدا می‌کنیم
        categories = [p.category for p in products]

        # پیدا کردن پرتکرارترین (Most Common)
        from collections import Counter
        if categories:
            most_common_cat = Counter(categories).most_common(1)[0][0]
            suggested_category = {
                'name': most_common_cat.name,
                'slug': most_common_cat.slug,
                'url': most_common_cat.get_absolute_url()
            }

    # ۳. فرمت‌دهی خروجی برای JSON
    results = []
    for p in products:
        results.append({
            'name': p.name,
            'price': p.new_price if p.new_price else p.price,
            'image': p.images.first().file.url if p.images.exists() else '',
            'url': p.get_absolute_url(),
            'category_name': p.category.name
        })

    return {
        'products': results,
        'suggested_category': suggested_category,
        'query': query
    }


def get_frequently_bought_products(user, limit=10):
    """
    محصولاتی که کاربر بیش از یک بار خریده است (به ترتیب تعداد خرید)
    """
    if not user.is_authenticated:
        return []

    # پیدا کردن محصولاتی که در سفارش‌های موفق کاربر هستند
    # و تعداد تکرارشان در OrderItem ها بیشتر از 1 است
    products = Product.objects.select_related(
        'category',
        'brand',
    ).prefetch_related(
        'images',
    ).filter(
        order_items__order__user=user,
        order_items__order__paid=True  # فقط خریدهای موفق
    ).annotate(
        buy_count=Count('order_items')
    ).filter(
        buy_count__gt=1  # حداقل 2 بار خریده شده باشد
    ).order_by('-buy_count')[:limit]

    return products


def get_wishlist_products(user, limit=10):
    """
    محصولات موجود در لیست علاقه‌مندی‌های کاربر
    """
    if not user.is_authenticated:
        return []

    return Product.objects.filter(
        favorited_by__user=user
    ).order_by('-favorited_by__created')[:limit]

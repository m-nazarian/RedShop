from .models import Brand, Color, ProductFeatureValue
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
    ).select_related('feature')

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
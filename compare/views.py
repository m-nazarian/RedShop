from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from shop.models import Product, ProductFeatureValue, FeatureGroup, CategoryFeature
from django.template.loader import render_to_string
from .compare import Compare


def get_comparison_data(products):
    """
    الگوریتم ساخت جدول مقایسه
    خروجی: لیستی از گروه‌ها و ویژگی‌ها که مقادیر هر محصول در آن مرتب شده است.
    """
    if not products:
        return []

    # 1. پیدا کردن تمام ویژگی‌های موجود در این محصولات
    # (فقط ویژگی‌هایی که حداقل یکی از محصولات دارد را می‌آوریم)
    feature_ids = ProductFeatureValue.objects.filter(product__in=products) \
        .values_list('feature_id', flat=True).distinct()

    features = CategoryFeature.objects.filter(id__in=feature_ids).select_related('group').order_by('group__id', 'id')

    # 2. ساخت ساختار داده نهایی
    comparison_table = []

    current_group = None
    group_data = {'group': None, 'rows': []}

    for feature in features:
        # مدیریت گروه‌بندی
        if feature.group != current_group:
            if group_data['rows']:  # اگر گروه قبلی پر بود ذخیره‌اش کن
                comparison_table.append(group_data)

            current_group = feature.group
            group_name = current_group.name if current_group else "سایر ویژگی‌ها"
            group_data = {'group': group_name, 'rows': []}

        # جمع‌آوری مقادیر این ویژگی برای تک‌تک محصولات (به ترتیب)
        row_values = []
        for product in products:
            # سعی می‌کنیم مقدار را پیدا کنیم
            value_obj = ProductFeatureValue.objects.filter(product=product, feature=feature).first()
            row_values.append(value_obj.value if value_obj else "-")

        group_data['rows'].append({
            'name': feature.name,
            'values': row_values
        })

    # افزودن آخرین گروه
    if group_data['rows']:
        comparison_table.append(group_data)

    return comparison_table


def show_compare(request):
    compare = Compare(request)
    products = list(compare)  # تبدیل به لیست برای حفظ ترتیب و استفاده چندباره

    comparison_table = get_comparison_data(products)

    context = {
        'products': products,
        'comparison_table': comparison_table,
    }

    # اگر درخواست AJAX بود، فقط جدول را بفرست (برای حذف و رفرش)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'compare/partials/compare_table.html', context)

    # اگر درخواست معمولی بود، کل صفحه را بفرست
    return render(request, 'compare/detail.html', context)


@require_POST
def add_to_compare(request, product_id):
    compare = Compare(request)
    product = get_object_or_404(Product, id=product_id)

    # چک کردن دسته‌بندی
    current_products = list(compare)
    if current_products:
        first_product = current_products[0]
        if product.category.get_root() != first_product.category.get_root():
            return JsonResponse({
                'success': False,
                'message': f'شما فقط می‌توانید محصولات گروه "{first_product.category.get_root().name}" را با هم مقایسه کنید.'
            })

    added, message = compare.add(product)
    return JsonResponse({
        'success': added,
        'message': message,
        'count': len(compare)
    })


@require_POST
def remove_from_compare(request, product_id):
    compare = Compare(request)
    product = get_object_or_404(Product, id=product_id)
    compare.remove(product)

    return JsonResponse({'success': True, 'message': 'محصول حذف شد.'})


@login_required
def compare_suggestions(request):
    compare = Compare(request)
    current_products = list(compare)

    if not current_products:
        html = '<p class="p-4 text-center text-gray-500">ابتدا یک محصول را از لیست محصولات به مقایسه اضافه کنید.</p>'
        return JsonResponse({'html_form': html})

    root_category = current_products[0].category.get_root()
    current_ids = [p.id for p in current_products]

    # کوئری پایه: محصولات هم‌دسته و غیر تکراری
    products_qs = Product.objects.filter(
        category__in=root_category.get_descendants(include_self=True)
    ).exclude(id__in=current_ids)

    # ✅ منطق جستجو
    search_query = request.GET.get('q')
    if search_query:
        # اگر کاربر سرچ کرد، فیلتر کن و محدودیت تعداد را بردار (یا بیشتر کن)
        suggested_products = products_qs.filter(name__icontains=search_query).order_by('-created')[:20]
    else:
        # اگر سرچ نکرد، ۱۰ تا محصول آخر را نشان بده
        suggested_products = products_qs.order_by('-created')[:10]

    html = render_to_string('compare/partials/suggestions.html', {'products': suggested_products}, request=request)

    return JsonResponse({'html_form': html})
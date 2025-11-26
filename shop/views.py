from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404
from .models import Category, Product, CategoryFeature
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
import json
from .services import sort_products, get_dynamic_features, assemble_filters, is_staff, apply_filters


# --------------------------------------------------------------------------
# Views اصلی
# --------------------------------------------------------------------------
def index(request):
    """ نمایش صفحه اصلی. """
    parent_categories = Category.objects.filter(parent=None)
    context = {
        'parent_categories': parent_categories,
    }
    return render(request, "shop/index.html", context)


def product_list(request, category_slug=None):
    """
    نمایش لیست محصولات برای بارگذاری اولیه صفحه (GET request).
    """
    category = None
    products = Product.objects.prefetch_related('colors', 'images').all()
    categories = Category.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category__in=category.get_descendants(include_self=True))

    sort_option = request.GET.get('sort', 'newest')
    products = sort_products(products, sort_option)

    dynamic_features_data = get_dynamic_features(products)

    current_selections = {}
    ordered_filters = assemble_filters(request, products, dynamic_features_data)

    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'sort_option': sort_option,
        'ordered_filters': ordered_filters,
        'current_selections': current_selections,
    }
    return render(request, 'shop/list.html', context)

def product_detail(request, id, slug):
    """ نمایش جزئیات یک محصول. """
    product = get_object_or_404(Product, id=id, slug=slug)

    grouped_features = product.get_grouped_features()

    context = {
        'product': product,
        'grouped_features': grouped_features,
    }
    return render(request, 'shop/detail.html', context)


def filter_products(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    products = Product.objects.prefetch_related('colors', 'images').all()

    products = apply_filters(products, data)

    sort_option = data.get('sort', 'newest')
    products = sort_products(products, sort_option)

    dynamic_features_data = get_dynamic_features(products)
    ordered_filters = assemble_filters(request, products, dynamic_features_data)

    html_products = render_to_string("partials/product_list_partials.html", {"products": products})
    html_filters = render_to_string("partials/all_filters_partials.html", {
        "ordered_filters": ordered_filters,
        "current_selections": data
    })

    return JsonResponse({
        "html_products": html_products,
        "html_filters": html_filters
    }, safe=False)




@user_passes_test(is_staff, login_url=None)
def get_category_features(request, category_id):
    print("user is staff : ", request.user.is_staff)
    if category_id is None or category_id == 0:
        return JsonResponse({'features': []})

    try:
        current_category = Category.objects.get(id=category_id)
        ancestors_and_self = current_category.get_ancestors(include_self=True)
        features = CategoryFeature.objects.filter(
            category__in=ancestors_and_self
        ).values('id', 'name').distinct()

        feature_list = list(features)
        return JsonResponse({'features': feature_list})

    except Category.DoesNotExist:
        return JsonResponse({'features': []})
    except Exception as e:
        return JsonResponse({'error': f"Internal Server Error: {str(e)}"}, status=500)



class FilteredAutocompleteJsonView(AutocompleteJsonView):
    def get_queryset(self):
        qs = super().get_queryset()
        term = self.term
        category_id = self.request.GET.get('category_id')
        print("Autocomplete request GET:", self.request.GET)

        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                ancestors_and_self = category.get_ancestors(include_self=True)
                qs = qs.filter(category__in=ancestors_and_self).distinct()
                if term:
                    qs = qs.filter(name__icontains=term)
            except (Category.DoesNotExist, ValueError):
                qs = qs.none()
        else:
            qs = qs.none()

        print("Filtered QS names:", list(qs.values_list('name', flat=True)))
        return qs


@staff_member_required
def categoryfeature_autocomplete(request):
    """
    Autocomplete هوشمند با پشتیبانی از ارث‌بری دسته‌ها.
    """
    category_id = request.GET.get('category_id')
    term = request.GET.get('term', '')  # Select2 پارامتر term میفرسته برای جستجو

    if not category_id:
        return JsonResponse({'results': []})

    try:
        # ۱. پیدا کردن دسته انتخاب شده
        category = Category.objects.get(id=category_id)

        # ۲. گرفتن لیست خود دسته و تمام پدرانش (Ancestors)
        relevant_categories = category.get_ancestors(include_self=True)

        # ۳. فیلتر کردن ویژگی‌ها
        features = CategoryFeature.objects.filter(
            category__in=relevant_categories
        )

        # ۴. اگر کاربر چیزی تایپ کرده، فیلتر کن
        if term:
            features = features.filter(name__icontains=term)

        # ۵. فرمت استاندارد Select2
        results = [
            {'id': f.id, 'text': f"{f.group.name if f.group else 'عمومی'} - {f.name} ({f.category.name})"}
            for f in features
        ]
        return JsonResponse({'results': results})

    except Category.DoesNotExist:
        return JsonResponse({'results': []})
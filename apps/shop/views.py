import json
from collections import OrderedDict
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .forms import ProductCommentForm
from .models import (
    Category, Product, CategoryFeature, CommentLike,
    ProductComment, ProductFavorite
)
from .services import (
    sort_products, get_dynamic_features, assemble_filters,
    apply_filters, global_search, get_frequently_bought_products,
    get_wishlist_products
)


# --------------------------------------------------------------------------
# Views اصلی صفحات
# --------------------------------------------------------------------------

def index(request):
    """
    نمایش صفحه اصلی به همراه اسلایدرهای هوشمند.
    """
    parent_categories = Category.objects.filter(parent=None)

    # دریافت لیست‌های هوشمند (خرید پرتکرار و علاقه‌مندی)
    frequent_products = get_frequently_bought_products(request.user)
    wishlist_products = get_wishlist_products(request.user)

    context = {
        'parent_categories': parent_categories,
        'frequent_products': frequent_products,
        'wishlist_products': wishlist_products,
    }
    return render(request, "shop/index.html", context)


def product_list(request, category_slug=None):
    """
    نمایش لیست محصولات برای بارگذاری اولیه صفحه (GET request).
    """
    category = None
    # کوئری‌ست پایه
    products = Product.objects.prefetch_related('colors', 'images').all()
    categories = Category.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category__in=category.get_descendants(include_self=True))

    # مرتب‌سازی پیش‌فرض
    sort_option = request.GET.get('sort', 'newest')
    products = sort_products(products, sort_option)

    # فیلترها
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
    """
    نمایش جزئیات محصول، نظرات و محصولات مرتبط.
    """
    product = get_object_or_404(Product, id=id, slug=slug)

    grouped_features = product.get_grouped_features()
    comment_form = ProductCommentForm()

    # فقط نظرات فعال
    active_comments = product.comments.filter(active=True)

    # محصولات مرتبط (هم‌دسته، به جز خود محصول، تصادفی)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('?')[:6]

    context = {
        'product': product,
        'grouped_features': grouped_features,
        'comment_form': comment_form,
        'comments': active_comments,
        'related_products': related_products,
    }
    return render(request, 'shop/detail.html', context)


def filter_products(request):
    """
    View مخصوص AJAX برای فیلتر کردن محصولات.
    نکته مهم: لیست فیلترها (سایدبار) نباید با انتخاب کاربر محدود شود.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # 1. لیست پایه (فقط بر اساس دسته‌بندی فیلتر شده، نه انتخاب کاربر)
    base_products = Product.objects.prefetch_related('colors', 'images').all()

    # اگر اسلاگ دسته ارسال شده بود، لیست پایه را محدود به آن دسته کن
    category_slug = data.get('category_slug')
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            base_products = base_products.filter(category__in=category.get_descendants(include_self=True))
        except Category.DoesNotExist:
            pass

    # 2. لیست نهایی (برای نمایش کارت‌های محصول) -> فیلترهای کاربر روی این اعمال می‌شود
    filtered_products = apply_filters(base_products, data)

    # 3. مرتب‌سازی
    sort_option = data.get('sort', 'newest')
    filtered_products = sort_products(filtered_products, sort_option)

    # 4. ساخت گزینه‌های فیلتر (سایدبار)
    base_dynamic_features = get_dynamic_features(base_products)
    ordered_filters = assemble_filters(request, base_products, base_dynamic_features)

    # 5. رندر کردن پارشیال‌ها
    html_products = render_to_string(
        "partials/product_list_partials.html",
        {"products": filtered_products},
        request=request
    )

    html_filters = render_to_string(
        "partials/all_filters_partials.html",
        {
            "ordered_filters": ordered_filters,
            "current_selections": data
        },
        request=request
    )

    return JsonResponse({
        "html_products": html_products,
        "html_filters": html_filters
    }, safe=False)


# --------------------------------------------------------------------------
# API جستجو و اتوکامپلیت
# --------------------------------------------------------------------------

def search_suggestions(request):
    """
    API برای جستجوی زنده (Live Search) در هدر.
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'products': [], 'suggested_category': None})

    data = global_search(query)
    return JsonResponse(data)


@staff_member_required
def categoryfeature_autocomplete(request):
    """
    Autocomplete برای انتخاب ویژگی‌ها در پنل ادمین.
    """
    category_id = request.GET.get('category_id')
    term = request.GET.get('term', '')

    if not category_id:
        return JsonResponse({'results': []})

    try:
        category = Category.objects.get(id=category_id)
        relevant_categories = category.get_ancestors(include_self=True)

        features = CategoryFeature.objects.filter(category__in=relevant_categories)

        if term:
            features = features.filter(name__icontains=term)

        results = [
            {'id': f.id, 'text': f"{f.group.name if f.group else 'عمومی'} - {f.name} ({f.category.name})"}
            for f in features
        ]
        return JsonResponse({'results': results})

    except Category.DoesNotExist:
        return JsonResponse({'results': []})


class FilteredAutocompleteJsonView(AutocompleteJsonView):
    def get_queryset(self):
        qs = super().get_queryset()
        term = self.term
        category_id = self.request.GET.get('category_id')

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
        return qs


def is_staff(user):
    return user.is_staff


@user_passes_test(is_staff, login_url=None)
def get_category_features(request, category_id):
    if category_id is None or category_id == 0:
        return JsonResponse({'features': []})

    try:
        current_category = Category.objects.get(id=category_id)
        ancestors_and_self = current_category.get_ancestors(include_self=True)
        features = CategoryFeature.objects.filter(
            category__in=ancestors_and_self
        ).values('id', 'name').distinct()

        return JsonResponse({'features': list(features)})

    except Category.DoesNotExist:
        return JsonResponse({'features': []})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------------------------------------------------------
# تعاملات کاربر (نظر، لایک، علاقه‌مندی)
# --------------------------------------------------------------------------

@login_required
@require_POST
def add_product_comment(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ProductCommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.product = product
        comment.user = request.user
        comment.save()
        return JsonResponse({'success': True, 'message': 'نظر شما با موفقیت ثبت شد و پس از تایید نمایش داده می‌شود.'})

    return JsonResponse({'success': False, 'errors': form.errors})


@login_required
@require_POST
def like_comment(request, comment_id):
    comment = get_object_or_404(ProductComment, id=comment_id)
    action_type = request.POST.get('type')
    is_like = (action_type == 'like')

    try:
        existing_like = CommentLike.objects.get(user=request.user, comment=comment)
        if existing_like.status == is_like:
            existing_like.delete()  # حذف لایک/دیس‌لایک قبلی
            action = 'removed'
        else:
            existing_like.status = is_like  # تغییر نظر
            existing_like.save()
            action = 'changed'

    except CommentLike.DoesNotExist:
        CommentLike.objects.create(user=request.user, comment=comment, status=is_like)
        action = 'created'

    return JsonResponse({
        'success': True,
        'action': action,
        'likes_count': comment.likes_count,
        'dislikes_count': comment.dislikes_count
    })


@login_required
@require_POST
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = ProductFavorite.objects.get_or_create(user=request.user, product=product)

    if not created:
        favorite.delete()
        status = 'removed'
    else:
        status = 'added'

    return JsonResponse({'success': True, 'status': status})


# --------------------------------------------------------------------------
# پارشیال‌های داشبورد کاربر (AJAX)
# --------------------------------------------------------------------------

@login_required
def user_favorites_partial(request):
    favorites = request.user.favorites.select_related('product').all()
    return render(request, 'partials/favorites_list.html', {'favorites': favorites})


@login_required
def user_reviews_partial(request):
    reviews = request.user.comments.select_related('product').order_by('-created')
    return render(request, 'partials/reviews_list.html', {'reviews': reviews})
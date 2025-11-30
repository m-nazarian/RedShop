from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, get_object_or_404
from .models import Category, Product, CategoryFeature, CommentLike, ProductComment, ProductFavorite
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
import json
from .services import sort_products, get_dynamic_features, assemble_filters, is_staff, apply_filters, global_search
from django.views.decorators.http import require_POST
from .forms import ProductCommentForm


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
    comment_form = ProductCommentForm()

    active_comments = product.comments.filter(active=True)

    # دریافت محصولات مرتبط
    # منطق: محصولاتی که در همین دسته‌بندی هستند، به جز خودِ این محصول
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('?')[:6]
    # order_by('?') یعنی تصادفی انتخاب کن

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
    View مخصوص AJAX (POST request)
    """
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

    # پاس دادن request به render_to_string
    html_products = render_to_string(
        "partials/product_list_partials.html",
        {"products": products},
        request=request
    )

    html_filters = render_to_string(
        "partials/all_filters_partials.html",
        {
            "ordered_filters": ordered_filters,
            "current_selections": data
        },
        request=request # اینجا هم برای اطمینان می‌فرستیم
    )

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


def search_suggestions(request):
    """
    API برای جستجوی زنده (Live Search)
    """
    query = request.GET.get('q', '')
    if len(query) < 2:  # اگر کمتر از ۲ حرف بود جستجو نکن (فشار نیاد)
        return JsonResponse({'products': [], 'suggested_category': None})

    data = global_search(query)
    return JsonResponse(data)


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

    # نوع درخواست: 'like' یا 'dislike'
    action_type = request.POST.get('type')  # مقداری که با AJAX میفرستیم
    is_like = (action_type == 'like')

    try:
        # چک میکنیم آیا قبلا واکنشی داشته؟
        existing_like = CommentLike.objects.get(user=request.user, comment=comment)

        if existing_like.status == is_like:
            # اگر دوباره روی همون دکمه زده، یعنی میخواد پس بگیره (Delete)
            existing_like.delete()
            action = 'removed'
        else:
            # اگر نظرش عوض شده (لایک بوده حالا دیس‌لایک کرده یا برعکس)
            existing_like.status = is_like
            existing_like.save()
            action = 'changed'

    except CommentLike.DoesNotExist:
        # اولین بار است که واکنش نشان میدهد
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

    # متد get_or_create: اگر بود می‌گیرد، اگر نبود می‌سازد
    # created=True یعنی تازه ساخته شد (لایک شد)
    # created=False یعنی قبلاً بوده (پس باید حذفش کنیم)
    favorite, created = ProductFavorite.objects.get_or_create(user=request.user, product=product)

    if not created:
        favorite.delete()
        status = 'removed'
    else:
        status = 'added'

    return JsonResponse({'success': True, 'status': status})
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from apps.coupons.forms import CouponApplyForm
from apps.shop.models import Product

from .cart import Cart


def _product_queryset():
    return Product.objects.select_related(
        'category',
        'brand',
    ).prefetch_related(
        'images',
    )


def _cart_totals_payload(cart):
    return {
        'item_count': len(cart),
        'total_price': cart.get_total_price(),
        'final_price': cart.get_final_price(),
        'post_price': cart.get_post_price_if_any(),
    }


def _json_error(message, *, status=400):
    return JsonResponse(
        {
            'success': False,
            'error': message,
        },
        status=status,
    )


@require_POST
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(_product_queryset(), id=product_id)

    if product.inventory <= 0:
        return _json_error('موجودی این محصول تمام شده است.', status=400)

    product_id_str = str(product.id)
    current_qty_in_cart = int(cart.cart.get(product_id_str, {}).get('quantity', 0))

    if current_qty_in_cart + 1 > product.inventory:
        return _json_error('تعداد درخواستی بیشتر از موجودی انبار است.', status=400)

    cart.add(product)

    html_cart = render_to_string(
        'partials/nav_cart.html',
        {'cart': cart},
        request=request,
    )

    payload = _cart_totals_payload(cart)
    payload.update(
        {
            'success': True,
            'html_cart': html_cart,
        }
    )
    return JsonResponse(payload, status=200)


def cart_detail(request):
    cart = Cart(request)
    coupon_apply_form = CouponApplyForm()
    context = {
        'cart': cart,
        'coupon_apply_form': coupon_apply_form,
    }
    return render(request, 'cart/detail.html', context)


@require_POST
def update_quantity(request):
    item_id = request.POST.get('item_id')
    action = request.POST.get('action')

    if not item_id:
        return _json_error('شناسه محصول ارسال نشده است.', status=400)

    if action not in {'add', 'decrease'}:
        return _json_error('عملیات سبد خرید معتبر نیست.', status=400)

    cart = Cart(request)
    product = get_object_or_404(_product_queryset(), id=item_id)
    product_id = str(product.id)

    if product_id not in cart.cart:
        return _json_error('این محصول در سبد خرید وجود ندارد.', status=404)

    if action == 'add':
        current_qty = int(cart.cart[product_id].get('quantity', 0))
        if current_qty + 1 > product.inventory:
            return _json_error('تعداد درخواستی بیشتر از موجودی انبار است.', status=400)
        cart.add(product)
    else:
        cart.decrease(product)

    item = cart.cart.get(product_id)
    if item is None:
        return _json_error('این محصول در سبد خرید وجود ندارد.', status=404)

    payload = _cart_totals_payload(cart)
    payload.update(
        {
            'success': True,
            'quantity': item['quantity'],
            'item_total': item['quantity'] * item['price'],
        }
    )
    return JsonResponse(payload)


@require_POST
def remove_item(request):
    item_id = request.POST.get('item_id')

    if not item_id:
        return _json_error('شناسه محصول ارسال نشده است.', status=400)

    cart = Cart(request)
    product = get_object_or_404(_product_queryset(), id=item_id)
    product_id = str(product.id)

    if product_id not in cart.cart:
        return _json_error('این محصول در سبد خرید وجود ندارد.', status=404)

    cart.remove(product)

    payload = _cart_totals_payload(cart)
    payload['success'] = True
    return JsonResponse(payload)


def checkout_start(request):
    if not request.user.is_authenticated:
        return redirect(f"/login/?next=/cart/checkout/")

    return redirect('orders:checkout_address')

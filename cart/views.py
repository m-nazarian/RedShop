from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from shop.models import Product
from .cart import Cart



@require_POST
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    # 1. بررسی موجودی کلی محصول
    if product.inventory <= 0:
        return JsonResponse({'error': 'موجودی این محصول تمام شده است!'}, status=400)

    # 2. بررسی اینکه آیا کاربر بیشتر از موجودی انبار دارد به سبد اضافه می‌کند؟
    product_id_str = str(product_id)
    current_qty_in_cart = 0
    if product_id_str in cart.cart:
        current_qty_in_cart = cart.cart[product_id_str]['quantity']

    if current_qty_in_cart + 1 > product.inventory:
        return JsonResponse({'error': 'تعداد درخواستی بیشتر از موجودی انبار است!'}, status=400)

    # اگر همه چی اوکی بود، اضافه کن
    try:
        cart.add(product)
        context = {
            'item_count': len(cart),
            'total_price': cart.get_total_price()
        }
        return JsonResponse(context, status=200)
    except Exception as e:
        # اگر ارور پیش ‌بینی نشده‌ای رخ داد
        return JsonResponse({'error': 'خطایی در افزودن محصول رخ داد.'}, status=500)


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})

@require_POST
def update_quantity(request):
    item_id = request.POST.get('item_id')
    action = request.POST.get('action')
    try:
        product = get_object_or_404(Product, id=item_id)
        cart = Cart(request)
        if action == 'add':
            cart.add(product)
        elif action == 'decrease':
            cart.decrease(product)
        item = cart.cart[str(item_id)]
        context = {
            'success': True,
            'item_count': len(cart),
            'total_price': cart.get_total_price(),
            'final_price': cart.get_final_price(),
            'post_price': cart.get_post_price_if_any(),
            'quantity': item['quantity'],
            'item_total': item['quantity'] * item['price'],
        }
        return JsonResponse(context)
    except:
        return JsonResponse({'success': False, 'error': 'Item not found!'})


@require_POST
def remove_item(request):
    item_id = request.POST.get('item_id')
    try:
        product = get_object_or_404(Product, id=item_id)
        cart = Cart(request)
        cart.remove(product)
        context = {
            'success': True,
            'item_count': len(cart),
            'total_price': cart.get_total_price(),
            'final_price': cart.get_final_price(),
            'post_price': cart.get_post_price_if_any(),
        }
        return JsonResponse(context)
    except:
        return JsonResponse({'success': False, 'error': 'Item not found!'})


def checkout_start(request):
    # اگر کاربر وارد نشده → هدایت به صفحه لاگین
    if not request.user.is_authenticated:
        return redirect(f"/login/?next=/cart/checkout/")
    # اگر وارد شده → بره به صفحه مشخصات ارسال
    return redirect('orders:checkout_address')

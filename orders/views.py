from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.crypto import get_random_string
from django.db import transaction
from django.contrib import messages
from .models import Order,OrderItem
from cart.cart import Cart
from account.models import Address
from shop.models import Product

@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'orders/user_orders.html', {
        'orders': orders,
        'active_tab': 'orders'
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    items = order.items.all()

    # مجموع قیمت کالاها
    total_items = sum(item.quantity * item.price for item in items)

    # هزینه ارسال (در سفارش ذخیره نشده، پس باید ذخیره شود)
    post_price = order.post_price if hasattr(order, "post_price") else 0

    # جمع نهایی
    final_total = total_items + post_price

    return render(request, "orders/order_detail.html", {
        "order": order,
        "items": items,
        "total_items": total_items,
        "post_price": post_price,
        "final_total": final_total,
    })


def generate_order_number():
    return get_random_string(10).upper()


@login_required
def checkout_address(request):
    cart = Cart(request)

    if len(cart) == 0:
        return redirect("cart:cart_detail")

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":
        address_id = request.POST.get("address_id")
        if not address_id:
            return render(request, "orders/checkout_address.html", {
                "cart": cart,
                "addresses": addresses,
                "error": "لطفا یک آدرس انتخاب کنید"
            })

        request.session["checkout_address_id"] = address_id
        return redirect("orders:checkout_review")

    return render(request, "orders/checkout_address.html", {
        "cart": cart,
        "addresses": addresses
    })


@login_required
def checkout_review(request):
    cart = Cart(request)

    if "checkout_address_id" not in request.session:
        return redirect("orders:checkout_address")

    address = get_object_or_404(
        Address, id=request.session["checkout_address_id"]
    )

    return render(request, "orders/checkout_review.html", {
        "cart": cart,
        "address": address,
    })


@login_required
def checkout_create_order(request):
    cart = Cart(request)

    if len(cart) == 0:
        return redirect("cart:cart_detail")

    if "checkout_address_id" not in request.session:
        return redirect("orders:checkout_address")

    address = get_object_or_404(
        Address, id=request.session["checkout_address_id"]
    )

    if request.session.get("order_created"):
        return redirect("orders:checkout_complete")

    # 🟩 شروع بلاک تراکنش اتمیک
    # یعنی یا همه کارها انجام میشه یا هیچی انجام نمیشه (Rollback)
    try:
        with transaction.atomic():
            # 1. ساخت سفارش اولیه
            order = Order.objects.create(
                user=request.user,
                address=address.address_line,
                order_number=generate_order_number(),
                status="pending",
                first_name=address.first_name,
                last_name=address.last_name,
                phone=address.phone,
                province=address.province,
                city=address.city,
                postal_code=address.postal_code,
                address_line=address.address_line,
            )

            # 2. ساخت آیتم‌ها و کسر موجودی
            for item in cart:
                product_id = item['product'].id
                quantity = item['quantity']

                # 🔥 قفل کردن رکورد محصول برای جلوگیری از تداخل (Race Condition)
                # select_for_update باعث میشه تا پایان این تراکنش، کس دیگه‌ای نتونه این محصول رو ویرایش کنه
                product = Product.objects.select_for_update().get(id=product_id)

                # بررسی موجودی دقیقاً در لحظه خرید
                if product.inventory < quantity:
                    # اگر موجودی کم بود، ارور ایجاد میکنیم تا تراکنش رول‌بک بشه
                    raise ValueError(
                        f"متاسفانه موجودی محصول '{product.name}' کافی نیست (موجودی فعلی: {product.inventory}).")

                # کسر موجودی
                product.inventory -= quantity
                product.save()

                # ایجاد آیتم سفارش
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=quantity,
                    weight=item['weight'],
                )

            # 3. محاسبات نهایی سفارش
            order.subtotal = order.get_total_cost()
            order.post_price = order.get_post_cost()
            order.shipping_price = order.post_price
            order.total = order.subtotal + order.post_price
            order.save()

            # پایان موفقیت‌آمیز
            request.session["order_created"] = True
            cart.clear()

            return redirect("orders:checkout_complete")

    except ValueError as e:
        # اگر موجودی کافی نبود، تراکنش خودکار لغو میشه و به اینجا میایم
        messages.error(request, str(e))
        return redirect("cart:cart_detail")

    except Exception as e:
        # سایر خطاهای احتمالی
        messages.error(request, "مشکلی در ثبت سفارش پیش آمد. لطفا مجددا تلاش کنید.")
        return redirect("cart:cart_detail")



@login_required
def checkout_complete(request):
    # بعد پایان سفارش، سشن را پاک می‌کنیم تا سفارش جدید ساخته شود
    request.session.pop("checkout_address_id", None)
    request.session.pop("order_created", None)

    return render(request, "orders/checkout_complete.html")
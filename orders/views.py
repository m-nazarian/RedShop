from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.db import transaction
from django.contrib import messages
from .emails import send_order_confirmation
from .models import Order,OrderItem
from cart.cart import Cart
from account.models import Address
from shop.models import Product
from django.http import HttpResponse
import weasyprint

@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'partials/orders_list.html', {
        'orders': orders,
        'active_tab': 'orders'
    })


@login_required
def user_orders_partial(request):
    """
    نمایش لیست سفارش‌ها + قابلیت جستجو
    """
    # 1. دریافت کلمه جستجو شده (اگر وجود داشته باشد)
    query = request.GET.get('q')

    # 2. کوئری پایه: سفارش‌های خود کاربر
    orders = Order.objects.filter(user=request.user)

    # 3. اگر کاربر چیزی جستجو کرده بود:
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |  # جستجو در شماره سفارش
            Q(id__icontains=query) |  # جستجو در ID عددی
            Q(items__product__name__icontains=query)  # جستجو در نام محصولات داخل سفارش
        ).distinct()  # جلوگیری از تکراری شدن نتایج به خاطر Join

    # 4. مرتب‌سازی نهایی
    orders = orders.order_by('-created')

    context = {
        'orders': orders,
    }
    return render(request, 'partials/orders_list.html', context)


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

    return render(request, "partials/orders_list.html", {
        "order": order,
        "items": items,
        "total_items": total_items,
        "post_price": post_price,
        "final_total": final_total,
    })


@login_required
def order_detail_partial(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'partials/order_detail_content.html', {'order': order})



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

    # اگر کاربر چیزی نفرستاده بود، پیش‌فرض 'cod' بگذار
    payment_method = request.POST.get('payment_method', 'cod')

    if request.session.get("order_created"):
        # اگر قبلا ساخته شده، با توجه به روش پرداخت ریدایرکت کن
        return redirect("orders:checkout_complete")

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

                payment_method=payment_method
            )

            # ساخت آیتم‌ها و کسر موجودی
            for item in cart:
                product_id = item['product'].id
                quantity = item['quantity']

                product = Product.objects.select_for_update().get(id=product_id)

                if product.inventory < quantity:
                    raise ValueError(
                        f"متاسفانه موجودی محصول '{product.name}' کافی نیست (موجودی فعلی: {product.inventory}).")

                product.inventory -= quantity
                product.save()

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=quantity,
                    weight=item['weight'],
                )

            # محاسبات نهایی سفارش
            order.subtotal = order.get_total_cost()
            order.post_price = order.get_post_cost()
            order.shipping_price = order.post_price
            order.total = order.subtotal + order.post_price
            order.save()

            # پایان موفقیت‌آمیز
            request.session["order_created"] = True

            # ذخیره آیدی سفارش در سشن برای درگاه
            request.session['order_id'] = order.id

            # پاک کردن سبد خرید
            cart.clear()

            if order.payment_method == 'online':
                # هدایت به پردازش پرداخت
                return redirect('payment:process')
            else:
                send_order_confirmation(order)
                # پرداخت در محل (COD) -> صفحه تشکر معمولی
                return redirect("orders:checkout_complete")

    except ValueError as e:
        messages.error(request, str(e))
        return redirect("cart:cart_detail")

    except Exception as e:
        messages.error(request, "مشکلی در ثبت سفارش پیش آمد. لطفا مجددا تلاش کنید.")
        return redirect("cart:cart_detail")



@login_required
def checkout_complete(request):
    # بعد پایان سفارش، سشن را پاک می‌کنیم تا سفارش جدید ساخته شود
    request.session.pop("checkout_address_id", None)
    request.session.pop("order_created", None)

    return render(request, "orders/checkout_complete.html")


@login_required
def order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # تنظیمات برای پیدا کردن فایل‌های استاتیک (مثل فونت و لوگو) توسط WeasyPrint
    # چون WeasyPrint یک مرورگر نیست، باید آدرس فایل‌ها را دقیق بهش بدیم

    html = render_to_string('orders/pdf/invoice.html', {
        'order': order
    }, request=request)

    response = HttpResponse(content_type='application/pdf')
    # attachment یعنی دانلود شود، inline یعنی در مرورگر باز شود
    response['Content-Disposition'] = f'filename=order_{order.order_number}.pdf'

    # تبدیل به PDF
    # base_url برای این است که عکس‌ها و استایل‌ها پیدا شوند
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(response)

    return response
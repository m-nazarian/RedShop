import logging

import weasyprint
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.account.models import Address
from apps.cart.cart import Cart

from .forms import CheckoutPaymentForm
from .models import Order
from .services import CheckoutError, CheckoutService

logger = logging.getLogger(__name__)


@login_required
@require_GET
def user_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created")
    return render(
        request,
        "partials/orders_list.html",
        {"orders": orders, "active_tab": "orders"},
    )


@login_required
@require_GET
def user_orders_partial(request):
    query = request.GET.get("q", "").strip()
    orders = Order.objects.filter(user=request.user).prefetch_related("items")

    if query:
        from django.db.models import Q

        orders = orders.filter(
            Q(order_number__icontains=query)
            | Q(id__icontains=query)
            | Q(items__title__icontains=query)
        ).distinct()

    return render(
        request,
        "partials/orders_list.html",
        {"orders": orders.order_by("-created")},
    )


@login_required
@require_GET
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )
    return render(
        request,
        "partials/orders_list.html",
        {
            "order": order,
            "items": order.items.all(),
            "total_items": order.subtotal,
            "discount_amount": order.discount_amount,
            "post_price": order.post_price,
            "final_total": order.total,
        },
    )


@login_required
@require_GET
def order_detail_partial(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )
    return render(request, "partials/order_detail_content.html", {"order": order})


@login_required
@require_http_methods(["GET", "POST"])
def checkout_address(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart:cart_detail")

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":
        address_id = request.POST.get("address_id")
        if not address_id:
            return render(
                request,
                "orders/checkout_address.html",
                {
                    "cart": cart,
                    "addresses": addresses,
                    "error": "یک آدرس را انتخاب کنید.",
                },
            )

        address = get_object_or_404(Address, id=address_id, user=request.user)
        request.session["checkout_address_id"] = address.id
        return redirect("orders:checkout_review")

    return render(
        request,
        "orders/checkout_address.html",
        {"cart": cart, "addresses": addresses},
    )


@login_required
@require_GET
def checkout_review(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart:cart_detail")

    address_id = request.session.get("checkout_address_id")
    if not address_id:
        return redirect("orders:checkout_address")

    address = get_object_or_404(Address, id=address_id, user=request.user)
    return render(
        request,
        "orders/checkout_review.html",
        {
            "cart": cart,
            "address": address,
            "payment_form": CheckoutPaymentForm(),
        },
    )


@login_required
@require_POST
def checkout_create_order(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart:cart_detail")

    address_id = request.session.get("checkout_address_id")
    if not address_id:
        return redirect("orders:checkout_address")

    existing_order_id = request.session.get("checkout_order_id")
    if existing_order_id:
        existing_order = Order.objects.filter(
            id=existing_order_id,
            user=request.user,
        ).first()

        if existing_order is None:
            request.session.pop("checkout_order_id", None)
            request.session.pop("order_id", None)
        elif existing_order.paid or existing_order.status == "canceled" or existing_order.stock_released:
            request.session.pop("checkout_order_id", None)
            request.session.pop("order_id", None)
        elif existing_order.payment_method == "online":
            request.session["order_id"] = existing_order.id
            return redirect("payment:process")
        else:
            request.session.pop("order_id", None)
            return redirect("orders:checkout_complete")

    form = CheckoutPaymentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "روش پرداخت معتبر نیست.")
        return redirect("orders:checkout_review")

    try:
        order = CheckoutService.place_order(
            user=request.user,
            cart=cart,
            address_id=address_id,
            payment_method=form.cleaned_data["payment_method"],
        )
    except CheckoutError as exc:
        messages.error(request, str(exc))
        return redirect("orders:checkout_review")
    except Exception:
        logger.exception("ثبت سفارش با خطای پیش‌بینی‌نشده متوقف شد.")
        messages.error(request, "ثبت سفارش انجام نشد. دوباره تلاش کنید.")
        return redirect("orders:checkout_review")

    request.session["checkout_order_id"] = order.id
    request.session.pop("checkout_address_id", None)
    cart.clear()

    if order.payment_method == "online":
        request.session["order_id"] = order.id
        return redirect("payment:process")

    request.session.pop("order_id", None)
    return redirect("orders:checkout_complete")


@login_required
@require_GET
def checkout_complete(request):
    request.session.pop("checkout_address_id", None)
    request.session.pop("checkout_order_id", None)
    request.session.pop("order_created", None)
    return render(request, "orders/checkout_complete.html")


@login_required
@require_GET
def order_pdf(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )

    html = render_to_string(
        "orders/pdf/invoice.html",
        {"order": order},
        request=request,
    )
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"filename=order_{order.order_number}.pdf"
    weasyprint.HTML(
        string=html,
        base_url=request.build_absolute_uri("/"),
    ).write_pdf(response)
    return response
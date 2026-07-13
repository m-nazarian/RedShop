import logging
from datetime import timedelta
from functools import partial

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.orders.emails import send_order_confirmation
from apps.orders.models import Order, Transaction
from apps.orders.services import OrderLifecycleService, PaymentLifecycleService

from .zarinpal_service import ZarinPalService
from apps.orders.session_keys import (
    CHECKOUT_ORDER_SESSION_KEY,
    PAYMENT_ORDER_SESSION_KEY,
    clear_checkout_order_session,
    clear_checkout_order_session_if_matches,
)

logger = logging.getLogger(__name__)


def _get_online_order_for_payment(user, order_id):
    return Order.objects.filter(
        id=order_id,
        user=user,
        payment_method="online",
    ).first()


def _render_already_paid_order(request, order):
    successful_transaction = order.transactions.filter(success=True).first()
    return render(
        request,
        "payment/success.html",
        {
            "ref_id": successful_transaction.ref_id if successful_transaction else "-",
            "order_number": order.order_number,
        },
    )


def _render_released_order_failure(request):
    return render(
        request,
        "payment/failure.html",
        {
            "message": "این سفارش قبلاً لغو شده و موجودی آن به انبار برگشته است.",
            "show_retry": False,
        },
    )


@login_required
@require_GET
def payment_process(request):
    order_id = request.session.get(PAYMENT_ORDER_SESSION_KEY)
    if not order_id:
        return redirect("orders:user_orders")

    order = _get_online_order_for_payment(request.user, order_id)

    if order is None:
        clear_checkout_order_session(request.session)
        messages.error(request, "سفارش پرداخت معتبر پیدا نشد.")
        return redirect("cart:cart_detail")

    if order.status == "canceled" or order.stock_released:
        clear_checkout_order_session(request.session)
        return _render_released_order_failure(request)

    if order.paid:
        clear_checkout_order_session(request.session)
        return _render_already_paid_order(request, order)

    recent_pending = order.transactions.filter(
        provider="zarinpal",
        status="pending",
        success=False,
        transaction_id__isnull=False,
        created_at__gte=timezone.now() - timedelta(minutes=15),
    ).first()
    if recent_pending:
        return redirect(f"{settings.ZARINPAL_START_PAY_URL}{recent_pending.transaction_id}")

    zarinpal = ZarinPalService()
    response = zarinpal.send_request(
        amount=order.total,
        description=f"پرداخت سفارش {order.order_number}",
        email=order.user.email,
        mobile=order.user.phone,
    )

    if response["status"]:
        Transaction.objects.create(
            order=order,
            transaction_id=response["authority"],
            amount=order.total,
            provider="zarinpal",
            success=False,
            status="pending",
            raw_response={"request_status": "created"},
        )
        return redirect(response["url"])

    logger.warning(
        "ایجاد تراکنش زرین‌پال برای سفارش %s ناموفق بود: %s",
        order.order_number,
        response.get("code"),
    )
    Transaction.objects.create(
        order=order,
        amount=order.total,
        provider="zarinpal",
        success=False,
        status="failed",
        raw_response={"request_status": "failed", "code": response.get("code")},
    )
    return render(
        request,
        "payment/failure.html",
        {"error_code": response.get("code"), "show_retry": True},
    )


from .logging_events import log_payment_callback_event

@require_GET
def payment_verify(request):
    log_payment_callback_event(
        "callback_received",
        authority=(
            request.GET.get("Authority")
            or request.POST.get("Authority")
            or request.GET.get("authority")
            or request.POST.get("authority")
            or ""
        ),
        status=(
            request.GET.get("Status")
            or request.POST.get("Status")
            or request.GET.get("status")
            or request.POST.get("status")
            or ""
        ),
        request=request,
    )
    authority = request.GET.get("Authority", "").strip()
    status = request.GET.get("Status", "").strip()

    if not authority:
        return render(
            request,
            "payment/failure.html",
            {"message": "Payment authority was not provided.", "show_retry": False},
        )

    payment_transaction = Transaction.objects.filter(
        transaction_id=authority,
        provider="zarinpal",
    ).select_related("order").first()

    if payment_transaction is None:
        return render(
            request,
            "payment/failure.html",
            {"message": "A valid transaction was not found.", "show_retry": False},
        )

    if payment_transaction.success:
        order = payment_transaction.order
        clear_checkout_order_session_if_matches(request.session, order.id)

        template = (
            "payment/failure.html"
            if order.status == Order.STATUS_PAYMENT_REVIEW
            else "payment/success.html"
        )

        context = {
            "ref_id": payment_transaction.ref_id,
            "order_number": order.order_number,
        }

        if template == "payment/failure.html":
            context.update(
                {
                    "message": "Payment was verified, but the order needs manual review.",
                    "show_retry": False,
                }
            )

        return render(request, template, context)

    if status != "OK":
        result = PaymentLifecycleService.cancel_from_callback(
            payment_transaction.pk,
            callback_status=status,
        )

        if request.session.get(PAYMENT_ORDER_SESSION_KEY) == result.order.id:
            request.session.pop(PAYMENT_ORDER_SESSION_KEY, None)

        if request.session.get(CHECKOUT_ORDER_SESSION_KEY) == result.order.id:
            request.session.pop(CHECKOUT_ORDER_SESSION_KEY, None)

        return render(
            request,
            "payment/failure.html",
            {
                "message": "Payment was canceled and the reserved stock was released.",
                "show_retry": False,
            },
        )

    zarinpal = ZarinPalService()
    response = zarinpal.verify_payment(authority, payment_transaction.amount)

    if not response["status"]:
        PaymentLifecycleService.mark_verification_failed(
            payment_transaction.pk,
            response_code=response.get("code"),
        )

        return render(
            request,
            "payment/failure.html",
            {"error_code": response.get("code"), "show_retry": False},
        )

    result = PaymentLifecycleService.confirm_online_payment(
        payment_transaction.pk,
        ref_id=response["ref_id"],
        response_code=response.get("code"),
    )

    clear_checkout_order_session_if_matches(request.session, result.order.id)

    if result.outcome == PaymentLifecycleService.OUTCOME_REVIEW:
        return render(
            request,
            "payment/failure.html",
            {
                "message": "Payment was verified, but the order needs manual review.",
                "ref_id": response["ref_id"],
                "order_number": result.order.order_number,
                "show_retry": False,
            },
        )

    return render(
        request,
        "payment/success.html",
        {"ref_id": response["ref_id"], "order_number": result.order.order_number},
    )

import logging
from datetime import timedelta
from functools import partial

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.orders.emails import send_order_confirmation
from apps.orders.models import Order, Transaction
from apps.orders.services import OrderLifecycleService

from .zarinpal_service import ZarinPalService

logger = logging.getLogger(__name__)


@login_required
@require_GET
def payment_process(request):
    order_id = request.session.get("order_id")
    if not order_id:
        return redirect("orders:user_orders")

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
        payment_method="online",
    )

    if order.paid:
        successful_transaction = order.transactions.filter(success=True).first()
        return render(
            request,
            "payment/success.html",
            {
                "ref_id": successful_transaction.ref_id if successful_transaction else "-",
                "order_number": order.order_number,
            },
        )

    if order.status == "canceled" or order.stock_released:
        request.session.pop("order_id", None)
        request.session.pop("checkout_order_id", None)
        return render(
            request,
            "payment/failure.html",
            {
                "message": "این سفارش قبلاً لغو شده و موجودی آن به انبار برگشته است.",
                "show_retry": False,
            },
        )

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


@require_GET
def payment_verify(request):
    authority = request.GET.get("Authority", "").strip()
    status = request.GET.get("Status", "").strip()

    if not authority:
        return render(
            request,
            "payment/failure.html",
            {"message": "شناسه تراکنش ارسال نشده است.", "show_retry": False},
        )

    payment_transaction = Transaction.objects.filter(
        transaction_id=authority,
        provider="zarinpal",
    ).select_related("order").first()

    if payment_transaction is None:
        return render(
            request,
            "payment/failure.html",
            {"message": "تراکنش معتبر پیدا نشد.", "show_retry": False},
        )

    if payment_transaction.success:
        return render(
            request,
            "payment/success.html",
            {
                "ref_id": payment_transaction.ref_id,
                "order_number": payment_transaction.order.order_number,
            },
        )

    if status != "OK":
        with db_transaction.atomic():
            locked_transaction = Transaction.objects.select_for_update().get(
                id=payment_transaction.id
            )
            locked_transaction.status = "canceled"
            locked_transaction.raw_response = {
                "callback_status": status or "unknown",
                "verified": False,
            }
            locked_transaction.save(update_fields=["status", "raw_response", "updated_at"])

        order, _ = OrderLifecycleService.cancel_unpaid_order(
            payment_transaction.order_id,
            reason="پرداخت از طرف کاربر یا درگاه لغو شد.",
        )

        if request.session.get("order_id") == order.id:
            request.session.pop("order_id", None)
        if request.session.get("checkout_order_id") == order.id:
            request.session.pop("checkout_order_id", None)

        return render(
            request,
            "payment/failure.html",
            {
                "message": "پرداخت لغو شد و موجودی سفارش به انبار برگشت.",
                "show_retry": False,
            },
        )

    zarinpal = ZarinPalService()
    response = zarinpal.verify_payment(authority, payment_transaction.amount)

    if not response["status"]:
        payment_transaction.status = "failed"
        payment_transaction.raw_response = {
            "verified": False,
            "code": response.get("code"),
        }
        payment_transaction.save(update_fields=["status", "raw_response", "updated_at"])
        return render(
            request,
            "payment/failure.html",
            {"error_code": response.get("code"), "show_retry": False},
        )

    with db_transaction.atomic():
        locked_transaction = Transaction.objects.select_for_update().get(
            id=payment_transaction.id
        )
        order = Order.objects.select_for_update().get(id=locked_transaction.order_id)

        if not locked_transaction.success:
            locked_transaction.success = True
            locked_transaction.status = "paid"
            locked_transaction.ref_id = str(response["ref_id"])
            locked_transaction.raw_response = {
                "verified": True,
                "code": response.get("code"),
                "ref_id": str(response["ref_id"]),
            }
            locked_transaction.save(
                update_fields=["success", "status", "ref_id", "raw_response", "updated_at"]
            )

            was_paid = order.paid
            order.paid = True
            order.status = "processing"
            order.save(update_fields=["paid", "status", "updated"])

            if not was_paid:
                db_transaction.on_commit(
                    partial(send_order_confirmation, order),
                    robust=True,
                )

    if request.session.get("order_id") == order.id:
        request.session.pop("order_id", None)
    if request.session.get("checkout_order_id") == order.id:
        request.session.pop("checkout_order_id", None)

    return render(
        request,
        "payment/success.html",
        {"ref_id": response["ref_id"], "order_number": order.order_number},
    )
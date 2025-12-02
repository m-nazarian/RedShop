from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from orders.emails import send_order_confirmation
from orders.models import Order, Transaction
from .zarinpal_service import ZarinPalService

@login_required
def payment_process(request):
    # گرفتن سفارش از سشن
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('orders:user_orders')

    order = get_object_or_404(Order, id=order_id)
    amount = order.total  # مبلغ نهایی (شامل هزینه پست)

    # اتصال به سرویس زرین‌پال
    zarinpal = ZarinPalService()
    response = zarinpal.send_request(
        amount=amount,
        description=f"پرداخت سفارش {order.order_number}",
        mobile=request.user.phone
    )

    if response['status']:
        # ذخیره تراکنش اولیه (Pending)
        Transaction.objects.create(
            order=order,
            transaction_id=response['authority'],
            amount=amount,
            provider='zarinpal',
            success=False
        )
        # هدایت کاربر به درگاه بانک
        return redirect(response['url'])
    else:
        # نمایش خطا در صورت عدم اتصال به بانک
        return render(request, 'payment/failure.html', {'error_code': response['code']})


@login_required
def payment_verify(request):
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    # اگر کاربر دکمه انصراف را در بانک زده باشد
    if status != 'OK':
        return render(request, 'payment/failure.html', {'message': 'عملیات پرداخت توسط کاربر لغو شد.'})

    try:
        transaction = Transaction.objects.get(transaction_id=authority)
        order = transaction.order
    except Transaction.DoesNotExist:
        return render(request, 'payment/failure.html', {'message': 'تراکنش معتبر یافت نشد.'})

    # تایید نهایی با بانک
    zarinpal = ZarinPalService()
    response = zarinpal.verify_payment(authority, transaction.amount)

    if response['status']:
        # ✅ پرداخت موفق
        transaction.success = True
        transaction.ref_id = response['ref_id']
        transaction.save()

        order.paid = True
        order.status = 'processing' # تغییر وضعیت به "در حال پردازش"
        order.save()

        send_order_confirmation(order)

        # پاک کردن سشن سفارش
        if 'order_id' in request.session:
            del request.session['order_id']

        return render(request, 'payment/success.html', {
            'ref_id': response['ref_id'],
            'order_number': order.order_number
        })
    else:
        # ❌ پرداخت ناموفق
        return render(request, 'payment/failure.html', {'error_code': response['code']})
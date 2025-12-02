from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import threading


def send_order_email_thread(subject, html_message, recipient_list):
    """ ارسال ایمیل در یک ترد جداگانه برای جلوگیری از کندی سایت """
    try:
        plain_message = strip_tags(html_message)
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            recipient_list,
            html_message=html_message
        )
    except Exception as e:
        print(f"Error sending email: {e}")


def send_order_confirmation(order):
    """
    آماده‌سازی داده‌ها و فراخوانی ارسال ایمیل
    """
    if not order.user.email:
        return

    subject = f'رسید ثبت سفارش: {order.order_number}'

    domain = "http://127.0.0.1:8000"

    html_message = render_to_string('emails/order_created.html', {
        'order': order,
        'domain': domain
    })

    # ارسال به صورت Async (با Threading)
    threading.Thread(
        target=send_order_email_thread,
        args=(subject, html_message, [order.user.email])
    ).start()
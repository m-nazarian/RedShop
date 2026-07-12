"""کلیدهای session مربوط به checkout و payment.

این فایل جلوی پراکنده‌شدن رشته‌های session در viewها و تست‌ها را می‌گیرد.
"""

CART_SESSION_KEY = "cart"
CHECKOUT_ADDRESS_SESSION_KEY = "checkout_address_id"
CHECKOUT_ORDER_SESSION_KEY = "checkout_order_id"
COUPON_SESSION_KEY = "coupon_id"
PAYMENT_ORDER_SESSION_KEY = "order_id"


def clear_checkout_order_session(session):
    """شناسه‌های سفارش checkout و payment را از session پاک می‌کند."""

    session.pop(CHECKOUT_ORDER_SESSION_KEY, None)
    session.pop(PAYMENT_ORDER_SESSION_KEY, None)


def clear_checkout_order_session_if_matches(session, order_id):
    """شناسه‌های سفارش را فقط وقتی با سفارش فعلی برابر باشند پاک می‌کند."""

    if session.get(PAYMENT_ORDER_SESSION_KEY) == order_id:
        session.pop(PAYMENT_ORDER_SESSION_KEY, None)

    if session.get(CHECKOUT_ORDER_SESSION_KEY) == order_id:
        session.pop(CHECKOUT_ORDER_SESSION_KEY, None)

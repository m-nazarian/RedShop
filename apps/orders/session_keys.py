"""کلیدهای session مربوط به checkout و payment.

این فایل جلوی پراکنده‌شدن رشته‌های session در viewها و تست‌ها را می‌گیرد.
"""

CART_SESSION_KEY = "cart"
CHECKOUT_ADDRESS_SESSION_KEY = "checkout_address_id"
CHECKOUT_ORDER_SESSION_KEY = "checkout_order_id"
COUPON_SESSION_KEY = "coupon_id"
PAYMENT_ORDER_SESSION_KEY = "order_id"

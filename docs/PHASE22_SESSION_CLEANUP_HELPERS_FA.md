# مرحله بیست‌ودوم: helperهای پاک‌سازی session

در مرحله قبل کلیدهای session مرکزی شدند. در این مرحله پاک‌کردن کلیدهای مرتبط با سفارش checkout/payment هم به helperهای کوچک منتقل شد.

## تغییرات

- `clear_checkout_order_session` اضافه شد.
- `clear_checkout_order_session_if_matches` اضافه شد.
- `orders/views.py` از helper پاک‌سازی session استفاده می‌کند.
- `payment/views.py` از helper پاک‌سازی session استفاده می‌کند.

## نتیجه

کدهای تکراری `session.pop` کمتر شد و پاک‌سازی session سفارش در یک نقطه قابل نگهداری‌تر شد.

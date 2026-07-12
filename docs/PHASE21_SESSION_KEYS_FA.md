# مرحله بیست‌ویکم: ثابت‌سازی کلیدهای session

در این مرحله کلیدهای session مربوط به checkout و payment در یک فایل مرکزی قرار گرفتند.

## تغییرات

- فایل `apps/orders/session_keys.py` اضافه شد.
- کلیدهای `cart`، `checkout_address_id`، `checkout_order_id`، `coupon_id` و `order_id` ثابت شدند.
- `apps/orders/views.py` از ثابت‌ها استفاده می‌کند.
- `apps/payment/views.py` از ثابت‌ها استفاده می‌کند.
- تست‌های سفارش هم از همین ثابت‌ها استفاده می‌کنند.

## نتیجه

ریسک خطای تایپی در session keyها کمتر شد و نگهداری مسیر checkout/payment ساده‌تر شد.

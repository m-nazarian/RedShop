# مرحله بیست‌وهفتم: گارد تستی session keyها

در این مرحله یک تست محافظ اضافه شد تا رشته‌های خام مربوط به session keyها دوباره وارد فایل‌های حساس checkout/payment نشوند.

## تغییرات

- کلاس `CheckoutSessionKeyUsageTests` اضافه شد.
- فایل‌های `apps/orders/views.py`، `apps/payment/views.py` و `apps/orders/tests.py` اسکن می‌شوند.
- اگر کلیدهایی مثل `order_id`، `checkout_order_id`، `checkout_address_id`، `coupon_id` یا `cart` به‌صورت literal خام پیدا شوند، تست خطا می‌دهد.

## نتیجه

ثابت‌های `apps/orders/session_keys.py` فقط برای تغییر فعلی نیستند؛ از این به بعد تست‌ها جلوی برگشت رشته‌های پراکنده را می‌گیرند.

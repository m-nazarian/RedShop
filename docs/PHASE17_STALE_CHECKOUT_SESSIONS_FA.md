# مرحله هفدهم: پاک‌سازی sessionهای کهنه Checkout و Payment

در این مرحله مدیریت sessionهای checkout و payment دقیق‌تر شد.

## تغییرات

- اگر `checkout_order_id` داخل session به سفارش نامعتبر اشاره کند، پاک می‌شود.
- اگر سفارش session شده پرداخت‌شده، لغوشده یا stock_released باشد، session پاک می‌شود.
- در مسیر پرداخت، سفارش نامعتبر session را پاک می‌کند و کاربر را به سبد خرید برمی‌گرداند.
- سفارش پرداخت‌شده یا لغوشده، `order_id` و `checkout_order_id` را از session پاک می‌کند.
- رفتار صفحه success پرداخت حفظ شد و همچنان `ref_id` و `order_number` به قالب داده می‌شود.
- تست session کهنه checkout با ساخت مستقیم سفارش قدیمی و cart داخل session پایدارتر شد.
- تست session نامعتبر payment اضافه شد.

## نتیجه

کاربر کمتر در مسیرهای قدیمی checkout/payment گیر می‌کند و sessionهای stale کنترل‌شده‌تر پاک می‌شوند.

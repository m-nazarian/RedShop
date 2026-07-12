# مرحله سی‌وهفتم: جداکردن تست‌های payment process

در این مرحله تست‌های مربوط به `payment_process` از فایل checkout/payment جدا شدند.

## تغییرات

- کلاس `PaymentProcessTests` در `apps/orders/tests/test_payment_process.py` اضافه شد.
- تست پاک‌سازی session نامعتبر payment منتقل شد.
- تست پاک‌سازی session برای سفارش پرداخت‌شده منتقل شد.
- تست پاک‌سازی session برای سفارش آزادشده منتقل شد.

## نتیجه

فایل checkout/payment سبک‌تر شد و تست‌های payment process در فایل مستقل خودشان قرار گرفتند.

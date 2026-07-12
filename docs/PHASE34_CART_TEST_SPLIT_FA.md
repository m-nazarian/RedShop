# مرحله سی‌وچهارم: جداکردن تست‌های cart

در این مرحله تست‌های مربوط به cart از فایل checkout/payment جدا شدند.

## تغییرات

- کلاس `CartViewTests` در `apps/orders/tests/test_cart_views.py` اضافه شد.
- تست‌های read-only و mutation مربوط به cart به فایل جدید منتقل شدند.
- فایل checkout/payment فقط روی checkout، profile، payment process و smoke مربوط به shop متمرکزتر شد.

## نتیجه

ساختار تست‌ها خواناتر شد و تست‌های cart در فایل مستقل خودشان قرار گرفتند.

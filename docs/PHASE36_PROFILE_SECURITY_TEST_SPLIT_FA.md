# مرحله سی‌وششم: جداکردن تست امنیت profile

در این مرحله تست امنیتی profile از فایل checkout/payment جدا شد.

## تغییرات

- کلاس `ProfileSecurityTests` در `apps/orders/tests/test_profile_security.py` اضافه شد.
- تست `test_profile_does_not_accept_post_or_staff_fields` به فایل جدید منتقل شد.
- فایل checkout/payment فقط روی checkout و مسیرهای payment process متمرکزتر شد.

## نتیجه

تست مربوط به profile در فایل مستقل خودش قرار گرفت و فایل checkout/payment سبک‌تر شد.

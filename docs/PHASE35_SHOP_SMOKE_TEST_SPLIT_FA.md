# مرحله سی‌وپنجم: جداکردن smoke تست shop

در این مرحله smoke تست مربوط به صفحه اصلی shop و صفحه جزئیات محصول از فایل checkout/payment جدا شد.

## تغییرات

- کلاس `ShopSmokeTests` در `apps/orders/tests/test_shop_smoke.py` اضافه شد.
- تست `test_shop_index_and_product_detail_smoke_after_query_optimization` به فایل جدید منتقل شد.
- فایل checkout/payment روی checkout، profile و مسیرهای payment process متمرکزتر شد.

## نتیجه

تست‌های shop در فایل مستقل خودشان قرار گرفتند و ساختار تست‌ها خواناتر شد.

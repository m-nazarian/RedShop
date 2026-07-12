# مرحله پانزدهم: محدودسازی روش‌های HTTP

در این مرحله چند View که رفتارشان مشخص بود، با decorator مناسب محدود شدند.

## تغییرات

- Viewهای فقط‌خواندنی shop با `require_GET` محدود شدند.
- Viewهای فرم‌محور account با `require_http_methods(["GET", "POST"])` محدود شدند.
- Viewهای خواندنی cart با `require_GET` محدود شدند.
- `filter_products` به‌جای بررسی دستی method، با `require_POST` محدود شد.
- برای endpointهای تغییر‌دهنده Cart تست 405 اضافه شد.

## نتیجه

رفتار HTTP شفاف‌تر، قابل تست‌تر و نزدیک‌تر به الگوی استاندارد Django شد.

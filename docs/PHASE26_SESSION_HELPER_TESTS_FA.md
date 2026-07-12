# مرحله بیست‌وششم: تست helperهای session

در این مرحله برای helperهای پاک‌سازی session تست مستقیم اضافه شد.

## تغییرات

- تست `clear_checkout_order_session` اضافه شد.
- تست `clear_checkout_order_session_if_matches` اضافه شد.
- بررسی شد که کلیدهای نامرتبط مثل `cart` یا داده‌های دیگر پاک نشوند.
- بررسی شد که پاک‌سازی شرطی فقط برای سفارش همسان انجام شود.

## نتیجه

helperهای session مستقل از viewها هم پوشش تستی دارند.

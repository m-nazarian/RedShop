# مرحله سی‌ام: تبدیل تست‌های orders به پکیج

در این مرحله فایل بزرگ `apps/orders/tests.py` به پکیج تست تبدیل شد.

## تغییرات

- فایل `apps/orders/tests.py` حذف و محتوای آن به `apps/orders/tests/test_checkout_payment.py` منتقل شد.
- فایل `apps/orders/tests/__init__.py` اضافه شد.
- importهای نسبی تست‌ها به importهای absolute از `apps.orders` تبدیل شدند.
- مسیر `project_root` در تست گارد session key با محل جدید فایل هماهنگ شد.

## نتیجه

رفتار تست‌ها تغییر نکرد، اما ساختار تست‌ها برای تقسیم تدریجی در مراحل بعد آماده شد.

# مرحله سی‌ویکم: جداکردن تست‌های session key

در این مرحله تست‌های مربوط به session keyها از فایل اصلی checkout/payment جدا شدند.

## تغییرات

- کلاس `CheckoutSessionHelperTests` به `apps/orders/tests/test_session_keys.py` منتقل شد.
- کلاس `CheckoutSessionKeyUsageTests` به `apps/orders/tests/test_session_keys.py` منتقل شد.
- importهای اضافی helperهای session از `test_checkout_payment.py` حذف شد.
- گارد session key علاوه بر viewها، فایل تست checkout/payment را هم بررسی می‌کند.

## نتیجه

فایل تست checkout/payment سبک‌تر شد و تست‌های session key در فایل مستقل خودشان قرار گرفتند.

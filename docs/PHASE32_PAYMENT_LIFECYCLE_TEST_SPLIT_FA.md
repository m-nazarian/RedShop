# مرحله سی‌ودوم: جداکردن تست‌های lifecycle پرداخت

در این مرحله تست‌های lifecycle پرداخت از فایل checkout/payment جدا شدند.

## تغییرات

- کلاس `PaymentLifecycleTests` به `apps/orders/tests/test_payment_lifecycle.py` منتقل شد.
- importهای مربوط به `Transaction` و `OrderLifecycleService` از فایل checkout/payment حذف شدند.
- فایل جدید برای تست‌های lifecycle پرداخت ساخته شد.

## نتیجه

فایل checkout/payment سبک‌تر شد و تست‌های مرتبط با lifecycle سفارش و پرداخت در فایل مستقل خودشان قرار گرفتند.

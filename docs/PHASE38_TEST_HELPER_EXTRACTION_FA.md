# مرحله سی‌وهشتم: انتقال helper مشترک تست‌ها

در این مرحله کلاس مشترک `RedShopTestBase` از فایل checkout/payment خارج شد و در فایل مستقل helper قرار گرفت.

## تغییرات

- فایل `apps/orders/tests/helpers.py` ساخته شد.
- کلاس `RedShopTestBase` به فایل helper منتقل شد.
- import فایل‌های تستی که از این helper استفاده می‌کردند اصلاح شد.
- importهای اضافه از `test_checkout_payment.py` حذف شدند.

## نتیجه

فایل‌های تست دیگر به فایل checkout/payment به‌عنوان helper عمومی وابسته نیستند و ساختار تست‌ها تمیزتر شد.

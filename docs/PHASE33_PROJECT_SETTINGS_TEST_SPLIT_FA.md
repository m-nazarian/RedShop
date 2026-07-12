# مرحله سی‌وسوم: جداکردن تست تنظیمات پروژه

در این مرحله تست مربوط به تنظیمات پروژه از فایل checkout/payment جدا شد.

## تغییرات

- کلاس `ProjectSettingsTests` به `apps/orders/tests/test_project_settings.py` منتقل شد.
- فایل checkout/payment فقط روی تست‌های checkout، cart، profile و smoke مربوط به shop متمرکزتر شد.

## نتیجه

تست تنظیمات logging در فایل مستقل خودش قرار گرفت و ساختار تست‌ها خواناتر شد.

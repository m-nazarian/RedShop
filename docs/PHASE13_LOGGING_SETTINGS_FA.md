# مرحله سیزدهم: تنظیمات Logging پروژه

در این مرحله پیکربندی logging پروژه در `settings.py` استانداردتر شد.

## تغییرات

- تنظیم `LOGGING` با فرمت dictConfig اضافه شد.
- لاگ‌ها هم روی console و هم در فایل `logs/redshop.log` ثبت می‌شوند.
- فایل لاگ با `RotatingFileHandler` کنترل می‌شود تا بی‌نهایت بزرگ نشود.
- سطح لاگ با `DJANGO_LOG_LEVEL` قابل تنظیم است.
- سطح لاگ Django با `DJANGO_LOG_LEVEL_DJANGO` قابل تنظیم است.
- مسیر `logs/` و فایل‌های `*.log` وارد `.gitignore` شدند.
- متغیرهای logging به `.env.example` اضافه شدند.
- یک تست sanity برای تنظیمات logging اضافه شد.

## نتیجه

لاگ‌های پروژه قابل پیگیری‌تر شدند و برای محیط توسعه و بعداً production آماده‌تر هستند.

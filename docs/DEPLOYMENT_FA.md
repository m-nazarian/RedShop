
# راهنمای آماده‌سازی دیپلوی RedShop

این پروژه حالا علاوه بر تست‌های دامنه و امنیت، ابزارهای عملی برای دیپلوی امن دارد:

- RedShop.settings_production
- RedShop.env
- redshop_deployment_check
- Security Headers Middleware
- Command آزادسازی سفارش‌های آنلاین منقضی‌شده

## 1. تنظیم فایل محیطی

برای توسعه محلی:

    Copy-Item .env.example .env

برای Production، مقدارهای واقعی را در محیط هاست یا سرور تنظیم کن و فایل .env واقعی را Commit نکن.

حداقل متغیرهای ضروری Production:

    DJANGO_SETTINGS_MODULE=RedShop.settings_production
    DJANGO_SECRET_KEY=<long-random-secret>
    DJANGO_ALLOWED_HOSTS=example.com,www.example.com
    DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

## 2. چک‌های قبل از دیپلوی

    .\.venv\Scripts\python.exe manage.py check --deploy
    .\.venv\Scripts\python.exe manage.py redshop_deployment_check --strict
    .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
    .\.venv\Scripts\python.exe manage.py test

redshop_deployment_check در حالت عادی فقط گزارش می‌دهد. با --strict اگر ریسک جدی مثل DEBUG=True یا Secret Key ضعیف پیدا کند، خطا می‌دهد.

## 3. Migration و Static Files

    .\.venv\Scripts\python.exe manage.py migrate
    .\.venv\Scripts\python.exe manage.py collectstatic --noinput

## 4. آزادسازی سفارش‌های پرداخت‌نشده

برای جلوگیری از قفل‌شدن دائمی موجودی سفارش‌های آنلاین رهاشده:

    .\.venv\Scripts\python.exe manage.py release_expired_orders --older-than-minutes 30 --limit 200

برای تست بدون تغییر داده:

    .\.venv\Scripts\python.exe manage.py release_expired_orders --older-than-minutes 30 --dry-run

در Production این دستور باید با Cron، Task Scheduler یا Worker دوره‌ای اجرا شود.

## 5. سفارش‌های payment_review

اگر پرداخت بعد از آزادسازی موجودی موفق شود، سفارش به payment_review می‌رود. در Admin:

- Badge مخصوص دارد.
- Filter مخصوص دارد.
- خروجی CSV دارد.

این سفارش‌ها نباید خودکار پردازش شوند؛ باید توسط ادمین بررسی شوند.

## 6. CSP و Security Headers

CSP در Local به‌صورت Report-Only است تا UI نشکند. در Production با این مقدار enforce می‌شود:

    REDSHOP_ENFORCE_CSP=true

قبل از enforce نهایی، گزارش‌های CSP و assetهای خارجی را بررسی کن.

## 7. نکات امنیتی مهم

- .env واقعی را Commit نکن.
- DJANGO_SECRET_KEY باید طولانی و تصادفی باشد.
- ALLOWED_HOSTS نباید * باشد.
- بعد از اطمینان از HTTPS، HSTS را فعال نگه دار.
- برای پرداخت واقعی، کلیدهای Gateway باید فقط از محیط خوانده شوند.

## 8. Request ID و ردیابی لاگ‌ها

هر Response یک Header با نام X-Request-ID دارد. اگر Reverse Proxy یا Client مقدار معتبر X-Request-ID بفرستد، همان مقدار حفظ می‌شود؛ در غیر این صورت سیستم یک مقدار امن تولید می‌کند.

در لاگ‌های Production، request_id داخل فرمت plain و JSON ثبت می‌شود تا خطاهای checkout، پرداخت، و admin قابل ردیابی باشند.

## 9. Order audit logs

برای عملیات حساس ادمین، مثل خروجی گرفتن از سفارش‌های payment_review، رکورد audit ساخته می‌شود. این رکوردها شامل order، actor، action، request_id، metadata و زمان ثبت هستند و در Admin فقط خواندنی‌اند.

## 10. Sensitive log redaction

لاگ‌های Production قبل از خروج از handlerها از فیلتر RedactingFilter عبور می‌کنند. ایمیل، موبایل ایران، شماره کارت، Bearer token و key-valueهای حساس مثل password، secret، token و api_key ماسک می‌شوند.

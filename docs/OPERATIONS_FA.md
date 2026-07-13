
# RedShop Production Operations Runbook

این Runbook برای روزی است که RedShop روی Production یا محیط شبیه Production اجرا می‌شود. هدف این سند این است که هنگام خطای پرداخت، سفارش‌های رهاشده، هشدارهای امنیتی و بررسی ادمین، مسیر عملیاتی واضح وجود داشته باشد.

## 1. چک سریع سلامت قبل از Release

قبل از هر Release این دستورها باید سبز باشند:

    python manage.py makemigrations --check --dry-run
    python manage.py check
    python manage.py check --deploy
    python manage.py redshop_deployment_check --strict
    python manage.py test -v 2

اگر redshop_deployment_check خطای DEBUG، SECRET_KEY یا ALLOWED_HOSTS داد، Release نباید انجام شود.

## 2. بررسی مشکل پرداخت

برای پیگیری یک پرداخت، این داده‌ها را کنار هم بررسی کن:

- request_id از Header یا لاگ
- authority_hash از لاگ callback
- order_number از سفارش
- transaction_status
- order_status
- paid
- payment_review بودن یا نبودن سفارش

نکته مهم: مقدار خام Authority نباید در لاگ ذخیره شود. فقط authority_hash کوتاه برای correlation استفاده می‌شود.

نمونه جستجوی ذهنی در لاگ:

    request_id=req-payment-...
    authority_hash=...

اگر مشتری Authority خام را ارائه کرد، مقدار خام را در تیکت عمومی یا لاگ ذخیره نکن. فقط در محیط امن، hash همان مقدار را با hash_payment_identifier محاسبه کن و با authority_hash لاگ مقایسه کن.

## 3. سفارش payment_review

سفارش زمانی وارد payment_review می‌شود که پرداخت موفق بعد از آزادسازی موجودی یا حالت نیازمند بررسی رخ دهد.

اقدام‌های پیشنهادی:

1. order_number را در Admin پیدا کن.
2. OrderAuditLog مربوط به آن سفارش را بررسی کن.
3. transaction_status و transaction_success را بررسی کن.
4. موجودی محصولات سفارش را با وضعیت فعلی انبار مقایسه کن.
5. اگر نیاز به ارسال کالا وجود دارد، تصمیم را خارج از سیستم خودکار و با تأیید ادمین انجام بده.
6. اگر نیاز به Refund است، عملیات Gateway را خارج از RedShop انجام بده و نتیجه را در یادداشت داخلی ثبت کن.

این سفارش‌ها نباید خودکار وارد پردازش ارسال شوند.

## 4. آزادسازی سفارش‌های آنلاین رهاشده

برای جلوگیری از قفل دائمی موجودی:

    python manage.py release_expired_orders --older-than-minutes 30 --limit 200

برای بررسی بدون تغییر داده:

    python manage.py release_expired_orders --older-than-minutes 30 --dry-run

این دستور باید با Cron، systemd timer، Task Scheduler یا Worker دوره‌ای اجرا شود.

## 5. Audit Log ادمین

OrderAuditLog برای عملیات حساس ادمین استفاده می‌شود. این رکوردها append-only هستند و در Admin فقط خواندنی‌اند.

فیلدهای مهم:

- order
- actor
- action
- request_id
- message
- metadata
- created_at

برای خروجی CSV سفارش‌های payment_review، برای هر سفارش export شده یک audit record ثبت می‌شود.

## 6. Request ID

هر Response دارای Header زیر است:

    X-Request-ID

اگر Client یا Reverse Proxy مقدار معتبر بفرستد، همان مقدار حفظ می‌شود. در غیر این صورت RedShop مقدار امن تولید می‌کند.

برای trace کردن یک رخداد:

1. request_id را از Response، لاگ یا گزارش خطا بردار.
2. همان request_id را در لاگ‌های Django، apps.payment و apps.orders جستجو کن.
3. اگر پرداخت است، authority_hash را هم کنار request_id جستجو کن.

## 7. Log Redaction

لاگ‌ها قبل از خروج از handlerها از RedactingFilter عبور می‌کنند.

مواردی که ماسک می‌شوند:

- ایمیل
- موبایل ایران
- شماره کارت یا عددهای card-like
- Bearer token
- password
- secret
- token
- authorization
- api_key
- merchant_id

اگر در لاگی مقدار حساس خام دیدی، باید همان روز تست redaction اضافه شود.

## 8. CSP و Security Headers

در Local، CSP می‌تواند report-only باشد. در Production بعد از بررسی assetها:

    REDSHOP_ENFORCE_CSP=true

Headerهای امنیتی باید در responseها وجود داشته باشند، از جمله:

- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- Cross-Origin-Opener-Policy
- Content-Security-Policy یا Content-Security-Policy-Report-Only

## 9. حداقل متغیرهای Production

    DJANGO_SETTINGS_MODULE=RedShop.settings_production
    DJANGO_SECRET_KEY=<long-random-secret>
    DJANGO_DEBUG=false
    DJANGO_ALLOWED_HOSTS=example.com,www.example.com
    DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
    DJANGO_SECURE_SSL_REDIRECT=true
    DJANGO_SESSION_COOKIE_SECURE=true
    DJANGO_CSRF_COOKIE_SECURE=true
    REDSHOP_ENFORCE_CSP=true

## 10. چک‌لیست Incident پرداخت

1. request_id را از کاربر، لاگ یا response پیدا کن.
2. authority_hash را از لاگ payment callback پیدا کن.
3. order_number را از سفارش مرتبط پیدا کن.
4. وضعیت Order، Transaction و OrderAuditLog را کنار هم بررسی کن.
5. اگر سفارش payment_review است، ارسال خودکار انجام نده.
6. اگر موجودی آزاد شده، ارسال را فقط بعد از بررسی دستی انجام بده.
7. اگر پرداخت باید برگشت داده شود، Refund را در Gateway انجام بده.
8. نتیجه بررسی را در یادداشت داخلی یا سیستم پشتیبانی ثبت کن.

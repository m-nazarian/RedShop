
# RedShop

RedShop یک فروشگاه اینترنتی فارسی و راست‌به‌چپ بر پایه Django است که با تمرکز روی تجربه خرید، مدیریت سفارش، پرداخت، امنیت، یکپارچگی داده و آمادگی عملیاتی توسعه داده شده است.

این پروژه صرفاً یک نمونه ظاهری یا CRUD ساده نیست. RedShop تلاش می‌کند بخش‌های مهم یک فروشگاه واقعی را، از لیست محصول و سبد خرید تا ثبت سفارش، پرداخت، مدیریت موجودی، لاگ عملیاتی، audit trail و چک‌های قبل از دیپلوی، به شکل قابل تست و قابل نگهداری پیاده‌سازی کند.

> وضعیت پروژه: در حال hardening و آماده‌سازی برای ارائه رزومه‌ای/نمونه‌کار حرفه‌ای. پروژه برای اجرای واقعی نیازمند تنظیمات Production، دامنه، SSL، کلیدهای واقعی درگاه پرداخت، سرویس ایمیل، job scheduler و مانیتورینگ خارجی است.

---

## فهرست

- [نگاه کلی](#نگاه-کلی)
- [برای کارفرما یا مشتری](#برای-کارفرما-یا-مشتری)
- [برای همکار فنی](#برای-همکار-فنی)
- [قابلیت‌های اصلی](#قابلیت‌های-اصلی)
- [امنیت و یکپارچگی داده](#امنیت-و-یکپارچگی-داده)
- [پرداخت و مدیریت سفارش](#پرداخت-و-مدیریت-سفارش)
- [Observability و عملیات](#observability-و-عملیات)
- [ساختار پروژه](#ساختار-پروژه)
- [راه‌اندازی محلی](#راه‌اندازی-محلی)
- [دستورات مهم](#دستورات-مهم)
- [مستندات پروژه](#مستندات-پروژه)
- [محدودیت‌های فعلی](#محدودیت‌های-فعلی)
- [مسیر توسعه بعدی](#مسیر-توسعه-بعدی)

---

## نگاه کلی

RedShop یک monolith جنگویی با اپلیکیشن‌های جداگانه برای حساب کاربری، فروشگاه، سبد خرید، سفارش، پرداخت، کوپن و مقایسه محصول است. معماری پروژه ساده و قابل فهم نگه داشته شده، اما در بخش‌های حساس مثل پرداخت، سفارش، موجودی و امنیت از سرویس‌ها، تست‌ها، constraintهای دیتابیس و ابزارهای عملیاتی استفاده شده است.

هدف پروژه این نیست که خود را بزرگ‌تر از واقعیت نشان دهد. RedShop هنوز یک سیستم production-deployed عمومی نیست، اما بخش زیادی از دغدغه‌های جدی یک فروشگاه آنلاین در آن دیده شده و برای توسعه بیشتر پایه مناسبی دارد.

---

## برای کارفرما یا مشتری

RedShop نشان می‌دهد که یک فروشگاه آنلاین فقط صفحه محصول و سبد خرید نیست. بخش‌های مهم‌تری مثل درست ثبت شدن سفارش، خراب نشدن موجودی، قابل پیگیری بودن پرداخت، جلوگیری از نشت اطلاعات حساس، ثبت عملیات ادمین و داشتن مسیر عملیاتی برای خطاها هم در پروژه دیده شده‌اند.

از نگاه کسب‌وکار، پروژه روی این موارد تمرکز دارد:

- نمایش و جستجوی محصولات
- دسته‌بندی و برندها
- سبد خرید و ثبت سفارش
- پشتیبانی از پرداخت آنلاین
- کوپن و تخفیف
- مدیریت وضعیت سفارش
- حفظ تاریخچه مالی سفارش‌ها
- جلوگیری از ارسال خودکار سفارش‌های مشکوک به پرداخت
- ابزار بررسی سفارش‌های نیازمند بازبینی
- مستندات دیپلوی و عملیات
- تست‌های خودکار برای سناریوهای حساس

این پروژه می‌تواند پایه خوبی برای یک فروشگاه سفارشی باشد، اما برای استفاده تجاری واقعی باید نیازهای دامنه کسب‌وکار، طراحی UI نهایی، سرویس پرداخت واقعی، زیرساخت Production، پشتیبان‌گیری، مانیتورینگ و فرآیندهای پشتیبانی مشتری روی آن تکمیل شود.

---

## برای همکار فنی

از نگاه فنی، RedShop روی چند اصل بنا شده است:

- جدا نگه داشتن concernها در اپلیکیشن‌های Django
- استفاده از service layer برای منطق حساس سفارش و پرداخت
- استفاده از transaction و locking در مسیرهای مالی/موجودی
- تکیه نکردن صرف به منطق view یا admin برای حفظ یکپارچگی
- استفاده از database constraints برای جلوگیری از داده نامعتبر
- تست regression برای باگ‌های امنیتی و مالی
- مستندسازی عملیاتی به جای اکتفا به توضیح شفاهی
- logging قابل پیگیری با request_id
- redaction اطلاعات حساس در لاگ‌ها
- audit log برای عملیات حساس ادمین

پروژه تلاش می‌کند ساده بماند، اما در نقاطی که ریسک واقعی وجود دارد، محافظ‌های جدی‌تری داشته باشد.

---

## قابلیت‌های اصلی

### فروشگاه و محصول

- مدیریت محصولات، دسته‌بندی‌ها و برندها
- صفحه لیست محصول با pagination واقعی
- فیلتر و جستجوی محصول
- صفحه جزئیات محصول
- تصویر محصول
- ویژگی‌های محصول
- امتیاز و نظر کاربران
- خلاصه امتیاز و تعداد review روی کارت محصول
- علاقه‌مندی‌ها
- مقایسه محصول
- حذف استفاده از order_by تصادفی در مسیرهای حساس به performance

### حساب کاربری

- ثبت‌نام با اعتبارسنجی قوی‌تر
- اعتبارسنجی شماره موبایل ایران
- جلوگیری از ثبت موبایل تکراری
- بررسی قدرت رمز عبور
- محدودسازی تلاش‌های ناموفق ورود
- فرم‌های پروفایل بدون جمع‌آوری اطلاعات حساس plaintext
- آدرس‌های کاربر با constraint برای default address

### سبد خرید و سفارش

- checkout با کنترل مالکیت آدرس
- ثبت snapshot از اطلاعات محصول در سفارش
- پشتیبانی از تخفیف و کوپن
- مدیریت وضعیت سفارش
- حفظ تاریخچه مالی حتی در صورت حذف کاربر یا محصول
- جلوگیری از تغییر مستقیم فیلدهای مالی/وضعیت حساس در admin

### پرداخت

- پرداخت آنلاین با مدل Transaction
- callback idempotent
- کنترل تکرار callback موفق
- تفکیک وضعیت paid، failed، canceled و pending
- مدیریت late success بعد از آزادسازی موجودی
- انتقال سفارش‌های پرریسک به payment_review
- logging امن callback بدون ذخیره Authority خام

---

## امنیت و یکپارچگی داده

RedShop چند لایه محافظ برای کاهش خطاهای رایج فروشگاه اینترنتی دارد.

### Database constraints

نمونه‌هایی از constraintهای پروژه:

- معتبر بودن مبلغ تخفیف نسبت به subtotal سفارش
- سازگاری status و success در Transaction
- یکتا بودن provider و authority معتبر در Transaction
- جلوگیری از مقدار نامعتبر برای quantity و weight آیتم سفارش
- جلوگیری از قیمت جدید نامعتبر برای محصول
- جلوگیری از تخفیف بیشتر از قیمت محصول
- محدودیت مقدار امتیاز review
- یکتایی feature value برای محصول و feature
- فقط یک آدرس default برای هر کاربر

### Admin safety

در Django Admin، مسیرهای حساس مالی تا حد ممکن مستقیم قابل تغییر نیستند. تغییر وضعیت‌هایی مثل پرداخت شدن سفارش یا لغو سفارش باید از مسیر lifecycle انجام شود، نه با ویرایش دستی چند فیلد.

### Frontend safety

بخش‌هایی مثل live search و toast message از الگوهای امن‌تر DOM API و textContent استفاده می‌کنند و از تزریق HTML ناامن دور شده‌اند.

### Log redaction

لاگ‌های Production قبل از خروج از handlerها از RedactingFilter عبور می‌کنند. موارد زیر ماسک می‌شوند:

- ایمیل
- موبایل ایران
- شماره کارت یا عددهای card-like
- Bearer tokens
- password
- secret
- token
- authorization
- api_key
- merchant_id

---

## پرداخت و مدیریت سفارش

یکی از بخش‌های مهم پروژه، پرداخت و اثر آن روی موجودی و وضعیت سفارش است.

سناریوهای پوشش‌داده‌شده:

- پرداخت موفق عادی
- callback تکراری
- پرداخت ناموفق یا لغوشده
- سفارش پرداخت‌نشده‌ای که موجودی آن آزاد شده است
- پرداخت موفق دیرهنگام بعد از آزادسازی موجودی
- سفارش‌هایی که باید وارد payment_review شوند
- حفظ transaction history
- audit کردن عملیات حساس ادمین روی سفارش‌های نیازمند بررسی

### payment_review چیست؟

اگر پرداختی بعد از آزاد شدن موجودی موفق شود، سیستم نباید بی‌صدا سفارش را وارد پردازش ارسال کند؛ چون ممکن است موجودی قبلاً به فروش دیگری برگشته باشد. در این حالت سفارش به payment_review می‌رود تا ادمین وضعیت پرداخت، موجودی و تصمیم نهایی را دستی بررسی کند.

این رفتار از خراب شدن موجودی و ارسال اشتباه جلوگیری می‌کند.

---

## Observability و عملیات

RedShop فقط به پیاده‌سازی featureها اکتفا نکرده و برای عملیات هم ابزارهایی دارد.

### Request ID

هر response دارای header زیر است:

    X-Request-ID

این مقدار در لاگ‌ها هم ثبت می‌شود تا بتوان یک خطای checkout یا payment را از response تا log دنبال کرد.

### Payment callback logging

callback پرداخت event ساختاریافته ثبت می‌کند. مقدار خام Authority در لاگ ذخیره نمی‌شود. به جای آن authority_hash کوتاه ثبت می‌شود تا بتوان callbackهای مرتبط را بدون نشت داده حساس به هم وصل کرد.

### OrderAuditLog

برای عملیات حساس ادمین، مثل export سفارش‌های payment_review، رکورد audit ثبت می‌شود. این رکوردها شامل موارد زیر هستند:

- order
- actor
- action
- request_id
- message
- metadata
- created_at

Audit logها در admin فقط خواندنی هستند.

### آزادسازی سفارش‌های رهاشده

برای جلوگیری از قفل شدن دائمی موجودی سفارش‌های آنلاین پرداخت‌نشده، command زیر وجود دارد:

    python manage.py release_expired_orders --older-than-minutes 30 --limit 200

برای اجرای آزمایشی بدون تغییر داده:

    python manage.py release_expired_orders --older-than-minutes 30 --dry-run

### Deployment readiness check

پروژه command اختصاصی برای بررسی آماده بودن تنظیمات Production دارد:

    python manage.py redshop_deployment_check

و برای حالت سخت‌گیرانه:

    python manage.py redshop_deployment_check --strict

---

## ساختار پروژه

ساختار کلی اپلیکیشن‌ها:

    RedShop/
      settings.py
      settings_production.py
      env.py
      security.py
      request_id.py
      logging_config.py
      logging_redaction.py
      deployment_checks.py

    apps/
      account/
      cart/
      coupons/
      orders/
      payment/
      shop/
      compare/

    docs/
      DEPLOYMENT_FA.md
      OPERATIONS_FA.md
      ROADMAP_RESUME_FA.md

نقش چند اپلیکیشن مهم:

- account: کاربر، ثبت‌نام، ورود، پروفایل و آدرس‌ها
- shop: محصول، دسته‌بندی، برند، review، feature، favorite و listing
- cart: سبد خرید
- orders: سفارش، آیتم سفارش، transaction، lifecycle، audit log
- payment: فرآیند پرداخت و callback
- coupons: کوپن و محدودیت مصرف
- compare: مقایسه محصول

---

## راه‌اندازی محلی

پیش‌نیازها:

- Python
- PostgreSQL
- virtualenv
- نصب dependencyها از requirements.txt

مراحل پیشنهادی:

    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt

فایل محیطی نمونه:

    Copy-Item .env.example .env

سپس مقدارهای دیتابیس و تنظیمات محلی را در .env تنظیم کن.

اجرای migration:

    python manage.py migrate

اجرای پروژه:

    python manage.py runserver

---

## دستورات مهم

### تست‌ها

    python manage.py test -v 2

### بررسی migration

    python manage.py makemigrations --check --dry-run

### Django check

    python manage.py check

### بررسی Production readiness

    python manage.py redshop_deployment_check
    python manage.py redshop_deployment_check --strict

### آزادسازی سفارش‌های منقضی

    python manage.py release_expired_orders --older-than-minutes 30 --limit 200

### Dry-run آزادسازی سفارش‌ها

    python manage.py release_expired_orders --older-than-minutes 30 --dry-run

---

## مستندات پروژه

- docs/DEPLOYMENT_FA.md: راهنمای آماده‌سازی دیپلوی، envها، security headers، CSP، CI و commandهای عملیاتی
- docs/OPERATIONS_FA.md: Runbook عملیاتی برای پرداخت، payment_review، request_id، authority_hash، audit log و redaction
- docs/ROADMAP_RESUME_FA.md: مسیر hardening پروژه برای ارائه رزومه‌ای و فنی

---

## CI و quality gates

GitHub Actions CI برای پروژه تعریف شده و این موارد را اجرا می‌کند:

- compile کردن فایل‌های Python
- بررسی migrationهای ساخته‌نشده
- Django system check
- گزارش deployment readiness
- اجرای تست‌ها

این CI جایگزین بررسی Production واقعی نیست، اما جلوی بسیاری از regressionهای رایج را قبل از merge یا push می‌گیرد.

---

## محدودیت‌های فعلی

برای شفافیت، این پروژه هنوز این موارد را به شکل کامل نهایی نکرده است:

- دیپلوی عمومی واقعی با دامنه و SSL انجام نشده است.
- مانیتورینگ خارجی مثل Sentry یا Prometheus متصل نشده است.
- job scheduler واقعی برای اجرای دوره‌ای commandها باید در زیرساخت Production تنظیم شود.
- UI نهایی می‌تواند از نظر طراحی، accessibility و تجربه موبایل بیشتر polish شود.
- payment_review فعلاً مسیر بررسی و audit دارد، اما workflow کامل resolution یا refund داخلی هنوز می‌تواند توسعه داده شود.
- تست‌های performance در سطح محدود هستند و load test واقعی انجام نشده است.
- اتصال به سرویس ایمیل و درگاه پرداخت واقعی نیازمند env و secretهای Production است.

این محدودیت‌ها ضعف پنهان نیستند؛ مسیر طبیعی تبدیل پروژه از نمونه حرفه‌ای به محصول Production هستند.

---

## مسیر توسعه بعدی

اولویت‌های منطقی بعدی:

1. اضافه کردن event logهای دقیق‌تر برای outcomeهای پرداخت: success، failure، cancel و payment_review
2. اضافه کردن actionهای امن برای resolve کردن payment_review در admin
3. اضافه کردن audit log برای resolution، refund note و re-reserve decision
4. اضافه کردن Sentry یا سرویس مشابه برای error reporting
5. افزودن correlation ID در reverse proxy
6. افزودن README badge بعد از اجرای موفق CI
7. بهبود UI موبایل، accessibility و SEO
8. افزودن integration testهای بیشتر برای checkout و payment
9. افزودن معماری تصویری یا sequence diagram برای portfolio

---

## جمع‌بندی

RedShop یک پروژه فروشگاهی Django است که علاوه بر قابلیت‌های معمول فروشگاه، روی بخش‌هایی تمرکز کرده که در پروژه‌های واقعی دردسرساز می‌شوند: پرداخت، موجودی، یکپارچگی مالی، امنیت فرم‌ها، XSS، admin safety، audit log، request tracing، redaction لاگ‌ها، commandهای عملیاتی و چک‌های قبل از دیپلوی.

این پروژه نه یک SaaS آماده فروش است و نه صرفاً یک تمرین ساده. RedShop یک نمونه‌کار فنی قابل دفاع است که نشان می‌دهد توسعه‌دهنده به جز ساخت feature، به نگهداری، خطاهای واقعی، امنیت، عملیات و قابل اعتماد بودن سیستم هم فکر کرده است.

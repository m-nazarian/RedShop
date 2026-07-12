# مرحله بیست‌وهشتم: افزودن GitHub Actions CI

در این مرحله یک workflow برای GitHub Actions اضافه شد تا چک‌های اصلی پروژه روی push و pull request اجرا شوند.

## کارهایی که CI انجام می‌دهد

- نصب Python
- نصب dependencyهای پروژه
- اجرای `compileall`
- اجرای `makemigrations --check --dry-run`
- اجرای `manage.py check`
- اجرای تست‌های Django

## نکته‌های فنی

- برای دیتابیس CI از سرویس PostgreSQL استفاده شده است.
- چند env متداول برای Django و دیتابیس در workflow تنظیم شده‌اند.
- اگر `settings.py` از envهای دیگری استفاده کرده باشد، اسکریپت تا حد ممکن آن‌ها را هم به workflow اضافه می‌کند.
- دسترسی workflow محدود به `contents: read` تنظیم شده است.

## نتیجه

از این مرحله به بعد هر push روی `main` باید از چک‌های اصلی Django عبور کند.

## اصلاح ادامه مرحله

در اجرای اول، بخش اعتبارسنجی workflow با syntax مخصوص Bash داخل PowerShell اجرا شده بود و مرحله قبل از commit متوقف شد. در ادامه مرحله، اعتبارسنجی با فایل Python موقت انجام شد و workflow برای PowerShell-safe بودن بررسی شد.

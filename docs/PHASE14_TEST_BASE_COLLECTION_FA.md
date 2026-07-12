# مرحله چهاردهم: جلوگیری از collect شدن کلاس پایه تست

در مرحله قبل مشخص شد `RedShopTestBase` هنوز توسط test runner اجرا می‌شود.

## تغییرات

- `RedShopTestBase` دیگر از `TestCase` ارث‌بری نمی‌کند.
- کلاس‌های واقعی تست به شکل `RedShopTestBase, TestCase` تعریف شدند.
- تست تنظیمات logging از کلاس پایه جدا شد.
- تست logging به کلاس مستقل `ProjectSettingsTests` منتقل شد.

## نتیجه

کلاس پایه فقط fixture و helper مشترک نگه می‌دارد و دیگر خودش به‌عنوان test case اجرا نمی‌شود.

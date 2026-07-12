# مرحله شانزدهم: پاک‌سازی Importهای استفاده‌نشده

در این مرحله Importها با AST اسکن شدند و فقط موارد بسیار امن حذف شدند.

## خروجی اسکن

## apps\shop\views.py
- خط 3: `OrderedDict` از `from collections import OrderedDict`

## apps\shop\services.py
- خط 2: `Category` از `from .models import Category`

## تغییر انجام‌شده

- Import استفاده‌نشده `OrderedDict` از `apps/shop/views.py` حذف شد.

## نتیجه

پاک‌سازی به‌صورت محافظه‌کارانه انجام شد تا رفتار runtime پروژه تغییر نکند.

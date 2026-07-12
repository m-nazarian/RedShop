# مرحله بیست‌وسوم: کوچک‌کردن payment_process

در این مرحله چند helper خصوصی به `apps/payment/views.py` اضافه شد تا بدنه ابتدایی `payment_process` خواناتر شود.

## تغییرات

- خواندن سفارش آنلاین به `_get_online_order_for_payment` منتقل شد.
- رندر سفارش از قبل پرداخت‌شده به `_render_already_paid_order` منتقل شد.
- رندر سفارش لغوشده/stock_released به `_render_released_order_failure` منتقل شد.

## نتیجه

رفتار پرداخت تغییر نکرد، اما مسیرهای ابتدایی `payment_process` کوتاه‌تر و قابل نگهداری‌تر شدند.

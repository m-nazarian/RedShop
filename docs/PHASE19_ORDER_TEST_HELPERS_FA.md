# مرحله نوزدهم: سبک‌سازی تست‌های سفارش

در مرحله هفدهم تست session کهنه checkout طولانی شده بود. در این مرحله منطق تکراری و ساخت داده تستی به helperهای کلاس پایه منتقل شد.

## تغییرات

- ساخت سفارش پرداخت‌شده قدیمی به `_create_paid_stale_order` منتقل شد.
- انتخاب payment method غیرآنلاین به `_choose_cash_payment_method` منتقل شد.
- مقداردهی فیلدهای required سفارش به `_sample_value_for_required_order_field` منتقل شد.
- ساخت cart تستی داخل session به `_put_single_product_cart_in_session` منتقل شد.
- تست `test_stale_paid_checkout_session_is_ignored_before_new_order` کوتاه‌تر و خواناتر شد.

## نتیجه

تست‌ها همان رفتار قبلی را پوشش می‌دهند، اما فایل تست قابل نگهداری‌تر شد.

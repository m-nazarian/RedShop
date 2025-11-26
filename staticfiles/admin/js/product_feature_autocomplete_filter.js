/* admin/js/product_feature_autocomplete_filter.js
   نسخه اصلاح‌شده — با فَـالبک به window.jQuery، تاخیر/تلاش مجدد،
   جلوگیری از double-init، ارسال category_id و پشتیبانی از inlines دینامیک.
*/

(function (/* jQuery will be passed in when available */) {
    'use strict';

    // Helper: امن بررسی می‌کنه که jQuery ادمین یا window.jQuery موجوده
    function getJQuery() {
        return (window.django && window.django.jQuery) ? window.django.jQuery : window.jQuery;
    }

    // تنظیمات بازرس و تلاش مجدد
    const CHECK_INTERVAL_MS = 100;   // هر 100ms بررسی می‌کنه
    const MAX_TRIES = 60;            // حداکثر 60 بار = ~6s

    // selectorِ المنت‌هایی که می‌خوایم select2 روشون اجرا کنیم
    const SELECTOR = 'select[data-autocomplete-light-function]';

    // نگه‌دارنده برای این که دوبار init نکنیم
    const initialized = new WeakSet();

    // تابعی که یک المنت <select> رو initialize می‌کنه (اگر قبلاً نشده باشه)
    function initSelect($, el) {
        try {
            const $el = $(el);

            // اگر از قبل select2 روش فعال شده باشه، رد کن
            if ($el.hasClass('select2-hidden-accessible') || initialized.has(el)) {
                return;
            }

            // اگر select2 در دسترس نیست، خطا لاگ می‌کنه و برمی‌گرده
            if (!$.fn || !$.fn.select2) {
                console.error('Select2 not available for element:', el);
                return;
            }

            // config برای select2
            $el.select2({
                width: '100%',
                placeholder: $el.attr('data-placeholder') || 'انتخاب کنید...',
                allowClear: true,
                ajax: {
                    // Select2 خودش urlِ autocomplete را از data-* های ویجت ادمین می‌گیرد
                    delay: 250,
                    dataType: 'json',
                    // زمانی که Select2 درخواست می‌ده، این تابع داده‌های اضافه می‌سازه
                    data: function (params) {
                        // تلاش برای گرفتن category_id از فرم ادمین:
                        // اول با idِ فیلد پیشفرض (id_category) سپس fallback به name="category"
                        let categoryId = null;
                        const catById = $('#id_category');
                        if (catById.length) {
                            categoryId = catById.val();
                        } else {
                            const catByName = $('select[name="category"], input[name="category"]');
                            if (catByName.length) categoryId = catByName.val();
                        }

                        return {
                            q: params.term || '',
                            page: params.page || 1,
                            category_id: categoryId || ''
                        };
                    },
                    transport: function (params, success, failure) {
                        // transport فقط برای اطمینان: شامل CSRF و header X-Requested-With
                        const $request = $.ajax(params);
                        $request.done(success);
                        $request.fail(failure);
                        return $request;
                    }
                },
                // وقتی results از سرور اومد، اینکه چطور نمایش داده بشه رو می‌ذاره خودش
                escapeMarkup: function (m) { return m; } // اجازه می‌ده HTML در optionها در صورت نیاز بیاد
            });

            // نشان می‌ده این المنت init شده
            initialized.add(el);
            // debug
            if (window.console && window.console.debug) {
                console.debug('Initialized select2 autocomplete for', el);
            }
        } catch (err) {
            console.error('Error initializing select2 for element', el, err);
        }
    }

    // تابعی که تمام selectهای مورد نظر را پیدا و init می‌کند
    function initAllSelects($) {
        const $selects = $(SELECTOR);
        if (!$selects.length) return false;
        $selects.each(function () {
            initSelect($, this);
        });
        return $selects.length > 0;
    }

    // تابع اصلی: منتظر jQuery و select2 می‌مونه و سپس init می‌کنه
    function waitForJqueryAndInit(triesLeft) {
        const $ = getJQuery();

        if ($ && $.fn && $.fn.select2) {
            // وقتی jQuery و select2 هر دو هستن — init رو اجرا کن
            $(function () {
                // init اولیه
                initAllSelects($);

                // تنظیم یک MutationObserver برای شناسایی inlines که پویا اضافه می‌شن
                try {
                    const target = document.querySelector('body');
                    if (target && window.MutationObserver) {
                        const observer = new MutationObserver(function (mutationsList) {
                            for (let m of mutationsList) {
                                if (m.addedNodes && m.addedNodes.length) {
                                    // هرگاه node جدید اضافه شد، سعی می‌کنیم selectها رو init کنیم
                                    initAllSelects($);
                                }
                            }
                        });
                        observer.observe(target, { childList: true, subtree: true });
                    }
                } catch (obsErr) {
                    console.warn('MutationObserver unavailable or failed:', obsErr);
                }
            });

            return;
        }

        if (triesLeft <= 0) {
            console.error('product_feature_autocomplete_filter.js: jQuery or select2 did not become available in time.');
            return;
        }

        // تلاش مجدد بعد از تأخیر
        setTimeout(function () {
            waitForJqueryAndInit(triesLeft - 1);
        }, CHECK_INTERVAL_MS);
    }

    // شروع: از window scope بدون ارجاع مستقیم به نام 'django' استفاده می‌کنیم
    waitForJqueryAndInit(MAX_TRIES);

})(/* no argument here; jQuery resolved inside with window.* checks */);

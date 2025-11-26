// static/admin/js/product_feature_autocomplete_filter.js
(function($) {
    $(document).ready(function() {

        // ----------------------------------------------------
        // 1. تاشو کردن بخش اینلاین (Collapsible Section)
        // ----------------------------------------------------
        // اگر collapse.js جنگو 4+ را ندارید، این بخش تاشو کردن را انجام می‌دهد:
        $('.inline-group .collapse').each(function() {
            const $fieldset = $(this);
            const $h2 = $fieldset.find('h2:first');
            const $a = $('<a class="inline-toggler" href="#"></a>');

            $h2.wrapInner($a);
             $h2.addClass('collapsed'); // شروع به صورت تاشده
             $fieldset.find('div.module').hide();

             $h2.on('click', function(e) {
                 e.preventDefault();
                 $(this).toggleClass('collapsed').next('div.module').slideToggle(200);
             });
         });

        // ----------------------------------------------------
        // 2. فیلترینگ پویای ویژگی‌ها با AJAX
        // ----------------------------------------------------
        const $categoryField = $('#id_category');
        // ✅ آدرس URL باید با تعریف شما در urls.py مطابقت داشته باشد:
        const featureUrlBase = "/shop/api/features/";

        function loadFeatures(categoryId) {
            // تمامی فیلدهای 'ویژگی' در اینلاین‌های جاری
            const $featureFields = $('.field-feature select[name$="-feature"]');

            if (!categoryId) {
                $featureFields.empty();
                $featureFields.append($('<option value="">--- دسته‌بندی را انتخاب کنید ---</option>'));
                return;
            }

            $featureFields.empty();
            $featureFields.append($('<option value="">در حال بارگذاری ویژگی‌ها...</option>'));

            // فراخوانی AJAX
            $.ajax({
                url: featureUrlBase + categoryId + '/',
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    const features = data.features;
                    $featureFields.empty(); // خالی کردن مجدد
                    $featureFields.append($('<option value="">--- یک ویژگی انتخاب کنید ---</option>'));

                    if (features.length === 0) {
                        $featureFields.append($('<option value="">--- ویژگی برای این دسته تعریف نشده است ---</option>'));
                    } else {
                        // پر کردن Dropdown ها با ویژگی‌های فیلتر شده
                        $.each(features, function(index, feature) {
                            $featureFields.append($('<option></option>')
                                .attr('value', feature.id)
                                .text(feature.name));
                        });
                    }
                },
                error: function(xhr, status, error) {
                    $featureFields.empty();
                    $featureFields.append($('<option value="">خطا در بارگذاری ویژگی‌ها: ' + error + '</option>'));
                }
            });
        }

        // 💡 عملکرد: بارگذاری مجدد ویژگی‌ها هنگام تغییر دسته
        $categoryField.on('change', function() {
            const selectedCategoryId = $(this).val();
            loadFeatures(selectedCategoryId);
        });

        // 💡 عملکرد: بارگذاری اولیه (برای صفحه ویرایش که دسته از قبل انتخاب شده)
        if ($categoryField.val()) {
             loadFeatures($categoryField.val());
        }

        // 💡 عملکرد: تنظیم مجدد ویژگی‌ها برای ردیف‌های جدید (Add Another Product Feature Value)
        // این کار باعث می‌شود ردیف‌های تازه اضافه شده نیز ویژگی‌های فیلترشده را دریافت کنند.
        $('#product_feature_value_set-group').on('click', '.add-row a', function() {
            // تاخیر کوتاه برای اطمینان از ساخت کامل ردیف جدید
            setTimeout(function() {
                const selectedCategoryId = $categoryField.val();
                if (selectedCategoryId) {
                    // آخرین فیلد ویژگی که اضافه شده را پیدا کن و لود کن
                    const $lastFeatureField = $('.field-feature select[name$="-feature"]').last();

                    $.ajax({
                        url: featureUrlBase + selectedCategoryId + '/',
                        type: 'GET',
                        dataType: 'json',
                        success: function(data) {
                            const features = data.features;
                            $lastFeatureField.empty();
                            $lastFeatureField.append($('<option value="">--- یک ویژگی انتخاب کنید ---</option>'));

                            $.each(features, function(index, feature) {
                                $lastFeatureField.append($('<option></option>')
                                    .attr('value', feature.id)
                                    .text(feature.name));
                            });
                        }
                        // عدم مدیریت خطا برای سادگی
                    });
                }
            }, 10);
        });

    });
})(django.jQuery);
window.addEventListener('load', function() {
    const $ = (window.django && window.django.jQuery) ? window.django.jQuery : window.jQuery;

    if (!$) {
        console.error("❌ Critical Error: jQuery is not loaded in Django Admin!");
        return;
    }

    console.log("✅ jQuery Found & Script Started! (Edit Support Mode)");

    $(document).ready(function() {
        const categoryField = $('#id_category');

        if (categoryField.length === 0) {
            return;
        }

        function initSelect2($select) {
            if ($select.data('select2')) {
                return;
            }

            // قبل از خالی کردن، چک می‌کنیم آیا مقداری از قبل انتخاب شده؟
            const $selectedOption = $select.find('option:selected');
            const initialValue = $selectedOption.val();
            const initialText = $selectedOption.text();

            // پاک کردن همه گزینه‌ها (برای حذف گزینه‌های نامربوط جنگو)
            $select.empty();

            // اگر مقداری داشتیم، دوباره آن را می‌سازیم و اضافه می‌کنیم
            if (initialValue && initialText) {
                const option = new Option(initialText, initialValue, true, true);
                $select.append(option).trigger('change');
            }
            // ---------------------------------------

            $select.select2({
                width: '100%',
                placeholder: 'جستجو برای انتخاب ویژگی...',
                language: "fa",
                allowClear: true,
                ajax: {
                    url: '/categoryfeature/autocomplete/',
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            term: params.term,
                            category_id: categoryField.val()
                        };
                    },
                    processResults: function(data) {
                        return { results: data.results };
                    },
                    cache: true
                }
            });
        }

        function updateFeatures() {
            const categoryId = categoryField.val();
            const featureSelects = $('select[name^="feature_values-"][name$="-feature"]');

            featureSelects.each(function() {
                const $select = $(this);

                if (!categoryId) {
                    $select.val(null).trigger('change');
                    $select.prop('disabled', true);
                    return;
                }

                $select.prop('disabled', false);

                if (!$select.hasClass("select2-hidden-accessible")) {
                    initSelect2($select);
                }
            });
        }

        // --- Events ---

        updateFeatures();

        categoryField.on('change', function() {
            console.log("🔀 Category Changed -> Resetting Features");
            // وقتی دسته عوض می‌شود، باید مقادیر قبلی پاک شوند
            $('select[name^="feature_values-"][name$="-feature"]').each(function(){
                const $el = $(this);
                $el.empty(); // پاک کردن آپشن‌ها
                $el.val(null).trigger('change');
            });
            updateFeatures();
        });

        $(document).on('formset:added', function(event, $row, formsetName) {
            if (formsetName === 'feature_values') {
                const $newSelect = $row.find('select[name$="-feature"]');
                const categoryId = categoryField.val();

                $newSelect.empty();

                if (categoryId) {
                    $newSelect.prop('disabled', false);
                    initSelect2($newSelect);
                } else {
                    $newSelect.prop('disabled', true);
                }
            }
        });
    });
});
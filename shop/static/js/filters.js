document.addEventListener("DOMContentLoaded", () => {

    // ------------------------------------------------------------------
    // 1. تعریف متغیرهای اصلی DOM
    // ------------------------------------------------------------------
    const productContainer = document.getElementById("product-container");
    const allFiltersContainer = document.getElementById("all-filters-container");
    const csrfToken = document.getElementById("csrf-token").value;


    let rangeInput = null;
    let priceValueDisplay = null;

    // تابع Debounce برای جلوگیری از درخواست‌های مکرر
    const debounce = (func, delay) => {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };

    // ------------------------------------------------------------------
    // 2. تابع جمع‌آوری داده‌ها (Payload Creator)
    // ------------------------------------------------------------------
    const getSelectedFilters = () => {
        const selected = {};

        // جمع‌آوری فیلترهای کاربر (برند، رنگ، قیمت و...)
        const filters = document.querySelectorAll(".filter-input");

        filters.forEach(f => {
            const key = f.dataset.filter;

            // برای چک‌باکس‌ها
            if (f.type === 'checkbox' && f.checked) {
                if (!selected[key]) selected[key] = [];
                selected[key].push(f.value);
            }

            // برای Dropdown مرتب‌سازی (Sort)
            if (f.tagName === 'SELECT') {
                selected[key] = f.value;
            }

            // برای رنج قیمت
            if (f.type === 'range') {
                selected[key] = f.value;
            }
        });

        // خواندن اسلاگ دسته‌بندی از اینپوت مخفی و اضافه کردن به درخواست
        const catInput = document.getElementById("page-category-slug");
        if (catInput && catInput.value) {
            selected['category_slug'] = catInput.value;
        }

        return selected;
    };

    // ------------------------------------------------------------------
    // 3. تابع اصلی: ارسال و دریافت AJAX
    // ------------------------------------------------------------------
    const updateProducts = () => {
        const selected = getSelectedFilters();

        productContainer.style.opacity = '0.5';

        fetch("/products/filter/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify(selected)
        })
        .then(res => res.json())
        .then(data => {
            productContainer.style.opacity = '1';

            // 1. به‌روزرسانی لیست محصولات
            if (data.html_products) {
                productContainer.innerHTML = data.html_products;
            }

            // 2. به‌روزرسانی نوار کناری فیلترها
            if (data.html_filters) {
                allFiltersContainer.innerHTML = data.html_filters;

                // 3. فعال‌سازی مجدد شنوندگان برای المان‌های جدید نوار کناری
                reinitializeListeners();
            }
        })
        .catch(err => {
            console.error("خطا در فیلتر محصولات:", err);
            productContainer.style.opacity = '1';
        });
    };

    // ------------------------------------------------------------------
    // 4. تابع فعال‌سازی مجدد شنوندگان و Collapsible (پس از AJAX)
    // ------------------------------------------------------------------

    // تابع کمکی برای منطق Collapsible
    const toggleCollapsible = (e) => {
        const header = e.currentTarget;
        const content = header.nextElementSibling;
        header.classList.toggle('active');

        if (content.style.maxHeight) {
            content.style.maxHeight = null; // بستن
        } else {
            content.style.maxHeight = content.scrollHeight + "px"; // باز کردن
        }
    };

    // تابع Debounce شده برای فیلتر
    const debouncedUpdateProducts = debounce(updateProducts, 300);

    const reinitializeListeners = () => {

        // الف) متصل کردن شنوندگان به فیلترهای چک‌باکس و دراپ‌داون
        document.querySelectorAll(".filter-input").forEach(f => {
            // فقط به چک‌باکس‌ها و select شنونده 'change' فوری می‌دهیم
            if (f.type === 'checkbox' || f.tagName === 'SELECT') {
                // پاک کردن لیسنرهای احتمالی قبلی برای جلوگیری از تکرار
                f.removeEventListener("change", updateProducts);
                f.addEventListener("change", updateProducts);
            }
        });

        // ب) متصل کردن شنوندگان به رنج قیمت (با Debounce)
        rangeInput = document.getElementById("price-range");
        priceValueDisplay = document.getElementById("price-value");

        if (rangeInput && priceValueDisplay) {
            // آپدیت عدد قیمت هنگام کشیدن (بدون درخواست سرور)
            rangeInput.removeEventListener("input", updatePriceDisplay);
            rangeInput.addEventListener("input", updatePriceDisplay);

            // ارسال درخواست سرور فقط وقتی موس رها شد (change)
            rangeInput.removeEventListener("change", updateProducts);
            rangeInput.addEventListener("change", updateProducts);
        }

        // ج) فعال‌سازی Collapsible برای بخش‌های جدید نوار کناری
        document.querySelectorAll('.filter-group h3').forEach(header => {
            header.removeEventListener('click', toggleCollapsible);
            header.classList.add('collapsible-header');
            header.addEventListener('click', toggleCollapsible);
        });
    };

    // تابع کمکی برای نمایش لحظه‌ای قیمت
    const updatePriceDisplay = () => {
        if (priceValueDisplay) {
            priceValueDisplay.textContent = `تا ${Number(rangeInput.value).toLocaleString()} تومان`;
        }
    };


    // ------------------------------------------------------------------
    // 5. فراخوانی اولیه
    // ------------------------------------------------------------------

    // فراخوانی اولیه برای متصل کردن شنوندگان به فیلترهای بارگذاری اولیه
    reinitializeListeners();

    // اتصال رویداد به دراپ‌داون مرتب‌سازی (که بیرون از سایدبار بود)
    const sortSelect = document.getElementById("sort-select");
    if(sortSelect) {
        sortSelect.addEventListener("change", updateProducts);
    }
});
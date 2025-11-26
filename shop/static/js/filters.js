document.addEventListener("DOMContentLoaded", () => {

    // ------------------------------------------------------------------
    // 1. تعریف متغیرهای اصلی DOM
    // ------------------------------------------------------------------
    const productContainer = document.getElementById("product-container");
    const allFiltersContainer = document.getElementById("all-filters-container");
    const csrfToken = document.getElementById("csrf-token").value;


    let rangeInput = null;
    let priceValueDisplay = null;

    // تابع Debounce برای جلوگیری از درخواست‌های مکرر (مثل رنج قیمت)
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
        // باید فیلترها را هر بار دوباره بگیریم چون نوار کناری ممکن است آپدیت شود.
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

            // برای رنج قیمت (که data-filter='max_price' دارد)
            if (f.type === 'range') {
                selected[key] = f.value;
            }
        });

        return selected;
    };

    // ------------------------------------------------------------------
    // 3. تابع اصلی: ارسال و دریافت AJAX
    // ------------------------------------------------------------------
    const updateProducts = () => {
        const selected = getSelectedFilters();

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
        .catch(err => console.error("خطا در فیلتر محصولات:", err));
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
                f.removeEventListener("change", updateProducts); // حذف قبلی (جلوگیری از تکرار)
                f.addEventListener("change", updateProducts);
            }
        });

        // ب) متصل کردن شنوندگان به رنج قیمت (با Debounce)
        rangeInput = document.getElementById("price-range");
        priceValueDisplay = document.getElementById("price-value");

        if (rangeInput && priceValueDisplay) {
            rangeInput.removeEventListener("input", updatePriceDisplay);
            rangeInput.addEventListener("input", updatePriceDisplay);

            rangeInput.removeEventListener("change", debouncedUpdateProducts);
            rangeInput.addEventListener("change", debouncedUpdateProducts);
        }

        // ج) فعال‌سازی Collapsible برای بخش‌های جدید نوار کناری
        document.querySelectorAll('.filter-group h3').forEach(header => {
            header.removeEventListener('click', toggleCollapsible); // حذف قبلی
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
});
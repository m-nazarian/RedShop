
document.addEventListener("DOMContentLoaded", () => {

    // ------------------------------------------------------------------
    // 1. تعریف متغیرهای اصلی DOM
    // ------------------------------------------------------------------
    const productContainer = document.getElementById("product-container");
    const allFiltersContainer = document.getElementById("all-filters-container");
    const csrfToken = document.getElementById("csrf-token").value;

    let rangeInput = null;
    let priceValueDisplay = null;

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
        const filters = document.querySelectorAll(".filter-input");

        filters.forEach(f => {
            const key = f.dataset.filter;

            if (f.type === 'checkbox' && f.checked) {
                if (!selected[key]) selected[key] = [];
                selected[key].push(f.value);
            }

            if (f.tagName === 'SELECT') {
                selected[key] = f.value;
            }

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
            if (data.html_products) {
                productContainer.innerHTML = data.html_products;
            }

            if (data.html_filters) {
                allFiltersContainer.innerHTML = data.html_filters;

                reinitializeListeners();
            }
        })
        .catch(err => console.error("خطا در فیلتر محصولات:", err));
    };

    // ------------------------------------------------------------------
    // 4. تابع فعال‌سازی مجدد شنوندگان و Collapsible (پس از AJAX)
    // ------------------------------------------------------------------

    const toggleCollapsible = (e) => {
        const header = e.currentTarget;
        const content = header.nextElementSibling;
        header.classList.toggle('active');

        if (content.style.maxHeight) {
            content.style.maxHeight = null;
        } else {
            content.style.maxHeight = content.scrollHeight + "px";
        }
    };

    const debouncedUpdateProducts = debounce(updateProducts, 300);

    const reinitializeListeners = () => {

        document.querySelectorAll(".filter-input").forEach(f => {
            if (f.type === 'checkbox' || f.tagName === 'SELECT') {
                f.removeEventListener("change", updateProducts);
                f.addEventListener("change", updateProducts);
            }
        });

        rangeInput = document.getElementById("price-range");
        priceValueDisplay = document.getElementById("price-value");

        if (rangeInput && priceValueDisplay) {
            rangeInput.removeEventListener("input", updatePriceDisplay);
            rangeInput.addEventListener("input", updatePriceDisplay);

            rangeInput.removeEventListener("change", debouncedUpdateProducts);
            rangeInput.addEventListener("change", debouncedUpdateProducts);
        }

        document.querySelectorAll('.filter-group h3').forEach(header => {
            header.removeEventListener('click', toggleCollapsible);
            header.classList.add('collapsible-header');
            header.addEventListener('click', toggleCollapsible);
        });
    };

    const updatePriceDisplay = () => {
        if (priceValueDisplay) {
            priceValueDisplay.textContent = `تا ${Number(rangeInput.value).toLocaleString()} تومان`;
        }
    };


    // ------------------------------------------------------------------
    // 5. فراخوانی اولیه
    // ------------------------------------------------------------------

    reinitializeListeners();
});
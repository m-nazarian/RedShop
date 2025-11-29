document.addEventListener("DOMContentLoaded", function() {

    const contentContainer = document.getElementById("profile-dynamic-content");
    const tabs = document.querySelectorAll(".tab-link");
    let currentUrl = ""; // ذخیره آدرس تب فعلی

    // تابع Debounce (برای تاخیر در جستجو)
    const debounce = (func, delay) => {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };

    // تابع اصلی لود محتوا
    function loadContent(url) {
        currentUrl = url.split('?')[0]; // آدرس پایه را نگه می‌داریم

        // 1. نمایش لودینگ
        contentContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center py-20 text-gray-500">
                <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-4"></div>
                <p>در حال دریافت اطلاعات...</p>
            </div>
        `;

        // 2. درخواست AJAX
        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.text();
            })
            .then(html => {
                // 3. قرار دادن HTML
                contentContainer.innerHTML = html;

                // 4. ✅ فعال‌سازی قابلیت‌های محتوای جدید (مثل جستجو)
                attachDynamicEvents();
            })
            .catch(error => {
                console.error("Error loading content:", error);
                contentContainer.innerHTML = `
                    <div class="text-center py-10 text-red-500">
                        <p>متأسفانه مشکلی پیش آمد.</p>
                        <button onclick="location.reload()" class="mt-4 text-blue-600 underline">تلاش مجدد</button>
                    </div>
                `;
            });
    }

    // تابع متصل کردن رویدادها به محتوای لود شده
    function attachDynamicEvents() {
        const searchInput = document.getElementById("order-search-input");

        if (searchInput) {
            // فوکس را در انتهای متن نگه دار (برای تجربه کاربری بهتر)
            const val = searchInput.value;
            searchInput.focus();
            searchInput.setSelectionRange(val.length, val.length);

            // شنود کردن تایپ کاربر
            searchInput.addEventListener("input", debounce(function(e) {
                const query = e.target.value.trim();

                // ساخت آدرس جدید همراه با کوئری جستجو
                // مثال: /orders/api/my-orders/?q=mobile
                let searchUrl = `${currentUrl}?q=${encodeURIComponent(query)}`;

                // ارسال درخواست جدید (بدون لودینگ کامل صفحه برای حس بهتر، یا با لودینگ)
                // اینجا از همان loadContent استفاده می‌کنیم
                loadContent(searchUrl);

            }, 1000)); // 1000 میلی‌ثانیه تاخیر
        }
    }

    // هندل کردن کلیک روی تب‌ها
    tabs.forEach(tab => {
        tab.addEventListener("click", function(e) {
            e.preventDefault();
            const url = this.dataset.url;
            if (!url) return;

            // تغییر کلاس اکتیو
            tabs.forEach(t => {
                t.classList.remove("bg-blue-50", "text-blue-700", "font-bold");
                t.classList.add("text-gray-700");
            });
            this.classList.remove("text-gray-700");
            this.classList.add("bg-blue-50", "text-blue-700", "font-bold");

            loadContent(url);
        });
    });

    // لود کردن تب پیش‌فرض
    const defaultTab = document.querySelector('.tab-link[data-target="orders"]');
    if (defaultTab) {
        defaultTab.click();
    }
});
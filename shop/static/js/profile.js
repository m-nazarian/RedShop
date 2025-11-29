document.addEventListener("DOMContentLoaded", function() {

    const contentContainer = document.getElementById("profile-dynamic-content");
    const tabs = document.querySelectorAll(".tab-link");

    // تابع برای لود کردن محتوا
    function loadContent(url) {
        // 1. نمایش لودینگ (با استایل Tailwind)
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
                // 3. قرار دادن HTML در صفحه

                contentContainer.innerHTML = html;

                // اگر اسکریپت خاصی داخل HTML لود شده بود (مثل دکمه‌های آدرس)، اینجا می‌تونیم صدا بزنیم
            })
            .catch(error => {
                console.error("Error loading content:", error);
                contentContainer.innerHTML = `
                    <div class="text-center py-10 text-red-500">
                        <p>متأسفانه مشکلی در بارگذاری پیش آمد.</p>
                        <button onclick="location.reload()" class="mt-4 text-blue-600 underline">تلاش مجدد</button>
                    </div>
                `;
            });
    }

    // هندل کردن کلیک روی تب‌ها
    tabs.forEach(tab => {
        tab.addEventListener("click", function(e) {
            e.preventDefault(); // جلوگیری از رفرش صفحه

            const url = this.dataset.url;
            if (!url) return;

            // تغییر کلاس اکتیو (ظاهر دکمه)
            tabs.forEach(t => {
                t.classList.remove("bg-blue-50", "text-blue-700", "font-bold");
                t.classList.add("text-gray-700");
            });

            this.classList.remove("text-gray-700");
            this.classList.add("bg-blue-50", "text-blue-700", "font-bold");

            // لود محتوا
            loadContent(url);
        });
    });

    // لود کردن تب پیش‌فرض (اولین تب یا تب سفارش‌ها)
    const defaultTab = document.querySelector('.tab-link[data-target="orders"]');
    if (defaultTab) {
        defaultTab.click();
    }
});
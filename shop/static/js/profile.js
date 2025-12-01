// ==========================================
// 1. توابع جهانی (Global Functions)
// قابل دسترسی برای دکمه‌های HTML (onclick)
// ==========================================

// متغیر جهانی برای ذخیره آدرس فعلی (جهت جستجو)
window.currentProfileUrl = "";

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

// تابع فعال‌سازی اسکریپت‌های محتوای جدید (مثل سرچ باکس)
function attachDynamicEvents() {
    const searchInput = document.getElementById("order-search-input");

    if (searchInput) {
        // نگه داشتن فوکوس و موقعیت نشانگر تایپ
        const val = searchInput.value;
        searchInput.focus();
        searchInput.setSelectionRange(val.length, val.length);

        // شنود تایپ کاربر
        searchInput.addEventListener("input", debounce(function(e) {
            const query = e.target.value.trim();
            // ساخت آدرس جدید با پارامتر جستجو
            let searchUrl = `${window.currentProfileUrl}?q=${encodeURIComponent(query)}`;
            // فراخوانی مجدد لود محتوا
            window.loadProfileContent(searchUrl);
        }, 1000));
    }
}

// ✅ تابع اصلی لود محتوا با AJAX (اصلاح شده و جهانی)
window.loadProfileContent = function(url) {
    const contentContainer = document.getElementById("profile-dynamic-content");
    if (!contentContainer) return;

    // ذخیره آدرس پایه (بدون پارامترهای کوئری مثل ؟q=...)
    window.currentProfileUrl = url.split('?')[0];

    // 1. نمایش لودینگ
    contentContainer.innerHTML = `
        <div class="flex flex-col items-center justify-center py-20 text-gray-500">
            <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-4"></div>
            <p>در حال بارگذاری...</p>
        </div>
    `;

    // 2. درخواست به سرور
    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (!response.ok) throw new Error("Network response was not ok");
        return response.text();
    })
    .then(html => {
        contentContainer.innerHTML = html;
        // فعال‌سازی مجدد رویدادها (برای محتوای جدید)
        attachDynamicEvents();
    })
    .catch(error => {
        console.error("Error:", error);
        contentContainer.innerHTML = `
            <div class="text-center py-10 text-red-500">
                <p>خطا در بارگذاری محتوا.</p>
                <button onclick="loadProfileContent('${url}')" class="mt-4 text-blue-600 underline">تلاش مجدد</button>
            </div>
        `;
    });
};

// ✅ تابع حذف کارت علاقه‌مندی (جهانی)
window.removeFavCard = function(pid) {
    const card = document.getElementById(`fav-item-${pid}`);
    if (card) {
        // انیمیشن حذف نرم
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.9)';

        // حذف کامل بعد از پایان انیمیشن
        setTimeout(() => {
            card.remove();

            // چک کنیم اگر لیست خالی شد، پیام "خالی" نشان دهیم (اختیاری ولی حرفه‌ای)
            const grid = document.querySelector('.grid-cols-1'); // گرید محصولات
            if (grid && grid.children.length === 0) {
                grid.parentElement.innerHTML = `
                    <div class="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p class="text-gray-500">لیست علاقه‌مندی‌های شما خالی است.</p>
                    </div>
                `;
            }
        }, 300);
    }
};

// ==========================================
// 2. آماده‌سازی صفحه (Initialization)
// ==========================================

document.addEventListener("DOMContentLoaded", function() {
    const tabs = document.querySelectorAll(".tab-link");

    tabs.forEach(tab => {
        tab.addEventListener("click", function(e) {
            e.preventDefault();
            const url = this.dataset.url;

            if (!url) return;

            // تغییر کلاس اکتیو دکمه‌ها
            tabs.forEach(t => {
                t.classList.remove("bg-blue-50", "text-blue-700", "font-bold");
                t.classList.add("text-gray-700");
            });

            this.classList.remove("text-gray-700");
            this.classList.add("bg-blue-50", "text-blue-700", "font-bold");

            // فراخوانی تابع جهانی
            window.loadProfileContent(url);
        });
    });

    // لود کردن تب پیش‌فرض (سفارش‌ها) در ابتدای کار
    const defaultTab = document.querySelector('.tab-link[data-target="orders"]');
    if (defaultTab) {
        defaultTab.click();
    }
});
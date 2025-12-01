//=========================================
//--------------toggleFavorite-------------
//=========================================
function toggleFavorite(productId, btnElement) {
    const url = `/favorite/toggle/${productId}/`;
    
    // پیدا کردن آیکون قلب داخل دکمه
    const svg = btnElement.querySelector('svg');

    // انیمیشن کلیک
    btnElement.style.transform = "scale(0.8)";
    setTimeout(() => btnElement.style.transform = "scale(1)", 200);

    fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(res => {
        if (res.status === 401) {
            if (typeof showToast === "function") {
                showToast('برای افزودن به علاقه‌مندی‌ها لطفاً وارد شوید.', 'error');
            } else {
                alert('لطفاً وارد شوید.');
            }
            return null;
        }
        if (!res.ok) throw new Error("Network Error");
        return res.json();
    })
    .then(data => {
        if (data && data.success) {
            if (data.status === 'added') {
                // قرمز و توپر ❤️
                svg.classList.remove('text-gray-400', 'hover:text-red-400');
                svg.classList.add('text-red-500', 'fill-red-500');
                if (typeof showToast === "function") showToast('به لیست علاقه‌مندی‌ها اضافه شد.', 'success');
            } else {
                // خالی 🤍
                svg.classList.remove('text-red-500', 'fill-red-500');
                svg.classList.add('text-gray-400', 'hover:text-red-400');
                if (typeof showToast === "function") showToast('از لیست حذف شد.', 'error'); // یا info
            }
        }
    })
    .catch(err => console.error("Favorite Error:", err));
}

//=========================================
//----------------getCookie----------------
//=========================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

//=========================================
//-------تابع ساخت و نمایش نوتیفیکیشن------
//=========================================
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    let icon = type === 'success' ? '✔' : '✖';

    const toast = document.createElement('div');
    toast.classList.add('toast-message', type);

    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${icon}</span>
            <span>${message}</span>
        </div>
        <span class="toast-close" onclick="this.parentElement.remove()">&times;</span>
    `;

    container.appendChild(toast);
    setTimeout(() => { toast.classList.add('show'); }, 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => { toast.remove(); }, 400);
    }, 4000);
}

// =========================================
// سیستم مقایسه (Compare) ⚖️
// =========================================

// افزودن به مقایسه (در لیست محصولات استفاده می‌شود)
function addToCompare(productId) {
    const url = `/compare/add/${productId}/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(err => console.error(err));
}

// حذف از مقایسه (در صفحه مقایسه استفاده می‌شود)
function removeFromCompare(productId) {
    const url = `/compare/remove/${productId}/`;
    const container = document.getElementById('compare-container');

    // حالت لودینگ
    container.style.opacity = '0.5';

    fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(res => res.json()) // اول مطمئن میشیم حذف شده
    .then(data => {
        if (data.success) {
            // درخواست میدیم جدول جدید رو بگیریم (Reload Table)
            return fetch('/compare/', {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
        }
    })
    .then(res => res ? res.text() : null)
    .then(html => {
        if (html) {
            container.innerHTML = html;
            container.style.opacity = '1';
            showToast('محصول از مقایسه حذف شد.', 'success');
        }
    })
    .catch(err => {
        console.error(err);
        container.style.opacity = '1';
    });
}


// 1. باز کردن مودال پیشنهاد مقایسه
function openCompareModal() {
    if (typeof window.openModal === "function") {
        window.openModal('/compare/suggestions/');
    } else {
        console.error("Modal function not found. Please move modal JS to main.js");
    }
}

// 2. افزودن محصول از داخل مودال
function addFromModal(productId) {
    const url = `/compare/add/${productId}/`;

    // بستن مودال
    if (typeof window.closeModal === "function") window.closeModal();

    // حالت لودینگ روی جدول
    const container = document.getElementById('compare-container');
    if(container) container.style.opacity = '0.5';

    fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // رفرش جدول
            return fetch('/compare/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        } else {
            showToast(data.message, 'error');
            if(container) container.style.opacity = '1';
        }
    })
    .then(res => res ? res.text() : null)
    .then(html => {
        if (html && container) {
            container.innerHTML = html;
            container.style.opacity = '1';
            showToast('محصول به مقایسه اضافه شد.', 'success');
        }
    })
    .catch(err => console.error(err));
}


// ==========================================
// مدیریت مودال (Modal Management)
// ==========================================
window.closeModal = function() {
    const modal = document.getElementById('general-modal');
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalPanel = document.getElementById('modal-panel');

    if (!modal) return;

    if (modalPanel) {
        modalPanel.classList.add('opacity-0', 'scale-95');
        modalPanel.classList.remove('opacity-100', 'scale-100');
    }
    if (modalBackdrop) {
        modalBackdrop.classList.add('opacity-0');
        modalBackdrop.classList.remove('opacity-100');
    }

    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
};

window.openModal = function(url) {
    const modal = document.getElementById('general-modal');
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalPanel = document.getElementById('modal-panel');
    const modalContent = document.getElementById('modal-content');

    if (!modal) {
        console.error("Modal element (#general-modal) not found in HTML!");
        return;
    }

    // ریست محتوا
    if (modalContent) {
        modalContent.innerHTML = `
            <div class="flex justify-center py-10">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        `;
    }

    modal.classList.remove('hidden');

    setTimeout(() => {
        if (modalBackdrop) {
            modalBackdrop.classList.remove('opacity-0');
            modalBackdrop.classList.add('opacity-100');
        }
        if (modalPanel) {
            modalPanel.classList.remove('opacity-0', 'scale-95');
            modalPanel.classList.add('opacity-100', 'scale-100');
        }
    }, 10);

    console.log("Fetching URL:", url); // برای دیباگ

    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => {
        // چک کردن نوع محتوا برای جلوگیری از ارور JSON
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return res.json();
        } else {
            throw new Error("Server returned HTML instead of JSON. Check your View!");
        }
    })
    .then(data => {
        if (data.html_form) {
            if (modalContent) {
                modalContent.innerHTML = data.html_form;
                // اجرای اسکریپت‌ها
                const scripts = modalContent.querySelectorAll("script");
                scripts.forEach(script => {
                    const newScript = document.createElement("script");
                    newScript.textContent = script.textContent;
                    document.body.appendChild(newScript);
                });
            }
        }
    })
    .catch(err => {
        console.error(err);
        if (modalContent) modalContent.innerHTML = '<p class="text-red-500 text-center py-4">خطا در بارگذاری.</p>';
    });
};
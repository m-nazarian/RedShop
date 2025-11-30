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

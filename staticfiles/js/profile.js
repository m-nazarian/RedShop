
document.addEventListener('DOMContentLoaded', function() {
    const profileNavItems = document.querySelectorAll('.profile-nav li');

    profileNavItems.forEach(item => {
        item.addEventListener('click', function() {
            profileNavItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            updateContent(this.querySelector('a').textContent.trim());
        });
    });

    // مدیریت جستجو
    const searchBox = document.querySelector('.search-box input');
    const searchBtn = document.querySelector('.search-btn');

    searchBtn.addEventListener('click', performSearch);
    searchBox.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    const orderButtons = document.querySelectorAll('.order-actions .btn');

    orderButtons.forEach(button => {
        button.addEventListener('click', function() {
            const orderCard = this.closest('.order-card');
            const orderId = orderCard.querySelector('.order-id').textContent;
            const buttonText = this.textContent.trim();

            handleOrderAction(orderId, buttonText);
        });
    });

    const editProfileBtn = document.querySelector('.edit-profile-btn');
    editProfileBtn.addEventListener('click', function() {
        openEditProfileModal();
    });

    const userData = {
        name: 'کاربر مهمان',
        phone: '۰۹۱۲××××۱۲۳۴',
        email: 'user@example.com',
        joinDate: '۱۴۰۲/۰۱/۱۵'
    };

    loadUserData();
});

function performSearch() {
    const searchTerm = document.querySelector('.search-box input').value.trim();
    if (searchTerm) {
        console.log('جستجو برای:', searchTerm);
        simulateSearch(searchTerm);
    }
}

function simulateSearch(term) {
    const orderCards = document.querySelectorAll('.order-card');
    let found = false;

    orderCards.forEach(card => {
        const orderText = card.textContent.toLowerCase();
        if (orderText.includes(term.toLowerCase())) {
            card.style.display = 'block';
            card.style.animation = 'highlight 1.5s ease-in-out';
            found = true;
        } else {
            card.style.display = 'none';
        }
    });

    if (!found) {
        showNoResultsMessage(term);
    }
}

function showNoResultsMessage(term) {
    const ordersList = document.querySelector('.orders-list');
    const existingMessage = document.querySelector('.no-results-message');

    if (existingMessage) {
        existingMessage.remove();
    }

    const message = document.createElement('div');
    message.className = 'no-results-message';
    message.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #666;">
            <h3>نتیجه‌ای یافت نشد</h3>
            <p>هیچ سفارشی با عبارت "${term}" پیدا نشد.</p>
            <button class="btn btn-primary" onclick="clearSearch()">نمایش همه سفارش‌ها</button>
        </div>
    `;

    ordersList.appendChild(message);
}

function clearSearch() {
    document.querySelector('.search-box input').value = '';
    const orderCards = document.querySelectorAll('.order-card');
    orderCards.forEach(card => {
        card.style.display = 'block';
        card.style.animation = '';
    });

    const message = document.querySelector('.no-results-message');
    if (message) {
        message.remove();
    }
}

function handleOrderAction(orderId, action) {
    console.log(`اقدام ${action} برای سفارش ${orderId}`);

    switch(action) {
        case 'مشاهده جزئیات':
            showOrderDetails(orderId);
            break;
        case 'خرید مجدد':
            reorderProducts(orderId);
            break;
        case 'پیگیری سفارش':
            trackOrder(orderId);
            break;
        case 'لغو سفارش':
            cancelOrder(orderId);
            break;
    }
}

function showOrderDetails(orderId) {
    alert(`جزئیات سفارش ${orderId} در اینجا نمایش داده می‌شود.`);

}


function reorderProducts(orderId) {
    if (confirm('آیا می‌خواهید این محصولات را مجدداً خریداری کنید؟')) {
        console.log(`محصولات سفارش ${orderId} به سبد خرید اضافه شد.`);
        showToast('محصولات به سبد خرید اضافه شدند');
    }
}

function trackOrder(orderId) {
    window.open(`/tracking/${orderId}`, '_blank');
}

function cancelOrder(orderId) {
    if (confirm('آیا از لغو این سفارش مطمئن هستید؟')) {
        console.log(`سفارش ${orderId} لغو شد.`);
        showToast('سفارش با موفقیت لغو شد');

        updateOrderStatus(orderId, 'لغو شده');
    }
}

function updateOrderStatus(orderId, newStatus) {
    const orderCard = document.querySelector(`.order-card:has(.order-id:contains("${orderId}"))`);
    if (orderCard) {
        const statusElement = orderCard.querySelector('.order-status');
        statusElement.textContent = newStatus;
        statusElement.className = 'order-status cancelled';
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 1rem 2rem;
        border-radius: 5px;
        z-index: 1000;
        animation: slideDown 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function loadUserData() {
    const userInfoElements = {
        name: document.querySelector('.profile-info h3'),
        phone: document.querySelector('.profile-info p'),
        username: document.querySelector('.username')
    };

    if (userInfoElements.name) userInfoElements.name.textContent = 'کاربر مهمان';
    if (userInfoElements.phone) userInfoElements.phone.textContent = '۰۹۱۲××××۱۲۳۴';
    if (userInfoElements.username) userInfoElements.username.textContent = 'کاربر مهمان';
}


function updateContent(selectedItem) {
    const contentHeader = document.querySelector('.content-header h2');
    if (contentHeader) {
        contentHeader.textContent = selectedItem;
    }

    console.log(`بارگذاری محتوای: ${selectedItem}`);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes highlight {
        0% { background-color: transparent; }
        50% { background-color: #fff3cd; }
        100% { background-color: transparent; }
    }
    
    @keyframes slideDown {
        from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
    }
    
    .order-status.cancelled {
        background: #f8d7da;
        color: #721c24;
    }
    
    .toast {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
`;
document.head.appendChild(style);
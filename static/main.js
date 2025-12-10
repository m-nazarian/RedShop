document.addEventListener("DOMContentLoaded", function() {

    // ===========================================
    // 1. 🔍 مدیریت جستجوی هوشمند (Live Search)
    // ===========================================
    const searchInput = document.getElementById("main-search-input");
    const resultsBox = document.getElementById("search-results-box");
    let debounceTimer;

    if (searchInput && resultsBox) {
        const formatMoney = (price) => toPersianNum(price.toLocaleString()) + ' تومان';

        searchInput.addEventListener("input", function() {
            const query = this.value.trim();
            clearTimeout(debounceTimer);

            if (query.length < 2) {
                resultsBox.style.display = "none";
                resultsBox.innerHTML = "";
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                    .then(res => {
                        if (!res.ok) throw new Error("Network response was not ok");
                        return res.json();
                    })
                    .then(data => {
                        renderResults(data, query);
                    })
                    .catch(err => console.error("Search Error:", err));
            }, 300);
        });

        function renderResults(data, query) {
            resultsBox.innerHTML = "";

            if (data.products.length === 0 && !data.suggested_category) {
                resultsBox.style.display = "none";
                return;
            }

            let htmlContent = "";

            if (data.suggested_category) {
                htmlContent += `
                    <a href="${data.suggested_category.url}" class="block px-4 py-3 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors text-sm border-b border-gray-100">
                        🔍 جستجو برای «<strong>${query}</strong>» در دسته‌ی 
                        <strong>${data.suggested_category.name}</strong>
                    </a>
                `;
            }

            data.products.forEach(p => {
                htmlContent += `
                    <a href="${p.url}" class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0">
                        <img src="${p.image}" alt="${p.name}" class="w-10 h-10 object-cover rounded-lg border border-gray-200">
                        <div class="flex-1 min-w-0">
                            <span class="block text-sm font-bold text-gray-800 truncate">${p.name}</span>
                            <div class="flex items-center gap-2 text-xs text-gray-500 mt-1">
                                <span class="bg-gray-100 px-1.5 py-0.5 rounded">${p.category_name}</span>
                                <span>|</span>
                                <span class="text-blue-600 font-medium">${formatMoney(p.price)}</span>
                            </div>
                        </div>
                    </a>
                `;
            });

            resultsBox.innerHTML = htmlContent;
            resultsBox.style.display = "block";
        }

        document.addEventListener("click", function(e) {
            if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
                resultsBox.style.display = "none";
            }
        });
    }

    // ===========================================
    // 2. 🧬 مدیریت منوها (Menu Logic)
    // ===========================================
    const menuTimers = {};
    const triggers = document.querySelectorAll('.hover-trigger');

    function closeMenuImmediately(content) {
        content.classList.add('hidden');
        content.classList.remove('opacity-100', 'translate-y-0');
        content.classList.add('opacity-0', 'translate-y-2');
    }

    if (triggers.length > 0) {
        triggers.forEach(trigger => {
            const targetId = trigger.dataset.target;
            const content = document.getElementById(targetId);

            if (!content) return;

            const showMenu = () => {
                if (menuTimers[targetId]) {
                    clearTimeout(menuTimers[targetId]);
                    delete menuTimers[targetId];
                }
                triggers.forEach(otherTrigger => {
                    const otherId = otherTrigger.dataset.target;
                    if (otherId !== targetId) {
                        const otherContent = document.getElementById(otherId);
                        if (otherContent && !otherContent.classList.contains('hidden')) {
                            if (menuTimers[otherId]) clearTimeout(menuTimers[otherId]);
                            closeMenuImmediately(otherContent);
                        }
                    }
                });
                content.classList.remove('hidden');
                void content.offsetWidth;
                content.classList.remove('opacity-0', 'translate-y-2');
                content.classList.add('opacity-100', 'translate-y-0');
            };

            const hideMenu = () => {
                menuTimers[targetId] = setTimeout(() => {
                    content.classList.remove('opacity-100', 'translate-y-0');
                    content.classList.add('opacity-0', 'translate-y-2');
                    setTimeout(() => {
                        if (content.classList.contains('opacity-0')) {
                            content.classList.add('hidden');
                        }
                    }, 300);
                }, 200);
            };

            trigger.addEventListener('mouseenter', showMenu);
            trigger.addEventListener('mouseleave', hideMenu);
            content.addEventListener('mouseenter', showMenu);
            content.addEventListener('mouseleave', hideMenu);
        });
    }

    // مدیریت تب‌های مگا منو
    const categoryItems = document.querySelectorAll('.category-item');
    const contents = document.querySelectorAll('.subcategory-content');
    const defaultContent = document.getElementById('cat-default');
    let catTimeout;

    if (categoryItems.length > 0) {
        categoryItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                const id = this.dataset.id;
                const targetContent = document.getElementById(`cat-content-${id}`);

                if (catTimeout) clearTimeout(catTimeout);

                categoryItems.forEach(i => {
                    const link = i.querySelector('a');
                    if (link) link.classList.remove('bg-white', 'text-blue-600', 'border-blue-600', 'shadow-sm');
                });

                const currentLink = this.querySelector('a');
                if (currentLink) currentLink.classList.add('bg-white', 'text-blue-600', 'border-blue-600', 'shadow-sm');

                contents.forEach(c => c.classList.add('hidden'));
                if (defaultContent) defaultContent.classList.add('hidden');

                if (targetContent) {
                    targetContent.classList.remove('hidden');
                    targetContent.classList.remove('animate-fade-in-fast');
                    void targetContent.offsetWidth;
                    targetContent.classList.add('animate-fade-in-fast');
                }
            });
        });

        const megaMenu = document.getElementById('mega-menu');
        if (megaMenu) {
            megaMenu.addEventListener('mouseleave', () => {
                categoryItems.forEach(i => {
                    const link = i.querySelector('a');
                    if (link) link.classList.remove('bg-white', 'text-blue-600', 'border-blue-600', 'shadow-sm');
                });
                contents.forEach(c => c.classList.add('hidden'));
                if (defaultContent) defaultContent.classList.remove('hidden');
            });
        }
    }


    // ===========================================
    // 3. 🚀 اسکرول نرم هدر
    // ===========================================
    let lastScrollTop = 0;
    const bottomNav = document.getElementById('bottom-nav');
    const topNav = document.getElementById('top-nav');

    if (bottomNav && topNav) {
        window.addEventListener("scroll", function() {
            let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            if (scrollTop < 0) return;
            if (scrollTop < 50) {
                bottomNav.classList.remove('nav-slide-up');
                bottomNav.classList.add('shadow-md');
                topNav.classList.remove('shadow-md');
                lastScrollTop = scrollTop;
                return;
            }
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                if (!bottomNav.classList.contains('nav-slide-up')) {
                    bottomNav.classList.add('nav-slide-up');
                    bottomNav.classList.remove('shadow-md');
                    topNav.classList.add('shadow-md');
                }
            } else if (scrollTop < lastScrollTop) {
                if (bottomNav.classList.contains('nav-slide-up')) {
                    bottomNav.classList.remove('nav-slide-up');
                    topNav.classList.remove('shadow-md');
                    bottomNav.classList.add('shadow-md');
                }
            }
            lastScrollTop = scrollTop;
        }, { passive: true });
    }

    // =========================================
    // 4. اسلایدرها (Drag Scroll)
    // =========================================
    const sliders = document.querySelectorAll('.product-slider');
    sliders.forEach(slider => {
        let isDown = false;
        let startX;
        let scrollLeft;
        let velX = 0;
        let momentumID;
        const isHero = slider.id === 'hero-slider';

        slider.addEventListener('dragstart', (e) => e.preventDefault());
        slider.addEventListener('mousedown', (e) => {
            isDown = true; slider.classList.add('active'); startX = e.pageX - slider.offsetLeft; scrollLeft = slider.scrollLeft; cancelAnimationFrame(momentumID);
        });
        slider.addEventListener('mouseleave', () => {
            if (isDown) { isDown = false; slider.classList.remove('active'); if (isHero) snapToSlide(); else beginMomentum(); }
        });
        slider.addEventListener('mouseup', () => {
            isDown = false; slider.classList.remove('active'); if (isHero) snapToSlide(); else beginMomentum();
        });
        slider.addEventListener('mousemove', (e) => {
            if (!isDown) return; e.preventDefault(); const x = e.pageX - slider.offsetLeft; const walk = (x - startX); velX = walk; slider.scrollLeft = scrollLeft - walk;
        });

        function snapToSlide() {
            const slideWidth = slider.offsetWidth;
            const currentScroll = slider.scrollLeft;
            const targetIndex = Math.round(currentScroll / slideWidth);
            slider.scrollTo({ left: targetIndex * slideWidth, behavior: 'smooth' });
        }
        function beginMomentum() {
            cancelAnimationFrame(momentumID);
            function loop() { if (Math.abs(velX) < 0.1) return; slider.scrollLeft -= velX; velX *= 0.95; momentumID = requestAnimationFrame(loop); }
            loop();
        }

        const wrapper = slider.closest('section') || slider.parentElement;
        if(wrapper) {
            const nextBtn = wrapper.querySelector('.slider-next');
            const prevBtn = wrapper.querySelector('.slider-prev');
            const scrollAmount = isHero ? slider.offsetWidth : 300;
            if(nextBtn) nextBtn.addEventListener('click', () => { cancelAnimationFrame(momentumID); slider.scrollBy({ left: -scrollAmount, behavior: 'smooth' }); });
            if(prevBtn) prevBtn.addEventListener('click', () => { cancelAnimationFrame(momentumID); slider.scrollBy({ left: scrollAmount, behavior: 'smooth' }); });
        }
    });

});


// =========================================================
// 🚨 بخش دوم: توابع جهانی (Global Functions)
// =========================================================

// لایک و دیس‌لایک
window.reactToComment = function(commentId, actionType) {
    const likeBtn = document.getElementById(`like-btn-${commentId}`);
    const dislikeBtn = document.getElementById(`dislike-btn-${commentId}`);
    const likeCountSpan = document.getElementById(`like-count-${commentId}`);
    const dislikeCountSpan = document.getElementById(`dislike-count-${commentId}`);
    const url = `/comment/react/${commentId}/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `type=${actionType}`
    })
    .then(res => {
        if (res.status === 401) {
            if (typeof showToast === "function") showToast('برای ثبت نظر لطفاً وارد شوید.', 'error');
            return null;
        }
        return res.json();
    })
    .then(data => {
        if (data && data.success) {
            if (likeCountSpan) likeCountSpan.innerText = toPersianNum(data.likes_count);
            if (dislikeCountSpan) dislikeCountSpan.innerText = toPersianNum(data.dislikes_count);

            likeBtn.className = "flex items-center gap-1 px-2 py-1 rounded transition-colors duration-200 hover:text-green-600";
            dislikeBtn.className = "flex items-center gap-1 px-2 py-1 rounded transition-colors duration-200 hover:text-red-500";

            if (data.action === 'created' || data.action === 'changed') {
                if (actionType === 'like') {
                    likeBtn.classList.remove('hover:text-green-600');
                    likeBtn.classList.add('text-green-600', 'bg-green-50', 'font-bold');
                } else {
                    dislikeBtn.classList.remove('hover:text-red-500');
                    dislikeBtn.classList.add('text-red-500', 'bg-red-50', 'font-bold');
                }
            }
        }
    })
    .catch(console.error);
};

window.toggleFavorite = function(productId, btnElement) {
    const url = `/favorite/toggle/${productId}/`;
    const svg = btnElement.querySelector('svg');

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
            if (typeof showToast === "function") showToast('لطفاً وارد شوید.', 'error');
            return null;
        }
        return res.json();
    })
    .then(data => {
        if (data && data.success) {
            if (data.status === 'added') {
                svg.classList.remove('text-gray-400', 'hover:text-red-400');
                svg.classList.add('text-red-500', 'fill-red-500');
                if (typeof showToast === "function") showToast('به علاقه‌مندی‌ها اضافه شد.', 'success');
            } else {
                svg.classList.remove('text-red-500', 'fill-red-500');
                svg.classList.add('text-gray-400', 'hover:text-red-400');
                if (typeof showToast === "function") showToast('از علاقه‌مندی‌ها حذف شد.', 'error');
            }
        }
    })
    .catch(console.error);
};

// سیستم مقایسه (جهانی شده)
window.addToCompare = function(productId) {
    const url = `/compare/add/${productId}/`;
    fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (typeof showToast === "function") showToast(data.message, 'success');
        } else {
            if (typeof showToast === "function") showToast(data.message, 'error');
        }
    })
    .catch(console.error);
};

window.removeFromCompare = function(productId) {
    const url = `/compare/remove/${productId}/`;
    const container = document.getElementById('compare-container');
    if(container) container.style.opacity = '0.5';

    fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) return fetch('/compare/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    })
    .then(res => res ? res.text() : null)
    .then(html => {
        if (html && container) {
            container.innerHTML = html;
            container.style.opacity = '1';
            if (typeof showToast === "function") showToast('محصول حذف شد.', 'success');
        }
    })
    .catch(err => { console.error(err); if(container) container.style.opacity = '1'; });
};

window.openCompareModal = function() {
    if (typeof window.openModal === "function") {
        window.openModal('/compare/suggestions/');
    }
};

window.addFromModal = function(productId) {
    const url = `/compare/add/${productId}/`;
    if (typeof window.closeModal === "function") window.closeModal();
    const container = document.getElementById('compare-container');
    if(container) container.style.opacity = '0.5';

    fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            return fetch('/compare/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        } else {
            if (typeof showToast === "function") showToast(data.message, 'error');
            if(container) container.style.opacity = '1';
        }
    })
    .then(res => res ? res.text() : null)
    .then(html => {
        if (html && container) {
            container.innerHTML = html;
            container.style.opacity = '1';
            if (typeof showToast === "function") showToast('محصول اضافه شد.', 'success');
        }
    })
    .catch(console.error);
};

// حذف کارت علاقه‌مندی
window.removeFavCard = function(pid) {
    const card = document.getElementById(`fav-item-${pid}`);
    if (card) {
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.9)';
        setTimeout(() => {
            card.remove();
            const grid = document.querySelector('.grid-cols-1');
            if (grid && grid.children.length === 0) {
                grid.parentElement.innerHTML = '<div class="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300"><p class="text-gray-500">لیست علاقه‌مندی‌های شما خالی است.</p></div>';
            }
        }, 300);
    }
};

// توابع کمکی
window.getCookie = function(name) {
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
};

window.showToast = function(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    let icon = type === 'success' ? '✔' : '✖';
    const toast = document.createElement('div');
    toast.classList.add('toast-message', type);
    toast.innerHTML = `<div class="toast-content"><span class="toast-icon">${icon}</span><span>${message}</span></div>`;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 400); }, 4000);
};

window.toPersianNum = function(num) {
    if (num === undefined || num === null) return "";
    return num.toString().replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);
};

// مودال جهانی
window.closeModal = function() {
    const modal = document.getElementById('general-modal');
    if (!modal) return;
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalPanel = document.getElementById('modal-panel');
    if (modalPanel) { modalPanel.classList.add('opacity-0', 'scale-95'); modalPanel.classList.remove('opacity-100', 'scale-100'); }
    if (modalBackdrop) { modalBackdrop.classList.add('opacity-0'); modalBackdrop.classList.remove('opacity-100'); }
    setTimeout(() => { modal.classList.add('hidden'); }, 300);
};

window.openModal = function(url) {
    const modal = document.getElementById('general-modal');
    if (!modal) return;
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalPanel = document.getElementById('modal-panel');
    const modalContent = document.getElementById('modal-content');
    if (modalContent) modalContent.innerHTML = `<div class="flex justify-center py-10"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>`;
    modal.classList.remove('hidden');
    setTimeout(() => {
        if (modalBackdrop) { modalBackdrop.classList.remove('opacity-0'); modalBackdrop.classList.add('opacity-100'); }
        if (modalPanel) { modalPanel.classList.remove('opacity-0', 'scale-95'); modalPanel.classList.add('opacity-100', 'scale-100'); }
    }, 10);
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(res => res.json())
    .then(data => {
        if (data.html_form && modalContent) {
            modalContent.innerHTML = data.html_form;
            modalContent.querySelectorAll("script").forEach(script => {
                const newScript = document.createElement("script");
                newScript.textContent = script.textContent;
                document.body.appendChild(newScript);
            });
        }
    })
    .catch(err => { console.error(err); if (modalContent) modalContent.innerHTML = '<p class="text-red-500 text-center py-4">خطا در بارگذاری.</p>'; });
};
document.addEventListener("DOMContentLoaded", function() {

    // ===========================================
    // 1. جستجو (بدون تغییر)
    // ===========================================
    const searchInput = document.getElementById("main-search-input");
    const resultsBox = document.getElementById("search-results-box");
    let debounceTimer;

    if (searchInput && resultsBox) {
        const toPersianNum = (num) => num.toString().replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);
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
                fetch(`/api/search/?q=${encodeURIComponent(query)}`).then(res => { if (!res.ok) throw new Error("Network response was not ok"); return res.json(); }).then(data => { renderResults(data, query); }).catch(err => console.error("Search Error:", err));
            }, 300);
        });

        
function renderResults(data, query) {
            while (resultsBox.firstChild) {
                resultsBox.removeChild(resultsBox.firstChild);
            }

            const products = Array.isArray(data.products) ? data.products : [];
            const suggestedCategory = data.suggested_category || null;

            if (products.length === 0 && !suggestedCategory) {
                resultsBox.style.display = "none";
                return;
            }

            const safeSameOriginUrl = (value) => {
                if (!value) return "#";

                try {
                    const url = new URL(String(value), window.location.origin);

                    if (url.origin !== window.location.origin) {
                        return "#";
                    }

                    return `${url.pathname}${url.search}${url.hash}`;
                } catch (_error) {
                    return "#";
                }
            };

            const appendStrongText = (parent, value) => {
                const strong = document.createElement("strong");
                strong.textContent = String(value ?? "");
                parent.appendChild(strong);
                return strong;
            };

            if (suggestedCategory) {
                const categoryLink = document.createElement("a");
                categoryLink.href = safeSameOriginUrl(suggestedCategory.url);
                categoryLink.className = "block px-4 py-3 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors text-sm border-b border-gray-100";

                categoryLink.appendChild(document.createTextNode("🔍 جستجو برای «"));
                appendStrongText(categoryLink, query);
                categoryLink.appendChild(document.createTextNode("» در دسته‌ی "));
                appendStrongText(categoryLink, suggestedCategory.name);

                resultsBox.appendChild(categoryLink);
            }

            products.forEach((product) => {
                const item = document.createElement("a");
                item.href = safeSameOriginUrl(product.url);
                item.className = "flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0";

                const image = document.createElement("img");
                image.src = safeSameOriginUrl(product.image);
                image.alt = String(product.name ?? "");
                image.className = "w-10 h-10 object-cover rounded-lg border border-gray-200";
                item.appendChild(image);

                const body = document.createElement("div");
                body.className = "flex-1 min-w-0";

                const title = document.createElement("span");
                title.className = "block text-sm font-bold text-gray-800 truncate";
                title.textContent = String(product.name ?? "");
                body.appendChild(title);

                const meta = document.createElement("div");
                meta.className = "flex items-center gap-2 text-xs text-gray-500 mt-1";

                const category = document.createElement("span");
                category.className = "bg-gray-100 px-1.5 py-0.5 rounded";
                category.textContent = String(product.category_name ?? "");

                const separator = document.createElement("span");
                separator.textContent = "|";

                const price = document.createElement("span");
                price.className = "text-blue-600 font-medium";

                const numericPrice = Number(product.price);
                price.textContent = Number.isFinite(numericPrice) ? formatMoney(numericPrice) : "";

                meta.appendChild(category);
                meta.appendChild(separator);
                meta.appendChild(price);

                body.appendChild(meta);
                item.appendChild(body);
                resultsBox.appendChild(item);
            });

            resultsBox.style.display = "block";
        }
        document.addEventListener("click", function(e) { if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) { resultsBox.style.display = "none"; } });
    }

    // ===========================================
    // 2. مدیریت منوها (بدون تغییر)
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
                if (menuTimers[targetId]) { clearTimeout(menuTimers[targetId]); delete menuTimers[targetId]; }
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
                    setTimeout(() => { if (content.classList.contains('opacity-0')) { content.classList.add('hidden'); } }, 300);
                }, 200);
            };

            trigger.addEventListener('mouseenter', showMenu);
            trigger.addEventListener('mouseleave', hideMenu);
            content.addEventListener('mouseenter', showMenu);
            content.addEventListener('mouseleave', hideMenu);
        });
    }

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
                categoryItems.forEach(i => { const link = i.querySelector('a'); if(link) link.classList.remove('bg-white', 'text-blue-600', 'border-blue-600', 'shadow-sm'); });
                const currentLink = this.querySelector('a');
                if(currentLink) currentLink.classList.add('bg-white', 'text-blue-600', 'border-blue-600', 'shadow-sm');
                contents.forEach(c => c.classList.add('hidden'));
                if(defaultContent) defaultContent.classList.add('hidden');
                if (targetContent) {
                    targetContent.classList.remove('hidden');
                    targetContent.classList.remove('animate-fade-in-fast');
                    void targetContent.offsetWidth;
                    targetContent.classList.add('animate-fade-in-fast');
                }
            });
        });
        const megaMenu = document.getElementById('mega-menu');
        if(megaMenu){ megaMenu.addEventListener('mouseleave', () => { categoryItems.forEach(i => { const link = i.querySelector('a'); if(link) link.classList.remove('bg-white', 'text-blue-600', 'border-blue-600', 'shadow-sm'); }); contents.forEach(c => c.classList.add('hidden')); if(defaultContent) defaultContent.classList.remove('hidden'); }); }
    }

// ===========================================
    // 3. 🚀 لاجیک اسکرول نرم (Sliding Header + Smart Shadow)
    // ===========================================
    let lastScrollTop = 0;
    const bottomNav = document.getElementById('bottom-nav');
    const topNav = document.getElementById('top-nav'); // گرفتن المنت بالا

    if (bottomNav && topNav) {
        window.addEventListener("scroll", function() {
            let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            if (scrollTop < 0) return;

            // اگر بالای صفحه هستیم (حالت اولیه)
            if (scrollTop < 50) {
                // نوار پایین رو نشون بده
                bottomNav.classList.remove('nav-slide-up');
                // سایه رو به نوار پایین بده (پیش‌فرض HTML)
                bottomNav.classList.add('shadow-md');
                // سایه نوار بالا رو حذف کن (تا یکدست بشن)
                topNav.classList.remove('shadow-md');

                lastScrollTop = scrollTop;
                return;
            }

            // تشخیص جهت اسکرول
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // 👇 اسکرول به پایین (مخفی شدن نوار پایین)
                if (!bottomNav.classList.contains('nav-slide-up')) {
                    bottomNav.classList.add('nav-slide-up');

                    // 💡 نکته کلیدی: حالا که نوار پایین رفت، سایه رو بده به نوار بالا
                    bottomNav.classList.remove('shadow-md'); // حذف سایه مخفی شده
                    topNav.classList.add('shadow-md');       // اضافه کردن سایه به بالا
                }
            } else if (scrollTop < lastScrollTop) {
                // 👆 اسکرول به بالا (نمایش نوار پایین)
                if (bottomNav.classList.contains('nav-slide-up')) {
                    bottomNav.classList.remove('nav-slide-up');

                    // برگرداندن سایه به جای اولش
                    topNav.classList.remove('shadow-md');
                    bottomNav.classList.add('shadow-md');
                }
            }

            lastScrollTop = scrollTop;
        }, { passive: true });
    }
});

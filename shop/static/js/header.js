
document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("menu-overlay");
  const dropdowns = document.querySelectorAll(".nav-categories .dropdown");

  dropdowns.forEach((dropdown) => {
    dropdown.addEventListener("mouseenter", () => {
      overlay.classList.add("active");
    });

    dropdown.addEventListener("mouseleave", () => {
      overlay.classList.remove("active");
    });
  });

  overlay.addEventListener("click", () => {
    overlay.classList.remove("active");
  });
});

document.addEventListener('DOMContentLoaded', function() {
  const dropdowns = document.querySelectorAll('.nav-categories .dropdown');
  const overlay = document.getElementById('menu-overlay');

  dropdowns.forEach(drop => {
    drop.addEventListener('mouseenter', () => {
      overlay.classList.add('active');
    });
    drop.addEventListener('mouseleave', () => {
      overlay.classList.remove('active');
    });
  });
});



//===========================================
//----------------Search Box-----------------
//===========================================
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("main-search-input");
    const resultsBox = document.getElementById("search-results-box");
    let debounceTimer;

    // تابع تبدیل اعداد به فارسی (برای قیمت)
    const toPersianNum = (num) => {
        return num.toString().replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);
    };

    // تابع فرمت پول
    const formatMoney = (price) => {
        return toPersianNum(price.toLocaleString()) + ' تومان';
    };

    searchInput.addEventListener("input", function() {
        const query = this.value.trim();

        clearTimeout(debounceTimer);

        if (query.length < 2) {
            resultsBox.style.display = "none";
            resultsBox.innerHTML = "";
            return;
        }

        // تاخیر ۳۰۰ میلی‌ثانیه برای بهینگی
        debounceTimer = setTimeout(() => {
            fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    renderResults(data, query);
                })
                .catch(err => console.error(err));
        }, 300);
    });

    function renderResults(data, query) {
        resultsBox.innerHTML = "";

        if (data.products.length === 0 && !data.suggested_category) {
            resultsBox.style.display = "none";
            return;
        }

        let htmlContent = "";

        // 1. پیشنهاد دسته‌بندی (مثل دیجی‌کالا)
        if (data.suggested_category) {
            htmlContent += `
                <a href="${data.suggested_category.url}" class="search-suggestion-header">
                    🔍 جستجو برای «<strong>${query}</strong>» در دسته‌ی 
                    <strong>${data.suggested_category.name}</strong>
                </a>
            `;
        }

        // 2. لیست محصولات
        data.products.forEach(p => {
            htmlContent += `
                <a href="${p.url}" class="search-item">
                    <img src="${p.image}" alt="${p.name}">
                    <div class="search-item-info">
                        <span class="search-item-title">${p.name}</span>
                        <span class="search-item-cat">در ${p.category_name} | ${formatMoney(p.price)}</span>
                    </div>
                </a>
            `;
        });

        // 3. مشاهده همه نتایج
        // (این لینک رو باید به صفحه لیست محصولات با پارامتر جستجو وصل کنی)
        // htmlContent += `<a href="/shop/products/?q=${query}" class="search-show-all">مشاهده همه نتایج</a>`;

        resultsBox.innerHTML = htmlContent;
        resultsBox.style.display = "block";
    }

    // بستن باکس وقتی جای دیگر کلیک شد
    document.addEventListener("click", function(e) {
        if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
            resultsBox.style.display = "none";
        }
    });
});
document.addEventListener("DOMContentLoaded", function() {

    // =========================================
    // 1. Collapsible (مشخصات کالا)
    // =========================================
    const collapsibles = document.querySelectorAll(".collapsible-group");


    collapsibles.forEach((btn, index) => {
        // حذف ایونت‌های قبلی برای اطمینان
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener("click", function() {

            // پیدا کردن محتوا
            const content = this.nextElementSibling;

            if (!content) {
                console.error("❌ Error: No content div found immediately after this button.");
                return;
            }

            // تغییر کلاس
            this.classList.toggle("active");

            // تغییر ارتفاع
            if (content.style.maxHeight) {
                content.style.maxHeight = null;
            } else {
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });

    // =========================================
    // 2. سیستم پیشرفته گالری و لایت‌باکس 🛡️
    // =========================================

    // المان‌های HTML
    const lightbox = document.getElementById("lightbox");
    const track = document.getElementById("track");
    const lightboxThumbsContainer = document.getElementById("lightbox-thumbnails");
    const closeBtn = document.querySelector(".close-lightbox");
    const prevBtn = document.querySelector(".prev-btn");
    const nextBtn = document.querySelector(".next-btn");
    const counter = document.querySelector(".lightbox-counter");

    // المان‌های صفحه اصلی
    const mainImgElem = document.getElementById("main-image");
    const pageThumbnails = document.querySelectorAll(".page-thumbnail");

    // --- گارد ایمنی: اگر لایت‌باکس در صفحه نیست، بقیه کد اجرا نشود ---
    if (!lightbox || !track) {
        return;
    }

    // جمع‌آوری لیست تصاویر (منبع حقیقت)
    let gallerySources = [];

    // اگر تامبنیل‌ها در صفحه هستند، از روی آن‌ها لیست را بساز
    if (pageThumbnails.length > 0) {
        pageThumbnails.forEach(img => gallerySources.push(img.src));
    } else if (mainImgElem) {
        gallerySources.push(mainImgElem.src);
    }

    // متغیرهای وضعیت
    let currentIndex = 0;
    let isDragging = false;
    let startPos = 0;
    let currentTranslate = 0;
    let prevTranslate = 0;
    let animationID;
    let startTime = 0;
    let zoomLevel = 1;

    // ---------------------------------------------
    // ساختن محتوای لایت‌باکس (اسلایدها + تامبنیل‌ها)
    // ---------------------------------------------
    function buildLightboxContent() {
        track.innerHTML = "";
        lightboxThumbsContainer.innerHTML = "";

        gallerySources.forEach((src, index) => {
            // الف) ساخت اسلاید بزرگ
            const slideDiv = document.createElement("div");
            slideDiv.classList.add("lightbox-slide");
            const img = document.createElement("img");
            img.src = src;
            img.draggable = false;
            enableZoom(img, slideDiv); // فعال‌سازی زوم
            slideDiv.appendChild(img);
            track.appendChild(slideDiv);

            // ب) ساخت تامبنیل پایین لایت‌باکس
            const thumb = document.createElement("img");
            thumb.src = src;
            thumb.classList.add("lightbox-thumb-img");
            // کلیک روی تامبنیل -> رفتن به آن عکس
            thumb.addEventListener("click", (e) => {
                e.stopPropagation();
                currentIndex = index;
                setPositionByIndex();
            });
            lightboxThumbsContainer.appendChild(thumb);
        });
    }

    // ---------------------------------------------
    // باز و بسته کردن
    // ---------------------------------------------
    function openLightbox(index) {
        currentIndex = index;

        // اگر خالی بود، بساز
        if (track.children.length === 0) buildLightboxContent();

        // حذف انیمیشن برای باز شدن سریع
        track.style.transition = "none";
        currentTranslate = currentIndex * -window.innerWidth;
        prevTranslate = currentTranslate;
        track.style.transform = `translateX(${currentTranslate}px)`;

        lightbox.style.display = "flex";
        requestAnimationFrame(() => lightbox.classList.add("show"));

        updateUI(); // آپدیت کلاس‌های اکتیو
    }

    function closeLightbox() {
        lightbox.classList.remove("show");
        setTimeout(() => {
            lightbox.style.display = "none";
            resetAllZooms();
        }, 300);
    }

    // ---------------------------------------------
    // منطق آپدیت UI (سینک کردن تامبنیل‌ها با اسلایدر)
    // ---------------------------------------------
    function updateUI() {
        // 1. آپدیت شمارنده
        if(counter) counter.innerText = `${currentIndex + 1} / ${gallerySources.length}`;

        // 2. آپدیت تامبنیل‌های داخل لایت‌باکس
        const allLightboxThumbs = document.querySelectorAll(".lightbox-thumb-img");
        allLightboxThumbs.forEach((t, i) => {
            if (i === currentIndex) {
                t.classList.add("active-lightbox-thumb");
                t.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
            } else {
                t.classList.remove("active-lightbox-thumb");
            }
        });

        // 3. آپدیت تامبنیل‌های صفحه اصلی
        pageThumbnails.forEach((t, i) => {
            if (i === currentIndex) {
                t.classList.add("active-thumb");
                if(mainImgElem) mainImgElem.src = t.src;
            } else {
                t.classList.remove("active-thumb");
            }
        });
    }

    // ---------------------------------------------
    // منطق حرکت اسلایدر (Swipe & Navigation)
    // ---------------------------------------------
    function setPositionByIndex() {
        track.style.transition = "transform 0.3s ease-out";
        currentTranslate = currentIndex * -window.innerWidth;
        prevTranslate = currentTranslate;
        track.style.transform = `translateX(${currentTranslate}px)`;

        resetAllZooms();
        updateUI();
    }

    function getPositionX(event) { return event.type.includes('mouse') ? event.pageX : event.touches[0].clientX; }

    function touchStart(index) {
        return function(event) {
            if (zoomLevel > 1) return;
            isDragging = true;
            startTime = new Date().getTime();
            startPos = getPositionX(event);
            track.style.transition = "none";
            animationID = requestAnimationFrame(animation);
            track.style.cursor = "grabbing";
        }
    }

    function touchMove(event) {
        if (isDragging) {
            const currentPosition = getPositionX(event);
            currentTranslate = prevTranslate + currentPosition - startPos;
        }
    }

    function touchEnd() {
        isDragging = false;
        cancelAnimationFrame(animationID);
        track.style.cursor = "grab";
        if (zoomLevel > 1) return;

        const movedBy = currentTranslate - prevTranslate;
        const timeTaken = new Date().getTime() - startTime;

        if (movedBy < -100 || (movedBy < -50 && timeTaken < 300)) {
            if (currentIndex < gallerySources.length - 1) currentIndex++;
        } else if (movedBy > 100 || (movedBy > 50 && timeTaken < 300)) {
            if (currentIndex > 0) currentIndex--;
        }

        setPositionByIndex();
    }

    function animation() {
        if(isDragging) {
            track.style.transform = `translateX(${currentTranslate}px)`;
            requestAnimationFrame(animation);
        }
    }

    // ---------------------------------------------
    // رویدادها (Listeners)
    // ---------------------------------------------

    if(mainImgElem) {
        mainImgElem.addEventListener("click", () => openLightbox(currentIndex));
    }

    pageThumbnails.forEach((thumb, index) => {
        thumb.addEventListener("click", () => {
            currentIndex = index;
            updateUI();
        });
    });

    track.addEventListener('mousedown', touchStart(currentIndex));
    track.addEventListener('touchstart', touchStart(currentIndex), {passive: true});
    track.addEventListener('mouseup', touchEnd);
    track.addEventListener('mouseleave', () => { if(isDragging) touchEnd() });
    track.addEventListener('touchend', touchEnd);
    track.addEventListener('mousemove', touchMove);
    track.addEventListener('touchmove', touchMove, {passive: true});

    if (nextBtn) nextBtn.addEventListener('click', (e) => { e.stopPropagation(); if(currentIndex < gallerySources.length - 1) { currentIndex++; setPositionByIndex(); } });
    if (prevBtn) prevBtn.addEventListener('click', (e) => { e.stopPropagation(); if(currentIndex > 0) { currentIndex--; setPositionByIndex(); } });
    if (closeBtn) closeBtn.addEventListener('click', closeLightbox);

    document.addEventListener("keydown", e => {
        if (lightbox.style.display === "flex") {
            if (e.key === "ArrowRight") { if(currentIndex < gallerySources.length - 1) { currentIndex++; setPositionByIndex(); } }
            if (e.key === "ArrowLeft") { if(currentIndex > 0) { currentIndex--; setPositionByIndex(); } }
            if (e.key === "Escape") closeLightbox();
        }
    });

    window.addEventListener('resize', () => {
        if (lightbox.style.display === "flex") {
            track.style.transition = "none";
            currentTranslate = currentIndex * -window.innerWidth;
            prevTranslate = currentTranslate;
            track.style.transform = `translateX(${currentTranslate}px)`;
        }
    });

    // ---------------------------------------------
    // زوم
    // ---------------------------------------------
    function enableZoom(imgElement, container) {
        let scale = 1;
        let panning = false;
        let pointX = 0, pointY = 0, startX = 0, startY = 0;

        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const xs = (e.clientX - pointX) / scale;
            const ys = (e.clientY - pointY) / scale;
            const delta = -e.deltaY;
            (delta > 0) ? (scale *= 1.1) : (scale /= 1.1);
            scale = Math.min(Math.max(1, scale), 4);
            if(scale === 1) { pointX = 0; pointY = 0; zoomLevel = 1; } else { zoomLevel = scale; }
            imgElement.style.transform = `translate(${pointX}px, ${pointY}px) scale(${scale})`;
        });

        container.addEventListener('mousedown', (e) => {
            if (scale > 1) {
                e.preventDefault();
                panning = true;
                startX = e.clientX - pointX;
                startY = e.clientY - pointY;
                imgElement.style.cursor = "grabbing";
            }
        });

        container.addEventListener('mousemove', (e) => {
            if (!panning) return;
            e.preventDefault();
            pointX = e.clientX - startX;
            pointY = e.clientY - startY;
            imgElement.style.transform = `translate(${pointX}px, ${pointY}px) scale(${scale})`;
        });

        container.addEventListener('mouseup', () => { panning = false; imgElement.style.cursor = "default"; });
    }

    function resetAllZooms() {
        track.querySelectorAll("img").forEach(img => img.style.transform = "translate(0px, 0px) scale(1)");
        zoomLevel = 1;
    }

    // تنظیم اولیه
    updateUI();
});


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

//=========================================
//---------مدیریت ارسال نظر با AJAX--------
//=========================================
// مدیریت ارسال نظر با AJAX
document.addEventListener("DOMContentLoaded", function() {
    const commentForm = document.getElementById('comment-form');

    // استفاده از یک متغیر برای جلوگیری از اجرای چندباره ایونت
    if (commentForm && !commentForm.dataset.listenerAttached) {

        // علامت می‌زنیم که لیسنر به این فرم وصل شد
        commentForm.dataset.listenerAttached = "true";

        commentForm.addEventListener('submit', function(e) {
            // 1. مهمترین خط: جلوگیری از ارسال عادی فرم توسط مرورگر
            e.preventDefault();
            e.stopImmediatePropagation(); // اطمینان از اینکه لیسنرهای تکراری احتمالی اجرا نشن

            const form = this;

            // 2. بررسی اینکه آیا فرم در حال ارسال است؟
            if (form.dataset.submitting === "true") {
                console.warn("Form is already submitting...");
                return;
            }

            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn.innerText;

            // 3. قفل کردن فرم
            form.dataset.submitting = "true"; // علامت "در حال ارسال"
            btn.disabled = true;
            btn.innerText = 'در حال ثبت...';

            const formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    form.reset(); // پاک کردن فرم
                    // ریست کردن ستاره‌ها (چون رادیو باتن هستن و با reset ممکنه بصری درست نشن)
                    const lastStar = form.querySelector('input[name="score"][value="5"]');
                    if(lastStar) lastStar.checked = true;
                } else {
                    showToast('لطفا ورودی‌ها را بررسی کنید.', 'error');
                    console.log(data.errors);
                }
            })
            .catch(err => {
                console.error(err);
                showToast('خطایی رخ داد.', 'error');
            })
            .finally(() => {
                // 4. آزاد کردن فرم (چه موفق چه ناموفق)
                delete form.dataset.submitting;
                btn.disabled = false;
                btn.innerText = originalText;
            });
        });
    }
});

// ===========================================
// -------سیستم لایک و دیس‌لایک نظرات 👍👎------
// ===========================================

function reactToComment(commentId, actionType) {
    // پیدا کردن مستقیم عناصر با ID منحصر به فرد
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
            showToast('برای ثبت نظر لطفاً وارد شوید.', 'error');
            return null;
        }
        return res.json();
    })
    .then(data => {
        if (data && data.success) {
            // 1. آپدیت اعداد (لایو)
            if (likeCountSpan) likeCountSpan.innerText = toPersianNum(data.likes_count);
            if (dislikeCountSpan) dislikeCountSpan.innerText = toPersianNum(data.dislikes_count);

            // 2. مدیریت کلاس‌های رنگی (UI Update)

            // اول همه رنگ‌ها رو پاک می‌کنیم (حالت خنثی)
            likeBtn.className = "flex items-center gap-1 px-2 py-1 rounded transition-colors duration-200 hover:text-green-600";
            dislikeBtn.className = "flex items-center gap-1 px-2 py-1 rounded transition-colors duration-200 hover:text-red-500";

            // حالا بر اساس وضعیت جدید رنگ می‌پاشیم
            if (data.action === 'created' || data.action === 'changed') {
                if (actionType === 'like') {
                    // لایک شده: سبز و بولد
                    likeBtn.classList.remove('hover:text-green-600');
                    likeBtn.classList.add('text-green-600', 'bg-green-50', 'font-bold');
                } else {
                    // دیس‌لایک شده: قرمز و بولد
                    dislikeBtn.classList.remove('hover:text-red-500');
                    dislikeBtn.classList.add('text-red-500', 'bg-red-50', 'font-bold');
                }
            }
            // اگر action === 'removed' بود، همون حالت خنثی که بالا ست کردیم باقی می‌مونه
        }
    })
    .catch(err => console.error("Reaction Error:", err));
}

// توابع کمکی (اگر قبلا نداری)
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

function toPersianNum(num) {
    return num.toString().replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);
}
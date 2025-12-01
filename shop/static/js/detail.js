document.addEventListener("DOMContentLoaded", function() {

// =========================================
    // 1. افزودن به سبد خرید (AJAX) 🛒
    // =========================================
    const addToCartBtn = document.getElementById('add_cart');

    // شرط جلوگیری از لیسنر تکراری
    if (addToCartBtn && !addToCartBtn.dataset.listenerAttached) {

        addToCartBtn.dataset.listenerAttached = "true";

        addToCartBtn.addEventListener('click', function() {
            const button = this;
            const originalText = button.innerText;

            if (button.disabled) return;

            button.disabled = true;
            button.innerText = 'در حال پردازش...';

            const url = button.dataset.url;

            if(!url) {
                console.error("URL not found!");
                button.disabled = false;
                button.innerText = originalText;
                return;
            }

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(res => res.json())
            .then(data => {
                if(data.item_count !== undefined) {
                    // 1. آپدیت بج قرمز هدر
                    const countBadge = document.getElementById('header-cart-count');
                    if(countBadge) {
                        countBadge.innerText = toPersianNum(data.item_count);
                        if(data.item_count > 0) countBadge.classList.remove('hidden');
                    }

                    // 2. آپدیت محتوای مینی‌کارت (لیست هاور)
                    const miniCartContainer = document.getElementById('mini-cart-container');
                    if (miniCartContainer && data.html_cart) {
                        miniCartContainer.innerHTML = data.html_cart;
                    }

                    // 3. آپدیت سایر المان‌های صفحه
                    const itemCountElem = document.getElementById('item_count');
                    const totalPriceElem = document.getElementById('total_price');
                    if(itemCountElem) itemCountElem.innerText = toPersianNum(data.item_count);
                    if(totalPriceElem) totalPriceElem.innerText = toPersianNum(data.total_price);

                    // 4. ✅ نمایش پیام موفقیت
                    if (typeof showToast === "function") {
                        showToast('محصول با موفقیت به سبد خرید اضافه شد', 'success');
                    }
                } else if (data.error) {
                    if (typeof showToast === "function") showToast(data.error, 'error');
                }
            })
            .catch(err => {
                console.error(err);
                if (typeof showToast === "function") showToast('خطایی رخ داد.', 'error');
            })
            .finally(() => {
                button.disabled = false;
                button.innerText = originalText;
            });
        });
    }


    // =========================================
    // 2. Collapsible (مشخصات کالا)
    // =========================================
    const collapsibles = document.querySelectorAll(".collapsible-group");

    collapsibles.forEach((btn, index) => {
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener("click", function() {
            const content = this.nextElementSibling;
            if (!content) return;
            this.classList.toggle("active");
            if (content.style.maxHeight) {
                content.style.maxHeight = null;
            } else {
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });


    // =========================================
    // 3. سیستم لایت‌باکس و گالری 🛡️
    // =========================================
    const lightbox = document.getElementById("lightbox");
    const track = document.getElementById("track");
    const lightboxThumbsContainer = document.getElementById("lightbox-thumbnails");
    const closeBtn = document.querySelector(".close-lightbox");
    const prevBtn = document.querySelector(".prev-btn");
    const nextBtn = document.querySelector(".next-btn");
    const counter = document.querySelector(".lightbox-counter");
    const mainImgElem = document.getElementById("main-image");
    const pageThumbnails = document.querySelectorAll(".page-thumbnail");

    if (lightbox && track) {
        let gallerySources = [];
        if (pageThumbnails.length > 0) {
            pageThumbnails.forEach(img => gallerySources.push(img.src));
        } else if (mainImgElem) {
            gallerySources.push(mainImgElem.src);
        }

        let currentIndex = 0;
        let isDragging = false;
        let startPos = 0;
        let currentTranslate = 0;
        let prevTranslate = 0;
        let animationID;
        let startTime = 0;
        let zoomLevel = 1;

        function buildLightboxContent() {
            track.innerHTML = "";
            lightboxThumbsContainer.innerHTML = "";
            gallerySources.forEach((src, index) => {
                const slideDiv = document.createElement("div");
                slideDiv.classList.add("lightbox-slide");
                const img = document.createElement("img");
                img.src = src;
                img.draggable = false;
                enableZoom(img, slideDiv);
                slideDiv.appendChild(img);
                track.appendChild(slideDiv);

                const thumb = document.createElement("img");
                thumb.src = src;
                thumb.classList.add("lightbox-thumb-img");
                thumb.addEventListener("click", (e) => {
                    e.stopPropagation();
                    currentIndex = index;
                    setPositionByIndex();
                });
                lightboxThumbsContainer.appendChild(thumb);
            });
        }

        function openLightbox(index) {
            currentIndex = index;
            if (track.children.length === 0) buildLightboxContent();
            track.style.transition = "none";
            currentTranslate = currentIndex * -window.innerWidth;
            prevTranslate = currentTranslate;
            track.style.transform = `translateX(${currentTranslate}px)`;
            lightbox.style.display = "flex";
            requestAnimationFrame(() => lightbox.classList.add("show"));
            updateUI();
        }

        function closeLightbox() {
            lightbox.classList.remove("show");
            setTimeout(() => {
                lightbox.style.display = "none";
                resetAllZooms();
            }, 300);
        }

        function updateUI() {
            if(counter) counter.innerText = `${currentIndex + 1} / ${gallerySources.length}`;
            const allLightboxThumbs = document.querySelectorAll(".lightbox-thumb-img");
            allLightboxThumbs.forEach((t, i) => {
                if (i === currentIndex) {
                    t.classList.add("active-lightbox-thumb");
                    t.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
                } else {
                    t.classList.remove("active-lightbox-thumb");
                }
            });
            pageThumbnails.forEach((t, i) => {
                if (i === currentIndex) {
                    t.classList.add("active-thumb");
                    if(mainImgElem) mainImgElem.src = t.src;
                } else {
                    t.classList.remove("active-thumb");
                }
            });
        }

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

        // Listeners
        if(mainImgElem) mainImgElem.addEventListener("click", () => openLightbox(currentIndex));
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
        updateUI();
    }


    // =========================================
    // 4. ثبت نظر با AJAX
    // =========================================
    const commentForm = document.getElementById('comment-form');
    if (commentForm && !commentForm.dataset.listenerAttached) {
        commentForm.dataset.listenerAttached = "true";
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            const form = this;
            if (form.dataset.submitting === "true") return;

            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn.innerText;
            form.dataset.submitting = "true";
            btn.disabled = true;
            btn.innerText = 'در حال ثبت...';

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (typeof showToast === "function") showToast(data.message, 'success');
                    form.reset();
                    const lastStar = form.querySelector('input[name="score"][value="5"]');
                    if(lastStar) lastStar.checked = true;
                } else {
                    if (typeof showToast === "function") showToast('لطفا ورودی‌ها را بررسی کنید.', 'error');
                }
            })
            .catch(err => {
                console.error(err);
                if (typeof showToast === "function") showToast('خطایی رخ داد.', 'error');
            })
            .finally(() => {
                delete form.dataset.submitting;
                btn.disabled = false;
                btn.innerText = originalText;
            });
        });
    }
});


// =========================================
// 5. لایک و دیس‌لایک کامنت (جهانی)
// =========================================
function reactToComment(commentId, actionType) {
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
    .catch(err => console.error(err));
}

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


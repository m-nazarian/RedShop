document.addEventListener("DOMContentLoaded", function() {

    // =========================================
    // 1. افزودن به سبد خرید (AJAX) 🛒
    // =========================================
    const addToCartBtn = document.getElementById('add_cart');

    if (addToCartBtn && !addToCartBtn.dataset.listenerAttached) {
        addToCartBtn.dataset.listenerAttached = "true";

        addToCartBtn.addEventListener('click', function() {
            const button = this;
            const originalContent = button.innerHTML;

            if (button.disabled) return;
            button.disabled = true;
            button.innerHTML = '<span class="animate-spin h-5 w-5 border-2 border-white rounded-full border-t-transparent"></span> در حال پردازش...';

            const url = button.dataset.url;

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
                    const countBadge = document.getElementById('header-cart-count');
                    if(countBadge) {
                        countBadge.innerText = toPersianNum(data.item_count);
                        if(data.item_count > 0) countBadge.classList.remove('hidden');
                    }
                    const miniCartContainer = document.getElementById('mini-cart-container');
                    if (miniCartContainer && data.html_cart) {
                        miniCartContainer.innerHTML = data.html_cart;
                    }
                    if (typeof showToast === "function") showToast('محصول با موفقیت به سبد خرید اضافه شد', 'success');
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
                button.innerHTML = originalContent;
            });
        });
    }

    // =========================================
    // 2. سیستم لایت‌باکس و گالری (نسخه اصلاح شده RTL) 🖼️
    // =========================================
    const lightbox = document.getElementById("lightbox");
    const track = document.getElementById("track");
    const lightboxThumbsContainer = document.getElementById("lightbox-thumbnails");
    const mainImgElem = document.getElementById("main-image");
    const pageThumbnails = document.querySelectorAll(".page-thumbnail");
    const closeBtn = document.querySelector(".close-lightbox");
    const prevBtn = document.querySelector(".prev-btn"); // دکمه سمت چپ
    const nextBtn = document.querySelector(".next-btn"); // دکمه سمت راست
    const counter = document.querySelector(".lightbox-counter");

    if (lightbox && track) {
        let gallerySources = [];
        if (pageThumbnails.length > 0) {
            pageThumbnails.forEach(div => {
                const img = div.querySelector('img');
                if(img) gallerySources.push(img.src);
            });
        } else if (mainImgElem) {
            gallerySources.push(mainImgElem.src);
        }

        let currentIndex = 0;
        let isDragging = false;
        let startPos = 0;
        let currentTranslate = 0;
        let prevTranslate = 0;
        let animationID;

        function openLightbox(index) {
            currentIndex = index;
            buildLightbox();
            updateLightboxPosition();
            lightbox.classList.remove("hidden");
            lightbox.classList.add("flex");
            document.body.style.overflow = 'hidden';
            window.addEventListener('keydown', handleKeyboardNav);
        }

        function closeLightbox() {
            lightbox.classList.add("hidden");
            lightbox.classList.remove("flex");
            document.body.style.overflow = '';
            window.removeEventListener('keydown', handleKeyboardNav);
        }

        function buildLightbox() {
            if (track.children.length > 0) return;

            track.innerHTML = "";
            lightboxThumbsContainer.innerHTML = "";

            const innerTrack = document.createElement('div');
            innerTrack.className = 'flex h-full transition-transform duration-300 ease-out';
            innerTrack.style.width = `${gallerySources.length * 100}%`;
            innerTrack.style.direction = 'ltr';
            track.appendChild(innerTrack);

            gallerySources.forEach((src, idx) => {
                const slide = document.createElement("div");
                slide.className = "w-full h-full flex items-center justify-center flex-shrink-0 p-4";
                const img = document.createElement("img");
                img.src = src;
                img.className = "max-w-full max-h-full object-contain pointer-events-none select-none";
                slide.appendChild(img);
                innerTrack.appendChild(slide);

                const thumb = document.createElement("img");
                thumb.src = src;
                thumb.className = `w-16 h-16 object-cover rounded-lg border-2 border-transparent cursor-pointer opacity-60 hover:opacity-100 transition-all flex-shrink-0 ${idx === currentIndex ? 'border-blue-500 opacity-100' : ''}`;
                thumb.onclick = () => { currentIndex = idx; updateLightboxPosition(); };
                lightboxThumbsContainer.appendChild(thumb);
            });

            track.addEventListener('mousedown', touchStart);
            track.addEventListener('mouseup', touchEnd);
            track.addEventListener('mouseleave', touchEnd);
            track.addEventListener('mousemove', touchMove);

            track.addEventListener('touchstart', touchStart);
            track.addEventListener('touchend', touchEnd);
            track.addEventListener('touchmove', touchMove);
        }

        function updateLightboxPosition() {
            const innerTrack = track.firstElementChild;
            if (!innerTrack) return;
            currentTranslate = currentIndex * -track.offsetWidth;
            prevTranslate = currentTranslate;
            setSliderPosition();

            if(counter) counter.innerText = `${toPersianNum(currentIndex + 1)} / ${toPersianNum(gallerySources.length)}`;

            Array.from(lightboxThumbsContainer.children).forEach((thumb, idx) => {
                if (idx === currentIndex) {
                    thumb.classList.add('border-blue-500', 'opacity-100');
                    thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                } else {
                    thumb.classList.remove('border-blue-500', 'opacity-100');
                }
            });
        }

        function touchStart(event) {
            isDragging = true;
            startPos = getPositionX(event);
            track.firstElementChild.style.transition = 'none';
            animationID = requestAnimationFrame(animation);
            track.style.cursor = 'grabbing';
        }

        function touchMove(event) {
            if (!isDragging) return;
            const currentPosition = getPositionX(event);
            const diff = currentPosition - startPos;
            currentTranslate = prevTranslate + diff;
        }

        function touchEnd() {
            isDragging = false;
            cancelAnimationFrame(animationID);
            track.firstElementChild.style.transition = 'transform 0.3s ease-out';
            track.style.cursor = 'grab';

            const movedBy = currentTranslate - prevTranslate;

            if (movedBy < -100 && currentIndex < gallerySources.length - 1) {
                currentIndex += 1; // بعدی
            } else if (movedBy > 100 && currentIndex > 0) {
                currentIndex -= 1; // قبلی
            }

            updateLightboxPosition();
        }

        function getPositionX(event) {
            return event.type.includes('mouse') ? event.pageX : event.touches[0].clientX;
        }

        function animation() {
            setSliderPosition();
            if (isDragging) requestAnimationFrame(animation);
        }

        function setSliderPosition() {
            if (track.firstElementChild) {
                track.firstElementChild.style.transform = `translateX(${currentTranslate}px)`;
            }
        }

        // --- نویگیشن با کیبورد ---
        function handleKeyboardNav(e) {
            if (e.key === 'Escape') closeLightbox();
            // فلش راست -> عکس بعدی
            if (e.key === 'ArrowRight') {
                if(currentIndex < gallerySources.length - 1) { currentIndex++; updateLightboxPosition(); }
            }
            // فلش چپ -> عکس قبلی
            if (e.key === 'ArrowLeft') {
                if(currentIndex > 0) { currentIndex--; updateLightboxPosition(); }
            }
        }

        // --- اتصال رویدادها ---
        if(mainImgElem) {
            mainImgElem.parentElement.addEventListener("click", () => openLightbox(0));
        }

        pageThumbnails.forEach((div, idx) => {
            div.addEventListener("click", () => {
                const img = div.querySelector('img');
                if(mainImgElem && img) mainImgElem.src = img.src;
                document.querySelectorAll('.page-thumbnail').forEach(t => t.classList.remove('active-thumb', 'border-blue-500'));
                div.classList.add('active-thumb', 'border-blue-500');
            });
        });

        if(closeBtn) closeBtn.addEventListener("click", closeLightbox);
        lightbox.addEventListener("click", (e) => {
            if (e.target === lightbox || e.target === track) closeLightbox();
        });

        // ✅ اصلاح دکمه‌ها (برعکس شدن منطق قبلی):

        // دکمه سمت راست (nextBtn) -> باید برود بعدی
        if(nextBtn) nextBtn.addEventListener("click", () => {
            if(currentIndex < gallerySources.length - 1) {
                currentIndex++;
                updateLightboxPosition();
            }
        });

        // دکمه سمت چپ (prevBtn) -> باید برود قبلی
        if(prevBtn) prevBtn.addEventListener("click", () => {
            if(currentIndex > 0) {
                currentIndex--;
                updateLightboxPosition();
            }
        });

        window.addEventListener('resize', () => {
            if (!lightbox.classList.contains('hidden')) {
                updateLightboxPosition();
            }
        });
    }

    // =========================================
    // 3. ثبت نظر (AJAX) - (بدون تغییر)
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
            .catch(console.error)
            .finally(() => {
                delete form.dataset.submitting;
                btn.disabled = false;
                btn.innerText = originalText;
            });
        });
    }
});
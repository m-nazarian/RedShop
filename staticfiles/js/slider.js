
const slidesContainer = document.querySelector('.slides');
const slides = document.querySelectorAll('.slides img');
const prevBtn = document.querySelector('.prev');
const nextBtn = document.querySelector('.next');
const dotsContainer = document.querySelector('.dots');

let currentIndex = 0;
let interval;
let startX = 0;
let isDragging = false;

slides.forEach((_, i) => {
    const dot = document.createElement('span');
    dot.addEventListener('click', () => goToSlide(i));
    dotsContainer.appendChild(dot);
});
const dots = dotsContainer.querySelectorAll('span');

function showSlide(index) {
    slidesContainer.style.transform = `translateX(${index * 100}%)`;
    dots.forEach(dot => dot.classList.remove('active'));
    dots[index].classList.add('active');
    currentIndex = index;
}

function nextSlide() {
    showSlide((currentIndex + 1) % slides.length);
}
function prevSlide() {
    showSlide((currentIndex - 1 + slides.length) % slides.length);
}
function goToSlide(index) {
    showSlide(index);
}

function startAutoSlide() {
    interval = setInterval(nextSlide, 5000);
}
function stopAutoSlide() {
    clearInterval(interval);
}

nextBtn.addEventListener('click', () => { nextSlide(); stopAutoSlide(); startAutoSlide(); });
prevBtn.addEventListener('click', () => { prevSlide(); stopAutoSlide(); startAutoSlide(); });

showSlide(currentIndex);
startAutoSlide();

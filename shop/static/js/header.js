
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
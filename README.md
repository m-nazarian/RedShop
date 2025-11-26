# RedShop 🛒

---

## English Version 🇺🇸

**RedShop** — An online store with Django back-end and a simple front-end (HTML/CSS/JS).  
**Purpose:** A lightweight e-commerce project for learning, practice, or personal use. It includes product management, shopping cart, user registration, and orders.

### 🚀 Features

- User management: register, login, profile  
- Product management: add, edit, delete products  
- Shopping cart: add/remove items and place orders  
- Order management  
- Modular structure: each functionality in a separate Django app (users, cart, shop, orders, etc.)  
- Static files support: Tailwind / CSS / JS  
- Easy to extend: add more features such as admin panel, online payment, etc.

### 📁 Project Structure

RedShop/
├── manage.py
├── .gitignore
├── shop/ # Shop app
├── account/ # Users app
├── cart/ # Cart app
├── orders/ # Orders app
├── static/ # Static files (CSS, JS, images)
└── ... # Other apps / folders

bash
Copy code

### 💻 Prerequisites

- Python 3.x  
- Django  
- pip  
- (Optional) Virtual environment recommended  

### 🛠 Installation & Run

```bash
git clone https://github.com/m-nazarian/RedShop.git
cd RedShop

# Optional: create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Optional: create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
Visit http://127.0.0.1:8000/ to see the store.

📈 Current Status
Back-end: ~80% complete

Front-end: under development

Some features like online payment and full admin panel are not implemented yet

🤝 Contributing
Fork the repository

Work in a separate branch (e.g., feature-xyz)

Commit changes and submit a pull request

Suggested features to add:

Improved frontend UI

Online payment integration

REST API / mobile-friendly support

Unit and automated tests

📄 License
MIT License — free to use, modify, and distribute.

نسخه فارسی 🇮🇷
RedShop — یک فروشگاه آنلاین با بک‌اند نوشته‌شده با Django و فرانت‌آند ساده (HTML/CSS/JS).
هدف: پروژه‌ای سبک برای یادگیری و تمرین یا استفاده شخصی که شامل مدیریت محصولات، سبد خرید، ثبت نام کاربران و سفارشات است.

🚀 ویژگی‌ها
مدیریت کاربران: ثبت‌نام، ورود، پروفایل

مدیریت محصولات: افزودن، ویرایش، حذف محصولات

سبد خرید: اضافه/حذف محصول و ثبت سفارش

مدیریت سفارشات

ساختار ماژولار: هر بخش در یک اپلیکیشن جداگانه Django (کاربران، سبد خرید، فروشگاه، سفارشات و غیره)

پشتیبانی از فایل‌های ایستا: Tailwind / CSS / JS

امکان توسعه راحت: افزودن قابلیت‌هایی مانند پنل ادمین، پرداخت آنلاین و غیره

📁 ساختار پروژه
csharp
Copy code
RedShop/
├── manage.py
├── .gitignore
├── shop/          # اپ فروشگاه
├── account/       # اپ کاربران
├── cart/          # اپ سبد خرید
├── orders/        # اپ سفارشات
├── static/        # فایل‌های ایستا (CSS، JS، تصاویر)
└── ...            # سایر اپ‌ها یا پوشه‌ها
💻 پیش‌نیازها
Python 3.x

Django

pip

(اختیاری) استفاده از محیط مجازی پیشنهاد می‌شود

🛠 نصب و اجرا
bash
Copy code
git clone https://github.com/m-nazarian/RedShop.git
cd RedShop

# (اختیاری) ساخت و فعال‌سازی محیط مجازی
python -m venv .venv
# ویندوز:
.venv\Scripts\activate
# لینوکس/macOS:
source .venv/bin/activate

# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای مایگریشن‌ها
python manage.py migrate

# (اختیاری) ساخت superuser
python manage.py createsuperuser

# اجرای سرور
python manage.py runserver
به آدرس http://127.0.0.1:8000/ برو تا فروشگاه را ببینی.

📈 وضعیت فعلی پروژه
بک‌اند تقریباً کامل (~ 80٪)

فرانت‌اند در حال توسعه

قابلیت‌هایی مانند پرداخت آنلاین و پنل ادمین کامل هنوز آماده نیستند

🤝 مشارکت در توسعه
پروژه را fork کن

در یک branch جدا کار کن (مثلاً feature-xyz)

تغییرات را commit و pull request بده

قابلیت‌های پیشنهادی برای توسعه:

طراحی بهتر Frontend

افزودن پرداخت آنلاین

ایجاد REST API و بهینه‌سازی برای موبایل

تست‌های واحد و خودکار

📄 مجوز
MIT License — اجازه استفاده، تغییر و توزیع آزاد را می‌دهد.
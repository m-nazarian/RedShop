from shop.models import Product
from shop.utils.shipping import calculate_post_price


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart


    def add(self, product):
        if product.inventory <= 0:
            return  # محصول موجود نیست، هیچ کاری نکن
        product_id = str(product.id)
        if product_id not in self.cart:

            self.cart[product_id] = {
                'quantity': 1,
                'price': float(product.new_price),
                'weight': float(product.weight)
            }
        else:

            if self.cart[product_id]['quantity'] < product.inventory:
                self.cart[product_id]['quantity'] += 1

        self.save()


    def decrease(self, product):
        product_id = str(product.id)
        if product_id in self.cart and self.cart[product_id]['quantity'] > 1:
            self.cart[product_id]['quantity'] -= 1
            self.save()


    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()


    def clear(self):
        if 'cart' in self.session:
            del self.session['cart']
        self.save()

    def get_post_price(self):
        weight = sum(item['weight'] * item['quantity'] for item in self.cart.values())
        return calculate_post_price(weight)

    def get_post_price_if_any(self):
        return self.get_post_price() if len(self) > 0 else 0


    def get_total_price(self):
        return sum(item['price'] * item['quantity'] for item in self.cart.values())

    def get_final_price(self):
        total = self.get_total_price()
        if len(self) == 0:
            return 0
        return total + self.get_post_price()


    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())



    def __iter__(self):
        # گرفتن شناسه‌ها (به صورت عددی) برای کوئری امن‌تر
        product_ids = [int(pid) for pid in self.cart.keys()]

        # کوئری محصولات موجود در دیتابیس
        products = (
            Product.objects
            .filter(id__in=product_ids)
            .select_related('category','brand')  # برای رابطه ForeignKey
            .prefetch_related('images')  # برای رابطه Reverse ForeignKey یا ManyToMany
        )

        # کپی از inner-dicts تا تغییرات موقتی (مثل افزودن 'product') روی session اعمال نشه
        cart_copy = {pid: item.copy() for pid, item in self.cart.items()}

        updated = False

        # برای هر محصول موجود در دیتابیس، مقادیر کپی را آماده کن و yield کن
        for product in products:
            pid = str(product.id)
            if pid not in cart_copy:
                continue

            # اگر موجودی صفر است → حذف از سبد و ادامه
            if product.inventory <= 0:
                if pid in self.cart:
                    del self.cart[pid]
                    updated = True
                continue

            item = cart_copy[pid]

            new_price = float(product.new_price)
            new_weight = float(product.weight)

            if item.get('price') != new_price or item.get('weight') != new_weight:
                self.cart[pid]['price'] = new_price
                self.cart[pid]['weight'] = new_weight
                item['price'] = new_price
                item['weight'] = new_weight
                updated = True

            item['product'] = product
            item['total'] = item['price'] * item['quantity']
            yield item

        # حذف آیتم‌هایی که دیگر در دیتابیس موجود نیستند
        db_ids = {str(p.id) for p in products}
        removed = [pid for pid in list(self.cart.keys()) if pid not in db_ids]
        if removed:
            for pid in removed:
                del self.cart[pid]
            updated = True

        # فقط در صورت تغییر، session را ذخیره کن
        if updated:
            self.save()

    def save(self):
        self.session.modified = True

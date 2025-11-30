from shop.models import Product
from shop.utils.shipping import calculate_post_price
from coupons.models import Coupon


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')


    def add(self, product):
        if product.inventory <= 0:
            return
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
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
        self.save()


    def get_post_price(self):
        weight = sum(item['weight'] * item['quantity'] for item in self.cart.values())
        return calculate_post_price(weight)


    def get_post_price_if_any(self):
        return self.get_post_price() if len(self) > 0 else 0


    def get_total_price(self):
        return sum(item['price'] * item['quantity'] for item in self.cart.values())


    @property
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None


    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / 100) * self.get_total_price()
        return 0


    def get_final_price(self):
        total = self.get_total_price()
        if len(self) == 0:
            return 0

        post_price = self.get_post_price()
        discount = self.get_discount()

        # قیمت کالاها منهای تخفیف، به علاوه هزینه پست
        return int((total - discount) + post_price)


    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())


    def __iter__(self):
        product_ids = [int(pid) for pid in self.cart.keys()]
        products = (
            Product.objects
            .filter(id__in=product_ids)
            .select_related('category', 'brand')
            .prefetch_related('images')
        )

        cart_copy = {pid: item.copy() for pid, item in self.cart.items()}
        updated = False

        for product in products:
            pid = str(product.id)
            if pid not in cart_copy:
                continue

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

        db_ids = {str(p.id) for p in products}
        removed = [pid for pid in list(self.cart.keys()) if pid not in db_ids]
        if removed:
            for pid in removed:
                del self.cart[pid]
            updated = True

        if updated:
            self.save()


    def save(self):
        self.session.modified = True
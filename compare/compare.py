from shop.models import Product


class Compare:
    def __init__(self, request):
        """
        ایجاد یا شروع کلاس مقایسه
        """
        self.session = request.session
        compare = self.session.get('compare')
        if not compare:
            # یک لیست خالی برای نگهداری ID محصولات
            compare = self.session['compare'] = []
        self.compare = compare

    def add(self, product):
        """
        اضافه کردن محصول به لیست مقایسه
        """
        product_id = str(product.id)

        # اگر محصول قبلاً در لیست نبود، اضافه کن
        if product_id not in self.compare:
            # محدودیت: مثلاً ماکسیمم ۴ محصول برای مقایسه
            if len(self.compare) >= 4:
                return False, "لیست مقایسه پر است (حداکثر ۴ محصول)."

            self.compare.append(product_id)
            self.save()
            return True, "محصول به لیست مقایسه اضافه شد."

        return False, "این محصول قبلاً در لیست وجود دارد."

    def remove(self, product):
        """
        حذف محصول از لیست
        """
        product_id = str(product.id)
        if product_id in self.compare:
            self.compare.remove(product_id)
            self.save()

    def clear(self):
        """
        پاک کردن کل لیست مقایسه
        """
        del self.session['compare']
        self.save()

    def __iter__(self):
        """
        برگرداندن آبجکت محصولات موجود در لیست
        """
        product_ids = self.compare
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            yield product

    def __len__(self):
        return len(self.compare)

    def save(self):
        self.session.modified = True
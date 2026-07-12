from decimal import Decimal, ROUND_DOWN
from functools import partial

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.account.models import Address
from apps.coupons.models import Coupon
from apps.shop.models import Product
from apps.shop.utils.shipping import calculate_post_price

from .emails import send_order_confirmation
from .models import Order, OrderItem


class CheckoutError(Exception):
    """خطاهای قابل نمایش در فرآیند ثبت سفارش."""


class CheckoutService:
    """منطق ثبت سفارش را از ویو جدا و در یک تراکنش اجرا می‌کند."""

    @staticmethod
    def _read_cart_items(cart):
        items = []
        for product_id, data in cart.cart.items():
            try:
                quantity = int(data.get("quantity", 0))
                normalized_id = int(product_id)
            except (TypeError, ValueError):
                raise CheckoutError("اطلاعات سبد خرید معتبر نیست.")

            if quantity < 1:
                raise CheckoutError("تعداد یکی از کالاهای سبد خرید معتبر نیست.")

            items.append((normalized_id, quantity))

        if not items:
            raise CheckoutError("سبد خرید خالی است.")

        return items

    @staticmethod
    def _get_active_coupon(cart):
        if not cart.coupon_id:
            return None

        now = timezone.now()
        return Coupon.objects.filter(
            id=cart.coupon_id,
            active=True,
            valid_from__lte=now,
            valid_to__gte=now,
        ).first()

    @staticmethod
    def _calculate_discount(subtotal, coupon):
        if coupon is None or subtotal <= 0:
            return 0

        discount = (
            Decimal(subtotal)
            * Decimal(coupon.discount)
            / Decimal("100")
        ).quantize(Decimal("1"), rounding=ROUND_DOWN)
        return min(int(discount), subtotal)

    @classmethod
    def place_order(cls, *, user, cart, address_id, payment_method):
        allowed_methods = {value for value, _ in Order.PAYMENT_METHODS}
        if payment_method not in allowed_methods:
            raise CheckoutError("روش پرداخت انتخاب‌شده معتبر نیست.")

        cart_items = cls._read_cart_items(cart)
        product_ids = [product_id for product_id, _ in cart_items]

        with transaction.atomic():
            address = Address.objects.filter(id=address_id, user=user).first()
            if address is None:
                raise CheckoutError("آدرس انتخاب‌شده معتبر نیست.")

            products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            if len(products) != len(set(product_ids)):
                raise CheckoutError("یکی از کالاهای سبد خرید دیگر در دسترس نیست.")

            order = Order.objects.create(
                user=user,
                status="pending",
                first_name=address.first_name,
                last_name=address.last_name,
                phone=address.phone,
                province=address.province,
                city=address.city,
                postal_code=address.postal_code,
                address=address.address_line,
                address_line=address.address_line,
                payment_method=payment_method,
            )

            order_items = []
            subtotal = 0
            total_weight = 0

            for product_id, quantity in cart_items:
                product = products[product_id]
                if product.inventory < quantity:
                    raise CheckoutError(
                        f"موجودی محصول «{product.name}» کافی نیست. "
                        f"موجودی فعلی: {product.inventory}"
                    )

                unit_price = int(product.new_price or product.price)
                unit_weight = int(product.weight or 0)

                subtotal += unit_price * quantity
                total_weight += unit_weight * quantity

                product.inventory -= quantity
                product.save(update_fields=["inventory"])

                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        title=product.name,
                        price=unit_price,
                        quantity=quantity,
                        weight=unit_weight,
                    )
                )

            OrderItem.objects.bulk_create(order_items)

            coupon = cls._get_active_coupon(cart)
            discount_amount = cls._calculate_discount(subtotal, coupon)
            shipping_price = calculate_post_price(total_weight)
            total = max(0, subtotal - discount_amount) + shipping_price

            order.subtotal = subtotal
            order.discount_amount = discount_amount
            order.coupon_code = coupon.code if coupon else ""
            order.shipping_price = shipping_price
            order.post_price = shipping_price
            order.total = total
            order.save(
                update_fields=[
                    "subtotal",
                    "discount_amount",
                    "coupon_code",
                    "shipping_price",
                    "post_price",
                    "total",
                    "updated",
                ]
            )

            if payment_method == "cod":
                transaction.on_commit(
                    partial(send_order_confirmation, order),
                    robust=True,
                )

            return order

class OrderLifecycleService:
    """عملیات حساس چرخه سفارش را اتمیک و قابل تکرار اجرا می‌کند."""

    @staticmethod
    def _append_note(order, note):
        current_notes = (order.notes or "").strip()
        if not current_notes:
            return note
        return f"{current_notes}\n{note}"

    @classmethod
    def cancel_unpaid_order(cls, order_id, *, reason="لغو سفارش پرداخت‌نشده"):
        """سفارش پرداخت‌نشده را لغو می‌کند و موجودی را فقط یک‌بار برمی‌گرداند."""
        with transaction.atomic():
            order = (
                Order.objects.select_for_update()
                .prefetch_related("items")
                .get(id=order_id)
            )

            if order.paid:
                return order, False

            changed = False

            if not order.stock_released:
                items = list(order.items.all())
                product_ids = [item.product_id for item in items]

                locked_products = {
                    product.id: product
                    for product in Product.objects.select_for_update().filter(id__in=product_ids)
                }

                for item in items:
                    if item.product_id in locked_products:
                        Product.objects.filter(id=item.product_id).update(
                            inventory=F("inventory") + item.quantity
                        )

                order.stock_released = True
                changed = True

            if order.status != "canceled":
                order.status = "canceled"
                order.canceled_at = timezone.now()
                changed = True

            if reason and reason not in (order.notes or ""):
                order.notes = cls._append_note(order, reason)
                changed = True

            if changed:
                # این به‌روزرسانی عمداً با QuerySet.update انجام می‌شود.
                # سیگنال‌های قدیمی سفارش هم هنگام تغییر وضعیت لغو، موجودی را برمی‌گردانند.
                # اگر اینجا از save استفاده شود، موجودی دوبار آزاد می‌شود.
                Order.objects.filter(id=order.id).update(
                    status=order.status,
                    stock_released=order.stock_released,
                    canceled_at=order.canceled_at,
                    notes=order.notes,
                    updated=timezone.now(),
                )
                order.refresh_from_db()

            return order, changed

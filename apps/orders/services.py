from dataclasses import dataclass
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
from .models import Order, OrderItem, Transaction


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

        return (
            Coupon.usable_queryset()
            .select_for_update()
            .filter(id=cart.coupon_id)
            .first()
        )

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
            if coupon:
                Coupon.objects.filter(id=coupon.id).update(
                    used_count=F("used_count") + 1
                )

            order.coupon_code = coupon.code if coupon else ""
            order.shipping_price = shipping_price
            order.post_price = shipping_price
            order.total = total
            order.save(
                update_fields=[
                    "subtotal",
                    "discount_amount",
                    "coupon_code",
                    "coupon_released",
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

            if (
                order.coupon_code
                and order.discount_amount > 0
                and not order.coupon_released
            ):
                Coupon.objects.select_for_update().filter(
                    code=order.coupon_code,
                    used_count__gt=0,
                ).update(
                    used_count=F("used_count") - 1
                )
                order.coupon_released = True
                changed = True

            if reason and reason not in (order.notes or ""):
                order.notes = cls._append_note(order, reason)
                changed = True

            if changed:
                order.save(
                    update_fields=[
                        "status",
                        "stock_released",
                        "coupon_released",
                        "canceled_at",
                        "notes",
                        "updated",
                    ]
                )

            return order, changed


@dataclass(frozen=True, slots=True)
class PaymentTransitionResult:
    """Result returned by a payment/order state transition."""

    order: Order
    payment_transaction: Transaction
    outcome: str
    changed: bool


class PaymentLifecycleService:
    """Atomic payment state machine for online payment callbacks.

    Every callback transition locks the order and the transaction in a stable
    order. This prevents a successful provider callback from silently reviving a
    canceled order whose stock has already been released.
    """

    OUTCOME_PAID = "paid"
    OUTCOME_ALREADY_PAID = "already_paid"
    OUTCOME_CANCELED = "canceled"
    OUTCOME_FAILED = "failed"
    OUTCOME_REVIEW = "payment_review"

    @staticmethod
    def _lock_order_and_transaction(transaction_pk):
        snapshot = Transaction.objects.only("id", "order_id").get(pk=transaction_pk)
        order = Order.objects.select_for_update().get(pk=snapshot.order_id)
        payment_transaction = Transaction.objects.select_for_update().get(pk=snapshot.pk)
        return order, payment_transaction

    @staticmethod
    def _merge_raw_response(payment_transaction, payload):
        current = payment_transaction.raw_response or {}
        return {**current, **payload}

    @classmethod
    def cancel_from_callback(cls, transaction_pk, *, callback_status):
        """Register a canceled callback and cancel the unpaid order safely."""
        with transaction.atomic():
            order, payment_transaction = cls._lock_order_and_transaction(transaction_pk)

            if payment_transaction.success or order.paid:
                return PaymentTransitionResult(
                    order=order,
                    payment_transaction=payment_transaction,
                    outcome=cls.OUTCOME_ALREADY_PAID,
                    changed=False,
                )

            payment_transaction.status = Transaction.STATUS_CANCELED
            payment_transaction.success = False
            payment_transaction.raw_response = cls._merge_raw_response(
                payment_transaction,
                {"callback_status": callback_status or "unknown", "verified": False},
            )
            payment_transaction.save(
                update_fields=["status", "success", "raw_response", "updated_at"]
            )

        order, changed = OrderLifecycleService.cancel_unpaid_order(
            order.id,
            reason="Payment was canceled by the customer or provider.",
        )
        payment_transaction.refresh_from_db()

        return PaymentTransitionResult(
            order=order,
            payment_transaction=payment_transaction,
            outcome=cls.OUTCOME_CANCELED,
            changed=changed,
        )

    @classmethod
    def mark_verification_failed(cls, transaction_pk, *, response_code):
        """Record a failed provider verification without releasing stock."""
        with transaction.atomic():
            order, payment_transaction = cls._lock_order_and_transaction(transaction_pk)

            if payment_transaction.success:
                outcome = (
                    cls.OUTCOME_REVIEW
                    if order.status == Order.STATUS_PAYMENT_REVIEW
                    else cls.OUTCOME_ALREADY_PAID
                )
                return PaymentTransitionResult(order, payment_transaction, outcome, False)

            payment_transaction.status = Transaction.STATUS_FAILED
            payment_transaction.success = False
            payment_transaction.raw_response = cls._merge_raw_response(
                payment_transaction,
                {"verified": False, "code": response_code},
            )
            payment_transaction.save(
                update_fields=["status", "success", "raw_response", "updated_at"]
            )

            return PaymentTransitionResult(
                order=order,
                payment_transaction=payment_transaction,
                outcome=cls.OUTCOME_FAILED,
                changed=True,
            )

    @classmethod
    def confirm_online_payment(cls, transaction_pk, *, ref_id, response_code):
        """Record a successful provider verification and update the order safely."""
        with transaction.atomic():
            order, payment_transaction = cls._lock_order_and_transaction(transaction_pk)

            if payment_transaction.success:
                outcome = (
                    cls.OUTCOME_REVIEW
                    if order.status == Order.STATUS_PAYMENT_REVIEW
                    else cls.OUTCOME_ALREADY_PAID
                )
                return PaymentTransitionResult(order, payment_transaction, outcome, False)

            other_successful_payment_exists = Transaction.objects.filter(
                order=order,
                success=True,
            ).exclude(pk=payment_transaction.pk).exists()

            payment_transaction.success = True
            payment_transaction.status = Transaction.STATUS_PAID
            payment_transaction.ref_id = str(ref_id)
            payment_transaction.raw_response = cls._merge_raw_response(
                payment_transaction,
                {"verified": True, "code": response_code, "ref_id": str(ref_id)},
            )
            payment_transaction.save(
                update_fields=["success", "status", "ref_id", "raw_response", "updated_at"]
            )

            review_reasons = []

            if order.stock_released or order.status == Order.STATUS_CANCELED:
                review_reasons.append(
                    "Payment was verified after the order stock had already been released."
                )

            if payment_transaction.amount != order.total:
                review_reasons.append("Transaction amount does not match order total.")

            if other_successful_payment_exists:
                review_reasons.append("More than one successful payment exists for this order.")

            was_paid = order.paid
            order.paid = True

            if review_reasons:
                order.status = Order.STATUS_PAYMENT_REVIEW
                for reason in review_reasons:
                    if reason not in (order.notes or ""):
                        order.notes = OrderLifecycleService._append_note(order, reason)
                outcome = cls.OUTCOME_REVIEW
                update_fields = ["paid", "status", "notes", "updated"]
            else:
                order.status = Order.STATUS_PROCESSING
                order.canceled_at = None
                outcome = cls.OUTCOME_PAID
                update_fields = ["paid", "status", "canceled_at", "updated"]

            order.save(update_fields=update_fields)

            if outcome == cls.OUTCOME_PAID and not was_paid:
                transaction.on_commit(
                    partial(send_order_confirmation, order),
                    robust=True,
                )

            return PaymentTransitionResult(
                order=order,
                payment_transaction=payment_transaction,
                outcome=outcome,
                changed=True,
            )

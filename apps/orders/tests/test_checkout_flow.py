
from django.test import TestCase
from django.urls import reverse


from apps.orders.models import Order
from apps.orders.tests.helpers import RedShopTestBase
from apps.orders.session_keys import (
    CHECKOUT_ADDRESS_SESSION_KEY,
    CHECKOUT_ORDER_SESSION_KEY,
    PAYMENT_ORDER_SESSION_KEY,
)


class CheckoutFlowTests(RedShopTestBase, TestCase):

    def test_stale_paid_checkout_session_is_ignored_before_new_order(self):
        old_order, payment_method = self._create_paid_stale_order()

        session = self.client.session
        self._put_single_product_cart_in_session(session)
        session[CHECKOUT_ORDER_SESSION_KEY] = old_order.id
        session[PAYMENT_ORDER_SESSION_KEY] = old_order.id
        session[CHECKOUT_ADDRESS_SESSION_KEY] = self.address.id
        session.save()

        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": payment_method},
        )

        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertNotEqual(session.get(CHECKOUT_ORDER_SESSION_KEY), old_order.id)
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 2)

    def test_checkout_review_rejects_another_users_address(self):
        self._prepare_checkout_session(address_id=self.other_address.id)
        response = self.client.get(reverse("orders:checkout_review"))
        self.assertEqual(response.status_code, 404)

    def test_order_creation_is_post_only(self):
        self._prepare_checkout_session()
        response = self.client.get(reverse("orders:checkout_create"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_payment_method_does_not_create_order(self):
        self._prepare_checkout_session()
        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "invalid"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_stores_product_snapshot_and_discount(self):
        self._prepare_checkout_session()
        response = self.client.post(
            reverse("orders:checkout_create"),
            {"payment_method": "cod"},
        )

        self.assertRedirects(response, reverse("orders:checkout_complete"))
        order = Order.objects.get(user=self.user)
        item = order.items.get()
        self.product.refresh_from_db()

        expected_subtotal = self.product.new_price * 2
        expected_discount = expected_subtotal * 10 // 100
        expected_shipping = 65_000

        self.assertEqual(item.title, self.product.name)
        self.assertEqual(item.price, self.product.new_price)
        self.assertEqual(order.subtotal, expected_subtotal)
        self.assertEqual(order.discount_amount, expected_discount)
        self.assertEqual(order.coupon_code, self.coupon.code)
        self.assertEqual(
            order.total,
            expected_subtotal - expected_discount + expected_shipping,
        )
        self.assertEqual(self.product.inventory, 8)

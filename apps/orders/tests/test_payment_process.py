from django.test import TestCase
from django.urls import reverse

from apps.orders.session_keys import (
    CHECKOUT_ORDER_SESSION_KEY,
    PAYMENT_ORDER_SESSION_KEY,
)
from apps.orders.tests.test_checkout_payment import RedShopTestBase


class PaymentProcessTests(RedShopTestBase, TestCase):

    def test_invalid_payment_session_is_cleared(self):
        session = self.client.session
        session[PAYMENT_ORDER_SESSION_KEY] = 999999
        session[CHECKOUT_ORDER_SESSION_KEY] = 999999
        session.save()

        response = self.client.get(reverse("payment:process"))

        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)

    def test_payment_process_clears_session_for_already_paid_order(self):
        order, _payment_method = self._create_paid_stale_order()
        order.payment_method = "online"
        order.paid = True
        order.stock_released = False
        order.save(update_fields=["payment_method", "paid", "stock_released", "updated"])

        session = self.client.session
        session[PAYMENT_ORDER_SESSION_KEY] = order.id
        session[CHECKOUT_ORDER_SESSION_KEY] = order.id
        session.save()

        response = self.client.get(reverse("payment:process"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/success.html")

        session = self.client.session
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)

    def test_payment_process_clears_session_for_stock_released_order(self):
        order, _payment_method = self._create_paid_stale_order()
        order.payment_method = "online"
        order.paid = False
        order.stock_released = True
        order.save(update_fields=["payment_method", "paid", "stock_released", "updated"])

        session = self.client.session
        session[PAYMENT_ORDER_SESSION_KEY] = order.id
        session[CHECKOUT_ORDER_SESSION_KEY] = order.id
        session.save()

        response = self.client.get(reverse("payment:process"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/failure.html")

        session = self.client.session
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)

from django.test import TestCase
from django.urls import reverse

from apps.orders.session_keys import CART_SESSION_KEY
from apps.orders.tests.test_checkout_payment import RedShopTestBase


class CartViewTests(RedShopTestBase, TestCase):

    def test_cart_mutation_views_are_post_only(self):
        update_response = self.client.get(reverse("cart:update_quantity"))
        remove_response = self.client.get(reverse("cart:remove_item"))

        self.assertEqual(update_response.status_code, 405)
        self.assertEqual(remove_response.status_code, 405)

    def test_read_only_cart_pages_accept_get(self):
        response = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(response.status_code, 200)

    def test_cart_update_rejects_invalid_action(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {
            str(self.product.id): {
                "quantity": 1,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session.save()

        response = self.client.post(
            reverse("cart:update_quantity"),
            {"item_id": self.product.id, "action": "invalid"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_cart_update_rejects_missing_item(self):
        response = self.client.post(
            reverse("cart:update_quantity"),
            {"item_id": self.product.id, "action": "add"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_cart_update_rejects_quantity_over_inventory(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {
            str(self.product.id): {
                "quantity": self.product.inventory,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session.save()

        response = self.client.post(
            reverse("cart:update_quantity"),
            {"item_id": self.product.id, "action": "add"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_cart_remove_rejects_missing_item(self):
        response = self.client.post(
            reverse("cart:remove_item"),
            {"item_id": self.product.id},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_cart_remove_existing_item(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {
            str(self.product.id): {
                "quantity": 1,
                "price": float(self.product.new_price),
                "weight": float(self.product.weight),
            }
        }
        session.save()

        response = self.client.post(
            reverse("cart:remove_item"),
            {"item_id": self.product.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["item_count"], 0)

from django.test import TestCase
from django.urls import reverse

from apps.orders.tests.test_checkout_payment import RedShopTestBase


class ShopSmokeTests(RedShopTestBase, TestCase):
    def test_shop_index_and_product_detail_smoke_after_query_optimization(self):
        index_response = self.client.get(reverse("shop:index"))
        self.assertEqual(index_response.status_code, 200)

        detail_response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(detail_response.status_code, 200)

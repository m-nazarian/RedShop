
import json
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

from apps.shop.models import Brand, Category, Product
from apps.shop.services import PRODUCTS_PER_PAGE, global_search


ROOT = Path(__file__).resolve().parents[2]


class ProductListingPerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Performance", slug="performance")
        cls.brand = Brand.objects.create(
            name="Performance Brand",
            About_the_company="About",
            established="2024",
        )

        products = []
        for index in range(PRODUCTS_PER_PAGE + 3):
            number = index + 1
            products.append(
                Product(
                    category=cls.category,
                    brand=cls.brand,
                    name=f"Performance Product {number:02d}",
                    slug=f"performance-product-{number:02d}",
                    description="Performance test product",
                    inventory=10,
                    price=1000 + number,
                    off=0,
                    new_price=900 + number,
                    weight=1000,
                )
            )

        Product.objects.bulk_create(products)

    def test_product_list_uses_real_pagination(self):
        response = self.client.get(reverse("shop:product_list"))

        self.assertEqual(response.status_code, 200)

        page = response.context["products"]

        self.assertTrue(page.has_next())
        self.assertEqual(page.paginator.per_page, PRODUCTS_PER_PAGE)
        self.assertEqual(page.paginator.count, PRODUCTS_PER_PAGE + 3)
        self.assertEqual(len(page.object_list), PRODUCTS_PER_PAGE)

    def test_product_list_page_two_is_available(self):
        response = self.client.get(reverse("shop:product_list"), {"page": 2})

        self.assertEqual(response.status_code, 200)

        page = response.context["products"]

        self.assertEqual(page.number, 2)
        self.assertEqual(len(page.object_list), 3)

    def test_ajax_filter_returns_paginated_results_html(self):
        response = self.client.post(
            reverse("shop:filter_products"),
            data=json.dumps({"page": 2}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["num_pages"], 2)
        self.assertIn("html_products", payload)
        self.assertIn('data-page="1"', payload["html_products"])

    def test_live_search_result_count_is_limited(self):
        results = global_search("Performance")

        self.assertLessEqual(len(results["products"]), 5)
        self.assertEqual(results["query"], "Performance")

    def test_product_detail_does_not_use_database_random_ordering(self):
        views_source = (ROOT / "apps" / "shop" / "views.py").read_text(encoding="utf-8")

        self.assertNotIn("order_by('?')", views_source)
        self.assertIn(".order_by('-created', 'id')[:6]", views_source)

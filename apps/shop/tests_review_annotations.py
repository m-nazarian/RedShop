
from django.test import TestCase
from django.urls import reverse

from apps.account.models import ShopUser
from apps.shop.models import Brand, Category, Product, ProductComment
from apps.shop.services import get_product_card_queryset


class ProductReviewAnnotationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Reviews", slug="reviews")
        cls.brand = Brand.objects.create(
            name="Review Brand",
            About_the_company="About",
            established="2024",
        )
        cls.product = Product.objects.create(
            category=cls.category,
            brand=cls.brand,
            name="Review Product",
            slug="review-product",
            description="Review test product",
            inventory=10,
            price=1000,
            off=0,
            new_price=900,
            weight=1000,
        )
        cls.empty_product = Product.objects.create(
            category=cls.category,
            brand=cls.brand,
            name="No Review Product",
            slug="no-review-product",
            description="No review product",
            inventory=10,
            price=1000,
            off=0,
            new_price=900,
            weight=1000,
        )
        cls.user1 = ShopUser.objects.create_user(
            phone="09124440301",
            password="StrongPass123!",
            first_name="Test",
            last_name="One",
        )
        cls.user2 = ShopUser.objects.create_user(
            phone="09124440302",
            password="StrongPass123!",
            first_name="Test",
            last_name="Two",
        )

        ProductComment.objects.create(
            product=cls.product,
            user=cls.user1,
            score=5,
            text="Great",
            suggest="yes",
            active=True,
        )
        ProductComment.objects.create(
            product=cls.product,
            user=cls.user2,
            score=3,
            text="Okay",
            suggest="none",
            active=True,
        )
        ProductComment.objects.create(
            product=cls.product,
            user=cls.user2,
            score=1,
            text="Hidden",
            suggest="no",
            active=False,
        )

    def test_product_card_queryset_annotates_active_review_summary(self):
        product = get_product_card_queryset(
            Product.objects.filter(pk=self.product.pk)
        ).get()

        self.assertEqual(product.review_count, 2)
        self.assertAlmostEqual(product.avg_score, 4.0)

    def test_product_card_queryset_defaults_empty_review_summary_to_zero(self):
        product = get_product_card_queryset(
            Product.objects.filter(pk=self.empty_product.pk)
        ).get()

        self.assertEqual(product.review_count, 0)
        self.assertEqual(product.avg_score, 0.0)

    def test_product_list_page_exposes_review_annotations_to_cards(self):
        response = self.client.get(reverse("shop:product_list"))

        self.assertEqual(response.status_code, 200)

        products = list(response.context["products"].object_list)

        self.assertTrue(products)
        self.assertTrue(hasattr(products[0], "review_count"))
        self.assertTrue(hasattr(products[0], "avg_score"))

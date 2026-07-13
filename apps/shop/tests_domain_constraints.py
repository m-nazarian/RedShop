
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.account.models import ShopUser
from apps.shop.models import (
    Brand,
    Category,
    CategoryFeature,
    Product,
    ProductComment,
    ProductFeatureValue,
)


class ShopDomainConstraintTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Laptop", slug="laptop")
        self.brand = Brand.objects.create(
            name="Test Brand",
            About_the_company="About test brand",
            established="2024",
        )
        self.product = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name="Test Product",
            slug="test-product",
            description="Test description",
            inventory=10,
            price=1000,
            off=100,
            new_price=900,
            weight=1000,
        )
        self.feature = CategoryFeature.objects.create(
            category=self.category,
            name="RAM",
        )
        self.user = ShopUser.objects.create_user(
            phone="09124440201",
            password="StrongPass123!",
            first_name="Test",
            last_name="User",
        )

    def test_product_feature_value_is_unique_per_product_and_feature(self):
        ProductFeatureValue.objects.create(
            product=self.product,
            feature=self.feature,
            value="16GB",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductFeatureValue.objects.create(
                    product=self.product,
                    feature=self.feature,
                    value="32GB",
                )

    def test_product_discount_cannot_exceed_price(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    category=self.category,
                    brand=self.brand,
                    name="Invalid Discount",
                    slug="invalid-discount",
                    description="Invalid",
                    inventory=1,
                    price=100,
                    off=101,
                    new_price=0,
                    weight=1,
                )

    def test_product_new_price_cannot_exceed_price_unless_zero(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.bulk_create(
                    [
                        Product(
                            category=self.category,
                            brand=self.brand,
                            name="Invalid New Price",
                            slug="invalid-new-price",
                            description="Invalid",
                            inventory=1,
                            price=100,
                            off=0,
                            new_price=101,
                            weight=1,
                        )
                    ]
                )

    def test_product_comment_score_must_be_between_one_and_five(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductComment.objects.create(
                    product=self.product,
                    user=self.user,
                    score=6,
                    text="Invalid score",
                    suggest="none",
                    active=True,
                )

    def test_product_comment_suggest_must_be_known_value(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductComment.objects.create(
                    product=self.product,
                    user=self.user,
                    score=5,
                    text="Invalid suggest",
                    suggest="maybe",
                    active=True,
                )

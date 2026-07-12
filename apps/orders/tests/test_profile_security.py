from django.test import TestCase
from django.urls import reverse

from apps.orders.tests.test_checkout_payment import RedShopTestBase


class ProfileSecurityTests(RedShopTestBase, TestCase):
    def test_profile_does_not_accept_post_or_staff_fields(self):
        response = self.client.post(
            reverse("account:profile"),
            {"is_staff": "on", "is_superuser": "on"},
        )
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 405)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

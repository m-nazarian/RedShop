
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.account.forms import AccountEditForm, UserEditForm, UserRegistrationForm
from apps.account.models import Account, ShopUser


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "account-security-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class RegistrationSecurityTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_registration_rejects_weak_passwords(self):
        form = UserRegistrationForm(
            data={
                "phone": "09125550101",
                "password": "123",
                "password2": "123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)
        self.assertFalse(ShopUser.objects.filter(phone="09125550101").exists())

    def test_registration_accepts_valid_passwords(self):
        form = UserRegistrationForm(
            data={
                "phone": "09125550102",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertEqual(user.phone, "09125550102")

    def test_registration_rejects_duplicate_phone(self):
        ShopUser.objects.create_user(
            phone="09125550103",
            password="StrongPass123!",
        )

        form = UserRegistrationForm(
            data={
                "phone": "09125550103",
                "password": "AnotherStrong123!",
                "password2": "AnotherStrong123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)


@override_settings(CACHES=TEST_CACHES)
class LoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = ShopUser.objects.create_user(
            phone="09125550201",
            password="StrongPass123!",
            first_name="Test",
            last_name="User",
        )

    def test_failed_login_attempts_are_rate_limited(self):
        url = reverse("account:login")

        for _attempt in range(5):
            response = self.client.post(
                url,
                {
                    "phone": self.user.phone,
                    "password": "wrong-password",
                },
                REMOTE_ADDR="203.0.113.10",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            {
                "phone": self.user.phone,
                "password": "StrongPass123!",
            },
            REMOTE_ADDR="203.0.113.10",
        )

        self.assertEqual(response.status_code, 429)

    def test_successful_login_resets_failure_counter(self):
        url = reverse("account:login")

        response = self.client.post(
            url,
            {
                "phone": self.user.phone,
                "password": "wrong-password",
            },
            REMOTE_ADDR="203.0.113.11",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            {
                "phone": self.user.phone,
                "password": "StrongPass123!",
            },
            REMOTE_ADDR="203.0.113.11",
        )
        self.assertEqual(response.status_code, 302)

        self.client.logout()

        for _attempt in range(4):
            response = self.client.post(
                url,
                {
                    "phone": self.user.phone,
                    "password": "wrong-password",
                },
                REMOTE_ADDR="203.0.113.11",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            {
                "phone": self.user.phone,
                "password": "StrongPass123!",
            },
            REMOTE_ADDR="203.0.113.11",
        )
        self.assertEqual(response.status_code, 302)


class ProfileFormSecurityTests(TestCase):
    def test_profile_form_allows_unique_email_for_password_reset(self):
        user = ShopUser.objects.create_user(
            phone="09125550301",
            password="StrongPass123!",
            first_name="Old",
            last_name="Name",
        )

        form = UserEditForm(
            data={
                "first_name": "New",
                "last_name": "Name",
                "email": "new@example.com",
                "address": "Test address",
            },
            instance=user,
        )

        self.assertTrue(form.is_valid(), form.errors)

        updated_user = form.save()

        self.assertEqual(updated_user.email, "new@example.com")

    def test_profile_form_rejects_duplicate_email(self):
        ShopUser.objects.create_user(
            phone="09125550302",
            password="StrongPass123!",
            email="used@example.com",
        )
        user = ShopUser.objects.create_user(
            phone="09125550303",
            password="StrongPass123!",
            first_name="Test",
            last_name="User",
        )

        form = UserEditForm(
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": "used@example.com",
                "address": "",
            },
            instance=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_public_account_form_does_not_collect_sensitive_plaintext_identifiers(self):
        self.assertNotIn("id_card", AccountEditForm.base_fields)
        self.assertNotIn("payment_card_number", AccountEditForm.base_fields)

    def test_account_form_still_saves_non_sensitive_fields(self):
        user = ShopUser.objects.create_user(
            phone="09125550304",
            password="StrongPass123!",
        )
        account, _created = Account.objects.get_or_create(user=user)

        form = AccountEditForm(
            data={"date_of_birth": "1995-01-02"},
            files={},
            instance=account,
        )

        self.assertTrue(form.is_valid(), form.errors)

        updated_account = form.save()

        self.assertEqual(str(updated_account.date_of_birth), "1995-01-02")


from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.account.models import Address, ShopUser


def create_user(phone):
    return ShopUser.objects.create_user(
        phone=phone,
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )


def create_address(user, *, is_default):
    return Address.objects.create(
        user=user,
        first_name="Ali",
        last_name="Test",
        phone="09125559999",
        province="Tehran",
        city="Tehran",
        postal_code="1234567890",
        address_line="Test address",
        is_default=is_default,
    )


class AddressDomainConstraintTests(TestCase):
    def test_user_can_have_only_one_default_address(self):
        user = create_user("09124440101")
        create_address(user, is_default=True)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_address(user, is_default=True)

    def test_user_can_have_many_non_default_addresses(self):
        user = create_user("09124440102")
        create_address(user, is_default=False)
        create_address(user, is_default=False)

        self.assertEqual(Address.objects.filter(user=user).count(), 2)

    def test_different_users_can_each_have_default_address(self):
        user1 = create_user("09124440103")
        user2 = create_user("09124440104")

        create_address(user1, is_default=True)
        create_address(user2, is_default=True)

        self.assertEqual(Address.objects.filter(is_default=True).count(), 2)

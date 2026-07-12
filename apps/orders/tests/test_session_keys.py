from django.test import TestCase

from apps.orders.session_keys import (
    CART_SESSION_KEY,
    CHECKOUT_ADDRESS_SESSION_KEY,
    CHECKOUT_ORDER_SESSION_KEY,
    COUPON_SESSION_KEY,
    PAYMENT_ORDER_SESSION_KEY,
    clear_checkout_order_session,
    clear_checkout_order_session_if_matches,
)


class CheckoutSessionHelperTests(TestCase):
    def test_clear_checkout_order_session_removes_only_order_keys(self):
        session = {
            CART_SESSION_KEY: {"1": {"quantity": 1}},
            CHECKOUT_ORDER_SESSION_KEY: 10,
            PAYMENT_ORDER_SESSION_KEY: 10,
            "unrelated": "keep",
        }

        clear_checkout_order_session(session)

        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)
        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertIn(CART_SESSION_KEY, session)
        self.assertEqual(session["unrelated"], "keep")

    def test_clear_checkout_order_session_if_matches_is_order_scoped(self):
        session = {
            CHECKOUT_ORDER_SESSION_KEY: 20,
            PAYMENT_ORDER_SESSION_KEY: 10,
            "unrelated": "keep",
        }

        clear_checkout_order_session_if_matches(session, 10)

        self.assertNotIn(PAYMENT_ORDER_SESSION_KEY, session)
        self.assertEqual(session[CHECKOUT_ORDER_SESSION_KEY], 20)
        self.assertEqual(session["unrelated"], "keep")

        clear_checkout_order_session_if_matches(session, 20)

        self.assertNotIn(CHECKOUT_ORDER_SESSION_KEY, session)
        self.assertEqual(session["unrelated"], "keep")


class CheckoutSessionKeyUsageTests(TestCase):
    def test_sensitive_checkout_files_use_session_key_constants(self):
        import ast
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[3]
        checked_files = [
            project_root / "apps" / "orders" / "views.py",
            project_root / "apps" / "payment" / "views.py",
            Path(__file__),
            Path(__file__).with_name("test_checkout_payment.py"),
        ]
        raw_session_keys = {
            CART_SESSION_KEY,
            CHECKOUT_ADDRESS_SESSION_KEY,
            CHECKOUT_ORDER_SESSION_KEY,
            COUPON_SESSION_KEY,
            PAYMENT_ORDER_SESSION_KEY,
        }

        violations = []

        for file_path in checked_files:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if not isinstance(node, ast.Constant):
                    continue

                if not isinstance(node.value, str):
                    continue

                if node.value not in raw_session_keys:
                    continue

                relative_path = file_path.relative_to(project_root)
                violations.append(f"{relative_path}:{node.lineno}: {node.value}")

        self.assertEqual(violations, [])

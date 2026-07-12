import ast
from pathlib import Path

from django.test import TestCase


class OrderTestStructureTests(TestCase):
    def test_order_tests_do_not_import_shared_helper_from_checkout_module(self):
        tests_dir = Path(__file__).resolve().parent
        legacy_module = ".".join(
            ["apps", "orders", "tests", "test_checkout_payment"]
        )
        violations = []

        for file_path in sorted(tests_dir.glob("test_*.py")):
            tree = ast.parse(file_path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == legacy_module:
                    violations.append(
                        f"{file_path.name}:{node.lineno}: {legacy_module}"
                    )

        self.assertEqual(violations, [])

    def test_redshop_test_base_only_lives_in_helpers_module(self):
        tests_dir = Path(__file__).resolve().parent
        helper_module = ".".join(["apps", "orders", "tests", "helpers"])
        violations = []

        for file_path in sorted(tests_dir.glob("test_*.py")):
            tree = ast.parse(file_path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "RedShopTestBase":
                    violations.append(
                        f"{file_path.name}:{node.lineno}: RedShopTestBase تعریف شده است"
                    )

                if not isinstance(node, ast.ImportFrom):
                    continue

                imported_names = {alias.name for alias in node.names}

                if "RedShopTestBase" in imported_names and node.module != helper_module:
                    violations.append(
                        f"{file_path.name}:{node.lineno}: {node.module}"
                    )

        self.assertEqual(violations, [])

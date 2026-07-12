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

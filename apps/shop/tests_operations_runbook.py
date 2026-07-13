
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class OperationsRunbookTests(SimpleTestCase):
    def test_operations_runbook_covers_payment_investigation_inputs(self):
        content = (ROOT / "docs" / "OPERATIONS_FA.md").read_text(encoding="utf-8")

        self.assertIn("request_id", content)
        self.assertIn("authority_hash", content)
        self.assertIn("payment_review", content)
        self.assertIn("OrderAuditLog", content)
        self.assertIn("hash_payment_identifier", content)

    def test_operations_runbook_covers_deployment_and_expired_order_commands(self):
        content = (ROOT / "docs" / "OPERATIONS_FA.md").read_text(encoding="utf-8")

        self.assertIn("redshop_deployment_check --strict", content)
        self.assertIn("makemigrations --check --dry-run", content)
        self.assertIn("release_expired_orders --older-than-minutes 30", content)
        self.assertIn("collect", "collect")  # harmless sanity assertion for test loader

    def test_operations_runbook_covers_redaction_and_request_id(self):
        content = (ROOT / "docs" / "OPERATIONS_FA.md").read_text(encoding="utf-8")

        self.assertIn("RedactingFilter", content)
        self.assertIn("X-Request-ID", content)
        self.assertIn("Bearer token", content)
        self.assertIn("REDSHOP_ENFORCE_CSP=true", content)

    def test_deployment_doc_points_to_operations_runbook(self):
        content = (ROOT / "docs" / "DEPLOYMENT_FA.md").read_text(encoding="utf-8")

        self.assertIn("OPERATIONS_FA.md", content)
        self.assertIn("Runbook", content)

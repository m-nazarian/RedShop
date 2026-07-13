
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class ReadmeSecuritySummaryTests(SimpleTestCase):
    def test_readme_has_security_and_operations_summary(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("RedShop hardening summary", content)
        self.assertIn("payment_review", content)
        self.assertIn("OrderAuditLog", content)
        self.assertIn("request_id", content)
        self.assertIn("authority_hash", content)
        self.assertIn("RedactingFilter", content)

    def test_readme_links_to_operational_docs(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("docs/DEPLOYMENT_FA.md", content)
        self.assertIn("docs/OPERATIONS_FA.md", content)
        self.assertIn("docs/ROADMAP_RESUME_FA.md", content)

    def test_readme_mentions_core_operational_commands(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("redshop_deployment_check --strict", content)
        self.assertIn("release_expired_orders --older-than-minutes 30", content)
        self.assertIn("makemigrations --check --dry-run", content)
        self.assertIn("python manage.py test -v 2", content)

    def test_readme_mentions_ci_and_redaction(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("GitHub Actions CI", content)
        self.assertIn("Bearer tokens", content)
        self.assertIn("Security headers", content)

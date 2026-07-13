
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class ReadmeSecuritySummaryTests(SimpleTestCase):
    def test_readme_has_product_and_technical_positioning(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("برای کارفرما یا مشتری", content)
        self.assertIn("برای همکار فنی", content)
        self.assertIn("RedShop یک پروژه فروشگاهی Django", content)
        self.assertIn("نمونه‌کار فنی قابل دفاع", content)

    def test_readme_has_security_and_operations_summary(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("payment_review", content)
        self.assertIn("OrderAuditLog", content)
        self.assertIn("request_id", content)
        self.assertIn("authority_hash", content)
        self.assertIn("RedactingFilter", content)
        self.assertIn("Bearer tokens", content)

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

    def test_readme_is_honest_about_current_limitations(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("دیپلوی عمومی واقعی", content)
        self.assertIn("مانیتورینگ خارجی", content)
        self.assertIn("load test واقعی", content)
        self.assertIn("این محدودیت‌ها ضعف پنهان نیستند", content)

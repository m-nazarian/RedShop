
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class DeploymentDocumentationTests(SimpleTestCase):
    def test_env_example_documents_required_production_values_without_real_secret(self):
        content = (ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("DJANGO_SECRET_KEY=", content)
        self.assertIn("DJANGO_ALLOWED_HOSTS=", content)
        self.assertIn("DJANGO_CSRF_TRUSTED_ORIGINS=", content)
        self.assertIn("REDSHOP_ENFORCE_CSP=true", content)
        self.assertNotIn("django-insecure-", content)

    def test_deployment_doc_mentions_required_operational_commands(self):
        content = (ROOT / "docs" / "DEPLOYMENT_FA.md").read_text(encoding="utf-8")

        self.assertIn("redshop_deployment_check --strict", content)
        self.assertIn("release_expired_orders", content)
        self.assertIn("collectstatic --noinput", content)
        self.assertIn("payment_review", content)

    def test_ci_workflow_runs_core_quality_gates(self):
        content = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("python manage.py makemigrations --check --dry-run", content)
        self.assertIn("python manage.py check", content)
        self.assertIn("python manage.py redshop_deployment_check", content)
        self.assertIn("python manage.py test -v 2", content)
        self.assertIn("postgres:16", content)


from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from RedShop.deployment_checks import collect_deployment_findings


class DeploymentReadinessCheckTests(SimpleTestCase):
    @override_settings(
        DEBUG=False,
        ALLOWED_HOSTS=["example.com"],
        SECRET_KEY="x" * 64,
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=3600,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        REDSHOP_ENFORCE_CSP=True,
    )
    def test_clean_production_settings_have_no_findings(self):
        self.assertEqual(collect_deployment_findings(), [])

        out = StringIO()
        call_command("redshop_deployment_check", stdout=out)

        self.assertIn("Deployment check passed", out.getvalue())

    @override_settings(
        DEBUG=True,
        ALLOWED_HOSTS=[],
        SECRET_KEY="django-insecure-change-me",
        SECURE_SSL_REDIRECT=False,
        SECURE_HSTS_SECONDS=0,
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        REDSHOP_ENFORCE_CSP=False,
    )
    def test_insecure_settings_are_reported(self):
        findings = collect_deployment_findings()
        codes = {finding.code for finding in findings}

        self.assertIn("deploy.E001", codes)
        self.assertIn("deploy.E002", codes)
        self.assertIn("deploy.E004", codes)
        self.assertIn("deploy.W001", codes)
        self.assertIn("deploy.W002", codes)
        self.assertIn("deploy.W003", codes)
        self.assertIn("deploy.W004", codes)
        self.assertIn("deploy.W005", codes)

    @override_settings(
        DEBUG=True,
        ALLOWED_HOSTS=[],
        SECRET_KEY="django-insecure-change-me",
    )
    def test_strict_mode_raises_for_blocking_findings(self):
        with self.assertRaises(CommandError):
            call_command("redshop_deployment_check", "--strict", stdout=StringIO())

    @override_settings(
        DEBUG=False,
        ALLOWED_HOSTS=["*"],
        SECRET_KEY="x" * 64,
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=3600,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        REDSHOP_ENFORCE_CSP=True,
    )
    def test_wildcard_allowed_hosts_is_blocking(self):
        codes = {finding.code for finding in collect_deployment_findings()}

        self.assertIn("deploy.E003", codes)

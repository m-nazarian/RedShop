
from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class DeploymentFinding:
    code: str
    level: str
    message: str
    hint: str = ""


def _is_placeholder_secret_key(value):
    value = str(value or "").strip().lower()

    if not value:
        return True

    placeholders = (
        "change-me",
        "changeme",
        "django-insecure",
        "secret",
        "your-secret-key",
        "replace-me",
    )

    return len(value) < 32 or any(item in value for item in placeholders)


def _has_wildcard_allowed_hosts(value):
    return "*" in [str(item).strip() for item in value or []]


def collect_deployment_findings():
    """Return deployment-readiness findings without mutating settings.

    The project can run with developer-friendly defaults locally, but this helper
    makes production risk visible before deployment.
    """
    findings = []

    debug = bool(getattr(settings, "DEBUG", False))
    allowed_hosts = list(getattr(settings, "ALLOWED_HOSTS", []) or [])
    secure_ssl_redirect = bool(getattr(settings, "SECURE_SSL_REDIRECT", False))
    secure_hsts_seconds = int(getattr(settings, "SECURE_HSTS_SECONDS", 0) or 0)
    session_secure = bool(getattr(settings, "SESSION_COOKIE_SECURE", False))
    csrf_secure = bool(getattr(settings, "CSRF_COOKIE_SECURE", False))
    csp_enforced = bool(getattr(settings, "REDSHOP_ENFORCE_CSP", False))
    secret_key = getattr(settings, "SECRET_KEY", "")

    if debug:
        findings.append(
            DeploymentFinding(
                code="deploy.E001",
                level="ERROR",
                message="DEBUG is enabled.",
                hint="Set DEBUG=False in production.",
            )
        )

    if not allowed_hosts:
        findings.append(
            DeploymentFinding(
                code="deploy.E002",
                level="ERROR",
                message="ALLOWED_HOSTS is empty.",
                hint="Set ALLOWED_HOSTS to your production domain(s).",
            )
        )
    elif _has_wildcard_allowed_hosts(allowed_hosts):
        findings.append(
            DeploymentFinding(
                code="deploy.E003",
                level="ERROR",
                message="ALLOWED_HOSTS contains a wildcard.",
                hint="Replace '*' with explicit production host names.",
            )
        )

    if _is_placeholder_secret_key(secret_key):
        findings.append(
            DeploymentFinding(
                code="deploy.E004",
                level="ERROR",
                message="SECRET_KEY looks weak or placeholder-like.",
                hint="Use a long random secret from an environment variable.",
            )
        )

    if not secure_ssl_redirect:
        findings.append(
            DeploymentFinding(
                code="deploy.W001",
                level="WARNING",
                message="SECURE_SSL_REDIRECT is disabled.",
                hint="Enable it behind HTTPS in production.",
            )
        )

    if secure_hsts_seconds < 3600:
        findings.append(
            DeploymentFinding(
                code="deploy.W002",
                level="WARNING",
                message="SECURE_HSTS_SECONDS is not configured for production.",
                hint="Use a gradual HSTS rollout after HTTPS is confirmed.",
            )
        )

    if not session_secure:
        findings.append(
            DeploymentFinding(
                code="deploy.W003",
                level="WARNING",
                message="SESSION_COOKIE_SECURE is disabled.",
                hint="Set SESSION_COOKIE_SECURE=True in production.",
            )
        )

    if not csrf_secure:
        findings.append(
            DeploymentFinding(
                code="deploy.W004",
                level="WARNING",
                message="CSRF_COOKIE_SECURE is disabled.",
                hint="Set CSRF_COOKIE_SECURE=True in production.",
            )
        )

    if not csp_enforced:
        findings.append(
            DeploymentFinding(
                code="deploy.W005",
                level="WARNING",
                message="CSP is running in report-only mode.",
                hint="Enable REDSHOP_ENFORCE_CSP=True after reviewing CSP reports.",
            )
        )

    return findings


def has_blocking_findings(findings):
    return any(finding.level == "ERROR" for finding in findings)

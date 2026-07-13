
from __future__ import annotations

from django.conf import settings


DEFAULT_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'self'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


class SecurityHeadersMiddleware:
    """Add conservative browser security headers.

    CSP is report-only by default so the current UI keeps working while the
    project gains deployment-ready visibility into unsafe asset usage.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        headers = getattr(
            settings,
            "REDSHOP_SECURITY_HEADERS",
            DEFAULT_SECURITY_HEADERS,
        )

        for header, value in headers.items():
            response.setdefault(header, value)

        csp = getattr(settings, "REDSHOP_CONTENT_SECURITY_POLICY", DEFAULT_CSP)

        if csp:
            enforce_csp = bool(getattr(settings, "REDSHOP_ENFORCE_CSP", False))
            header_name = (
                "Content-Security-Policy"
                if enforce_csp
                else "Content-Security-Policy-Report-Only"
            )
            response.setdefault(header_name, csp)

        return response

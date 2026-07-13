
from django.test import TestCase, override_settings
from django.urls import path
from django.http import HttpResponse

from RedShop.security import DEFAULT_CSP, SecurityHeadersMiddleware


def security_header_test_view(request):
    return HttpResponse("ok")


urlpatterns = [
    path("__security-header-test__/", security_header_test_view),
]


@override_settings(ROOT_URLCONF=__name__)
class SecurityHeadersMiddlewareTests(TestCase):
    def test_security_headers_are_added(self):
        response = self.client.get("/__security-header-test__/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "same-origin")
        self.assertIn("camera=()", response["Permissions-Policy"])
        self.assertEqual(response["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertIn(
            "default-src 'self'",
            response["Content-Security-Policy-Report-Only"],
        )
        self.assertNotIn("Content-Security-Policy", response)

    def test_existing_headers_are_not_overwritten(self):
        def get_response(request):
            response = HttpResponse("ok")
            response["Referrer-Policy"] = "strict-origin"
            return response

        middleware = SecurityHeadersMiddleware(get_response)
        response = middleware(None)

        self.assertEqual(response["Referrer-Policy"], "strict-origin")

    @override_settings(REDSHOP_ENFORCE_CSP=True)
    def test_csp_can_be_enforced_by_setting(self):
        response = self.client.get("/__security-header-test__/")

        self.assertEqual(response["Content-Security-Policy"], DEFAULT_CSP)
        self.assertNotIn("Content-Security-Policy-Report-Only", response)

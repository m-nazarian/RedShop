
from __future__ import annotations

import json
import logging

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path

from RedShop.logging_config import (
    JsonLogFormatter,
    RequestIdFilter,
    build_logging_config,
)
from RedShop.request_id import (
    get_request_id,
    reset_request_id,
    sanitize_request_id,
    set_request_id,
)


def request_id_test_view(request):
    return HttpResponse(getattr(request, "request_id", ""))


urlpatterns = [
    path("__request-id-test__/", request_id_test_view),
]


@override_settings(ROOT_URLCONF=__name__)
class RequestIDMiddlewareTests(SimpleTestCase):
    def test_generated_request_id_is_added_to_response_and_request(self):
        response = self.client.get("/__request-id-test__/")

        request_id = response["X-Request-ID"]

        self.assertRegex(request_id, r"^[a-f0-9]{32}$")
        self.assertEqual(response.content.decode("utf-8"), request_id)

    def test_valid_incoming_request_id_is_preserved(self):
        response = self.client.get(
            "/__request-id-test__/",
            HTTP_X_REQUEST_ID="client-request-123",
        )

        self.assertEqual(response["X-Request-ID"], "client-request-123")
        self.assertEqual(response.content.decode("utf-8"), "client-request-123")

    def test_invalid_incoming_request_id_is_replaced(self):
        response = self.client.get(
            "/__request-id-test__/",
            HTTP_X_REQUEST_ID="../bad id",
        )

        self.assertRegex(response["X-Request-ID"], r"^[a-f0-9]{32}$")
        self.assertNotEqual(response["X-Request-ID"], "../bad id")

    def test_request_id_context_is_reset_after_response(self):
        response = self.client.get("/__request-id-test__/")

        self.assertIn("X-Request-ID", response)
        self.assertEqual(get_request_id(), "-")

    def test_request_id_sanitizer_allows_safe_values_only(self):
        self.assertEqual(sanitize_request_id("abc-123_4.5:6"), "abc-123_4.5:6")
        self.assertEqual(sanitize_request_id("bad value"), "")
        self.assertEqual(sanitize_request_id("x" * 129), "")


class RequestIDLoggingTests(SimpleTestCase):
    def test_request_id_filter_injects_current_context(self):
        token = set_request_id("req-test-001")

        try:
            record = logging.LogRecord(
                name="apps.payment",
                level=logging.INFO,
                pathname=__file__,
                lineno=10,
                msg="Payment callback received",
                args=(),
                exc_info=None,
            )

            RequestIdFilter().filter(record)

            self.assertEqual(record.request_id, "req-test-001")
        finally:
            reset_request_id(token)

    def test_json_formatter_includes_request_id(self):
        token = set_request_id("req-json-001")

        try:
            record = logging.LogRecord(
                name="apps.orders",
                level=logging.INFO,
                pathname=__file__,
                lineno=10,
                msg="Order paid",
                args=(),
                exc_info=None,
            )
            RequestIdFilter().filter(record)

            payload = json.loads(JsonLogFormatter().format(record))

            self.assertEqual(payload["request_id"], "req-json-001")
            self.assertEqual(payload["logger"], "apps.orders")
            self.assertEqual(payload["message"], "Order paid")
        finally:
            reset_request_id(token)

    def test_logging_config_adds_request_id_filter_to_handlers(self):
        config = build_logging_config(log_level="INFO")

        self.assertIn("request_id", config["filters"])
        self.assertIn("request_id", config["handlers"]["console"]["filters"])
        self.assertIn("[%(request_id)s]", config["formatters"]["plain"]["format"])

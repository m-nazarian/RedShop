
from __future__ import annotations

import hashlib
from pathlib import Path

from django.test import RequestFactory, SimpleTestCase

from apps.payment.logging_events import (
    hash_payment_identifier,
    log_payment_callback_event,
)


ROOT = Path(__file__).resolve().parents[2]


class PaymentCallbackLoggingTests(SimpleTestCase):
    def test_hash_payment_identifier_is_stable_and_does_not_return_raw_value(self):
        raw = "A000000000000000000000000000123456"

        hashed = hash_payment_identifier(raw)

        self.assertEqual(hashed, hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16])
        self.assertNotEqual(hashed, raw)

    def test_payment_callback_event_payload_uses_request_id_and_authority_hash(self):
        request = RequestFactory().get("/payment/verify/")
        request.request_id = "req-payment-001"

        payload = log_payment_callback_event(
            "callback_received",
            authority="A000000000000000000000000000123456",
            status="OK",
            request=request,
        )

        self.assertEqual(payload["event"], "callback_received")
        self.assertEqual(payload["request_id"], "req-payment-001")
        self.assertEqual(payload["gateway_status"], "OK")
        self.assertNotEqual(payload["authority_hash"], "A000000000000000000000000000123456")

    def test_payment_callback_log_line_does_not_emit_raw_authority(self):
        authority = "A000000000000000000000000000123456"
        request = RequestFactory().get("/payment/verify/")
        request.request_id = "req-payment-002"

        with self.assertLogs("apps.payment", level="INFO") as captured:
            payload = log_payment_callback_event(
                "callback_received",
                authority=authority,
                status="OK",
                request=request,
            )

        log_line = "\n".join(captured.output)

        self.assertIn(payload["authority_hash"], log_line)
        self.assertNotIn(authority, log_line)
        self.assertIn("req-payment-002", log_line)

    def test_payment_verify_view_is_instrumented(self):
        content = (ROOT / "apps" / "payment" / "views.py").read_text(encoding="utf-8")

        self.assertIn("log_payment_callback_event", content)
        self.assertIn("callback_received", content)
        self.assertIn("request.GET.get", content)


from __future__ import annotations

import json
import logging

from django.test import SimpleTestCase

from RedShop.logging_config import JsonLogFormatter, RequestIdFilter, build_logging_config
from RedShop.logging_redaction import RedactingFilter, redact_text, redact_value
from RedShop.request_id import reset_request_id, set_request_id


class LoggingRedactionTests(SimpleTestCase):
    def test_redact_text_masks_email_mobile_card_token_and_secret_pairs(self):
        text = (
            "email=customer@example.com phone=09123456789 "
            "card=6274-1212-3456-7890 Authorization=Bearer abcdefghijklmnop "
            "password=my-pass token=abc123merchant"
        )

        redacted = redact_text(text)

        self.assertNotIn("customer@example.com", redacted)
        self.assertIn("cu***@example.com", redacted)
        self.assertNotIn("09123456789", redacted)
        self.assertIn("[REDACTED_MOBILE]", redacted)
        self.assertNotIn("6274-1212-3456-7890", redacted)
        self.assertIn("627412******7890", redacted)
        self.assertIn("Bearer [REDACTED_TOKEN]", redacted)
        self.assertIn("password=[REDACTED]", redacted)
        self.assertIn("token=[REDACTED]", redacted)

    def test_redact_value_masks_nested_sensitive_mapping_values(self):
        value = {
            "email": "buyer@example.com",
            "password": "secret-pass",
            "nested": {
                "api_key": "abc123",
                "message": "call 09124445566",
            },
        }

        redacted = redact_value(value)

        self.assertEqual(redacted["email"], "bu***@example.com")
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["message"], "call [REDACTED_MOBILE]")

    def test_redacting_filter_masks_record_message_and_args(self):
        record = logging.LogRecord(
            name="apps.payment",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Payment for %s using token=%s",
            args=("buyer@example.com", "plain-token"),
            exc_info=None,
        )

        RedactingFilter().filter(record)
        message = record.getMessage()

        self.assertNotIn("buyer@example.com", message)
        self.assertIn("bu***@example.com", message)
        self.assertIn("token=[REDACTED]", message)

    def test_json_formatter_outputs_redacted_message_with_request_id(self):
        token = set_request_id("req-redact-001")

        try:
            record = logging.LogRecord(
                name="apps.orders",
                level=logging.INFO,
                pathname=__file__,
                lineno=10,
                msg="Order phone=09120001122 email=buyer@example.com",
                args=(),
                exc_info=None,
            )
            RedactingFilter().filter(record)
            RequestIdFilter().filter(record)

            payload = json.loads(JsonLogFormatter().format(record))

            self.assertEqual(payload["request_id"], "req-redact-001")
            self.assertNotIn("09120001122", payload["message"])
            self.assertNotIn("buyer@example.com", payload["message"])
        finally:
            reset_request_id(token)

    def test_logging_config_applies_redaction_filter_before_request_id(self):
        config = build_logging_config(log_level="INFO")

        self.assertIn("redact", config["filters"])
        self.assertEqual(
            config["handlers"]["console"]["filters"],
            ["redact", "request_id"],
        )

        file_config = build_logging_config(log_file="logs/redshop.log")
        self.assertEqual(
            file_config["handlers"]["file"]["filters"],
            ["redact", "request_id"],
        )

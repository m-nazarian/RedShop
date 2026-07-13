
from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from django.test import SimpleTestCase

from RedShop.logging_config import (
    JsonLogFormatter,
    build_logging_config,
    normalize_log_level,
)


@contextmanager
def patched_environ(values, remove=()):
    old_values = {key: os.environ.get(key) for key in values}
    removed_values = {key: os.environ.get(key) for key in remove}

    try:
        for key in remove:
            os.environ.pop(key, None)

        for key, value in values.items():
            os.environ[key] = value

        yield
    finally:
        for key in values:
            if old_values[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_values[key]

        for key in remove:
            if removed_values[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = removed_values[key]


def import_fresh_production_settings():
    sys.modules.pop("RedShop.settings_production", None)
    return importlib.import_module("RedShop.settings_production")


class LoggingConfigTests(SimpleTestCase):
    def production_env(self, **extra):
        values = {
            "DJANGO_SECRET_KEY": "x" * 64,
            "DJANGO_ALLOWED_HOSTS": "example.com,www.example.com",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://example.com,https://www.example.com",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECURE_SSL_REDIRECT": "true",
            "DJANGO_SESSION_COOKIE_SECURE": "true",
            "DJANGO_CSRF_COOKIE_SECURE": "true",
            "REDSHOP_ENFORCE_CSP": "true",
        }
        values.update(extra)
        return values

    def test_normalize_log_level_falls_back_to_info(self):
        self.assertEqual(normalize_log_level("warning"), "WARNING")
        self.assertEqual(normalize_log_level("invalid"), "INFO")

    def test_logging_config_uses_console_handler_by_default(self):
        config = build_logging_config(log_level="WARNING")

        self.assertIn("console", config["handlers"])
        self.assertEqual(config["root"]["handlers"], ["console"])
        self.assertEqual(config["root"]["level"], "WARNING")
        self.assertIn("apps.orders", config["loggers"])
        self.assertIn("apps.payment", config["loggers"])

    def test_logging_config_can_add_rotating_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "redshop.log"
            config = build_logging_config(
                log_level="ERROR",
                log_file=log_file,
                json_format=True,
            )

        self.assertIn("file", config["handlers"])
        self.assertEqual(config["handlers"]["file"]["class"], "logging.handlers.RotatingFileHandler")
        self.assertEqual(config["handlers"]["file"]["formatter"], "json")
        self.assertIn("file", config["root"]["handlers"])

    def test_json_formatter_outputs_valid_json(self):
        formatter = JsonLogFormatter()
        record = logging.LogRecord(
            name="apps.orders",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Order paid",
            args=(),
            exc_info=None,
        )

        payload = json.loads(formatter.format(record))

        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["logger"], "apps.orders")
        self.assertEqual(payload["message"], "Order paid")

    def test_production_settings_read_logging_env_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = str(Path(tmpdir) / "redshop.log")
            with patched_environ(
                self.production_env(
                    DJANGO_LOG_LEVEL="ERROR",
                    DJANGO_LOG_FILE=log_file,
                    DJANGO_LOG_JSON="true",
                )
            ):
                module = import_fresh_production_settings()

        self.assertEqual(module.LOGGING["root"]["level"], "ERROR")
        self.assertIn("file", module.LOGGING["handlers"])
        self.assertEqual(module.LOGGING["handlers"]["console"]["formatter"], "json")

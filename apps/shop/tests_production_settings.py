
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from RedShop.env import env, env_bool, env_int, env_list, load_dotenv_file


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


class EnvironmentHelperTests(SimpleTestCase):
    def test_dotenv_loader_preserves_local_settings_compatibility(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                """
                # comment
                REDSHOP_TEST_DOTENV_SECRET="loaded-secret"
                REDSHOP_TEST_DOTENV_LIST=one,two;three
                """,
                encoding="utf-8",
            )

            with patched_environ(
                {},
                remove=(
                    "REDSHOP_TEST_DOTENV_SECRET",
                    "REDSHOP_TEST_DOTENV_LIST",
                ),
            ):
                self.assertTrue(load_dotenv_file(env_file))
                self.assertEqual(env("REDSHOP_TEST_DOTENV_SECRET"), "loaded-secret")
                self.assertEqual(
                    env_list("REDSHOP_TEST_DOTENV_LIST"),
                    ["one", "two", "three"],
                )

    def test_env_raw_helper_preserves_settings_compatibility(self):
        with patched_environ({"REDSHOP_TEST_RAW": "value"}):
            self.assertEqual(env("REDSHOP_TEST_RAW"), "value")

        self.assertEqual(env("REDSHOP_TEST_MISSING", "fallback"), "fallback")

    def test_env_bool_parses_common_values(self):
        with patched_environ({"REDSHOP_TEST_BOOL": "yes"}):
            self.assertTrue(env_bool("REDSHOP_TEST_BOOL"))

        with patched_environ({"REDSHOP_TEST_BOOL": "0"}):
            self.assertFalse(env_bool("REDSHOP_TEST_BOOL"))

    def test_env_bool_rejects_invalid_values(self):
        with patched_environ({"REDSHOP_TEST_BOOL": "sometimes"}):
            with self.assertRaises(ImproperlyConfigured):
                env_bool("REDSHOP_TEST_BOOL")

    def test_env_int_parses_integer(self):
        with patched_environ({"REDSHOP_TEST_INT": "42"}):
            self.assertEqual(env_int("REDSHOP_TEST_INT"), 42)

    def test_env_list_splits_commas_and_semicolons(self):
        with patched_environ({"REDSHOP_TEST_LIST": "a.example, b.example; c.example"}):
            self.assertEqual(
                env_list("REDSHOP_TEST_LIST"),
                ["a.example", "b.example", "c.example"],
            )

    def test_env_list_accepts_string_defaults_for_local_settings(self):
        self.assertEqual(
            env_list("REDSHOP_TEST_MISSING_LIST", "localhost,127.0.0.1"),
            ["localhost", "127.0.0.1"],
        )


class ProductionSettingsTests(SimpleTestCase):
    def production_env(self):
        return {
            "DJANGO_SECRET_KEY": "x" * 64,
            "DJANGO_ALLOWED_HOSTS": "example.com,www.example.com",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://example.com,https://www.example.com",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECURE_SSL_REDIRECT": "true",
            "DJANGO_SESSION_COOKIE_SECURE": "true",
            "DJANGO_CSRF_COOKIE_SECURE": "true",
            "REDSHOP_ENFORCE_CSP": "true",
        }

    def test_production_settings_are_env_driven_and_secure_by_default(self):
        with patched_environ(self.production_env()):
            module = import_fresh_production_settings()

        self.assertFalse(module.DEBUG)
        self.assertEqual(module.SECRET_KEY, "x" * 64)
        self.assertEqual(module.ALLOWED_HOSTS, ["example.com", "www.example.com"])
        self.assertEqual(
            module.CSRF_TRUSTED_ORIGINS,
            ["https://example.com", "https://www.example.com"],
        )
        self.assertTrue(module.SECURE_SSL_REDIRECT)
        self.assertTrue(module.SESSION_COOKIE_SECURE)
        self.assertTrue(module.CSRF_COOKIE_SECURE)
        self.assertGreaterEqual(module.SECURE_HSTS_SECONDS, 3600)
        self.assertTrue(module.REDSHOP_ENFORCE_CSP)

    def test_production_settings_require_secret_key(self):
        env_values = self.production_env()
        env_values.pop("DJANGO_SECRET_KEY")

        with patched_environ(env_values, remove=("DJANGO_SECRET_KEY",)):
            with self.assertRaises(ImproperlyConfigured):
                import_fresh_production_settings()

    def test_production_settings_require_allowed_hosts(self):
        env_values = self.production_env()
        env_values.pop("DJANGO_ALLOWED_HOSTS")

        with patched_environ(env_values, remove=("DJANGO_ALLOWED_HOSTS",)):
            with self.assertRaises(ImproperlyConfigured):
                import_fresh_production_settings()

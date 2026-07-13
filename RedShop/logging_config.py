
from __future__ import annotations

import json
import logging
from pathlib import Path

from RedShop.logging_redaction import RedactingFilter
from RedShop.request_id import get_request_id


VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class RequestIdFilter(logging.Filter):
    """Inject the current request ID into every log record."""

    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        return True


class JsonLogFormatter(logging.Formatter):
    """Small JSON formatter for production logs without extra dependencies."""

    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "time": self.formatTime(record, self.datefmt),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def normalize_log_level(value):
    level = str(value or "INFO").strip().upper()

    if level not in VALID_LOG_LEVELS:
        return "INFO"

    return level


def build_logging_config(log_level="INFO", log_file=None, json_format=False):
    """Build Django LOGGING configuration for production."""
    level = normalize_log_level(log_level)

    formatters = {
        "plain": {
            "format": "%(levelname)s %(asctime)s [%(request_id)s] %(name)s %(message)s",
        },
        "verbose": {
            "format": "%(levelname)s %(asctime)s [%(request_id)s] %(name)s %(module)s:%(lineno)d %(message)s",
        },
        "json": {
            "()": "RedShop.logging_config.JsonLogFormatter",
        },
    }

    filters = {
        "request_id": {
            "()": "RedShop.logging_config.RequestIdFilter",
        },
        "redact": {
            "()": "RedShop.logging_redaction.RedactingFilter",
        },
    }

    formatter_name = "json" if json_format else "plain"
    handler_filters = ["redact", "request_id"]

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": formatter_name,
            "filters": handler_filters,
            "level": level,
        },
    }

    root_handlers = ["console"]

    if log_file:
        log_path = Path(str(log_file)).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_path),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": formatter_name,
            "filters": handler_filters,
            "level": level,
        }
        root_handlers.append("file")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": filters,
        "formatters": formatters,
        "handlers": handlers,
        "root": {
            "handlers": root_handlers,
            "level": level,
        },
        "loggers": {
            "django": {
                "handlers": root_handlers,
                "level": level,
                "propagate": False,
            },
            "django.request": {
                "handlers": root_handlers,
                "level": "ERROR",
                "propagate": False,
            },
            "apps.orders": {
                "handlers": root_handlers,
                "level": level,
                "propagate": False,
            },
            "apps.payment": {
                "handlers": root_handlers,
                "level": level,
                "propagate": False,
            },
        },
    }


from __future__ import annotations

import json
import logging
from pathlib import Path


VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class JsonLogFormatter(logging.Formatter):
    """Small JSON formatter for production logs without extra dependencies."""

    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
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
    """Build Django LOGGING configuration for production.

    Console logging is always enabled. File logging is opt-in through
    DJANGO_LOG_FILE so local development and container deployments stay simple.
    """
    level = normalize_log_level(log_level)

    formatters = {
        "plain": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(module)s:%(lineno)d %(message)s",
        },
        "json": {
            "()": "RedShop.logging_config.JsonLogFormatter",
        },
    }

    formatter_name = "json" if json_format else "plain"

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": formatter_name,
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
            "level": level,
        }
        root_handlers.append("file")

    return {
        "version": 1,
        "disable_existing_loggers": False,
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

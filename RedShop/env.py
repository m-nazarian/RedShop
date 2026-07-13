
from __future__ import annotations

import os

from django.core.exceptions import ImproperlyConfigured


TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


def env_value(name, default=None, *, required=False):
    value = os.environ.get(name)

    if value is None or value == "":
        if required:
            raise ImproperlyConfigured(f"Missing required environment variable: {name}")
        return default

    return value


def env_required(name):
    return env_value(name, required=True)


def env_bool(name, default=False):
    value = env_value(name, default=None)

    if value is None:
        return default

    normalized = str(value).strip().lower()

    if normalized in TRUE_VALUES:
        return True

    if normalized in FALSE_VALUES:
        return False

    raise ImproperlyConfigured(
        f"Environment variable {name} must be a boolean value."
    )


def env_int(name, default=0):
    value = env_value(name, default=None)

    if value is None:
        return default

    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"Environment variable {name} must be an integer."
        ) from exc


def env_list(name, default=None, *, required=False):
    value = env_value(name, default=None, required=required)

    if value is None:
        return list(default or [])

    items = [
        item.strip()
        for item in str(value).replace(";", ",").split(",")
        if item.strip()
    ]

    if required and not items:
        raise ImproperlyConfigured(
            f"Environment variable {name} must contain at least one value."
        )

    return items

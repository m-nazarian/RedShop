
from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = BASE_DIR / ".env"


def _unquote(value):
    value = str(value).strip()

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value


def load_dotenv_file(path=None, *, override=False):
    """Load simple KEY=value pairs from a .env file.

    This keeps the project independent from python-dotenv while preserving the
    previous local-development behavior expected by settings.py.
    """
    env_file = Path(path or os.environ.get("REDSHOP_ENV_FILE", DEFAULT_ENV_FILE))

    if not env_file.exists():
        return False

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export "):].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = _unquote(value)

        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = value

    return True


load_dotenv_file()


def env(name, default=None, *, required=False):
    """Backward-compatible raw environment helper used by settings.py."""
    return env_value(name, default=default, required=required)


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


def _split_env_list(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    return [
        item.strip()
        for item in str(value).replace(";", ",").split(",")
        if item.strip()
    ]


def env_list(name, default=None, *, required=False):
    value = env_value(name, default=None, required=required)

    items = _split_env_list(default if value is None else value)

    if required and not items:
        raise ImproperlyConfigured(
            f"Environment variable {name} must contain at least one value."
        )

    return items

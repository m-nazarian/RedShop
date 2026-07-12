from __future__ import annotations

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

# این فایل خواندن تنظیمات محیطی را ساده می‌کند.
# وابستگی خارجی اضافه نشده تا پروژه با همان محیط فعلی هم اجرا شود.
BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_LOADED = False


def load_dotenv(path: Path | None = None) -> None:
    """فایل .env ریشه پروژه را به os.environ اضافه می‌کند."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = path or BASE_DIR / ".env"
    if not env_path.exists():
        _ENV_LOADED = True
        return

    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # مقدارهای واقعی محیط اولویت دارند تا اجرای PyCharm، تست و CI قابل کنترل بماند.
        os.environ.setdefault(key, value)

    _ENV_LOADED = True


def env(name: str, default: str | None = None, *, required: bool = False) -> str:
    """خواندن رشته از محیط با پیام خطای روشن."""
    load_dotenv()
    value = os.environ.get(name, default)

    if required and (value is None or value == ""):
        raise ImproperlyConfigured(f"تنظیم محیطی {name} مقدار ندارد.")

    return "" if value is None else value


def env_bool(name: str, default: bool = False) -> bool:
    """خواندن مقدار بولی از محیط."""
    value = env(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on", "y"}


def env_int(name: str, default: int = 0) -> int:
    """خواندن عدد صحیح از محیط."""
    value = env(name, str(default)).strip()

    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"تنظیم محیطی {name} باید عدد صحیح باشد.") from exc


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    """خواندن لیست جداشده با ویرگول از محیط."""
    fallback = ",".join(default or [])
    value = env(name, fallback)
    return [item.strip() for item in value.split(",") if item.strip()]

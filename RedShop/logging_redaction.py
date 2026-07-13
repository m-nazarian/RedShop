
from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence


EMAIL_RE = re.compile(r"(?P<local>[A-Za-z0-9._%+-]{1,64})@(?P<domain>[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
IRAN_MOBILE_RE = re.compile(r"(?<!\d)(?:\+?98|0)?9\d{9}(?!\d)")
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
AUTH_BEARER_RE = re.compile(
    r"\b(?P<key>authorization)(?P<sep>\s*[:=]\s*)Bearer\s+[A-Za-z0-9._~+/=-]{12,}",
    re.IGNORECASE,
)
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE)
AUTH_VALUE_RE = re.compile(
    r"\b(?P<key>authorization)(?P<sep>\s*[:=]\s*)(?P<value>(?!Bearer\b)[^\s,;&]+)",
    re.IGNORECASE,
)
KEY_VALUE_SECRET_RE = re.compile(
    r"(?P<key>\b(?:password|passwd|secret|token|api[_-]?key|merchant[_-]?id)\b)"
    r"(?P<sep>\s*[:=]\s*)"
    r"(?P<value>[^\s,;&]+)",
    re.IGNORECASE,
)
SENSITIVE_KEY_RE = re.compile(
    r"(password|passwd|secret|token|authorization|api[_-]?key|merchant[_-]?id)",
    re.IGNORECASE,
)


def _mask_email(match):
    local = match.group("local")
    domain = match.group("domain")

    if len(local) <= 2:
        masked_local = local[:1] + "***"
    else:
        masked_local = local[:2] + "***"

    return f"{masked_local}@{domain}"


def _mask_card_like(value):
    digits = re.sub(r"\D", "", value)

    if len(digits) < 13 or len(digits) > 19:
        return value

    return f"{digits[:6]}******{digits[-4:]}"


def redact_text(value):
    text = str(value)

    text = EMAIL_RE.sub(_mask_email, text)
    text = IRAN_MOBILE_RE.sub("[REDACTED_MOBILE]", text)

    text = AUTH_BEARER_RE.sub(
        lambda m: f"{m.group('key')}{m.group('sep')}Bearer [REDACTED_TOKEN]",
        text,
    )
    text = BEARER_RE.sub("Bearer [REDACTED_TOKEN]", text)
    text = AUTH_VALUE_RE.sub(
        lambda m: f"{m.group('key')}{m.group('sep')}[REDACTED]",
        text,
    )
    text = KEY_VALUE_SECRET_RE.sub(
        lambda m: f"{m.group('key')}{m.group('sep')}[REDACTED]",
        text,
    )

    def replace_card(match):
        return _mask_card_like(match.group(0))

    text = CARD_RE.sub(replace_card, text)

    return text


def redact_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, Mapping):
        redacted = {}

        for key, item in value.items():
            key_text = str(key)
            if SENSITIVE_KEY_RE.search(key_text):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_value(item)

        return redacted

    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)

    if isinstance(value, list):
        return [redact_value(item) for item in value]

    if isinstance(value, set):
        return {redact_value(item) for item in value}

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        try:
            return type(value)(redact_value(item) for item in value)
        except TypeError:
            return redact_text(value)

    return value


class RedactingFilter(logging.Filter):
    """Mask common sensitive values before records reach formatters/handlers."""

    def filter(self, record):
        try:
            rendered_message = record.getMessage()
        except Exception:
            rendered_message = f"{record.msg} {record.args}"

        record.msg = redact_text(rendered_message)
        record.args = ()

        return True


from __future__ import annotations

import re
import uuid
from contextvars import ContextVar

from django.conf import settings


REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_META_HEADER = "HTTP_X_REQUEST_ID"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_request_id_context = ContextVar("redshop_request_id", default="-")


def generate_request_id():
    return uuid.uuid4().hex


def sanitize_request_id(value):
    value = str(value or "").strip()

    if _REQUEST_ID_PATTERN.fullmatch(value):
        return value

    return ""


def get_request_id():
    return _request_id_context.get()


def set_request_id(value):
    return _request_id_context.set(value or "-")


def reset_request_id(token):
    _request_id_context.reset(token)


class RequestIDMiddleware:
    """Attach a correlation ID to every request and response."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.meta_header = getattr(
            settings,
            "REDSHOP_REQUEST_ID_META_HEADER",
            REQUEST_ID_META_HEADER,
        )
        self.response_header = getattr(
            settings,
            "REDSHOP_REQUEST_ID_RESPONSE_HEADER",
            REQUEST_ID_HEADER,
        )

    def __call__(self, request):
        request_id = sanitize_request_id(request.META.get(self.meta_header))
        if not request_id:
            request_id = generate_request_id()

        token = set_request_id(request_id)
        request.request_id = request_id

        try:
            response = self.get_response(request)
            response.setdefault(self.response_header, request_id)
            return response
        finally:
            reset_request_id(token)


from __future__ import annotations

import hashlib
import logging

from RedShop.request_id import get_request_id


logger = logging.getLogger("apps.payment")


def hash_payment_identifier(value):
    """Return a short stable hash for gateway identifiers.

    Raw payment authority/reference values must not be emitted to production
    logs. A short hash is enough to correlate repeated callbacks.
    """
    value = str(value or "").strip()

    if not value:
        return ""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _request_id_from(request):
    if request is not None:
        request_id = getattr(request, "request_id", None)
        if request_id:
            return request_id

    return get_request_id()


def _order_payload(order):
    if order is None:
        return {}

    return {
        "order_id": getattr(order, "pk", None),
        "order_number": getattr(order, "order_number", ""),
        "order_status": getattr(order, "status", ""),
        "order_paid": bool(getattr(order, "paid", False)),
    }


def _transaction_payload(transaction):
    if transaction is None:
        return {}

    return {
        "transaction_id": getattr(transaction, "pk", None),
        "transaction_status": getattr(transaction, "status", ""),
        "transaction_success": bool(getattr(transaction, "success", False)),
    }


def log_payment_callback_event(
    event,
    *,
    authority="",
    status="",
    order=None,
    transaction=None,
    request=None,
    message="payment callback event",
    extra=None,
):
    payload = {
        "event": str(event),
        "request_id": _request_id_from(request),
        "gateway_status": str(status or ""),
        "authority_hash": hash_payment_identifier(authority),
    }
    payload.update(_order_payload(order))
    payload.update(_transaction_payload(transaction))

    if extra:
        payload["extra"] = extra

    logger.info("%s %s", message, payload)

    return payload

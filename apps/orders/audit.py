
from __future__ import annotations

from RedShop.request_id import get_request_id

from .models import OrderAuditLog


ORDER_AUDIT_PAYMENT_REVIEW_EXPORT = OrderAuditLog.ACTION_PAYMENT_REVIEW_EXPORT
ORDER_AUDIT_ADMIN_NOTE = OrderAuditLog.ACTION_ADMIN_NOTE


def _safe_actor(actor):
    if actor is None:
        return None

    if not getattr(actor, "is_authenticated", False):
        return None

    return actor


def log_order_audit(
    *,
    order=None,
    action,
    actor=None,
    request_id=None,
    message="",
    metadata=None,
):
    """Create an append-only audit log for sensitive order operations."""
    return OrderAuditLog.objects.create(
        order=order,
        actor=_safe_actor(actor),
        action=action,
        request_id=str(request_id or get_request_id() or "-")[:128],
        message=message or "",
        metadata=metadata or {},
    )


from __future__ import annotations

import hashlib

from django.core.cache import cache


class LoginThrottle:
    """Small cache-backed throttle for the phone/password login endpoint.

    The throttle stores only hashed identifiers. It rate-limits both the phone
    value and the client IP address so repeated guessing cannot hammer a single
    account or spread attempts across many phone numbers from the same address.
    """

    MAX_FAILURES = 5
    WINDOW_SECONDS = 15 * 60
    LOCKOUT_SECONDS = 15 * 60
    CACHE_PREFIX = "account-login-throttle:v1"

    @classmethod
    def _hash(cls, value: str) -> str:
        normalized = (value or "unknown").strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def _client_ip(cls, request) -> str:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    @classmethod
    def _keys(cls, request, identifier: str) -> tuple[str, str, str, str]:
        identifier_hash = cls._hash(identifier)
        ip_hash = cls._hash(cls._client_ip(request))

        return (
            f"{cls.CACHE_PREFIX}:fail:identifier:{identifier_hash}",
            f"{cls.CACHE_PREFIX}:block:identifier:{identifier_hash}",
            f"{cls.CACHE_PREFIX}:fail:ip:{ip_hash}",
            f"{cls.CACHE_PREFIX}:block:ip:{ip_hash}",
        )

    @classmethod
    def is_blocked(cls, request, identifier: str) -> bool:
        _identifier_fail_key, identifier_block_key, _ip_fail_key, ip_block_key = cls._keys(
            request,
            identifier,
        )
        return bool(cache.get(identifier_block_key) or cache.get(ip_block_key))

    @classmethod
    def _increment_failure(cls, fail_key: str, block_key: str) -> None:
        failures = int(cache.get(fail_key) or 0) + 1
        cache.set(fail_key, failures, cls.WINDOW_SECONDS)

        if failures >= cls.MAX_FAILURES:
            cache.set(block_key, True, cls.LOCKOUT_SECONDS)

    @classmethod
    def register_failure(cls, request, identifier: str) -> None:
        identifier_fail_key, identifier_block_key, ip_fail_key, ip_block_key = cls._keys(
            request,
            identifier,
        )

        cls._increment_failure(identifier_fail_key, identifier_block_key)
        cls._increment_failure(ip_fail_key, ip_block_key)

    @classmethod
    def reset(cls, request, identifier: str) -> None:
        for key in cls._keys(request, identifier):
            cache.delete(key)

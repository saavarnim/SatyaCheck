"""app/identity.py – HMAC pseudonymisation and in-memory rate limiting (docs/03)."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request

from app.config import (
    REPORTER_SALT,
    IP_SALT,
    TRUST_BODY_IDENTITY,
    RATE_PER_HOUR,
    RATE_PER_INDICATOR_HOUR,
)


def hash_token(salt: str, value: str) -> str:
    """Return the first 16 hex characters of HMAC-SHA256(salt, value)."""
    if not value:
        value = "anonymous"
    return hmac.new(
        salt.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]


def get_ip_prefix(raw_ip: str) -> str:
    """Return /24 for IPv4 or /48 for IPv6 as string."""
    try:
        ip = ipaddress.ip_address(raw_ip.strip())
        if ip.version == 4:
            net = ipaddress.ip_network(f"{ip}/24", strict=False)
            return str(net.network_address) + "/24"
        else:
            net = ipaddress.ip_network(f"{ip}/48", strict=False)
            return str(net.network_address) + "/48"
    except Exception:
        return "0.0.0.0/24"


def resolve_reporter_and_ip_tokens(
    request: Request,
    body_reporter_id: Optional[str] = None,
    body_ip_prefix: Optional[str] = None,
) -> tuple[str, str]:
    """Resolve reporter_token and ip_token using HMAC-SHA256.

    Per docs/03:
    If body has reporter_id and ip_prefix and TRUST_BODY_IDENTITY=true -> use them.
    Else reporter token from header X-Device-Id and ip token from /24 (IPv4) or /48 (IPv6)
    of first X-Forwarded-For hop (or client host).
    """
    if TRUST_BODY_IDENTITY and body_reporter_id and body_ip_prefix:
        reporter_raw = body_reporter_id
        ip_raw = body_ip_prefix
    else:
        # Header / request fallback
        reporter_raw = request.headers.get("X-Device-Id") or body_reporter_id or "anonymous"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client and request.client.host:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"
        ip_raw = body_ip_prefix if (TRUST_BODY_IDENTITY and body_ip_prefix) else get_ip_prefix(client_ip)

    reporter_token = hash_token(REPORTER_SALT, reporter_raw)
    ip_token = hash_token(IP_SALT, ip_raw)
    return reporter_token, ip_token


# In-memory sliding window rate limiter:
# _reporter_history: {reporter_token: [timestamp, ...]}
# _indicator_history: {(reporter_token, indicator_id): [timestamp, ...]}
_reporter_history: dict[str, list[datetime]] = {}
_indicator_history: dict[tuple[str, int], list[datetime]] = {}


def check_and_record_rate_limit(
    reporter_token: str,
    indicator_id: int,
    now: datetime,
) -> bool:
    """Return True if request is allowed, False if rate limit exceeded.

    Limits (docs/03):
    - RATE_PER_HOUR (30) submissions/hour per reporter_token
    - RATE_PER_INDICATOR_HOUR (10) submissions/hour per reporter_token per indicator
    """
    one_hour_ago = now - timedelta(hours=1)

    # Clean and check reporter submissions
    rep_times = [t for t in _reporter_history.get(reporter_token, []) if t > one_hour_ago]
    if len(rep_times) >= RATE_PER_HOUR:
        return False

    # Clean and check per-indicator submissions
    ind_key = (reporter_token, indicator_id)
    ind_times = [t for t in _indicator_history.get(ind_key, []) if t > one_hour_ago]
    if len(ind_times) >= RATE_PER_INDICATOR_HOUR:
        return False

    # Record current timestamp
    rep_times.append(now)
    _reporter_history[reporter_token] = rep_times

    ind_times.append(now)
    _indicator_history[ind_key] = ind_times

    return True


def reset_rate_limits() -> None:
    """Clear in-memory rate limiting state (for testing)."""
    _reporter_history.clear()
    _indicator_history.clear()

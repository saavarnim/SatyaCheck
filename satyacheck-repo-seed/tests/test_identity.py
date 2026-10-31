"""tests/test_identity.py – Unit tests for HMAC tokens and rate limiting (T3c)."""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest

from app.identity import (
    hash_token,
    get_ip_prefix,
    resolve_reporter_and_ip_tokens,
    check_and_record_rate_limit,
    reset_rate_limits,
)


@pytest.fixture(autouse=True)
def clean_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


# ===================================================================
# 1. HMAC Token Hashing Tests
# ===================================================================

def test_hash_token_deterministic_16_hex():
    """hash_token must be deterministic and exactly 16 hex characters."""
    t1 = hash_token("test-salt", "reporter_123")
    t2 = hash_token("test-salt", "reporter_123")
    assert t1 == t2
    assert len(t1) == 16
    assert all(c in "0123456789abcdef" for c in t1)


def test_hash_token_distinct():
    """Different values or salts must produce distinct tokens."""
    t1 = hash_token("salt-1", "user")
    t2 = hash_token("salt-2", "user")
    t3 = hash_token("salt-1", "other_user")
    assert t1 != t2
    assert t1 != t3


def test_hash_token_handles_empty():
    """Empty or None values default to anonymous and return a valid 16-hex token."""
    t_empty = hash_token("salt", "")
    t_none = hash_token("salt", None)
    assert t_empty == t_none
    assert len(t_empty) == 16


# ===================================================================
# 2. IP Prefix Extraction Tests (IPv4 /24 and IPv6 /48)
# ===================================================================

def test_get_ip_prefix_ipv4():
    """IPv4 addresses must be masked to /24."""
    assert get_ip_prefix("192.168.1.155") == "192.168.1.0/24"
    assert get_ip_prefix("10.0.55.99") == "10.0.55.0/24"


def test_get_ip_prefix_ipv6():
    """IPv6 addresses must be masked to /48."""
    assert get_ip_prefix("2001:db8:85a3:8d3:1319:8a2e:370:7348") == "2001:db8:85a3::/48"


def test_get_ip_prefix_invalid():
    """Invalid IPs safely fall back to 0.0.0.0/24."""
    assert get_ip_prefix("invalid-ip") == "0.0.0.0/24"
    assert get_ip_prefix("") == "0.0.0.0/24"


# ===================================================================
# 3. Identity Resolution (Header vs Body)
# ===================================================================

def test_resolve_tokens_body_when_trusted(monkeypatch):
    """When TRUST_BODY_IDENTITY=True, body values are used."""
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    req = MagicMock()
    req.headers = {"X-Device-Id": "header_dev", "X-Forwarded-For": "1.2.3.4"}

    rep_tok, ip_tok = resolve_reporter_and_ip_tokens(
        req,
        body_reporter_id="body_user_1",
        body_ip_prefix="10.0.0.0/24",
    )
    # Token reflects body values
    assert rep_tok == hash_token("dev-reporter-salt", "body_user_1")
    assert ip_tok == hash_token("dev-ip-salt", "10.0.0.0/24")


def test_resolve_tokens_headers_when_body_not_trusted(monkeypatch):
    """When TRUST_BODY_IDENTITY=False, headers are used even if body is supplied."""
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", False)
    req = MagicMock()
    req.headers = {"X-Device-Id": "device_header_xyz", "X-Forwarded-For": "203.0.113.195, 198.51.100.1"}

    rep_tok, ip_tok = resolve_reporter_and_ip_tokens(
        req,
        body_reporter_id="body_user_1",
        body_ip_prefix="10.0.0.0/24",
    )
    # Token reflects headers
    assert rep_tok == hash_token("dev-reporter-salt", "device_header_xyz")
    assert ip_tok == hash_token("dev-ip-salt", "203.0.113.0/24")


# ===================================================================
# 4. Sliding Window Rate Limiting Tests
# ===================================================================

def test_rate_limit_per_reporter():
    """Reporter exceeding 30 submissions in 1 hour is rejected."""
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    rep = "token_rep_1"

    # 30 submissions to different indicators
    for ind_id in range(30):
        allowed = check_and_record_rate_limit(rep, ind_id, now)
        assert allowed is True

    # 31st submission within the same hour is blocked
    blocked = check_and_record_rate_limit(rep, 99, now)
    assert blocked is False

    # After 1 hour has elapsed, new submission is allowed
    future = now + timedelta(hours=1, seconds=1)
    allowed_future = check_and_record_rate_limit(rep, 99, future)
    assert allowed_future is True


def test_rate_limit_per_reporter_per_indicator():
    """Reporter exceeding 10 submissions for the same indicator in 1 hour is rejected."""
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    rep = "token_rep_2"
    ind_id = 42

    # 10 submissions to the same indicator
    for _ in range(10):
        allowed = check_and_record_rate_limit(rep, ind_id, now)
        assert allowed is True

    # 11th submission is blocked
    blocked = check_and_record_rate_limit(rep, ind_id, now)
    assert blocked is False

    # Submission to a DIFFERENT indicator is still allowed (reporter total is only 10 < 30)
    allowed_diff = check_and_record_rate_limit(rep, 43, now)
    assert allowed_diff is True

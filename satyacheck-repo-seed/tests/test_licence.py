"""tests/test_licence.py – Part 1: licence crypto unit tests.

All tests generate their own keypair at runtime; no real key is ever used.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone, timedelta

import pytest
from nacl.signing import SigningKey

from app.licence import canonical_bytes, sign, verify, parse_expiry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def keypair():
    """Generate a fresh Ed25519 keypair for the test session."""
    sk = SigningKey.generate()
    return bytes(sk), bytes(sk.verify_key)


@pytest.fixture()
def licence_data(keypair):
    """Return a valid (licensee, expires_at, signature_b64) tuple."""
    private_key, _public_key = keypair
    licensee = "Test Corp"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    sig = sign(licensee, expires_at, private_key)
    return licensee, expires_at, sig


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCanonicalBytes:
    def test_deterministic(self):
        a = canonical_bytes("Alice", "2030-01-01T00:00:00+00:00")
        b = canonical_bytes("Alice", "2030-01-01T00:00:00+00:00")
        assert a == b

    def test_sorted_keys(self):
        raw = canonical_bytes("Alice", "2030-01-01T00:00:00+00:00")
        assert b'"expires_at"' in raw
        assert raw.index(b'"expires_at"') < raw.index(b'"licensee"')


class TestValidLicence:
    def test_valid_signature_returns_true(self, keypair, licence_data):
        _private, public = keypair
        licensee, expires_at, sig = licence_data
        assert verify(licensee, expires_at, sig, public) is True


class TestTamperedExpiresAt:
    def test_tampered_expires_at_fails(self, keypair, licence_data):
        _private, public = keypair
        licensee, _expires_at, sig = licence_data
        tampered = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        assert verify(licensee, tampered, sig, public) is False


class TestTamperedLicensee:
    def test_tampered_licensee_fails(self, keypair, licence_data):
        _private, public = keypair
        _licensee, expires_at, sig = licence_data
        assert verify("Evil Corp", expires_at, sig, public) is False


class TestWrongKey:
    def test_wrong_key_fails(self, licence_data):
        other_sk = SigningKey.generate()
        other_pub = bytes(other_sk.verify_key)
        licensee, expires_at, sig = licence_data
        assert verify(licensee, expires_at, sig, other_pub) is False


class TestMalformedBase64:
    def test_malformed_base64_raises(self, keypair):
        _private, public = keypair
        with pytest.raises(ValueError, match="[Mm]alformed"):
            verify("X", "2030-01-01T00:00:00+00:00", "!!!not-base64!!!", public)


class TestNaiveTimestamp:
    def test_naive_timestamp_rejected(self):
        """A timestamp without UTC offset must raise ValueError."""
        with pytest.raises(ValueError, match="offset"):
            parse_expiry("2030-01-01T00:00:00")

    def test_aware_timestamp_accepted(self):
        dt = parse_expiry("2030-01-01T00:00:00+00:00")
        assert dt.tzinfo is not None

    def test_aware_timestamp_with_offset(self):
        dt = parse_expiry("2030-06-15T10:30:00+05:30")
        assert dt.tzinfo is not None

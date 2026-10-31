"""tests/test_licence.py – Licence crypto + integration tests.

All tests generate their own keypair at runtime; no real key is ever used.
Part 1: crypto unit tests (canonical_bytes, sign, verify, parse_expiry).
Part 2: integration tests via TestClient (middleware, routes, cache, clock rollback).
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone, timedelta

import pytest
from nacl.signing import SigningKey

from app.licence import canonical_bytes, sign, verify, parse_expiry


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture(scope="session")
def keypair():
    """Generate a fresh Ed25519 keypair for the test session."""
    sk = SigningKey.generate()
    return bytes(sk), bytes(sk.verify_key)


@pytest.fixture()
def pub_b64(keypair):
    """Base64-encoded public key string (for LICENCE_PUBLIC_KEY env/config)."""
    _, pub = keypair
    return base64.b64encode(pub).decode("ascii")


@pytest.fixture()
def licence_data(keypair):
    """Return a valid (licensee, expires_at, signature_b64) tuple."""
    private_key, _ = keypair
    licensee = "Test Corp"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    sig = sign(licensee, expires_at, private_key)
    return licensee, expires_at, sig


def _make_licence_json(keypair, licensee="Test Corp", minutes=60):
    """Helper: build a signed licence dict."""
    private_key, _ = keypair
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    sig = sign(licensee, expires_at, private_key)
    return {"licensee": licensee, "expires_at": expires_at, "signature": sig}


# ===================================================================
# Part 1 – Crypto unit tests
# ===================================================================

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
        _, public = keypair
        licensee, expires_at, sig = licence_data
        assert verify(licensee, expires_at, sig, public) is True


class TestTamperedExpiresAt:
    def test_tampered_expires_at_fails(self, keypair, licence_data):
        _, public = keypair
        licensee, _, sig = licence_data
        tampered = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        assert verify(licensee, tampered, sig, public) is False


class TestTamperedLicensee:
    def test_tampered_licensee_fails(self, keypair, licence_data):
        _, public = keypair
        _, expires_at, sig = licence_data
        assert verify("Evil Corp", expires_at, sig, public) is False


class TestWrongKey:
    def test_wrong_key_fails(self, licence_data):
        other_sk = SigningKey.generate()
        other_pub = bytes(other_sk.verify_key)
        licensee, expires_at, sig = licence_data
        assert verify(licensee, expires_at, sig, other_pub) is False


class TestMalformedBase64:
    def test_malformed_base64_raises(self, keypair):
        _, public = keypair
        with pytest.raises(ValueError, match="[Mm]alformed"):
            verify("X", "2030-01-01T00:00:00+00:00", "!!!not-base64!!!", public)


class TestNaiveTimestamp:
    def test_naive_timestamp_rejected(self):
        with pytest.raises(ValueError, match="offset"):
            parse_expiry("2030-01-01T00:00:00")

    def test_aware_timestamp_accepted(self):
        dt = parse_expiry("2030-01-01T00:00:00+00:00")
        assert dt.tzinfo is not None

    def test_aware_timestamp_with_offset(self):
        dt = parse_expiry("2030-06-15T10:30:00+05:30")
        assert dt.tzinfo is not None


# ===================================================================
# Part 2 – Integration tests (routes + middleware)
# ===================================================================

@pytest.fixture()
def licence_client(test_db, monkeypatch, keypair):
    """TestClient with licence module wired to the test DB and a test keypair."""
    import app.licence as licence_mod
    import app.clock as clock_module
    import app.db as db_mod
    from app.main import app
    from app.db import get_db
    from app.licence import LicenceState
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    _, pub = keypair
    pub_b64_str = base64.b64encode(pub).decode("ascii")

    # Point licence module at our test public key
    monkeypatch.setattr("app.config.LICENCE_PUBLIC_KEY", pub_b64_str)
    monkeypatch.setattr("app.licence.LICENCE_PUBLIC_KEY", pub_b64_str)

    # Wire DB - point app.db engine/SessionLocal at test engine
    test_engine = test_db.get_bind()
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db_mod, "engine", test_engine)
    monkeypatch.setattr(db_mod, "SessionLocal", TestingSession)

    # Skip seed (verified.json has a field mismatch not related to licence)
    monkeypatch.setattr(db_mod, "_seed", lambda: None)

    # Create licence_state table in the test DB
    LicenceState.__table__.create(bind=test_engine, checkfirst=True)

    # Override SessionLocal and engine in licence module too
    monkeypatch.setattr(licence_mod, "SessionLocal", TestingSession)
    monkeypatch.setattr(licence_mod, "engine", test_engine)

    # Override get_db for routes
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Reset licence cache
    licence_mod.reset_cache()

    # Set up a controllable clock
    _now = [datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)]

    def fake_now():
        return _now[0]

    def set_time(dt):
        _now[0] = dt

    monkeypatch.setattr(clock_module, "now", fake_now)

    with TestClient(app, raise_server_exceptions=False) as c:
        c._set_time = set_time   # type: ignore[attr-defined]
        c._keypair = keypair     # type: ignore[attr-defined]
        c._fake_now = _now       # type: ignore[attr-defined]
        yield c

    app.dependency_overrides.clear()
    licence_mod.reset_cache()


def _post_licence(client, keypair, licensee="Test Corp", minutes=60):
    """Helper: POST a signed licence to the client."""
    priv, _ = keypair
    now = client._fake_now[0]
    expires_at = (now + timedelta(minutes=minutes)).isoformat()
    sig = sign(licensee, expires_at, priv)
    body = {"licensee": licensee, "expires_at": expires_at, "signature": sig}
    return client.post("/license", json=body), expires_at


class TestExpiredGives403:
    """Expired → protected paths get 403 but /health, /license and static stay open."""

    def test_no_licence_protected_403(self, licence_client):
        """No licence loaded → protected path returns 403."""
        r = licence_client.get("/reports")
        assert r.status_code == 403
        assert r.json()["error"] == "LICENSE_EXPIRED"

    def test_no_licence_health_200(self, licence_client):
        """No licence → /health still works."""
        r = licence_client.get("/health")
        assert r.status_code == 200

    def test_no_licence_get_license_200(self, licence_client):
        """/license GET works when expired."""
        r = licence_client.get("/license")
        assert r.status_code == 200
        assert r.json()["status"] == "EXPIRED"

    def test_no_licence_post_license_accessible(self, licence_client):
        """/license POST is accessible when expired (may return 400 for bad body)."""
        r = licence_client.post("/license", json={})
        # Not 403 – it's open; it may return 400 for invalid input
        assert r.status_code != 403

    def test_no_licence_static_file(self, licence_client):
        """Static files are reachable when expired (not in protected prefixes)."""
        # / serves index.html via the static mount – should not be 403
        r = licence_client.get("/")
        assert r.status_code != 403

    def test_expired_licence_protected_403(self, licence_client):
        """Active licence that then expires → protected 403."""
        kp = licence_client._keypair
        # Post a licence expiring in 30 minutes
        resp, _ = _post_licence(licence_client, kp, minutes=30)
        assert resp.status_code == 200

        # Protected paths work while active
        r = licence_client.get("/lookup")
        # Might be 404/400 (route may not have logic yet) but NOT 403
        assert r.status_code != 403

        # Advance time past expiry
        licence_client._set_time(
            licence_client._fake_now[0] + timedelta(minutes=31)
        )
        # Force cache refresh
        import app.licence as lm
        lm.reset_cache()

        r = licence_client.get("/lookup")
        assert r.status_code == 403


class TestRenewalWithoutRestart:
    """Renewal without restart, data preserved."""

    def test_renewal_no_restart(self, licence_client):
        kp = licence_client._keypair

        # Upload first licence (1 hour)
        resp, _ = _post_licence(licence_client, kp, minutes=60)
        assert resp.status_code == 200

        # GET /license → ACTIVE
        r = licence_client.get("/license")
        assert r.json()["status"] == "ACTIVE"

        # Advance time past first licence
        licence_client._set_time(
            licence_client._fake_now[0] + timedelta(minutes=61)
        )
        import app.licence as lm
        lm.reset_cache()

        # Now expired
        r = licence_client.get("/license")
        assert r.json()["status"] == "EXPIRED"

        # Upload a new licence (another hour from "now")
        resp2, _ = _post_licence(licence_client, kp, minutes=60)
        assert resp2.status_code == 200

        # Active again — no restart needed
        r = licence_client.get("/license")
        assert r.json()["status"] == "ACTIVE"


class TestShortLicenceOverLong:
    """A 5-minute licence replacing a long one must work."""

    def test_five_min_replaces_long(self, licence_client):
        kp = licence_client._keypair

        # Upload a long licence (30 days)
        resp, _ = _post_licence(licence_client, kp, minutes=60*24*30)
        assert resp.status_code == 200

        r = licence_client.get("/license")
        data = r.json()
        assert data["status"] == "ACTIVE"
        long_remaining = data["seconds_remaining"]

        # Upload a short licence (5 minutes)
        resp2, _ = _post_licence(licence_client, kp, minutes=5)
        assert resp2.status_code == 200

        r2 = licence_client.get("/license")
        data2 = r2.json()
        assert data2["status"] == "ACTIVE"
        assert data2["seconds_remaining"] <= 300
        assert data2["seconds_remaining"] < long_remaining


class TestClockRollback:
    """Clock rollback beyond tolerance → treat as expired."""

    def test_clock_rollback_blocks_protected(self, licence_client):
        kp = licence_client._keypair
        import app.licence as lm

        # Upload valid licence
        resp, _ = _post_licence(licence_client, kp, minutes=60)
        assert resp.status_code == 200

        # Set last_seen to "now"
        now = licence_client._fake_now[0]
        lm.set_last_seen_server_time(now)
        lm.reset_cache()
        lm.refresh_cache(force=True)

        # Roll clock back beyond tolerance (> 120s)
        rolled_back = now - timedelta(seconds=300)
        licence_client._set_time(rolled_back)
        lm.reset_cache()

        # Protected path should be blocked
        r = licence_client.get("/reports")
        assert r.status_code == 403

        # /health and /license still work
        r = licence_client.get("/health")
        assert r.status_code == 200
        r = licence_client.get("/license")
        assert r.status_code == 200


class TestBadSignature400:
    """POST with bad signature → 400 INVALID_SIGNATURE."""

    def test_bad_signature(self, licence_client):
        body = {
            "licensee": "Test Corp",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "signature": base64.b64encode(b"not-a-real-signature-64-bytes-pad" * 2).decode(),
        }
        r = licence_client.post("/license", json=body)
        assert r.status_code == 400
        assert r.json()["error"] == "INVALID_SIGNATURE"


class TestAlreadyExpired400:
    """POST with expires_at in the past → 400 ALREADY_EXPIRED."""

    def test_already_expired(self, licence_client):
        kp = licence_client._keypair
        priv, _ = kp
        now = licence_client._fake_now[0]
        # Sign a licence that's already expired
        past = (now - timedelta(hours=1)).isoformat()
        sig = sign("Test Corp", past, priv)
        body = {"licensee": "Test Corp", "expires_at": past, "signature": sig}
        r = licence_client.post("/license", json=body)
        assert r.status_code == 400
        assert r.json()["error"] == "ALREADY_EXPIRED"

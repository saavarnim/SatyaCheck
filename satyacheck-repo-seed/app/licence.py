"""app/licence.py – Licence crypto + runtime state (cache, DB, clock rollback).

Part 1: canonical_bytes, sign, verify, parse_expiry (pure functions, stdlib + PyNaCl).
Part 2: in-memory cache, is_allowed, DB persistence, clock-rollback detection,
        LICENSE_BOOTSTRAP.  Imports app.clock and app.db (engine only) + app.config.

Spec: docs/05-licence.md
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time as _time
from datetime import datetime, timezone
from typing import Optional

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from sqlalchemy import Column, DateTime, Integer, MetaData, String
from sqlalchemy.orm import declarative_base

import app.clock as clock
from app.config import LICENCE_PROTECTED_PREFIXES, LICENCE_PUBLIC_KEY
from app.db import engine, SessionLocal

licence_metadata = MetaData()
LicenceBase = declarative_base(metadata=licence_metadata)


class LicenceState(LicenceBase):
    __tablename__ = "licence_state"

    id = Column(Integer, primary_key=True, default=1)
    licensee = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    signature = Column(String, nullable=True)
    last_seen_server_time = Column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CACHE_TTL_S: float = 5.0          # refresh from DB every 5 s
CLOCK_TOLERANCE_S: int = 120      # seconds of allowed clock drift
LAST_SEEN_WRITE_INTERVAL_S: float = 20.0  # persist last_seen at most every 20 s


# ---------------------------------------------------------------------------
# Canonical form (pure – part 1)
# ---------------------------------------------------------------------------

def canonical_bytes(licensee: str, expires_at: str) -> bytes:
    """Return the UTF-8 canonical byte string that gets signed."""
    payload = {"licensee": licensee, "expires_at": expires_at}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Sign / verify (pure – part 1)
# ---------------------------------------------------------------------------

def sign(licensee: str, expires_at: str, private_key_bytes: bytes) -> str:
    """Sign the canonical payload and return the signature as base64."""
    signing_key = SigningKey(private_key_bytes)
    message = canonical_bytes(licensee, expires_at)
    signed = signing_key.sign(message)
    return base64.b64encode(signed.signature).decode("ascii")


def verify(licensee: str, expires_at: str, signature_b64: str,
           public_key_bytes: bytes) -> bool:
    """Return True iff the signature is valid. Raises ValueError on bad base64."""
    verify_key = VerifyKey(public_key_bytes)
    message = canonical_bytes(licensee, expires_at)
    try:
        sig_bytes = base64.b64decode(signature_b64, validate=True)
    except Exception as exc:
        raise ValueError(f"Malformed base64 signature: {exc}") from exc
    try:
        verify_key.verify(message, sig_bytes)
        return True
    except BadSignatureError:
        return False


# ---------------------------------------------------------------------------
# Timestamp helpers (pure – part 1)
# ---------------------------------------------------------------------------

def parse_expiry(expires_at: str) -> datetime:
    """Parse an ISO-8601 timestamp that MUST include a UTC offset."""
    dt = datetime.fromisoformat(expires_at)
    if dt.tzinfo is None:
        raise ValueError(
            f"expires_at must include a UTC offset (got naive timestamp): {expires_at}"
        )
    return dt


# ===================================================================
# Part 2 – runtime state
# ===================================================================

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class _LicenceCache:
    """Thread-safe in-memory licence state cache."""

    def __init__(self):
        self.lock = threading.Lock()
        self.licensee: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.signature: Optional[str] = None
        self.last_seen_server_time: Optional[datetime] = None
        self.last_refresh: float = 0.0
        self.last_persist: float = 0.0
        self._initialised = False

    def is_stale(self) -> bool:
        return (_time.monotonic() - self.last_refresh) > CACHE_TTL_S

    def update(self, row: Optional[LicenceState]):
        with self.lock:
            if row is None:
                self.licensee = None
                self.expires_at = None
                self.signature = None
                self.last_seen_server_time = None
            else:
                self.licensee = row.licensee
                self.expires_at = _ensure_utc(row.expires_at)
                self.signature = row.signature
                self.last_seen_server_time = _ensure_utc(row.last_seen_server_time)
            self.last_refresh = _time.monotonic()


_cache = _LicenceCache()


# ---------------------------------------------------------------------------
# DB helpers (use the shared engine from app.db)
# ---------------------------------------------------------------------------

def _ensure_table():
    """Lazily create the licence_state table if it doesn't exist."""
    licence_metadata.create_all(bind=engine, checkfirst=True)


def _load_row() -> Optional[LicenceState]:
    """Load the single licence row from DB."""
    _ensure_table()
    db = SessionLocal()
    try:
        row = db.query(LicenceState).filter_by(id=1).first()
        if row is not None:
            db.expunge(row)
        return row
    except Exception:
        return None
    finally:
        db.close()


def _save_row(licensee: str, expires_at_dt: datetime, signature: str,
              last_seen: Optional[datetime] = None):
    """Upsert the single licence row."""
    _ensure_table()
    db = SessionLocal()
    try:
        row = db.query(LicenceState).filter_by(id=1).first()
        if row is None:
            row = LicenceState(id=1)
            db.add(row)
        row.licensee = licensee
        row.expires_at = expires_at_dt
        row.signature = signature
        if last_seen is not None:
            row.last_seen_server_time = last_seen
        db.commit()
    finally:
        db.close()


def _update_last_seen(dt: datetime):
    """Persist last_seen_server_time (keep max)."""
    _ensure_table()
    db = SessionLocal()
    try:
        row = db.query(LicenceState).filter_by(id=1).first()
        if row is not None:
            current_last_seen = _ensure_utc(row.last_seen_server_time)
            dt_utc = _ensure_utc(dt)
            if current_last_seen is None or (dt_utc is not None and dt_utc > current_last_seen):
                row.last_seen_server_time = dt_utc
                db.commit()
            else:
                db.rollback()
        else:
            db.rollback()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Refresh cache from DB
# ---------------------------------------------------------------------------

def refresh_cache(force: bool = False):
    """Reload licence state from DB into the in-memory cache."""
    if not force and not _cache.is_stale():
        return
    row = _load_row()
    _cache.update(row)


# ---------------------------------------------------------------------------
# Public-key resolution
# ---------------------------------------------------------------------------

def _get_public_key_bytes() -> Optional[bytes]:
    """Return the 32-byte public key or None."""
    # env/config: base64-encoded
    pk_str = LICENCE_PUBLIC_KEY
    if not pk_str:
        return None
    try:
        return base64.b64decode(pk_str)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# is_allowed – called by LicenceMiddleware in main.py
# ---------------------------------------------------------------------------

def is_allowed(path: str) -> bool:
    """Return True if the request *path* is allowed under the current licence state.

    Protected prefixes are blocked when: no licence, expired, or clock rollback detected.
    Always-open: /health, /license, static (anything not in LICENCE_PROTECTED_PREFIXES).
    """
    # Always-open paths are never blocked (middleware only calls us for protected paths,
    # but be defensive).
    if not any(path.startswith(p) for p in LICENCE_PROTECTED_PREFIXES):
        return True

    # Ensure cache is fresh
    refresh_cache()

    # No licence → treat as expired
    if _cache.licensee is None or _cache.expires_at is None:
        return False

    now = clock.now()

    # Persist last_seen (at most every LAST_SEEN_WRITE_INTERVAL_S)
    _maybe_persist_last_seen(now)

    # Clock rollback check
    if _cache.last_seen_server_time is not None:
        if now < _cache.last_seen_server_time:
            from datetime import timedelta
            drift = (_cache.last_seen_server_time - now).total_seconds()
            if drift > CLOCK_TOLERANCE_S:
                return False

    # Expiry check
    if now >= _cache.expires_at:
        return False

    return True


def _maybe_persist_last_seen(now: datetime):
    """Write last_seen_server_time to DB at most every LAST_SEEN_WRITE_INTERVAL_S."""
    elapsed = _time.monotonic() - _cache.last_persist
    if elapsed >= LAST_SEEN_WRITE_INTERVAL_S:
        _update_last_seen(now)
        _cache.last_seen_server_time = now
        _cache.last_persist = _time.monotonic()


# ---------------------------------------------------------------------------
# Store licence (POST /license logic)
# ---------------------------------------------------------------------------

def store_licence(licensee: str, expires_at_str: str, signature_b64: str) -> dict:
    """Validate and store a new licence.

    Returns a dict with either {"ok": True} or {"error": str, "status_code": int}.
    """
    # Get public key
    pub_bytes = _get_public_key_bytes()
    if pub_bytes is None:
        return {"error": "INVALID_SIGNATURE", "status_code": 400}

    # Verify signature
    try:
        valid = verify(licensee, expires_at_str, signature_b64, pub_bytes)
    except ValueError:
        return {"error": "INVALID_SIGNATURE", "status_code": 400}

    if not valid:
        return {"error": "INVALID_SIGNATURE", "status_code": 400}

    # Parse and validate expiry
    try:
        expires_dt = parse_expiry(expires_at_str)
    except ValueError:
        return {"error": "INVALID_SIGNATURE", "status_code": 400}

    now = clock.now()
    if now >= expires_dt:
        return {"error": "ALREADY_EXPIRED", "status_code": 400}

    # Store in DB
    _ensure_table()
    _save_row(licensee, expires_dt, signature_b64, last_seen=now)

    # Immediately refresh cache
    refresh_cache(force=True)

    return {"ok": True}


# ---------------------------------------------------------------------------
# GET /license logic
# ---------------------------------------------------------------------------

def get_licence_status() -> dict:
    """Return the current licence status for GET /license."""
    refresh_cache()
    now = clock.now()

    if _cache.licensee is None or _cache.expires_at is None:
        return {
            "licensee": None,
            "expires_at": None,
            "status": "EXPIRED",
            "seconds_remaining": 0,
        }

    remaining = (_cache.expires_at - now).total_seconds()
    # Clock rollback → treat as expired
    if _cache.last_seen_server_time is not None:
        drift = (_cache.last_seen_server_time - now).total_seconds()
        if drift > CLOCK_TOLERANCE_S:
            remaining = 0

    status = "ACTIVE" if remaining > 0 else "EXPIRED"
    return {
        "licensee": _cache.licensee,
        "expires_at": _cache.expires_at.isoformat(),
        "status": status,
        "seconds_remaining": max(0, int(remaining)),
    }


# ---------------------------------------------------------------------------
# Initialisation (call from startup)
# ---------------------------------------------------------------------------

def init_licence():
    """Create table, load bootstrap licence if present, populate cache."""
    _ensure_table()

    # LICENSE_BOOTSTRAP: env var with licence JSON string
    bootstrap = os.getenv("LICENSE_BOOTSTRAP", "")
    if bootstrap:
        try:
            data = json.loads(bootstrap)
            existing = _load_row()
            if existing is None or existing.licensee is None:
                store_licence(data["licensee"], data["expires_at"], data["signature"])
        except Exception:
            pass  # silently ignore bad bootstrap

    refresh_cache(force=True)


# ---------------------------------------------------------------------------
# Force-set last_seen for testing / clock rollback scenarios
# ---------------------------------------------------------------------------

def set_last_seen_server_time(dt: datetime):
    """Directly set last_seen_server_time in DB and cache (for tests)."""
    _ensure_table()
    dt_utc = _ensure_utc(dt)
    db = SessionLocal()
    try:
        row = db.query(LicenceState).filter_by(id=1).first()
        if row is not None:
            row.last_seen_server_time = dt_utc
            db.commit()
    finally:
        db.close()
    _cache.last_seen_server_time = dt_utc


def reset_cache():
    """Reset the in-memory cache (for tests between runs)."""
    _cache.licensee = None
    _cache.expires_at = None
    _cache.signature = None
    _cache.last_seen_server_time = None
    _cache.last_refresh = 0.0
    _cache.last_persist = 0.0
    _cache._initialised = False

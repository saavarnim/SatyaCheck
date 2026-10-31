"""app/licence.py – Licence crypto helpers (pure functions, stdlib + PyNaCl only).

Spec: docs/05-licence.md
Signature = Ed25519 (PyNaCl) over UTF-8 of
    json.dumps({"licensee":..., "expires_at":...}, sort_keys=True, separators=(",", ":"))
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Tuple

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey


# ---------------------------------------------------------------------------
# Canonical form
# ---------------------------------------------------------------------------

def canonical_bytes(licensee: str, expires_at: str) -> bytes:
    """Return the UTF-8 canonical byte string that gets signed.

    json.dumps with sort_keys=True and compact separators, so the
    canonical form is deterministic regardless of dict ordering.
    """
    payload = {"licensee": licensee, "expires_at": expires_at}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Sign / verify
# ---------------------------------------------------------------------------

def sign(licensee: str, expires_at: str, private_key_bytes: bytes) -> str:
    """Sign the canonical payload and return the signature as base64.

    *private_key_bytes*: 32-byte Ed25519 seed (raw, not base64).
    """
    signing_key = SigningKey(private_key_bytes)
    message = canonical_bytes(licensee, expires_at)
    signed = signing_key.sign(message)
    # signed.signature is the 64-byte detached signature
    return base64.b64encode(signed.signature).decode("ascii")


def verify(licensee: str, expires_at: str, signature_b64: str,
           public_key_bytes: bytes) -> bool:
    """Return True if *signature_b64* is a valid Ed25519 signature over the
    canonical payload for the given public key.

    *public_key_bytes*: 32-byte raw public key.
    Raises ValueError on malformed base64.
    """
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
# Timestamp helpers
# ---------------------------------------------------------------------------

def parse_expiry(expires_at: str) -> datetime:
    """Parse an ISO-8601 timestamp that MUST include a UTC offset.

    Raises ValueError if the string is naive (no timezone info) or
    otherwise unparseable.
    """
    dt = datetime.fromisoformat(expires_at)
    if dt.tzinfo is None:
        raise ValueError(
            f"expires_at must include a UTC offset (got naive timestamp): {expires_at}"
        )
    return dt

"""app/normalise.py – Canonicalise phone/upi/url/sender_id. Raises InvalidIdentifier -> 400."""
from __future__ import annotations

import re


class InvalidIdentifier(ValueError):
    """Raised for invalid identifiers. Message never contains the raw value."""


# ── Phone ──────────────────────────────────────────────────────────────────────

_STRAIGHT_RUN = re.compile(r"^(?:0123456789|9876543210|12345678|87654321).*$")


def _normalise_phone(raw: str) -> str:
    # Strip everything except digits
    digits = re.sub(r"[^\d]", "", raw)

    # Rule 1: toll-free (1800 / 1860, 8-11 digits total)
    if re.match(r"^(1800|1860)\d{4,7}$", digits):
        return digits

    # Rule 2: 4-digit short code ^19\d\d$
    if re.match(r"^19\d{2}$", digits):
        return digits

    # Rule 3: mobile / landline -> canonical +91XXXXXXXXXX
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) != 10:
        raise InvalidIdentifier("invalid phone")
    if digits[0] not in "23456789":
        raise InvalidIdentifier("invalid phone")
    if len(set(digits)) == 1:
        raise InvalidIdentifier("invalid phone: all same digit")
    # Reject known sequential runs per spec (1234567890 style)
    # ASSUMED: only these two exact sequences are blocked; 9876543210 is valid per doc example
    _BLOCKED_RUNS = {"1234567890", "0123456789"}
    if digits in _BLOCKED_RUNS:
        raise InvalidIdentifier("invalid phone: sequential run")

    return f"+91{digits}"


# ── UPI ───────────────────────────────────────────────────────────────────────

_UPI_RE = re.compile(r"^[a-z0-9._-]{2,64}@[a-z][a-z0-9]{1,32}$")


def _normalise_upi(raw: str) -> str:
    canon = raw.lower().replace(" ", "")
    if not _UPI_RE.match(canon):
        raise InvalidIdentifier("invalid upi")
    return canon


# ── URL ───────────────────────────────────────────────────────────────────────

def _normalise_url(raw: str) -> str:
    s = raw.strip()
    # Add scheme if missing
    if not re.match(r"^https?://", s, re.IGNORECASE):
        s = "https://" + s
    # Force https
    s = re.sub(r"^http://", "https://", s, flags=re.IGNORECASE)
    # Split into parts: scheme://host/path?query#fragment
    m = re.match(r"^(https://)([^/?#]+)(.*?)$", s, re.IGNORECASE)
    if not m:
        raise InvalidIdentifier("invalid url")
    host = m.group(2).lower()
    path_etc = m.group(3)
    # Drop query and fragment
    path_etc = re.sub(r"[?#].*$", "", path_etc)
    # Drop trailing slash(es)
    path_etc = path_etc.rstrip("/")
    # Remove leading www.
    host = re.sub(r"^www\.", "", host)
    # Validate host: must contain a dot and a 2+ letter TLD
    parts = host.split(".")
    if len(parts) < 2 or len(parts[-1]) < 2:
        raise InvalidIdentifier("invalid url host")
    return f"https://{host}{path_etc}"


# ── Sender ID ─────────────────────────────────────────────────────────────────

def _normalise_sender(raw: str) -> str:
    s = raw.strip().upper().replace("-", "")
    # If 8 chars, drop first 2 (e.g. VMHDFCBK -> HDFCBK, AD-HDFCBK -> ADHDFCBK -> drop AD)
    if len(s) == 8:
        s = s[2:]
    if not re.match(r"^[A-Z0-9]{6}$", s):
        raise InvalidIdentifier("invalid sender_id")
    return s


# ── Public API ────────────────────────────────────────────────────────────────

_HANDLERS = {
    "phone": _normalise_phone,
    "upi": _normalise_upi,
    "url": _normalise_url,
    "sender_id": _normalise_sender,
}


def normalise(identifier_type: str, value: str) -> str:
    """Return canonical form of the identifier, or raise InvalidIdentifier."""
    handler = _HANDLERS.get(identifier_type)
    if handler is None:
        raise InvalidIdentifier("unknown identifier_type")
    return handler(value)


def is_valid(identifier_type: str, value: str) -> bool:
    """Return True if value is valid for the given type."""
    try:
        normalise(identifier_type, value)
        return True
    except (InvalidIdentifier, ValueError):
        return False


# ── Other-field normalisation helpers ─────────────────────────────────────────

_KNOWN_CHANNELS = {
    "phone call", "sms or whatsapp", "qr code",
    "fake website", "upi request", "something else",
}


def normalise_channel(raw: str) -> str:
    """Normalise channel; anything unknown -> 'Something else'."""
    s = (raw or "").strip().lower()
    return raw.strip() if s in _KNOWN_CHANNELS else "Something else"


_KNOWN_SCAM_TYPES = {
    "digital-arrest", "fake-kyc-link", "upi-refund-qr",
    "investment-group", "courier-customs", "job-offer",
    "lottery-prize", "loan-app-harassment", "electricity-disconnection",
    "fake-customer-care", "otp-call", "sextortion",
}


def normalise_scam_type(raw: str) -> str:
    """Normalise scam_type; anything unknown -> 'other'."""
    s = (raw or "").strip().lower()
    return s if s in _KNOWN_SCAM_TYPES else "other"

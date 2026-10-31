"""app/redact.py – Strip PII from report notes. Notes are internal-only, never returned."""
from __future__ import annotations

import re

# Patterns to redact (in order)
_PATTERNS = [
    # Indian mobile / landline with optional country code and separators
    re.compile(r"(?:\+?91[\s\-]?)?[6-9]\d[\s\-]?\d{4}[\s\-]?\d{4}"),
    # 10-12 digit numeric runs (catches other long numbers)
    re.compile(r"\b\d{10,12}\b"),
    # UPI ids: word@word
    re.compile(r"[a-zA-Z0-9._-]{2,64}@[a-zA-Z][a-zA-Z0-9]{1,32}"),
    # Email addresses
    re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    # URLs (http/https or bare domain-looking things)
    re.compile(r"https?://[^\s]+"),
    re.compile(r"\bwww\.[^\s]+"),
]

_MAX_LEN = 300


def redact(note: str) -> str:
    """Replace PII patterns with [redacted] and cap at 300 chars."""
    if not note:
        return ""
    result = note
    for pattern in _PATTERNS:
        result = pattern.sub("[redacted]", result)
    return result[:_MAX_LEN]

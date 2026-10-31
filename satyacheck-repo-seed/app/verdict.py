"""app/verdict.py – Verdict ordering + display_value masking (docs/03)."""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

from app.config import KNOWN_MIN_COHORTS, KNOWN_MIN_SCORE, UNMASK_MIN
from app.trust import IndicatorTrust


def verdict(
    trust: Optional[IndicatorTrust],
    is_verified: bool,
    has_active_challenge: bool,
) -> str:
    """Return verdict string per docs/03 precedence order:

    1. indicator in verified_indicators -> VERIFIED_BUSINESS (always wins)
    2. cohort_count == 0 -> NO_REPORTS
    3. active challenge (under_review) -> cap at SUSPICIOUS, challenged=true
    4. cohort_count >= KNOWN_MIN_COHORTS (3) AND score >= KNOWN_MIN_SCORE (2.5) -> KNOWN_SCAM
    5. else SUSPICIOUS
    """
    if is_verified:
        return "VERIFIED_BUSINESS"
    if trust is None or trust.cohort_count == 0:
        return "NO_REPORTS"
    if has_active_challenge:
        return "SUSPICIOUS"
    if trust.cohort_count >= KNOWN_MIN_COHORTS and trust.score >= KNOWN_MIN_SCORE:
        return "KNOWN_SCAM"
    return "SUSPICIOUS"


def mask_display_value(identifier_type: str, canonical_value: str) -> str:
    """Return masked display value per docs/03 masking rules:

    - phone/toll-free: first 2 digits of national number + XXXXX + last 3
      (+919876543210 -> 98XXXXX210); 4-digit short code: 1XX0
    - upi: first char + ***@ + handle (r***@okaxis)
    - url: first 3 chars of host + *** + rest of TLD part + /... (sbi***.in/...)
    - sender: first 2 chars + **** (HD****)
    """
    if identifier_type == "phone":
        digits_only = re.sub(r"\D", "", canonical_value)
        if len(digits_only) == 4:
            return f"{digits_only[0]}XX{digits_only[-1]}"
        if canonical_value.startswith("+91"):
            nat = canonical_value[3:]
        else:
            nat = digits_only
        if len(nat) >= 5:
            return f"{nat[:2]}XXXXX{nat[-3:]}"
        return f"{canonical_value[:2]}XXXXX"

    elif identifier_type == "upi":
        if "@" in canonical_value:
            user, handle = canonical_value.split("@", 1)
            first_char = user[0] if user else ""
            return f"{first_char}***@{handle}"
        return f"{canonical_value[:1]}***"

    elif identifier_type == "url":
        val = canonical_value
        if "://" not in val:
            val = "http://" + val
        parsed = urlparse(val)
        host = parsed.netloc or val.split("/")[0]
        dot_idx = host.find(".")
        if dot_idx != -1:
            host_prefix = host[:dot_idx][:3]
            tld_part = host[dot_idx:]
            return f"{host_prefix}***{tld_part}/..."
        return f"{host[:3]}***/..."

    elif identifier_type == "sender_id":
        prefix = canonical_value[:2]
        return f"{prefix}****"

    return canonical_value


def resolve_display_value(
    identifier_type: str,
    canonical_value: str,
    cohort_count: int,
    is_verified: bool,
) -> str:
    """Return unmasked canonical_value if is_verified or cohort_count >= UNMASK_MIN (3),
    otherwise return masked string (docs/03).
    """
    if is_verified or cohort_count >= UNMASK_MIN:
        return canonical_value
    return mask_display_value(identifier_type, canonical_value)

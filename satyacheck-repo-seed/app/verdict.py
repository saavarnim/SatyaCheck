"""app/verdict.py – Verdict ordering + display_value masking. (T3)"""
from __future__ import annotations

from app.trust import IndicatorTrust


def verdict(
    trust: IndicatorTrust,
    is_verified: bool,
    has_active_challenge: bool,
) -> str:
    """
    Return verdict string per docs/03 order:
      VERIFIED_BUSINESS > NO_REPORTS > (cap SUSPICIOUS if challenged) > KNOWN_SCAM > SUSPICIOUS
    (T3 implements)
    """
    raise NotImplementedError("T3")


def mask_display_value(identifier_type: str, canonical_value: str) -> str:
    """
    Return masked display value per docs/03 masking rules.
    (T3 implements)
    """
    raise NotImplementedError("T3")

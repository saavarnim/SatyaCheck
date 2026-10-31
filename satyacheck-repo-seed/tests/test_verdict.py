"""tests/test_verdict.py – Pure unit tests for verdict ordering and masking (T3b)."""
import pytest

from app.trust import IndicatorTrust
from app.verdict import (
    verdict,
    mask_display_value,
    resolve_display_value,
)


def _make_trust(cohort_count: int, score: float) -> IndicatorTrust:
    return IndicatorTrust(cohort_count=cohort_count, score=score, units=[])


# ===================================================================
# 1. Verdict Precedence Tests
# ===================================================================

def test_verified_business_always_wins():
    """Verified business takes precedence over reports and active challenges."""
    # Even if 10 cohorts reported and active challenge exists
    t = _make_trust(cohort_count=10, score=10.0)
    assert verdict(t, is_verified=True, has_active_challenge=False) == "VERIFIED_BUSINESS"
    assert verdict(t, is_verified=True, has_active_challenge=True) == "VERIFIED_BUSINESS"


def test_no_reports_when_zero_cohorts():
    """Zero cohorts gives NO_REPORTS (when unverified)."""
    t = _make_trust(cohort_count=0, score=0.0)
    assert verdict(t, is_verified=False, has_active_challenge=False) == "NO_REPORTS"
    assert verdict(None, is_verified=False, has_active_challenge=False) == "NO_REPORTS"


def test_active_challenge_caps_verdict_at_suspicious():
    """An active challenge caps the verdict at SUSPICIOUS even if KNOWN_SCAM threshold is met."""
    t = _make_trust(cohort_count=5, score=5.0)
    # Without challenge -> KNOWN_SCAM
    assert verdict(t, is_verified=False, has_active_challenge=False) == "KNOWN_SCAM"
    # With challenge -> capped at SUSPICIOUS
    assert verdict(t, is_verified=False, has_active_challenge=True) == "SUSPICIOUS"


def test_known_scam_threshold():
    """cohort_count >= 3 AND score >= 2.5 gives KNOWN_SCAM."""
    # Meets both: 3 cohorts, score 2.5
    t1 = _make_trust(cohort_count=3, score=2.5)
    assert verdict(t1, is_verified=False, has_active_challenge=False) == "KNOWN_SCAM"

    # Meets both: 3 cohorts, score 2.7
    t2 = _make_trust(cohort_count=3, score=2.7)
    assert verdict(t2, is_verified=False, has_active_challenge=False) == "KNOWN_SCAM"

    # Meets both: 5 cohorts, score 4.8
    t3 = _make_trust(cohort_count=5, score=4.8)
    assert verdict(t3, is_verified=False, has_active_challenge=False) == "KNOWN_SCAM"


def test_suspicious_below_threshold():
    """Less than 3 cohorts or score below 2.5 gives SUSPICIOUS."""
    # 1 cohort
    t1 = _make_trust(cohort_count=1, score=1.0)
    assert verdict(t1, is_verified=False, has_active_challenge=False) == "SUSPICIOUS"

    # 2 cohorts
    t2 = _make_trust(cohort_count=2, score=2.0)
    assert verdict(t2, is_verified=False, has_active_challenge=False) == "SUSPICIOUS"

    # 3 cohorts but score < 2.5
    t3 = _make_trust(cohort_count=3, score=2.4)
    assert verdict(t3, is_verified=False, has_active_challenge=False) == "SUSPICIOUS"


# ===================================================================
# 2. Masking Format Tests (4 Types)
# ===================================================================

def test_mask_phone_formats():
    """Phone masking: 10-digit national number -> 2 digits + XXXXX + 3 digits; 4-digit -> 1XX0."""
    # 10-digit standard with +91
    assert mask_display_value("phone", "+919876543210") == "98XXXXX210"
    # 10-digit without prefix
    assert mask_display_value("phone", "9876543210") == "98XXXXX210"
    # 4-digit short code (e.g. 1930)
    assert mask_display_value("phone", "1930") == "1XX0"


def test_mask_upi():
    """UPI masking: first char + ***@ + handle."""
    assert mask_display_value("upi", "ramesh@okaxis") == "r***@okaxis"
    assert mask_display_value("upi", "scammer.fraud@paytm") == "s***@paytm"


def test_mask_url():
    """URL masking: first 3 chars of host + *** + rest of TLD + /..."""
    assert mask_display_value("url", "https://sbi-fake.in/verify") == "sbi***.in/..."
    assert mask_display_value("url", "sbi-fake.in/login") == "sbi***.in/..."
    assert mask_display_value("url", "https://fakebank.co.in/portal") == "fak***.co.in/..."


def test_mask_sender_id():
    """SMS sender ID masking: first 2 chars + ****."""
    assert mask_display_value("sender_id", "HDFCBK") == "HD****"
    assert mask_display_value("sender_id", "SBIINB") == "SB****"


# ===================================================================
# 3. Unmasking Threshold Tests (1, 2, 3 Cohorts)
# ===================================================================

def test_unmasking_by_cohort_count():
    """Masked for 1 and 2 cohorts; unmasked for >= 3 cohorts or when verified."""
    phone = "+919876543210"

    # 0 cohorts, unverified -> masked
    assert resolve_display_value("phone", phone, cohort_count=0, is_verified=False) == "98XXXXX210"

    # 1 cohort, unverified -> masked
    assert resolve_display_value("phone", phone, cohort_count=1, is_verified=False) == "98XXXXX210"

    # 2 cohorts, unverified -> masked
    assert resolve_display_value("phone", phone, cohort_count=2, is_verified=False) == "98XXXXX210"

    # 3 cohorts, unverified -> UNMASKED
    assert resolve_display_value("phone", phone, cohort_count=3, is_verified=False) == "+919876543210"

    # 4 cohorts, unverified -> UNMASKED
    assert resolve_display_value("phone", phone, cohort_count=4, is_verified=False) == "+919876543210"

    # Verified -> ALWAYS UNMASKED even with 0 cohorts
    assert resolve_display_value("phone", phone, cohort_count=0, is_verified=True) == "+919876543210"

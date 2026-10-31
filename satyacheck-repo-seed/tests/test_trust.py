"""tests/test_trust.py – Pure unit tests for the trust engine (T3a)."""
from datetime import datetime, timezone, timedelta
import pytest

from app.trust import (
    EventRow,
    TrustedUnit,
    compute_indicator_trust,
    jaccard_similarity,
    clean_note_for_similarity,
)


def _dt(hours_offset: int = 0) -> datetime:
    return datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=hours_offset)


def test_empty_events_gives_zero_trust():
    trust = compute_indicator_trust([])
    assert trust.cohort_count == 0
    assert trust.score == 0.0
    assert trust.units == []


def test_single_reporter_multiple_reports_is_one_voice():
    """One reporter submitting 6 reports produces exactly 1 voice and 1 cohort."""
    events = [
        EventRow(
            indicator_id=1,
            occurred_at=_dt(i),
            reporter_token="rep_alice",
            ip_token=f"ip_{i}",
            pincode="560102",
            scam_type="loan",
            channel="call",
            note="short note" if i < 5 else "this is a very long note for report",
        )
        for i in range(6)
    ]

    trust = compute_indicator_trust(events)
    assert trust.cohort_count == 1
    # One long note exists -> weight 1.0
    assert trust.score == 1.0
    assert len(trust.units) == 1
    # Earliest event is from i=0
    assert trust.units[0].occurred_at == _dt(0)


def test_same_ip_prefix_merges_into_one_cohort():
    """22 different reporters on the same IP prefix merge into 1 single cohort."""
    events = [
        EventRow(
            indicator_id=1,
            occurred_at=_dt(i),
            reporter_token=f"rep_bot_{i}",
            ip_token="shared_network_prefix_token",
            pincode="560102",
            scam_type="investment",
            channel="sms",
            note="fake report",
        )
        for i in range(22)
    ]

    trust = compute_indicator_trust(events)
    assert trust.cohort_count == 1
    assert len(trust.units) == 1
    # Notes are short (< 15 chars) -> weight 0.9
    assert trust.score == 0.9


def test_copy_pasted_notes_merge_into_one_cohort():
    """Different reporters and IPs with >= 80% 3-gram note similarity merge into 1 cohort."""
    note1 = "Urgent: electricity will be disconnected tonight pay now at link"
    note2 = "Urgent: electricity will be disconnected tonight pay now at link!"  # near identical

    events = [
        EventRow(
            indicator_id=1,
            occurred_at=_dt(0),
            reporter_token="rep_1",
            ip_token="ip_net_1",
            pincode="560102",
            scam_type="electricity",
            channel="sms",
            note=note1,
        ),
        EventRow(
            indicator_id=1,
            occurred_at=_dt(1),
            reporter_token="rep_2",
            ip_token="ip_net_2",
            pincode="560102",
            scam_type="electricity",
            channel="sms",
            note=note2,
        ),
    ]

    sim = jaccard_similarity(note1, note2)
    assert sim >= 0.80

    trust = compute_indicator_trust(events)
    assert trust.cohort_count == 1
    assert trust.score == 1.0
    assert len(trust.units) == 1


def test_independent_reporters_produce_independent_cohorts():
    """3 reporters on 3 different IPs with different notes form 3 cohorts."""
    events = [
        EventRow(
            indicator_id=1,
            occurred_at=_dt(0),
            reporter_token="rep_1",
            ip_token="ip_1",
            pincode="560102",
            scam_type="kyc",
            channel="call",
            note="Bank manager asked for my Aadhaar and OTP on phone",
        ),
        EventRow(
            indicator_id=1,
            occurred_at=_dt(1),
            reporter_token="rep_2",
            ip_token="ip_2",
            pincode="560038",
            scam_type="kyc",
            channel="sms",
            note="Received a fraudulent SMS claiming my SIM card will expire",
        ),
        EventRow(
            indicator_id=1,
            occurred_at=_dt(2),
            reporter_token="rep_3",
            ip_token="ip_3",
            pincode="560034",
            scam_type="kyc",
            channel="whatsapp",
            note="WhatsApp message demanding payment for KYC renewal immediately",
        ),
    ]

    trust = compute_indicator_trust(events)
    assert trust.cohort_count == 3
    assert trust.score == 3.0  # 3 x 1.0
    assert len(trust.units) == 3


def test_cohort_weight_calculation():
    """Cohorts with note < 15 chars weigh 0.9; >= 15 chars weigh 1.0."""
    events = [
        # Cohort 1: short note (< 15 chars)
        EventRow(
            indicator_id=1,
            occurred_at=_dt(0),
            reporter_token="rep_short",
            ip_token="ip_alpha",
            pincode="560102",
            scam_type="other",
            channel="call",
            note="fraud call",
        ),
        # Cohort 2: long note (>= 15 chars)
        EventRow(
            indicator_id=1,
            occurred_at=_dt(1),
            reporter_token="rep_long",
            ip_token="ip_beta",
            pincode="560102",
            scam_type="other",
            channel="call",
            note="They claimed my package has customs violations and demanded payment",
        ),
    ]

    trust = compute_indicator_trust(events)
    assert trust.cohort_count == 2
    assert trust.score == 1.9  # 0.9 + 1.0
    assert len(trust.units) == 2


def test_jaccard_similarity_multilingual():
    """Character 3-gram similarity works for Hindi / Hinglish text."""
    hindi1 = "तुरंत बिजली बिल भरें अन्यथा कनेक्शन काट दिया जाएगा"
    hindi2 = "तुरंत बिजली बिल भरें अन्यथा कनेक्शन काट दिया जाएगा।"
    assert jaccard_similarity(hindi1, hindi2) >= 0.80

    diff_hindi = "कस्टम्स विभाग में आपका पार्सल पकड़ा गया है"
    assert jaccard_similarity(hindi1, diff_hindi) < 0.30

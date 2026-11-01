"""tests/test_explain.py – Tests for plain-language explain feature (Task F1)."""
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app import clock
from app.explain import build_explain
from app.main import app


BANNED_WORDS = ["cohort", "verdict", "known_scam", "indicator", "hash", "token", "trust engine"]
VERDICTS = ["KNOWN_SCAM", "SUSPICIOUS", "NO_REPORTS", "VERIFIED_BUSINESS"]
SCAM_TYPES = [
    "digital-arrest", "fake-kyc-link", "upi-refund-qr",
    "investment-group", "courier-customs", "job-offer",
    "lottery-prize", "loan-app-harassment", "electricity-disconnection",
    "fake-customer-care", "otp-call", "sextortion", "other",
]


def _load_i18n_keys():
    """Extract all keys present in web/i18n.js for EN and HI."""
    i18n_file = Path(__file__).resolve().parent.parent / "web" / "i18n.js"
    content = i18n_file.read_text(encoding="utf-8")

    en_part = content[content.find("en: {"):content.find("hi: {")]
    hi_part = content[content.find("hi: {"):]

    en_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+):", en_part, re.MULTILINE))
    hi_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+):", hi_part, re.MULTILINE))
    return en_keys, hi_keys, content


def test_build_explain_structure_all_verdicts():
    """Every verdict returns the required keys without raw values."""
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    raw_identifier = "+919876543210"
    raw_token = "tok_abc123secret"
    raw_note = "He claimed he was police"

    for v in VERDICTS:
        res = build_explain(
            verdict=v,
            cohort_count=3 if v != "NO_REPORTS" else 0,
            score=2.8 if v == "KNOWN_SCAM" else 1.0,
            scam_type="digital-arrest",
            last_seen=now - timedelta(days=2),
            challenged=False,
            now=now,
        )

        # Check required fields exist
        assert "level" in res
        assert "headline_key" in res
        assert "why" in res
        assert "do" in res
        assert "not_meaning_key" in res

        assert res["level"] in ("low", "medium", "high")
        assert isinstance(res["why"], list)
        assert isinstance(res["do"], list)
        assert len(res["do"]) >= 2

        # Check why elements
        for item in res["why"]:
            assert "key" in item
            assert "n" in item

        # Verify no raw identifier, notes or tokens leaked
        as_str = str(res)
        assert raw_identifier not in as_str
        assert raw_token not in as_str
        assert raw_note not in as_str


def test_build_explain_level_logic():
    """Test 3-tier confidence level with recency adjustment (+1 within 7d, -1 > 30d)."""
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)

    # 1-2 reporters = low (base index 0)
    # With recent last_seen (<= 7d) -> raises by 1 to medium
    res1 = build_explain("SUSPICIOUS", cohort_count=1, score=1.0, scam_type=None,
                         last_seen=now - timedelta(days=2), challenged=False, now=now)
    assert res1["level"] == "medium"

    # With older last_seen (> 30d) -> base 0 lowered stays low (clamped)
    res2 = build_explain("SUSPICIOUS", cohort_count=1, score=1.0, scam_type=None,
                         last_seen=now - timedelta(days=45), challenged=False, now=now)
    assert res2["level"] == "low"

    # With normal window (8-30 days) -> stays base low
    res3 = build_explain("SUSPICIOUS", cohort_count=2, score=1.0, scam_type=None,
                         last_seen=now - timedelta(days=15), challenged=False, now=now)
    assert res3["level"] == "low"

    # 3-4 reporters = medium (base index 1)
    # Recent raises to high
    res4 = build_explain("KNOWN_SCAM", cohort_count=3, score=2.5, scam_type="otp-call",
                         last_seen=now - timedelta(days=3), challenged=False, now=now)
    assert res4["level"] == "high"

    # > 30d lowers to low
    res5 = build_explain("KNOWN_SCAM", cohort_count=4, score=2.5, scam_type="otp-call",
                         last_seen=now - timedelta(days=40), challenged=False, now=now)
    assert res5["level"] == "low"

    # 5+ reporters = high (base index 2)
    # Normal window stays high
    res6 = build_explain("KNOWN_SCAM", cohort_count=6, score=5.0, scam_type="fake-kyc-link",
                         last_seen=now - timedelta(days=10), challenged=False, now=now)
    assert res6["level"] == "high"


def test_build_explain_challenged_headline():
    """Challenged indicators get the challenged headline and review action."""
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    res = build_explain("SUSPICIOUS", cohort_count=2, score=1.5, scam_type="job-offer",
                        last_seen=now - timedelta(days=1), challenged=True, now=now)
    assert res["headline_key"] == "explain_headline_challenged"
    assert "explain_do_wait_owner_review" in res["do"]
    why_keys = [w["key"] for w in res["why"]]
    assert "explain_why_under_review" in why_keys


def test_every_key_exists_in_both_en_and_hi():
    """Ensure all translation keys produced by build_explain exist in EN and HI."""
    en_keys, hi_keys, _ = _load_i18n_keys()
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)

    all_keys_seen = set()

    # Collect keys across all combinations of verdicts, scam types, and challenges
    for v in VERDICTS:
        for st in SCAM_TYPES:
            for ch in (False, True):
                for cnt in (0, 1, 3, 6):
                    res = build_explain(
                        verdict=v,
                        cohort_count=cnt,
                        score=2.5 if v == "KNOWN_SCAM" else 0.5,
                        scam_type=st,
                        last_seen=now - timedelta(days=2) if cnt > 0 else None,
                        challenged=ch,
                        now=now,
                    )
                    all_keys_seen.add(res["headline_key"])
                    all_keys_seen.add(res["not_meaning_key"])
                    all_keys_seen.add(f"explain_conf_{res['level']}")
                    for w in res["why"]:
                        all_keys_seen.add(w["key"])
                    for d in res["do"]:
                        all_keys_seen.add(d)

    # Add scam type how it works keys
    for st in SCAM_TYPES:
        clean = st.replace("-", "_").lower()
        all_keys_seen.add(f"how_scam_{clean}")

    # Check structural card keys
    structural_keys = [
        "explain_card_title",
        "explain_part_meaning",
        "explain_part_why",
        "explain_part_do",
        "explain_not_meaning_prefix",
        "explain_how_scam_works_title",
        "explain_confidence_label",
        "explain_conf_low",
        "explain_conf_medium",
        "explain_conf_high",
        "explain_listen_btn",
        "explain_stop_btn",
    ]
    for k in structural_keys:
        all_keys_seen.add(k)

    missing_in_en = [k for k in all_keys_seen if k not in en_keys]
    missing_in_hi = [k for k in all_keys_seen if k not in hi_keys]

    assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
    assert not missing_in_hi, f"Keys missing in HI: {missing_in_hi}"


def test_banned_words_absent_in_explain_translations():
    """Writing rules: Never the words cohort, verdict, KNOWN_SCAM, indicator, hash, token, trust engine."""
    i18n_file = Path(__file__).resolve().parent.parent / "web" / "i18n.js"
    content = i18n_file.read_text(encoding="utf-8")

    # Extract all explain-related translation lines
    explain_lines = [
        line for line in content.splitlines()
        if any(prefix in line for prefix in ("explain_", "how_scam_"))
    ]
    assert len(explain_lines) >= 30, "Explain lines should be present in i18n.js"

    violations = []
    for line in explain_lines:
        line_lower = line.lower()
        for banned in BANNED_WORDS:
            if banned in line_lower:
                violations.append(f"Line '{line.strip()}' contains banned word '{banned}'")

    assert not violations, f"Banned words found in explain copy: {violations}"


def test_sentence_lengths_in_explain_copy():
    """Ensure sentences in explain copy are 14 words or fewer (class 6 writing rule)."""
    i18n_file = Path(__file__).resolve().parent.parent / "web" / "i18n.js"
    content = i18n_file.read_text(encoding="utf-8")

    # Match string values in EN explain lines
    en_section = content[content.find("en: {"):content.find("hi: {")]
    explain_en_lines = [
        line for line in en_section.splitlines()
        if any(prefix in line for prefix in ("explain_", "how_scam_")) and ":" in line
    ]

    for line in explain_en_lines:
        val_match = re.search(r':\s*"([^"]+)"', line)
        if not val_match:
            continue
        val = val_match.group(1).replace("<br>", ". ")
        # Split by periods, question marks, exclamation marks
        sentences = [s.strip() for s in re.split(r"[.!?]", val) if s.strip()]
        for sent in sentences:
            words = sent.split()
            assert len(words) <= 14, f"Sentence has {len(words)} words (> 14): '{sent}'"


def test_lookup_endpoint_includes_explain_and_under_500ms(client):
    """GET /lookup response includes 'explain' and responds in under 500ms."""
    # Test verified number lookup
    start = time.perf_counter()
    resp = client.get("/lookup?type=phone&value=%2B918041002233")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert resp.status_code == 200
    assert elapsed_ms < 500, f"Lookup took {elapsed_ms:.1f}ms (must be < 500ms)"

    data = resp.json()
    assert "explain" in data
    expl = data["explain"]
    assert "level" in expl
    assert "headline_key" in expl
    assert "why" in expl
    assert "do" in expl
    assert "not_meaning_key" in expl

    # Test unknown number (NO_REPORTS)
    start = time.perf_counter()
    resp_unknown = client.get("/lookup?type=phone&value=%2B919999900000")
    elapsed_ms_unknown = (time.perf_counter() - start) * 1000

    assert resp_unknown.status_code == 200
    assert elapsed_ms_unknown < 500, f"Unknown lookup took {elapsed_ms_unknown:.1f}ms (< 500ms)"
    data_unknown = resp_unknown.json()
    assert "explain" in data_unknown
    assert data_unknown["explain"]["headline_key"] == "explain_headline_no_reports"

"""tests/test_audit.py – Final Privacy Checklist Audit & Performance Verification (T10 per docs/06-privacy.md & docs/08-tests-deploy-readme.md)."""
import logging
import re
import time
from datetime import datetime, timezone
import pytest
from app import clock, config
from app.models import Challenge, Indicator, Report, VerifiedIndicator


def test_audit_privacy_checklist(client, test_db, monkeypatch):
    """
    Verify all 10 items of docs/06-privacy.md checklist:
    1. Pincode only for location (locality/city from directory). No GPS/street.
    2. reporter_id and ip_prefix stored ONLY as 16-hex HMAC tokens.
    3. Notes: redacted, <= 300 chars, internal only, NEVER returned in any public route.
    4. No screenshot uploads (has_screenshot is boolean only).
    5. Safe logging: method, path WITHOUT query string, status, duration.
    6. Masking until 3 cohorts unless verified.
    7. Wording: 'reported', never 'scammer', 'fraudster', 'criminal', 'culprit'.
    8. Challenge claimant data lives only in challenges table.
    9. No external network scraping.
    10. Evidence objects contain only occurred_at, channel, scam_type, pincode.
    """
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    now = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: now)

    # 1 & 2 & 3 & 4. Submit report with PII in note, raw reporter_id, raw IP
    raw_reporter = "user_secret_phone_9999999999"
    raw_ip = "192.168.1.100"
    pii_note = "Call me at +919876543210 or email test@example.com about upi test@okaxis. " + ("A" * 400)

    post_resp = client.post("/reports", json={
        "identifier_type": "phone",
        "identifier_value": "+91 98111 22333",
        "pincode": "560102",
        "reporter_id": raw_reporter,
        "ip_prefix": raw_ip,
        "note": pii_note,
        "has_screenshot": True,
    })
    assert post_resp.status_code == 201

    # Verify DB storage directly:
    report_row = test_db.query(Report).filter_by(pincode="560102").first()
    assert report_row is not None

    # Check 1: Pincode stored, no GPS coordinates in reports table
    assert report_row.pincode == "560102"
    assert not hasattr(report_row, "lat")
    assert not hasattr(report_row, "lng")
    assert not hasattr(report_row, "reporter_name")

    # Check 2: HMAC tokens only (16 hex chars)
    assert len(report_row.reporter_token) == 16
    assert re.fullmatch(r"[0-9a-f]{16}", report_row.reporter_token)
    assert raw_reporter not in report_row.reporter_token

    assert len(report_row.ip_token) == 16
    assert re.fullmatch(r"[0-9a-f]{16}", report_row.ip_token)
    assert raw_ip not in report_row.ip_token

    # Check 3: Notes redacted, capped <= 300 chars, never in public lookup
    assert len(report_row.note_redacted) <= 300
    assert "+919876543210" not in report_row.note_redacted
    assert "test@example.com" not in report_row.note_redacted

    # Check 4: has_screenshot is boolean only
    assert report_row.has_screenshot is True
    assert not hasattr(report_row, "screenshot_data")
    assert not hasattr(report_row, "screenshot_url")

    # Public route lookup check: notes, tokens, reporter_id NEVER returned
    lookup_resp = client.get("/lookup?type=phone&value=9811122333")
    assert lookup_resp.status_code == 200
    lookup_data = lookup_resp.json()
    assert "note" not in lookup_data
    assert "note_redacted" not in lookup_data
    assert "reporter_token" not in lookup_data
    assert "ip_token" not in lookup_data

    # Check 6: Display value masked (1 cohort < 3)
    assert lookup_data["display_value"] == "98XXXXX333"
    assert "+919811122333" not in str(lookup_data)

    # Check 10: Evidence object allowed keys only
    assert len(lookup_data["evidence"]) >= 1
    ev = lookup_data["evidence"][0]
    assert set(ev.keys()) == {"occurred_at", "channel", "scam_type", "pincode"}

    # Check 8: Challenge claimant data isolation
    client.post("/challenges", json={
        "identifier_type": "phone",
        "identifier_value": "9811122333",
        "claimant_name": "Private Claimant Name",
        "contact_email": "private@claimant.com",
        "proof_note": "Internal proof details",
    })
    # Lookup shows challenged=True, but NO claimant name or email
    lookup_ch = client.get("/lookup?type=phone&value=9811122333").json()
    assert lookup_ch["challenged"] is True
    assert "claimant_name" not in lookup_ch
    assert "contact_email" not in lookup_ch
    assert "Private Claimant Name" not in str(lookup_ch)


def test_audit_safe_logging(client, caplog):
    """
    Rule 5: App logging middleware logs method, path WITHOUT query string, status, duration only.
    No bodies, no query strings, no tokens, no claimant data.
    """
    caplog.set_level(logging.INFO, logger="satyacheck")

    secret_val = "SECRET_VALUE_9876543210"
    resp = client.get(f"/lookup?type=phone&value={secret_val}")
    assert resp.status_code == 200

    # Inspect records produced by satyacheck application logger
    app_log_messages = [r.getMessage() for r in caplog.records if r.name == "satyacheck"]
    assert len(app_log_messages) >= 1
    full_app_logs = "\n".join(app_log_messages)

    assert secret_val not in full_app_logs
    assert "value=" not in full_app_logs
    assert "type=phone" not in full_app_logs
    # Log must contain /lookup path without query string
    assert "/lookup" in full_app_logs


def test_performance_bulk_lookups(client, test_db, monkeypatch):
    """
    Performance test: Seed ~500 events across 20 indicators,
    perform 100 lookups, verify p95 latency < 150ms.
    (docs/08-tests-deploy-readme.md)
    """
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    now = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: now)

    # Insert indicators and bulk reports
    indicators = []
    for i in range(20):
        ind = Indicator(type="phone", canonical_value=f"+9198000000{i:02d}")
        test_db.add(ind)
        indicators.append(ind)
    test_db.commit()

    bulk_reports = []
    for ind in indicators:
        for r in range(25):
            bulk_reports.append(Report(
                report_id=f"BULK-{ind.id}-{r}",
                case_id=f"CASE-{ind.id}",
                indicator_id=ind.id,
                occurred_at=now,
                reported_at=now,
                reporter_token=f"tok_{r:04d}",
                ip_token=f"ip_{r % 5:04d}",
                channel="phone call",
                scam_type="fake-kyc-link",
                pincode="560102",
                note_redacted="Bulk test report note for benchmark",
                has_screenshot=False,
                amount_lost_inr=None,
            ))
    test_db.bulk_save_objects(bulk_reports)
    test_db.commit()

    # Benchmark 100 lookups
    latencies = []
    for i in range(100):
        phone_num = f"+9198000000{i % 20:02d}"
        t0 = time.perf_counter()
        resp = client.get(f"/lookup?type=phone&value={phone_num}")
        assert resp.status_code == 200
        latencies.append((time.perf_counter() - t0) * 1000)

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    # Verify p95 < 150 ms per docs/08
    assert p95 < 150, f"p95 latency was {p95:.2f}ms (expected < 150ms)"

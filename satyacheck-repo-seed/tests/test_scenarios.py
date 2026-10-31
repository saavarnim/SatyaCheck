"""tests/test_scenarios.py – Integration scenarios for trust and verdict (T3d / docs/03)."""
import pytest


def test_22_accounts_on_one_prefix_is_one_cohort(client, monkeypatch):
    """22 fake accounts reporting from one IP prefix group into 1 cohort:

    verdict remains SUSPICIOUS, display_value remains masked, only 1 TrustedUnit.
    """
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    shared_prefix = "198.51.100.0/24"
    phone_val = "9876543210"

    for i in range(22):
        resp = client.post("/reports", json={
            "report_id": f"REP-BOT-{i}",
            "identifier_type": "phone",
            "identifier_value": phone_val,
            "pincode": "560102",
            "reporter_id": f"fake_user_{i}",
            "ip_prefix": shared_prefix,
            "channel": "phone call",
            "scam_type": "fake-kyc-link",
            "note": f"fraudulent activity reported by account {i}",
        })
        assert resp.status_code == 201

    lookup_resp = client.get(f"/lookup?type=phone&value={phone_val}")
    assert lookup_resp.status_code == 200
    data = lookup_resp.json()

    # Raw stored report count is 22, but independent cohort count is strictly 1
    assert data["report_count"] == 22
    assert data["distinct_reporters"] == 1
    # Does NOT reach KNOWN_SCAM threshold
    assert data["verdict"] == "SUSPICIOUS"
    # Remains masked because distinct_reporters < 3
    assert data["display_value"] == "98XXXXX210"
    # Only 1 TrustedUnit produced for map/alerts/evidence
    assert len(data["evidence"]) == 1


def test_three_independent_reporters_unmask_and_reach_known_scam(client, monkeypatch):
    """3 independent reporters on different networks with distinct notes

    produce 3 cohorts, reaching KNOWN_SCAM and unmasking the display_value.
    """
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    phone_val = "9812345678"

    reports_data = [
        ("rep_alice", "10.1.0.0/24", "They called claiming to be from my bank asking for an OTP"),
        ("rep_bob", "10.2.0.0/24", "Suspicious caller demanding money for courier release fee"),
        ("rep_carol", "10.3.0.0/24", "Received threatening WhatsApp call about loan repayment"),
    ]

    for i, (rep_id, ip_net, note_text) in enumerate(reports_data):
        resp = client.post("/reports", json={
            "report_id": f"REP-IND-{i}",
            "identifier_type": "phone",
            "identifier_value": phone_val,
            "pincode": "560102",
            "reporter_id": rep_id,
            "ip_prefix": ip_net,
            "channel": "phone call",
            "scam_type": "fake-customer-care",
            "note": note_text,
        })
        assert resp.status_code == 201

    lookup_resp = client.get(f"/lookup?type=phone&value={phone_val}")
    assert lookup_resp.status_code == 200
    data = lookup_resp.json()

    assert data["report_count"] == 3
    assert data["distinct_reporters"] == 3
    # Meets threshold (>= 3 cohorts and score >= 2.5) -> KNOWN_SCAM
    assert data["verdict"] == "KNOWN_SCAM"
    # Unmasked because distinct_reporters >= 3
    assert data["display_value"] == "+919812345678"
    assert len(data["evidence"]) == 3


def test_one_reporter_six_reports_is_one_voice(client, monkeypatch):
    """1 reporter reporting 6 times contributes only 1 voice and cohort."""
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    phone_val = "9823456789"

    for i in range(6):
        resp = client.post("/reports", json={
            "report_id": f"REP-SINGLE-{i}",
            "identifier_type": "phone",
            "identifier_value": phone_val,
            "pincode": "560102",
            "reporter_id": "single_reporter",
            "ip_prefix": f"10.0.{i}.0/24",
            "channel": "phone call",
            "scam_type": "digital-arrest",
            "note": f"report number {i}",
        })
        assert resp.status_code == 201

    lookup_resp = client.get(f"/lookup?type=phone&value={phone_val}")
    assert lookup_resp.status_code == 200
    data = lookup_resp.json()

    assert data["report_count"] == 6
    assert data["distinct_reporters"] == 1
    assert data["verdict"] == "SUSPICIOUS"
    assert data["display_value"] == "98XXXXX789"

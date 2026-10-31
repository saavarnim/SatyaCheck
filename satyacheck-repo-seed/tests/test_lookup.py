"""tests/test_lookup.py – Tests for GET /lookup (T2d)."""
import pytest
from app.models import Indicator, Report


def test_invalid_identifier_gives_400(client):
    """Invalid identifier (e.g. 12345 for phone) must return 400."""
    resp = client.get("/lookup?type=phone&value=12345")
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}


def test_missing_params_gives_400(client):
    """Missing type or value must return 400."""
    resp = client.get("/lookup?type=phone")
    assert resp.status_code == 400
    resp2 = client.get("/lookup?value=9876543210")
    assert resp2.status_code == 400


def test_unreported_valid_gives_200_no_reports(client):
    """Unreported valid indicator must return 200 with NO_REPORTS (never 404) and masked display_value."""
    resp = client.get("/lookup?type=phone&value=9876543210")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] == "NO_REPORTS"
    assert data["report_count"] == 0
    assert data["distinct_reporters"] == 0
    assert data["first_seen"] is None
    assert data["last_seen"] is None
    assert data["challenged"] is False
    assert data["evidence"] == []
    # Masked: 98XXXXX210
    assert data["display_value"] == "98XXXXX210"


def test_1930_gives_verified_business(client):
    """1930 is in seed verified.json -> returns VERIFIED_BUSINESS and unmasked display_value."""
    resp = client.get("/lookup?type=phone&value=1930")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] == "VERIFIED_BUSINESS"
    assert data["display_value"] == "1930"


def test_reported_indicator_lookup_and_evidence(client):
    """After posting a report, lookup returns report_count 1, SUSPICIOUS verdict, and IST timestamp."""
    post_resp = client.post("/reports", json={
        "identifier_type": "upi",
        "identifier_value": "scammer@okaxis",
        "pincode": "560102",
        "channel": "sms or whatsapp",
        "scam_type": "fake-kyc-link",
    })
    assert post_resp.status_code == 201

    lookup_resp = client.get("/lookup?type=upi&value=scammer@okaxis")
    assert lookup_resp.status_code == 200
    data = lookup_resp.json()
    assert data["verdict"] == "SUSPICIOUS"
    assert data["report_count"] == 1
    assert data["distinct_reporters"] == 1
    assert data["scam_type"] == "fake-kyc-link"
    # Masked (only 1 cohort): s***@okaxis
    assert data["display_value"] == "s***@okaxis"
    assert len(data["evidence"]) == 1
    ev = data["evidence"][0]
    assert ev["channel"] == "sms or whatsapp"
    assert ev["scam_type"] == "fake-kyc-link"
    assert ev["pincode"] == "560102"
    assert "+05:30" in ev["occurred_at"]
    assert "+05:30" in data["first_seen"]
    assert "+05:30" in data["last_seen"]

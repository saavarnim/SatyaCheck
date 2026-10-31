"""tests/test_reports.py – Tests for POST /reports (T2c)."""
import pytest
from app.models import Indicator, Report


def test_invalid_phone_gives_400(client):
    """Invalid phone (e.g. 12345) must return 400."""
    payload = {
        "identifier_type": "phone",
        "identifier_value": "12345",
        "pincode": "560102",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}


def test_unknown_pincode_gives_400(client):
    """Pincode not in areas.json must return 400."""
    payload = {
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "pincode": "999999",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}


def test_invalid_type_gives_400(client):
    """Identifier type outside phone/upi/url/sender_id must return 400."""
    payload = {
        "identifier_type": "bitcoin",
        "identifier_value": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "pincode": "560102",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}


def test_four_phone_formats_make_one_indicator(client, test_db):
    """Four phone formats (+919876543210, 09876543210, 9876543210, 98765-43210)

    must all normalise to the same canonical indicator and share the same case_id.
    First report has merged=False; subsequent ones have merged=True.
    """
    formats = [
        "+919876543210",
        "09876543210",
        "9876543210",
        "98765-43210",
    ]

    case_ids = []
    for i, phone_val in enumerate(formats):
        payload = {
            "identifier_type": "phone",
            "identifier_value": phone_val,
            "pincode": "560102",
            "reporter_id": f"reporter_{i}",
            "ip_prefix": f"192.168.{i}.0/24",
        }
        resp = client.post("/reports", json=payload)
        assert resp.status_code == 201, f"Failed for {phone_val}: {resp.text}"
        data = resp.json()
        assert "report_id" in data
        assert "case_id" in data
        case_ids.append(data["case_id"])
        if i == 0:
            assert data["merged"] is False
        else:
            assert data["merged"] is True

    # All 4 reports have identical case_id
    assert len(set(case_ids)) == 1

    # Exactly one indicator row exists in DB
    indicators = test_db.query(Indicator).filter_by(type="phone").all()
    assert len(indicators) == 1
    assert indicators[0].canonical_value == "+919876543210"

    # Exactly 4 reports in DB pointing to that indicator
    reports = test_db.query(Report).filter_by(indicator_id=indicators[0].id).all()
    assert len(reports) == 4


def test_duplicate_report_id_returns_201_unchanged(client, test_db):
    """Submitting the same report_id returns 201 unchanged and stores no new rows."""
    payload = {
        "report_id": "REP-DUP-001",
        "identifier_type": "upi",
        "identifier_value": "scammer@okhdfcbank",
        "pincode": "560102",
    }
    resp1 = client.post("/reports", json=payload)
    assert resp1.status_code == 201
    data1 = resp1.json()

    # Second submission with same report_id
    resp2 = client.post("/reports", json=payload)
    assert resp2.status_code == 201
    data2 = resp2.json()

    assert data1["report_id"] == data2["report_id"]
    assert data1["case_id"] == data2["case_id"]

    # Only one report row was stored
    count = test_db.query(Report).filter_by(report_id="REP-DUP-001").count()
    assert count == 1


def test_normalise_channel_and_scam_type(client, test_db):
    """Unknown channel -> 'Something else'; unknown scam_type -> 'other'."""
    payload = {
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "pincode": "560102",
        "channel": "telepathy",
        "scam_type": "black_magic",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 201

    rep = test_db.query(Report).filter_by(report_id=resp.json()["report_id"]).first()
    assert rep is not None
    assert rep.channel == "Something else"
    assert rep.scam_type == "other"


def test_note_redaction_and_privacy(client, test_db):
    """Phone numbers and emails in report notes must be scrubbed."""
    payload = {
        "identifier_type": "url",
        "identifier_value": "https://sbi-fake-login.in/verify",
        "pincode": "560102",
        "note": "They told me to call 9876543210 or email test@gmail.com for refund",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 201

    rep = test_db.query(Report).filter_by(report_id=resp.json()["report_id"]).first()
    assert rep is not None
    assert "9876543210" not in rep.note_redacted
    assert "test@gmail.com" not in rep.note_redacted
    assert "[redacted]" in rep.note_redacted


def test_future_occurred_at_gives_400(client):
    """occurred_at far in the future must return 400."""
    payload = {
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "pincode": "560102",
        "occurred_at": "2099-01-01T00:00:00Z",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}


def test_rate_limiting_per_indicator_gives_429(client, monkeypatch):
    """Submitting more than 10 reports/hour for the same reporter and indicator returns 429 SLOW_DOWN."""
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    payload = {
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "pincode": "560102",
        "reporter_id": "spammer_user",
        "ip_prefix": "10.0.0.0/24",
    }

    # 10 submissions succeed
    for i in range(10):
        resp = client.post("/reports", json={**payload, "report_id": f"REP-RL-{i}"})
        assert resp.status_code == 201

    # 11th submission gets 429
    resp11 = client.post("/reports", json={**payload, "report_id": "REP-RL-11"})
    assert resp11.status_code == 429
    assert resp11.json() == {"error": "SLOW_DOWN"}

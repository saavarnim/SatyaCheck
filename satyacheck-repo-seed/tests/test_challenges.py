"""tests/test_challenges.py – Tests for challenges, admin resolution, and reset (T7)."""
from datetime import datetime, timedelta, timezone
import pytest
from app import clock, config
from app.models import Area, Challenge, Indicator, Report, VerifiedIndicator


def test_post_challenge_creates_and_marks_lookup(client):
    """Submitting a challenge creates an under_review challenge and sets challenged=True on lookup."""
    payload = {
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "claimant_name": "Apex Support",
        "contact_email": "ops@apex.in",
        "proof_note": "Official registered helpline",
    }
    resp = client.post("/challenges", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["challenge_id"].startswith("CH-")
    assert data["status"] == "under_review"

    # Verify lookup shows challenged=True
    l_resp = client.get("/lookup?type=phone&value=9876543210")
    assert l_resp.status_code == 200
    l_data = l_resp.json()
    assert l_data["challenged"] is True


def test_challenge_caps_verdict_at_suspicious(client, monkeypatch):
    """Active challenge caps verdict at SUSPICIOUS even if 3 cohorts corroborate KNOWN_SCAM."""
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    now = datetime(2026, 10, 31, 10, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: now)

    phone_val = "9812345678"
    distinct_notes = [
        "They called claiming to be from my bank asking for an OTP",
        "Suspicious caller demanding money for courier release fee",
        "Received threatening WhatsApp call about loan repayment",
    ]

    # 3 independent reports -> KNOWN_SCAM
    for i, note in enumerate(distinct_notes):
        r = client.post("/reports", json={
            "identifier_type": "phone",
            "identifier_value": phone_val,
            "pincode": "560102",
            "reporter_id": f"reporter_{i}",
            "ip_prefix": f"192.168.{i}.0/24",
            "note": note,
        })
        assert r.status_code == 201

    # Before challenge -> KNOWN_SCAM
    lookup_before = client.get(f"/lookup?type=phone&value={phone_val}").json()
    assert lookup_before["verdict"] == "KNOWN_SCAM"
    assert lookup_before["challenged"] is False

    # Submit challenge
    ch_resp = client.post("/challenges", json={
        "identifier_type": "phone",
        "identifier_value": phone_val,
        "claimant_name": "Apex Logistics",
        "contact_email": "ops@apex.in",
        "proof_note": "Helpline dispute",
    })
    assert ch_resp.status_code == 201

    # After challenge -> capped at SUSPICIOUS
    lookup_after = client.get(f"/lookup?type=phone&value={phone_val}").json()
    assert lookup_after["verdict"] == "SUSPICIOUS"
    assert lookup_after["challenged"] is True


def test_post_challenge_idempotent_if_under_review(client):
    """Submitting challenge while one is under review returns 201 with existing ID."""
    payload = {
        "identifier_type": "upi",
        "identifier_value": "shop@okaxis",
        "claimant_name": "Shop Owner",
        "contact_email": "owner@shop.com",
    }
    resp1 = client.post("/challenges", json=payload)
    assert resp1.status_code == 201
    ch_id1 = resp1.json()["challenge_id"]

    resp2 = client.post("/challenges", json=payload)
    assert resp2.status_code == 201
    assert resp2.json()["challenge_id"] == ch_id1
    assert resp2.json()["status"] == "under_review"


def test_admin_list_challenges_requires_token(client):
    """GET /admin/challenges requires valid X-Admin-Token."""
    # Missing token -> 403
    resp_no_token = client.get("/admin/challenges")
    assert resp_no_token.status_code == 403

    # Wrong token -> 403
    resp_bad_token = client.get("/admin/challenges", headers={"X-Admin-Token": "wrong"})
    assert resp_bad_token.status_code == 403

    # Submit a challenge first
    client.post("/challenges", json={
        "identifier_type": "url",
        "identifier_value": "https://secure-bank.example.com",
        "claimant_name": "Example Bank",
        "contact_email": "legal@example.com",
    })

    # Correct token -> 200
    resp_ok = client.get("/admin/challenges", headers={"X-Admin-Token": config.ADMIN_TOKEN})
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert "challenges" in data
    assert len(data["challenges"]) >= 1
    ch = data["challenges"][0]
    assert ch["claimant_name"] == "Example Bank"
    assert ch["status"] == "under_review"


def test_admin_resolve_upheld(client):
    """Upheld challenge marks status as upheld and adds to verified_indicators."""
    resp = client.post("/challenges", json={
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "claimant_name": "Verified Bakery",
        "contact_email": "bakery@local.com",
    })
    ch_id = resp.json()["challenge_id"]

    # Resolve as upheld
    res_resp = client.post(
        f"/admin/challenges/{ch_id}/resolve",
        headers={"X-Admin-Token": config.ADMIN_TOKEN},
        json={"decision": "upheld"},
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "upheld"

    # Lookup should now be VERIFIED_BUSINESS
    l_resp = client.get("/lookup?type=phone&value=9876543210")
    assert l_resp.status_code == 200
    assert l_resp.json()["verdict"] == "VERIFIED_BUSINESS"


def test_admin_resolve_rejected_and_cooldown(client, monkeypatch):
    """Rejected challenge blocks new challenges for 7 days (409 CHALLENGE_BLOCKED)."""
    t0 = datetime(2026, 10, 31, 10, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    resp = client.post("/challenges", json={
        "identifier_type": "upi",
        "identifier_value": "disputed@okaxis",
        "claimant_name": "Spam Entity",
        "contact_email": "spam@entity.com",
    })
    ch_id = resp.json()["challenge_id"]

    # Reject
    res_resp = client.post(
        f"/admin/challenges/{ch_id}/resolve",
        headers={"X-Admin-Token": config.ADMIN_TOKEN},
        json={"decision": "rejected"},
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "rejected"

    # New challenge within 7 days -> 409
    t_3d = t0 + timedelta(days=3)
    monkeypatch.setattr(clock, "now", lambda: t_3d)

    retry_resp = client.post("/challenges", json={
        "identifier_type": "upi",
        "identifier_value": "disputed@okaxis",
        "claimant_name": "Spam Entity",
        "contact_email": "spam@entity.com",
    })
    assert retry_resp.status_code == 409
    assert retry_resp.json() == {"error": "CHALLENGE_BLOCKED"}

    # After 8 days -> allowed again
    t_8d = t0 + timedelta(days=8)
    monkeypatch.setattr(clock, "now", lambda: t_8d)

    allow_resp = client.post("/challenges", json={
        "identifier_type": "upi",
        "identifier_value": "disputed@okaxis",
        "claimant_name": "Spam Entity 2",
        "contact_email": "spam2@entity.com",
    })
    assert allow_resp.status_code == 201


def test_admin_reset_flow(client, monkeypatch, test_db):
    """
    POST /admin/reset:
    - 403 if DEMO_MODE != true
    - 200 if DEMO_MODE == true, clearing reports, indicators, challenges, review verified
    - Keeps seed areas (25) and seed/demo verified indicators (19)
    """
    # 1. With DEMO_MODE=False -> 403
    monkeypatch.setattr("app.config.DEMO_MODE", False)
    resp_blocked = client.post("/admin/reset")
    assert resp_blocked.status_code == 403
    assert resp_blocked.json() == {"error": "DEMO_MODE_REQUIRED"}

    # 2. Add some state
    monkeypatch.setattr("app.config.DEMO_MODE", True)
    client.post("/reports", json={
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "pincode": "560102",
        "note": "Some note",
    })
    client.post("/challenges", json={
        "identifier_type": "phone",
        "identifier_value": "9876543210",
        "claimant_name": "Test",
        "contact_email": "test@test.com",
    })

    # Verify rows exist
    assert test_db.query(Report).count() >= 1
    assert test_db.query(Challenge).count() >= 1

    # 3. Call reset
    resp_reset = client.post("/admin/reset")
    assert resp_reset.status_code == 200
    assert resp_reset.json() == {"ok": True}

    # Verify cleared tables
    assert test_db.query(Report).count() == 0
    assert test_db.query(Challenge).count() == 0
    assert test_db.query(Indicator).count() == 0

    # Seeded areas and verified remain
    assert test_db.query(Area).count() == 25
    assert test_db.query(VerifiedIndicator).count() == 19


def test_admin_reviews_portal_auth(client):
    """Admin reviews portal requires valid authentication."""
    # JSON request with missing token -> 403 JSON
    r_json_no_auth = client.get("/admin/reviews", headers={"Accept": "application/json"})
    assert r_json_no_auth.status_code == 403
    assert r_json_no_auth.json() == {"error": "FORBIDDEN"}

    # Browser request with missing token -> 200 HTML with auth input form
    r_html_no_auth = client.get("/admin/reviews")
    assert r_html_no_auth.status_code == 200
    assert "Admin Review Portal" in r_html_no_auth.text
    assert "<form method=\"GET\" action=\"/admin/reviews\">" in r_html_no_auth.text

    # Browser request with invalid token -> 403 HTML with error note
    r_html_wrong = client.get("/admin/reviews?token=wrongtoken")
    assert r_html_wrong.status_code == 403
    assert "Invalid administrative token" in r_html_wrong.text


def test_admin_reviews_portal_json_and_html(client):
    """Admin reviews portal returns reviews data in JSON and HTML formats."""
    # Create challenge
    client.post("/challenges", json={
        "identifier_type": "phone",
        "identifier_value": "9123456789",
        "claimant_name": "Test Claimant Corp",
        "contact_email": "desk@claimant.com",
        "proof_note": "Legitimate enterprise customer care number.",
    })

    # Fetch JSON format
    resp_json = client.get(f"/admin/reviews?token={config.ADMIN_TOKEN}&format=json")
    assert resp_json.status_code == 200
    data = resp_json.json()
    assert "reviews" in data
    assert len(data["reviews"]) >= 1
    rev = data["reviews"][0]
    assert rev["claimant_name"] == "Test Claimant Corp"
    assert rev["contact_email"] == "desk@claimant.com"
    assert rev["proof_note"] == "Legitimate enterprise customer care number."
    assert rev["status"] == "under_review"

    # Fetch HTML dashboard
    resp_html = client.get(f"/admin/reviews?token={config.ADMIN_TOKEN}")
    assert resp_html.status_code == 200
    assert "SatyaCheck • Trust & Safety Review" in resp_html.text
    assert "Test Claimant Corp" in resp_html.text
    assert "desk@claimant.com" in resp_html.text
    assert "mailto:desk@claimant.com" in resp_html.text
    assert "Uphold" in resp_html.text
    assert "Reject" in resp_html.text


def test_admin_resolve_challenge_with_query_token(client):
    """Admin challenge resolution works seamlessly via query parameter token."""
    post_res = client.post("/challenges", json={
        "identifier_type": "phone",
        "identifier_value": "9988776655",
        "claimant_name": "Verified Org",
        "contact_email": "ops@verified.org",
        "proof_note": "Hospital emergency line.",
    })
    ch_id = post_res.json()["challenge_id"]

    # Resolve using ?token= query parameter without X-Admin-Token header
    resolve_res = client.post(
        f"/admin/challenges/{ch_id}/resolve?token={config.ADMIN_TOKEN}",
        json={"decision": "upheld"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json() == {"challenge_id": ch_id, "status": "upheld"}

    # Verify lookup reflects verified status
    lookup_res = client.get("/lookup?type=phone&value=9988776655")
    assert lookup_res.status_code == 200
    assert lookup_res.json()["verdict"] == "VERIFIED_BUSINESS"


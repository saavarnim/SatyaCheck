"""tests/test_map_alerts.py – Tests for GET /map and GET /alerts (T5 per docs/04-map-alerts.md)."""
from datetime import datetime, timedelta, timezone
import pytest
from app import clock, config
from app.trust import TrustedUnit


def test_map_defaults_and_clustering(client, monkeypatch):
    """Units within default 7 days are clustered by pincode with area details and severity."""
    t0 = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    fake_units = [
        TrustedUnit(1, t0 - timedelta(days=1), "560102", "fake-kyc-link", "sms"),
        TrustedUnit(2, t0 - timedelta(days=2), "560102", "fake-kyc-link", "call"),
        TrustedUnit(3, t0 - timedelta(days=3), "560102", "upi-refund-qr", "whatsapp"),
        TrustedUnit(4, t0 - timedelta(hours=10), "560034", "job-offer", "sms"),
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: fake_units)

    resp = client.get("/map")
    assert resp.status_code == 200
    data = resp.json()
    assert "clusters" in data
    clusters = {c["pincode"]: c for c in data["clusters"]}

    assert "560102" in clusters
    c_hsr = clusters["560102"]
    assert c_hsr["locality"] == "HSR Layout"
    assert c_hsr["city"] == "Bengaluru"
    assert c_hsr["count"] == 3
    assert c_hsr["top_scam_type"] == "fake-kyc-link"
    assert c_hsr["severity"] == "MED"
    assert c_hsr["lat"] == pytest.approx(12.9116)
    assert c_hsr["lng"] == pytest.approx(77.6473)

    assert "560034" in clusters
    c_kor = clusters["560034"]
    assert c_kor["locality"] == "Koramangala"
    assert c_kor["count"] == 1
    assert c_kor["top_scam_type"] == "job-offer"
    assert c_kor["severity"] == "MED"


def test_map_excludes_8_day_old_and_month_old_units(client, monkeypatch):
    """8-day-old and month-old units are excluded from default 7-day map."""
    t0 = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    fake_units = [
        TrustedUnit(1, t0 - timedelta(days=6), "560102", "fake-kyc-link", "sms"),   # in
        TrustedUnit(2, t0 - timedelta(days=8), "560102", "fake-kyc-link", "sms"),   # out
        TrustedUnit(3, t0 - timedelta(days=30), "560034", "job-offer", "sms"),      # out
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: fake_units)

    resp = client.get("/map")
    assert resp.status_code == 200
    clusters = resp.json()["clusters"]
    assert len(clusters) == 1
    assert clusters[0]["pincode"] == "560102"
    assert clusters[0]["count"] == 1


def test_map_radius_filter(client, monkeypatch):
    """Radius filter around pincode includes only areas within radius_km."""
    t0 = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    # HSR Layout (560102) and Koramangala (560034) are ~3.6 km apart
    fake_units = [
        TrustedUnit(1, t0 - timedelta(hours=2), "560102", "fake-kyc-link", "sms"),
        TrustedUnit(2, t0 - timedelta(hours=3), "560034", "job-offer", "call"),
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: fake_units)

    # 1. Radius 2 km around 560102 -> only 560102
    resp1 = client.get("/map?pincode=560102&radius_km=2.0")
    assert resp1.status_code == 200
    clusters1 = resp1.json()["clusters"]
    assert len(clusters1) == 1
    assert clusters1[0]["pincode"] == "560102"

    # 2. Radius 5 km around 560102 -> includes both 560102 and 560034
    resp2 = client.get("/map?pincode=560102&radius_km=5.0")
    assert resp2.status_code == 200
    pincodes2 = {c["pincode"] for c in resp2.json()["clusters"]}
    assert pincodes2 == {"560102", "560034"}


def test_map_severities(client, monkeypatch):
    """Verify severity levels: <5 MED, >=5 HIGH, >=10 CRIT."""
    t0 = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    fake_units = []
    # 10 units in 560102 -> CRIT
    for i in range(10):
        fake_units.append(TrustedUnit(i, t0 - timedelta(hours=i), "560102", "fake-kyc-link", "sms"))
    # 5 units in 560034 -> HIGH
    for i in range(5):
        fake_units.append(TrustedUnit(10 + i, t0 - timedelta(hours=i), "560034", "job-offer", "sms"))
    # 2 units in 560038 -> MED
    for i in range(2):
        fake_units.append(TrustedUnit(20 + i, t0 - timedelta(hours=i), "560038", "lottery-prize", "sms"))

    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: fake_units)

    resp = client.get("/map")
    assert resp.status_code == 200
    clusters = {c["pincode"]: c for c in resp.json()["clusters"]}
    assert clusters["560102"]["severity"] == "CRIT"
    assert clusters["560034"]["severity"] == "HIGH"
    assert clusters["560038"]["severity"] == "MED"


def test_map_invalid_params_return_400(client):
    """Invalid pincode, negative days or radius return 400 INVALID_REQUEST."""
    resp = client.get("/map?pincode=999999")
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}

    resp = client.get("/map?days=0")
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}

    resp = client.get("/map?radius_km=-1")
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}


def test_alerts_spike_thresholds(client, monkeypatch):
    """
    SPIKE alert fires if last24 >= 5 AND last24 >= 2 * baseline_per_day.
    - 4 units with baseline 0: does not fire (<5)
    - 5 units with baseline 0: fires
    - 5 units with baseline 2.0 (14 prior units / 7): fires (5 >= 4.0)
    - 5 units with baseline 3.0 (21 prior units / 7): does not fire (5 < 6.0)
    """
    t0 = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    # Case A: 4 units in last 24h -> no spike
    units_4 = [
        TrustedUnit(i, t0 - timedelta(hours=i + 1), "560102", "fake-kyc-link", "sms")
        for i in range(4)
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: units_4)
    resp = client.get("/alerts?pincode=560102")
    assert resp.status_code == 200
    assert resp.json()["alerts"] == []

    # Case B: 5 units in last 24h, 0 baseline -> SPIKE fires
    units_5 = [
        TrustedUnit(i, t0 - timedelta(hours=i + 1), "560102", "fake-kyc-link", "sms")
        for i in range(5)
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: units_5)
    resp = client.get("/alerts?pincode=560102")
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    assert len(alerts) == 1
    assert alerts[0] == {
        "type": "SPIKE",
        "pincode": "560102",
        "window": "24h",
        "count": 5,
        "baseline_per_day": 0.0,
    }

    # Case C: 5 units in last 24h, 14 units in [t0-24h-7d, t0-24h) -> baseline=2.0 -> 5 >= 4.0 -> fires
    baseline_14 = [
        TrustedUnit(100 + i, t0 - timedelta(hours=30 + i * 5), "560102", "fake-kyc-link", "sms")
        for i in range(14)
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: units_5 + baseline_14)
    resp = client.get("/alerts?pincode=560102")
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    spike = [a for a in alerts if a["type"] == "SPIKE"][0]
    assert spike["count"] == 5
    assert spike["baseline_per_day"] == 2.0

    # Case D: 5 units in last 24h, 21 units in baseline -> baseline=3.0 -> 5 < 6.0 -> no spike
    baseline_21 = [
        TrustedUnit(100 + i, t0 - timedelta(hours=30 + i * 3), "560102", "fake-kyc-link", "sms")
        for i in range(21)
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: units_5 + baseline_21)
    resp = client.get("/alerts?pincode=560102")
    assert resp.status_code == 200
    spikes = [a for a in resp.json()["alerts"] if a["type"] == "SPIKE"]
    assert len(spikes) == 0


def test_alerts_new_type(client, monkeypatch):
    """
    NEW_TYPE alert fires if:
    - area had >= 2 units in prior 30 days ([now-24h-30d, now-24h))
    - scam_type in last 24h was NOT in prior 30 days
    """
    t0 = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    # 1. Without history (< 2 prior units): only 1 prior unit
    units_no_hist = [
        TrustedUnit(1, t0 - timedelta(days=5), "560102", "job-offer", "sms"),
        TrustedUnit(2, t0 - timedelta(hours=2), "560102", "digital-arrest", "call"),
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: units_no_hist)
    resp = client.get("/alerts?pincode=560102")
    assert resp.status_code == 200
    assert resp.json()["alerts"] == []

    # 2. With history (>= 2 prior units): 2 prior job-offer units, new digital-arrest in last 24h
    units_with_hist = [
        TrustedUnit(1, t0 - timedelta(days=5), "560102", "job-offer", "sms"),
        TrustedUnit(2, t0 - timedelta(days=10), "560102", "job-offer", "call"),
        TrustedUnit(3, t0 - timedelta(hours=2), "560102", "digital-arrest", "call"),
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: units_with_hist)
    resp = client.get("/alerts?pincode=560102")
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    assert len(alerts) == 1
    assert alerts[0] == {
        "type": "NEW_TYPE",
        "pincode": "560102",
        "scam_type": "digital-arrest",
        "window": "24h",
    }

    # 3. Known type (job-offer) in last 24h does NOT fire NEW_TYPE
    units_known_type = [
        TrustedUnit(1, t0 - timedelta(days=5), "560102", "job-offer", "sms"),
        TrustedUnit(2, t0 - timedelta(days=10), "560102", "job-offer", "call"),
        TrustedUnit(3, t0 - timedelta(hours=2), "560102", "job-offer", "sms"),
    ]
    monkeypatch.setattr("app.routes_map.all_trusted_units", lambda db: units_known_type)
    resp = client.get("/alerts?pincode=560102")
    assert resp.status_code == 200
    assert resp.json()["alerts"] == []


def test_alerts_invalid_pincode_returns_400(client):
    """Unknown pincode query param returns 400 INVALID_REQUEST."""
    resp = client.get("/alerts?pincode=999999")
    assert resp.status_code == 400
    assert resp.json() == {"error": "INVALID_REQUEST"}


def test_alerts_and_map_real_reports_scenario(client, test_db, monkeypatch):
    """
    Full end-to-end integration test (matches judge_sim section 3):
    1. Area with a sudden jump gets a SPIKE alert
    2. Normal area (2 a day with baseline) gets NO alert
    3. New kind of scam gets NEW_TYPE (and old kind does not)
    4. Month-old (30 days ago) and 8-day-old reports are accepted (201) but NOT on 7-day map
    5. Recent reports appear on map with right count
    """
    from app.identity import reset_rate_limits
    reset_rate_limits()
    monkeypatch.setattr("app.config.TRUST_BODY_IDENTITY", True)
    t0 = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "now", lambda: t0)

    # 1. SPIKE area (560102): 14 baseline reports over prior 7 days (2/day), then 10 new reports in last 20 hours
    spike_p = "560102"
    for i in range(14):
        hours_ago = 30 + i * 10
        resp = client.post("/reports", json={
            "report_id": f"REP-SPK-BASE-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91981100{i:04d}",
            "pincode": spike_p,
            "reporter_id": f"rep_spk_base_{i}",
            "ip_prefix": f"10.1.{i}.0/24",
            "occurred_at": (t0 - timedelta(hours=hours_ago)).isoformat(),
            "channel": "phone call",
            "scam_type": "digital-arrest",
            "note": f"baseline report incident {i} from long ago",
        })
        assert resp.status_code == 201
    # 10 recent reports on one campaign
    for i in range(10):
        hours_ago = 1 + i * 1.5
        resp = client.post("/reports", json={
            "report_id": f"REP-SPK-REC-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91982200{i:04d}",
            "pincode": spike_p,
            "reporter_id": f"rep_spk_rec_{i}",
            "ip_prefix": f"10.2.{i}.0/24",
            "occurred_at": (t0 - timedelta(hours=hours_ago)).isoformat(),
            "channel": "phone call",
            "scam_type": "digital-arrest",
            "note": f"sudden wave attack incident {i}",
        })
        assert resp.status_code == 201

    r1 = client.get(f"/alerts?pincode={spike_p}")
    assert r1.status_code == 200
    alerts1 = r1.json()["alerts"]
    spikes = [a for a in alerts1 if a.get("type") == "SPIKE"]
    assert len(spikes) == 1
    assert spikes[0]["count"] >= 5
    assert spikes[0]["baseline_per_day"] == 2.0
    assert spikes[0]["pincode"] == spike_p

    # 2. Normal area (560064): same baseline (14 prior reports), but only 2 today -> NO alert
    normal_p = "560064"
    normal_types = ["digital-arrest", "courier-customs"]
    for i in range(14):
        hours_ago = 30 + i * 10
        resp = client.post("/reports", json={
            "report_id": f"REP-NORM-BASE-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91983300{i:04d}",
            "pincode": normal_p,
            "reporter_id": f"rep_norm_base_{i}",
            "ip_prefix": f"10.3.{i}.0/24",
            "occurred_at": (t0 - timedelta(hours=hours_ago)).isoformat(),
            "channel": "phone call",
            "scam_type": normal_types[i % 2],
            "note": f"normal baseline report {i}",
        })
        assert resp.status_code == 201
    for i in range(2):
        hours_ago = 2 + i * 5
        resp = client.post("/reports", json={
            "report_id": f"REP-NORM-REC-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91984400{i:04d}",
            "pincode": normal_p,
            "reporter_id": f"rep_norm_rec_{i}",
            "ip_prefix": f"10.4.{i}.0/24",
            "occurred_at": (t0 - timedelta(hours=hours_ago)).isoformat(),
            "channel": "phone call",
            "scam_type": normal_types[i % 2],
            "note": f"regular report today {i}",
        })
        assert resp.status_code == 201

    r2 = client.get(f"/alerts?pincode={normal_p}")
    assert r2.status_code == 200
    assert r2.json()["alerts"] == []

    # 3. New-type area (110016): 4 'otp-call' reports in prior 3-18 days, then 1 'job-offer' in last 3 hours
    new_p = "110016"
    for i, d in enumerate([3, 6, 10, 18]):
        resp = client.post("/reports", json={
            "report_id": f"REP-NEWT-PRIOR-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91985500{i:04d}",
            "pincode": new_p,
            "reporter_id": f"rep_newt_prior_{i}",
            "ip_prefix": f"10.5.{i}.0/24",
            "occurred_at": (t0 - timedelta(days=d)).isoformat(),
            "channel": "phone call",
            "scam_type": "otp-call",
            "note": f"prior otp call sighting {i}",
        })
        assert resp.status_code == 201
    resp = client.post("/reports", json={
        "report_id": "REP-NEWT-TODAY-1",
        "identifier_type": "phone",
        "identifier_value": "+919866000001",
        "pincode": new_p,
        "reporter_id": "rep_newt_today_1",
        "ip_prefix": "10.6.1.0/24",
        "occurred_at": (t0 - timedelta(hours=3)).isoformat(),
        "channel": "phone call",
        "scam_type": "job-offer",
        "note": "new job offer scam wave sighted today",
    })
    assert resp.status_code == 201

    r3 = client.get(f"/alerts?pincode={new_p}")
    assert r3.status_code == 200
    alerts3 = r3.json()["alerts"]
    nt = [a for a in alerts3 if a.get("type") == "NEW_TYPE"]
    assert any(a.get("scam_type") == "job-offer" for a in nt)
    assert not any(a.get("scam_type") == "otp-call" for a in nt)
    assert not any(a.get("type") == "SPIKE" for a in alerts3)

    # 4. Old reports (400050): 10 reports ~month old (31-35 days), 3 reports 8-9 days old
    # Must be accepted (201), but completely EXCLUDED from default 7-day map
    old_p = "400050"
    old_ok = 0
    for i in range(10):
        hours_ago = 31 * 24 + i * 8
        resp = client.post("/reports", json={
            "report_id": f"REP-OLD-MONTH-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91987700{i:04d}",
            "pincode": old_p,
            "reporter_id": f"rep_old_month_{i}",
            "ip_prefix": f"10.7.{i}.0/24",
            "occurred_at": (t0 - timedelta(hours=hours_ago)).isoformat(),
            "channel": "phone call",
            "scam_type": "digital-arrest",
            "note": f"month old historical report {i}",
        })
        if resp.status_code == 201:
            old_ok += 1
    for i in range(3):
        hours_ago = 8.5 * 24 + i * 5
        resp = client.post("/reports", json={
            "report_id": f"REP-OLD-8DAY-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91988800{i:04d}",
            "pincode": old_p,
            "reporter_id": f"rep_old_8day_{i}",
            "ip_prefix": f"10.8.{i}.0/24",
            "occurred_at": (t0 - timedelta(hours=hours_ago)).isoformat(),
            "channel": "phone call",
            "scam_type": "digital-arrest",
            "note": f"8-day old historical report {i}",
        })
        if resp.status_code == 201:
            old_ok += 1

    assert old_ok == 13
    # Check 7-day map excludes 400050
    map_old = client.get(f"/map?pincode={old_p}&days=7&radius_km=2")
    assert map_old.status_code == 200
    clusters_old = map_old.json().get("clusters", [])
    pincodes_on_map = [c["pincode"] for c in clusters_old]
    assert old_p not in pincodes_on_map

    # 5. Recent reports (500081): 7 independent reports in last 5 days
    recent_p = "500081"
    for i in range(7):
        hours_ago = 5 + i * 15
        resp = client.post("/reports", json={
            "report_id": f"REP-REC-5DAY-{i}",
            "identifier_type": "phone",
            "identifier_value": f"+91989900{i:04d}",
            "pincode": recent_p,
            "reporter_id": f"rep_rec_5day_{i}",
            "ip_prefix": f"10.9.{i}.0/24",
            "occurred_at": (t0 - timedelta(hours=hours_ago)).isoformat(),
            "channel": "phone call",
            "scam_type": "fake-kyc-link",
            "note": f"recent report sighting {i}",
        })
        assert resp.status_code == 201

    map_rec = client.get(f"/map?pincode={recent_p}")
    assert map_rec.status_code == 200
    clusters_rec = [c for c in map_rec.json().get("clusters", []) if c["pincode"] == recent_p]
    assert len(clusters_rec) == 1
    assert clusters_rec[0]["count"] == 7
    assert clusters_rec[0]["severity"] in ("CRIT", "HIGH", "MED")


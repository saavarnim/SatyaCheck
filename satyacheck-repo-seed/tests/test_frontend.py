"""tests/test_frontend.py – Verify web static assets and HTML shell structure (T8 per docs/07-frontend.md)."""
import pytest


def test_index_html_served_at_root(client):
    """GET / must serve web/index.html with title and Leaflet assets."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "SatyaCheck" in html
    assert "leaflet" in html.lower()
    # Check all view sections exist
    assert 'id="view-check"' in html
    assert 'id="view-report"' in html
    assert 'id="view-map"' in html
    assert 'id="view-alerts"' in html
    assert 'id="view-about"' in html
    # Check licence expired overlay exists
    assert 'id="licence-expired-overlay"' in html


def test_static_assets_served(client):
    """Static assets in web/ (css, js) must be served directly."""
    css_resp = client.get("/app.css")
    assert css_resp.status_code == 200
    assert "emerald" in css_resp.text or "--primary" in css_resp.text

    app_js_resp = client.get("/app.js")
    assert app_js_resp.status_code == 200
    assert "translations" in app_js_resp.text or "AREAS" in app_js_resp.text

    i18n_js_resp = client.get("/i18n.js")
    assert i18n_js_resp.status_code == 200
    assert "translations" in i18n_js_resp.text
    assert "सत्यचेक" in i18n_js_resp.text


def test_task_f3_heatmap_and_map_view(client):
    """Task F3: Verify heatmap.js, pinned CDN 0.2.0, time chips (24h/3d/7d), colours and legend."""
    # 1. heatmap.js static asset served
    resp = client.get("/heatmap.js")
    assert resp.status_code == 200
    content = resp.text
    # Verify severity colours
    assert "#D32F2F" in content  # CRIT red
    assert "#F57C00" in content  # HIGH orange
    assert "#F2B01E" in content  # MED amber
    assert "#10b981" in content  # Faint green
    # Verify fallback concentric circles (r, 0.6r, 0.3r)
    assert "0.6" in content and "0.3" in content
    # Verify gradient yellow -> orange -> red
    assert "gradient" in content
    # Verify advice and popup
    assert "Check a number" in content or "popup-check-link" in content
    assert "Top scam type" in content or "top_scam_type" in content

    # 2. index.html has leaflet.heat 0.2.0 and time chips
    idx = client.get("/")
    assert idx.status_code == 200
    html = idx.text
    assert "leaflet.heat@0.2.0" in html or "leaflet.heat/0.2.0" in html
    # Time chips: 24h, 3d, 7d. Never offer more than 7
    assert 'data-days="1"' in html
    assert 'data-days="3"' in html
    assert 'data-days="7"' in html
    assert 'data-days="14"' not in html
    assert 'data-days="30"' not in html
    assert "map-time-chips" in html
    assert "map-blocked-message" in html

    # 3. app.css has mobile 60vh and numbered markers
    css = client.get("/app.css").text
    assert "60vh" in css
    assert "cluster-num-marker" in css
    assert "heatmap-legend" in css

    # 4. i18n has time chips, text badges and legend in EN and HI
    i18n = client.get("/i18n.js").text
    assert "24 hours" in i18n and "24 घंटे" in i18n
    assert "3 days" in i18n and "3 दिन" in i18n
    assert "7 days" in i18n and "7 दिन" in i18n
    assert "A few reports" in i18n and "कुछ रिपोर्टें" in i18n
    assert "Very many" in i18n and "अत्यधिक रिपोर्टें" in i18n
    assert "no reports in this period" in i18n and "कोई रिपोर्ट नहीं" in i18n

    # 5. Interactive filters, search, city chips, and listing tabs
    assert "map-search-input" in html
    assert "map-filter-scam-type" in html
    assert "map-filter-severity" in html
    assert "map-city-chips" in html
    assert "btn-map-fit-all" in html
    assert "cluster-tab-filters" in html
    assert "flyToLocality" in content
    assert "markerPulse" in css or "marker-highlight-pulse" in css


def test_task_f4_timepicker_and_report_submission(client, test_db):
    """Task F4: Verify timepicker.js, UI controls, pure functions nowIst/istIso, and POST /reports with past IST occurred_at."""
    # 1. timepicker.js static asset served with 200
    resp = client.get("/timepicker.js")
    assert resp.status_code == 200
    js = resp.text

    # Verify pure functions exported and window assignments for console testing
    assert "export function nowIst" in js
    assert "export function istIso" in js
    assert "window.nowIst = nowIst" in js
    assert "window.istIso = istIso" in js

    # Verify IST timezone and +05:30 offset
    assert "Asia/Kolkata" in js
    assert "+05:30" in js

    # Verify 90 days min limit
    assert "90" in js

    # 2. index.html has required timepicker UI elements
    idx_resp = client.get("/")
    assert idx_resp.status_code == 200
    html = idx_resp.text

    # Default path remains "Just now" chips & summary
    assert 'id="report-time-chips"' in html
    assert 'id="chip-time-now"' in html
    assert 'id="chip-time-1h"' in html
    assert 'id="chip-time-this-morning"' in html
    assert 'id="chip-time-last-night"' in html
    assert 'id="chip-time-yesterday"' in html
    assert 'id="chip-time-2-3-days"' in html
    assert 'id="chip-time-last-week"' in html

    # Summary line
    assert 'id="timepicker-summary"' in html

    # Collapsed drawer and toggle
    assert 'id="timepicker-toggle-btn"' in html
    assert 'id="timepicker-custom-drawer"' in html
    assert 'id="timepicker-date"' in html
    assert 'id="timepicker-time"' in html
    assert 'id="timepicker-error"' in html

    # 3. i18n has translations for chips and Hindi summary
    i18n_resp = client.get("/i18n.js")
    assert i18n_resp.status_code == 200
    i18n = i18n_resp.text
    assert "Just now" in i18n and "अभी-अभी" in i18n
    assert "1 hour ago" in i18n and "1 घंटा पहले" in i18n
    assert "This morning" in i18n and "आज सुबह" in i18n
    assert "Last night" in i18n and "कल रात" in i18n
    assert "Yesterday" in i18n and "कल" in i18n
    assert "2-3 days ago" in i18n and "2-3 दिन पहले" in i18n
    assert "Last week" in i18n and "पिछले हफ्ते" in i18n
    assert "Change date and time" in i18n and "तारीख और समय बदलें" in i18n

    # 4. Default path submission (takes 0 extra taps)
    default_payload = {
        "report_id": "REP-TEST-DEF-001",
        "identifier_type": "phone",
        "identifier_value": "+91 98765 43210",
        "channel": "phone call",
        "scam_type": "digital-arrest",
        "pincode": "560102",
        "occurred_at": "2026-11-01T07:00:00+05:30",
        "reported_at": "2026-11-01T07:00:00+05:30",
        "reporter_id": "test_device_f4_1",
    }
    def_resp = client.post("/reports", json=default_payload)
    assert def_resp.status_code == 201
    data = def_resp.json()
    assert data["report_id"] == "REP-TEST-DEF-001"

    # 5. Past date & time report submission (e.g. 5 days ago in IST +05:30)
    past_ist = "2026-10-27T14:30:00+05:30"
    past_payload = {
        "report_id": "REP-TEST-PAST-002",
        "identifier_type": "upi",
        "identifier_value": "scammer123@okaxis",
        "channel": "upi request",
        "scam_type": "upi-refund-qr",
        "pincode": "560038",
        "occurred_at": past_ist,
        "reported_at": "2026-11-01T07:00:00+05:30",
        "reporter_id": "test_device_f4_2",
    }
    past_resp = client.post("/reports", json=past_payload)
    assert past_resp.status_code == 201
    assert past_resp.json()["report_id"] == "REP-TEST-PAST-002"

    # Verify in DB that occurred_at was stored accurately
    from app.models import Report
    saved = test_db.query(Report).filter_by(report_id="REP-TEST-PAST-002").first()
    assert saved is not None
    # Converted to UTC in DB: 14:30 IST is 09:00 UTC (14:30 - 05:30 = 09:00)
    assert saved.occurred_at.hour == 9
    assert saved.occurred_at.minute == 0
    assert saved.occurred_at.day == 27
    assert saved.occurred_at.month == 10
    from app.clock import to_ist_iso
    assert to_ist_iso(saved.occurred_at) == "2026-10-27T14:30:00+05:30"

    # 6. Future date & time must be rejected by POST /reports
    future_ist = "2026-11-05T12:00:00+05:30"
    future_payload = {
        "report_id": "REP-TEST-FUT-003",
        "identifier_type": "phone",
        "identifier_value": "+91 91234 56789",
        "channel": "phone call",
        "scam_type": "job-offer",
        "pincode": "560102",
        "occurred_at": future_ist,
        "reporter_id": "test_device_f4_3",
    }
    fut_resp = client.post("/reports", json=future_payload)
    assert fut_resp.status_code == 400
    assert fut_resp.json()["error"] == "INVALID_REQUEST"




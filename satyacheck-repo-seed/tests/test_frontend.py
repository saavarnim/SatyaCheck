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



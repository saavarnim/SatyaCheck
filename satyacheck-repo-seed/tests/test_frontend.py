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

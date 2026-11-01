"""tests/test_export.py – Tests for admin export and official portals (Task F2)."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app import config
from app.db import SessionLocal
from app.main import app
from app.models import Indicator, Report


def test_export_requires_valid_admin_token(client):
    """GET /admin/export/known-scams requires X-Admin-Token."""
    # 1. No token -> 401
    resp_no_token = client.get("/admin/export/known-scams")
    assert resp_no_token.status_code in (401, 403)

    # 2. Invalid token -> 403
    resp_bad_token = client.get(
        "/admin/export/known-scams",
        headers={"X-Admin-Token": "wrong-token"},
    )
    assert resp_bad_token.status_code == 403

    # 3. Valid token -> 200
    resp_valid = client.get(
        "/admin/export/known-scams",
        headers={"X-Admin-Token": config.ADMIN_TOKEN},
    )
    assert resp_valid.status_code == 200


def test_export_contains_no_reporter_ip_or_note_data(client):
    """Privacy rule: export must never contain reporter tokens, IPs, or user notes."""
    resp = client.get(
        "/admin/export/known-scams",
        headers={"X-Admin-Token": config.ADMIN_TOKEN},
    )
    assert resp.status_code == 200
    data = resp.json()

    prohibited_keys = ["reporter", "reporter_token", "ip", "ip_token", "ip_prefix", "note", "note_redacted"]
    for row in data:
        for k in row.keys():
            assert k.lower() not in prohibited_keys, f"Found prohibited key '{k}' in export"
        row_str = json.dumps(row).lower()
        for pk in ("reporter_token", "ip_token", "note_redacted"):
            assert pk not in row_str, f"Found '{pk}' in serialized row: {row_str}"


def test_export_includes_only_known_scam(client):
    """Export only includes indicators reaching KNOWN_SCAM status."""
    resp = client.get(
        "/admin/export/known-scams",
        headers={"X-Admin-Token": config.ADMIN_TOKEN},
    )
    assert resp.status_code == 200
    data = resp.json()

    # The seeded database has verified businesses (e.g. +918041002233)
    # Verified businesses must never appear in known scams export
    values_in_export = [item["value"] for item in data]
    assert "+918041002233" not in values_in_export, "Verified business appeared in known scams export"

    for row in data:
        assert "type" in row
        assert "value" in row
        assert "distinct_reporters" in row
        assert "first_seen" in row
        assert "last_seen" in row
        assert "scam_type" in row
        assert "top_pincodes" in row
        assert row["distinct_reporters"] >= 3, "Only indicators with >= 3 cohorts can be KNOWN_SCAM"


def test_export_csv_format(client):
    """GET /admin/export/known-scams?format=csv returns text/csv."""
    resp = client.get(
        "/admin/export/known-scams?format=csv",
        headers={"X-Admin-Token": config.ADMIN_TOKEN},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    content = resp.text
    lines = content.strip().splitlines()
    assert len(lines) >= 1
    header = lines[0].split(",")
    expected_headers = ["type", "value", "distinct_reporters", "first_seen", "last_seen", "scam_type", "top_pincodes"]
    assert header == expected_headers


def test_official_json_portal_links_and_hindi_text():
    """web/official.json: web links are https, includes 1930 tel link, has Hindi descriptions."""
    official_file = Path(__file__).resolve().parent.parent / "web" / "official.json"
    assert official_file.exists(), "web/official.json must exist"

    data = json.loads(official_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 3, "Must include 1930, cybercrime.gov.in, and sancharsaathi.gov.in"

    has_1930 = False
    has_cybercrime = False
    has_sancharsaathi = False

    for item in data:
        assert "id" in item
        assert "name_en" in item
        assert "name_hi" in item
        assert "desc_en" in item
        assert "desc_hi" in item
        assert "url" in item

        # Verify non-empty Hindi strings with Devanagari characters
        assert any("\u0900" <= char <= "\u097F" for char in item["name_hi"]), f"No Hindi text in {item['name_hi']}"
        assert any("\u0900" <= char <= "\u097F" for char in item["desc_hi"]), f"No Hindi text in {item['desc_hi']}"

        url = item["url"]
        if "1930" in url:
            has_1930 = True
            assert url.startswith("tel:1930"), f"1930 link must be tel link, got {url}"
        elif "cybercrime.gov.in" in url:
            has_cybercrime = True
            assert url.startswith("https://"), f"cybercrime.gov.in link must be https, got {url}"
        elif "sancharsaathi.gov.in" in url:
            has_sancharsaathi = True
            assert url.startswith("https://"), f"sancharsaathi link must be https, got {url}"

    assert has_1930, "Missing 1930 portal"
    assert has_cybercrime, "Missing cybercrime.gov.in portal"
    assert has_sancharsaathi, "Missing sancharsaathi portal (Chakshu)"


def test_advisories_json_shipped_empty():
    """web/advisories.json must ship as an empty array per spec."""
    advisories_file = Path(__file__).resolve().parent.parent / "web" / "advisories.json"
    assert advisories_file.exists(), "web/advisories.json must exist"

    data = json.loads(advisories_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 0, "web/advisories.json must ship as an empty list"


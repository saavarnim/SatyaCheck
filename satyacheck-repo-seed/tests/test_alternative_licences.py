"""tests/test_alternative_licences.py – Test alternative 5-minute licence keys catalog."""
import json
from pathlib import Path
from datetime import datetime, timezone
import base64
from app.licence import verify
import app.config as config


def test_alternative_5min_slots_validity():
    catalog_path = Path("licences/alternative_5min.json")
    assert catalog_path.exists(), "licences/alternative_5min.json must exist"

    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert "slots" in data
    assert len(data["slots"]) >= 40

    pub_bytes = base64.b64decode(config.LICENCE_PUBLIC_KEY)

    for slot in data["slots"]:
        assert slot["licensee"] == "Demo Bank"
        assert "validity_window_ist" in slot
        assert "validity_window_sgt" in slot
        assert "IST" in slot["time_validity"]["ist"]["expires_at"]
        assert "SGT" in slot["time_validity"]["sgt"]["expires_at"]

        # Cryptographic verification
        valid = verify(slot["licensee"], slot["expires_at"], slot["signature"], pub_bytes)
        assert valid is True, f"Signature invalid for slot {slot['slot_id']}"


def test_standalone_slot_files():
    slots_dir = Path("licences/slots")
    assert slots_dir.exists()
    slot_files = list(slots_dir.glob("slot_*.json"))
    assert len(slot_files) >= 40

    pub_bytes = base64.b64decode(config.LICENCE_PUBLIC_KEY)
    sample = json.loads(slot_files[0].read_text(encoding="utf-8"))
    assert "licensee" in sample
    assert "expires_at" in sample
    assert "signature" in sample
    assert "_validity_notes" in sample
    assert verify(sample["licensee"], sample["expires_at"], sample["signature"], pub_bytes) is True


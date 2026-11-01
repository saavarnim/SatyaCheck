#!/usr/bin/env python3
"""tools/generate_slots.py – Generate pre-signed 5-minute licence slots.

Covers the demo window (10:00 AM to 1:00 PM+ IST / 12:30 PM to 3:30 PM+ SGT).
Outputs:
- licences/alternative_5min.json: Complete catalog of slots with full IST & SGT metadata.
- licences/slots/slot_*.json: Standalone files for each slot ready for direct upload.
"""
from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.licence import sign, verify
import app.config as config


def main() -> None:
    priv_path = Path.home() / ".satyacheck" / "private.key"
    if not priv_path.exists():
        print(f"Error: private key not found at {priv_path}", file=sys.stderr)
        sys.exit(1)

    priv_key = priv_path.read_bytes()
    pub_bytes = base64.b64decode(config.LICENCE_PUBLIC_KEY)

    ist = timezone(timedelta(hours=5, minutes=30), name="IST")
    sgt = timezone(timedelta(hours=8), name="SGT")

    # Cover from 09:55 AM IST to 02:05 PM IST on Nov 1, 2026 (50 slots of 5 mins)
    start_dt_ist = datetime(2026, 11, 1, 9, 55, 0, tzinfo=ist)
    end_dt_ist = datetime(2026, 11, 1, 14, 5, 0, tzinfo=ist)

    slots = []
    slots_dir = ROOT_DIR / "licences" / "slots"
    slots_dir.mkdir(parents=True, exist_ok=True)

    curr = start_dt_ist
    slot_idx = 1

    while curr < end_dt_ist:
        exp_ist = curr + timedelta(minutes=5)
        exp_utc = exp_ist.astimezone(timezone.utc)
        curr_sgt = curr.astimezone(sgt)
        exp_sgt = exp_ist.astimezone(sgt)

        expires_at_iso = exp_utc.isoformat()
        licensee = "Demo Bank"
        sig = sign(licensee, expires_at_iso, priv_key)

        # Verify against public key
        assert verify(licensee, expires_at_iso, sig, pub_bytes), f"Signature failed for slot {slot_idx}"

        slot_data = {
            "slot_id": f"SLOT-{slot_idx:02d}",
            "validity_window_ist": f"{curr.strftime('%I:%M %p')} to {exp_ist.strftime('%I:%M %p')} IST (01 Nov 2026)",
            "validity_window_sgt": f"{curr_sgt.strftime('%I:%M %p')} to {exp_sgt.strftime('%I:%M %p')} SGT (01 Nov 2026)",
            "time_validity": {
                "ist": {
                    "valid_from": curr.strftime("%Y-%m-%d %I:%M:%S %p IST"),
                    "expires_at": exp_ist.strftime("%Y-%m-%d %I:%M:%S %p IST"),
                    "utc_offset": "+05:30"
                },
                "sgt": {
                    "valid_from": curr_sgt.strftime("%Y-%m-%d %I:%M:%S %p SGT"),
                    "expires_at": exp_sgt.strftime("%Y-%m-%d %I:%M:%S %p SGT"),
                    "utc_offset": "+08:00"
                }
            },
            "licensee": licensee,
            "expires_at": expires_at_iso,
            "signature": sig,
        }
        slots.append(slot_data)

        # Also write standalone slot json for direct upload
        time_tag = curr.strftime("%H%M")
        slot_filename = f"slot_{slot_idx:02d}_{time_tag}_ist.json"
        slot_file_payload = {
            "licensee": licensee,
            "expires_at": expires_at_iso,
            "signature": sig,
            "_validity_notes": {
                "slot_id": slot_data["slot_id"],
                "validity_ist": slot_data["validity_window_ist"],
                "validity_sgt": slot_data["validity_window_sgt"],
            }
        }
        (slots_dir / slot_filename).write_text(json.dumps(slot_file_payload, indent=2) + "\n", encoding="utf-8")

        slot_idx += 1
        curr = exp_ist

    catalog = {
        "title": "SatyaCheck 5-Minute Alternative Licence Keys",
        "description": "Pre-signed 5-minute evaluation licence keys for the live demo window (10:00 AM to 1:00 PM+ IST / 12:30 PM to 3:30 PM+ SGT).",
        "generated_date": "2026-11-01",
        "licensee": "Demo Bank",
        "total_slots": len(slots),
        "timezone_reference": {
            "IST": "Indian Standard Time (UTC+05:30)",
            "SGT": "Singapore Time (UTC+08:00, IST + 2h 30m)"
        },
        "instructions": "Copy any single slot JSON or upload it in the web interface. To test, upload a slot matching your current time window. After 5 minutes, the app will return 403 / expired state. Then upload licences/long.json to restore.",
        "slots": slots
    }

    out_file = ROOT_DIR / "licences" / "alternative_5min.json"
    out_file.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"Successfully generated {len(slots)} slots in {out_file} and {slots_dir}")


if __name__ == "__main__":
    main()


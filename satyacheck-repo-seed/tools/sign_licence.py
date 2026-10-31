#!/usr/bin/env python3
"""tools/sign_licence.py – Create a signed licence JSON file.

Usage:
    python tools/sign_licence.py --licensee "Demo Bank" --minutes 5
    python tools/sign_licence.py --licensee "Demo Bank" --days 30
    python tools/sign_licence.py --licensee "Demo Bank" --days 30 -o licence.json

Reads the private key from ~/.satyacheck/private.key.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Import the pure licence helpers (no other app modules)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.licence import sign  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Sign a SatyaCheck licence")
    parser.add_argument("--licensee", required=True, help="Licensee name")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--minutes", type=int, help="Minutes until expiry")
    group.add_argument("--days", type=int, help="Days until expiry")
    parser.add_argument("-o", "--output", default=None,
                        help="Output file (default: stdout)")
    args = parser.parse_args()

    # Load private key
    private_key_path = Path.home() / ".satyacheck" / "private.key"
    if not private_key_path.exists():
        print(f"ERROR: Private key not found at {private_key_path}", file=sys.stderr)
        print("Run  python tools/gen_keys.py  first.", file=sys.stderr)
        sys.exit(1)

    private_key_bytes = private_key_path.read_bytes()
    if len(private_key_bytes) != 32:
        print("ERROR: Private key must be exactly 32 bytes.", file=sys.stderr)
        sys.exit(1)

    # Compute expiry
    now = datetime.now(timezone.utc)
    if args.minutes:
        expires = now + timedelta(minutes=args.minutes)
    else:
        expires = now + timedelta(days=args.days)

    expires_at = expires.isoformat()

    # Sign
    signature_b64 = sign(args.licensee, expires_at, private_key_bytes)

    licence = {
        "licensee": args.licensee,
        "expires_at": expires_at,
        "signature": signature_b64,
    }

    licence_json = json.dumps(licence, indent=2)

    if args.output:
        Path(args.output).write_text(licence_json + "\n", encoding="utf-8")
        print(f"Licence written to {args.output}")
    else:
        print(licence_json)


if __name__ == "__main__":
    main()

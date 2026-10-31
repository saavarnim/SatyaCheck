#!/usr/bin/env python3
"""tools/gen_keys.py – Generate an Ed25519 keypair for licence signing.

Writes the PRIVATE key to ~/.satyacheck/private.key (outside the repo).
Prints the PUBLIC key as base64 (to be pasted into app/licence_pubkey.py
or set via LICENSE_PUBLIC_KEY env var).

Usage:
    python tools/gen_keys.py
"""

from __future__ import annotations

import base64
import os
import stat
import sys
from pathlib import Path

from nacl.signing import SigningKey


def main() -> None:
    key_dir = Path.home() / ".satyacheck"
    key_dir.mkdir(parents=True, exist_ok=True)
    private_key_path = key_dir / "private.key"

    if private_key_path.exists():
        print(f"⚠  Private key already exists at {private_key_path}", file=sys.stderr)
        print("   Delete it first if you really want to regenerate.", file=sys.stderr)
        sys.exit(1)

    signing_key = SigningKey.generate()
    private_bytes = bytes(signing_key)  # 32-byte seed
    public_bytes = bytes(signing_key.verify_key)  # 32-byte public key

    # Write private key (owner-read-only)
    private_key_path.write_bytes(private_bytes)
    try:
        os.chmod(private_key_path, stat.S_IRUSR)
    except OSError:
        pass  # Windows may not support chmod fully

    public_b64 = base64.b64encode(public_bytes).decode("ascii")

    print(f"Private key written to: {private_key_path}")
    print(f"Public key (base64):    {public_b64}")
    print()
    print("Paste this into app/licence_pubkey.py:")
    print(f'PUBLIC_KEY_B64 = "{public_b64}"')


if __name__ == "__main__":
    main()

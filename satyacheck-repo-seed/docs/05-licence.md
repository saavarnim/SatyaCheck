# Licence (app/licence.py, app/routes_licence.py, tools/*)
Licence JSON: `{"licensee": str, "expires_at": ISO-8601 with offset, "signature": base64}`.
Signature = Ed25519 (PyNaCl) over UTF-8 of `json.dumps({"licensee":..., "expires_at":...}, sort_keys=True, separators=(",", ":"))`.

## Keys
- `tools/gen_keys.py` writes the PRIVATE key to `~/.satyacheck/private.key` (outside the repo) and prints the PUBLIC key (base64). Public key goes in `app/licence_pubkey.py` (committed; env LICENSE_PUBLIC_KEY can override).
- ONE person (the "signer", see GIT_WORKFLOW.md) holds the private key. It is never committed, never deployed, never pasted into an agent chat.
- `tools/sign_licence.py --licensee "Demo Bank" --minutes 5` or `--days 30` writes a licence JSON file.

## Behaviour
- Middleware checks on EVERY request. Open when expired: GET /health, GET+POST /license, static files. Protected prefixes (docs/01) -> 403 `{"error":"LICENSE_EXPIRED"}`. NEVER delete data on expiry.
- Cache the parsed licence in memory; refresh from DB every 5 s and immediately on POST. Adds ~zero latency.
- **GET /license** (works when expired) -> `{"licensee","expires_at","status":"ACTIVE"|"EXPIRED","seconds_remaining"}`.
- **POST /license**: bad signature -> 400 `{"error":"INVALID_SIGNATURE"}`; expires_at already past -> 400 `{"error":"ALREADY_EXPIRED"}`; else store and activate with NO restart. **Replacing a long licence with a shorter one must work** (the live demo uploads a 5-minute licence over a long one).
- **Clock rollback**: persist last_seen_server_time (write at most every 20 s, always keep the max, survives restart). If now() < last_seen - CLOCK_TOLERANCE_S (120) -> treat as expired.
- No licence yet -> behave as expired. Optional env LICENSE_BOOTSTRAP (licence JSON string) loads one on first boot.

## tests/test_licence.py
valid; tampered expires_at fails; expired -> protected 403 but /health and /license 200; renewal without restart and data preserved; 5-min licence over a long one; clock rollback; static file reachable while expired.

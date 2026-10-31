# Privacy checklist (cross-cutting; every task obeys, T-final audits)
1. Stored: pincode only for location (locality/city from areas.json). No names, phones of reporters, GPS.
2. reporter_id and ip_prefix stored only as HMAC tokens (docs/03). Never returned.
3. Notes: redacted (docs/02), <= 300 chars, internal only, never returned by any route.
4. No screenshot uploads. `has_screenshot` is a boolean only.
5. Logging: custom middleware logs method, path WITHOUT query string, status, duration. Disable uvicorn access log (`--no-access-log`). No bodies, no identifiers, no tokens, no claimant data. 500s return `{"error":"SERVER_ERROR"}` with no trace.
6. Masking until 3 distinct cohorts (docs/03). Masked raw value must not appear anywhere in the JSON.
7. Wording: "reported", never "scammer", "fraud", "fraudster", "criminal", "culprit". Add `tests/test_wording.py` scanning `web/` strings and API label text for these words.
8. Challenge claimant data lives only in `challenges`, never in public responses/logs.
9. No scraping, no people-search, no external API calls.
10. Evidence objects: only occurred_at, channel, scam_type, pincode.

# Golden rules (breaking one = disqualification or lost points)
Privacy
- Never store or return reporter name, phone or exact location. Location = pincode only.
- reporter_id and ip_prefix are stored ONLY as salted HMAC tokens. Never returned.
- Notes: redacted before storage, internal only, never returned.
- Logs: method, path WITHOUT query string, status, duration. Never bodies, identifiers, notes, tokens, claimant data.
- Wording: "reported", never "scammer / fraud / fraudster / criminal / culprit".
- No scraping, no external network calls.
API
- Bad input -> HTTP 400 `{"error": ...}` (never 422). Never echo the raw value in errors.
- Times come from each report's `occurred_at`, compared with `clock.now()` (never `datetime.now()`).
- Never reject old timestamps. Reject only unparseable or > 5 min in the future.
- All tunable numbers live in `app/config.py`. No hardcoded identifiers or special cases.
- Evidence objects contain only: occurred_at, channel, scam_type, pincode.

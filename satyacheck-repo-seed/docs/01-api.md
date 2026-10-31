# API contract (exact; the judge's test tool depends on it)

General: JSON in/out. The 7 judging routes have NO auth. Extra response fields are fine. Output timestamps in IST (`+05:30`), stored UTC.
- Request models: all fields optional, extra allowed. Register a `RequestValidationError` handler returning **400** `{"error":"INVALID_REQUEST"}` (FastAPI's default 422 is wrong). Never echo values.
- Mount the static `web/` folder at `/` LAST, after routers. Frontend uses `#hash` routes only (so `/map` etc. stay API).
- Licence-protected path prefixes: `/reports /lookup /map /alerts /admin /challenges`. When expired -> 403 `{"error":"LICENSE_EXPIRED"}`. Always open: `/health`, `/license`, static files.

## Tables (SQLAlchemy, no DB-specific SQL)
- indicators(id, type, canonical_value; unique(type, canonical_value))
- reports(id, report_id unique, case_id, indicator_id, occurred_at, reported_at, reporter_token, ip_token, channel, scam_type, pincode, note_redacted, has_screenshot, amount_lost_inr)
- areas(pincode pk, locality, city, lat, lng)  <- data/areas.json
- verified_indicators(type, canonical_value, org, source['seed'|'demo'|'review'])  <- data/verified.json
- challenges(id, indicator_id, claimant_name, contact_email, proof_note, status['under_review'|'upheld'|'rejected'], created_at, resolved_at)  (never in public queries, never logged)
- licence_state(id=1, licensee, expires_at, signature, last_seen_server_time)
Indexes: reports(indicator_id, occurred_at), reports(pincode, occurred_at), reports(reporter_token).

## Routes
**GET /health** -> 200 `{"ok":true}`

**POST /reports** body: report_id, occurred_at, reported_at, reporter_id, ip_prefix, channel, scam_type, identifier_type (phone|upi|url|sender_id), identifier_value, pincode, locality, city, note, has_screenshot, amount_lost_inr.
- 201 `{"report_id","case_id","merged"}`; merged=true if the indicator already had a stored report. case_id stable per indicator (`"CASE-"`+short hash).
- 400 `{"error"}` for invalid identifier / unknown pincode / bad time. 429 `{"error":"SLOW_DOWN"}` when rate limited (docs/03).
- Duplicate report_id -> 201 with same case_id, store nothing new.
- channel not in list -> "Something else". scam_type not in known list -> "other". (docs/02)
- Locality/city come from areas table, ignore request values.

**GET /lookup?type=&value=** (value URL-encoded; optional `&pincode=`)
`{"verdict","report_count","distinct_reporters","first_seen","last_seen","scam_type","display_value","evidence","challenged"}`
- verdict exactly KNOWN_SCAM | SUSPICIOUS | NO_REPORTS | VERIFIED_BUSINESS (order in docs/03).
- report_count = stored events for the indicator; distinct_reporters = cohort_count; scam_type = most common among trusted units ("other" if none).
- first_seen/last_seen = min/max occurred_at (null if none). display_value masked unless distinct_reporters >= 3 or verified.
- evidence = up to 5 latest trusted units as `{occurred_at, channel, scam_type, pincode}` ONLY.
- Valid but unreported -> 200 NO_REPORTS (never 404). Invalid (e.g. `12345`) -> 400.

**GET /map?pincode=&days=7&radius_km=2** -> `{"clusters":[{"pincode","locality","city","count","top_scam_type","severity","lat","lng"}]}` (docs/04)
**GET /alerts?pincode=** -> `{"alerts":[...]}` or `{"alerts":[]}` (docs/04)
**POST /admin/reset** -> 200. Only if env DEMO_MODE=true, else 403 `{"error":"DEMO_MODE_REQUIRED"}`. No auth (test tool sends none). Deletes reports, indicators, challenges, review-added verified rows; keeps areas, seed verified, licence.
**POST /challenges** body: identifier_type, identifier_value, claimant_name, contact_email, proof_note -> 201 `{"challenge_id":"CH-xxxxxx","status":"under_review"}`. If an under_review challenge exists for the indicator, return 201 with the existing id. Lookup then has challenged=true and is never KNOWN_SCAM.
**GET /admin/challenges**, **POST /admin/challenges/{id}/resolve** `{"decision":"upheld"|"rejected"}` need header `X-Admin-Token` == env ADMIN_TOKEN. upheld -> add to verified_indicators(source='review'); rejected -> close, and block new challenges for that indicator for 7 days (409).
**GET/POST /license**: docs/05.

# SatyaCheck — Development Progress Log

> **Time Budget:** 8 Hours Total  
> **Development Rules:**  
> - Simple, robust implementations — no over-engineering.  
> - Run tests and ensure all pass before committing.  
> - Push to Git after every completed task slice.  
> - Obtain approval before starting the next task slice.  
> - Never assume — ask for clarification when in doubt.  
> - Strictly uphold AGENTS.md privacy rules (no PII, HMAC-only tokens, redacted notes, safe logging).

---

## Task Roadmap & Status

| Task ID | Description | Status | Commit / Notes |
|---|---|---|---|
| **T0** | Application scaffold | **DONE** | Commit `[T0] scaffold` |
| **T1** | Normalise & redact (`normalise.py`, `redact.py`, 56 tests) | **DONE** | Commit `[T1] normalise + redact` |
| **T2a** | DB engine, session, models (`app/db.py`, `app/models.py`) | **DONE** | Commit `[T2a] db engine, session, models` |
| **T2b** | Seed loader (`app/seed.py`) | **DONE** | Commit `[T2b] seed loader wired` |
| **T2c** | POST /reports (`routes_reports.py`, `tests/test_reports.py`) | **DONE** | Validation, HMAC, duplicates, rate limit |
| **T2d** | GET /lookup basic (`routes_reports.py`) | **DONE** | NO_REPORTS, VERIFIED_BUSINESS, 400 |
| **T3a** | Trust core (pure functions: voice, cohort, score) | **DONE** | Voice, cohort (union-find), scoring |
| **T3b** | Verdict + masking (pure functions) | **DONE** | Verdict precedence, unmasking at 3 cohorts |
| **T3c** | HMAC tokens + rate limit | **DONE** | HMAC 16-hex, IPv4/v6 prefix, sliding window |
| **T3d** | Wire trust + verdict + identity into routes | **DONE** | Integration in `app/routes_reports.py` |
| **T4** | Threshold tuning & wording privacy audit | **DONE** | `app/config.py` constants & `test_wording.py` |
| **T5** | Map & alerts APIs (`routes_map.py`) | **DONE** | GET /map, GET /alerts (SPIKE, NEW_TYPE) |
| **T6** | Licence system (cryptography, middleware, cache) | **DONE** | 23/23 tests pass |
| **T6b** | Public HTTPS deployment | **Pending** | Render / fly / Railway |
| **T7** | Challenges & admin routes | **DONE** | POST /challenges, GET/POST admin, reset |
| **T8** | Frontend (HTML, CSS, JS, Leaflet map) | **NEXT** | `web/` plain static files, EN/HI i18n |
| **T9** | README, demo script, video | **Pending** | Documentation & submission |
| **T10** | Privacy audit & performance verification | **Pending** | docs/06-privacy.md checklist |

---

## Task Execution Log

### Baseline (Prior to Turn)
- **T0 Scaffold:** Created directory layout, configuration, database setup, models, logging middleware, and health check endpoint.
- **T1 Normalisation & Redaction:** Implemented normalisation for phone, UPI, URL, and SMS sender IDs with `InvalidIdentifier` handling. Implemented regex-based PII scrubbing + 300-char truncation in `redact.py`. 56/56 tests passing.
- **T2a Database Setup:** Six core database tables (`indicators`, `reports`, `areas`, `verified_indicators`, `challenges`, `licence_state`) configured in `app/models.py`.
- **T6 Licence System:** Full Ed25519 signature verification, ISO-8601 expiry checks, persistent state, 5-second cache, clock-rollback detection with tolerance, dynamic activation without application restart. 23/23 tests passing.
### [T2b] Seed Loader Wired & Verified (2026-10-31)
- **Files Modified:** `app/main.py`, `tasks/A.md`, `status/A.md`
- **Actions:** Connected `seed(db)` to `on_startup` in `app/main.py` so tables are populated automatically upon launch. Confirmed idempotent seeding (25 areas, 19 verified indicators).
- **Test Status:** 79/79 pytest tests passing.

### [T2c] POST /reports Endpoint & Rate Limiting (2026-10-31)
- **Files Modified/Created:** `app/routes_reports.py`, `app/identity.py`, `tests/test_reports.py`, `tests/conftest.py`, `tasks/A.md`, `status/A.md`
- **Actions:**
  - Implemented `POST /reports` handling validation of identifier types (`phone`, `upi`, `url`, `sender_id`) and canonical values using T1 normalisation.
  - Implemented area/pincode validation against the seeded `areas` table.
  - Added timestamp validation rejecting timestamps in the future.
  - Added `report_id` duplicate detection returning 201 unchanged without creating duplicate rows.
  - Handled indicator lookup/creation, case ID generation (`CASE-<hash>`), and `merged` indicator status.
  - Implemented HMAC-SHA256 pseudonymisation for `reporter_token` and `ip_token` in `app/identity.py` (privacy preservation).
  - Implemented in-memory sliding window rate limiting (429 `SLOW_DOWN`).
  - Added full test suite in `tests/test_reports.py` (9 tests covering 4 phone formats mapping to one indicator, invalid input 400, duplicate report idempotency, note PII scrubbing, and 429 rate limiting).
- **Test Status:** 88/88 pytest tests passing.

### [T2d] GET /lookup Basic Endpoint (2026-10-31)
- **Files Modified/Created:** `app/routes_reports.py`, `app/verdict.py`, `app/clock.py`, `tests/test_lookup.py`, `tasks/A.md`, `status/A.md`
- **Actions:**
  - Implemented `GET /lookup?type=&value=` returning full JSON schema per `docs/01-api.md`.
  - Added lookup for `verified_indicators` returning `VERIFIED_BUSINESS` (e.g. `1930`).
  - Added valid unreported indicator lookup returning HTTP 200 with `verdict: "NO_REPORTS"` (never 404).
  - Enforced HTTP 400 for invalid identifiers (e.g., `12345`).
  - Implemented `to_ist_iso` in `app/clock.py` converting UTC timestamps to IST (`+05:30`) for public outputs.
  - Implemented `mask_display_value` in `app/verdict.py` (phone, UPI, URL, sender_id rules).
  - Implemented evidence extraction (up to 5 latest events with `occurred_at`, `channel`, `scam_type`, `pincode`).
  - Added test suite in `tests/test_lookup.py` (5 tests passing).
- **Test Status:** 93/93 pytest tests passing.

### [T3a] Trust Core Pure Functions (2026-10-31)
- **Files Modified/Created:** `app/trust.py`, `tests/test_trust.py`, `tasks/A.md`, `status/A.md`
- **Actions:**
  - Implemented `compute_indicator_trust(events)` as pure function per `docs/03-trust.md`.
  - Implemented voice deduplication: groups reports by `reporter_token`, keeping earliest event and longest note.
  - Implemented disjoint-set union-find cohort formation merging on shared `ip_token` or character 3-gram Jaccard similarity $\ge 0.80$ (for notes $\ge 15$ characters).
  - Implemented cohort weighting: 1.0 for notes $\ge 15$ chars, 0.9 otherwise; total confidence score = sum of cohort weights.
  - Implemented `TrustedUnit` generation per cohort for map/alert aggregation.
  - Added `all_trusted_units(db)` helper.
  - Added unit test suite in `tests/test_trust.py` (7 tests covering voice deduplication, IP-based merging, note similarity merging, Hindi/multilingual similarity, and independent cohorts).
- **Test Status:** 100/100 pytest tests passing.

### [T3b] Verdict Precedence & Masking Pure Tests (2026-10-31)
- **Files Modified/Created:** `app/verdict.py`, `tests/test_verdict.py`, `tasks/A.md`, `status/A.md`
- **Actions:**
  - Implemented `verdict(trust, is_verified, has_active_challenge)` respecting strict precedence:
    `VERIFIED_BUSINESS` > `NO_REPORTS` > active challenge cap (`SUSPICIOUS`) > `KNOWN_SCAM` ($\ge 3$ cohorts and score $\ge 2.5$) > `SUSPICIOUS`.
  - Implemented `mask_display_value` for all four identifier types (`phone`, `upi`, `url`, `sender_id`).
  - Added `resolve_display_value` unmasking at $\ge 3$ cohorts or when indicator belongs to a verified business.
  - Created unit test suite in `tests/test_verdict.py` (10 tests covering full verdict ordering, all 4 masking types, and cohort unmasking thresholds).
- **Test Status:** 110/110 pytest tests passing.

### [T3c] HMAC Pseudonymisation & Rate Limiting Unit Tests (2026-10-31)
- **Files Modified/Created:** `tests/test_identity.py`, `tasks/A.md`, `status/A.md`
- **Actions:**
  - Validated deterministic HMAC-SHA256 16-hex token derivation for pseudonymous reporter tokens and IP tokens.
  - Verified network prefix masking for IPv4 (`/24`) and IPv6 (`/48`).
  - Tested header-based identity resolution (`X-Device-Id` and `X-Forwarded-For`) vs body-based identity under `TRUST_BODY_IDENTITY=True`.
  - Tested in-memory sliding window rate limits: 30 submissions/hour per reporter and 10 submissions/hour per reporter per indicator, with expiry of records older than 1 hour.
  - Created unit test suite in `tests/test_identity.py` (10 tests passing).
- **Test Status:** 120/120 pytest tests passing.

### [T3d] Wire Trust Engine, Verdict, and Identity into Routes (2026-10-31)
- **Files Modified/Created:** `app/routes_reports.py`, `app/identity.py`, `tests/test_scenarios.py`, `tasks/A.md`, `status/A.md`
- **Actions:**
  - Integrated `compute_indicator_trust` into `GET /lookup` by transforming database reports into `EventRow` models.
  - Wired `verdict()` and `resolve_display_value()` into `GET /lookup`.
  - Derived `evidence` from the aggregated `TrustedUnit` list (sorted descending by `occurred_at`, limited to 5).
  - Derived `top_scam_type` from `TrustedUnit`s.
  - Refactored `app/identity.py` to reference `config.TRUST_BODY_IDENTITY` dynamically for testing and runtime control.
  - Implemented end-to-end integration scenario tests in `tests/test_scenarios.py`:
    - 22 bot accounts reporting from one IP prefix group into exactly 1 cohort: stays `SUSPICIOUS`, display_value remains masked, exactly 1 `TrustedUnit`.
    - 3 independent reporters on different networks with distinct notes produce 3 cohorts: reaches `KNOWN_SCAM` and unmasks the display_value.
    - 1 reporter submitting 6 reports contributes 1 voice and 1 cohort.
- **Test Status:** 123/123 pytest tests passing.

### [T4] Threshold Tuning & Prohibited Wording Audit (2026-10-31)
- **Files Modified/Created:** `tests/test_wording.py`, `tasks/A.md`, `status/A.md`, `progress.md`
- **Actions:**
  - Audited `app/config.py` constants (`NOTE_MIN_LEN=15`, `SIM_THRESHOLD=0.80`, `WEIGHT_NOTE=1.0`, `WEIGHT_NO_NOTE=0.9`, `KNOWN_MIN_COHORTS=3`, `KNOWN_MIN_SCORE=2.5`, `UNMASK_MIN=3`, `RATE_PER_HOUR=30`, `RATE_PER_INDICATOR_HOUR=10`, `MAP_DEFAULT_DAYS=7`, `MAP_DEFAULT_RADIUS_KM=2.0`). All verified consistent with specification.
  - Implemented `tests/test_wording.py` enforcing strict privacy policy rule 7 from `docs/06-privacy.md`:
    - Scans all Python files under `app/` to ensure prohibited words (`scammer`, `fraudster`, `criminal`, `culprit`) never appear in code.
    - Tests live API responses (`/health`, `/lookup`) ensuring prohibited terms are never returned.
- **Test Status:** 125/125 pytest tests passing.

### [T5] Map & Alerts APIs (2026-10-31)
- **Files Modified/Created:** `app/routes_map.py`, `app/config.py`, `tests/test_map_alerts.py`, `tasks/B.md`, `status/B.md`, `progress.md`
- **Actions:**
  - Implemented `GET /map?pincode=&days=7&radius_km=2`:
    - Filters `TrustedUnit`s within the sliding window `(now - days, now]`.
    - Handles geographic filtering when `pincode` is provided, computing Haversine distance from the reference area center to all candidate areas.
    - Groups units into area clusters returning `pincode`, `locality`, `city`, `count`, `top_scam_type`, `severity` (`CRIT` for $\ge 10$, `HIGH` for $\ge 5$, `MED` otherwise), `lat`, and `lng`.
    - Enforces 400 `INVALID_REQUEST` on unknown pincodes, non-positive days, or negative radius.
  - Implemented `GET /alerts?pincode=`:
    - Evaluates 24-hour activity window `(now - 24h, now]` against baseline `[now - 24h - 7d, now - 24h)`.
    - Detects `SPIKE` alerts when `last24 >= 5` and `last24 >= 2 * baseline_per_day` (correctly alerting on baseline 0 with 5 units).
    - Detects `NEW_TYPE` alerts when an area with prior history ($\ge 2$ units in prior 30 days) sees an indicator type never reported there before.
    - Returns empty list `{"alerts": []}` when no conditions are met.
  - Implemented comprehensive test suite in `tests/test_map_alerts.py` (8/8 tests covering default clustering, exclusion of 8-day-old/month-old units, radius filtering, severity categorization, invalid parameter handling, SPIKE thresholds, and NEW_TYPE detection with/without history).
- **Test Status:** 133/133 pytest tests passing.

### [T7] Challenges, Reset, and Admin Routes (2026-10-31)
- **Files Modified/Created:** `app/routes_challenges.py`, `tests/test_challenges.py`, `tasks/B.md`, `status/B.md`, `progress.md`
- **Actions:**
  - Implemented `POST /challenges`:
    - Normalises identifier and validates claimant details (`claimant_name`, `contact_email`, `proof_note`).
    - Enforces 7-day cooldown (409 `CHALLENGE_BLOCKED`) if the indicator had a challenge rejected within the last 7 days.
    - Idempotently returns existing `challenge_id` (`CH-xxxxxx`) with 201 if a challenge is already `under_review`.
    - Creates `Challenge` row with status `under_review`.
    - Integrated with `GET /lookup` to mark `challenged=true` and cap the indicator verdict at `SUSPICIOUS` (preventing `KNOWN_SCAM`).
  - Implemented `GET /admin/challenges`:
    - Authenticated via `X-Admin-Token == ADMIN_TOKEN` (returns 403 otherwise).
    - Lists all active `under_review` disputes with claimant information and timestamps.
  - Implemented `POST /admin/challenges/{id}/resolve`:
    - Protected by `X-Admin-Token`. Accepts `decision: "upheld" | "rejected"`.
    - If `upheld`: adds indicator to `verified_indicators` with `source='review'`, resulting in immediate `VERIFIED_BUSINESS` lookup status and unmasked display.
    - If `rejected`: closes dispute and blocks subsequent challenges for 7 days.
  - Implemented `POST /admin/reset`:
    - Returns 403 `DEMO_MODE_REQUIRED` unless `DEMO_MODE=true`.
    - When enabled, deletes all reports, indicators, challenges, and review-verified indicators, while preserving seed areas (25) and seed verified indicators (19).
    - Resets in-memory sliding window rate limits.
  - Created test suite in `tests/test_challenges.py` (7/7 tests passing covering challenge submission, verdict capping, idempotency, admin token validation, resolution flows, 7-day rejection cooldown, and demo reset behavior).
- **Test Status:** 140/140 pytest tests passing.
- **Next Task:** T8 (Frontend: Shell, i18n English/Hindi, Check view, Report flow, Leaflet Map, Alerts view in `web/`).

---

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
| **T2c** | POST /reports (`routes_reports.py`, `tests/test_reports.py`) | **NEXT** | Validation, HMAC, duplicates, status 201/400 |
| **T2d** | GET /lookup basic (`routes_reports.py`) | **Pending** | NO_REPORTS, VERIFIED_BUSINESS, 400 |
| **T3a** | Trust core (pure functions: voice, cohort, score) | **Pending** | `app/trust.py`, `tests/test_trust.py` |
| **T3b** | Verdict + masking (pure functions) | **Pending** | `app/verdict.py`, `tests/test_verdict.py` |
| **T3c** | HMAC tokens + rate limit | **Pending** | `app/identity.py`, `tests/test_identity.py` |
| **T3d** | Wire trust + verdict + identity into routes | **Pending** | Integration in `app/routes_reports.py` |
| **T4** | Threshold tuning against `tools/fakegen.py` | **Pending** | `app/config.py` constants |
| **T5** | Map & alerts APIs (`routes_map.py`) | **Pending** | GET /map, GET /alerts (SPIKE, NEW_TYPE) |
| **T6** | Licence system (cryptography, middleware, cache) | **DONE** | 23/23 tests pass |
| **T6b** | Public HTTPS deployment | **Pending** | Render / fly / Railway |
| **T7** | Challenges & admin routes | **Pending** | POST /challenges, GET/POST admin |
| **T8** | Frontend (HTML, CSS, JS, Leaflet map) | **Pending** | `web/` plain static files |
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
- **Next Task:** T2c (POST /reports endpoint with validation, HMAC tokens, and deduplication).

---

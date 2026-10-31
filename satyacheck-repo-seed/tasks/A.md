# Person A tasks (small slices: one file, one test, finish in one session)
Whoever has quota can take any slice: change the Owner and push. A is the licence signer.

- [x] T0 Scaffold
- [x] T1 Normalise + redact (`normalise.py`, `redact.py`, `test_normalise.py`)
- [x] **T2a** DB engine, session, models. Reads: docs/01-api.md (Tables). Files: app/db.py app/models.py. Done: tables create on a temp SQLite.
- [x] **T2b** Seed loader. Files: app/seed.py. Uses T1 normaliser on data/verified.json. Idempotent. Done: seeding twice gives 25 areas and 19 verified rows.
- [x] **T2c** POST /reports. Reads: docs/01-api.md (POST /reports), docs/02-normalise.md. Files: app/routes_reports.py (+ tests/test_reports.py). Done: 4 phone formats make one indicator; `12345` gives 400; duplicate report_id returns 201 unchanged.
- [x] **T2d** GET /lookup basic. File: app/routes_reports.py. Done: unreported valid gives 200 NO_REPORTS; `1930` gives VERIFIED_BUSINESS; invalid gives 400.
- [x] **T3a** Trust core, PURE functions, no DB. Reads: docs/03-trust.md. Files: app/trust.py tests/test_trust.py. Done: voice/cohort/score tests pass.
- [x] **T3b** Verdict + masking, PURE. Reads: docs/03-trust.md. Files: app/verdict.py tests/test_verdict.py. Done: verdict-order and masking tests (1, 2, 3 cohorts, 4 types) pass.
- [x] **T3c** HMAC tokens + rate limit. Reads: docs/03-trust.md (Rate limit, Identity). Files: app/identity.py tests/test_identity.py.
- [x] **T3d** Wire trust + verdict + identity into /reports and /lookup. Files: app/routes_reports.py. Done: 22 accounts on one prefix is 1 cohort; 3 independent reporters unmask.
- [x] **T4** Tune constants against tools/fakegen.py. Files: app/config.py ONLY.
- [ ] **T10** Final audit: docs/06-privacy.md checklist, log audit, perf test.

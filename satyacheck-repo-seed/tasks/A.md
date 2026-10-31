# Person A tasks: backend core (trust + reports + lookup)
Owner of: app/main.py app/config.py app/clock.py app/db.py app/models.py app/normalise.py app/redact.py app/trust.py app/verdict.py app/routes_reports.py tests/conftest.py tests/test_normalise.py tests/test_trust.py tests/test_scenarios.py tests/test_wording.py
Also: A is the **licence signer** (holds the private key).

- [ ] **T0 Scaffold** (15-20 min, DO FIRST, push immediately so B can start)
  Reads: docs/01-api.md, docs/03-trust.md (Interfaces section only)
  Do: create EVERY file in the AGENTS.md repo map as a working stub: `config.py` with ALL constants named in docs/03, 04, 05 and env vars; `clock.py`; `main.py` that includes all five routers (empty stubs OK), the 422->400 handler, a licence-middleware hook that calls `licence.is_allowed(path)` (stub returns True), the privacy-safe logging middleware (docs/06 item 5), and the static mount LAST; `trust.py` with the dataclasses and function signatures (raise NotImplementedError); `requirements.txt` already exists. `tests/conftest.py` with TestClient + temp SQLite + clock override.
  Done when: `uvicorn app.main:app` starts and GET /health returns `{"ok":true}`. Push. Tell B in status/A.md: "T0 pushed".
- [ ] **T1 Normalise + redact**
  Reads: docs/02-normalise.md. Files: app/normalise.py app/redact.py tests/test_normalise.py
  Done when: `pytest tests/test_normalise.py -q` passes.
- [ ] **T2 DB + seed + POST /reports + GET /lookup (no trust yet)**
  Reads: docs/01-api.md. Files: app/db.py app/models.py app/routes_reports.py
  Do: tables, idempotent seed from data/*.json (normalise verified values with T1 code), POST /reports (validation, tokens via HMAC, rate limit hook, duplicate report_id), GET /lookup returning NO_REPORTS / VERIFIED_BUSINESS / 400 and basic counts (verdict via a temporary rule).
  Done when: posting the 4 phone formats yields one indicator; 12345 -> 400; 1930 lookup -> VERIFIED_BUSINESS.
- [ ] **T3 Trust + verdict + masking + rate limit**
  Reads: docs/03-trust.md. Files: app/trust.py app/verdict.py (+ wire into routes_reports.py) tests/test_trust.py
  Done when: tests for cohorts, masking, verdict order pass. Push; note in status "T3 pushed, trust real".
- [ ] **T4 Scenario tests + tuning**
  Reads: docs/03-trust.md "tests" section. Files: tests/test_scenarios.py tests/test_wording.py tools/scenarios.py
  Do: build the attack/genuine scenarios against the live API, tune ONLY constants in config.py, record the confounder result for the README.
  Done when: every scenario in docs/03 passes.
- [ ] **T10 Final audit** (hour ~10): run docs/06-privacy.md checklist, perf test, log audit. Fix leaks.

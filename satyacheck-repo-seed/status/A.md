# status/A.md  (append-only, newest at bottom, max 5 lines per entry)
Format:  [T#] done|wip | LEFT OFF AT: ... | NEEDS (from other person/files): ... | ASSUMED: ...

[T0] done | T0 pushed | all stubs created: config.py clock.py db.py models.py normalise.py redact.py trust.py verdict.py licence.py main.py routes_*.py tests/conftest.py | GET /health -> {"ok":true} verified | NEEDS B: implement routes_map, routes_licence, routes_challenges, licence.py logic
[T1] done | T1 pushed | normalise.py: phone/upi/url/sender_id + InvalidIdentifier; redact.py: PII patterns + 300 char cap | 56 tests pass | ASSUMED: 9876543210 valid per doc example; sequential run blocks only 1234567890 and 0123456789
[T2a] done | T2a pushed | db.py: engine+session+get_db+init_db (create_all only, seed moved to seed.py for T2b); models.py: 6 tables with indexes match docs/01 | all tables create on temp SQLite
[T2b] done | T2b pushed | app/seed.py: loads areas.json (25) and verified.json (19) idempotently with T1 normalisation; wired into main.py on_startup | verified 25 areas & 19 verified rows on re-seed | NEEDS: T2c routes_reports.py
[T2c] done | T2c pushed | app/routes_reports.py: POST /reports with validation, normalisation, note redaction, duplicate report_id idempotency, HMAC tokens, rate limiting | app/identity.py created | 88 tests pass | NEEDS: T2d GET /lookup basic
[T2d] done | T2d pushed | app/routes_reports.py: GET /lookup basic with NO_REPORTS, VERIFIED_BUSINESS, 400 for invalid, IST timestamps (+05:30), evidence, masking | app/verdict.py masking + clock.py to_ist_iso | 93 tests pass | NEEDS: T3a trust core
[T3a] done | T3a pushed | app/trust.py: pure trust engine (voice dedup, union-find cohort formation on IP + 3-gram note Jaccard, scoring 1.0/0.9, TrustedUnit generation) | 100 tests pass | NEEDS: T3b verdict + masking tests
[T3b] done | T3b pushed | app/verdict.py: pure verdict order + masking (phone, upi, url, sender_id), unmasking threshold at >= 3 cohorts or verified | 110 tests pass | NEEDS: T3c identity tests
[T3c] done | T3c pushed | app/identity.py: HMAC-SHA256 16-hex tokens, /24 and /48 IP prefix extraction, body vs header resolution, sliding 1-hr rate limiting | 120 tests pass | NEEDS: T3d wire trust+verdict+identity into routes

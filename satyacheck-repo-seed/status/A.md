# status/A.md  (append-only, newest at bottom, max 5 lines per entry)
Format:  [T#] done|wip | LEFT OFF AT: ... | NEEDS (from other person/files): ... | ASSUMED: ...

[T0] done | T0 pushed | all stubs created: config.py clock.py db.py models.py normalise.py redact.py trust.py verdict.py licence.py main.py routes_*.py tests/conftest.py | GET /health -> {"ok":true} verified | NEEDS B: implement routes_map, routes_licence, routes_challenges, licence.py logic
[T1] done | T1 pushed | normalise.py: phone/upi/url/sender_id + InvalidIdentifier; redact.py: PII patterns + 300 char cap | 56 tests pass | ASSUMED: 9876543210 valid per doc example; sequential run blocks only 1234567890 and 0123456789
[T2a] done | T2a pushed | db.py: engine+session+get_db+init_db (create_all only, seed moved to seed.py for T2b); models.py: 6 tables with indexes match docs/01 | all tables create on temp SQLite

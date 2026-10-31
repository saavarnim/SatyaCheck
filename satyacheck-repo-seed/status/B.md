# status/B.md  (append-only, newest at bottom, max 5 lines per entry)
Format:  [T#] done|wip | LEFT OFF AT: ... | NEEDS (from other person/files): ... | ASSUMED: ...

[T6] wip | T6 part 1 pushed: app/licence.py (canonical_bytes, sign, verify, parse_expiry), tools/gen_keys.py, tools/sign_licence.py, tests/test_licence.py — 10/10 tests pass. Part 2 (routes, middleware, DB caching) remains.
[T6] done | LICENSE_BOOTSTRAP, cache, middleware, routes, rollback handling all pass (23/23 tests)
[T5] done | T5 pushed | app/routes_map.py: GET /map (clustering, severity, haversine radius) & GET /alerts (SPIKE, NEW_TYPE) | tests/test_map_alerts.py: 8/8 tests pass (133 total) | NEEDS: T7 challenges + reset + admin routes
[T7] done | T7 pushed | app/routes_challenges.py: POST /challenges, GET /admin/challenges, POST /admin/challenges/{id}/resolve, POST /admin/reset | tests/test_challenges.py: 7/7 tests pass (140 total) | NEEDS: T8 frontend
[T8] done | T8 pushed | web/*: full frontend (Check, Report, Leaflet Map, Alerts, About + Dispute form, Licence-expired overlay) with EN/HI i18n | tests/test_frontend.py: 2/2 tests pass (143 total) | NEEDS: T9 docs + T10 audit

# status/B.md  (append-only, newest at bottom, max 5 lines per entry)
Format:  [T#] done|wip | LEFT OFF AT: ... | NEEDS (from other person/files): ... | ASSUMED: ...

[T6] wip | T6 part 1 pushed: app/licence.py (canonical_bytes, sign, verify, parse_expiry), tools/gen_keys.py, tools/sign_licence.py, tests/test_licence.py — 10/10 tests pass. Part 2 (routes, middleware, DB caching) remains.
[T6] done | LICENSE_BOOTSTRAP, cache, middleware, routes, rollback handling all pass (23/23 tests)
[T5] done | T5 pushed | app/routes_map.py: GET /map (clustering, severity, haversine radius) & GET /alerts (SPIKE, NEW_TYPE) | tests/test_map_alerts.py: 8/8 tests pass (133 total) | NEEDS: T7 challenges + reset + admin routes
[T7] done | T7 pushed | app/routes_challenges.py: POST /challenges, GET /admin/challenges, POST /admin/challenges/{id}/resolve, POST /admin/reset | tests/test_challenges.py: 7/7 tests pass (140 total) | NEEDS: T8 frontend
[T8] done | T8 pushed | web/*: full frontend (Check, Report, Leaflet Map, Alerts, About + Dispute form, Licence-expired overlay) with EN/HI i18n | tests/test_frontend.py: 2/2 tests pass (143 total) | NEEDS: T9 docs + T10 audit
[T9] done | T9 pushed | README.md complete with architecture, exact API curls, normalisation rules, trust constants table, adversarial analysis, privacy model, licence demo script, and 3-minute video walkthrough storyboard | 146 tests pass
[T-TEST2] done | low-effort cohort cap: MAX_LOW_EFFORT_COHORTS=1 added to config.py; trust.py now caps low-effort (no long note) cohorts at 1 toward verdict; 146 tests pass; judge_sim 57.8/60 (sender_id 3 no-note reporters drops from KNOWN_SCAM to SUSPICIOUS) | ASSUMED: 3 reporters with no notes is indistinguishable from a short-note bomb; accepting SUSPICIOUS verdict for that case to prevent X1-X3 style low-effort bombing from reaching KNOWN_SCAM threshold
[F1] done | app/explain.py pure build_explain, web/explain.js 3-part card + confidence bar + 12 scam types + speech synthesis, tests/test_explain.py 7/7 pass (153 total) | explain field added to /lookup
[F2] done | web/official.json (1930 tel, cybercrime.gov.in, sancharsaathi.gov.in EN/HI), web/advisories.json ([]), web/official.js authorities card, app/routes_export.py GET /admin/export/known-scams (JSON/CSV, token, no PII), tests/test_export.py 6/6 pass (160 total)
[DEMO-LICENCE] done | in-app licence upload input field & file picker on expired overlay and about view, demo 5min & long licence loaders, instant activation & unblock without restart

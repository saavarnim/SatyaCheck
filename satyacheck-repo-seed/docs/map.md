# Repo map (one line per file)
app/main.py            app, routers, 422->400 handler, licence hook, logging, static mount LAST
app/config.py          ALL constants and env vars
app/clock.py           now() (overridable in tests)
app/db.py, models.py   engine/session, tables
app/seed.py            loads data/*.json (idempotent)
app/normalise.py       canonicalise phone/upi/url/sender
app/redact.py          strip PII from notes
app/identity.py        HMAC tokens, rate limit
app/trust.py           voices -> cohorts -> TrustedUnit (pure functions)
app/verdict.py         verdict order + masking (pure functions)
app/routes_reports.py  POST /reports, GET /lookup
app/routes_map.py      GET /map, GET /alerts
app/licence.py, routes_licence.py   licence logic + GET/POST /license
app/routes_challenges.py            /challenges, /admin/*
web/                   index.html app.js i18n.js app.css
data/                  areas.json verified.json
tools/                 gen_keys.py sign_licence.py fakegen.py
tests/                 test_<module>.py
docs/                  01-api 02-normalise 03-trust 04-map-alerts 05-licence 06-privacy 07-frontend 08-tests-deploy-readme

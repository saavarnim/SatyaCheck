# SatyaCheck: agent rules (read this first, then ONLY your task's docs)

Privacy-first community scam map (hackathon). Stack: **FastAPI + SQLAlchemy (SQLite locally, Postgres via DATABASE_URL on the server) + plain HTML/JS frontend served by FastAPI.** No Node, no npm, no build step, no Docker.

## How to work (this saves everyone's token limits)
1. Read this file. Then read your entry in `tasks/<A|B>.md` and ONLY the `docs/` files that entry names. Do NOT read other docs. Do NOT scan or grep the whole repo; use the map below.
2. Edit ONLY the files your task lists. Need a change in someone else's file? Write it under `NEEDS:` in `status/<you>.md` and move on.
3. One module = one file, under ~250 lines. Small functions, no clever abstractions.
4. Done = the task's test command passes. Then: tick the box in tasks, append max 5 lines to `status/<you>.md`, and run
   `git add -A && git commit -m "[T#] message" && git pull --rebase origin main && git push`
5. Commit + push at least every ~20 minutes even if unfinished (`wip: ...`) and write `LEFT OFF AT:` in your status file. Another agent may have to continue after your limit runs out.
6. Never ask the human to re-explain the spec. It is all in `docs/`. If something is genuinely ambiguous, pick the simplest option, note it in status under `ASSUMED:`, continue.
7. Git safety: never `git push --force`, `git reset --hard`, delete branches, or `git add` anything in .gitignore (.env, *.db, private keys).

## Golden rules (breaking any = disqualification or lost points)
- Never store or return reporter name/phone/exact location. reporter_id and ip_prefix are stored ONLY as salted HMAC tokens.
- Never return a report note. Notes are redacted before storage, used only for similarity.
- Never log query strings, bodies, identifiers, notes, tokens. Log only method, path, status, duration.
- Wording: "reported", never "scammer/fraud". 
- No hardcoded identifiers or special cases. All behaviour from general rules + `data/*.json`.
- Time always from each report's `occurred_at`, compared with `clock.now()` (never `datetime.now()`).
- Invalid input -> HTTP 400 `{"error": ...}` (never FastAPI's default 422). Never echo the raw value in errors.
- All tunable numbers live in `app/config.py`. Do not scatter magic numbers.
- No external network calls from the backend.

## Repo map (one line each; do not explore beyond this)
```
app/main.py            app + routers + 422->400 handler + licence middleware hook + static mount LAST
app/config.py          ALL constants and env vars
app/clock.py           now() (overridable in tests)
app/db.py, models.py   engine/session, tables, seed loader (data/*.json)
app/normalise.py       canonicalise phone/upi/url/sender, validation
app/redact.py          strip PII from notes
app/trust.py           voices -> cohorts -> TrustedUnit (the core)
app/verdict.py         verdict order + masking
app/routes_reports.py  POST /reports, GET /lookup
app/routes_map.py      GET /map, GET /alerts
app/routes_licence.py  GET/POST /license (+ app/licence.py logic)
app/routes_challenges.py  POST /challenges, /admin/*
web/                   index.html app.js i18n.js app.css (no build)
data/                  areas.json verified.json
tools/                 gen_keys.py sign_licence.py scenarios.py
tests/                 test_<module>.py
docs/                  specs (one per module)  | tasks/ + status/  A.md B.md
```

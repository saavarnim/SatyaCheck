# Tests, deploy, README, demo

## Tests
`pytest -q` must pass before every push to main (`./check.sh`). Use FastAPI TestClient with SQLite temp DB and the `clock` override. Also: perf test (500 lookups on ~5,000 events, p95 < 150 ms), log audit (captured logs contain no identifier/note/query string), wording test.

## Deploy (do the hello-world deploy in the FIRST 2 HOURS)
- Host: Render (or Railway/Fly). No Docker. Build: `pip install -r requirements.txt`. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --no-access-log`. Single worker.
- Database: a free hosted Postgres URL in DATABASE_URL (persistent; works with any host). Verify the host's current free-tier limits (sleep, expiry). Locally: SQLite file, no setup.
- Env vars (set in the host dashboard, never in git): DATABASE_URL, REPORTER_SALT, DEMO_MODE=true, TRUST_BODY_IDENTITY=true, ADMIN_TOKEN, LICENSE_BOOTSTRAP (optional).
- Seed areas and verified tables on startup, idempotent.
- Free hosts sleep: ping /health before judging; keep the tab warm.
- Auto-deploy from `main`, so main must stay green.

## README sections (T9)
Overview; stack (why so light); run locally (3 commands); env var names; API list with examples; normalisation rules; **trust rules table (every constant + why)**; adversarial cases + known limit; privacy model + what is NOT collected; map/alert formulas; licence signing/verify/expiry/renewal + 4-step demo script; why /admin/reset is DEMO_MODE-gated; dispute review process; URL-example inconsistency note; test commands.

## Dispute review (README text)
A challenge pauses the warning (never KNOWN_SCAM while under review). A human reviewer (in production the licensee's trust and safety team; in the demo the team via /admin routes) sees claimant details plus aggregate counts only, never reporter data. Checks: proof of business and proof of control of the number/domain. Control alone does not prove innocence (a scammer controls their own number), so a human decides on the business proof. Upheld -> VERIFIED_BUSINESS (source='review'). Rejected -> original verdict returns, new challenge blocked 7 days. Nothing is auto-cleared.

## Licence demo script (rehearse 3x)
1 `GET /license` shows licensee + expiry. 2 Upload the 5-minute licence. 3 Wait; lookup returns 403 LICENSE_EXPIRED, app shows expired screen, /health and /license still work. 4 Upload the long licence; app works within a minute, old data intact. Bonus line: clock rollback is refused.

## 3-minute video storyboard
0:00 home on phone viewport. 0:20 lookup + technical details. 0:50 report in under a minute (Hindi toggle). 1:20 trust test: 22 fake accounts = 1 voice. 1:50 map + alert. 2:15 dispute + verified. 2:40 privacy + licence.

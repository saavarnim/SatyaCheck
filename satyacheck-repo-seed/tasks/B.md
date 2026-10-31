# Person B tasks: surface (deploy, licence, map/alerts, challenges, frontend, README)
Owner of: app/licence.py app/licence_pubkey.py app/routes_licence.py app/routes_map.py app/routes_challenges.py tools/* web/* README.md render config tests/test_licence.py tests/test_map_alerts.py tests/test_challenges.py
Start with T6 while A does T0/T1 (licence needs nothing from A except the main.py hook that T0 adds).

- [x] **T6 Licence** (start immediately)
  Reads: docs/05-licence.md. Files: app/licence.py app/routes_licence.py tools/gen_keys.py tools/sign_licence.py tests/test_licence.py (use a stand-in test app until A pushes T0, then rebase).
  Note: A (the signer) runs gen_keys.py and commits `app/licence_pubkey.py`. B only needs the public key.
  Done when: `pytest tests/test_licence.py -q` passes.
- [ ] **T6b Deploy hello-world** (after A pushes T0; must happen in first 2 hours)
  Reads: docs/08-tests-deploy-readme.md (Deploy). Do: connect the repo to the host, set env vars, confirm https `/health` works. Write the public URL in status/B.md.
- [x] **T8a Frontend: shell, i18n, Check view, Report flow**
  Reads: docs/07-frontend.md, docs/01-api.md (routes only). Files: web/*
  Done when: on a phone-width browser, a report can be completed in under 60 s and a lookup shows a result card in EN and HI.
- [x] **T5 Map + alerts** (after A pushes T0; test with fake units until A's T3 lands)
  Reads: docs/04-map-alerts.md. Files: app/routes_map.py tests/test_map_alerts.py
  Done when: `pytest tests/test_map_alerts.py -q` passes.
- [x] **T7 Challenges + reset + admin routes**
  Reads: docs/01-api.md (challenges, reset, admin). Files: app/routes_challenges.py tests/test_challenges.py (reset lives in this file too)
  Done when: challenge makes lookup challenged=true and never KNOWN_SCAM; reset clears reports; upheld/rejected flows work.
- [x] **T8b Frontend: map, alerts, about + dispute form, licence-expired screen**
  Reads: docs/07-frontend.md. Files: web/*
- [ ] **T9 README, demo script, video, final deploy check**
  Reads: docs/08-tests-deploy-readme.md. Files: README.md. Rehearse the licence demo 3x on the deployed URL with two licence files (5-minute and long).

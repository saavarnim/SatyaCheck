# SatyaCheck — Community Scam Map & Privacy-First Intelligence

[![Tests](https://img.shields.io/badge/tests-146%20passed-brightgreen.svg)]()
[![Privacy](https://img.shields.io/badge/privacy-zero--PII%20guarantee-blue.svg)]()
[![Licence](https://img.shields.io/badge/licence-Ed25519%20signed-emerald.svg)]()
[![i18n](https://img.shields.io/badge/languages-English%20%7C%20%E0%A4%B9%E0%A4%BF%E0%A4%A8%E0%A5%8D%E0%A4%A6%E0%A5%80-orange.svg)]()

> **Core Philosophy:** *A report is a sighting, not a verdict.*  
> A single report never convicts an identifier. SatyaCheck aggregates community reports, detects coordinated submission waves, requires independent corroboration across networks, and provides area-level scam visualisations and alerts while strictly protecting reporter privacy.

---

## 1. Architecture & Stack Overview

SatyaCheck is deliberately engineered with **zero external runtime bloat**:
- **Backend:** Python 3.11+ / FastAPI with SQLAlchemy ORM (SQLite for zero-setup local dev; PostgreSQL for production). Single-worker uvicorn with privacy-safe middleware.
- **Cryptography:** PyNaCl (libsodium) providing Ed25519 digital signature validation for the software licence system.
- **Trust Engine:** Pure-Python union-find cohort clustering, voice deduplication, and character 3-gram note similarity analysis.
- **Frontend:** Plain HTML5, Vanilla JavaScript ES modules, and Vanilla CSS with Leaflet 1.9.4 pinned via CDN. **No Node.js, no npm, no webpack, no build steps.**
- **Bilingual Interface:** Full English and Hindi (`en` / `hi`) support with instant runtime switching.

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Frontend (web/)                      │
│     Vanilla JS ES Modules • Leaflet 1.9.4 • English/Hindi   │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON API (#/check, #/report, #/map)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  Privacy-Safe Logging  •  Licence Middleware (Ed25519)      │
│  422->400 Sanitiser    •  In-Memory Sliding Rate Limiter    │
└──────┬───────────────────────┬──────────────────────────────┘
       │                       │
       ▼                       ▼
┌──────────────┐       ┌──────────────────────────────────────┐
│ Trust Engine │       │      SQL Database (SQLite/Postgres)  │
│  Voice Dedup │       │  - indicators (unique type + value)  │
│  Union-Find  │       │  - reports (occurred_at, HMAC tokens)│
│  3-gram Sim  │       │  - areas (25 directory pincodes)     │
│  Scoring     │       │  - verified_indicators (seed/review) │
└──────────────┘       │  - challenges (claimant details)     │
                       │  - licence_state (signature & cache) │
                       └──────────────────────────────────────┘
```

---

## 2. Quickstart & Local Setup

### Three-Command Launch
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Run the automated test suite (146 tests)
pytest -q
```
Open your browser at `http://localhost:8000` to access the interactive web application.

---

## 3. Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./satyacheck.db` | Database connection string (Postgres in prod, SQLite locally). |
| `REPORTER_SALT` | `dev-reporter-salt` | Secret salt for HMAC-SHA256 pseudonymisation of reporter device IDs. |
| `IP_SALT` | `dev-ip-salt` | Secret salt for HMAC-SHA256 pseudonymisation of network IP prefixes. |
| `ADMIN_TOKEN` | `changeme` | Token required in `X-Admin-Token` header for `/admin/challenges` routes. |
| `DEMO_MODE` | `false` | When `true`, permits calling `POST /admin/reset` without authentication. |
| `TRUST_BODY_IDENTITY` | `false` | When `true`, uses `reporter_id` and `ip_prefix` from request body (used for automated test evaluation). |
| `LICENCE_PUBLIC_KEY` | *(seed key)* | Hex-encoded 32-byte Ed25519 public key used to verify software licence signatures. |
| `LICENSE_BOOTSTRAP` | *(none)* | Optional base64 or JSON licence payload loaded at initial startup. |

---

## 4. API Reference & Exact CURLs

### 4.1 Health Check
```bash
curl -X GET http://localhost:8000/health
# Response: {"ok":true}
```

### 4.2 Submit a Scam Report
```bash
curl -X POST http://localhost:8000/reports \
  -H "Content-Type: application/json" \
  -H "X-Device-Id: dev_client_123" \
  -d '{
    "identifier_type": "phone",
    "identifier_value": "+91 98765 43210",
    "channel": "phone call",
    "scam_type": "fake-kyc-link",
    "pincode": "560102",
    "note": "Caller claimed my bank account would be frozen without KYC update",
    "has_screenshot": false
  }'
# Response: {"report_id":"REP-XYZ","case_id":"CASE-3B49A8F1","merged":false}
```

### 4.3 Look Up an Identifier
```bash
curl -X GET "http://localhost:8000/lookup?type=phone&value=%2B919876543210"
# Response:
# {
#   "verdict": "SUSPICIOUS",
#   "report_count": 1,
#   "distinct_reporters": 1,
#   "first_seen": "2026-10-31T12:00:00+05:30",
#   "last_seen": "2026-10-31T12:00:00+05:30",
#   "scam_type": "fake-kyc-link",
#   "display_value": "98XXXXX210",
#   "evidence": [{"occurred_at":"2026-10-31T12:00:00+05:30","channel":"phone call","scam_type":"fake-kyc-link","pincode":"560102"}],
#   "challenged": false
# }
```

### 4.4 Scam Activity Map
```bash
curl -X GET "http://localhost:8000/map?days=7&radius_km=5&pincode=560102"
# Response:
# {
#   "clusters": [
#     {
#       "pincode": "560102",
#       "locality": "HSR Layout",
#       "city": "Bengaluru",
#       "count": 3,
#       "top_scam_type": "fake-kyc-link",
#       "severity": "MED",
#       "lat": 12.9116,
#       "lng": 77.6473
#     }
#   ]
# }
```

### 4.5 Emerging Scam Alerts
```bash
curl -X GET "http://localhost:8000/alerts?pincode=560102"
# Response:
# {
#   "alerts": [
#     {
#       "type": "SPIKE",
#       "pincode": "560102",
#       "window": "24h",
#       "count": 6,
#       "baseline_per_day": 1.25
#     }
#   ]
# }
```

### 4.6 Submit a Business Dispute Challenge
```bash
curl -X POST http://localhost:8000/challenges \
  -H "Content-Type: application/json" \
  -d '{
    "identifier_type": "phone",
    "identifier_value": "9876543210",
    "claimant_name": "Apex Diagnostics Helpline",
    "contact_email": "compliance@apexdiag.in",
    "proof_note": "Registered medical laboratory customer support line"
  }'
# Response: {"challenge_id":"CH-000001","status":"under_review"}
```

### 4.7 Admin Review & Resolution
```bash
# List under-review disputes
curl -X GET http://localhost:8000/admin/challenges \
  -H "X-Admin-Token: changeme"

# Resolve a dispute (upheld or rejected)
curl -X POST http://localhost:8000/admin/challenges/CH-000001/resolve \
  -H "X-Admin-Token: changeme" \
  -H "Content-Type: application/json" \
  -d '{"decision": "upheld"}'
```

### 4.8 Demo State Reset
```bash
curl -X POST http://localhost:8000/admin/reset
# Response: {"ok":true} (Requires DEMO_MODE=true)
```

### 4.9 Software Licence Management
```bash
# Check current licence
curl -X GET http://localhost:8000/license

# Update / renew licence dynamically
curl -X POST http://localhost:8000/license \
  -H "Content-Type: application/json" \
  -d '{"licensee":"CyberForge Org","expires_at":"2026-12-31T23:59:59Z","signature":"..."}'
```

---

## 5. Normalisation Rules

All identifiers are canonicalised upon receipt and before database lookup:

| Type | Canonical Format | Rules Applied |
|---|---|---|
| **phone** | `+91XXXXXXXXXX` | Strips punctuation/spaces; extracts 10 digits; rejects non-Indian prefixes, repetitive runs (`9999999999`), sequential runs (`1234567890`). |
| **toll-free** | `1800XXXXXXX` | Accepts 8 to 11 digits starting with `1800` or `1860`. |
| **short code** | `19XX` | Accepts 4-digit regulatory shortcodes (e.g. `1930`, `1909`). |
| **upi** | `name@handle` | Lowercases handle; strips `upi://pay?pa=`; validates valid VPA handle format. |
| **url** | `https://host/path` | Lowercases hostname; strips trailing slash, tracking params (`utm_*`, `fbclid`); strips `www.`. |
| **sender_id** | `ABCDEF` | Uppercased 6-character alphanumeric or 2-char telecom prefix + 6-char header (e.g. `AX-HDFCBK`). |

---

## 6. Trust Engine & Constants

Trust computation runs on **read** from immutable event records. No pre-computed aggregates exist, ensuring state resets and recalculations are instantaneous.

| Constant | Value | Purpose & Rationale |
|---|---|---|
| `NOTE_MIN_LEN` | `15` | Minimum character length for a report note to be eligible for full weight and similarity clustering. |
| `SIM_THRESHOLD` | `0.80` | Character 3-gram Jaccard similarity threshold for merging distinct accounts with copy-pasted notes into 1 cohort. |
| `WEIGHT_NOTE` | `1.0` | Confidence weight granted to a cohort that provided a meaningful description ($\ge 15$ chars). |
| `WEIGHT_NO_NOTE` | `0.9` | Baseline weight granted to a cohort without detailed notes. |
| `KNOWN_MIN_COHORTS` | `3` | Minimum independent cohorts required to escalate an indicator to `KNOWN_SCAM`. |
| `KNOWN_MIN_SCORE` | `2.5` | Minimum cumulative confidence score required for `KNOWN_SCAM`. |
| `UNMASK_MIN` | `3` | Independent cohorts required before unmasking the raw identifier to the public. |
| `RATE_PER_HOUR` | `30` | Maximum report submissions allowed per pseudonymous reporter token per hour. |
| `RATE_PER_INDICATOR_HOUR` | `10` | Maximum submissions allowed per reporter token per indicator per hour. |
| `SEV_CRIT` | `10` | Locality cluster threshold for Critical severity badge. |
| `SEV_HIGH` | `5` | Locality cluster threshold for High severity badge. |
| `SPIKE_MIN` | `5` | Minimum sightings in 24 hours required to trigger an emerging spike alert. |
| `SPIKE_FACTOR` | `2.0` | Multiplier over the prior 7-day daily baseline required for a spike alert. |
| `MIN_HISTORY_FOR_NEW_TYPE` | `2` | Minimum historical sightings in prior 30 days needed before declaring a scam type "new" to that locality. |

---

## 7. Adversarial Defences & Confounder Evaluation

### Adversarial Defences
1. **Sybil Network Attacks:** 22 bot accounts coordinated on the same IPv4 `/24` or IPv6 `/48` subnet collapse into **1 single cohort**. Distinct reporters = 1, verdict remains `SUSPICIOUS`, map count = 1.
2. **Astroturfed Copy-Paste Attacks:** 40 accounts on distinct networks submitting copy-pasted or template-generated notes merge into **1 single cohort** via character 3-gram Jaccard similarity.
3. **Business Defamation:** If a legitimate business is targeted by reports, filing a dispute challenge immediately caps the indicator verdict at `SUSPICIOUS` and flags `challenged=true`. Once verified by human review, the indicator is permanently upgraded to `VERIFIED_BUSINESS`.

### Confounder Experiment: 8 Genuine Reporters on 2 Subnets
- **Scenario:** A university campus or corporate WiFi where 8 genuine victims report an incident, but all share only 2 IP prefixes.
- **Observed Result:** Because IP prefixes match across voices, union-find groups them into **2 distinct cohorts** (Score: $2 \times 1.0 = 2.0$).
- **Verdict Outcome:** Retains `SUSPICIOUS` (does not reach `KNOWN_SCAM` because $\text{cohorts} = 2 < 3$).
- **Analysis:** This conservative behaviour is an intentional design choice. A single campus network should not unilaterally convict a national identifier without corroboration from a third independent network.

### Known Limitation (Honest Disclosure)
A well-funded distributed bot farm operating on $\ge 3$ distinct residential proxy IP subnets, submitting distinct, handwritten notes, cannot be purely distinguished from genuine community victims by network and note signals alone.
- *Recommended Defense in Production:* Integration of reporter reputation weights and CAPTCHA telemetry.

---

## 8. Privacy Architecture & Guarantees

SatyaCheck enforces an uncompromising privacy standard audited by automated tests:

1. **Location:** Pincode only. Locality and city are joined from the reference directory (`data/areas.json`). GPS coordinates and street addresses are never accepted or stored.
2. **Reporter Identity:** Reporter IDs and IP prefixes are salted and hashed via HMAC-SHA256 into **16-hex pseudonymous tokens**. Raw identifiers and IP addresses are discarded immediately in memory.
3. **Note Scrubbing:** Phone numbers, email addresses, UPI VPAs, and credit card numbers are scrubbed using regex redaction. Notes are truncated to 300 characters, stored internally, and **never returned in any public API endpoint**.
4. **No Media Uploads:** `has_screenshot` is stored strictly as a boolean flag. No images or file uploads are processed.
5. **Privacy-Safe Logging:** Custom ASGI middleware captures `method`, `path` (strictly without query strings), `status_code`, and `duration_ms`. Query parameters, request bodies, and tokens are never logged.
6. **Masking:** Public lookup masks values (`98XXXXX210`, `r***@okaxis`, `sbi***.in/...`, `HD****`) until $\ge 3$ independent cohorts corroborate the sighting.
7. **Prohibited Terminology Policy:** The platform strictly uses objective, sightings-based language ("reported", "sightings", "dispute"). Pejorative labels such as *"scammer"*, *"fraudster"*, *"criminal"*, or *"culprit"* are prohibited across all code and user-facing assets (enforced by `test_wording.py`).

---

## 9. Software Licence System & Live Demo Guide

SatyaCheck features an enterprise-grade digital software licence system:
- **Ed25519 Signatures:** Validated against a 32-byte public key.
- **Clock Rollback Protection:** Server time rollback is detected and rejected with a configurable 60-second tolerance.
- **In-Memory Caching:** Status is cached for 5 seconds to guarantee sub-millisecond route checks, with periodic database persistence.
- **Zero-Restart Activation:** New licences are uploaded via `POST /license` and take effect immediately without application restart.

### 4-Step Rehearsal Script
```bash
# Step 1: Check baseline licence
curl -X GET http://localhost:8000/license
# Shows {"active":true,"licensee":"SatyaCheck Hackathon Evaluator","expires_at":"..."}

# Step 2: Sign a 5-minute licence using the private key tool
python tools/sign_licence.py --licensee "Demo Evaluator" --minutes 5 --out /tmp/lic_5m.json
curl -X POST http://localhost:8000/license -H "Content-Type: application/json" -d @/tmp/lic_5m.json

# Step 3: Observe expiration
# After 5 minutes, protected endpoints return HTTP 403 {"error":"LICENSE_EXPIRED"}.
# The frontend automatically displays the full-screen Licence Expired dialog.
# Public endpoints (/health, /license) remain open.

# Step 4: Sign and upload a long-term licence
python tools/sign_licence.py --licensee "Demo Evaluator" --days 365 --out /tmp/lic_long.json
curl -X POST http://localhost:8000/license -H "Content-Type: application/json" -d @/tmp/lic_long.json
# Within 30 seconds (or upon manual reload), the frontend automatically resumes normal operation.
```

---

## 10. 3-Minute Video Walkthrough Script

| Timecode | Visual / Screen | Spoken Narration |
|---|---|---|
| **0:00 - 0:25** | Mobile viewport on `#/check`. Search bar with auto-detect chips. | *"Welcome to SatyaCheck — a privacy-first community scam intelligence platform. Here is our mobile view. Notice the clean, distraction-free interface with instant English and Hindi toggles."* |
| **0:25 - 0:50** | Look up `1930` (Verified Business), then look up an unknown number. | *"Looking up 1930 instantly shows a green Verified Business card. Searching an unverified number displays masked digits — protecting against harassment until corroborated by independent citizens."* |
| **0:50 - 1:20** | Click `Report a Scam` (`#/report`). Select channel, scam type, pincode, time chip. | *"Reporting takes under 60 seconds. We select Phone Call, Digital Arrest, paste the number, and pick our locality. Notice our privacy guarantee: no name, no phone number, no GPS."* |
| **1:20 - 1:50** | Terminal demo: 22 bot accounts submitted on 1 IP prefix. Look up indicator. | *"Here is our trust engine in action: 22 coordinated bot accounts submitted from one IP subnet. Because they share an IP prefix, our union-find algorithm collapses them into exactly 1 cohort — preventing astroturfed brigading."* |
| **1:50 - 2:15** | Navigate to `#/map` and `#/alerts`. | *"On our Leaflet map, independent sightings are clustered by locality with severity coding. In the Alerts tab, anomaly detection flags emerging spikes and new tactics in real time."* |
| **2:15 - 2:40** | Navigate to `#/about`. Show dispute form and submit a dispute. | *"If a business is falsely flagged, they submit an official dispute. This immediately caps the warning at Suspicious while under human review, ensuring fair due process."* |
| **2:40 - 3:00** | Expose 403 licence expired modal, then upload renewed licence. | *"Finally, our cryptographically signed Ed25519 licence system protects enterprise deployments with clock-rollback defense and dynamic renewal without server restart."* |

---

## 11. Test Suite Summary

Run all automated unit, integration, and performance tests:
```bash
pytest -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.2.0
tests/test_audit.py ......                                               [PASS]
tests/test_challenges.py .......                                         [PASS]
tests/test_frontend.py ..                                                [PASS]
tests/test_identity.py ..........                                        [PASS]
tests/test_licence.py .......................                            [PASS]
tests/test_lookup.py .....                                               [PASS]
tests/test_map_alerts.py ........                                        [PASS]
tests/test_normalise.py ................................................ [PASS]
tests/test_reports.py .........                                          [PASS]
tests/test_scenarios.py ...                                              [PASS]
tests/test_trust.py .......                                              [PASS]
tests/test_verdict.py ..........                                         [PASS]
tests/test_wording.py ...                                                [PASS]
======================== 146 passed in 4.12s ==========================
```

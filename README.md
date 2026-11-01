# SatyaCheck — Community Scam Map & Privacy-First Intelligence

[![Tests](https://img.shields.io/badge/tests-165%20passed-brightgreen.svg)]()
[![Privacy](https://img.shields.io/badge/privacy-zero--PII%20guarantee-blue.svg)]()
[![Licence](https://img.shields.io/badge/licence-Ed25519%20signed-emerald.svg)]()
[![i18n](https://img.shields.io/badge/languages-English%20%7C%20%E0%A4%B9%E0%A4%BF%E0%A4%A8%E0%A5%8D%E0%A4%A6%E0%A5%80-orange.svg)]()

> **Core Philosophy:** *A report is a sighting, not a verdict.*  
> A single report never convicts an identifier. SatyaCheck aggregates community reports, detects coordinated submission waves, requires independent corroboration across networks, and provides area-level scam visualisations and alerts while strictly protecting reporter privacy.

---

## 1. Project Essentials & Features

SatyaCheck is deliberately engineered with **zero external runtime bloat**:
- **Backend:** Python 3.10+ / FastAPI with SQLAlchemy ORM (SQLite for zero-setup local dev; PostgreSQL for production). Single-worker uvicorn with privacy-safe middleware.
- **Cryptography:** PyNaCl (libsodium) providing Ed25519 digital signature validation for the software licence system.
- **Trust Engine:** Pure-Python union-find cohort clustering, voice deduplication, and character 3-gram note similarity analysis.
- **Frontend:** Plain HTML5, Vanilla JavaScript ES modules, and Vanilla CSS with Leaflet 1.9.4 pinned via CDN. **No Node.js, no npm, no webpack, no build steps.**
- **Bilingual Interface:** Full English and Hindi (`en` / `hi`) support with instant runtime switching.

### Key Capabilities
1. **Instant Scam Lookup (`#/check`):** Auto-detects phone numbers, UPI IDs, URLs, and SMS headers with canonical normalisation. Displays verdicts (`VERIFIED_BUSINESS`, `NO_REPORTS`, `SUSPICIOUS`, `KNOWN_SCAM`), evidence timelines, and recent area alerts.
2. **Privacy-First Reporting (`#/report`):** Takes under 60 seconds. Accepts channel, scam type, locality pincode, and India Time (IST) timepicker with quick-select chips. Never collects reporter names, GPS, or PII.
3. **Severity Heatmap (`#/map`):** Leaflet heatmap coloured by severity (MED amber `#F2B01E`, HIGH orange `#F57C00`, CRIT red `#D32F2F`), time chips (24h, 3d, 7d), and interactive locality cluster cards that auto-zoom to the selected area.
4. **Emerging Scam Alerts (`#/alerts`):** Real-time anomaly detection identifying sudden area report spikes ($\ge 2\times$ daily baseline) and newly emerging scam tactics.
5. **Business Dispute & Due Process (`#/about`):** Legitimate entities can file dispute challenges. Active challenges immediately cap the indicator verdict at `SUSPICIOUS` to prevent wrongful damage.
6. **Admin Review Desk (`/admin/reviews`):** Web portal and JSON endpoint for trust & safety reviewers to inspect challenges, view community sighting counts, contact claimants via pre-filled email, and uphold or reject disputes with 1 click.
7. **Threat Intelligence Export (`/admin/export/known-scams`):** Exports confirmed `KNOWN_SCAM` threat feeds in JSON or CSV for law enforcement and partner integration without leaking reporter data.
8. **Cryptographic Software Licensing:** Ed25519 signed software licences with clock-rollback protection and zero-restart dynamic renewals.

---

## 2. The Trust Rules & Anti-Abuse Engine

Trust computation runs on **read** from immutable event records. No pre-computed aggregates exist, ensuring state recalculations are tamper-resistant and instant.

```
Individual Reports (raw submissions)
        │
        ▼
   [Voice Dedup]  -->  1 Reporter HMAC Token = 1 Voice (earliest event + longest note)
        │
        ▼
  [Union-Find]   -->  Merge voices into Cohorts if:
                        - Shared IP Prefix (same network subnet) OR
                        - 3-gram Note Similarity >= 0.80 (copy-paste / template)
        │
        ▼
[Cohort Weight]  -->  Substantive Note (>=15 chars): 1.0 weight
                        Low-effort Note (<15 chars): 0.9 weight (capped at 1 cohort)
        │
        ▼
   [Verdict]     -->  KNOWN_SCAM requires >= 3 Cohorts AND Score >= 2.5
```

### 2.1 Voice Aggregation
- **One reporter token = One voice:** Multiple reports submitted by the same pseudonymous device token for the same indicator are deduplicated into a single voice.
- **Earliest event & longest note:** The voice retains its earliest timestamp for timeline analysis and its longest note for content inspection.

### 2.2 Cohort Clustering (Union-Find)
Two distinct voices are automatically merged into the same **cohort** if *any* of the following conditions are met:
1. **Shared Network (IP Prefix):** Both voices share the same HMAC-salted IPv4 `/24` or IPv6 `/48` subnet. (e.g. 22 bot accounts operating on the same Wi-Fi collapse into **1 single cohort**).
2. **Note Content Similarity (3-gram Jaccard):** Both voices submit notes $\ge 15$ characters with a character 3-gram Jaccard similarity $\ge 0.80$. (e.g. 40 friends posting copy-pasted or lightly edited text merge into **1 single cohort**).

### 2.3 Confidence Weighting & Low-Effort Cap
- **Substantive Cohorts:** Cohorts containing at least one descriptive note ($\ge 15$ characters) receive a confidence weight of **1.0**.
- **Low-Effort Cohorts:** Cohorts with blank or short notes receive a baseline weight of **0.9**.
- **Low-Effort Cap (`MAX_LOW_EFFORT_COHORTS = 1`):** At most **1** low-effort cohort can count toward the final verdict. This guarantees that un-noted or short-text report-bombing waves cannot escalate an identifier to `KNOWN_SCAM` without detailed, independent accounts.

### 2.4 Verdict Escalation Thresholds
| Verdict | Required Conditions | User-Facing Meaning |
|---|---|---|
| `VERIFIED_BUSINESS` | Seeded in official verified registry or upheld via human review | Legitimate government helpline, bank support, or verified business. |
| `NO_REPORTS` | 0 community sightings | No reports recorded in the database. |
| `SUSPICIOUS` | $\ge 1$ cohort reported, OR active dispute challenge under review | Reported by community members; caution advised. |
| `KNOWN_SCAM` | $\ge 3$ independent cohorts **AND** cumulative score $\ge 2.5$ | Confirmed coordinated threat independently corroborated across multiple networks. |

### 2.5 Privacy Masking Rule
- For identifiers with fewer than 3 independent cohorts, the public lookup masks the sensitive digits (e.g., `98XXXXX210`, `r***@okaxis`, `sbi***.in/...`, `HD****`).
- Once $\ge 3$ independent cohorts corroborate the sighting, the full canonical value is unmasked to warn the public.

### 2.6 Dispute Protection Rule
- When a business files a dispute at `POST /challenges`, the status becomes `under_review`.
- While under review, the identifier's public verdict is **strictly capped at `SUSPICIOUS`** (even if corroborated by 10+ cohorts) and flags `"challenged": true`.
- If **Upheld**: The identifier is immediately added to `verified_indicators` (`VERIFIED_BUSINESS`).
- If **Rejected**: The verdict returns to its calculated score, and new challenges are blocked for 7 days (`CHALLENGE_BLOCKED`).

---

## 3. How to Use This Project

### 3.1 Prerequisites
- Python 3.10, 3.11, or 3.12
- Modern web browser (Chrome, Firefox, Safari, Edge)

### 3.2 Quick Setup (3 Steps)

```bash
# 1. Clone the repository
git clone https://github.com/saavarnim/SatyaCheck.git
cd SatyaCheck/SatyaCheck/satyacheck-repo-seed

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Launch the development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at **`http://localhost:8000`**.

---

### 3.3 Exploring the Web Application

| Tab | URL Hash | Key Actions |
|---|---|---|
| **Check** | `#/check` | Enter a phone number (e.g. `9876543210`), UPI ID (`fraud@okaxis`), website link, or SMS sender ID. Toggle language between English and हिन्दी. View verdict, evidence timeline, and recent local alerts. |
| **Report** | `#/report` | Report a suspicious interaction in under 60 seconds. Select communication channel, scam type, pincode, and India Time (IST) timepicker with quick chips (*Just now*, *1 hour ago*, *Yesterday*, etc.). |
| **Map** | `#/map` | View live heat clusters across Indian cities. Filter by time window (*24 hours*, *3 days*, *7 days*). Click any locality card under the map to auto-pan and zoom directly to that cluster. |
| **Alerts** | `#/alerts` | Browse real-time warnings for sudden locality spikes ($2\times$ daily baseline) and new scam tactics emerging in specific areas. Filter by pincode. |
| **About** | `#/about` | Read privacy guarantees and submit official business dispute challenges. Contains direct access link to the Trust & Safety Review Desk. |

---

### 3.4 Using the Admin Reviews Portal

Authorities and reviewers can access the admin review dashboard in their browser:
```
http://localhost:8000/admin/reviews?token=changeme
```
*(Replace `changeme` with your configured `ADMIN_TOKEN`)*

**Features available in the Admin Portal:**
- **Overview Stat Cards:** Total challenges, pending reviews, upheld verifications, and rejected disputes.
- **Filter Tabs:** Filter rows by `All`, `Under Review`, `Upheld`, and `Rejected`.
- **Claimant Outreach:** Clickable `📧 Claimant Email` links open pre-filled emails with the dispute reference number and identifier details.
- **Privacy Shield:** Reviewers see aggregate community sighting counts and claimant proof—never individual reporter tokens, IP subnets, or raw personal notes.
- **1-Click Resolution:** Click `✔️ Uphold` to verify the business or `❌ Reject` to maintain the scam verdict with cooldown.

---

### 3.5 Environment Variables

Configuration is loaded from environment variables or a local `.env` file (see [`.env.example`](file:///.env.example)):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./satyacheck.db` | SQLAlchemy connection string (SQLite for dev; PostgreSQL for production). |
| `ADMIN_TOKEN` | `changeme` | Token for `/admin/*` operations (reviews portal, challenges, export). |
| `DEMO_MODE` | `true` | Allows calling `POST /admin/reset` to restore clean state during judging/demos. |
| `TRUST_BODY_IDENTITY` | `true` | Permits `reporter_id` and `ip_prefix` overrides in request body for simulation tests. |
| `REPORTER_SALT` | `dev-reporter-salt` | Secret salt for HMAC-SHA256 pseudonymisation of device identifiers. |
| `IP_SALT` | `dev-ip-salt` | Secret salt for HMAC-SHA256 pseudonymisation of network subnets. |
| `LICENCE_PUBLIC_KEY` | *(seed key)* | Base64/Hex 32-byte Ed25519 public key verifying software licences. |

---

## 4. API Reference & Exact CURL Commands

### 4.1 Lookup an Identifier
```bash
curl -X GET "http://localhost:8000/lookup?type=phone&value=%2B919876543210"
```
**Response:**
```json
{
  "verdict": "SUSPICIOUS",
  "report_count": 2,
  "distinct_reporters": 2,
  "first_seen": "2026-10-31T12:00:00+05:30",
  "last_seen": "2026-10-31T14:30:00+05:30",
  "scam_type": "fake-kyc-link",
  "display_value": "98XXXXX210",
  "evidence": [
    {
      "occurred_at": "2026-10-31T12:00:00+05:30",
      "channel": "phone call",
      "scam_type": "fake-kyc-link",
      "pincode": "560102"
    }
  ],
  "challenged": false
}
```

### 4.2 Submit a Scam Report
```bash
curl -X POST http://localhost:8000/reports \
  -H "Content-Type: application/json" \
  -H "X-Device-Id: client_device_token" \
  -d '{
    "identifier_type": "phone",
    "identifier_value": "+91 98765 43210",
    "channel": "phone call",
    "scam_type": "fake-kyc-link",
    "pincode": "560102",
    "note": "Caller claimed my electricity connection would be disconnected without immediate payment",
    "occurred_at": "2026-10-31T14:00:00+05:30"
  }'
```

### 4.3 Submit a Business Dispute Challenge
```bash
curl -X POST http://localhost:8000/challenges \
  -H "Content-Type: application/json" \
  -d '{
    "identifier_type": "phone",
    "identifier_value": "9876543210",
    "claimant_name": "Apex Hospital Helpline",
    "contact_email": "ops@apexhospital.org",
    "proof_note": "Official registered hospital emergency helpline"
  }'
```

### 4.4 Admin Review Operations
```bash
# 1. Fetch challenged reviews (JSON)
curl -X GET "http://localhost:8000/admin/reviews?token=changeme&format=json"

# 2. Resolve a challenge (upheld or rejected)
curl -X POST "http://localhost:8000/admin/challenges/CH-000001/resolve?token=changeme" \
  -H "Content-Type: application/json" \
  -d '{"decision": "upheld"}'
```

### 4.5 Export Confirmed Known Scams (Threat Intel Feed)
```bash
# Export as JSON
curl -X GET "http://localhost:8000/admin/export/known-scams?format=json" \
  -H "X-Admin-Token: changeme"

# Export as CSV
curl -X GET "http://localhost:8000/admin/export/known-scams?format=csv" \
  -H "X-Admin-Token: changeme"
```

### 4.6 Software Licence Status & Dynamic Renewal
```bash
# Check current licence status
curl -X GET http://localhost:8000/license

# Upload cryptographically signed licence
curl -X POST http://localhost:8000/license \
  -H "Content-Type: application/json" \
  -d '{"licensee":"Demo Bank","expires_at":"2026-12-31T23:59:59Z","signature":"..."}'
```

---

## 5. Automated Tests & Judge Simulator

SatyaCheck includes a comprehensive automated test suite and hackathon evaluation simulation tool:

### Run the Unit & Integration Tests (165 Tests)
```bash
pytest -v
```

### Run the Judge Simulator
The simulator benchmarks adversarial report-bombing defenses, lookup accuracy, heatmap clustering, privacy leaks, dispute workflows, and licence compliance:
```bash
python tools/judge_sim.py --base http://127.0.0.1:8000
```

---

## 6. Privacy & Security Commitments

1. **Zero Raw PII Storage:** Raw IP addresses and device IDs are never stored; they are hashed with secret salts into 16-hex HMAC tokens immediately in memory.
2. **Scrubbed Notes:** Contact numbers, emails, and card numbers are redacted using regex filters before saving. Raw notes are never exposed on any public endpoint.
3. **No Street-Level Geolocation:** GPS coordinates are never captured. Map clusters render only at fixed locality pincode centroids.
4. **Sanitised Access Logs:** ASGI logging middleware records only HTTP method, scrubbed path (query strings stripped), status code, and execution duration. Request bodies, query parameters, and tokens are omitted.
5. **Neutral, Sightings-Based Language:** API responses and frontend text strictly present neutral sightings ("Reported by 3 people near you", never "fraudster" or "criminal").

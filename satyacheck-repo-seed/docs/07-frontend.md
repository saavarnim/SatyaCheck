# Frontend (web/, plain HTML + vanilla JS ES modules, NO build, NO npm)
Files: `index.html`, `app.js`, `i18n.js` (en + hi dictionaries), `app.css`. Only external asset: Leaflet 1.9.4 from a CDN `<script>/<link>` (pinned version) with OpenStreetMap tiles. Icons = emoji + visible text label (+ aria-label). Hash routes: `#/` `#/check` `#/report` `#/map` `#/alerts` `#/about`.

Style: emerald green primary, warm off-white bg, grey neutrals, amber caution, red ONLY for the top verdict. System sans font. 12-16px radius cards, 44px+ touch targets, visible focus, no horizontal scroll. Mobile first: bottom tab bar on phones, top bar on desktop.

## Language
EN / हिन्दी toggle in header, saved. EVERY string (labels, verdict text, advice, errors, licence screen) comes from i18n.js. Hindi simple and natural; leave `// TODO native speaker review`.

## Identity
Random device UUID in localStorage (every access in try/catch; works if storage is blocked). Send as `reporter_id` and header `X-Device-Id`. Never send location. Remember chosen area in localStorage.

## Views
1. **Home/Check**: big paste box ("Paste a number, UPI ID, link or SMS sender"), auto-detect type (changeable chip), "Report a scam" button, alert preview for saved area, safety line (1930, cybercrime.gov.in).
   Result card: verdict chip using names Known scam / Suspicious / No reports / Verified business; "Reported by N people" (never "is a fraud"); masked value; one-line explanation; "What to do" steps; expandable "Technical details" (type, value shown, report_count, distinct_reporters, first/last seen, scam type, evidence areas, challenged, why-this-result). NO_REPORTS text: "No one has reported this yet. That is not proof it is safe." If challenged: "The owner has disputed this. It is under review." Link "This is my number" -> dispute form (in About).
2. **Report** (under 60 s, no login): channel icons (6) -> scam type icons (12 + Other) -> paste identifier (auto-detect) -> area (searchable list of areas from `data` via GET /map? no: embed the 25 areas in app.js) -> time chips (Just now default / Today / Yesterday) -> optional note ("do not include names or numbers") -> Submit. Success: case ref, "Your report is anonymous", and "This is NOT a police complaint" with 1930 and cybercrime.gov.in. Do not echo the full identifier after submit.
3. **Map**: Leaflet circles per cluster (size by count, colour by severity), tap -> count, top scam type, advice. List under the map for small screens.
4. **Alerts**: SPIKE / NEW_TYPE cards with plain explanation + exact numbers.
5. **About**: how trust works in 5 plain lines, privacy promise, scam-type advice list, official resources, dispute form (POST /challenges).

## Licence screen
On any 403 `LICENSE_EXPIRED`, replace the app with full-screen "Licence expired. Contact your provider." (EN + HI). Poll GET /license every 30 s; return to the app when ACTIVE.

## Advice per scam type (write EN + HI, 1-2 lines each; end each with "Call 1930 or visit cybercrime.gov.in if money was lost")
digital-arrest: no agency arrests anyone over a video call; hang up. fake-kyc-link: banks never ask for KYC via links. upi-refund-qr: scanning a QR never receives money. investment-group: guaranteed profits are a red flag. courier-customs: no parcel fines over phone. job-offer: real jobs never ask for deposits. lottery-prize: you cannot win what you did not enter. loan-app-harassment: do not give contact access; report it. electricity-disconnection: check only on the official provider app/site. fake-customer-care: use numbers from the official website. otp-call: never share OTP or PIN. sextortion: do not pay; keep evidence; report. other: generic.

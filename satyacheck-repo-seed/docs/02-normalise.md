# Normalisation + validation (app/normalise.py, app/redact.py)
One function per type. Return canonical string or raise `InvalidIdentifier` (-> 400). Used by reports, lookup, verified matching, challenges. Error text never contains the raw value.

## phone
Keep digits only (ignore spaces, dashes, brackets, leading +).
1. Starts with 1800 or 1860 and 8-11 digits -> toll-free, canonical = digits (`1800 1600` -> `18001600`).
2. Matches `^19\d\d$` -> short code, canonical = digits (`1930`, `1909`).
3. Else: if length 12 and starts with 91 -> drop 91; if length 11 and starts with 0 -> drop 0. Need exactly 10 digits, first digit 2-9, not all the same digit, not a straight run (1234567890 style, 8+ ascending/descending). Canonical `+91` + 10 digits.
4. Anything else (`12345`, `test`) -> invalid.
`+91 98765 43210`, `09876543210`, `98765-43210`, `919876543210` all -> `+919876543210`. `+91 80 4100 2233` -> `+918041002233`.

## upi
Lowercase, remove all spaces. Must match `^[a-z0-9._-]{2,64}@[a-z][a-z0-9]{1,32}$`.

## url
Add `https://` if missing; force https; lowercase host; remove leading `www.`; drop query and fragment; drop trailing `/`. Host needs a dot and a 2+ letter TLD. **Never rewrite the hostname.** (The brief's example `sbikyc.in -> sbi-kyc.in` looks like a typo; note it in README, ask organisers.) `http://www.sbikyc.in/pay?utm=sms` -> `https://sbikyc.in/pay`.

## sender_id
Strip, remove hyphens, uppercase; if 8 chars drop first 2; must match `^[A-Z0-9]{6}$`. `VMHDFCBK`, `AD-HDFCBK`, `HDFCBK` -> `HDFCBK`.

## other fields
- identifier_type not in phone|upi|url|sender_id -> 400.
- channel allowed: Phone call, SMS or WhatsApp, QR code, Fake website, UPI request, Something else. Anything else -> "Something else".
- scam_type known: digital-arrest, fake-kyc-link, upi-refund-qr, investment-group, courier-customs, job-offer, lottery-prize, loan-app-harassment, electricity-disconnection, fake-customer-care, otp-call, sextortion. Anything else/missing -> "other".
- Times: ISO-8601 with offset. 400 if unparseable or occurred_at > now + 5 min. **Never reject old timestamps** (month-old reports must be accepted; they only feed the 30-day alert baseline).
- pincode must exist in areas.json else 400.
- note: redact phone numbers, 10-12 digit runs, UPI ids, emails, URLs -> `[redacted]`; cap 300 chars.

## tests/test_normalise.py must cover
all phone variants above; 1930, 1909, `1800 1600`, `1860 419 5555` valid; `12345`, `test`, `0000000000`, `1234567890`, `0123456789` invalid; UPI case/space; URL www/query/trailing slash/http; sender prefixes; redaction of a note containing a phone and an email.

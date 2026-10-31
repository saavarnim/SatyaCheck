# Trust engine, verdict, masking, rate limit (app/trust.py, app/verdict.py)
Core idea: **a report is a sighting, not a verdict.** Compute at READ time from stored events (no stored aggregates, so reset is trivial). Constants are in `app/config.py` (names in CAPS below).

## Interfaces (T0 creates stubs; other modules code against these)
```python
@dataclass(frozen=True)
class EventRow:        # one stored report
    indicator_id: int; occurred_at: datetime; reporter_token: str; ip_token: str
    pincode: str; scam_type: str; channel: str; note: str

@dataclass(frozen=True)
class TrustedUnit:     # one per cohort
    indicator_id: int; occurred_at: datetime; pincode: str; scam_type: str; channel: str

@dataclass
class IndicatorTrust:
    cohort_count: int; score: float; units: list[TrustedUnit]

def compute_indicator_trust(events: list[EventRow]) -> IndicatorTrust
def all_trusted_units(db) -> list[TrustedUnit]   # every indicator; used by map + alerts
```

## Algorithm
1. **Voice**: group events by reporter_token. One reporter = one voice, however many times they report. Keep the voice's earliest event and its longest note.
2. **Cohort** (union-find): merge two voices if ANY of
   - same ip_token;
   - both notes >= NOTE_MIN_LEN (15) chars and character 3-gram Jaccard >= SIM_THRESHOLD (0.80). Lowercase, collapse whitespace/punctuation first. Character n-grams so Hindi/Hinglish/English all work.
   Each cohort = ONE independent corroborator.
3. **Weight** per cohort = best voice: WEIGHT_NOTE 1.0 if note >= 15 chars, else WEIGHT_NO_NOTE 0.9. `score` = sum.
4. `cohort_count` is what the API calls `distinct_reporters`.
5. **TrustedUnit** per cohort, taking occurred_at/pincode/scam_type/channel from the cohort's earliest voice. Map and alerts count ONLY units (22 fake accounts on one network = 1 unit).

## Verdict order (verdict.py)
1. indicator in verified_indicators -> VERIFIED_BUSINESS (always wins)
2. cohort_count == 0 -> NO_REPORTS
3. active challenge (under_review) -> cap at SUSPICIOUS, challenged=true
4. cohort_count >= KNOWN_MIN_COHORTS (3) AND score >= KNOWN_MIN_SCORE (2.5) -> KNOWN_SCAM
5. else SUSPICIOUS

## Masking (until cohort_count >= UNMASK_MIN 3, unless verified)
- phone/toll-free: first 2 digits of national number + `XXXXX` + last 3 (`+919876543210` -> `98XXXXX210`); 4-digit short code: `1XX0`
- upi: first char + `***@` + handle (`r***@okaxis`)
- url: first 3 chars of host + `***` + rest of TLD part + `/...` (`sbi***.in/...`)
- sender: first 2 chars + `****` (`HD****`)
The raw value must not leak in any other field or error message.

## Rate limit (in-memory is fine)
Key on reporter_token ONLY, never the socket IP. > RATE_PER_HOUR (30) submissions/hour per reporter or > RATE_PER_INDICATOR_HOUR (10)/hour per reporter per indicator -> 429. Within limits, repeats are accepted (merged=true) but still count as one voice.

## Identity source
If body has reporter_id and ip_prefix and env TRUST_BODY_IDENTITY=true (set true for judging) -> use them. Else reporter token from header X-Device-Id and ip token from the /24 (IPv4) or /48 (IPv6) of the first X-Forwarded-For hop. Token = first 16 hex of HMAC-SHA256(REPORTER_SALT, value). Never store raw.

## Known limit (say it honestly in README)
Many unrelated-looking accounts on different networks with unique hand-written notes cannot be perfectly told apart from a real wave. Defences: note originality, network diversity. (Stretch, only if everything else passes: reporter reputation.)

## tests/test_trust.py + tests/test_scenarios.py
Use `clock` override and direct API calls. Cases (numbers are the contract):
- 1 reporter x 6 reports -> distinct_reporters 1, not KNOWN_SCAM
- 22 reporter_ids on ONE ip_prefix -> 1 cohort, not KNOWN_SCAM, map count 1, no SPIKE
- 40 reporters, copy-pasted notes, 3 prefixes -> not KNOWN_SCAM
- genuine wave: 8 reporters, 6 prefixes, distinct English/Hindi/Hinglish notes -> KNOWN_SCAM
- confounder: 8 genuine reporters on only 2 prefixes -> record actual result in README
- masking at 1, 2, 3 cohorts for all four types; evidence has only the 4 allowed keys
- verified bakery number stays VERIFIED_BUSINESS even with 10 reports
- active challenge -> challenged=true, never KNOWN_SCAM

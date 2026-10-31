"""app/config.py – ALL constants and env vars. Do not scatter magic numbers."""
import os

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./satyacheck.db")

# ── HMAC salts (required in production; defaults only for local dev) ─────────
REPORTER_SALT: str = os.getenv("REPORTER_SALT", "dev-reporter-salt")
IP_SALT: str = os.getenv("IP_SALT", "dev-ip-salt")

# ── Admin ────────────────────────────────────────────────────────────────────
ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "changeme")
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

# ── Trust-engine constants (docs/03) ─────────────────────────────────────────
NOTE_MIN_LEN: int = 15           # minimum note length for WEIGHT_NOTE to apply
SIM_THRESHOLD: float = 0.80      # 3-gram Jaccard similarity for note-based merge
WEIGHT_NOTE: float = 1.0         # cohort weight if note >= NOTE_MIN_LEN chars
WEIGHT_NO_NOTE: float = 0.9      # cohort weight otherwise

KNOWN_MIN_COHORTS: int = 3       # minimum cohorts to reach KNOWN_SCAM
KNOWN_MIN_SCORE: float = 2.5     # minimum score to reach KNOWN_SCAM
UNMASK_MIN: int = 3              # cohorts required to unmask display_value
MAX_LOW_EFFORT_COHORTS: int = 1  # at most this many low-effort (no long note) cohorts count toward verdict

# ── Rate-limit constants (docs/03) ───────────────────────────────────────────
RATE_PER_HOUR: int = 30          # max submissions/hour per reporter_token
RATE_PER_INDICATOR_HOUR: int = 10  # max/hour per reporter_token per indicator

# ── Identity source (docs/03) ────────────────────────────────────────────────
TRUST_BODY_IDENTITY: bool = os.getenv("TRUST_BODY_IDENTITY", "false").lower() == "true"

# ── Licence ──────────────────────────────────────────────────────────────────
LICENCE_PUBLIC_KEY: str = os.getenv("LICENCE_PUBLIC_KEY", "")  # hex-encoded Ed25519

# ── Map / alerts constants (docs/04) ─────────────────────────────────────────
MAP_DEFAULT_DAYS: int = 7
MAP_DEFAULT_RADIUS_KM: float = 2.0
SEV_CRIT: int = 10
SEV_HIGH: int = 5

SPIKE_MIN: int = 5
SPIKE_FACTOR: float = 2.0
MIN_HISTORY_FOR_NEW_TYPE: int = 2

# ── Scam / channel allow-lists (docs/02) ────────────────────────────────────
KNOWN_CHANNELS = [
    "call", "sms", "whatsapp", "email", "in_person", "social_media",
]
KNOWN_SCAM_TYPES = [
    "investment", "loan", "kyc", "job", "lottery", "impersonation",
    "phishing", "courier", "tech_support", "other",
]

IDENTIFIER_TYPES = ["phone", "upi", "url", "sender_id"]

# ── Misc ─────────────────────────────────────────────────────────────────────
LICENCE_PROTECTED_PREFIXES = (
    "/reports", "/lookup", "/map", "/alerts", "/admin", "/challenges",
)

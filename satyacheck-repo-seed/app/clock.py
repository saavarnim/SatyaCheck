from datetime import datetime, timezone, timedelta
from typing import Optional

IST = timezone(timedelta(hours=5, minutes=30))


def now() -> datetime:
    """Return current UTC time. Override in tests via monkeypatch or module-level replacement."""
    return datetime.now(timezone.utc)


def to_ist_iso(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to IST (+05:30) ISO-8601 string (docs/01-api.md)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()

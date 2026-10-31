"""app/clock.py – Overridable clock for tests. Always use clock.now(), never datetime.now()."""
from datetime import datetime, timezone


def now() -> datetime:
    """Return current UTC time. Override in tests via monkeypatch or module-level replacement."""
    return datetime.now(timezone.utc)

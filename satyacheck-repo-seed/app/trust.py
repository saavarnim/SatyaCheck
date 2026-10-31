"""app/trust.py – Trust engine: voices -> cohorts -> TrustedUnit. (T3 implements algorithm.)"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EventRow:
    """One stored report, as passed to the trust engine."""
    indicator_id: int
    occurred_at: datetime
    reporter_token: str
    ip_token: str
    pincode: str
    scam_type: str
    channel: str
    note: str


@dataclass(frozen=True)
class TrustedUnit:
    """One per cohort: the earliest-voice summary used by map + alerts."""
    indicator_id: int
    occurred_at: datetime
    pincode: str
    scam_type: str
    channel: str


@dataclass
class IndicatorTrust:
    """Aggregated trust result for one indicator."""
    cohort_count: int
    score: float
    units: list[TrustedUnit]


def compute_indicator_trust(events: list[EventRow]) -> IndicatorTrust:
    """Compute cohorts + score for a list of events. (T3)"""
    raise NotImplementedError("T3")


def all_trusted_units(db) -> list[TrustedUnit]:
    """Return TrustedUnits for every indicator. Used by map + alerts. (T3)"""
    raise NotImplementedError("T3")

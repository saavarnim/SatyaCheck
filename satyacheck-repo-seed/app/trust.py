"""app/trust.py – Trust engine: voices -> cohorts -> TrustedUnit (docs/03)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Set

from app.config import (
    NOTE_MIN_LEN,
    SIM_THRESHOLD,
    WEIGHT_NOTE,
    WEIGHT_NO_NOTE,
)


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


@dataclass
class _Voice:
    reporter_token: str
    indicator_id: int
    earliest_event: EventRow
    longest_note: str
    ip_tokens: Set[str]


def clean_note_for_similarity(text: str) -> str:
    """Lowercase and collapse whitespace and punctuation."""
    s = text.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def char_3grams(text: str) -> set[str]:
    """Return set of character 3-grams for similarity calculation."""
    cleaned = clean_note_for_similarity(text)
    if len(cleaned) < 3:
        return {cleaned} if cleaned else set()
    return {cleaned[i : i + 3] for i in range(len(cleaned) - 2)}


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between character 3-grams of two texts."""
    grams1 = char_3grams(text1)
    grams2 = char_3grams(text2)
    if not grams1 or not grams2:
        return 0.0
    intersection = len(grams1 & grams2)
    union = len(grams1 | grams2)
    return intersection / union if union > 0 else 0.0


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> None:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


def compute_indicator_trust(events: list[EventRow]) -> IndicatorTrust:
    """Compute cohorts + score for a list of events belonging to one indicator.

    Algorithm (docs/03):
    1. Voice: group events by reporter_token. One reporter = one voice.
       Keep voice's earliest event and its longest note.
    2. Cohort (Union-Find): merge two voices if ANY of:
       - same ip_token;
       - both notes >= NOTE_MIN_LEN (15) chars and character 3-gram Jaccard >= SIM_THRESHOLD (0.80).
    3. Weight per cohort = best voice:
       WEIGHT_NOTE (1.0) if note >= 15 chars, else WEIGHT_NO_NOTE (0.9).
       score = sum of cohort weights.
    4. TrustedUnit per cohort: taking occurred_at, pincode, scam_type, channel
       from the cohort's earliest voice.
    """
    if not events:
        return IndicatorTrust(cohort_count=0, score=0.0, units=[])

    # 1. Voice aggregation
    voices_map: dict[str, list[EventRow]] = {}
    for ev in events:
        voices_map.setdefault(ev.reporter_token, []).append(ev)

    voices: list[_Voice] = []
    for rep_token, ev_list in voices_map.items():
        # Earliest event
        earliest = min(ev_list, key=lambda x: x.occurred_at)
        # Longest note
        longest_note = max(ev_list, key=lambda x: len(x.note or "")).note or ""
        # IP tokens used by this voice
        ip_set = {x.ip_token for x in ev_list if x.ip_token}
        voices.append(
            _Voice(
                reporter_token=rep_token,
                indicator_id=earliest.indicator_id,
                earliest_event=earliest,
                longest_note=longest_note,
                ip_tokens=ip_set,
            )
        )

    num_voices = len(voices)
    uf = _UnionFind(num_voices)

    # 2. Pairwise cohort merging
    for i in range(num_voices):
        for j in range(i + 1, num_voices):
            v_i = voices[i]
            v_j = voices[j]

            # Merge condition A: shared IP token
            if v_i.ip_tokens and v_j.ip_tokens and (v_i.ip_tokens & v_j.ip_tokens):
                uf.union(i, j)
                continue

            # Merge condition B: character 3-gram Jaccard >= SIM_THRESHOLD
            if len(v_i.longest_note) >= NOTE_MIN_LEN and len(v_j.longest_note) >= NOTE_MIN_LEN:
                sim = jaccard_similarity(v_i.longest_note, v_j.longest_note)
                if sim >= SIM_THRESHOLD:
                    uf.union(i, j)

    # Group voices by root
    cohort_groups: dict[int, list[_Voice]] = {}
    for idx in range(num_voices):
        root = uf.find(idx)
        cohort_groups.setdefault(root, []).append(voices[idx])

    # 3. Calculate weights and TrustedUnits per cohort
    cohort_units: list[TrustedUnit] = []
    total_score = 0.0

    for cohort_voices in cohort_groups.values():
        # Weight per cohort
        has_long_note = any(len(v.longest_note) >= NOTE_MIN_LEN for v in cohort_voices)
        total_score += WEIGHT_NOTE if has_long_note else WEIGHT_NO_NOTE

        # Earliest voice in cohort
        earliest_voice = min(cohort_voices, key=lambda v: v.earliest_event.occurred_at)
        cohort_units.append(
            TrustedUnit(
                indicator_id=earliest_voice.indicator_id,
                occurred_at=earliest_voice.earliest_event.occurred_at,
                pincode=earliest_voice.earliest_event.pincode,
                scam_type=earliest_voice.earliest_event.scam_type,
                channel=earliest_voice.earliest_event.channel,
            )
        )

    # Sort units by occurred_at asc
    cohort_units.sort(key=lambda u: u.occurred_at)

    return IndicatorTrust(
        cohort_count=len(cohort_groups),
        score=round(total_score, 2),
        units=cohort_units,
    )


def all_trusted_units(db) -> list[TrustedUnit]:
    """Return TrustedUnits for every indicator in the DB. Used by map + alerts."""
    from app.models import Report

    reports = db.query(Report).order_by(Report.occurred_at.asc()).all()
    if not reports:
        return []

    # Group by indicator_id
    by_ind: dict[int, list[EventRow]] = {}
    for r in reports:
        ev = EventRow(
            indicator_id=r.indicator_id,
            occurred_at=r.occurred_at,
            reporter_token=r.reporter_token,
            ip_token=r.ip_token,
            pincode=r.pincode,
            scam_type=r.scam_type,
            channel=r.channel,
            note=r.note_redacted or "",
        )
        by_ind.setdefault(r.indicator_id, []).append(ev)

    all_units: list[TrustedUnit] = []
    for ind_events in by_ind.values():
        trust = compute_indicator_trust(ind_events)
        all_units.extend(trust.units)

    return all_units

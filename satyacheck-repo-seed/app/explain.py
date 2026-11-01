"""app/explain.py – Plain-language explanation builder (Task F1).

Returns translation keys and numbers (never text) so the frontend
renders in English or Hindi. Never includes identifiers, notes, or tokens.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Any


LEVELS = ["low", "medium", "high"]


def _ensure_utc(dt: Optional[Union[datetime, str]]) -> Optional[datetime]:
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_explain(
    verdict: str,
    cohort_count: int,
    score: float,
    scam_type: Optional[str],
    last_seen: Optional[Union[datetime, str]],
    challenged: bool,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Pure function building structured explanation dictionary.

    Returns:
        {
            "level": "low" | "medium" | "high",
            "headline_key": str,
            "why": [{"key": str, "n": Optional[int]}],
            "do": list[str],
            "not_meaning_key": str,
        }
    """
    now_utc = _ensure_utc(now) or datetime.now(timezone.utc)
    last_seen_utc = _ensure_utc(last_seen)

    # ── Level calculation ────────────────────────────────────────────────────
    # 1-2 reporters = low (0), 3-4 = medium (1), 5 or more = high (2)
    if cohort_count <= 2:
        lvl_idx = 0
    elif cohort_count <= 4:
        lvl_idx = 1
    else:
        lvl_idx = 2

    # Recency adjustment: <= 7 days raises level by one, > 30 days lowers by one
    if last_seen_utc is not None:
        delta = now_utc - last_seen_utc
        if delta <= timedelta(days=7):
            lvl_idx = min(lvl_idx + 1, 2)
        elif delta > timedelta(days=30):
            lvl_idx = max(lvl_idx - 1, 0)

    level = LEVELS[lvl_idx]

    # ── Headline key ────────────────────────────────────────────────────────
    if challenged:
        headline_key = "explain_headline_challenged"
    elif verdict == "KNOWN_SCAM":
        headline_key = "explain_headline_scam"
    elif verdict == "SUSPICIOUS":
        headline_key = "explain_headline_suspicious"
    elif verdict == "VERIFIED_BUSINESS":
        headline_key = "explain_headline_verified"
    else:  # NO_REPORTS
        headline_key = "explain_headline_no_reports"

    # ── Why we say this ─────────────────────────────────────────────────────
    why: list[dict[str, Any]] = []

    if verdict == "VERIFIED_BUSINESS":
        why.append({"key": "explain_why_verified_list", "n": None})
    elif verdict == "NO_REPORTS" or cohort_count == 0:
        why.append({"key": "explain_why_zero_reports", "n": 0})
    else:
        if cohort_count == 1:
            why.append({"key": "explain_why_single_reporter", "n": 1})
        else:
            why.append({"key": "explain_why_multiple_reporters", "n": cohort_count})

        if last_seen_utc is not None:
            delta = now_utc - last_seen_utc
            days = max(0, delta.days)
            if delta <= timedelta(days=7):
                why.append({"key": "explain_why_seen_recent", "n": days})
            elif delta > timedelta(days=30):
                why.append({"key": "explain_why_seen_older", "n": days})
            else:
                why.append({"key": "explain_why_seen_month", "n": days})

    clean_scam = (scam_type or "").replace("-", "_").lower()
    if clean_scam and clean_scam != "other":
        why.append({"key": f"explain_why_scam_{clean_scam}", "n": None})

    if challenged:
        why.append({"key": "explain_why_under_review", "n": None})

    # ── What to do now ──────────────────────────────────────────────────────
    if verdict == "KNOWN_SCAM":
        actions = [
            "explain_do_block_now",
            "explain_do_no_money_otp",
            "explain_do_call_1930",
        ]
    elif verdict == "SUSPICIOUS":
        actions = [
            "explain_do_do_not_pay",
            "explain_do_verify_independently",
            "explain_do_call_1930",
        ]
    elif verdict == "VERIFIED_BUSINESS":
        actions = [
            "explain_do_safe_contact",
            "explain_do_official_never_ask_pin",
        ]
    else:  # NO_REPORTS
        actions = [
            "explain_do_stay_careful",
            "explain_do_never_share_otp",
            "explain_do_report_if_doubt",
        ]

    if challenged:
        actions.append("explain_do_wait_owner_review")

    # ── What this does not mean ─────────────────────────────────────────────
    if verdict == "NO_REPORTS":
        not_meaning_key = "explain_not_meaning_no_reports"
    elif verdict == "VERIFIED_BUSINESS":
        not_meaning_key = "explain_not_meaning_verified"
    elif verdict == "KNOWN_SCAM":
        not_meaning_key = "explain_not_meaning_scam"
    else:  # SUSPICIOUS
        not_meaning_key = "explain_not_meaning_suspicious"

    return {
        "level": level,
        "headline_key": headline_key,
        "why": why,
        "do": actions,
        "not_meaning_key": not_meaning_key,
    }

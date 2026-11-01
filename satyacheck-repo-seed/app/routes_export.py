"""app/routes_export.py – GET /admin/export/known-scams (Task F2).

Admin export of confirmed KNOWN_SCAM indicators.
Privacy rule: Never exports reporter tokens, IPs, or user notes.
Protected by X-Admin-Token and covered by the licence middleware.
"""
from __future__ import annotations

import csv
import io
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import config
from app.clock import to_ist_iso
from app.db import get_db
from app.models import Challenge, Indicator, Report, VerifiedIndicator
from app.trust import EventRow, compute_indicator_trust
from app.verdict import verdict

router = APIRouter()


@router.get("/admin/export/known-scams")
def export_known_scams(
    format: str = Query("json", pattern="^(json|csv)$"),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
):
    """Export confirmed KNOWN_SCAM indicators as JSON or CSV.

    Headers:
        X-Admin-Token: Required admin token matching app.config.ADMIN_TOKEN.
    Query:
        format: 'json' (default) or 'csv'.
    """
    if not x_admin_token:
        return JSONResponse(status_code=401, content={"error": "UNAUTHORIZED"})
    if x_admin_token != config.ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "FORBIDDEN"})

    indicators = db.query(Indicator).all()
    known_scams = []

    for ind in indicators:
        # 1. Skip if verified business
        is_verified = (
            db.query(VerifiedIndicator)
            .filter_by(type=ind.type, canonical_value=ind.canonical_value)
            .first()
            is not None
        )
        if is_verified:
            continue

        # 2. Check active challenge (under_review caps at SUSPICIOUS)
        has_challenge = (
            db.query(Challenge)
            .filter_by(indicator_id=ind.id, status="under_review")
            .first()
            is not None
        )
        if has_challenge:
            continue

        # 3. Retrieve reports
        reports = (
            db.query(Report)
            .filter_by(indicator_id=ind.id)
            .order_by(Report.occurred_at.asc())
            .all()
        )
        if not reports:
            continue

        # 4. Compute trust
        events = [
            EventRow(
                indicator_id=r.indicator_id,
                occurred_at=r.occurred_at,
                reporter_token=r.reporter_token,
                ip_token=r.ip_token,
                pincode=r.pincode,
                scam_type=r.scam_type,
                channel=r.channel,
                note=r.note_redacted or "",
            )
            for r in reports
        ]
        trust = compute_indicator_trust(events)

        # 5. Determine verdict
        v_str = verdict(trust, is_verified=False, has_active_challenge=has_challenge)
        if v_str != "KNOWN_SCAM":
            continue

        # 6. Extract top scam type
        if trust.units:
            scam_counter = Counter(u.scam_type for u in trust.units if u.scam_type and u.scam_type != "other")
            top_scam = scam_counter.most_common(1)[0][0] if scam_counter else "other"
        else:
            scam_counter = Counter(r.scam_type for r in reports if r.scam_type and r.scam_type != "other")
            top_scam = scam_counter.most_common(1)[0][0] if scam_counter else "other"

        # 7. Extract top pincodes with counts
        pincode_counter = Counter(r.pincode for r in reports if r.pincode)
        top_pincodes = [
            {"pincode": p, "count": c}
            for p, c in pincode_counter.most_common(5)
        ]

        # Privacy assurance: Strictly no reporter, network, ip or note data
        known_scams.append({
            "type": ind.type,
            "value": ind.canonical_value,
            "distinct_reporters": trust.cohort_count,
            "first_seen": to_ist_iso(reports[0].occurred_at),
            "last_seen": to_ist_iso(reports[-1].occurred_at),
            "scam_type": top_scam,
            "top_pincodes": top_pincodes,
        })

    # Return CSV
    if format == "csv":
        output = io.StringIO()
        fieldnames = [
            "type",
            "value",
            "distinct_reporters",
            "first_seen",
            "last_seen",
            "scam_type",
            "top_pincodes",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for item in known_scams:
            pincode_str = ";".join(f"{p['pincode']}:{p['count']}" for p in item["top_pincodes"])
            writer.writerow({
                "type": item["type"],
                "value": item["value"],
                "distinct_reporters": item["distinct_reporters"],
                "first_seen": item["first_seen"],
                "last_seen": item["last_seen"],
                "scam_type": item["scam_type"],
                "top_pincodes": pincode_str,
            })
        return Response(content=output.getvalue(), media_type="text/csv")

    # Default JSON
    return known_scams


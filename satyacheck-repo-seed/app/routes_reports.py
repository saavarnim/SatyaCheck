"""app/routes_reports.py – POST /reports (T2c) and GET /lookup (T2d)."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app import clock
from app.config import IDENTIFIER_TYPES
from app.db import get_db
from app.identity import resolve_reporter_and_ip_tokens, check_and_record_rate_limit
from app.models import Area, Indicator, Report
from app.normalise import normalise, normalise_channel, normalise_scam_type, InvalidIdentifier
from app.redact import redact

router = APIRouter()


class ReportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    report_id: Optional[str] = None
    occurred_at: Optional[str] = None
    reported_at: Optional[str] = None
    reporter_id: Optional[str] = None
    ip_prefix: Optional[str] = None
    channel: Optional[str] = None
    scam_type: Optional[str] = None
    identifier_type: Optional[str] = None
    identifier_value: Optional[str] = None
    pincode: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    note: Optional[str] = None
    has_screenshot: Optional[bool] = False
    amount_lost_inr: Optional[float] = None


def _parse_iso_datetime(dt_str: Optional[str], default: datetime) -> Optional[datetime]:
    """Parse an ISO datetime string. Returns default if None, or None if invalid."""
    if not dt_str:
        return default
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _compute_case_id(identifier_type: str, canonical_value: str) -> str:
    """Generate a stable CASE ID per indicator."""
    hash_hex = hashlib.sha256(f"{identifier_type}:{canonical_value}".encode("utf-8")).hexdigest()[:8].upper()
    return f"CASE-{hash_hex}"


@router.post("/reports", status_code=201)
async def post_report(
    request: Request,
    payload: ReportCreateRequest,
    db: Session = Depends(get_db),
):
    """Submit a scam report (docs/01-api.md)."""
    now = clock.now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # 1. Validate identifier_type
    if not payload.identifier_type or payload.identifier_type not in IDENTIFIER_TYPES:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # 2. Validate identifier_value via normalise()
    if not payload.identifier_value or not isinstance(payload.identifier_value, str):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    try:
        canonical_val = normalise(payload.identifier_type, payload.identifier_value)
    except (InvalidIdentifier, Exception):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # 3. Validate pincode against areas table
    if not payload.pincode or not isinstance(payload.pincode, str):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
    pincode_clean = payload.pincode.strip()
    area = db.get(Area, pincode_clean)
    if not area:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # 4. Validate timestamps
    occurred_dt = _parse_iso_datetime(payload.occurred_at, default=now)
    if occurred_dt is None:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
    # occurred_at must not be in the future (with 60-second clock skew grace)
    if occurred_dt > (now + timedelta(seconds=60)):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    reported_dt = _parse_iso_datetime(payload.reported_at, default=now)
    if reported_dt is None:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    case_id = _compute_case_id(payload.identifier_type, canonical_val)

    # 5. Check duplicate report_id -> return 201 unchanged, store nothing new
    if payload.report_id:
        existing_report = db.query(Report).filter_by(report_id=payload.report_id).first()
        if existing_report:
            # Check if this indicator had other reports
            other_reports = (
                db.query(Report)
                .filter(Report.indicator_id == existing_report.indicator_id, Report.id != existing_report.id)
                .count()
            )
            return JSONResponse(
                status_code=201,
                content={
                    "report_id": existing_report.report_id,
                    "case_id": existing_report.case_id,
                    "merged": other_reports > 0,
                },
            )

    # 6. Lookup or create indicator
    indicator = (
        db.query(Indicator)
        .filter_by(type=payload.identifier_type, canonical_value=canonical_val)
        .first()
    )
    if indicator is not None:
        merged = True
    else:
        merged = False
        indicator = Indicator(type=payload.identifier_type, canonical_value=canonical_val)
        db.add(indicator)
        db.flush()  # assign indicator.id

    # 7. Pseudonymous tokens (HMAC-SHA256, never raw)
    reporter_token, ip_token = resolve_reporter_and_ip_tokens(
        request,
        body_reporter_id=payload.reporter_id,
        body_ip_prefix=payload.ip_prefix,
    )

    # 8. Rate limiting (429 SLOW_DOWN)
    if not check_and_record_rate_limit(reporter_token, indicator.id, now):
        return JSONResponse(status_code=429, content={"error": "SLOW_DOWN"})

    # 9. Normalise channel, scam_type, redact note
    channel_clean = normalise_channel(payload.channel)
    scam_type_clean = normalise_scam_type(payload.scam_type)
    note_clean = redact(payload.note) if payload.note else ""

    # 10. Generate report_id if omitted
    report_id = payload.report_id or f"REP-{uuid.uuid4().hex[:12].upper()}"

    # 11. Store report
    new_report = Report(
        report_id=report_id,
        case_id=case_id,
        indicator_id=indicator.id,
        occurred_at=occurred_dt,
        reported_at=reported_dt,
        reporter_token=reporter_token,
        ip_token=ip_token,
        channel=channel_clean,
        scam_type=scam_type_clean,
        pincode=pincode_clean,
        note_redacted=note_clean,
        has_screenshot=bool(payload.has_screenshot),
        amount_lost_inr=payload.amount_lost_inr,
    )
    db.add(new_report)
    db.commit()

    return JSONResponse(
        status_code=201,
        content={
            "report_id": report_id,
            "case_id": case_id,
            "merged": merged,
        },
    )


@router.get("/lookup")
async def get_lookup():
    """GET /lookup stub – implemented in T2d."""
    raise NotImplementedError("T2d")

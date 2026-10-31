"""app/routes_challenges.py – POST /challenges, GET/POST /admin/challenges, POST /admin/reset.
(docs/01-api.md & tasks/B.md)
"""
import os
from datetime import timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app import clock, config
from app.clock import to_ist_iso
from app.db import get_db
from app.models import Challenge, Indicator, Report, VerifiedIndicator
from app.normalise import normalise, InvalidIdentifier

router = APIRouter()


class ChallengeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    identifier_type: Optional[str] = None
    identifier_value: Optional[str] = None
    claimant_name: Optional[str] = None
    contact_email: Optional[str] = None
    proof_note: Optional[str] = None


class ChallengeResolveRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: Optional[str] = None  # "upheld" | "rejected"


def _is_demo_mode() -> bool:
    """Return True if DEMO_MODE is enabled via config or env."""
    return getattr(config, "DEMO_MODE", False) or os.getenv("DEMO_MODE", "false").lower() == "true"


def _ensure_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post("/challenges", status_code=201)
def post_challenge(
    payload: ChallengeCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a dispute with business proof.
    (docs/01-api.md)
    """
    # 1. Validate required fields
    if not payload.identifier_type or not payload.identifier_value:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
    if not payload.claimant_name or not payload.claimant_name.strip():
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
    if not payload.contact_email or not payload.contact_email.strip():
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # 2. Normalise identifier
    try:
        norm_type = payload.identifier_type.strip().lower()
        if norm_type not in config.IDENTIFIER_TYPES:
            return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
        canon_val = normalise(norm_type, payload.identifier_value)
    except (InvalidIdentifier, Exception):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    now = _ensure_utc(clock.now())

    # 3. Find or create indicator
    indicator = (
        db.query(Indicator)
        .filter_by(type=norm_type, canonical_value=canon_val)
        .first()
    )

    if indicator is not None:
        # Check 7-day cooldown on recent rejection
        cutoff_7d = now - timedelta(days=7)
        recent_rejected = (
            db.query(Challenge)
            .filter(
                Challenge.indicator_id == indicator.id,
                Challenge.status == "rejected",
                Challenge.resolved_at > cutoff_7d,
            )
            .first()
        )
        if recent_rejected is not None:
            return JSONResponse(status_code=409, content={"error": "CHALLENGE_BLOCKED"})

        # Check existing under_review challenge -> return 201 with existing id
        existing = (
            db.query(Challenge)
            .filter_by(indicator_id=indicator.id, status="under_review")
            .first()
        )
        if existing is not None:
            return JSONResponse(
                status_code=201,
                content={
                    "challenge_id": f"CH-{existing.id:06d}",
                    "status": "under_review",
                },
            )
    else:
        # Create indicator row
        indicator = Indicator(type=norm_type, canonical_value=canon_val)
        db.add(indicator)
        db.commit()
        db.refresh(indicator)

    # 4. Insert new challenge
    new_challenge = Challenge(
        indicator_id=indicator.id,
        claimant_name=payload.claimant_name.strip(),
        contact_email=payload.contact_email.strip(),
        proof_note=(payload.proof_note or "").strip(),
        status="under_review",
        created_at=now,
    )
    db.add(new_challenge)
    db.commit()
    db.refresh(new_challenge)

    return JSONResponse(
        status_code=201,
        content={
            "challenge_id": f"CH-{new_challenge.id:06d}",
            "status": "under_review",
        },
    )


@router.get("/admin/challenges")
def admin_list_challenges(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
):
    """
    List under-review challenges. Protected by X-Admin-Token.
    (docs/01-api.md)
    """
    if not x_admin_token or x_admin_token != config.ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "FORBIDDEN"})

    challenges = (
        db.query(Challenge)
        .filter_by(status="under_review")
        .order_by(Challenge.created_at.asc())
        .all()
    )

    items = []
    for c in challenges:
        ind = db.query(Indicator).filter_by(id=c.indicator_id).first()
        items.append({
            "challenge_id": f"CH-{c.id:06d}",
            "indicator_type": ind.type if ind else None,
            "indicator_value": ind.canonical_value if ind else None,
            "claimant_name": c.claimant_name,
            "contact_email": c.contact_email,
            "proof_note": c.proof_note,
            "status": c.status,
            "created_at": to_ist_iso(c.created_at),
        })

    return {"challenges": items}


@router.post("/admin/challenges/{challenge_id}/resolve")
def admin_resolve_challenge(
    challenge_id: str,
    payload: ChallengeResolveRequest,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
):
    """
    Resolve a challenge as upheld or rejected. Protected by X-Admin-Token.
    (docs/01-api.md)
    """
    if not x_admin_token or x_admin_token != config.ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "FORBIDDEN"})

    if payload.decision not in ("upheld", "rejected"):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # Parse integer ID from "CH-000001" or "1"
    raw = challenge_id.strip()
    if raw.upper().startswith("CH-"):
        raw = raw[3:]
    try:
        cid = int(raw)
    except ValueError:
        return JSONResponse(status_code=404, content={"error": "NOT_FOUND"})

    challenge = db.query(Challenge).filter_by(id=cid).first()
    if not challenge:
        return JSONResponse(status_code=404, content={"error": "NOT_FOUND"})

    now = _ensure_utc(clock.now())
    challenge.status = payload.decision
    challenge.resolved_at = now
    db.commit()

    if payload.decision == "upheld":
        # Add to verified_indicators(source='review')
        indicator = db.query(Indicator).filter_by(id=challenge.indicator_id).first()
        if indicator:
            existing_v = (
                db.query(VerifiedIndicator)
                .filter_by(type=indicator.type, canonical_value=indicator.canonical_value)
                .first()
            )
            if existing_v:
                existing_v.org = challenge.claimant_name
                existing_v.source = "review"
            else:
                new_v = VerifiedIndicator(
                    type=indicator.type,
                    canonical_value=indicator.canonical_value,
                    org=challenge.claimant_name,
                    source="review",
                )
                db.add(new_v)
            db.commit()

    return {
        "challenge_id": f"CH-{challenge.id:06d}",
        "status": challenge.status,
    }


@router.post("/admin/reset")
def admin_reset(
    db: Session = Depends(get_db),
):
    """
    Reset state when DEMO_MODE=true. Deletes reports, indicators, challenges,
    and review-added verified rows. Keeps areas, seed verified, and licence.
    (docs/01-api.md)
    """
    if not _is_demo_mode():
        return JSONResponse(status_code=403, content={"error": "DEMO_MODE_REQUIRED"})

    db.query(Report).delete()
    db.query(Challenge).delete()
    db.query(Indicator).delete()
    db.query(VerifiedIndicator).filter(VerifiedIndicator.source == "review").delete()
    db.commit()

    # Reset in-memory rate limits as well
    from app.identity import reset_rate_limits
    reset_rate_limits()

    return {"ok": True}

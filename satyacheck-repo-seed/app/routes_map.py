"""app/routes_map.py – GET /map, GET /alerts per docs/01-api.md and docs/04-map-alerts.md."""
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import clock, config
from app.db import get_db
from app.models import Area
from app.trust import all_trusted_units, TrustedUnit

router = APIRouter()


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    r_earth = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get("/map")
def get_map(
    pincode: Optional[str] = Query(None),
    days: int = Query(config.MAP_DEFAULT_DAYS),
    radius_km: float = Query(config.MAP_DEFAULT_RADIUS_KM),
    db: Session = Depends(get_db),
):
    """
    Cluster trusted units by pincode within the time window and optional radius.
    (docs/01-api.md & docs/04-map-alerts.md)
    """
    if days <= 0 or radius_km < 0:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    all_areas = db.query(Area).all()
    area_by_pincode = {a.pincode: a for a in all_areas}

    allowed_pincodes: Optional[set[str]] = None
    if pincode is not None:
        target_area = area_by_pincode.get(pincode)
        if not target_area:
            return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

        allowed_pincodes = set()
        for a in all_areas:
            if a.pincode == pincode:
                allowed_pincodes.add(a.pincode)
            elif (
                target_area.lat is not None
                and target_area.lng is not None
                and a.lat is not None
                and a.lng is not None
            ):
                dist = haversine_km(target_area.lat, target_area.lng, a.lat, a.lng)
                if dist <= radius_km:
                    allowed_pincodes.add(a.pincode)

    units: list[TrustedUnit] = all_trusted_units(db)
    now = _ensure_utc(clock.now())
    start_time = now - timedelta(days=days)

    # Filter units in (now - days, now] and within allowed_pincodes if specified
    units_by_pincode: dict[str, list[TrustedUnit]] = {}
    for u in units:
        u_dt = _ensure_utc(u.occurred_at)
        if not (start_time < u_dt <= now):
            continue
        if allowed_pincodes is not None and u.pincode not in allowed_pincodes:
            continue
        units_by_pincode.setdefault(u.pincode, []).append(u)

    clusters = []
    # Sorted by count desc, then pincode asc for stable output
    for code, p_units in sorted(units_by_pincode.items(), key=lambda item: (-len(item[1]), item[0])):
        area = area_by_pincode.get(code)
        count = len(p_units)

        # Most common scam_type
        scam_counts = Counter(u.scam_type for u in p_units)
        top_scam_type = scam_counts.most_common(1)[0][0] if scam_counts else "other"

        # Severity per docs/04
        if count >= config.SEV_CRIT:
            severity = "CRIT"
        elif count >= config.SEV_HIGH:
            severity = "HIGH"
        else:
            severity = "MED"

        clusters.append({
            "pincode": code,
            "locality": area.locality if area else "",
            "city": area.city if area else "",
            "count": count,
            "top_scam_type": top_scam_type,
            "severity": severity,
            "lat": area.lat if area else None,
            "lng": area.lng if area else None,
        })

    return {"clusters": clusters}


@router.get("/alerts")
def get_alerts(
    pincode: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Return emerging scam alerts (SPIKE and NEW_TYPE) per area.
    (docs/01-api.md & docs/04-map-alerts.md)
    """
    all_areas = db.query(Area).all()
    area_by_pincode = {a.pincode: a for a in all_areas}

    if pincode is not None:
        if pincode not in area_by_pincode:
            return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
        eval_pincodes = [pincode]
    else:
        eval_pincodes = sorted(area_by_pincode.keys())

    units: list[TrustedUnit] = all_trusted_units(db)
    now = _ensure_utc(clock.now())
    t_24h = now - timedelta(hours=24)
    t_baseline_start = t_24h - timedelta(days=7)  # [now-24h-7d, now-24h)
    t_30d_start = t_24h - timedelta(days=30)       # [now-24h-30d, now-24h)

    # Group units by pincode
    units_by_area: dict[str, list[TrustedUnit]] = {}
    for u in units:
        units_by_area.setdefault(u.pincode, []).append(u)

    alerts = []
    for code in eval_pincodes:
        a_units = units_by_area.get(code, [])
        if not a_units:
            continue

        # last24 units in (now-24h, now]
        last24_units = [u for u in a_units if t_24h < _ensure_utc(u.occurred_at) <= now]
        last24_count = len(last24_units)

        # Baseline units in [now-24h-7d, now-24h)
        baseline_units = [
            u for u in a_units
            if t_baseline_start <= _ensure_utc(u.occurred_at) < t_24h
        ]
        baseline_per_day = round(len(baseline_units) / 7.0, 2)

        # 1. SPIKE alert
        if (
            last24_count >= config.SPIKE_MIN
            and last24_count >= config.SPIKE_FACTOR * baseline_per_day
        ):
            alerts.append({
                "type": "SPIKE",
                "pincode": code,
                "window": "24h",
                "count": last24_count,
                "baseline_per_day": baseline_per_day,
            })

        # 2. NEW_TYPE alert
        if last24_units:
            prior_30d_units = [
                u for u in a_units
                if t_30d_start <= _ensure_utc(u.occurred_at) < t_24h
            ]
            if len(prior_30d_units) >= config.MIN_HISTORY_FOR_NEW_TYPE:
                prior_types = {u.scam_type for u in prior_30d_units}
                last24_types = sorted(set(u.scam_type for u in last24_units))
                for st in last24_types:
                    if st not in prior_types:
                        alerts.append({
                            "type": "NEW_TYPE",
                            "pincode": code,
                            "scam_type": st,
                            "window": "24h",
                        })

    return {"alerts": alerts}

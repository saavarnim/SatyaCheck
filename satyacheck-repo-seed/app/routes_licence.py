"""app/routes_licence.py – GET /license, POST /license, and demo licence helpers.

Both endpoints work even when the licence is expired (they are not
in LICENCE_PROTECTED_PREFIXES).
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app import licence

router = APIRouter()


@router.get("/license")
async def get_license():
    """Return current licence status (always open)."""
    return licence.get_licence_status()


@router.post("/license")
async def post_license(request: Request):
    """Upload a new licence JSON (always open)."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # If payload contains a multi-slot catalog, find the active slot
    if isinstance(body, dict) and "slots" in body and isinstance(body["slots"], list):
        now_utc = datetime.now(timezone.utc)
        for s in body["slots"]:
            try:
                exp_dt = datetime.fromisoformat(s.get("expires_at", ""))
                if (exp_dt - now_utc).total_seconds() >= 60:
                    body = s
                    break
            except Exception:
                continue

    licensee = body.get("licensee")
    expires_at = body.get("expires_at")
    signature = body.get("signature")

    if not all([licensee, expires_at, signature]):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    result = licence.store_licence(licensee, expires_at, signature)

    if "error" in result:
        return JSONResponse(
            status_code=result["status_code"],
            content={"error": result["error"]},
        )

    return {"ok": True}


@router.get("/license/demo-long")
async def get_demo_long_licence():
    """Demo helper: return pre-signed long evaluation licence."""
    long_path = Path(__file__).resolve().parent.parent / "licences" / "long.json"
    if long_path.exists():
        return json.loads(long_path.read_text(encoding="utf-8"))
    return {
        "licensee": "Demo Bank",
        "expires_at": "2026-11-30T16:18:29.141842+00:00",
        "signature": "F4JtrV95BDI4dZCrrO3aUmwYrXNcJ0s5uOT7vqGU6LVssdvF9WdzyZJho4Dr+qlJLPrHt17HVCJdwS+AcXwVCg==",
    }


@router.get("/license/demo-5min")
async def get_demo_5min_licence():
    """Demo helper: generate a fresh 5-minute licence if private key is present,
    or pick an active 5-minute slot from licences/alternative_5min.json."""
    from app.licence import sign

    priv_path = Path.home() / ".satyacheck" / "private.key"
    if priv_path.exists():
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(minutes=5)).isoformat()
        licensee = "Demo Bank"
        sig = sign(licensee, expires_at, priv_path.read_bytes())
        return {
            "licensee": licensee,
            "expires_at": expires_at,
            "signature": sig,
        }

    # If running where private key is not stored (e.g. cloud host Render),
    # pick the active slot from licences/alternative_5min.json
    alt_path = Path(__file__).resolve().parent.parent / "licences" / "alternative_5min.json"
    if alt_path.exists():
        try:
            data = json.loads(alt_path.read_text(encoding="utf-8"))
            slots = data.get("slots", [])
            now_utc = datetime.now(timezone.utc)
            for slot in slots:
                exp_dt = datetime.fromisoformat(slot["expires_at"])
                # Pick first slot expiring at least 60 seconds in the future
                if (exp_dt - now_utc).total_seconds() >= 60:
                    return {
                        "licensee": slot["licensee"],
                        "expires_at": slot["expires_at"],
                        "signature": slot["signature"],
                    }
        except Exception:
            pass

    # Fallback to pre-signed 5min.json if exists
    fmin_path = Path(__file__).resolve().parent.parent / "licences" / "5min.json"
    if fmin_path.exists():
        return json.loads(fmin_path.read_text(encoding="utf-8"))

    return JSONResponse(status_code=404, content={"error": "PRIVATE_KEY_NOT_FOUND"})

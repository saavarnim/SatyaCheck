"""app/routes_licence.py – GET /license, POST /license.

Both endpoints work even when the licence is expired (they are not
in LICENCE_PROTECTED_PREFIXES).
"""
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

"""app/routes_challenges.py – POST /challenges, GET/POST /admin/challenges. Stub. (T-B)"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/challenges", status_code=201)
async def post_challenge():
    raise NotImplementedError("T-B")


@router.get("/admin/challenges")
async def admin_list_challenges():
    raise NotImplementedError("T-B")


@router.post("/admin/challenges/{challenge_id}/resolve")
async def admin_resolve_challenge(challenge_id: str):
    raise NotImplementedError("T-B")


@router.post("/admin/reset")
async def admin_reset():
    raise NotImplementedError("T-B")

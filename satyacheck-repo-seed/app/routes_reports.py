"""app/routes_reports.py – POST /reports, GET /lookup. Stub. (T2)"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/reports", status_code=201)
async def post_report():
    raise NotImplementedError("T2")


@router.get("/lookup")
async def get_lookup():
    raise NotImplementedError("T2")

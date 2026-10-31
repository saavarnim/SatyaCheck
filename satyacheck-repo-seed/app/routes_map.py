"""app/routes_map.py – GET /map, GET /alerts. Stub. (T-B)"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/map")
async def get_map():
    raise NotImplementedError("T-B")


@router.get("/alerts")
async def get_alerts():
    raise NotImplementedError("T-B")

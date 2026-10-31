"""app/routes_licence.py – GET /license, POST /license. Stub. (T-B)"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/license")
async def get_license():
    raise NotImplementedError("T-B")


@router.post("/license")
async def post_license():
    raise NotImplementedError("T-B")

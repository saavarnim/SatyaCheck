"""app/main.py – FastAPI application entry point.

Registers:
  - Privacy-safe logging middleware (method, path, status, duration only)
  - Licence middleware hook (checks licence.is_allowed per protected path)
  - 422 -> 400 handler
  - All five routers
  - Static mount at / LAST (as required by docs/01)
"""
import time
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app import licence
from app.config import LICENCE_PROTECTED_PREFIXES
from app.db import init_db
from app.routes_reports import router as reports_router
from app.routes_map import router as map_router
from app.routes_licence import router as licence_router
from app.routes_challenges import router as challenges_router

# ── Logging: only method, path (no query string), status, duration ────────────
logger = logging.getLogger("satyacheck")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


class PrivacySafeLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path (no query string), status code, and duration only."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error("%-6s %-50s 500 %.1fms", request.method, request.url.path, duration_ms)
            return JSONResponse(status_code=500, content={"error": "SERVER_ERROR"})
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%-6s %-50s %s %.1fms",
            request.method,
            request.url.path,  # deliberately NOT request.url (which includes query string)
            response.status_code,
            duration_ms,
        )
        return response


class LicenceMiddleware(BaseHTTPMiddleware):
    """Check licence for protected paths. Always-open: /health, /license, static files."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(prefix) for prefix in LICENCE_PROTECTED_PREFIXES):
            if not licence.is_allowed(path):
                return JSONResponse(status_code=403, content={"error": "LICENSE_EXPIRED"})
        return await call_next(request)


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(title="SatyaCheck", docs_url="/docs", redoc_url=None)

# Middleware (outermost first)
app.add_middleware(PrivacySafeLoggingMiddleware)
app.add_middleware(LicenceMiddleware)


# 422 -> 400 handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})


# ── Health (always open) ──────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"ok": True}


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(reports_router)
app.include_router(map_router)
app.include_router(licence_router)
app.include_router(challenges_router)


# ── Startup: create tables + seed ────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    from app.licence import init_licence
    init_licence()
    from app.db import SessionLocal
    from app.seed import seed
    with SessionLocal() as db:
        seed(db)



# ── Static files LAST (so API routes are not overshadowed) ───────────────────
import pathlib  # noqa: E402

_web_dir = pathlib.Path(__file__).parent.parent / "web"
_web_dir.mkdir(exist_ok=True)
# Create a minimal index.html if not present so the static mount doesn't error
_index = _web_dir / "index.html"
if not _index.exists():
    _index.write_text("<!DOCTYPE html><html><body><h1>SatyaCheck</h1></body></html>")

app.mount("/", StaticFiles(directory=str(_web_dir), html=True), name="static")

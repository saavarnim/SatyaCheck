"""tests/conftest.py – Shared fixtures: TestClient, temp SQLite DB, clock override."""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.clock as clock_module
from app.models import Base
from app.db import get_db
from app.main import app


# ── Temporary in-memory SQLite for tests ──────────────────────────────────────
TEST_DB_URL = "sqlite://"  # in-memory


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh in-memory SQLite engine and yield a session with seed data."""
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    from app.seed import seed
    seed(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db, monkeypatch):
    """
    FastAPI TestClient wired to the temp in-memory DB.
    Overrides the get_db dependency so all routes use the test session.
    """
    engine = test_db.get_bind()
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app import licence
    from app.identity import reset_rate_limits
    reset_rate_limits()
    monkeypatch.setattr(licence, "is_allowed", lambda path: True)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── Clock override ────────────────────────────────────────────────────────────
@pytest.fixture
def fixed_clock(monkeypatch):
    """
    Override clock.now() with a fixed UTC datetime.
    Usage: fixed_clock(datetime(2025, 1, 1, tzinfo=timezone.utc))
    Returns a setter callable so tests can advance time.
    """
    _fixed: list[datetime] = [datetime(2025, 1, 1, tzinfo=timezone.utc)]

    def fake_now() -> datetime:
        return _fixed[0]

    def set_time(dt: datetime):
        _fixed[0] = dt

    monkeypatch.setattr(clock_module, "now", fake_now)
    return set_time

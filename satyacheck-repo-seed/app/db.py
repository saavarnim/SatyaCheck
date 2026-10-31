"""app/db.py – SQLAlchemy engine, session factory, and seed loader."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: yields a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and load seed data. Call once at startup."""
    from app.models import Base  # noqa: PLC0415 (avoid circular at module level)
    Base.metadata.create_all(bind=engine)
    _seed()


def _seed():
    """Idempotently load data/areas.json and data/verified.json."""
    import json
    import pathlib
    from app.models import Area, VerifiedIndicator

    data_dir = pathlib.Path(__file__).parent.parent / "data"
    db: Session = SessionLocal()
    try:
        # ── areas ──────────────────────────────────────────────────────────
        areas_path = data_dir / "areas.json"
        if areas_path.exists():
            for row in json.loads(areas_path.read_text()):
                if not db.get(Area, row["pincode"]):
                    db.add(Area(**row))

        # ── verified indicators ────────────────────────────────────────────
        verified_path = data_dir / "verified.json"
        if verified_path.exists():
            for row in json.loads(verified_path.read_text()):
                exists = (
                    db.query(VerifiedIndicator)
                    .filter_by(type=row["type"], canonical_value=row["canonical_value"])
                    .first()
                )
                if not exists:
                    db.add(VerifiedIndicator(source="seed", **row))

        db.commit()
    finally:
        db.close()

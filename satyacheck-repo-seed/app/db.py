"""app/db.py – SQLAlchemy engine, session factory, init_db."""
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
    """Create all tables. Seed loading is in app/seed.py (T2b)."""
    from app.models import Base  # noqa: PLC0415 (avoid circular at module level)
    Base.metadata.create_all(bind=engine)

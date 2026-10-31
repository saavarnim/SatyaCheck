"""app/models.py – SQLAlchemy ORM models matching the API contract tables."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    canonical_value = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("type", "canonical_value"),)

    reports = relationship("Report", back_populates="indicator")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True, nullable=False)
    case_id = Column(String, nullable=False)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=False)
    reporter_token = Column(String, nullable=False)
    ip_token = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    scam_type = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    note_redacted = Column(String, nullable=True)
    has_screenshot = Column(Boolean, default=False)
    amount_lost_inr = Column(Float, nullable=True)

    indicator = relationship("Indicator", back_populates="reports")

    __table_args__ = (
        Index("ix_reports_indicator_occurred", "indicator_id", "occurred_at"),
        Index("ix_reports_pincode_occurred", "pincode", "occurred_at"),
        Index("ix_reports_reporter_token", "reporter_token"),
    )


class Area(Base):
    __tablename__ = "areas"

    pincode = Column(String, primary_key=True)
    locality = Column(String, nullable=False)
    city = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)


class VerifiedIndicator(Base):
    __tablename__ = "verified_indicators"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    canonical_value = Column(String, nullable=False)
    org = Column(String, nullable=True)
    source = Column(String, nullable=False, default="seed")  # seed|demo|review

    __table_args__ = (UniqueConstraint("type", "canonical_value"),)


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    claimant_name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    proof_note = Column(String, nullable=True)
    status = Column(String, nullable=False, default="under_review")  # under_review|upheld|rejected
    created_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class LicenceState(Base):
    __tablename__ = "licence_state"

    id = Column(Integer, primary_key=True, default=1)
    licensee = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    signature = Column(String, nullable=True)
    last_seen_server_time = Column(DateTime(timezone=True), nullable=True)

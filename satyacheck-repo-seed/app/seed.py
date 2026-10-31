"""app/seed.py – Idempotent seed loader for areas and verified indicators."""
from __future__ import annotations

import json
import pathlib

from sqlalchemy.orm import Session

from app.models import Area, VerifiedIndicator
from app.normalise import normalise, InvalidIdentifier

_DATA_DIR = pathlib.Path(__file__).parent.parent / "data"


def seed(db: Session) -> None:
    """Idempotently load data/areas.json and data/verified.json.

    Verified values are normalised with T1 code so lookups (which also
    normalise) will match.  Safe to call multiple times — existing rows
    are skipped.
    """
    _seed_areas(db)
    _seed_verified(db)
    db.commit()


def _seed_areas(db: Session) -> None:
    areas_path = _DATA_DIR / "areas.json"
    if not areas_path.exists():
        return
    for row in json.loads(areas_path.read_text()):
        if not db.get(Area, row["pincode"]):
            db.add(Area(**row))


def _seed_verified(db: Session) -> None:
    verified_path = _DATA_DIR / "verified.json"
    if not verified_path.exists():
        return
    for row in json.loads(verified_path.read_text()):
        id_type = row["type"]
        raw_value = row.get("value", row.get("canonical_value", ""))
        source = row.get("source", "seed")
        org = row.get("org")
        try:
            canon = normalise(id_type, raw_value)
        except InvalidIdentifier:
            canon = raw_value  # fallback: store as-is if normalisation fails
        exists = (
            db.query(VerifiedIndicator)
            .filter_by(type=id_type, canonical_value=canon)
            .first()
        )
        if not exists:
            db.add(VerifiedIndicator(
                type=id_type,
                canonical_value=canon,
                org=org,
                source=source,
            ))

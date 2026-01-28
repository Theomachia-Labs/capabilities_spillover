"""Core ingestion logic."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from csp.data import crud
from csp.ingest.adapters import BaseSourceAdapter


def ingest_paper(
    db: Session,
    source: BaseSourceAdapter,
    identifier: str,
    force_update: bool = False
) -> Any:
    """Ingest a paper from a source into the database.
    
    1. Checks if paper already exists (canonicalization).
    2. Fetches metadata from source if needed.
    3. Saves/Updates record in DB.
    """
    # 1. Simple Canonicalization: existing ID check
    # In a real system, this would check DOI, arXiv ID, title fuzzy match, etc.
    existing = crud.get_paper(db, identifier)
    if existing and not force_update:
        return existing

    # 2. Fetch Metadata
    raw_data = source.fetch_metadata(identifier)
    if not raw_data:
        raise ValueError(f"Paper not found in source: {identifier}")

    # Ensure paper_id matches what we queried if not present, or normalize it
    if "paper_id" not in raw_data:
        raw_data["paper_id"] = identifier

    # 3. Save to DB
    # If updating, we might need an update_paper CRUD method, but for MVP we just create new
    # or fail if existing. Since we checked `existing`, we assume we are creating.
    return crud.create_paper(db, raw_data)

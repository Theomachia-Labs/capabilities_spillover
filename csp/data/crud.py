"""CRUD operations for Papers and Scores."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from csp.data.models import Paper, Score
from csp.schemas.loader import validate_instance


def create_paper(db: Session, record: dict[str, Any]) -> Paper:
    """Create a new paper record.
    
    Validates against JSON schema before insertion.
    """
    validate_instance(record, "paper_record")
    
    db_obj = Paper(
        paper_id=record["paper_id"],
        title=record["title"],
        abstract=record.get("abstract"),
        year=record.get("year"),
        identifiers=record.get("identifiers", {}),
        authors=record.get("authors", []),
        citations=record.get("citations", []),
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_paper(db: Session, paper_id: str) -> Paper | None:
    """Retrieve a paper by ID."""
    return db.execute(select(Paper).where(Paper.paper_id == paper_id)).scalar_one_or_none()


def create_score(db: Session, record: dict[str, Any]) -> Score:
    """Create a new CSP score.
    
    Validates against JSON schema before insertion.
    """
    validate_instance(record, "csp_score")
    
    db_obj = Score(
        score_id=record["score_id"],
        paper_id=record["paper_id"],
        rubric_version=record["rubric_version"],
        dimensions=record["dimensions"],
        provenance=record["provenance"],
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_score(db: Session, score_id: str) -> Score | None:
    """Retrieve a score by ID."""
    return db.execute(select(Score).where(Score.score_id == score_id)).scalar_one_or_none()


# Label CRUD operations
from csp.data.models import Label


def create_label(db: Session, record: dict[str, Any]) -> Label:
    """Create a new label record."""
    db_obj = Label(
        label_id=record["label_id"],
        paper_id=record["paper_id"],
        label=record["label"],
        confidence=record.get("confidence", 0.5),
        method=record["method"],
        audit_status=record.get("audit_status", "pending"),
        created_at=record["created_at"],
        evidence_spans=record.get("evidence_spans", []),
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_label(db: Session, label_id: str) -> Label | None:
    """Retrieve a label by ID."""
    return db.execute(select(Label).where(Label.label_id == label_id)).scalar_one_or_none()


def get_labels_for_paper(db: Session, paper_id: str) -> list[Label]:
    """Retrieve all labels for a paper."""
    return list(db.execute(select(Label).where(Label.paper_id == paper_id)).scalars().all())


def get_pending_labels(db: Session) -> list[Label]:
    """Retrieve all labels pending audit."""
    return list(db.execute(select(Label).where(Label.audit_status == "pending")).scalars().all())


def update_label_status(db: Session, label_id: str, new_status: str, new_label: str | None = None) -> Label | None:
    """Update the audit status (and optionally the label) of a label record."""
    db_obj = get_label(db, label_id)
    if db_obj:
        db_obj.audit_status = new_status
        if new_label:
            db_obj.label = new_label
        db.commit()
        db.refresh(db_obj)
    return db_obj


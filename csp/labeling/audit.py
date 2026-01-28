"""Audit queue logic for label review."""

from __future__ import annotations

from sqlalchemy.orm import Session

from csp.data import crud
from csp.data.models import Label


CONFIDENCE_THRESHOLD = 0.7


def route_to_audit(db: Session, label_record: dict) -> Label:
    """Save a label and route to audit queue if low confidence.
    
    Labels with confidence below threshold are marked as 'pending'.
    """
    if label_record.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        label_record["audit_status"] = "pending"
    else:
        label_record["audit_status"] = "verified"
    
    return crud.create_label(db, label_record)


def approve_label(db: Session, label_id: str) -> Label | None:
    """Mark a label as verified (approved by human)."""
    return crud.update_label_status(db, label_id, "verified")


def reject_label(db: Session, label_id: str, corrected_label: str) -> Label | None:
    """Reject label and apply human correction."""
    return crud.update_label_status(db, label_id, "verified", new_label=corrected_label)


def get_audit_queue(db: Session) -> list[Label]:
    """Get all labels pending human review."""
    return crud.get_pending_labels(db)

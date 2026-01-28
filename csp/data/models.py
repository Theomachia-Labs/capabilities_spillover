"""SQLAlchemy ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Column, Integer, String, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from csp.data.db import Base


class Paper(Base):
    """Database model for a research paper.
    
    Stores core metadata in columns and flexible/nested data in JSON fields.
    """
    __tablename__ = "papers"

    paper_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Store complex nested structures as JSON for MVP simplicity
    # This includes: identifiers, authors, citations
    identifiers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    authors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    citations: Mapped[list[str]] = mapped_column(JSON, default=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching the JSON schema."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "abstract": self.abstract,
            "year": self.year,
            "identifiers": self.identifiers,
            "authors": self.authors,
            "citations": self.citations,
        }


class Score(Base):
    """Database model for a CSP score."""
    __tablename__ = "scores"

    score_id: Mapped[str] = mapped_column(String, primary_key=True)
    paper_id: Mapped[str] = mapped_column(String, index=True)
    rubric_version: Mapped[str] = mapped_column(String)
    
    # Store scoring details as JSON
    dimensions: Mapped[dict[str, Any]] = mapped_column(JSON)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score_id": self.score_id,
            "paper_id": self.paper_id,
            "rubric_version": self.rubric_version,
            "dimensions": self.dimensions,
            "provenance": self.provenance,
        }


class Label(Base):
    """Database model for a paper label (intent classification)."""
    __tablename__ = "labels"

    label_id: Mapped[str] = mapped_column(String, primary_key=True)
    paper_id: Mapped[str] = mapped_column(String, index=True)
    label: Mapped[str] = mapped_column(String)  # safety_use, capability_use, mixed, unclear
    confidence: Mapped[float] = mapped_column(default=0.5)
    method: Mapped[str] = mapped_column(String)  # rules, llm, human, mixed
    audit_status: Mapped[str] = mapped_column(String, default="pending")  # pending, verified, disputed
    created_at: Mapped[str] = mapped_column(String)
    
    # Store evidence spans as JSON
    evidence_spans: Mapped[list[str]] = mapped_column(JSON, default=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label_id": self.label_id,
            "paper_id": self.paper_id,
            "label": self.label,
            "confidence": self.confidence,
            "method": self.method,
            "audit_status": self.audit_status,
            "created_at": self.created_at,
            "evidence_spans": self.evidence_spans,
        }


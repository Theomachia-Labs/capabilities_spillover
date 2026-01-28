"""Survey data models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import String, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column

from csp.data.db import Base


class SurveyResponse(Base):
    """Database model for an expert survey response."""
    __tablename__ = "survey_responses"

    response_id: Mapped[str] = mapped_column(String, primary_key=True)
    respondent_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String)
    
    # Calibration data (computed Brier score, notes)
    calibration_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibration_notes: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Full response data stored as JSON
    # Contains: [{topic, dimensions: {dim_id: {score, uncertainty}}}]
    responses: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "respondent_id": self.respondent_id,
            "created_at": self.created_at,
            "calibration": {
                "score": self.calibration_score,
                "notes": self.calibration_notes,
            } if self.calibration_score else None,
            "responses": self.responses,
        }


class CalibrationQuestion(Base):
    """Pre-defined calibration questions with known answers."""
    __tablename__ = "calibration_questions"

    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_text: Mapped[str] = mapped_column(String)
    true_answer: Mapped[float] = mapped_column(Float)  # The known correct probability
    category: Mapped[str] = mapped_column(String)  # e.g., "general", "ai_safety"

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "true_answer": self.true_answer,
            "category": self.category,
        }


class CalibrationResponse(Base):
    """Respondent's answer to a calibration question."""
    __tablename__ = "calibration_responses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    respondent_id: Mapped[str] = mapped_column(String, index=True)
    question_id: Mapped[str] = mapped_column(String, index=True)
    predicted_probability: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "respondent_id": self.respondent_id,
            "question_id": self.question_id,
            "predicted_probability": self.predicted_probability,
        }

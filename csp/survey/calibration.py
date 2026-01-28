"""Calibration utilities for expert elicitation."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from csp.survey.models import CalibrationQuestion, CalibrationResponse, SurveyResponse


def compute_brier_score(predictions: list[tuple[float, float | int]]) -> float:
    """Compute Brier score for a set of probability predictions.
    
    Args:
        predictions: List of (predicted_probability, actual_outcome) tuples.
                    actual_outcome should be 0 or 1.
                    
    Returns:
        Brier score (lower is better, 0 is perfect).
    """
    if not predictions:
        return 1.0  # Worst possible score for no predictions
    
    total = 0.0
    for predicted, actual in predictions:
        # Brier score = mean((predicted - actual)^2)
        total += (predicted - actual) ** 2
    
    return total / len(predictions)


def compute_calibration_weight(brier_score: float) -> float:
    """Convert Brier score to a calibration weight.
    
    Lower Brier scores get higher weights.
    Uses a simple inverse transformation.
    
    Args:
        brier_score: Brier score (0 to 1)
        
    Returns:
        Calibration weight (higher is better calibrated)
    """
    # Weight = 1 - Brier score
    # Perfect calibration (Brier=0) → weight=1
    # Random guessing (Brier=0.25) → weight=0.75
    # Worst calibration (Brier=1) → weight=0
    return max(0.0, 1.0 - brier_score)


def calibrate_respondent(
    db: Session, 
    respondent_id: str
) -> tuple[float, float]:
    """Compute calibration metrics for a respondent based on their calibration responses.
    
    Args:
        db: Database session
        respondent_id: ID of the respondent
        
    Returns:
        Tuple of (brier_score, calibration_weight)
    """
    # Get calibration responses
    responses = db.execute(
        select(CalibrationResponse)
        .where(CalibrationResponse.respondent_id == respondent_id)
    ).scalars().all()
    
    if not responses:
        # No calibration data - return neutral weight
        return 0.25, 0.75  # Assume random-ish baseline
    
    # Get corresponding questions for true answers
    predictions = []
    for response in responses:
        question = db.execute(
            select(CalibrationQuestion)
            .where(CalibrationQuestion.question_id == response.question_id)
        ).scalar_one_or_none()
        
        if question:
            # actual_outcome = 1 if true_answer matches prediction direction
            # For simplicity, treating true_answer as the probability we're evaluating against
            predictions.append((response.predicted_probability, question.true_answer))
    
    if not predictions:
        return 0.25, 0.75
    
    brier = compute_brier_score(predictions)
    weight = compute_calibration_weight(brier)
    
    return brier, weight


def update_respondent_calibration(db: Session, respondent_id: str) -> None:
    """Update calibration score for all survey responses from a respondent."""
    brier, weight = calibrate_respondent(db, respondent_id)
    
    # Update all survey responses from this respondent
    responses = db.execute(
        select(SurveyResponse)
        .where(SurveyResponse.respondent_id == respondent_id)
    ).scalars().all()
    
    for response in responses:
        response.calibration_score = weight
    
    db.commit()


def get_all_calibration_weights(db: Session) -> dict[str, float]:
    """Get calibration weights for all respondents with survey responses."""
    weights = {}
    
    respondent_ids = db.execute(
        select(SurveyResponse.respondent_id).distinct()
    ).scalars().all()
    
    for respondent_id in respondent_ids:
        _, weight = calibrate_respondent(db, respondent_id)
        weights[respondent_id] = weight
    
    return weights

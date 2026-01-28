"""Tests for survey module."""

import pytest
from datetime import datetime

from csp.data.db import init_db, get_db
from csp.survey.models import SurveyResponse
from csp.survey.calibration import compute_brier_score, compute_calibration_weight
from csp.survey.aggregation import compute_credible_interval


def test_brier_score_perfect():
    """Perfect predictions should have Brier score near 0."""
    predictions = [(1.0, 1), (0.0, 0), (1.0, 1)]
    score = compute_brier_score(predictions)
    assert score == 0.0


def test_brier_score_worst():
    """Worst predictions should have Brier score near 1."""
    predictions = [(0.0, 1), (1.0, 0)]
    score = compute_brier_score(predictions)
    assert score == 1.0


def test_brier_score_moderate():
    """50% predictions should have Brier score around 0.25."""
    predictions = [(0.5, 1), (0.5, 0)]
    score = compute_brier_score(predictions)
    assert 0.2 <= score <= 0.3


def test_calibration_weight():
    """Lower Brier scores should give higher weights."""
    assert compute_calibration_weight(0.0) == 1.0
    assert compute_calibration_weight(0.25) == 0.75
    assert compute_calibration_weight(1.0) == 0.0


def test_credible_interval():
    """Credible interval should bound reasonable range."""
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    lower, upper = compute_credible_interval(values, 0.90)
    
    assert lower <= 2
    assert upper >= 9


def test_credible_interval_empty():
    """Empty list should return (0, 0)."""
    lower, upper = compute_credible_interval([], 0.90)
    assert (lower, upper) == (0.0, 0.0)


def test_survey_response_model():
    """Test SurveyResponse model to_dict."""
    init_db()
    
    response = SurveyResponse(
        response_id="test_resp_1",
        respondent_id="expert_1",
        created_at=datetime.now().isoformat(),
        calibration_score=0.8,
        responses=[
            {"topic": "RLHF", "dimensions": {"d1": {"score": 3.5, "uncertainty": 0.3}}}
        ]
    )
    
    d = response.to_dict()
    assert d["response_id"] == "test_resp_1"
    assert d["calibration"]["score"] == 0.8
    assert len(d["responses"]) == 1

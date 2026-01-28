"""Survey response aggregation."""

from __future__ import annotations

import statistics
from typing import Any

from sqlalchemy.orm import Session

from csp.survey.models import SurveyResponse
from csp.survey.importer import get_responses_for_topic
from csp.survey.calibration import get_all_calibration_weights


def aggregate_responses(
    db: Session,
    topic: str,
    weighted: bool = True
) -> dict[str, dict[str, Any]]:
    """Aggregate survey responses for a topic into distributions.
    
    Args:
        db: Database session
        topic: Topic to aggregate (e.g., "RLHF", "interpretability")
        weighted: Whether to use calibration weights
        
    Returns:
        Dictionary mapping dimension_id to aggregated statistics:
        {
            "dim_id": {
                "mean": float,
                "median": float,
                "std": float,
                "min": float,
                "max": float,
                "n": int,
                "scores": [list of individual scores],
                "credible_interval_90": (lower, upper),
            }
        }
    """
    responses = get_responses_for_topic(db, topic)
    
    if not responses:
        return {}
    
    # Get calibration weights if needed
    weights = get_all_calibration_weights(db) if weighted else {}
    
    # Collect scores per dimension
    dimension_scores: dict[str, list[tuple[float, float]]] = {}  # dim -> [(score, weight)]
    
    for response in responses:
        respondent_weight = weights.get(response.respondent_id, 1.0) if weighted else 1.0
        
        for resp in response.responses:
            if resp.get("topic") != topic:
                continue
            
            for dim_id, dim_data in resp.get("dimensions", {}).items():
                if dim_id not in dimension_scores:
                    dimension_scores[dim_id] = []
                
                score = dim_data.get("score", 0)
                uncertainty = dim_data.get("uncertainty", 0.5)
                
                # Combine respondent calibration weight with stated uncertainty
                effective_weight = respondent_weight * (1 - uncertainty)
                dimension_scores[dim_id].append((score, effective_weight))
    
    # Aggregate per dimension
    result = {}
    for dim_id, scores_weights in dimension_scores.items():
        scores = [s for s, _ in scores_weights]
        weights_list = [w for _, w in scores_weights]
        
        if not scores:
            continue
        
        # Weighted mean
        total_weight = sum(weights_list)
        if total_weight > 0:
            weighted_mean = sum(s * w for s, w in scores_weights) / total_weight
        else:
            weighted_mean = statistics.mean(scores)
        
        result[dim_id] = {
            "mean": round(weighted_mean, 2),
            "median": round(statistics.median(scores), 2),
            "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0.0,
            "min": min(scores),
            "max": max(scores),
            "n": len(scores),
            "scores": scores,
            "credible_interval_90": compute_credible_interval(scores, 0.90),
        }
    
    return result


def compute_credible_interval(
    values: list[float], 
    level: float = 0.90
) -> tuple[float, float]:
    """Compute empirical credible interval.
    
    Args:
        values: List of values
        level: Credible level (e.g., 0.90 for 90%)
        
    Returns:
        Tuple of (lower, upper) bounds
    """
    if not values:
        return (0.0, 0.0)
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    tail = (1 - level) / 2
    lower_idx = max(0, int(n * tail))
    upper_idx = min(n - 1, int(n * (1 - tail)))
    
    return (round(sorted_values[lower_idx], 2), round(sorted_values[upper_idx], 2))


def get_all_topic_aggregations(db: Session) -> dict[str, dict[str, dict[str, Any]]]:
    """Get aggregations for all topics in the database."""
    from sqlalchemy import select
    
    all_responses = db.execute(select(SurveyResponse)).scalars().all()
    
    # Collect all unique topics
    topics = set()
    for response in all_responses:
        for resp in response.responses:
            topics.add(resp.get("topic"))
    
    topics.discard(None)
    
    return {topic: aggregate_responses(db, topic) for topic in topics}

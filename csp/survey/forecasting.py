"""Forecasting and risk-reward matrix generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from csp.survey.aggregation import aggregate_responses


@dataclass
class TopicAssessment:
    """Assessment for a single topic."""
    topic: str
    csp_score: float  # Aggregated CSP score (0-5)
    csp_uncertainty: float  # Standard deviation
    safety_benefit: float  # Estimated safety benefit (0-5) 
    safety_benefit_uncertainty: float
    risk_reward_ratio: float  # Computed ratio
    rank: int | None = None


def compute_csp_score(dimension_stats: dict[str, dict[str, Any]]) -> tuple[float, float]:
    """Compute overall CSP score from dimension statistics.
    
    Args:
        dimension_stats: Output from aggregate_responses()
        
    Returns:
        Tuple of (mean_score, mean_uncertainty)
    """
    if not dimension_stats:
        return (0.0, 1.0)
    
    means = [d["mean"] for d in dimension_stats.values()]
    stds = [d["std"] for d in dimension_stats.values()]
    
    overall_mean = sum(means) / len(means)
    overall_std = (sum(s**2 for s in stds) / len(stds)) ** 0.5
    
    return (round(overall_mean, 2), round(overall_std, 2))


def generate_risk_reward_matrix(
    db: Session,
    topics: list[str],
    safety_benefit_estimates: dict[str, tuple[float, float]] | None = None,
) -> list[TopicAssessment]:
    """Generate risk-reward matrix for a set of topics.
    
    Args:
        db: Database session
        topics: List of topics to analyze
        safety_benefit_estimates: Optional dict of topic -> (benefit, uncertainty)
                                  If not provided, uses inverse of CSP score
                                  
    Returns:
        List of TopicAssessment objects, ranked by risk-reward ratio
    """
    assessments = []
    
    for topic in topics:
        dim_stats = aggregate_responses(db, topic)
        csp_score, csp_uncertainty = compute_csp_score(dim_stats)
        
        # Get safety benefit estimate
        if safety_benefit_estimates and topic in safety_benefit_estimates:
            safety_benefit, sb_uncertainty = safety_benefit_estimates[topic]
        else:
            # Default: assume safety benefit is inverse of CSP
            # High CSP = high capability spillover = lower safety benefit
            safety_benefit = 5.0 - csp_score
            sb_uncertainty = csp_uncertainty
        
        # Compute risk-reward ratio
        # Higher is better: high safety benefit, low CSP risk
        if csp_score > 0:
            risk_reward = safety_benefit / csp_score
        else:
            risk_reward = safety_benefit * 10  # Very high if no spillover risk
        
        assessments.append(TopicAssessment(
            topic=topic,
            csp_score=csp_score,
            csp_uncertainty=csp_uncertainty,
            safety_benefit=round(safety_benefit, 2),
            safety_benefit_uncertainty=round(sb_uncertainty, 2),
            risk_reward_ratio=round(risk_reward, 2),
        ))
    
    # Rank by risk-reward ratio (higher is better)
    assessments.sort(key=lambda x: x.risk_reward_ratio, reverse=True)
    for i, assessment in enumerate(assessments):
        assessment.rank = i + 1
    
    return assessments


def rank_portfolio_options(
    assessments: list[TopicAssessment],
    budget_constraint: int | None = None,
) -> list[dict[str, Any]]:
    """Rank portfolio options based on risk-reward analysis.
    
    Args:
        assessments: List of TopicAssessment objects
        budget_constraint: Optional limit on number of topics to recommend
        
    Returns:
        List of portfolio recommendations with reasoning
    """
    recommendations = []
    
    for assessment in assessments:
        category = _categorize_assessment(assessment)
        
        recommendations.append({
            "rank": assessment.rank,
            "topic": assessment.topic,
            "category": category,
            "csp_score": assessment.csp_score,
            "safety_benefit": assessment.safety_benefit,
            "risk_reward_ratio": assessment.risk_reward_ratio,
            "recommendation": _generate_recommendation(assessment, category),
            "uncertainty_note": _uncertainty_note(assessment),
        })
    
    if budget_constraint:
        recommendations = recommendations[:budget_constraint]
    
    return recommendations


def _categorize_assessment(assessment: TopicAssessment) -> str:
    """Categorize assessment into portfolio category."""
    if assessment.risk_reward_ratio >= 2.0:
        return "high_priority"
    elif assessment.risk_reward_ratio >= 1.0:
        return "moderate_priority"
    elif assessment.risk_reward_ratio >= 0.5:
        return "low_priority"
    else:
        return "caution"


def _generate_recommendation(assessment: TopicAssessment, category: str) -> str:
    """Generate human-readable recommendation."""
    recommendations = {
        "high_priority": f"Strongly recommend funding. High safety benefit ({assessment.safety_benefit}) with manageable spillover risk.",
        "moderate_priority": f"Recommend funding with monitoring. Balanced risk-reward profile.",
        "low_priority": f"Consider carefully. Moderate spillover concerns (CSP: {assessment.csp_score}).",
        "caution": f"Exercise caution. High spillover potential (CSP: {assessment.csp_score}) relative to safety benefit.",
    }
    return recommendations.get(category, "Insufficient data for recommendation.")


def _uncertainty_note(assessment: TopicAssessment) -> str:
    """Generate uncertainty note based on assessment variance."""
    if assessment.csp_uncertainty > 1.5:
        return "High uncertainty - more expert input recommended."
    elif assessment.csp_uncertainty > 0.8:
        return "Moderate uncertainty in estimates."
    else:
        return "Relatively confident estimates."

"""Core logic for generating case studies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from csp.data.models import Paper, Label
from csp.survey.models import SurveyResponse
from csp.survey.aggregation import aggregate_responses
from csp.survey.forecasting import generate_risk_reward_matrix, TopicAssessment
from csp.data.crud import get_labels_for_paper


@dataclass
class CaseStudyData:
    """Aggregated data for a specific case study topic."""
    topic: str
    paper_count: int
    papers: list[Paper]
    labels: list[dict[str, Any]]
    survey_stats: dict[str, Any]  # Aggregated survey stats
    forecasting_assessment: TopicAssessment | None
    graph_stats: dict[str, Any] | None = None  # Graph analysis stats


def gather_case_study_data(db: Session, topic: str) -> CaseStudyData:
    """Gather all relevant data for a case study topic.
    
    In a real system, we'd need a robust way to link Papers to Topics.
    For this MVP, we will:
    1. Filter papers by title/abstract keywords matching the topic (simple fuzzy search).
    2. Get labels associated with those papers.
    3. Get survey responses for the topic.
    """
    
    # 1. Finds related papers (MVP: naive keyword matching)
    # In production, use tags or specialized 'Topic' table
    all_papers = db.execute(select(Paper)).scalars().all()
    topic_papers = []
    
    for paper in all_papers:
        text_corpus = (paper.title + " " + (paper.abstract or "")).lower()
        if topic.lower() in text_corpus:
            topic_papers.append(paper)
            
    # 2. Get labels for these papers
    relevant_labels = []
    for paper in topic_papers:
        paper_labels = get_labels_for_paper(db, paper.paper_id)
        for lbl in paper_labels:
            relevant_labels.append(lbl.to_dict())
            
    # 3. Get survey stats
    survey_stats = aggregate_responses(db, topic)
    
    # 4. Get forecasting assessment
    assessments = generate_risk_reward_matrix(db, [topic])
    assessments = generate_risk_reward_matrix(db, [topic])
    assessment = assessments[0] if assessments else None
    
    # 5. Graph Analysis
    # Lazy import to avoid circular dependency
    from csp.graph.core import build_graph
    from csp.graph.analysis import compute_diffusion_flow, compute_spillover_score
    
    g = build_graph(topic_papers)
    label_map = {l["paper_id"]: l["label"] for l in relevant_labels}
    
    flow = compute_diffusion_flow(g, label_map)
    spillover = compute_spillover_score(flow)
    
    graph_stats = {
        "node_count": len(g),
        "edge_count": g.number_of_edges(),
        "spillover_score": round(spillover, 3),
        "diffusion_flow": flow
    }
    
    return CaseStudyData(
        topic=topic,
        paper_count=len(topic_papers),
        papers=topic_papers,
        labels=relevant_labels,
        survey_stats=survey_stats,
        forecasting_assessment=assessment,
        graph_stats=graph_stats
    )

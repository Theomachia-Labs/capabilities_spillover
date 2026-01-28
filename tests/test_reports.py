"""Tests for reporting module."""

import pytest
from datetime import datetime

from csp.data.db import init_db, get_db
from csp.data.models import Paper, Label
from csp.data import crud
from sqlalchemy import select
from csp.reports.core import gather_case_study_data
from csp.reports.figures import generate_ascii_diffusion_plot
from csp.reports.policy_brief import generate_policy_brief


def setup_module(module):
    init_db()


def test_gather_case_study_data():
    """Test data aggregation for a topic."""
    with get_db() as db:
        # Create dummy paper
        p = Paper(
            paper_id="report_test_1",
            title="Analysis of RLHF Methods",
            abstract="RLHF is important.",
            year=2024,
            identifiers={},
            authors=[],
            citations=[]
        )
        # Explicitly check and delete if exists to ensure clean state
        existing = db.execute(select(Paper).where(Paper.paper_id == "report_test_1")).scalar_one_or_none()
        if existing:
            db.delete(existing)
            db.commit()
            
        crud.create_paper(db, p.to_dict())

        
        # Create dummy label 
        # Check if label exists first to avoid Primary Key error on re-run
        existing_label = db.execute(select(Label).where(Label.label_id == "lbl_report_1")).scalar_one_or_none()
        if not existing_label:
            l = Label(
                label_id="lbl_report_1", 
                paper_id="report_test_1",
                label="safety_use",
                confidence=0.9,
                method="human",
                created_at=datetime.now().isoformat()
            )
            db.add(l)
            db.commit()

        # Gather data - new session to ensure we read what was committed
        data = gather_case_study_data(db, "RLHF")
        
        assert data.paper_count >= 1
        assert len(data.labels) >= 1
        assert data.topic == "RLHF"


def test_figure_generation():
    """Test ASCII plot generation."""
    from csp.reports.core import CaseStudyData
    
    # Mock data
    paper = Paper(paper_id="p1", title="T", year=2023)
    data = CaseStudyData(
        topic="Test",
        paper_count=1,
        papers=[paper],
        labels=[{"paper_id": "p1", "label": "safety_use"}],
        survey_stats={},
        forecasting_assessment=None
    )
    
    plot = generate_ascii_diffusion_plot(data)
    assert "2023" in plot
    assert "S" in plot  # Bar for safety


def test_policy_brief_generation():
    """Test policy brief text generation."""
    from csp.reports.core import CaseStudyData
    
    data = CaseStudyData(
        topic="Test Topic",
        paper_count=10,
        papers=[],
        labels=[],
        survey_stats={"d1": {"mean": 3.5, "credible_interval_90": (2.0, 4.0)}},
        forecasting_assessment=None
    )
    
    brief = generate_policy_brief(data)
    
    assert "# Policy Brief: Test Topic" in brief
    assert "Papers Analyzed**: 10" in brief
    assert "Mean Score**: 3.5" in brief

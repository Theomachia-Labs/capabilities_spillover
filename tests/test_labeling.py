"""Tests for labeling pipeline."""

import pytest

from csp.data.models import Paper
from csp.labeling.rules import KeywordLabeler
from csp.labeling.llm import LLMLabeler

def test_keyword_labeler_safety():
    paper = Paper(
        paper_id="p1", 
        title="Safety and Alignment in AI", 
        abstract="We discuss robustness and interpretability."
    )
    labeler = KeywordLabeler()
    result = labeler.label_paper(paper)
    
    assert result["label"] == "safety-use"
    assert result["confidence"] > 0.5

def test_keyword_labeler_capability():
    paper = Paper(
        paper_id="p2", 
        title="State of the Art Language Models", 
        abstract="We outperform all benchmarks on accuracy."
    )
    labeler = KeywordLabeler()
    result = labeler.label_paper(paper)
    
    assert result["label"] == "capability-use"

def test_llm_labeler_stub():
    paper = Paper(paper_id="p3", title="Unknown", abstract="Unknown")
    labeler = LLMLabeler()
    result = labeler.label_paper(paper)
    
    assert result["method"] == "llm"
    assert result["label"] in ["safety_use", "capability_use", "mixed", "unclear"]
    assert "audit_status" in result


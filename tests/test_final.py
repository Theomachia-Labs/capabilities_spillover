"""Tests for final polish modules."""

import pytest
from csp.rubric.reliability import compute_percent_agreement, compute_cohens_kappa
from csp.security.redaction import Redactor

def test_reliability_metrics():
    # Perfect agreement
    l1 = ["A", "B", "A"]
    l2 = ["A", "B", "A"]
    assert compute_percent_agreement(l1, l2) == 1.0
    assert compute_cohens_kappa(l1, l2) == 1.0
    
    # Random/No agreement
    l3 = ["A", "A"]
    l4 = ["B", "B"]
    assert compute_percent_agreement(l3, l4) == 0.0
    # Kappa should be negative or 0
    
    # Known Kappa case
    # P1: A A B
    # P2: A B B
    # Agree: 1, 3 (2/3 = 0.66)
    # Expected: 
    # Freq P1: A:2, B:1
    # Freq P2: A:1, B:2
    # Pe = (2/3 * 1/3) + (1/3 * 2/3) = 2/9 + 2/9 = 4/9 = 0.44
    # Kappa = (0.66 - 0.44) / (1 - 0.44) = 0.22 / 0.56 = ~0.4
    k = compute_cohens_kappa(["A", "A", "B"], ["A", "B", "B"])
    assert 0.3 < k < 0.5


def test_redaction():
    r = Redactor()
    text = "This paper discusses a jailbreak prompt for LLMs."
    redacted = r.redact_text(text)
    assert "[REDACTED]" in redacted
    assert "jailbreak prompt" not in redacted
    
    clean = "This is safe."
    assert r.redact_text(clean) == clean

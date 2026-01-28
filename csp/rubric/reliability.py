"""Reliability metrics for inter-rater agreement."""

from __future__ import annotations
from typing import Sequence


def compute_percent_agreement(
    labels1: Sequence[str], 
    labels2: Sequence[str]
) -> float:
    """Compute simple percent agreement between two raters.
    
    Args:
        labels1: List of labels from rater 1
        labels2: List of labels from rater 2
        
    Returns:
        Float between 0.0 and 1.0
    """
    if not labels1 or not labels2:
        return 0.0
    
    if len(labels1) != len(labels2):
        raise ValueError("Label sequences must be same length")
        
    agreement_count = sum(1 for l1, l2 in zip(labels1, labels2) if l1 == l2)
    return agreement_count / len(labels1)


def compute_cohens_kappa(
    labels1: Sequence[str],
    labels2: Sequence[str]
) -> float:
    """Compute Cohen's Kappa for inter-rater reliability.
    
    Kappa = (Po - Pe) / (1 - Pe)
    where Po is observed agreement, Pe is percent agreement expected by chance.
    """
    if not labels1 or not labels2:
        return 0.0
        
    n = len(labels1)
    if len(labels2) != n:
        raise ValueError("Label sequences must be same length")
        
    # Observed Agreement (Po)
    po = compute_percent_agreement(labels1, labels2)
    
    # Expected Agreement (Pe)
    # Calculate label frequencies for each rater
    unique_labels = set(labels1) | set(labels2)
    
    freq1 = {l: 0 for l in unique_labels}
    freq2 = {l: 0 for l in unique_labels}
    
    for l in labels1: freq1[l] += 1
    for l in labels2: freq2[l] += 1
    
    pe = 0.0
    for l in unique_labels:
        prob1 = freq1[l] / n
        prob2 = freq2[l] / n
        pe += (prob1 * prob2)
        
    if pe == 1.0:
        return 1.0  # Perfect agreement on single category
        
    return (po - pe) / (1 - pe)

"""Tests for graph analysis module."""

import pytest
import networkx as nx

from csp.graph.analysis import detect_communities, compute_diffusion_flow, compute_spillover_score


def test_community_detection_simple():
    """Test community detection on two disconnected cliques."""
    # Graph: 0-1-2 (community A) and 3-4-5 (community B)
    g = nx.DiGraph()
    g.add_edges_from([(0,1), (1,2), (2,0)])
    g.add_edges_from([(3,4), (4,5), (5,3)])
    
    communities = detect_communities(g)
    
    assert communities[0] == communities[1] == communities[2]
    assert communities[3] == communities[4] == communities[5]
    assert communities[0] != communities[3]


def test_diffusion_flow():
    """Test diffusion flow calculation."""
    # Graph: Cap(0) -> Safety(1), Safety(1) -> Safety(2)
    # Flow: Safety(1) flows to Cap(0) ? No, Source(0) CITING Target(1)
    # Flow means "Influence". Cited paper influences citing paper.
    # If 0 cites 1, then 1 influenced 0.
    
    g = nx.DiGraph()
    g.add_edge("cap_paper", "safe_paper")  # Cap -> Safety
    g.add_edge("safe_paper", "safe_paper_2") # Safety -> Safety
    
    labels = {
        "cap_paper": "capability_use",
        "safe_paper": "safety_use",
        "safe_paper_2": "safety_use"
    }
    
    flow = compute_diffusion_flow(g, labels)
    
    # Check cap -> safety flow
    # source="capability_use" cites target="safety_use"
    assert flow["capability_use"]["safety_use"] == 1
    assert flow["safety_use"]["safety_use"] == 1


def test_spillover_score():
    """Test spillover score metric."""
    # Scenario: Cap papers make 10 citations total.
    # 3 citations to Safety, 7 to Cap.
    flow = {
        "capability_use": {
            "safety_use": 3,
            "capability_use": 7
        }
    }
    
    score = compute_spillover_score(flow)
    assert score == 0.3
    
    # Scenario: No citations from Cap
    flow2 = {}
    assert compute_spillover_score(flow2) == 0.0

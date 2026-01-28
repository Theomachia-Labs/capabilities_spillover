"""Tests for graph pipeline."""

import networkx as nx
from csp.data.models import Paper
from csp.graph import core, metrics

def test_build_graph():
    p1 = Paper(paper_id="A", title="Paper A", identifiers={}, authors=[], citations=["B"])
    p2 = Paper(paper_id="B", title="Paper B", identifiers={}, authors=[], citations=["C"])
    # C is not in our set, but edge should still be created if desired, or handled.
    # Our impl adds edge P->Cited. NetworkX implicitly adds node if not present.
    
    g = core.build_graph([p1, p2])
    
    assert "A" in g
    assert "B" in g
    assert "C" in g # Implicitly added
    assert g.has_edge("A", "B")
    assert g.has_edge("B", "C")

def test_metrics():
    g = nx.DiGraph()
    g.add_edge("A", "B")
    g.add_edge("C", "B")
    
    # B should have highest pagerank
    pr = metrics.compute_centrality(g)
    assert pr["B"] > pr["A"]
    
    comms = metrics.find_communities(g)
    assert comms["A"] == comms["B"] # Connected component

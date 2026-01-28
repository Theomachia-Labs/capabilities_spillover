"""Advanced graph analysis: Communities and Diffusion Flow."""

from __future__ import annotations

import networkx as nx
from collections import defaultdict
from typing import Any


def detect_communities(g: nx.DiGraph) -> dict[str, int]:
    """Detect communities in the graph.
    
    Uses greedy modularity maximization (available in standard NetworkX).
    Returns mapping of node_id -> community_id.
    """
    if len(g) == 0:
        return {}

    # Greedy modularity requires undirected graph usually, or works on undirected view
    # We'll use the undirected representation for community structure
    g_undirected = g.to_undirected()
    
    try:
        # returns list of frozensets
        communities_list = nx.community.greedy_modularity_communities(g_undirected)
    except (AttributeError, ImportError):
        # Fallback for older NetworkX or if not available
        # Simple connected components as fallback
        communities_list = list(nx.connected_components(g_undirected))

    community_map = {}
    for i, nodes in enumerate(communities_list):
        for node in nodes:
            community_map[node] = i
            
    return community_map


def compute_diffusion_flow(
    g: nx.DiGraph, 
    labels: dict[str, str]
) -> dict[str, dict[str, int]]:
    """Compute diffusion flow between labeled categories.
    
    Labels expected: 'safety_use', 'capability_use', 'mixed', etc.
    
    Returns a matrix (dict of dicts):
    {
        "source_category": {
            "target_category": count_of_citations
        }
    }
    
    Edge A -> B means A cites B. Flow of influence is B -> A (ideas flow from cited to citing).
    However, "Diffusion" usually means "Movement of ideas".
    If P(Safety) cites P(Capability), then Capability ideas are flowing into Safety work.
    We track citations: Source (quoter) -> Target (quoted).
    """
    flow = defaultdict(lambda: defaultdict(int))
    
    for u, v in g.edges():
        # u cites v
        label_u = labels.get(u, "unknown")
        label_v = labels.get(v, "unknown")
        
        flow[label_u][label_v] += 1
        
    # Convert to regular dict
    return {k: dict(v) for k, v in flow.items()}


def compute_spillover_score(flow: dict[str, dict[str, int]]) -> float:
    """Calculate specific spillover metric.
    
    Spillover = (Capability papers citing Safety papers) / (Total citations from Capability papers).
    High score = Capability work is heavily drawing on Safety work.
    """
    cap_flow = flow.get("capability_use", {})
    if not cap_flow:
        return 0.0
        
    citations_to_safety = cap_flow.get("safety_use", 0)
    total_citations_from_cap = sum(cap_flow.values())
    
    if total_citations_from_cap == 0:
        return 0.0
        
    return citations_to_safety / total_citations_from_cap

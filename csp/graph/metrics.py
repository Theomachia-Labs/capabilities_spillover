"""Graph metrics."""

from __future__ import annotations

import networkx as nx

def compute_centrality(g: nx.DiGraph) -> dict[str, float]:
    """Compute PageRank centrality for the graph."""
    if len(g) == 0:
        return {}
    try:
        return nx.pagerank(g)
    except Exception:
        # Fallback for empty or problematic graphs
        return {}

def find_communities(g: nx.DiGraph) -> dict[str, int]:
    """Find communities (stub using weakly connected components for MVP).
    
    Real implementation might use Louvain or Leiden.
    """
    communities = {}
    # Treat as undirected for simple component finding
    for i, component in enumerate(nx.weakly_connected_components(g)):
        for node in component:
            communities[node] = i
    return communities

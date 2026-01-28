"""Graph construction logic."""

from __future__ import annotations

import networkx as nx
from typing import Sequence
from csp.data.models import Paper

def build_graph(papers: Sequence[Paper]) -> nx.DiGraph:
    """Build a citation graph from a list of paper records.
    
    Nodes are paper IDs.
    Edges are citations (paper P cites citation C -> Edge P->C).
    For a diffusion graph, we might want the arrow to represent flow of ideas,
    so P cites C means C influenced P. 
    Standard citation graph: P -> C.
    """
    g = nx.DiGraph()
    
    for p in papers:
        g.add_node(p.paper_id, title=p.title, year=p.year)
        
        if p.citations:
            for cited_id in p.citations:
                g.add_edge(p.paper_id, cited_id)
                
    return g

"""Ingest subsystem.

Provides adapters for fetching research paper metadata from various sources.
"""

from csp.ingest.adapters import BaseSourceAdapter
from csp.ingest.openalex import OpenAlexAdapter
from csp.ingest.semantic_scholar import SemanticScholarAdapter
from csp.ingest.core import ingest_paper

__all__ = [
    "BaseSourceAdapter",
    "OpenAlexAdapter",
    "SemanticScholarAdapter", 
    "ingest_paper",
]

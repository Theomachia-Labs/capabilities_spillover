"""Semantic Scholar source adapter."""

from __future__ import annotations

import os
import requests
from typing import Any, Iterator

from csp.ingest.adapters import BaseSourceAdapter


class SemanticScholarAdapter(BaseSourceAdapter):
    """Adapter for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str | None = None):
        """Initialize adapter.
        
        Args:
            api_key: Semantic Scholar API key for higher rate limits.
        """
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    def _map_paper_to_record(self, paper: dict[str, Any]) -> dict[str, Any]:
        """Map Semantic Scholar paper object to PaperRecord schema."""
        
        # Extract authors
        authors = []
        for author in paper.get("authors", []):
            authors.append({
                "name": author.get("name"),
                "author_id": author.get("authorId")
            })

        # Extract identifiers
        external_ids = paper.get("externalIds", {}) or {}
        identifiers = {
            "s2": paper.get("paperId"),
            "doi": external_ids.get("DOI"),
            "arxiv": external_ids.get("ArXiv"),
            "pubmed": external_ids.get("PubMed"),
        }
        # Filter None values
        identifiers = {k: v for k, v in identifiers.items() if v}

        # Extract citations
        citations = []
        for citation in paper.get("citations", []):
            if citation and citation.get("paperId"):
                citations.append(citation["paperId"])

        return {
            "paper_id": f"s2:{paper['paperId']}",
            "title": paper.get("title"),
            "abstract": paper.get("abstract"),
            "year": paper.get("year"),
            "identifiers": identifiers,
            "authors": authors,
            "citations": citations[:50]  # Limit citations for MVP
        }

    def search(self, query: str, limit: int = 10) -> Iterator[dict[str, Any]]:
        """Search papers by query."""
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "paperId,title,abstract,year,authors,externalIds"
        }
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        data = response.json()
        for paper in data.get("data", []):
            yield self._map_paper_to_record(paper)

    def fetch_metadata(self, identifier: str) -> dict[str, Any] | None:
        """Fetch by Semantic Scholar paper ID or DOI.
        
        Args:
            identifier: Paper ID (e.g., "649def34f8be52c8b66281af98ae884c09aef38b") 
                       or DOI (e.g., "10.1145/3442188.3445922")
        """
        # If identifier looks like a DOI, prefix it
        if identifier.startswith("10."):
            identifier = f"DOI:{identifier}"
        
        url = f"{self.BASE_URL}/paper/{identifier}"
        params = {
            "fields": "paperId,title,abstract,year,authors,externalIds,citations"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._map_paper_to_record(response.json())
        except requests.RequestException:
            return None

    def fetch_citations(self, paper_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch papers that cite the given paper."""
        url = f"{self.BASE_URL}/paper/{paper_id}/citations"
        params = {
            "limit": limit,
            "fields": "paperId,title,year,authors"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            citations = []
            for item in response.json().get("data", []):
                citing_paper = item.get("citingPaper", {})
                if citing_paper.get("paperId"):
                    citations.append(self._map_paper_to_record(citing_paper))
            return citations
        except requests.RequestException:
            return []

    def fetch_references(self, paper_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch papers referenced by the given paper."""
        url = f"{self.BASE_URL}/paper/{paper_id}/references"
        params = {
            "limit": limit,
            "fields": "paperId,title,year,authors"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            references = []
            for item in response.json().get("data", []):
                cited_paper = item.get("citedPaper", {})
                if cited_paper.get("paperId"):
                    references.append(self._map_paper_to_record(cited_paper))
            return references
        except requests.RequestException:
            return []

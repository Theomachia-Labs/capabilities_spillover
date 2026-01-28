"""OpenAlex source adapter."""

from __future__ import annotations

import requests
from typing import Any, Iterator

from csp.ingest.adapters import BaseSourceAdapter


class OpenAlexAdapter(BaseSourceAdapter):
    """Adapter for OpenAlex API."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, email: str | None = None):
        """Initialize adapter.
        
        Args:
            email: Email address for OpenAlex polite pool usage.
        """
        self.headers = {}
        if email:
            self.headers["User-Agent"] = f"CSP-Toolkit/0.1.0 (mailto:{email})"

    def _map_work_to_record(self, work: dict[str, Any]) -> dict[str, Any]:
        """Map OpenAlex work object to PaperRecord schema."""
        
        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            authors.append({
                "name": author.get("display_name"),
                "author_id": author.get("id")
            })

        # Extract identifiers
        ids = work.get("ids", {})
        identifiers = {
            "openalex": ids.get("openalex"),
            "doi": ids.get("doi"),
            "mag": str(ids.get("mag")) if ids.get("mag") else None,
        }
        # Filter None values
        identifiers = {k: v for k, v in identifiers.items() if v}

        return {
            "paper_id": work["id"],  # Use OpenAlex ID as primary
            "title": work.get("display_name"),
            "abstract": work.get("abstract_inverted_index"), # Note: OpenAlex returns inverted index, needs reconstruction if full text needed, or fetch abstract elsewhere if available
            # For MVP simplicity we might leave abstract null or try to reconstruct if critical. 
            # OpenAlex moved to inverted index. reconstruct function is complex. 
            # Storing raw inverted index might not fit schema 'string'. 
            # Let's set abstract to None for now or a placeholder.
            "year": work.get("publication_year"),
            "identifiers": identifiers,
            "authors": authors,
            "citations": [] # OpenAlex provides counts, but list of citations requires separate call
        }

    def search(self, query: str, limit: int = 10) -> Iterator[dict[str, Any]]:
        """Search works by query."""
        params = {
            "search": query,
            "per_page": limit,
        }
        
        response = requests.get(self.BASE_URL, params=params, headers=self.headers)
        response.raise_for_status()
        
        data = response.json()
        for work in data.get("results", []):
            yield self._map_work_to_record(work)

    def fetch_metadata(self, identifier: str) -> dict[str, Any] | None:
        """Fetch by OpenAlex ID (e.g., W2741809807) or DOI."""
        url = f"{self.BASE_URL}/{identifier}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._map_work_to_record(response.json())
        except requests.RequestException:
            # log failure
            return None

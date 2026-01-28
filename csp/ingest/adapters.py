"""Source adapter interfaces."""

from __future__ import annotations

import abc
from typing import Any, Iterator

class BaseSourceAdapter(abc.ABC):
    """Abstract base class for paper data source adapters."""

    @abc.abstractmethod
    def search(self, query: str, limit: int = 10) -> Iterator[dict[str, Any]]:
        """Search for papers by query string.
        
        Yields raw paper record dictionaries compatible with PaperRecord schema.
        """
        pass

    @abc.abstractmethod
    def fetch_metadata(self, identifier: str) -> dict[str, Any] | None:
        """Fetch metadata for a single paper by its primary identifier (e.g. DOI, arXiv ID).
        
        Returns raw paper record dictionary or None if not found.
        """
        pass

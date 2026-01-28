"""Mock source adapter for testing."""

from __future__ import annotations

from typing import Any, Iterator

from csp.ingest.adapters import BaseSourceAdapter

class MockSourceAdapter(BaseSourceAdapter):
    """A mock adapter that returns predefined data."""

    def __init__(self, data: dict[str, dict[str, Any]]):
        self.data = data

    def search(self, query: str, limit: int = 10) -> Iterator[dict[str, Any]]:
        count = 0
        for pid, record in self.data.items():
            if query.lower() in record.get("title", "").lower():
                yield record
                count += 1
                if count >= limit:
                    break

    def fetch_metadata(self, identifier: str) -> dict[str, Any] | None:
        return self.data.get(identifier)

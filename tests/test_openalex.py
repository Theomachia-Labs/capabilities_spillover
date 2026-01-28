"""Tests for OpenAlex adapter."""

import unittest
from unittest.mock import patch, MagicMock
from csp.ingest.openalex import OpenAlexAdapter

class TestOpenAlexAdapter(unittest.TestCase):
    
    @patch("csp.ingest.openalex.requests.get")
    def test_search(self, mock_get):
        # Mock response setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "W123",
                    "display_name": "Test Work",
                    "publication_year": 2023,
                    "ids": {"openalex": "W123", "doi": "10.123/456"},
                    "authorships": [
                        {"author": {"display_name": "Alice", "id": "A1"}}
                    ]
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        adapter = OpenAlexAdapter()
        results = list(adapter.search("test query"))
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["paper_id"], "W123")
        self.assertEqual(results[0]["title"], "Test Work")
        self.assertEqual(results[0]["authors"][0]["name"], "Alice")

    @patch("csp.ingest.openalex.requests.get")
    def test_fetch_metadata(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "W123",
            "display_name": "Test Work",
            "publication_year": 2023
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        adapter = OpenAlexAdapter()
        record = adapter.fetch_metadata("W123")
        
        self.assertIsNotNone(record)
        self.assertEqual(record["paper_id"], "W123")

    @patch("csp.ingest.openalex.requests.get")
    def test_fetch_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        adapter = OpenAlexAdapter()
        record = adapter.fetch_metadata("W999")
        
        self.assertIsNone(record)

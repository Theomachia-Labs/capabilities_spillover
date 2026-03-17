# OpenAlex Downloader & Hybrid Cache Agent Guide

This directory (`openalex_downloader`) contains tools for downloading, locally caching, and querying metadata from the OpenAlex academic database. The core architectural philosophy here is **Local-First with API Fallback**, designed to circumvent API rate limits and network latency when analyzing large collections of papers, specifically tailored towards AI Safety research.

This document serves as a guide for AI agents and human developers interacting with this subsystem.

## 1. Core Architecture

The system operates in two main phases:
1.  **Bulk Acquisition & Caching:** Downloading specific subsets of OpenAlex data and ingesting them into a highly optimized local SQLite database equipped with Full-Text Search (FTS5).
2.  **Hybrid Querying:** Intercepting requests for paper metadata and routing them to the local database first. If the requested paper is not cached locally, it falls back to the live OpenAlex REST API.

## 2. Key Components & Scripts

### Data Ingestion & Storage
*   **`download_targeted.sh`**: A bash script that utilizes the `openalex-cli` to download batches of JSON metadata. It is currently configured to target the "Artificial Intelligence" subfield (ID: 1702) and filter by specific AI Safety queries (e.g., "RLHF", "Constitutional AI"). It correctly handles pagination and can resume interrupted downloads.
*   **`import_openalex.py`**: A Python script that parses the nested JSON files downloaded by the shell script and inserts them into `openalex_local.db`. It establishes the relational schema (`works`, `authors`, `work_authors`, `work_topics`) and maintains the FTS5 virtual tables via SQLite triggers.
*   **`openalex_local.db`**: The resulting SQLite database. *Agents should rarely interact with this directly via SQL, but rather through the provided client classes.*

### Python Clients & Interfaces
*   **`local_openalex.py`**: Contains `LocalOpenAlexClient`. This is the core engine for offline querying. It provides SQL-backed methods to search for works, authors, and relationships instantly. It acts as a drop-in replacement for standard API clients in offline workflows.
*   **`hybrid_lookup.py`**: Contains `HybridOpenAlexClient`. This is the recommended interface for general metadata retrieval. It intelligently attempts to resolve DOIs, OpenAlex IDs, and arXiv IDs against the local database first. If a match is not found, it uses the `OpenAlexAPIClient` (also defined here) to fetch the data directly from the internet.

### Demonstration & Proof of Concept
*   **`run.py`**: A proof-of-concept script. When executed, it initializes the empty SQLite schema (if needed) and, if data is present, runs a 1000-query speed test to demonstrate the performance benefits of local lookups. It outputs `example.txt` showing the query results.
*   **`runHybrid.py`**: A CLI tool to demonstrate the `HybridOpenAlexClient`. It accepts a DOI or arXiv link, fetches the metadata (preferring the local cache), and prints a cleanly formatted summary to the terminal.

## 3. Standard Agent Workflows

### Workflow A: Rebuilding the Local Cache
If the local database needs to be updated or initialized from scratch, an agent should follow these steps:
1.  Delete existing data: `rm openalex_local.db` and `rm -rf openalex_data/`
2.  Initialize the schema: `python3 run.py`
3.  Execute the download and import pipeline: `bash download_targeted.sh`

### Workflow B: Querying Paper Metadata
When an agent needs to retrieve metadata for a specific paper (e.g., to find its authors, citation count, or topics):
1.  **Always prefer `HybridOpenAlexClient`**: Instantiate this client from `hybrid_lookup.py`.
2.  Pass the identifier (DOI like `10.48550/arxiv.2204.05862`, arXiv URL, or OpenAlex ID) to `await client.get_work(identifier)`.
3.  The client will return the standard OpenAlex JSON dictionary, regardless of whether it came from the local DB or the API.

## 4. Important Gotchas & Edge Cases

*   **API DOI Formatting:** The OpenAlex API strictly requires DOIs to be prefixed with `https://doi.org/`. The `HybridOpenAlexClient` handles this normalization automatically before falling back to the API.
*   **arXiv ID Lookups:** The `LocalOpenAlexClient` does not have a dedicated index for `arXiv:` IDs. However, the `HybridOpenAlexClient` gracefully handles this: it will pass the arXiv ID to the API fallback, which *does* support them. Note that many arXiv papers are cached locally under their generated DOI (e.g., `10.48550/arxiv...`), so querying by that DOI will successfully hit the local cache.
*   **Database Schema:** The `raw_json` column in the `works` table contains the complete, unadulterated JSON payload from OpenAlex. `HybridOpenAlexClient` returns this parsed JSON, ensuring 1-to-1 compatibility with responses from the live API.
*   **Subfield Filtering:** OpenAlex's automated topic classification can be broad. For instance, subfield `1702` (Artificial Intelligence) often captures digital rights or internet policy papers if they mention algorithms. This is why `download_targeted.sh` uses very specific keyword filters alongside the subfield filter.

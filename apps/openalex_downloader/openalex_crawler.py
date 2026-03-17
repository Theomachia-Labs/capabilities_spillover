"""OpenAlex-only discovery using the local SQLite database.

Replaces the S2-based BFS crawler for fully offline operation.
Discovers researchers by traversing the co-author graph stored in the
local OpenAlex database (built by import_openalex.py).
"""

from __future__ import annotations

import json
import logging
import math
from typing import Optional

from local_openalex import LocalOpenAlexClient
try:
    from models import Author, CrawlState, Paper
    from state import save_state
except ImportError:
    Author, CrawlState, Paper = None, None, None
    save_state = None

logger = logging.getLogger(__name__)


def _openalex_id(raw_id: str) -> str:
    """Normalise an OpenAlex ID (strip URL prefix if present)."""
    if raw_id.startswith("https://openalex.org/"):
        return raw_id[len("https://openalex.org/"):]
    return raw_id


def _make_author_from_row(client: LocalOpenAlexClient, author_id: str,
                          display_name: str, orcid: str | None) -> Author:
    """Build an Author model from local OpenAlex data."""
    works = client.get_author_works(author_id, limit=500)

    # Compute metrics from works
    paper_count = len(works)
    citation_count = sum(w.get("cited_by_count", 0) for w in works)
    h_index = _compute_h_index([w.get("cited_by_count", 0) for w in works])
    paper_ids = [w["id"] for w in works]

    # Get affiliations from most recent work
    affiliations: list[str] = []
    for w in works:  # already sorted by year desc
        wa_rows = client.get_work_authors(w["id"])
        for wa in wa_rows:
            if wa["id"] == author_id and wa.get("institutions"):
                affiliations = [
                    inst.get("display_name", "")
                    for inst in wa["institutions"]
                    if inst.get("display_name")
                ]
                break
        if affiliations:
            break

    homepage = None
    if orcid:
        homepage = orcid

    return Author(
        s2_id=author_id,  # using openalex ID in this field
        name=display_name,
        affiliations=affiliations,
        homepage=homepage,
        paper_count=paper_count,
        citation_count=citation_count,
        h_index=h_index,
        paper_ids=paper_ids,
    )


def _make_paper_from_work(work: dict) -> Paper:
    """Build a Paper model from a local OpenAlex work row."""
    return Paper(
        s2_id=work["id"],  # using openalex ID
        title=work.get("title") or "",
        abstract=work.get("abstract"),
        venue=None,  # not stored in local DB
        year=work.get("publication_year"),
        citation_count=work.get("cited_by_count", 0),
        author_ids=[],  # populated lazily if needed
        open_access_url=work.get("open_access_url"),
    )


def _compute_h_index(citation_counts: list[int]) -> int:
    """Compute h-index from a list of per-paper citation counts."""
    if not citation_counts:
        return 0
    sorted_counts = sorted(citation_counts, reverse=True)
    h = 0
    for i, c in enumerate(sorted_counts):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h


def seed_expand_openalex(
    client: LocalOpenAlexClient,
    state: CrawlState,
    state_path: str,
) -> None:
    """Find a seed paper in the local DB and populate the initial frontier.

    The seed_paper_id can be a DOI or a search query (title keywords).
    """
    if state.current_stage != "seed":
        return

    seed = state.seed_paper_id
    logger.info(f"Searching local OpenAlex DB for seed: {seed}")

    # Try DOI first
    paper_row = None
    if seed.startswith("10.") or "doi.org" in seed:
        doi = seed
        if not doi.startswith("http"):
            doi = f"https://doi.org/{doi}"
        paper_row = client.get_work_by_doi(doi)

    # Fall back to FTS search
    if not paper_row:
        results = client.search_works(seed, limit=1)
        if results:
            paper_row = results[0]

    if not paper_row:
        raise ValueError(
            f"Seed paper not found in local OpenAlex DB: {seed}\n"
            f"Try a DOI or different title keywords."
        )

    work_id = paper_row["id"]
    paper = _make_paper_from_work(paper_row)
    state.papers[paper.s2_id] = paper

    # Get authors of the seed paper
    work_authors = client.get_work_authors(work_id)
    author_ids = [wa["id"] for wa in work_authors]
    paper.author_ids = author_ids

    for aid in author_ids:
        state.frontier_author_ids.add(aid)

    logger.info(
        f"Seed paper '{paper.title}' (OpenAlex {work_id}) "
        f"has {len(author_ids)} authors"
    )
    state.current_stage = "snowball"
    state.current_cycle = 0
    save_state(state, state_path)


def snowball_one_cycle_openalex(
    client: LocalOpenAlexClient,
    state: CrawlState,
    state_path: str,
    max_authors_per_cycle: int = 0,
) -> bool:
    """Run a single BFS cycle using the local OpenAlex DB.

    Returns True if no more work (frontier exhausted).
    """
    cycle = state.current_cycle
    to_fetch = list(state.frontier_author_ids - state.visited_author_ids)
    if not to_fetch:
        logger.info(f"Cycle {cycle}: no new authors to fetch, stopping early")
        return True

    if max_authors_per_cycle > 0:
        to_fetch = to_fetch[:max_authors_per_cycle]

    logger.info(f"Cycle {cycle}: processing {len(to_fetch)} authors from local DB")

    next_frontier: set[str] = set()
    fetched = 0

    for i, author_id in enumerate(to_fetch):
        if (i + 1) % 50 == 0:
            logger.info(f"  Cycle {cycle}: {i + 1}/{len(to_fetch)} authors processed")

        # Look up author metadata
        rows = client._conn.execute(
            "SELECT id, display_name, orcid FROM authors WHERE id = ?",
            (author_id,),
        ).fetchone()

        if not rows:
            state.visited_author_ids.add(author_id)
            continue

        author = _make_author_from_row(
            client, rows["id"], rows["display_name"], rows["orcid"]
        )
        state.authors[author.s2_id] = author
        state.visited_author_ids.add(author_id)
        fetched += 1

        # Store papers we encounter
        works = client.get_author_works(author_id, limit=500)
        for w in works:
            wid = w["id"]
            if wid not in state.papers:
                state.papers[wid] = _make_paper_from_work(w)

            # Discover co-authors → next frontier
            coauthors = client.get_work_authors(wid)
            for ca in coauthors:
                cid = ca["id"]
                if cid != author_id and cid not in state.visited_author_ids:
                    next_frontier.add(cid)

    state.frontier_author_ids = next_frontier
    state.current_cycle += 1
    logger.info(
        f"Cycle {cycle} complete: {fetched} authors processed, "
        f"{len(next_frontier)} new frontier IDs"
    )
    save_state(state, state_path)
    return False


def apply_filters_openalex(state: CrawlState, config: dict) -> None:
    """Apply filter thresholds — same logic as crawler.apply_filters but
    skips the recent_year paper check when papers lack year data.
    """
    # Delegate to the standard filter logic — it works fine with OpenAlex data
    from .crawler import apply_filters
    apply_filters(state, config)


def populate_paper_authors(client: LocalOpenAlexClient, state: CrawlState) -> None:
    """Populate author_ids on Paper objects (needed for classifier if it
    ever checks co-authorship). Skipped papers not in the local DB are ignored."""
    for pid, paper in state.papers.items():
        if paper.author_ids:
            continue
        try:
            wa = client.get_work_authors(pid)
            paper.author_ids = [a["id"] for a in wa]
        except Exception:
            pass

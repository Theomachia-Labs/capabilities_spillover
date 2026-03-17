"""Local OpenAlex search using SQLite + FTS5.

Drop-in replacement for the REST API client. Queries a local database
built by import_openalex.py instead of hitting the OpenAlex API.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalOpenAlexClient:
    """Query a local OpenAlex SQLite database.

    Provides the same lookup_author() interface as OpenAlexClient,
    plus additional search methods for works, topics, and authors.
    """

    def __init__(self, db_path: str | Path = "openalex_local.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Local OpenAlex database not found at {self.db_path}. "
                f"Run: python import_openalex.py <json_dir> {self.db_path}"
            )
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA query_only=ON")

    def close(self):
        self._conn.close()

    async def aclose(self):
        """Async-compatible close for drop-in compatibility with OpenAlexClient."""
        self.close()

    # -- Drop-in replacement for OpenAlexClient.lookup_author() --

    async def lookup_author(self, name: str) -> dict:
        """Search for an author by name. Matches the REST API client interface."""
        return self.lookup_author_sync(name)

    def lookup_author_sync(self, name: str) -> dict:
        """Synchronous author lookup by name using FTS5."""
        # Sanitize for FTS5 query: quote each token
        tokens = name.strip().split()
        if not tokens:
            return {}
        fts_query = " ".join(f'"{t}"' for t in tokens)

        row = self._conn.execute(
            """SELECT a.id, a.display_name, a.orcid,
                      COUNT(DISTINCT wa.work_id) as works_count,
                      COALESCE(SUM(w.cited_by_count), 0) as cited_by_count
               FROM authors_fts fts
               JOIN authors a ON a.rowid = fts.rowid
               LEFT JOIN work_authors wa ON wa.author_id = a.id
               LEFT JOIN works w ON w.id = wa.work_id
               WHERE authors_fts MATCH ?
               GROUP BY a.id
               ORDER BY rank
               LIMIT 1""",
            (fts_query,),
        ).fetchone()

        if not row:
            return {}

        # Get institutions from most recent work
        inst_row = self._conn.execute(
            """SELECT wa.institutions_json
               FROM work_authors wa
               JOIN works w ON w.id = wa.work_id
               WHERE wa.author_id = ?
               ORDER BY w.publication_year DESC NULLS LAST
               LIMIT 1""",
            (row["id"],),
        ).fetchone()

        institutions = []
        if inst_row and inst_row["institutions_json"]:
            for inst in json.loads(inst_row["institutions_json"]):
                name_ = inst.get("display_name")
                if name_:
                    institutions.append(name_)

        return {
            "openalex_id": row["id"],
            "orcid": row["orcid"],
            "homepage": None,
            "works_count": row["works_count"],
            "cited_by_count": row["cited_by_count"],
            "last_known_institutions": institutions,
        }

    # -- Extended search methods --

    def search_works(self, query: str, *, year_from: int | None = None,
                     year_to: int | None = None, min_citations: int = 0,
                     ai_only: bool = True,
                     limit: int = 50, offset: int = 0) -> list[dict]:
        """Full-text search over work titles and abstracts.

        Args:
            ai_only: If True (default), only return papers tagged as AI subfield.
                     Set to False to search all downloaded papers.
        """
        tokens = query.strip().split()
        if not tokens:
            return []
        fts_query = " ".join(f'"{t}"' for t in tokens)

        conditions = ["works_fts MATCH ?"]
        params: list = [fts_query]

        if ai_only:
            conditions.append("w.is_ai_safety = 1")
        if year_from is not None:
            conditions.append("w.publication_year >= ?")
            params.append(year_from)
        if year_to is not None:
            conditions.append("w.publication_year <= ?")
            params.append(year_to)
        if min_citations > 0:
            conditions.append("w.cited_by_count >= ?")
            params.append(min_citations)

        where = " AND ".join(conditions)
        params.extend([limit, offset])

        rows = self._conn.execute(
            f"""SELECT w.id, w.doi, w.title, w.publication_year,
                       w.cited_by_count, w.open_access_url, w.type,
                       w.abstract
                FROM works_fts fts
                JOIN works w ON w.rowid = fts.rowid
                WHERE {where}
                ORDER BY rank
                LIMIT ? OFFSET ?""",
            params,
        ).fetchall()

        return [dict(r) for r in rows]

    def search_authors(self, query: str, *, limit: int = 20) -> list[dict]:
        """Full-text search over author names."""
        tokens = query.strip().split()
        if not tokens:
            return []
        fts_query = " ".join(f'"{t}"' for t in tokens)

        rows = self._conn.execute(
            """SELECT a.id, a.display_name, a.orcid,
                      COUNT(DISTINCT wa.work_id) as works_count,
                      COALESCE(SUM(w.cited_by_count), 0) as cited_by_count
               FROM authors_fts fts
               JOIN authors a ON a.rowid = fts.rowid
               LEFT JOIN work_authors wa ON wa.author_id = a.id
               LEFT JOIN works w ON w.id = wa.work_id
               WHERE authors_fts MATCH ?
               GROUP BY a.id
               ORDER BY rank
               LIMIT ?""",
            (fts_query, limit),
        ).fetchall()

        return [dict(r) for r in rows]

    def get_work_authors(self, work_id: str) -> list[dict]:
        """Get all authors for a specific work."""
        rows = self._conn.execute(
            """SELECT a.id, a.display_name, a.orcid,
                      wa.author_position, wa.is_corresponding,
                      wa.raw_affiliation, wa.institutions_json
               FROM work_authors wa
               JOIN authors a ON a.id = wa.author_id
               WHERE wa.work_id = ?
               ORDER BY
                 CASE wa.author_position
                   WHEN 'first' THEN 0
                   WHEN 'middle' THEN 1
                   WHEN 'last' THEN 2
                 END""",
            (work_id,),
        ).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["institutions"] = json.loads(d.pop("institutions_json") or "[]")
            results.append(d)
        return results

    def get_author_works(self, author_id: str, *, limit: int = 100) -> list[dict]:
        """Get all works by a specific author."""
        rows = self._conn.execute(
            """SELECT w.id, w.doi, w.title, w.publication_year,
                      w.cited_by_count, w.open_access_url, w.type
               FROM work_authors wa
               JOIN works w ON w.id = wa.work_id
               WHERE wa.author_id = ?
               ORDER BY w.publication_year DESC NULLS LAST
               LIMIT ?""",
            (author_id, limit),
        ).fetchall()

        return [dict(r) for r in rows]

    def get_work_by_doi(self, doi: str) -> dict | None:
        """Look up a work by DOI. Accepts any format:
        - Full URL: https://doi.org/10.1234/...
        - Short: 10.1234/...
        - With http: http://doi.org/10.1234/...
        - With dx: https://dx.doi.org/10.1234/...
        """
        # Normalize to https://doi.org/ format (how OpenAlex stores them)
        doi = doi.strip()
        if doi.startswith("http://doi.org/"):
            doi = "https://doi.org/" + doi[len("http://doi.org/"):]
        elif doi.startswith("https://dx.doi.org/"):
            doi = "https://doi.org/" + doi[len("https://dx.doi.org/"):]
        elif doi.startswith("http://dx.doi.org/"):
            doi = "https://doi.org/" + doi[len("http://dx.doi.org/"):]
        elif not doi.startswith("https://doi.org/"):
            doi = f"https://doi.org/{doi}"
        row = self._conn.execute(
            "SELECT * FROM works WHERE doi = ?", (doi,)
        ).fetchone()
        if row:
            d = dict(row)
            d.pop("raw_json", None)
            return d
        return None

    def get_works_by_topic(self, topic_name: str, *, min_score: float = 0.5,
                           limit: int = 100) -> list[dict]:
        """Get works tagged with a specific topic."""
        rows = self._conn.execute(
            """SELECT w.id, w.doi, w.title, w.publication_year,
                      w.cited_by_count, w.open_access_url,
                      wt.display_name as topic, wt.score as topic_score
               FROM work_topics wt
               JOIN works w ON w.id = wt.work_id
               WHERE wt.display_name LIKE ? AND wt.score >= ?
               ORDER BY w.cited_by_count DESC
               LIMIT ?""",
            (f"%{topic_name}%", min_score, limit),
        ).fetchall()

        return [dict(r) for r in rows]

    def get_works_by_concept(self, concept_name: str, *, min_score: float = 0.5,
                             limit: int = 100) -> list[dict]:
        """Get works tagged with a specific concept."""
        rows = self._conn.execute(
            """SELECT w.id, w.doi, w.title, w.publication_year,
                      w.cited_by_count, w.open_access_url,
                      wc.display_name as concept, wc.score as concept_score
               FROM work_concepts wc
               JOIN works w ON w.id = wc.work_id
               WHERE wc.display_name LIKE ? AND wc.score >= ?
               ORDER BY w.cited_by_count DESC
               LIMIT ?""",
            (f"%{concept_name}%", min_score, limit),
        ).fetchall()

        return [dict(r) for r in rows]

    def stats(self) -> dict:
        """Return database statistics."""
        result = {}
        for table in ["works", "authors", "work_authors", "work_concepts",
                       "work_topics", "work_keywords"]:
            row = self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            result[table] = row[0]

        year_rows = self._conn.execute(
            """SELECT publication_year, COUNT(*) as cnt
               FROM works
               WHERE publication_year IS NOT NULL
               GROUP BY publication_year
               ORDER BY publication_year"""
        ).fetchall()
        result["works_by_year"] = {r[0]: r[1] for r in year_rows}
        return result

    def get_raw_work(self, work_id: str) -> dict | None:
        """Get the full raw JSON for a work (for debugging/inspection)."""
        row = self._conn.execute(
            "SELECT raw_json FROM works WHERE id = ?", (work_id,)
        ).fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return None

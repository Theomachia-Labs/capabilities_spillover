"""Import downloaded OpenAlex JSON files into a local SQLite database."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS works (
    id TEXT PRIMARY KEY,
    doi TEXT,
    title TEXT,
    publication_year INTEGER,
    publication_date TEXT,
    language TEXT,
    type TEXT,
    cited_by_count INTEGER DEFAULT 0,
    is_retracted INTEGER DEFAULT 0,
    is_ai_safety INTEGER DEFAULT 0,
    abstract TEXT,
    open_access_url TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS authors (
    id TEXT PRIMARY KEY,
    display_name TEXT,
    orcid TEXT
);

CREATE TABLE IF NOT EXISTS work_authors (
    work_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    author_position TEXT,
    is_corresponding INTEGER DEFAULT 0,
    raw_affiliation TEXT,
    institutions_json TEXT,
    PRIMARY KEY (work_id, author_id),
    FOREIGN KEY (work_id) REFERENCES works(id),
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

CREATE TABLE IF NOT EXISTS work_concepts (
    work_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    display_name TEXT,
    level INTEGER,
    score REAL,
    PRIMARY KEY (work_id, concept_id),
    FOREIGN KEY (work_id) REFERENCES works(id)
);

CREATE TABLE IF NOT EXISTS work_topics (
    work_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    display_name TEXT,
    score REAL,
    subfield TEXT,
    field TEXT,
    domain TEXT,
    PRIMARY KEY (work_id, topic_id),
    FOREIGN KEY (work_id) REFERENCES works(id)
);

CREATE TABLE IF NOT EXISTS work_keywords (
    work_id TEXT NOT NULL,
    keyword_id TEXT NOT NULL,
    display_name TEXT,
    score REAL,
    PRIMARY KEY (work_id, keyword_id),
    FOREIGN KEY (work_id) REFERENCES works(id)
);

CREATE INDEX IF NOT EXISTS idx_works_ai_safety ON works(is_ai_safety);
CREATE INDEX IF NOT EXISTS idx_works_year ON works(publication_year);
CREATE INDEX IF NOT EXISTS idx_works_cited ON works(cited_by_count);
CREATE INDEX IF NOT EXISTS idx_works_doi ON works(doi);
CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(display_name);
CREATE INDEX IF NOT EXISTS idx_authors_orcid ON authors(orcid);
CREATE INDEX IF NOT EXISTS idx_work_authors_author ON work_authors(author_id);
CREATE INDEX IF NOT EXISTS idx_work_concepts_concept ON work_concepts(concept_id);
CREATE INDEX IF NOT EXISTS idx_work_topics_topic ON work_topics(topic_id);

-- FTS5 virtual tables for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS works_fts USING fts5(
    id UNINDEXED, title, abstract, content=works, content_rowid=rowid
);

CREATE VIRTUAL TABLE IF NOT EXISTS authors_fts USING fts5(
    id UNINDEXED, display_name, content=authors, content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS works_ai AFTER INSERT ON works BEGIN
    INSERT INTO works_fts(rowid, id, title, abstract)
    VALUES (new.rowid, new.id, new.title, new.abstract);
END;

CREATE TRIGGER IF NOT EXISTS authors_ai AFTER INSERT ON authors BEGIN
    INSERT INTO authors_fts(rowid, id, display_name)
    VALUES (new.rowid, new.id, new.display_name);
END;

-- Metadata table for tracking import state
CREATE TABLE IF NOT EXISTS import_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Reconstruct abstract text from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions) if word_positions else None


def _extract_open_access_url(work: dict) -> str | None:
    """Get the best open access URL from a work."""
    oa = work.get("best_oa_location") or {}
    url = oa.get("pdf_url") or oa.get("landing_page_url")
    if not url:
        oa_info = work.get("open_access") or {}
        url = oa_info.get("oa_url")
    return url


def create_db(db_path: str | Path) -> sqlite3.Connection:
    """Create the database and return a connection."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    conn.executescript(SCHEMA)
    return conn


def import_work(conn: sqlite3.Connection, work: dict) -> bool:
    """Import a single work JSON dict into the database. Returns True if new."""
    work_id = work.get("id", "")
    if not work_id:
        return False

    # Check if already imported
    row = conn.execute("SELECT 1 FROM works WHERE id = ?", (work_id,)).fetchone()
    if row:
        return False

    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
    oa_url = _extract_open_access_url(work)

    # Check if any topic is in the AI subfield
    is_ai = 0
    for topic in work.get("topics") or []:
        sf = (topic.get("subfield") or {}).get("display_name", "")
        if sf == "Artificial Intelligence" and (topic.get("score", 0) or 0) > 0.5:
            is_ai = 1
            break

    conn.execute(
        """INSERT OR IGNORE INTO works
           (id, doi, title, publication_year, publication_date, language, type,
            cited_by_count, is_retracted, is_ai_safety, abstract, open_access_url, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            work_id,
            work.get("doi"),
            work.get("title") or work.get("display_name"),
            work.get("publication_year"),
            work.get("publication_date"),
            work.get("language"),
            work.get("type"),
            work.get("cited_by_count", 0),
            1 if work.get("is_retracted") else 0,
            is_ai,
            abstract,
            oa_url,
            json.dumps(work),
        ),
    )

    # Import authorships
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        author_id = author.get("id", "")
        if not author_id:
            continue

        conn.execute(
            "INSERT OR IGNORE INTO authors (id, display_name, orcid) VALUES (?, ?, ?)",
            (author_id, author.get("display_name"), author.get("orcid")),
        )

        institutions = [
            {"id": inst.get("id"), "display_name": inst.get("display_name"),
             "country_code": inst.get("country_code"), "type": inst.get("type")}
            for inst in (authorship.get("institutions") or [])
        ]
        raw_affils = "; ".join(authorship.get("raw_affiliation_strings") or [])

        conn.execute(
            """INSERT OR IGNORE INTO work_authors
               (work_id, author_id, author_position, is_corresponding,
                raw_affiliation, institutions_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                work_id, author_id,
                authorship.get("author_position"),
                1 if authorship.get("is_corresponding") else 0,
                raw_affils,
                json.dumps(institutions),
            ),
        )

    # Import concepts
    for concept in work.get("concepts") or []:
        concept_id = concept.get("id", "")
        if concept_id:
            conn.execute(
                """INSERT OR IGNORE INTO work_concepts
                   (work_id, concept_id, display_name, level, score)
                   VALUES (?, ?, ?, ?, ?)""",
                (work_id, concept_id, concept.get("display_name"),
                 concept.get("level"), concept.get("score")),
            )

    # Import topics
    for topic in work.get("topics") or []:
        topic_id = topic.get("id", "")
        if topic_id:
            conn.execute(
                """INSERT OR IGNORE INTO work_topics
                   (work_id, topic_id, display_name, score, subfield, field, domain)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    work_id, topic_id, topic.get("display_name"), topic.get("score"),
                    (topic.get("subfield") or {}).get("display_name"),
                    (topic.get("field") or {}).get("display_name"),
                    (topic.get("domain") or {}).get("display_name"),
                ),
            )

    # Import keywords
    for kw in work.get("keywords") or []:
        kw_id = kw.get("id", "")
        if kw_id:
            conn.execute(
                """INSERT OR IGNORE INTO work_keywords
                   (work_id, keyword_id, display_name, score)
                   VALUES (?, ?, ?, ?)""",
                (work_id, kw_id, kw.get("display_name"), kw.get("score")),
            )

    return True


def import_directory(json_dir: str | Path, db_path: str | Path,
                     batch_size: int = 500) -> int:
    """Import all JSON files from a directory into the database.

    Returns the number of newly imported works.
    """
    json_dir = Path(json_dir)
    db_path = Path(db_path)

    conn = create_db(db_path)
    imported = 0
    skipped = 0
    errors = 0
    total_files = 0

    # Collect all JSON files (supports flat and nested layouts)
    json_files = sorted(json_dir.rglob("*.json"))
    # Filter out checkpoint and log files
    json_files = [f for f in json_files if "checkpoint" not in f.name
                  and f.name != "openalex-download.log"]
    total_files = len(json_files)

    logger.info(f"Found {total_files} JSON files to import from {json_dir}")

    for i, fpath in enumerate(json_files):
        try:
            with open(fpath) as f:
                work = json.load(f)
            if import_work(conn, work):
                imported += 1
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                logger.warning(f"Error importing {fpath.name}: {e}")

        if (i + 1) % batch_size == 0:
            conn.commit()
            logger.info(f"Progress: {i + 1}/{total_files} files "
                        f"({imported} new, {skipped} existing, {errors} errors)")

    conn.commit()

    # Store import metadata
    conn.execute(
        "INSERT OR REPLACE INTO import_meta (key, value) VALUES (?, ?)",
        ("last_import_count", str(imported)),
    )
    conn.execute(
        "INSERT OR REPLACE INTO import_meta (key, value) VALUES (?, ?)",
        ("total_works", str(imported + skipped)),
    )
    conn.commit()
    conn.close()

    logger.info(f"Import complete: {imported} new, {skipped} existing, "
                f"{errors} errors out of {total_files} files")
    return imported


def main():
    """CLI entry point for importing OpenAlex data."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    json_dir = sys.argv[1] if len(sys.argv) > 1 else "openalex_data"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "openalex_local.db"

    logger.info(f"Importing from {json_dir} -> {db_path}")
    count = import_directory(json_dir, db_path)
    logger.info(f"Done. {count} works imported.")


if __name__ == "__main__":
    main()

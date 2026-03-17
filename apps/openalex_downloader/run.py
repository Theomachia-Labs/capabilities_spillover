import os
import sys
import time
import random
from pathlib import Path
import sqlite3
import asyncio

# Add current directory to path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from import_openalex import SCHEMA
from local_openalex import LocalOpenAlexClient

DB_PATH = "openalex_local.db"

def init_db():
    """Initialize the database if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        print(f"Initializing database: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SCHEMA)
        conn.close()
        print("Database initialized with schema.")
    else:
        print(f"Database already exists: {DB_PATH}")

def check_populated():
    """Check if the database has any works."""
    if not os.path.exists(DB_PATH):
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        conn.close()
        return count > 0
    except sqlite3.OperationalError:
        return False

async def run_speed_test():
    """Run a batch of 1000 queries to demonstrate lookup speed."""
    print("\n--- Speed Test: 1000 Local Lookups ---")
    try:
        client = LocalOpenAlexClient(DB_PATH)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Fetch some sample work IDs or DOIs to use for lookups
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    works = conn.execute("SELECT id, doi, title FROM works WHERE is_ai_safety = 1 LIMIT 100").fetchall()
    conn.close()
    
    if not works:
        print("No works found to query!")
        client.close()
        return

    sample_works = [dict(w) for w in works]
    sample_ids = [w["id"] for w in works]
    sample_dois = [w["doi"] for w in works if w["doi"]]

    print(f"Starting 1000 queries against {len(works)} unique records...")
    
    metadata_lines = []
    start_time = time.time()
    
    for i in range(1000):
        # Pick a random work to query
        target = random.choice(sample_works)
        work_id = target["id"]
        
        # Perform lookups
        # 1. Get work details (either by DOI or ID)
        if sample_dois and i % 2 == 0:
            doi = random.choice(sample_dois)
            work = client.get_work_by_doi(doi)
        else:
            work = client.get_raw_work(work_id)
            
        # 2. Get authors for the metadata output
        authors = client.get_work_authors(work_id)
        author_names = [a["display_name"] for a in authors]
        
        # Prepare metadata line for the example file
        title = target["title"] or "Unknown Title"
        authors_str = ", ".join(author_names) if author_names else "No Authors Listed"
        metadata_lines.append(f"Query {i+1:04d} | Title: {title} | Authors: {authors_str}")
            
        if (i + 1) % 100 == 0:
            print(f"Completed {i + 1} queries...")

    end_time = time.time()
    duration = end_time - start_time
    
    # Write metadata to example.txt
    with open("example.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(metadata_lines))
    
    print(f"\nFinished 1000 queries in {duration:.2f} seconds.")
    print(f"Average query time: {(duration / 1000) * 1000:.2f} ms")
    print(f"Example metadata saved to: example.txt")
    client.close()

async def main():
    print("OpenAlex Local Downloader & Lookup Proof of Concept")
    print("====================================================")
    
    init_db()
    
    if not check_populated():
        print("\nDatabase is currently empty.")
        print("To populate the database with a set of papers, run:")
        print("  bash download_targeted.sh")
        print("\nNote: download_targeted.sh requires a Python environment with the 'openalex-cli' package.")
    else:
        print("\nDatabase is populated. Running proof-of-concept speed test...")
        await run_speed_test()

if __name__ == "__main__":
    asyncio.run(main())

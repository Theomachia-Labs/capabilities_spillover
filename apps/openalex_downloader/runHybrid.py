#!/usr/bin/env python3
import argparse
import asyncio
import sys
import logging
from typing import Dict, Any

from hybrid_lookup import HybridOpenAlexClient

# Silent library logging for cleaner terminal output
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("hybrid_lookup").setLevel(logging.INFO)

def print_metadata(work: Dict[str, Any]):
    """Print selected OpenAlex metadata in a readable format."""
    print("\n" + "="*80)
    print(f"TITLE: {work.get('title')}")
    print("="*80)
    
    # Core Metadata
    year = work.get('publication_year')
    doi = work.get('doi')
    oa_status = (work.get('open_access') or {}).get('is_oa')
    
    print(f"YEAR:   {year}")
    print(f"DOI:    {doi}")
    print(f"ID:     {work.get('id')}")
    print(f"TYPE:   {work.get('type')}")
    print(f"CITED:  {work.get('cited_by_count')}")
    print(f"OA:     {'Yes' if oa_status else 'No'}")
    
    # Authors
    authorships = work.get('authorships') or []
    author_names = []
    for authorship in authorships:
        author = authorship.get('author') or {}
        name = author.get('display_name')
        if name:
            author_names.append(name)
            
    print("\nAUTHORS:")
    if author_names:
        print(", ".join(author_names[:20])) # Cap to avoid wall of text
        if len(author_names) > 20:
            print(f"... and {len(author_names)-20} more authors.")
    else:
        print("None listed.")

    # Topics/Concepts
    topics = work.get('topics') or []
    concepts = work.get('concepts') or []
    
    print("\nTOPICS:")
    if topics:
        for t in topics[:5]:
            print(f"- {t.get('display_name')} (score: {t.get('score', 0):.2f})")
    elif concepts:
        for c in concepts[:5]:
            print(f"- {c.get('display_name')} (score: {c.get('score', 0):.2f})")
    else:
        print("None listed.")
        
    print("="*80 + "\n")

async def main():
    parser = argparse.ArgumentParser(description="Hybrid OpenAlex Metadata Fetcher (Local + API)")
    parser.add_argument("identifier", help="DOI, arXiv ID, or OpenAlex ID")
    parser.add_argument("--db", default="openalex_local.db", help="Path to local database")
    parser.add_argument("--email", help="Optional email for OpenAlex API 'mailto' polite pool")
    
    args = parser.parse_args()

    client = HybridOpenAlexClient(db_path=args.db, email=args.email)
    
    try:
        work = await client.get_work(args.identifier)
        if work:
            print_metadata(work)
        else:
            print(f"Could not find metadata for: {args.identifier}")
            sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())

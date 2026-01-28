"""Unified data pipeline script.

Ingests papers from multiple sources, applies labeling, and persists to database.
"""

import argparse
import sys
from pathlib import Path

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from csp.data.db import init_db, get_db
from csp.data import crud
from csp.ingest.openalex import OpenAlexAdapter
from csp.ingest.semantic_scholar import SemanticScholarAdapter
from csp.ingest.core import ingest_paper
from csp.labeling.rules import KeywordLabeler
from csp.labeling.llm import LLMLabeler
from csp.labeling import audit


def get_adapter(source: str, email: str | None = None):
    """Get adapter by source name."""
    if source == "openalex":
        return OpenAlexAdapter(email=email)
    elif source == "s2":
        return SemanticScholarAdapter()
    else:
        raise ValueError(f"Unknown source: {source}")


def get_labeler(method: str):
    """Get labeler by method name."""
    if method == "rules":
        return KeywordLabeler()
    elif method == "llm":
        return LLMLabeler()
    else:
        raise ValueError(f"Unknown labeling method: {method}")


def ingest_and_label(paper_id: str, source: str = "openalex", 
                      labeling_method: str = "rules", email: str | None = None,
                      save_label: bool = True):
    """Ingest a paper and apply labeling.
    
    Args:
        paper_id: Paper identifier (OpenAlex ID, DOI, or S2 ID)
        source: Data source ("openalex" or "s2")
        labeling_method: Labeling method ("rules" or "llm")
        email: Email for API polite pool
        save_label: Whether to save label to database
    
    Returns:
        Tuple of (paper, label_record)
    """
    init_db()
    
    adapter = get_adapter(source, email)
    labeler = get_labeler(labeling_method)
    
    with get_db() as db:
        # Ingest
        paper = ingest_paper(db, adapter, paper_id)
        
        # Label
        label_record = labeler.label_paper(paper)
        
        # Save label (routes to audit if low confidence)
        if save_label:
            saved_label = audit.route_to_audit(db, label_record)
            return paper, saved_label.to_dict()
        
        return paper, label_record


def batch_ingest(ids: list[str], source: str = "openalex",
                 labeling_method: str = "rules", email: str | None = None):
    """Batch ingest multiple papers."""
    results = []
    for paper_id in ids:
        try:
            paper, label = ingest_and_label(paper_id, source, labeling_method, email)
            results.append({
                "paper_id": paper.paper_id,
                "title": paper.title,
                "label": label["label"],
                "confidence": label["confidence"],
                "audit_status": label.get("audit_status", "unknown"),
                "status": "success"
            })
        except Exception as e:
            results.append({
                "paper_id": paper_id,
                "status": "error",
                "error": str(e)
            })
    return results


def main():
    parser = argparse.ArgumentParser(description="Unified Data Pipeline: Ingest and Label.")
    parser.add_argument("--id", help="Paper ID to ingest (OpenAlex ID, DOI, or S2 ID)", required=True)
    parser.add_argument("--source", choices=["openalex", "s2"], default="openalex",
                       help="Data source (default: openalex)")
    parser.add_argument("--labeler", choices=["rules", "llm"], default="rules",
                       help="Labeling method (default: rules)")
    parser.add_argument("--email", help="Email for API polite pool", default=None)
    parser.add_argument("--no-save", action="store_true", help="Don't save label to DB")
    args = parser.parse_args()

    print(f"Source: {args.source} | Labeler: {args.labeler}")
    print(f"Fetching metadata for {args.id}...")
    
    try:
        paper, label_record = ingest_and_label(
            args.id, 
            source=args.source,
            labeling_method=args.labeler,
            email=args.email,
            save_label=not args.no_save
        )
        
        print(f"\n✅ Ingested: {paper.title} ({paper.year})")
        print(f"   Label: {label_record['label']} (Confidence: {label_record['confidence']:.0%})")
        print(f"   Audit Status: {label_record.get('audit_status', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

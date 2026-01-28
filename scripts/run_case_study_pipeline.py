"""Master pipeline script for running a complete case study."""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from csp.data.db import init_db, get_db
from csp.data import crud
from scripts.refresh_pipeline import batch_ingest
from csp.reports.core import gather_case_study_data
from csp.reports.policy_brief import generate_policy_brief
from csp.security.redaction import Redactor

def run_pipeline(
    topic: str,
    seed_ids: list[str],
    source: str = "openalex",
    labeler: str = "rules",
    output_dir: str = "output"
):
    """Run the end-to-end case study pipeline.
    
    1. Ingest seed papers.
    2. Label papers (and dependencies if expanded).
    3. Generate case study report.
    """
    print(f"🚀 Starting Case Study Pipeline for: {topic}")
    print(f"ℹ️  Seed Papers: {len(seed_ids)}")
    
    # 1. Ingest & Label
    print("📥 Ingesting and Labeling...")
    results = batch_ingest(seed_ids, source=source, labeling_method=labeler)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"✅ Successfully ingested {success_count}/{len(seed_ids)} papers.")
    if success_count == 0:
        print("❌ No papers ingested. Aborting.")
        return

    # 2. Generate Report
    print("📊 Generating Policy Brief...")
    with get_db() as db:
        # Note: gather_case_study_data currently relies on keyword matching in DB
        # If seed papers don't match the topic string in title/abstract, they might be missed by the report generator
        # unless we explicitly link them.
        # For this MVP pipeline, we trust the topic string matches the seed papers or we force it.
        # Ideally, we'd tag these papers with the topic in the DB.
        
        data = gather_case_study_data(db, topic)
        
        # Determine if we found enough data
        if data.paper_count == 0:
            print(f"⚠️  No papers found matching topic '{topic}' in database.")
            print("   (Ensure seed papers contain the topic keywords in Title/Abstract)")
        
        brief = generate_policy_brief(data)
        
    # 3. Export
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)
    
    filename = f"{topic.replace(' ', '_')}_Case_Study.md"
    file_path = out_path / filename
    
    with open(file_path, "w") as f:
        f.write(brief)
        
    print(f"💾 Report saved to: {file_path}")
    print("✨ Pipeline Complete!")


def main():
    parser = argparse.ArgumentParser(description="Run complete Case Study Pipeline.")
    parser.add_argument("--topic", required=True, help="Topic name (used for report generation and keyword search)")
    parser.add_argument("--seeds", required=True, help="Comma-separated list of seed paper IDs (OpenAlex/DOI)")
    parser.add_argument("--source", default="openalex", choices=["openalex", "s2"])
    parser.add_argument("--labeler", default="rules", choices=["rules", "llm"])
    parser.add_argument("--output", default="output", help="Output directory")
    
    args = parser.parse_args()
    
    seed_ids = [s.strip() for s in args.seeds.split(",") if s.strip()]
    
    run_pipeline(
        topic=args.topic,
        seed_ids=seed_ids,
        source=args.source,
        labeler=args.labeler,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()

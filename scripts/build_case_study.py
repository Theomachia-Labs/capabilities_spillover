"""Case Study Builder Script.

Generates a policy brief for a specific topic.
"""

import argparse
import sys
from pathlib import Path

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from csp.data.db import init_db, get_db
from csp.reports.core import gather_case_study_data
from csp.reports.policy_brief import generate_policy_brief


def main():
    parser = argparse.ArgumentParser(description="Generate Case Study Policy Brief.")
    parser.add_argument("--topic", help="Topic keywords to filter papers (e.g., 'RLHF')", required=True)
    parser.add_argument("--output", help="Output Markdown file path", default=None)
    args = parser.parse_args()

    init_db()
    
    print(f"Gathering data for topic: {args.topic}...")
    
    with get_db() as db:
        data = gather_case_study_data(db, args.topic)
        
        if data.paper_count == 0:
            print("❌ No papers found for this topic.")
            return

        print(f"Found {data.paper_count} papers and {len(data.labels)} labels.")
        
        brief = generate_policy_brief(data)
        
        output_path = args.output or f"{args.topic.replace(' ', '_')}_Policy_Brief.md"
        with open(output_path, "w") as f:
            f.write(brief)
            
        print(f"✅ Policy brief generated: {output_path}")


if __name__ == "__main__":
    main()

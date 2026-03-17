#!/usr/bin/env python3
"""Download and import OpenAlex data locally.

Usage:
    # Download AI safety papers (default query)
    python download_openalex.py

    # Download with a custom filter
    python download_openalex.py --filter "default.search:interpretability,from_publication_date:2015-01-01"

    # Import only (skip download, e.g. after a resumed download)
    python download_openalex.py --import-only

    # Download a different topic and add to existing database
    python download_openalex.py --filter "default.search:machine learning robustness,from_publication_date:2010-01-01"

    # Check database stats
    python download_openalex.py --stats
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_DATA_DIR = PROJECT_DIR / "openalex_data"
DEFAULT_DB_PATH = PROJECT_DIR / "openalex_local.db"
DEFAULT_FILTER = "primary_topic.subfield.id:1702,from_publication_date:2010-01-01,default.search:AI safety alignment"

# Find the openalex CLI in the project venv
VENV_BIN = PROJECT_DIR / "venv" / "bin"


def find_openalex_cli() -> str:
    """Find the openalex CLI executable."""
    venv_cli = VENV_BIN / "openalex"
    if venv_cli.exists():
        return str(venv_cli)
    system_cli = shutil.which("openalex")
    if system_cli:
        return system_cli
    raise FileNotFoundError(
        "openalex CLI not found. Install with: pip install openalex-official"
    )


def download(api_key: str, filter_str: str, output_dir: Path,
             workers: int = 8, resume: bool = True) -> None:
    """Run the OpenAlex CLI to download metadata."""
    cli = find_openalex_cli()

    cmd = [
        cli, "download",
        "--api-key", api_key,
        "--output", str(output_dir),
        "--filter", filter_str,
        "--nested",
        "--workers", str(workers),
    ]
    if resume:
        cmd.append("--resume")
    else:
        cmd.append("--fresh")

    logger.info(f"Starting download: filter={filter_str!r}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Workers: {workers}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Download interrupted. Run again with --resume to continue.")
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed with exit code {e.returncode}")
        raise SystemExit(1)


def import_to_db(data_dir: Path, db_path: Path) -> None:
    """Import downloaded JSON files into SQLite."""
    # Import here to avoid circular imports when used as a script
    sys.path.insert(0, str(PROJECT_DIR))
    from import_openalex import import_directory
    import_directory(data_dir, db_path)


def show_stats(db_path: Path) -> None:
    """Show database statistics."""
    from local_openalex import LocalOpenAlexClient

    client = LocalOpenAlexClient(db_path)
    stats = client.stats()
    client.close()

    print(f"\nDatabase: {db_path}")
    print(f"  Works:        {stats['works']:,}")
    print(f"  Authors:      {stats['authors']:,}")
    print(f"  Authorships:  {stats['work_authors']:,}")
    print(f"  Concepts:     {stats['work_concepts']:,}")
    print(f"  Topics:       {stats['work_topics']:,}")
    print(f"  Keywords:     {stats['work_keywords']:,}")
    print(f"\n  Works by year:")
    for year, count in sorted(stats.get("works_by_year", {}).items()):
        bar = "#" * min(count // 100, 60)
        print(f"    {year}: {count:>6,}  {bar}")


def main():
    parser = argparse.ArgumentParser(
        description="Download and import OpenAlex data locally"
    )
    parser.add_argument(
        "--api-key", default="td1fSpoJ9COOKXpm4zXrPz",
        help="OpenAlex API key (default: from config)",
    )
    parser.add_argument(
        "--filter", default=DEFAULT_FILTER,
        help=f"OpenAlex filter string (default: {DEFAULT_FILTER!r})",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR,
        help="Directory for downloaded JSON files",
    )
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB_PATH,
        help="Path to SQLite database",
    )
    parser.add_argument(
        "--workers", type=int, default=8,
        help="Number of concurrent download workers (default: 8)",
    )
    parser.add_argument(
        "--import-only", action="store_true",
        help="Skip download, only import existing JSON files into DB",
    )
    parser.add_argument(
        "--download-only", action="store_true",
        help="Only download, don't import into DB",
    )
    parser.add_argument(
        "--fresh", action="store_true",
        help="Start a fresh download (ignore checkpoint)",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show database statistics and exit",
    )

    args = parser.parse_args()

    if args.stats:
        show_stats(args.db)
        return

    if not args.import_only:
        args.data_dir.mkdir(parents=True, exist_ok=True)
        download(args.api_key, args.filter, args.data_dir,
                 workers=args.workers, resume=not args.fresh)

    if not args.download_only:
        logger.info("Importing into SQLite database...")
        import_to_db(args.data_dir, args.db)

    if args.db.exists():
        show_stats(args.db)


if __name__ == "__main__":
    main()

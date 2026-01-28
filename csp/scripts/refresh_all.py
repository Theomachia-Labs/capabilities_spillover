"""Refresh all pipeline stages (placeholder)."""

from __future__ import annotations

import logging
from pathlib import Path

from csp.config import load_config


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_config()

    for directory in (
        config.data_raw_dir,
        config.data_processed_dir,
        config.artifacts_dir,
    ):
        _ensure_dir(directory)
        logging.info("Ensured directory: %s", directory)

    logging.info("TODO: ingest metadata, build graph, run labeling, generate reports")


if __name__ == "__main__":
    main()

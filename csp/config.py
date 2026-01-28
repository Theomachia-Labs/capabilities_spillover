"""Configuration helpers for CSP Toolkit."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CSPConfig:
    data_raw_dir: Path
    data_processed_dir: Path
    artifacts_dir: Path
    openalex_api_key: str | None
    semantic_scholar_api_key: str | None
    crossref_mailto: str | None
    openai_api_key: str | None


def _env_path(key: str, default: str) -> Path:
    return Path(os.getenv(key, default)).expanduser().resolve()


def load_config() -> CSPConfig:
    """Load configuration from environment variables."""
    return CSPConfig(
        data_raw_dir=_env_path("CSP_DATA_RAW_DIR", "./data_raw"),
        data_processed_dir=_env_path("CSP_DATA_PROCESSED_DIR", "./data_processed"),
        artifacts_dir=_env_path("CSP_ARTIFACTS_DIR", "./artifacts"),
        openalex_api_key=os.getenv("OPENALEX_API_KEY"),
        semantic_scholar_api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY"),
        crossref_mailto=os.getenv("CROSSREF_MAILTO"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

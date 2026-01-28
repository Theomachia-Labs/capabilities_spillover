# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a design scaffold (see `CSP Toolkit_ Codebase Development Plan.md`). The intended layout is:
- `csp/` — core Python package (schemas, rubric, ingest, graph, labeling, survey, reports).
- `apps/` — UI apps (e.g., Streamlit scorecard, optional dashboard).
- `scripts/` — runnable entry points (e.g., refresh-all, run-labeling).
- `data_raw/`, `data_processed/`, `artifacts/` — separated data and outputs.
Adjust paths as the codebase lands, but keep raw vs processed data clearly separated.

## Build, Test, and Development Commands
No build tooling exists yet. Once scaffolding begins, expect commands like:
- `python -m csp.scripts.refresh_all` — run the end-to-end pipeline with provenance logging.
- `pytest` — run unit tests for schemas, ingest, and graph logic.
- `ruff check .` and `mypy .` — lint and type-check (planned CI gates).
Update this section as soon as concrete scripts/configs are added.

## Coding Style & Naming Conventions
- Python, 4-space indentation, PEP 8 style.
- Modules/functions: `snake_case`; classes/schemas: `CamelCase` (e.g., `CSPScore`).
- Schema files in `csp/schemas/`, rubric YAML in `csp/rubric/`.
- Prefer explicit, descriptive names for pipeline stages (e.g., `ingest_openalex.py`).

## Testing Guidelines
- Use `pytest` with fixtures in `tests/fixtures/` (small, non-sensitive).
- Name tests `test_*.py` and mirror module paths (e.g., `tests/graph/test_metrics.py`).
- Include at least one reproducibility smoke test over a tiny fixture corpus.

## Commit & Pull Request Guidelines
- No Git history exists yet; use Conventional Commits (e.g., `feat: add rubric schema`).
- PRs should include: purpose/risk summary, tests run, data/LLM output changes, and any dual-use considerations.
- Link relevant issues or research notes when available.

## Data, Safety, and Configuration Notes
- Do not commit `data_raw/` or large `data_processed/` outputs; use `.gitignore` and add small fixtures only.
- Tag model-generated artifacts and keep them separate from raw metadata.
- Store API keys in `.env` or local config files; never commit secrets.
- Public outputs should default to aggregated, non-tactical summaries.

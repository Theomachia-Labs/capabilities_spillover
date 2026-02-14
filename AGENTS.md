# AGENTS.md

This file is the operational guide for coding agents and contributors working in this repository.

## 1. Mission

The CSP Toolkit measures capability spillover risk in AI research. The codebase combines:
- schema-validated records,
- metadata ingestion,
- citation graph analysis,
- intent labeling with audit review,
- survey aggregation and forecasting,
- policy-brief generation with safety redaction.

## 2. Repository Map

- `csp/` core package
- `csp/schemas/` JSON schemas and validation loader
- `csp/rubric/` rubric YAML + reliability metrics
- `csp/data/` SQLAlchemy models, DB session helpers, CRUD
- `csp/ingest/` OpenAlex/Semantic Scholar adapters + ingest logic
- `csp/graph/` graph build, metrics, diffusion/spillover analysis
- `csp/labeling/` rules + LLM labelers + audit queue logic
- `csp/survey/` import, calibration, aggregation, forecasting
- `csp/reports/` case-study data assembly and policy brief rendering
- `csp/security/` text redaction
- `apps/scorecard/` Streamlit UIs (scorecard, audit, survey/forecasting)
- `scripts/` CLI entry points
- `tests/` pytest suite + fixtures

## 3. Fast Commands

- Install: `pip install -e ".[dev]"`
- Run tests: `PYTHONPATH=. pytest -q`
- Lint: `ruff check .`
- Type check: `mypy .`
- Init output dirs: `python scripts/refresh_all.py`
- Ingest + label one paper: `python scripts/refresh_pipeline.py --id W2741809807 --source openalex --labeler rules`
- Build brief from DB: `python scripts/build_case_study.py --topic RLHF`
- Run full case-study flow: `python scripts/run_case_study_pipeline.py --topic RLHF --seeds W2741809807`
- Launch scorecard UI: `streamlit run apps/scorecard/app.py`

## 4. Rules For Changes

- Keep edits surgical: change only files relevant to the task.
- Preserve schema contracts. Validate new records with `csp.schemas.validate_instance`.
- Preserve safety defaults. Public-facing text should stay aggregated and pass through redaction where applicable.
- Maintain testability. Add or update tests with functional changes.
- Keep names explicit and boring; avoid extra abstractions unless they remove clear duplication.

## 5. Known Sharp Edges

- Tests require module visibility as package (`PYTHONPATH=.`) unless installed editable.
- `gather_case_study_data()` currently links papers to topic by naive keyword matching.
- `OpenAlexAdapter` currently stores OpenAlex abstract payload directly; normalize if you need plain-text abstract quality.
- Legacy records may still contain hyphenated labels (`safety-use`, `capability-use`), but new writes normalize to underscore labels.
- On some external macOS volumes, `._*` AppleDouble files may appear and dirty the working tree.

## 6. Safety Posture

- Never commit secrets or API keys.
- Keep raw data, processed data, and generated artifacts separated.
- Avoid adding tactical capability guidance to reports.
- When uncertain about safety implications of an output, default to redaction and flag for human review.

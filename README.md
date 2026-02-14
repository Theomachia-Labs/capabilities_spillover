# CSP Toolkit

Capability Spillover Potential (CSP) Toolkit for studying spillover between AI safety/alignment research and AI capabilities research.

## Conceptual Overview

This repository is a research workflow for answering a practical alignment question:

- Which AI safety/alignment topics are most likely to spill over into general capabilities progress?
- Which capabilities topics may spill back into safety-relevant methods, tools, or governance insight?

In short, it helps evaluate where research is likely to be:
- net safety-supporting,
- dual-use with meaningful spillover risk,
- or primarily capability-accelerating.

The goal is not to make final judgments automatically. The goal is to provide a structured, evidence-backed starting point for analysis: rubric scoring, citation-flow analysis, labeling, expert aggregation, and policy-brief outputs.

## What Is Implemented

- JSON Schema contracts for `PaperRecord`, `CSPScore`, `LabelRecord`, and `SurveyResponse`
- Rubric loading (`YAML`) and inter-rater reliability metrics
- SQLite-backed data layer (`Paper`, `Score`, `Label`, survey tables)
- Metadata adapters for OpenAlex and Semantic Scholar
- Labeling pipeline with rules-based and OpenAI-backed labelers
- Audit queue helpers for low-confidence labels
- Citation graph construction, centrality, community detection, and spillover flow metrics
- Survey import/calibration/aggregation and risk-reward portfolio ranking
- Case-study report generation with redaction
- Streamlit apps for scorecard, audit review, and survey/forecasting workflows

## Repository Structure

- `csp/` core library modules
- `apps/scorecard/` Streamlit applications
- `scripts/` command-line entry points
- `tests/` unit tests and fixtures
- `CSP Toolkit_ Codebase Development Plan.md` roadmap/design context

## Quick Start

### 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2) Verify

```bash
PYTHONPATH=. pytest -q
ruff check .
mypy .
```

### 3) Initialize Directories

```bash
python scripts/refresh_all.py
```

This creates the configured output directories (`data_raw/`, `data_processed/`, `artifacts/`) if missing.

## Common Workflows

### Ingest + Label One Paper

```bash
python scripts/refresh_pipeline.py \
  --id W2741809807 \
  --source openalex \
  --labeler rules
```

### Run End-to-End Case Study

```bash
python scripts/run_case_study_pipeline.py \
  --topic RLHF \
  --seeds W2741809807,W2776280122 \
  --source openalex \
  --labeler rules \
  --output output
```

### Build Policy Brief From Existing DB

```bash
python scripts/build_case_study.py --topic RLHF --output RLHF_Policy_Brief.md
```

## Streamlit UIs

```bash
streamlit run apps/scorecard/app.py
streamlit run apps/scorecard/pages/audit.py
streamlit run apps/scorecard/pages/survey.py
```

## Configuration

Environment variables used by the toolkit:

- `CSP_DATABASE_URL` (default: `sqlite:///csp.db`)
- `CSP_DATA_RAW_DIR` (default: `./data_raw`)
- `CSP_DATA_PROCESSED_DIR` (default: `./data_processed`)
- `CSP_ARTIFACTS_DIR` (default: `./artifacts`)
- `OPENALEX_API_KEY`
- `SEMANTIC_SCHOLAR_API_KEY`
- `CROSSREF_MAILTO`
- `OPENAI_API_KEY`

## Known Limitations

- Topic linkage for case studies is currently keyword-based, not a normalized topic table.
- OpenAlex abstract handling is minimal and may need normalization for downstream NLP.
- Legacy databases may contain hyphenated labels (`safety-use`, `capability-use`), but current writes normalize to underscore labels.
- On some external macOS volumes, AppleDouble `._*` sidecar files can appear and dirty the Git tree.

## Safety Notes

- Keep API keys out of version control.
- Prefer aggregate outputs for public artifacts.
- Use redaction for potentially sensitive tactical text.

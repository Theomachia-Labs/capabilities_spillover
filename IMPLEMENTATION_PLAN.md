# CSP Toolkit: Initial Development & Codebase Implementation Plan

## 1. Overview
This plan translates the existing CSP Toolkit development blueprint into an actionable implementation roadmap. The goal is to deliver a reproducible, evidence-backed system for CSP scoring, bibliometric analysis, labeling, and reporting while preventing dual-use misuse. The plan emphasizes strict schema validation, provenance, and safe-by-default outputs.

## 2. Scope
In scope:
- CSP rubric definitions and versioned scoring schemas.
- Bibliometric ingestion (seed-based) with canonicalization and deduplication.
- Citation-graph construction, metrics, and exports.
- Human-in-the-loop labeling (rules + LLM + audit).
- Reporting and forecasting pipelines (case studies + expert elicitation).
- Streamlit scorecard MVP and optional read-only dashboard.
- Reproducibility and provenance logging throughout.

Out of scope (initially):
- Large-scale production infra, multi-tenant auth, or public APIs.
- Fully automated labeling without human audit.
- Publishing tactical or fine-grained capability roadmaps.

## 3. Guiding Principles (Non-Negotiables)
- Evidence-first: every score or label links to citations/snippets.
- Separation of concerns: raw data, processed data, and model outputs are isolated.
- Reproducibility: fixed inputs + code version = stable outputs.
- Auditability: LLM output must be schema-validated and reviewable.
- Safety: public exports default to aggregated, non-tactical summaries.

## 4. Target Architecture Summary
Subsystems and key responsibilities:
- Rubric Instrument: YAML rubric definitions, JSON schemas, reliability analytics.
- Ingestion & Storage: metadata fetch, canonicalization, DB storage, provenance.
- Graph Analysis: citation graph creation, centrality/communities/diffusion.
- Labeling: rules + LLM + audit queue; evidence spans + confidence.
- Reporting & Forecasting: case studies, survey ingest, portfolio outputs.
- Interfaces: Streamlit scorecard, optional dashboard.

## 5. Repository & Tooling Setup
Initial repo scaffolding (minimal but strict):
- Python package layout under `csp/` with submodules per subsystem.
- `scripts/` for CLI entry points (thin wrappers around `csp.*`).
- `tests/` with fixtures and small static corpora.
- `.env.example` and config module for API keys and paths.
- `data_raw/`, `data_processed/`, `artifacts/` as ignored outputs.

Quality gates (CI targets):
- `ruff` for linting and formatting.
- `mypy` for type checking (start permissive, tighten over time).
- `pytest` for unit and integration tests.
- Optional `pre-commit` hooks for consistency.

## 6. Data Model & Schemas
Primary schema objects:
- `PaperRecord`: identifiers, metadata, abstracts, citations.
- `CSPScore`: rubric version, per-dimension scores, uncertainty, evidence.
- `LabelRecord`: intent labels, confidence, evidence spans, audit status.
- `SurveyResponse`: rater metadata, calibration, CSP-like payloads.

Implementation approach:
- Define JSON Schemas in `csp/schemas/`.
- Generate Pydantic models from schemas or mirror them in code.
- Enforce schema validation on all I/O boundaries.

## 7. Detailed Phase Plan

### Phase 0: Repository Initialization (Week 0–1)
Objectives:
- Establish repo structure, CI, and baseline tooling.
Tasks:
- Create package skeleton under `csp/`.
- Add `ruff`, `mypy`, `pytest` configs.
- Add `.gitignore` for data directories and secrets.
- Add `scripts/` with placeholder CLI entry points.
Deliverables:
- Clean repo scaffold with CI passing on empty tests.
Acceptance Criteria:
- `ruff check .`, `mypy .`, and `pytest` run without errors.

### Phase 1: Rubric & Schema MVP (Week 1–2)
Objectives:
- Formalize CSP rubric and scoring schemas.
Tasks:
- Implement rubric YAML versioning and loader.
- Create JSON schemas for `CSPScore` and `LabelRecord`.
- Build a minimal scoring interface (non-UI).
- Add inter-rater reliability metrics (e.g., Cohen’s kappa).
Deliverables:
- Versioned rubric definitions.
- Schema validation utilities and tests.
Acceptance Criteria:
- Example rubric loads and validates.
- Schema validations pass with sample records.

### Phase 2: Scorecard UI MVP (Week 2–3)
Objectives:
- Provide a human-friendly scoring workflow.
Tasks:
- Build Streamlit scorecard for scoring per rubric dimension.
- Require evidence attachment per score.
- Add import/export of CSPScore JSON.
Deliverables:
- Streamlit app in `apps/` or `csp/ui/`.
Acceptance Criteria:
- Users can create, validate, and export CSPScore objects.

### Phase 3: Ingestion & Storage MVP (Week 3–4)
Objectives:
- Build metadata ingestion and canonical storage.
Tasks:
- Implement adapters for one or two sources (e.g., OpenAlex, Semantic Scholar).
- Implement canonicalization and dedup.
- Add SQLite storage models.
- Add caching and API rate-limit handling.
Deliverables:
- Working ingestion pipeline for a seed list.
Acceptance Criteria:
- Seed corpus yields stored `PaperRecord` entries with provenance.

### Phase 4: Graph Analysis MVP (Week 4–5)
Objectives:
- Build citation graph and metrics.
Tasks:
- Create graph construction from stored records.
- Compute centrality, communities, diffusion over time.
- Export graph artifacts and tables.
Deliverables:
- Graph pipeline producing tables in `artifacts/`.
Acceptance Criteria:
- Metrics generated for a fixture corpus; deterministic output.

### Phase 5: Labeling Pipeline MVP (Week 5–6)
Objectives:
- Classify papers and track evidence/uncertainty.
Tasks:
- Implement rules-based labeling.
- Add LLM labeling with strict JSON schema validation.
- Build audit queue and adjudication log.
Deliverables:
- End-to-end labeling pipeline with audit trail.
Acceptance Criteria:
- LLM outputs always validate; low-confidence labels queued.

### Phase 6: Case Study & Reporting MVP (Week 6–7)
Objectives:
- Produce case study artifacts (RLHF, interpretability, etc.).
Tasks:
- Define case-study configuration format.
- Generate figures, tables, and narrative summaries.
- Ensure safe default exports (aggregated views only).
Deliverables:
- Standardized report artifacts in `artifacts/`.
Acceptance Criteria:
- Case study can be regenerated from raw inputs and config.

### Phase 7: Survey & Forecasting MVP (Week 7–8)
Objectives:
- Ingest expert surveys and produce risk–reward matrices.
Tasks:
- Implement survey schema and calibration logic.
- Aggregate distributions and generate portfolio outputs.
- Add sensitivity analysis hooks.
Deliverables:
- Forecasting artifacts and portfolio recommendations.
Acceptance Criteria:
- Survey ingestion + aggregation deterministic on fixtures.

### Phase 8: Hardening & Publication Mode (Week 8+)
Objectives:
- Lock in safety and reproducibility as default behavior.
Tasks:
- Add redaction/sensitivity scan for outputs.
- Add “publication mode” flag with output filters.
- Improve CI coverage and integration tests.
Deliverables:
- Safe export pipeline; reproducibility smoke test.
Acceptance Criteria:
- Public artifacts contain only aggregates; no tactical content.

## 8. Testing & QA Strategy
- Unit tests for schema validation, canonicalization, and graph logic.
- Integration tests for ingestion + graph + labeling pipelines.
- Reproducibility smoke test on a tiny fixture corpus.
- CI gating on linting, typing, and tests.

## 9. Safety & Dual-Use Controls
- Store model outputs separately and label them clearly.
- Require evidence spans for every LLM output.
- Default exports to aggregated summaries and uncertainty bounds.
- Maintain an internal-only mode for sensitive outputs.

## 10. Configuration & Secrets
- Use `.env` or local config (never commit secrets).
- Centralize configuration in `csp/config.py` with overrides.
- Document required API keys and rate limits.

## 11. Deliverables Summary (MVP to MVO)
- MVP: schemas + scorecard + ingestion + graph + minimal labeling.
- MVO: MVP plus case study report and reproducible pipeline.
- Full baseline: survey ingest + forecasting + safety hardening.

## 12. Risks & Mitigations
- API limits/data licensing: cache responses and respect TOS.
- LLM hallucinations: strict schema validation + evidence required.
- Reproducibility drift: provenance logging and deterministic seeds.
- Dual-use risk: safe-by-default outputs and redaction layer.

## 13. Immediate Next Steps (First Commit Sequence)
1. Initialize repo scaffold with CI and tooling.
2. Add schema definitions and validation utilities.
3. Implement rubric YAML versioning and loaders.
4. Build Streamlit scorecard MVP.
5. Add PaperRecord schema and SQLite storage.
6. Scaffold refresh-all script with provenance logging.

---
This plan should be updated as each phase completes, with explicit changes to deliverables, timelines, and acceptance criteria.

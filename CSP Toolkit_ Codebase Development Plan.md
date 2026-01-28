## **CSP Toolkit: Codebase Development Plan**

This document describes a practical plan to build an open-source “CSP Toolkit” that supports the project’s core research workflow: defining a Capability Spillover Potential (CSP) rubric, applying it to retrospective case studies via bibliometrics and labeling, and generating forecasting and portfolio guidance for funders and researchers. The design goal is to make CSP scoring reproducible and evidence-backed while minimizing the risk that the work product becomes a capabilities roadmap.

### **Purpose and scope**

The toolkit is meant to turn a conceptual framework into an operational instrument. It should (1) enforce rubric consistency through versioned definitions and schema validation, (2) automate literature ingestion and citation-network analysis, (3) support human-in-the-loop classification of paper intent (safety-use vs capability-use), (4) ingest expert elicitation results and aggregate them into distributions, and (5) produce paper-ready and policy-ready artifacts with one-command reproducibility.

The system is explicitly not intended to publish tactical “how-to” instructions for improving model capabilities. Outputs should prioritize aggregate metrics, uncertainty, and evidence trails.

### **Design principles**

The codebase should be built around a few hard constraints. First, no CSP score exists without evidence: each dimension score must link to citations and snippets. Second, raw data, processed data, and model-generated inferences must be separated and clearly tagged. Third, the research workflow must be reproducible: the same inputs should yield the same outputs, with provenance logs that capture code versions, tool versions, and dataset hashes. Fourth, automation must be human-auditable: any LLM-assisted labeling must return a schema-validated record with confidence and supporting spans, and uncertain cases must route to a review queue. Finally, public-facing exports should default to safe, aggregated artifacts.

### **Proposed architecture**

The system has five main subsystems.

The first subsystem is the CSP rubric instrument: versioned rubric definitions, JSON schemas for score objects, a scoring interface, and reliability analytics (inter-rater agreement). This is the “measurement device” of the project.

The second subsystem is ingestion and storage: a pipeline that takes seed papers, fetches metadata and citation relationships, canonicalizes identifiers, deduplicates records, and stores everything in a local database (SQLite for development, Postgres for scale).

The third subsystem is graph analysis: building directed citation graphs, computing standard network metrics (centrality, communities, diffusion over time), and exporting the results as tables and portable graph formats.

The fourth subsystem is labeling: classifying papers (or citation contexts) into safety-use, capability-use, mixed, or unclear. This should be staged: high-precision rules first, then LLM-assisted labeling for the remainder, then audit sampling and adjudication.

The fifth subsystem is reporting and forecasting: generating standardized case study reports (RLHF, interpretability, robustness), ingesting expert elicitation surveys with calibration, aggregating CSP distributions, and producing a risk–reward matrix and portfolio recommendations with uncertainty.

### **Repository structure**

A clean layout keeps research code, apps, and pipelines organized and prevents accidental mixing of raw and derived artifacts. A target layout looks like this:

* `csp/schemas/` for JSON schemas: CSPScore, PaperRecord, LabelRecord, SurveyResponse, RubricVersion.  
* `csp/rubric/` for rubric YAML definitions, anchors, scoring utilities, and reliability metrics.  
* `csp/ingest/` for source adapters (Semantic Scholar/OpenAlex/Crossref/arXiv), normalization, canonicalization, and seed sets.  
* `csp/data/` for database models and provenance tracking.  
* `csp/graph/` for graph construction, metrics, communities, diffusion, and exports.  
* `csp/labeling/` for rules, LLM labeler adapter, prompts, cite-context extraction, audit queue, and optional active learning.  
* `csp/survey/` for survey import, calibration, aggregation.  
* `csp/reports/` for case-study generators, figure/table builders, and renderers.  
* `apps/` for a scorecard UI (Streamlit) and an optional dashboard (FastAPI/Streamlit multipage).  
* `scripts/` for runnable entry points like refresh-all, run-labeling, build-case-study, export-policy-brief.  
* `data_raw/`, `data_processed/`, and `artifacts/` as separate top-level directories (with explicit rules about what is committed vs cached).

### **Data model**

The toolkit revolves around a few canonical entities.

A PaperRecord stores stable identifiers (internal ID plus DOI/arXiv/OpenAlex/S2 where available), bibliographic metadata, abstract, and citation relationships. PaperRecord should represent “as collected,” not “as interpreted.”

A CSPScore is versioned by rubric definition and contains per-dimension scores, uncertainty estimates, evidence items (each with citation/snippet/note), and provenance (human vs agent, timestamp, method, model info if applicable). This object is the atomic unit of analysis and reporting.

A LabelRecord stores the intent label for a paper (or a paper within a case study), along with confidence, evidence spans, method (rules/LLM/human), and audit status (pending/verified/disputed). This makes downstream analysis defensible.

A SurveyResponse represents expert elicitation: rater metadata, optional calibration results, and CSPScore-like payloads for each topic. Aggregation should preserve distributions rather than collapsing to point estimates.

### **Pipelines and automation**

The toolkit should provide repeatable pipelines that can run end-to-end or in stages.

Ingestion pipeline: starting from a seed list, fetch metadata and citation links, canonicalize records, deduplicate, store in a database, and snapshot provenance hashes for reproducibility. Output portable JSONL exports as needed.

Graph pipeline: build the citation graph from stored records, compute metrics (degree, PageRank, betweenness, communities), model diffusion over time, and export graph artifacts plus metric tables.

Labeling pipeline: run rules-based labeling to capture easy cases with high precision, then apply an LLM labeler for remaining cases. Every LLM output must be schema-validated, include evidence spans, and include confidence. Route uncertain or high-impact cases to an audit queue. Record adjudications. Export a final labels table.

Case study pipeline: for each case study configuration (RLHF, interpretability, robustness), select a relevant subgraph, compute labeled flow metrics over time, identify bridging nodes and transitions, and render standard figures and tables. The system should allow rerunning the same case study with updated data using identical code paths.

Forecasting pipeline: import survey responses, calibrate raters, aggregate CSP dimension distributions, combine with separate safety-benefit estimates where available, generate a spillover risk–reward matrix with uncertainty, and output ranked portfolio options plus sensitivity analyses.

Operational pipeline: a single “refresh all” script should update metadata, rebuild graphs, rerun labeling (with caching and audit preservation), and regenerate artifacts. This is how you avoid manual analysis drift and quietly achieve scientific adulthood.

### **LLM and agent integration rules**

LLMs and agentic automation are useful, but they must be constrained. The code should treat the LLM as a function that returns strictly structured records, not as an oracle.

Every LLM call should produce JSON that validates against a schema. Outputs must contain evidence spans/snippets and a confidence level. Any output below a threshold must be sent to human review. Model-generated content must be tagged and stored separately from raw paper metadata.

A separate redaction/sensitivity module should scan generated summaries and drafts for “roadmap density” and rewrite into more abstract descriptions. The public default mode should produce aggregated summaries and omit fine-grained tactical pathways.

### **User interfaces**

Two interfaces are recommended.

The scorecard UI is the essential one. A Streamlit app can guide users through scoring dimensions with anchored examples, require evidence attachments per dimension, support import/export of CSPScore objects, compare two scorers, and show inter-rater reliability statistics.

An optional dashboard is valuable if you want community exploration. It should remain read-only, emphasize aggregates and uncertainty, and provide downloads of safe artifacts. If built, it can be a small FastAPI service serving data plus a minimal frontend, or a Streamlit multipage app.

### **Reproducibility and provenance**

Every pipeline step should produce provenance logs capturing input dataset hashes, code version (git SHA), tool versions, timestamps, and configuration parameters. Sampling operations must be seeded. Where feasible, API responses should be cached in a way consistent with terms of service. A “publication mode” flag should control what gets exported: public-safe aggregates vs internal full evidence logs.

### **CI, testing, and quality gates**

CI should enforce ruff linting, mypy type checks, and unit tests for schema validation, canonicalization/deduplication, and graph construction on fixture datasets. Add a reproducibility smoke test that runs the pipelines on a tiny fixture corpus and checks that expected metric tables are produced. Add policy checks that ensure public exports don’t include restricted or overly granular content and that all model-generated records are tagged.

### **Dual-use mitigation built into the codebase**

The repository should make it hard to accidentally ship a capabilities guide. Public mode should default to aggregated figures and high-level narratives. Fine-grained citation context extraction should be optional, and if used, its export should be restricted to internal mode. The reporting layer should prefer “this technique diffused into capabilities work” over “here’s exactly how to repurpose it.”

### **Roadmap and milestones**

A practical eight-week baseline is:

Weeks 1–2: build the rubric instrument MVP. Implement schemas, rubric YAML and versioning, a Streamlit scorecard with evidence requirements, and inter-rater reliability calculations. Deliverable is consistent CSP scoring for an initial set of topics.

Weeks 3–4: build ingestion and graph MVP. Implement one or two metadata sources, canonicalization, SQLite storage, citation graph construction, and basic metrics. Deliverable is an RLHF case-study graph and baseline diffusion plots.

Weeks 5–6: implement labeling pipeline MVP. Add rules-based labeling, LLM labeler with strict schemas, an audit queue, and labeled diffusion over time. Deliverable is an interpretability case study with verified label distributions and flow metrics.

Weeks 7–8: implement survey ingest and forecasting outputs. Add calibration, aggregation into distributions, risk–reward matrix generator, and policy brief artifact exporter. Deliverable is an end-to-end artifact set suitable for a paper draft and a policy brief.

### **Minimum Valuable Outcome implementation slice**

If the goal is a fast, defensible proof-of-concept, the minimum slice is: CSP schemas plus scorecard UI, RLHF metadata ingestion plus citation diffusion, minimal labeling (rules plus manual audit), and a single retrospective CSP score for RLHF backed by evidence. This yields a publishable “instrument \+ case study” without committing to the full dashboard.

### **Immediate next steps for the first commit sequence**

Start by initializing the repository with CI and formatting/type checking, then add CSP schemas and validators, then implement the rubric YAML and versioning, then build the Streamlit scorecard MVP, then wire up the PaperRecord schema and SQLite storage, and finally scaffold the refresh-all script with provenance logging. After that, ingestion source adapters and graph building can evolve without destabilizing the core rubric instrument.

That’s the plan. It’s basically a machine to help humans make hard strategic judgments, which is the closest you can get to “reshaping the Universe” without needing a Dyson swarm permit.


# Manual Read-Only Adapter Chain Smoke Fixture

This smoke fixture exercises the manual read-only adapter chain on sanitized offline rows. It is for local diagnostics, demos, and tests only.

Fixture path:

```text
tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv
```

The fixture contains fake job ids, fake company names, fake roles, and fake resume filenames. It does not contain real user data, real resume data, real application data, real job data, or private company details.

## Run The Manual Chain

Use a temporary output directory so no production planning outputs are touched:

```bash
TMP_CHAIN_DIR="$(mktemp -d)"
python -m src.agents.read_only_adapter_chain \
  --queue-input tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv \
  --output-dir "$TMP_CHAIN_DIR" \
  --json
find "$TMP_CHAIN_DIR" -maxdepth 3 -type f -print | sort
```

## Generate Artifacts With The Explicit Operator Utility

The operator artifact generator is also manual/offline only. It requires both `--queue-input` and `--output-dir`; it does not discover production paths, run automatically, update the production queue, generate tailoring, update packets, change scoring/ranking, or submit applications.

```bash
TMP_CHAIN_DIR="$(mktemp -d)"
python -m src.agents.read_only_chain_artifact_generator \
  --queue-input tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv \
  --output-dir "$TMP_CHAIN_DIR" \
  --json
find "$TMP_CHAIN_DIR" -maxdepth 3 -type f -print | sort
```

Expected root files:

```text
read_only_adapter_chain_result.json
read_only_adapter_chain_report.md
read_only_chain_artifact_generation_result.json
read_only_chain_artifact_generation_report.md
```

Expected adapter subdirectory files:

```text
job_prioritization/job_prioritization_read_only_adapter_result.json
job_prioritization/job_prioritization_read_only_adapter_report.md
job_prioritization/job_prioritization_read_only_adapter_recommendations.csv
tailoring_decision/tailoring_decision_read_only_adapter_result.json
tailoring_decision/tailoring_decision_read_only_adapter_report.md
tailoring_decision/tailoring_decision_read_only_adapter_decisions.csv
operator_review/operator_review_read_only_adapter_result.json
operator_review/operator_review_read_only_adapter_report.md
operator_review/operator_review_read_only_adapter_reviews.csv
```

## Viewing Artifacts Manually

Agentic Review can display chain diagnostics when these artifacts already exist in a run artifact set:

- `read_only_adapter_chain_result.json`
- `read_only_adapter_chain_report.md`

The explicit generator artifacts are regression-tested through workflow verification and the Agentic Review read model, but this does not run the generator automatically.

For manual viewer testing only, copy those two root files into a sanitized run output directory before artifact ingestion. Do not copy smoke outputs into production runs or real application artifacts.

## Safety Guarantees

- This fixture does not run automatically.
- This fixture is not production data.
- The chain is not wired into live planning, the scheduler, UI actions, `workflow_runner.py`, queue updates, tailoring generation, packet generation, scoring/ranking, RAG, or application submission.
- The artifact generator is explicit/operator-triggered only and refuses to run without an explicit queue input and explicit output directory.
- `workflow_runner.py` remains dry-run only.
- The preflight harness keeps `executable_adapter_count=0`.
- The smoke fixture does not implement real orchestration, autonomous execution, LangGraph integration, feedback-driven scoring/ranking, RAG retrieval changes, or automated application submission.

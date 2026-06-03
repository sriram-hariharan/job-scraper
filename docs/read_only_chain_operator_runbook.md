# Read-Only Chain Operator Runbook

This runbook is for manually generating read-only adapter chain diagnostics and viewing the resulting artifacts. It is an operator utility, not live orchestration.

Path: `docs/read_only_chain_operator_runbook.md`

## Purpose

Use the explicit generator when you want a local, isolated diagnostic bundle for the manual read-only adapter chain:

```text
explicit queue CSV -> read-only adapter chain -> diagnostic artifacts -> verifier / Agentic Review read model
```

The generator is explicit/manual only. It requires `--queue-input` and `--output-dir`.

## Prerequisites

- A sanitized or explicitly selected queue CSV with `application_execution_queue.csv`-like columns.
- A temporary or otherwise isolated output directory.
- A local checkout of ApplyLens AI.
- No production run directory as the output root.

## Safe Fixture Command

Use the sanitized offline fixture for demos and regression checks:

```bash
TMP_CHAIN_DIR="$(mktemp -d)"
python -m src.agents.read_only_chain_artifact_generator \
  --queue-input tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv \
  --output-dir "$TMP_CHAIN_DIR" \
  --json
find "$TMP_CHAIN_DIR" -maxdepth 3 -type f -print | sort
```

## Local Artifact Command

For a real local diagnostic file, choose the input and output path explicitly:

```bash
TMP_CHAIN_DIR="$(mktemp -d)"
python -m src.agents.read_only_chain_artifact_generator \
  --queue-input "<path-to-sanitized-or-explicit-queue-csv>" \
  --output-dir "$TMP_CHAIN_DIR" \
  --json
```

Do not hardcode production paths into scripts. Do not point `--output-dir` at a live planning output directory.

## Required Flags

- `--queue-input`: explicit CSV input path.
- `--output-dir`: explicit output directory for diagnostic artifacts.

The generator refuses to run the chain when either flag is missing.

## Expected Output

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

Inspect only the isolated output directory:

```bash
find "$TMP_CHAIN_DIR" -maxdepth 3 -type f -print | sort
```

The output root must not contain production artifact names such as `application_execution_queue.csv`, `job_prioritization_recommendations.csv`, `tailoring_decision_recommendations.csv`, or `operator_review_recommendations.csv`.

## Agentic Review

Agentic Review can display the manual chain and explicit generator diagnostics after those artifacts already exist in an ingested run artifact set. The viewer/read model path is diagnostic only and does not run the generator automatically.

For manual viewer testing, copy only sanitized diagnostic root artifacts into a sanitized run artifact set before ingestion. Do not copy smoke outputs into production runs or real application artifacts.

## What This Does Not Do

- No queue update.
- No tailoring generation.
- No packet generation.
- No scoring or ranking change.
- No application submission.
- No database write.
- No live planning.
- No `workflow_runner.py` execution.
- No scheduler or background run.
- No UI action or route runs the generator.

## Troubleshooting

- Missing queue input: provide `--queue-input`; the generator returns `missing_explicit_queue_input` and does not run the chain.
- Missing output dir: provide `--output-dir`; the generator returns `missing_explicit_output_dir` and does not run the chain.
- Nonexistent input file: check the path; the generator returns `queue_input_artifact_not_found`.
- Verifier warning: missing optional planning artifacts can be warning-only in non-strict mode. Inspect `reason_codes` before treating it as a failure.
- Verifier failure: check for unsafe flags, wrong execution mode, mutation signals, or production artifact names at the output root.
- Artifacts not visible in Agentic Review: confirm the run artifact ingestion includes the four root JSON/Markdown files and that you are viewing the same owner-scoped run.

## Safety Checklist

- I am using a sanitized fixture or an explicitly selected local queue CSV.
- I am using a fresh isolated `--output-dir`.
- I am not writing into a live planning output directory.
- I am not running this from a scheduler, UI action, API route, or background job.
- I understand this is read-only diagnostic output, not live orchestration.
- `workflow_runner.py` remains dry-run only.
- The preflight harness keeps `executable_adapter_count=0`.

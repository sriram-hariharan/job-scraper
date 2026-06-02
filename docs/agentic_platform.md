# ApplyLens Agentic Platform Runbook

This document describes the agentic workflow layer that currently exists in ApplyLens AI. It is a traceable, advisory layer around the existing job discovery and application-planning pipeline. It does not replace the pipeline, change queue actions, generate resume text, or introduce a multi-agent framework.

## Purpose

The agentic platform turns existing deterministic pipeline outputs into structured agent records, advisory artifacts, benchmarkable decisions, and operator-facing diagnostics. The implementation follows this pattern:

```text
existing pipeline stage -> agent wrapper -> structured output -> validation -> trace/artifact -> UI display
```

The current system is intentionally conservative. Advisory agents label and summarize existing outputs; they do not mutate production decisions.

## Workflow Registry

The orchestration contract lives in `src/agents/workflow_registry.py`. It is a deterministic manifest for the implemented agentic workflow, not an orchestration engine.

The registry records:

- workflow name and version
- ordered agent keys
- agent names, versions, owner modules, and deterministic model metadata
- input and output artifacts for each implemented agent
- generated artifact kinds
- required feature flags
- safety guarantees
- benchmark metric keys

Useful helpers:

- `get_agentic_workflow_manifest()`
- `list_agentic_agents()`
- `get_agent_manifest(agent_key)`
- `validate_agentic_workflow_manifest()`
- `render_agentic_workflow_manifest_markdown()`

The registry validates that no agent mutates production decisions, tracing is disabled by default, expected feature flags are documented, and expected agentic artifact kinds are present.

## Design Principles

- Advisory first: agent outputs are recommendations, summaries, validations, or diagnostics.
- Deterministic wrappers: current agents use rules over existing structured rows, not hidden LLM orchestration.
- No hidden production decision mutation: advisory outputs do not overwrite `action`, queue state, packet generation, or tailoring generation.
- Traceability: aggregate agent steps can be recorded to `agent_runs` and `agent_steps` when tracing is enabled.
- Benchmarkability: deterministic fixtures and CLI checks measure whether the agentic layer continues to behave as expected.
- Safe missing data behavior: optional artifacts and traces are allowed to be absent; UI surfaces should remain usable.

## Implemented Agents

### Resume Match Agent

Module: `src/agents/resume_match_agent.py`

Summarizes best-resume selector results and validates resume-selection credibility behavior. It tracks fallback-only rows, deterministic winner counts, score buckets, packet-generation eligibility, and low-confidence blocking.

Trace recording is optional and aggregate-only.

### Source Health Agent

Module: `src/agents/source_health_agent.py`

Reads `source_health_report.csv` rows and produces deterministic source/company recommendations:

- `promote`
- `keep`
- `monitor`
- `demote`
- `needs_detail_enrichment`
- `needs_timestamp_fix`

It does not add, remove, or mutate sources.

### Critic Agent

Module: `src/agents/critic_agent.py`

Validates tailoring suggestions in advisory mode. It labels suggestions as `approve`, `reject`, or `downgrade_to_guidance` using deterministic checks for unsupported claims, fake tools/domains, unsupported metrics, weak score lift, and patch safety.

The critic labels suggestions only when `APPLYLENS_CRITIC_ADVISORY_ENABLED=1`. It does not generate suggestions or overwrite tailoring decisions.

### Job Prioritization Agent

Module: `src/agents/job_prioritization_agent.py`

Reads existing queue/shortlist fields and emits advisory priority labels:

- `apply_now`
- `tailor_first`
- `manual_review`
- `skip_for_now`
- `watch_source`

The resulting artifact is advisory and keeps `existing_action` separate from `advisory_priority`.

### Tailoring Decision Agent

Module: `src/agents/tailoring_decision_agent.py`

Reads queue, prioritization, and credibility fields and emits advisory tailoring decisions:

- `no_tailoring_needed`
- `light_tailoring`
- `tailor_before_apply`
- `manual_review_before_tailoring`
- `do_not_tailor`

It decides whether tailoring may be worth doing; it does not write or modify resume content.

### Operator Review Agent

Module: `src/agents/operator_review_agent.py`

Consolidates advisory signals into human-review lanes:

- `ready_to_apply`
- `tailor_then_apply`
- `review_before_action`
- `hold_or_skip`
- `source_watch`

This is an operator summary layer only. It does not hide, reorder, or change jobs.

## Trace System

Schema:

- `agent_runs`
- `agent_steps`

Core modules:

- `src/storage/agent_trace/schema.sql`
- `src/storage/agent_trace/store.py`
- `src/agents/trace.py`

The trace layer stores aggregate agent run/step data, including structured input/output/validation JSON, model metadata, token usage JSON, cost JSON, latency, status, and errors. Existing UI exposes stored traces through the Agent Trace panel.

### Trace Flags

`APPLYLENS_AGENT_TRACE_ENABLED`

Set to `1` to allow agent wrappers to write trace rows when owner/run context is available.

`APPLYLENS_AGENT_TRACE_STRICT`

Set to `1` only when trace write failures should fail the caller. By default, trace write failures warn/return gracefully.

Tracing is disabled by default. Current tracing is aggregate-only; per-job trace rows are intentionally not implemented yet.

## Advisory Artifacts

The current agentic workflow uses these artifacts when available:

- `source_health_report.csv`
- `job_prioritization_recommendations.csv`
- `tailoring_decision_recommendations.csv`
- `tailoring_decision_summary.json`
- `operator_review_recommendations.csv`
- `operator_review_summary.json`
- `agentic_workflow_summary.json`
- `agentic_workflow_summary.md`
- `agentic_workflow_verification.json`

These artifacts are read-only/advisory. They preserve existing production fields such as `existing_action` and add separate advisory fields such as `advisory_priority`, `tailoring_decision`, and `operator_review_lane`.

## Benchmark

The offline deterministic benchmark lives in:

- `src/evaluation/agentic_benchmark.py`
- `src/evaluation/metrics.py`
- `tests/fixtures/agentic_benchmark/cases.json`

Run without writing outputs:

```bash
python -m src.evaluation.agentic_benchmark --no-write --print-summary
```

Run and write benchmark outputs:

```bash
python -m src.evaluation.agentic_benchmark --output-dir outputs/evaluation --print-summary
```

Write mode produces:

- `outputs/evaluation/agentic_benchmark_summary.json`
- `outputs/evaluation/agentic_benchmark_results.csv`
- `outputs/evaluation/agentic_benchmark_report.md`

The benchmark is offline and deterministic. It does not call LLMs, scrape websites, use private resume text, or depend on live pipeline state.

## Workflow Verifier

The run verifier lives in `src/agents/workflow_verifier.py`. It checks completed run artifact folders or loaded artifact rows for expected agentic artifacts and consistency rules.

Basic verification:

```bash
python -m src.agents.workflow_verifier --output-dir <artifact_dir>
```

Strict JSON verification:

```bash
python -m src.agents.workflow_verifier --output-dir <artifact_dir> --strict --json
```

The verifier returns a payload with:

- `validation_status`
- `strict`
- `checked_artifacts`
- `missing_artifacts`
- `row_counts`
- `consistency_checks`
- `reason_codes`
- `summary`

Verifier output is diagnostic. Missing optional artifacts produce warnings in non-strict mode. Planning writes `agentic_workflow_verification.json` when the integration path runs.

## Feature Flags

`APPLYLENS_AGENT_TRACE_ENABLED`

Enables aggregate trace recording for agent wrappers when owner/run context exists.

`APPLYLENS_AGENT_TRACE_STRICT`

Makes trace write failures fail the caller. Leave unset for normal operation.

`APPLYLENS_CRITIC_ADVISORY_ENABLED`

Adds critic advisory metadata to scan suggestions. When unset, the existing scan suggestion payload remains unchanged.

`APPLYLENS_WORKFLOW_VERIFIER_STRICT`

Runs workflow verification in strict mode during planning artifact generation when supported by the integration path. Leave unset for non-blocking diagnostics.

## Safety Guarantees

- No advisory agent overwrites production `action`.
- No advisory agent mutates queue ordering.
- No advisory agent mutates packet generation.
- No advisory agent generates resume text.
- No advisory agent changes tailoring generation.
- The workflow verifier is diagnostic only.
- Trace failures do not break normal operation unless strict tracing is explicitly enabled.
- Missing advisory artifacts are displayed safely or ignored by UI surfaces.

## Live Smoke Checklist

1. Enable trace recording for one run:

   ```bash
   export APPLYLENS_AGENT_TRACE_ENABLED=1
   ```

2. Run the pipeline through the normal user pipeline or planning flow.

3. Confirm status counts, when present:

   - `agent_trace_enabled=1`
   - `agent_trace_steps_recorded` is greater than zero
   - `agent_trace_write_failed=0`

4. Check trace rows:

   - `agent_runs`
   - `agent_steps`

5. Check generated advisory artifacts:

   - `job_prioritization_recommendations.csv`
   - `tailoring_decision_recommendations.csv`
   - `operator_review_recommendations.csv`
   - `agentic_workflow_summary.json`
   - `agentic_workflow_summary.md`
   - `agentic_workflow_verification.json`

6. Open the UI and confirm:

   - Agent Trace panel shows stored aggregate steps.
   - Advisory badges render separately from production action.
   - Agentic Workflow Summary panel renders read-only counts.
   - Agentic Workflow Verification panel renders diagnostic status.

## Known Limitations

- Current agents are deterministic advisory agents only.
- There is no LangGraph integration.
- There is no LLM agent orchestration.
- Existing LLM calls are not wrapped as LLM agent calls yet.
- Per-job trace rows are intentionally not implemented yet.
- Agentic artifacts are diagnostic/advisory and should not be treated as production action authority.
- The benchmark uses sanitized fixtures and does not measure live scraping or real LLM quality.

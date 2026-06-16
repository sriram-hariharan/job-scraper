# Phase 5C Shadow Sidecar Trace Schema Contract

This checkpoint defines the trace schema contract that future production pipeline shadow sidecar stages must emit.

This is documentation/test only.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No scheduler behavior is changed.

No storage schema is changed.

No migration is added.

Live agents connected to production pipeline remain zero.

Live agents allowed to automate mutations remain zero.

## Purpose

The shadow sidecar trace schema contract defines the minimum trace envelope, source deterministic decision snapshot, agent output summary, observability payloads, and safety metadata required before any future default-off, read-only shadow sidecar can be wired near the production pipeline.

This phase does not add pipeline wiring, runtime feature flags, provider calls, storage writes, schema changes, automated decisions, or mutation-capable behavior.

## Required Trace Envelope Fields

Every future sidecar trace event must include:

- `schema_version`
- `run_id`
- `batch_id`
- `job_id`
- `stage_name`
- `agent_name`
- `agent_mode`
- `provider_mode`
- `sidecar_enabled`
- `sidecar_stage_status`
- `started_at_utc`
- `completed_at_utc`
- `duration_ms`

The envelope identifies the batch/run context, the production job context, the shadow stage, the agent, and whether the sidecar was enabled or skipped.

## Required Source Decision Fields

Every future sidecar trace event must preserve the source deterministic pipeline decision:

- `source_deterministic_stage`
- `source_deterministic_status`
- `source_deterministic_score`
- `source_deterministic_decision`
- `source_deterministic_reason_codes`

The source deterministic pipeline decision must be preserved and must remain the authoritative production decision unless a later reviewed phase explicitly adds a human-approved influence path.

## Required Agent Output Fields

Every future sidecar trace event must summarize the shadow agent output:

- `agent_output_status`
- `agent_recommendation`
- `agent_confidence`
- `agent_reason_codes`
- `agent_evidence_refs`
- `agent_risk_flags`
- `agent_blocking_findings`

Agent recommendations are advisory only. They must not override scoring, ranking, queue state, approval state, resume content, execution requests, execution launch requests, application execution, or application submission.

## Required Observability Fields

Every future sidecar trace event must include:

- `trace_bundle`
- `evidence_pack`
- `readiness_decision`
- `health_status`
- `fallback_used`
- `error_type`
- `error_message`

Trace bundle, evidence pack, readiness decision, and health status are required so operators can audit enabled, disabled, fallback, skipped, failed, and blocked sidecar stages.

## Required Safety Metadata

Every future sidecar trace event must include safety metadata with these keys:

- `read_only`
- `shadow_only`
- `manual_review_required`
- `did_mutate_scoring`
- `did_change_ranking`
- `did_mutate_queue`
- `did_create_approval`
- `did_mutate_approval`
- `did_mutate_resume`
- `did_create_execution_request`
- `did_create_execution_launch_request`
- `did_execute_application`
- `did_submit_application`
- `pipeline_wiring_added`
- `auto_apply_enabled`

Expected safe values for future read-only sidecar traces are `read_only=true`, `shadow_only=true`, `manual_review_required=true`, and all mutation/execution/submission flags set to false.

## Required Status Enum

`sidecar_stage_status` must use one of these values:

- `not_enabled`
- `skipped_by_config`
- `completed_shadow`
- `completed_with_fallback`
- `blocked_by_kill_switch`
- `failed_non_blocking`

Unknown status values must be treated as invalid by future trace validation.

## Per-Agent Trace Requirements

The three coded live LLM-capable agents require stage-specific trace payloads:

### JD Intelligence Agent

- Must include extracted JD signal summaries when enabled.
- Must include validation errors and fallback status when disabled or invalid.
- Must preserve the source deterministic pipeline decision.

### Tailoring Suggestion Agent

- Must include patch-ready, guidance-only, rejected, missing-evidence, and unsupported-claim summaries when enabled.
- Must include validation errors and fallback status when disabled or invalid.
- Must preserve the source deterministic pipeline decision.

### Critic / Guardrail Agent

- Must include approved, downgraded, rejected, risk, evidence-gap, and reason-code summaries when enabled.
- Must include validation errors and fallback status when disabled or invalid.
- Must preserve the source deterministic pipeline decision.

## Failure Behavior

- Sidecar failures must not fail deterministic pipeline by default.
- Failures must emit trace/evidence payloads.
- Deterministic fallback required.
- No retry storm.
- Sidecar failure may set `sidecar_stage_status=failed_non_blocking` or `sidecar_stage_status=completed_with_fallback`.
- Sidecar failure must not mutate scoring, ranking, queue, approvals, resumes, execution requests, execution launch requests, applications, or submissions.

## Non-Mutation Contract

Future sidecar traces must prove:

- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.

## Testing Contract

Phase 5C tests are trace schema contract tests only.

Future tests for sidecar trace schema must use:

- No provider calls in tests.
- Provider calls disabled in tests.
- Deterministic fixtures only.
- No mutation assertions.
- Trace schema contract tests only.

Tests must not call live providers, write storage, alter schema, wire the pipeline, or mutate production decisions.

## Phase 5C Non-Goals

- No pipeline wiring.
- No provider calls.
- No automated decisions.
- No application execution/submission.
- No queue writes.
- No runtime behavior change.
- No storage schema change.
- No migration.

## Decision

Phase 5C defines the future shadow sidecar trace schema contract only.

The production pipeline connected live-agent count remains zero, and the mutation-capable live-agent count remains zero.


# Phase 5D Shadow Sidecar Adapter Interface Contract

This checkpoint defines the future adapter interface contract for production pipeline shadow sidecar stages.

This is documentation/test only.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No scheduler behavior is changed.

No storage schema is changed.

No migration is added.

Live agents connected to production pipeline remain zero.

Live agents allowed to automate mutations remain zero.

## Purpose

The shadow sidecar adapter interface contract defines how a future pipeline-adjacent adapter should receive deterministic pipeline context, optionally call a shadow agent under future default-off configuration, normalize output into the Phase 5C trace schema, and return a read-only sidecar result.

This phase does not implement a runtime adapter, add runtime feature flags, call providers, add pipeline wiring, write storage, change schema, or mutate production decisions.

## Adapter Role

A future shadow sidecar adapter must:

- Read deterministic pipeline context.
- Call shadow agent only when future config allows it.
- Normalize output into the Phase 5C trace schema.
- Return read-only sidecar result.
- Never override deterministic decisions.
- Preserve the source deterministic pipeline decision.
- Emit fallback, trace, evidence, readiness, health, and safety metadata when disabled, skipped, failed, or blocked.

## Adapter Input Contract

The future adapter input payload must include:

- `run_id`
- `batch_id`
- `job_id`
- `stage_name`
- `source_deterministic_stage`
- `source_deterministic_status`
- `source_deterministic_score`
- `source_deterministic_decision`
- `source_deterministic_reason_codes`
- `job_payload`
- `resume_profile_payload`
- `existing_trace_context`
- `sidecar_config`

Input payloads must be treated as read-only snapshots. A future adapter must deep-copy or otherwise protect caller-owned structures before normalization or fallback handling.

## Adapter Output Contract

The future adapter output payload must include:

- `sidecar_stage_status`
- `agent_name`
- `agent_mode`
- `provider_mode`
- `agent_output_status`
- `agent_recommendation`
- `agent_confidence`
- `agent_reason_codes`
- `agent_evidence_refs`
- `agent_risk_flags`
- `trace_bundle`
- `evidence_pack`
- `readiness_decision`
- `health_status`
- `safety_metadata`

Outputs are advisory and read-only. They must not mutate or replace deterministic production pipeline decisions.

## Required Future Adapter Functions

A future runtime implementation should define small, testable functions with these responsibilities:

- `build_shadow_sidecar_input_payload`
- `run_shadow_sidecar_agent`
- `build_shadow_sidecar_trace_payload`
- `build_shadow_sidecar_fallback_payload`
- `evaluate_shadow_sidecar_safety`

These names are an interface contract only in Phase 5D. They are not implemented in this checkpoint.

## Per-Agent Adapter Mapping

The three coded live LLM-capable agents map to future sidecar adapters as follows:

- JD Intelligence Agent maps to job description extraction and risk signals.
- Tailoring Suggestion Agent maps to resume/job tailoring advice.
- Critic / Guardrail Agent maps to risk review and blocking findings.

Each mapping must preserve deterministic pipeline decisions and emit Phase 5C-compatible trace output.

## Config Behavior

Future adapter execution must obey the Phase 5B configuration contract:

- Global sidecar flag default-off.
- Per-agent flags default-off.
- Kill switch disables all sidecar work.
- Provider calls require global plus per-agent enablement.
- Provider calls are disabled in tests.
- Tests must not call providers.
- Deterministic fallback is required when disabled, skipped, invalid, failed, or blocked.

## Failure Behavior

- Sidecar failures must not fail deterministic pipeline by default.
- Fallback payload required.
- Trace/evidence required even on failure.
- No retry storm.
- Failure output must preserve the source deterministic pipeline decision.
- Failure output must set safe safety metadata.

## Non-Mutation Contract

The future adapter must prove:

- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.

The adapter must not create approval records, queue records, execution requests, execution launch requests, applications, or submissions.

## Phase 5D Non-Goals

- No runtime adapter implementation.
- No pipeline wiring.
- No provider calls.
- No automated decisions.
- No queue writes.
- No application execution/submission.
- No scoring/ranking override.
- No resume overwrite.
- No storage schema change.
- No migration.
- No runtime behavior change.

## Decision

Phase 5D defines the future adapter interface contract only.

The production pipeline connected live-agent count remains zero, and the mutation-capable live-agent count remains zero.


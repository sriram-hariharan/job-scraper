# Phase 5S Shadow Sidecar Trace Readback Readiness Audit

This checkpoint is documentation/test only.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No service/API/UI code was added.

No UI wiring was added.

No trace writes were added.

No DB schema creation was added.

Default-off pipeline hook call site exists: 1.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

## Exact Inspected Files

Repository files inspected for this trace readback readiness audit:

- `src/agents/shadow_sidecar_hook.py`
- `src/agents/shadow_sidecar_trace_persistence.py`
- `src/agents/shadow_sidecar.py`
- `src/storage/agent_trace/store.py`
- `src/agents/trace.py`
- `src/app/services.py`
- `src/app/api.py`
- `src/pipeline/collector.py`
- `docs/phase5_shadow_sidecar_trace_persistence_readiness_audit.md`
- `tests/test_shadow_sidecar_trace_persistence_hook_integration_default_off.py`
- `tests/test_shadow_sidecar_hook_trace_capture_default_off.py`
- `tests/test_agent_trace_service_summary_readonly_no_api_change.py`
- `tests/test_agent_trace_readonly_api_endpoint_no_ui_no_writes.py`
- `tests/test_portfolio_demo_readiness_wrap_checkpoint.py`

Protected runtime, API, service, storage, and pipeline files were inspected only. They were not modified for this audit.

## Existing Trace Readback Service/API Files

Existing trace readback service/API files discovered from the repo:

- `src/app/services.py`
- `src/app/api.py`
- `src/storage/agent_trace/store.py`
- `src/agents/trace.py`

`src/app/services.py` already exposes the profile pipeline run trace readback service shape through `agent_trace_payload(...)`. That service reads existing agent run and step rows, returns public run/step payloads, and optionally attaches:

- `trace_summary`
- `stage_trace_bundle`
- `stage_trace_health`
- `stage_trace_readiness`
- `trace_evidence_pack`

`src/app/api.py` already exposes the profile pipeline run trace readback route:

- `GET /profile/pipeline-runs/{run_id}/agent-trace`

That route passes opt-in query flags for trace summary, stage trace bundle, stage trace health, stage trace readiness, and trace evidence pack.

`src/app/api.py` also contains an approval-scoped read-only trace pattern:

- `GET /api/agentic-approvals/{approval_request_id}/agent-trace`
- `_agent_trace_readonly_storage_connection`
- `_agent_trace_readonly_payload`
- `_read_agent_trace_for_approval`

These existing readback patterns are suitable references for future shadow sidecar trace readback.

## Existing Trace Storage And Helper Contracts

Existing trace storage/helper files from the repo:

- `src/storage/agent_trace/store.py`
- `src/storage/agent_trace/schema.sql`
- `src/agents/trace.py`

`src/storage/agent_trace/store.py` already defines the canonical agent trace readback concepts:

- `get_agent_run_postgres_payload`
- `list_agent_runs_postgres_payload`
- `list_agent_steps_postgres_payload`
- `build_agent_trace_summary_payload`

`build_agent_trace_summary_payload(...)` is deterministic and in-memory. It does not read Postgres, does not write Postgres, does not call external services, and does not mutate input rows.

`src/agents/trace.py` already defines the reusable trace/evidence/summary helper contracts:

- `build_stage_trace_bundle_payload`
- `evaluate_stage_trace_bundle_health`
- `build_stage_trace_readiness_decision`
- `build_agent_trace_evidence_pack`

The existing trace concepts are the right future readback surface for shadow sidecar hook trace capture and trace persistence metadata.

## Shadow Sidecar Trace Context

`src/agents/shadow_sidecar_hook.py` builds a structured in-memory `trace_capture` payload around hook output.

The hook trace capture includes:

- hook status
- chain summary
- deterministic source context
- trace bundle
- evidence pack
- trace summary
- safety metadata

`src/agents/shadow_sidecar_trace_persistence.py` builds default-off trace persistence metadata and record previews. It is not a readback service and it does not require a live database by default.

Phase 5S does not add trace readback, trace writes, API routes, service helpers, UI wiring, storage schema, or pipeline wiring.

## Suitability Decision

Existing trace readback endpoints/services can support future shadow sidecar trace readback after the shadow trace capture/persistence data is stored in the existing `agent_runs` and `agent_steps` concepts.

Future shadow sidecar trace readback should reuse existing agent trace concepts instead of adding a new readback architecture.

The safest path is to extend the existing read-only service/API pattern only after the default-off trace persistence contract is validated. A future readback helper should return compact public fields, trace summary, stage trace bundle, health, readiness, and evidence pack using the same opt-in conventions already present in `agent_trace_payload(...)`.

## Recommended First Readback Path

Recommended first readback path:

1. Keep hook trace capture default-off.
2. Keep trace persistence default-off.
3. Add service helper first.
4. Add read-only API only after service helper.
5. Add UI/dashboard only after API.

Required future readback feature flag:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED`

The global sidecar flag remains default-off.

The trace persistence flag remains default-off.

The readback flag remains default-off.

The kill switch disables trace capture/persistence/readback.

Provider calls disabled in tests.

Provider calls must not run in tests.

Deterministic fallback is required.

Readback failure must not fail deterministic pipeline.

Sidecar failures remain non-blocking.

## Required Constraints

Any future trace readback implementation must preserve all of these constraints:

- No runtime behavior change in this phase.
- No service/API/UI wiring in this phase.
- No UI wiring in this phase.
- No trace writes in this phase.
- No DB schema creation in this phase.
- No scoring override.
- No ranking override.
- No scoring/ranking override.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.
- No application execution/submission.
- Stage-level logging must be preserved.
- Existing metrics flow must be preserved.
- Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.

## Proposed Next Implementation Sequence

1. Add default-off service/helper readback function, not API/UI.
2. Add tests proving default-off and read-only behavior.
3. Add read-only API endpoint behind explicit readback flag.
4. Add UI/dashboard later.
5. Only later allow human-approved influence.
6. Only much later guarded automation.

## Explicit Non-Goals

- No runtime behavior change.
- No service/API/UI code.
- No trace writes.
- No schema change.
- No DB schema creation.
- No automated decisions.
- No mutation.
- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.
- No application execution/submission.

## Audit Decision

Phase 5S is a trace readback readiness audit only.

Existing trace readback service/API patterns are suitable for future shadow sidecar trace readback.

The future implementation should reuse `src/storage/agent_trace/store.py`, `src/agents/trace.py`, `src/app/services.py`, and `src/app/api.py` patterns instead of adding a new readback architecture.

No readback service was added.

No readback API was added.

No UI/dashboard was added.

No trace writes were added.

No runtime behavior changed.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

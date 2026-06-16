# Phase 5P Shadow Sidecar Trace Persistence Readiness Audit

This checkpoint is documentation/test only.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No scheduler behavior is changed.

No storage schema is changed.

No migration is added.

No trace writes were added.

No API/UI/service wiring was added.

Default-off pipeline hook call site exists: 1.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

## Exact Inspected Files

Repository files inspected for this trace persistence readiness audit:

- `src/agents/shadow_sidecar_hook.py`
- `src/agents/shadow_sidecar.py`
- `src/storage/agent_trace/store.py`
- `src/storage/agent_trace/schema.sql`
- `tests/test_agent_trace_recorder_service_no_pipeline_no_api.py`
- `tests/test_agent_trace_summary_helper_no_pipeline_change.py`
- `tests/test_agent_trace_service_summary_readonly_no_api_change.py`
- `tests/test_agent_trace_readonly_api_endpoint_no_ui_no_writes.py`
- `src/app/services.py`
- `src/app/api.py`
- `src/pipeline/collector.py`
- `docs/phase5_shadow_sidecar_pipeline_integration_point_audit.md`
- `docs/phase5_shadow_sidecar_trace_schema_contract_no_runtime_change.md`
- `tests/test_shadow_sidecar_hook_trace_capture_default_off.py`
- `tests/test_shadow_sidecar_first_pipeline_callsite_default_off.py`
- `tests/test_portfolio_demo_readiness_wrap_checkpoint.py`

Protected runtime, API, service, storage, and pipeline files were inspected only. They were not modified for this audit.

## Existing Trace Storage And Helper Files

The existing trace storage/helper surface is centered on:

- `src/storage/agent_trace/schema.sql`
- `src/storage/agent_trace/store.py`
- `src/agents/trace.py`
- `src/app/services.py`
- `src/app/api.py`

`src/storage/agent_trace/store.py` already defines the canonical `agent_runs` and `agent_steps` concepts through:

- `render_agent_trace_schema_sql`
- `agent_trace_table_specs`
- `agent_trace_contract_health_payload`
- `create_agent_run_postgres_payload`
- `record_agent_step_postgres_payload`
- `complete_agent_run_postgres_payload`
- `build_agent_trace_recording_payload`
- `execute_agent_trace_recording`
- `list_agent_runs_postgres_payload`
- `list_agent_steps_postgres_payload`
- `build_agent_trace_summary_payload`

Existing readback/read-only surfaces in `src/app/services.py` and `src/app/api.py` use the same concepts for trace summary, stage trace bundle, health, readiness, and evidence pack display.

## Existing Trace/Evidence/Summary Contracts

Existing trace/evidence/summary contracts discovered from the repo:

- `build_agent_trace_summary_payload(...)` is deterministic and in-memory. It does not read or write Postgres, does not call external services, and does not mutate inputs.
- `src/agents/trace.py` contains stage trace bundle, stage trace health, stage trace readiness, and trace evidence pack helper contracts.
- `src/agents/shadow_sidecar.py` emits shadow sidecar `trace_bundle`, `evidence_pack`, `readiness_decision`, `health_status`, fallback status, and no-mutation safety metadata.
- `src/agents/shadow_sidecar_hook.py` now builds a structured in-memory `trace_capture` payload around hook output, including hook status, chain summary, deterministic source context, trace bundle, evidence pack, trace summary, and safety metadata.

The current sidecar trace capture is intentionally not persistent. It is advisory/shadow only and includes `persistence_deferred=true` with the reason `no_existing_safe_persistent_shadow_sidecar_trace_sink`.

## Suitability Decision

`src/storage/agent_trace/store.py` is suitable as the future persistence home for shadow sidecar hook traces because it already models:

- agent run envelopes
- agent step records
- JSON input/output/validation metadata
- status, latency, provider, token, cost, and error fields
- read-only list/readback payloads
- deterministic trace summary helpers

Future shadow sidecar persistence should reuse existing agent trace concepts instead of adding a new storage architecture.

This phase does not add trace persistence. It does not create new tables, alter schema, create DB connections, write rows, or add API/UI/service wiring.

## Recommended First Persistence Path

Recommended future persistence path:

1. Start from the shadow sidecar hook `trace_capture` payload.
2. Map the hook envelope to an existing `agent_runs` record shape.
3. Map the hook or chain result to existing `agent_steps` record shape.
4. Preserve `trace_bundle`, `evidence_pack`, `trace_summary`, source deterministic context, and safety metadata in JSON fields.
5. Gate persistence behind `APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED`.
6. Keep the global sidecar flag default-off.
7. Keep per-agent flags default-off.
8. Keep the kill switch authoritative.
9. Use a non-blocking write path.
10. Use deterministic fallback if persistence fails.

Required future persistence feature flag:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED`

The first future implementation should add a default-off helper that can build the persistence payload without being called by the production pipeline. A later phase may wire it into the hook only when the explicit trace persistence flag is enabled.

## Required Constraints

Any future trace persistence implementation must preserve all of these constraints:

- Global sidecar flag remains default-off.
- Per-agent flags remain default-off.
- Kill switch disables trace capture/persistence.
- Provider calls disabled in tests.
- Provider calls must not run in tests.
- Deterministic fallback is required.
- Persistence failure must not fail deterministic pipeline.
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
- No API/UI/service wiring in this phase.
- No DB schema creation in this phase.
- No trace writes in this phase.
- Stage-level logging must be preserved.
- Existing metrics flow must be preserved.
- Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.

## Proposed Next Implementation Sequence

1. Add default-off trace persistence helper, not called by pipeline.
2. Add tests proving default-off and non-blocking behavior.
3. Wire persistence into the existing hook only behind explicit trace persistence flag.
4. Add service/API readback later.
5. Add UI/dashboard later.
6. Only later allow human-approved influence.
7. Only much later guarded automation.

## Explicit Non-Goals

- No runtime behavior change.
- No trace writes.
- No schema change.
- No DB schema creation.
- No API/UI/service changes.
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

Phase 5P is a readiness audit only.

The safest future path is to reuse the existing `agent_runs` and `agent_steps` trace concepts in `src/storage/agent_trace/store.py`, with a default-off persistence flag and non-blocking failure behavior.

No trace persistence was added.

No runtime behavior changed.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

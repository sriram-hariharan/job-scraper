# Phase 5B Shadow Sidecar Config Contract

This checkpoint defines the future configuration contract for a production pipeline shadow sidecar.

This is documentation/test only.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No scheduler behavior is changed.

No storage schema is changed.

No migration is added.

Live agents connected to production pipeline remain zero.

Live agents allowed to automate mutations remain zero.

## Purpose

The shadow sidecar config contract defines how a future production pipeline shadow sidecar will be enabled, configured, disabled, and audited without changing deterministic production pipeline decisions.

The contract is for future runtime wiring only. Phase 5B does not add real runtime feature flags, provider calls, pipeline adapters, storage writes, or automatic pipeline wiring.

## Default-Off Feature Flag Naming Contract

The global production pipeline shadow sidecar flag must be default-off:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=false`

The sidecar must not run unless this global flag is explicitly enabled and the global kill switch allows work.

## Per-Agent Default-Off Flags

Each live LLM-capable agent must also have a per-agent default-off flag:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=false`
- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=false`
- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=false`

Provider calls require both global and per-agent enablement. Enabling the global flag alone must not call a provider for any agent whose per-agent flag remains disabled.

## Global Kill Switch

The global kill switch must fail closed:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=true`

When `APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=true`, all sidecar work must be disabled, including deterministic sidecar stages and provider-backed shadow stages. The kill switch must take precedence over global and per-agent enablement flags.

## Provider Call Policy

- Provider calls disabled in tests.
- Provider calls must not run in tests.
- No network/provider calls in tests.
- Provider calls disabled unless global sidecar flag and per-agent flag are enabled.
- Provider calls require both global and per-agent enablement.
- Deterministic fallback required when flags are disabled, adapters are missing, provider output is invalid, providers raise errors, or validation fails.
- Provider-backed outputs remain advisory and must not change deterministic production pipeline decisions.

## Runtime Non-Mutation Contract

The sidecar must not mutate production behavior or state:

- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.
- No automated decision mutation.
- No deterministic pipeline decision mutation.

The source deterministic pipeline decision must be preserved.

## Observability Contract

Each future sidecar stage must emit enough observability to audit what happened without changing production decisions:

- Trace bundle required.
- Evidence pack required.
- Readiness decision required.
- Health status required.
- Batch/run id required.
- Stage name required.
- Agent name required.
- Source deterministic pipeline decision must be preserved.
- Disabled flags, kill-switch blocks, validation failures, provider errors, fallback usage, and skipped stages must be represented in trace/evidence payloads.

## Failure Behavior

- Sidecar failures must not fail deterministic pipeline by default.
- Failures must be logged into trace/evidence payload.
- Fallback output must be deterministic.
- No retry storm.
- Provider failure must not change scoring, ranking, queue, approval, resume, execution request, execution launch request, application execution, or application submission behavior.
- A sidecar failure can mark sidecar readiness or health as blocked/warning, but it must preserve the source deterministic pipeline decision.

## Testing Contract

Future sidecar tests must remain local and deterministic unless a later reviewed phase explicitly allows more:

- No network/provider calls in tests.
- Provider calls disabled in tests.
- Deterministic fixtures only.
- No mutation assertions.
- Config contract tests only in this phase.
- Tests must assert no scoring mutation.
- Tests must assert no ranking mutation.
- Tests must assert no queue mutation.
- Tests must assert no approval mutation.
- Tests must assert no resume mutation.
- Tests must assert no execution request mutation.
- Tests must assert no execution launch request mutation.
- Tests must assert no application execution.
- Tests must assert no application submission.

## Phase 5B Non-Goals

- No pipeline wiring.
- No real provider calls.
- No automated decisions.
- No human approval mutation.
- No application execution/submission.
- No queue writes.
- No scoring/ranking override.
- No resume overwrite.
- No runtime behavior change.

## Decision

Phase 5B defines the configuration contract only.

The production pipeline connected live-agent count remains zero, and the mutation-capable live-agent count remains zero.


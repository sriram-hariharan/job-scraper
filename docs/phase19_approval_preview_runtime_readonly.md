# Phase 19A Read-Only Approval Preview Runtime

## Scope

Phase 19A starts runtime implementation after the Phase 18 release. It adds
only a standalone agent helper for caller-supplied three-core shadow evidence.

The helper remains:

- default-off
- read-only
- shadow-only
- advisory-only

Phase 19A adds no API route, UI behavior, collector or pipeline wiring,
provider call, database write, or mutation.

## Release lineage

- `phase18-safety-wrap-release-v1`
- `phase18l-safety-wrap-release-checkpoint-v1`
- `phase18k-mutation-boundary-readiness-contract-v1`
- `phase18j-provider-call-boundary-readiness-contract-v1`
- `phase17-three-core-shadow-readiness-release-v1`

## Ordered three-core agents

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

## New helper

Phase 19A adds:

- `src/agents/three_core_approval_preview_runtime.py`
- `build_three_core_approval_preview_runtime_payload`
- `build_three_core_approval_preview_runtime_helper_payload`

The helper consumes caller-supplied runtime readback or caller-supplied shadow
sidecar evidence. It deterministically assembles reviewable approval preview
metadata and fails closed when the source evidence is missing or incomplete.
It creates no approval and grants no execution authority.

## Not authorized by Phase 19A

- No API route.
- No UI.
- No collector/pipeline wiring.
- No provider SDK/network call.
- No secrets access.
- No approval creation.
- No decision persistence.
- No audit persistence.
- No DB writes.
- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No execution request creation.
- No application execution.
- No application submission.

## Recommended next phase

Phase 19B should connect the read-only approval preview helper to a service
readback surface, still default-off, still no API/UI/pipeline wiring, still no
provider call, and still no mutation.

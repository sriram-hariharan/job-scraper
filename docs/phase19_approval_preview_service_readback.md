# Phase 19B Read-Only Approval Preview Service Readback

## Scope

Phase 19B builds on Phase 19A by adding only an agent-level service readback
helper. It does not wire into the application service layer.

The helper remains:

- default-off
- read-only
- shadow-only
- advisory-only

Phase 19B adds no API, UI, app service wiring, collector or pipeline wiring,
provider call, database access, or mutation.

## Release lineage

- `phase19a-approval-preview-runtime-readonly-v1`
- `phase18-safety-wrap-release-v1`
- `phase18l-safety-wrap-release-checkpoint-v1`
- `phase17-three-core-shadow-readiness-release-v1`

## Ordered three-core agents

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

## New helper

Phase 19B adds:

- `src/agents/three_core_approval_preview_service_readback.py`
- `build_three_core_approval_preview_service_readback_payload`
- `build_three_core_approval_preview_service_readback_helper_payload`

The helper summarizes caller-supplied Phase 19A preview payloads. When only
caller-supplied shadow evidence is available, it may invoke the Phase 19A
helper and passively summarize the resulting preview. It creates no approval,
decision, audit record, execution request, or application action.

## Not authorized by Phase 19B

- No API route.
- No UI.
- No app service wiring.
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

Phase 19C should add a default-off read-only API readback endpoint for this
service readback helper, still no UI, still no pipeline/collector wiring, still
no provider call, still no DB write, and still no mutation.

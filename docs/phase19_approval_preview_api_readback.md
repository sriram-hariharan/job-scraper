# Phase 19C Read-Only Approval Preview API Readback

## Scope

Phase 19C builds on Phase 19B by adding one default-off, read-only API
endpoint:

- `/api/three-core-approval-preview-service-readback`

The endpoint is read-only, shadow-only, and advisory-only. Phase 19C adds no
UI, app service storage, collector or pipeline wiring, provider call,
database access, or mutation.

## Release lineage

- `phase19b-approval-preview-service-readback-v1`
- `phase19a-approval-preview-runtime-readonly-v1`
- `phase18-safety-wrap-release-v1`
- `phase17-three-core-shadow-readiness-release-v1`

## Ordered three-core agents

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

## Endpoint behavior

`POST /api/three-core-approval-preview-service-readback` accepts only
caller-supplied payload data and returns the Phase 19B helper readback payload
directly. An absent body, a false `enabled` value, or a missing service
readback flag remains safely default-off.

The endpoint uses the existing application authentication middleware. It
does not load fixtures, files, secrets, provider clients, or persisted state.

## Not authorized by Phase 19C

- No UI.
- No app service storage.
- No collector or pipeline wiring.
- No provider SDK or network call.
- No secrets access.
- No approval creation.
- No decision persistence.
- No audit persistence.
- No database writes.
- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No resume mutation.
- No execution request creation.
- No application execution.
- No application submission.

## Recommended next phase

Phase 19D should add a read-only UI panel for this API readback endpoint,
still default-off, still with no pipeline or collector wiring, provider call,
database write, or mutation.

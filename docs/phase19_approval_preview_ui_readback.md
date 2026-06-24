# Phase 19D Read-Only Approval Preview UI Readback

## Scope

Phase 19D builds on Phase 19C by adding a default-off, passive UI panel for
approval preview service readback metadata. The panel is read-only,
shadow-only, and advisory-only.

Phase 19D adds no API, service storage, collector or pipeline wiring,
provider call, database access, or mutation.

## Release lineage

- `phase19c-approval-preview-api-readback-v1`
- `phase19b-approval-preview-service-readback-v1`
- `phase19a-approval-preview-runtime-readonly-v1`
- `phase18-safety-wrap-release-v1`

## Ordered three-core agents

1. `relevance_prefilter`
2. `jd_intelligence`
3. `final_application_scoring`

## Passive panel and fixture

The panel renders an existing
`three_core_approval_preview_service_readback_result` supplied in the trace
payload. It does not request data or call the Phase 19C API.

For deterministic local UI preview, use:

- `three_core_approval_preview_fixture=1`

The fixture is default-off and never replaces a real supplied readback
payload.

## Not authorized by Phase 19D

- No API changes.
- No service changes or storage.
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

Phase 19E should add a controlled read-only UI-to-API fetch path, still
default-off, with no pipeline or collector wiring, provider call, database
write, or mutation.

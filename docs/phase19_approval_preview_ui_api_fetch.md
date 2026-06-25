# Phase 19E Default-Off Approval Preview UI API Fetch

Phase 19E builds on the passive Phase 19D panel by adding a controlled,
read-only UI-to-API fetch path.

The fetch is disabled unless this query parameter is explicitly present:

- `three_core_approval_preview_api_fetch=1`

When enabled, the UI sends one POST request to:

- `/api/three-core-approval-preview-service-readback`

If the trace contains
`three_core_approval_preview_service_readback_request_payload`, that
caller-supplied request is used. Otherwise the UI sends a deterministic
default-off request with `enabled: false`. The response is stored only in the
in-memory trace payload and rendered by the existing Phase 19D renderer.

The existing `three_core_approval_preview_fixture=1` local fixture remains
available. A real supplied or API-returned readback payload always takes
precedence over fixture data.

Fetch failures are displayed as non-blocking, fail-closed, read-only metadata.

Phase 19E adds no controls, API changes, service changes, storage writes,
provider calls, database access, collector or pipeline wiring, approval
creation, decision persistence, audit persistence, scoring or ranking
mutation, queue or resume mutation, execution request creation, application
execution, or submission.

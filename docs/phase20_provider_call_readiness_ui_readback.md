# Phase 20C Provider-Call Readiness UI Readback

Phase 20C builds on Phase 20B by adding a default-off, passive UI readback
panel for provider-call readiness preflight metadata.

The panel renders only when a supplied readback payload exists, the
deterministic fixture gate `provider_call_readiness_fixture=1` is present, or
the explicit API fetch gate `provider_call_readiness_api_fetch=1` is present.
The endpoint is used only when explicitly gated:

- `POST /api/provider-call-readiness-readback`

Supplied or fetched payloads always take precedence over the local fixture.
Fetch failures render a deterministic, fail-closed, read-only safety payload.

Phase 20C changes only the static UI. It adds no backend, service, pipeline,
agent, provider, database, persistence, mutation, execution, submission,
auto-apply, or auto-submit behavior. It performs no live provider or network
call.

The permanent product rule remains: no auto-apply feature, no auto-submit
feature, no autonomous application execution, and no automatic job
application submission now or in future phases.

## Release lineage

- `phase20b-provider-call-readiness-api-readback-v1`
- `phase20a-provider-call-readiness-experiment-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`

## Recommended next phase

The next phase should be the Phase 20 wrap/release checkpoint or a stricter
no-auto-apply safety checkpoint.

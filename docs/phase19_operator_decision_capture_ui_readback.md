# Phase 19I Operator Decision Capture UI Readback

Phase 19I builds on Phase 19H by adding a default-off, read-only UI readback
panel for the operator decision capture contract.

The panel renders only when a supplied trace/readback payload is present, the
deterministic fixture gate is explicitly enabled, or the API fetch gate is
explicitly enabled. The endpoint is used only when
`operator_decision_capture_api_fetch=1`:

- `POST /api/operator-decision-capture-readback`

The local fixture gate is
`operator_decision_capture_readback_fixture=1`. Supplied or fetched readback
payloads take precedence, so the fixture never overwrites real readback data.
Fetch failures produce a passive, fail-closed safety display.

This phase changes only the static UI. It adds no backend, API, service,
pipeline, agent, provider, database, persistence, approval, execution,
submission, or mutation behavior. The panel remains read-only, shadow-only,
and advisory-only and introduces no action controls.

## Release lineage

- `phase19h-operator-decision-capture-api-readback-v1`
- `phase19g-operator-decision-capture-readback-contract-v1`
- `phase19f-approval-preview-operator-decision-preview-v1`
- `phase19e-approval-preview-ui-api-fetch-v1`
- `phase18-safety-wrap-release-v1`

## Next phase

The next phase should be the Phase 19 wrap/release checkpoint.

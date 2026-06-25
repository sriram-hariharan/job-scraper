# Phase 22E Core-Agent Evidence Materialization UI Readback
Safety scope: ui readback only.

Phase 22E builds on the Phase 22D API readback and adds a passive UI readback
surface only.

The panel is default-off, read-only, advisory-only, and manual-review only. It
renders only when page/readback data already contains a core-agent evidence
materialization payload, when the deterministic
`core_agent_evidence_materialization_fixture=1` gate is present, or when the
explicit `core_agent_evidence_materialization_api_fetch=1` gate is present.

The optional fetch is a POST to
`/api/core-agent-evidence-materialization-preview`. It is not performed by
default and fails closed as a read-only payload.

## Boundary

Phase 22E makes:

- no backend behavior changes
- no API changes
- no services changes
- no agent changes
- no pipeline changes
- no matching changes
- no tailoring runtime changes
- no provider calls
- no network calls except the optional explicitly gated POST to
  `/api/core-agent-evidence-materialization-preview`
- no database writes
- no persistence
- no mutation
- no execution
- no submission

The panel adds no buttons, inputs, forms, application controls, approval
controls, provider controls, execution controls, or autonomous controls. It
does not create approvals, persist decisions, persist audits, generate AI
tailoring, or submit applications.

## Tailoring and application safety

The tailoring agent remains separate from final scoring.
`Generate AI Tailoring` is only a later user-triggered action. Generated
tailoring suggestions remain preview/manual-review only unless the user
accepts edits.

The permanent product boundary remains:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control remains required for final job application submission

## Release references

- `phase22d-core-agent-evidence-materialization-api-readback-v1`
- `phase22c-core-agent-evidence-materialization-preview-v1`
- `phase22b-core-agent-automation-mutation-inventory-v1`
- `phase22a-manual-review-ux-hardening-v1`
- `phase21-manual-review-workflow-release-v1`
- `phase20-provider-readiness-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`
- `phase17-three-core-shadow-readiness-release-v1`

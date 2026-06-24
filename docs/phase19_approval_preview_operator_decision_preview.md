# Phase 19F Approval Preview Operator Decision Preview

Phase 19F builds on `phase19e-approval-preview-ui-api-fetch-v1` and adds only
a default-off, read-only UI preview of an operator decision.

The preview is visible when a supplied trace payload contains
`three_core_approval_preview_operator_decision_preview_result`, or when this
explicit local preview query parameter is present:

- `three_core_approval_preview_operator_decision_preview=1`

This is not a decision capture system. It does not persist decisions, create
approvals, write audit records, execute applications, or submit applications.
It adds no controls, API calls, service behavior, database access, provider
calls, pipeline wiring, or state mutation.

Release lineage:

- `phase19e-approval-preview-ui-api-fetch-v1`
- `phase19d-approval-preview-ui-readback-v1`
- `phase19c-approval-preview-api-readback-v1`
- `phase18-safety-wrap-release-v1`

The preview displays the proposed operator action, optional resume or variant,
optional reason or note, safety flags, persistence state, authorization state,
and the next safe step.

The next phase should define a separate, controlled capture and readback
contract that remains default-off and preserves the same no-execution,
no-submission, and no-mutation boundaries.

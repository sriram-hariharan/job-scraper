# Phase 22D Core-Agent Evidence Materialization API Readback

Phase 22D builds on the Phase 22C core-agent evidence materialization preview.
It adds default-off API readback only.

The endpoint is:

- Path: `/api/core-agent-evidence-materialization-preview`
- Method: `POST`

The API accepts caller JSON and returns the Phase 22C helper payload directly.
It forwards only the caller-supplied enablement, relevance prefilter, JD
intelligence, final scoring, tailoring opportunity, and manual-review context
fields. Missing or non-true enablement remains default-off.

## Boundary

This route is the only new connection. Phase 22D adds no UI or pipeline
execution connection beyond this route and makes no services changes. It does
not infer enablement from server configuration or environment variables.

The endpoint performs:

- no provider calls
- no network calls
- no database writes
- no persistence
- no mutation
- no execution
- no submission

It does not create approval records, persist decisions, persist audits, call
scoring/prefilter/matching/tailoring/pipeline runtime functions, or submit
applications. It does not generate AI tailoring.

`Generate AI Tailoring` remains only a later user-triggered action represented
by the Phase 22C helper output. No tailoring generation occurs through this
API readback.

## Permanent product boundary

The permanent product rule remains:

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control remains required for final job application submission

The API response remains default-off, read-only, advisory-only, and
manual-review only.

## Release references

- `phase22c-core-agent-evidence-materialization-preview-v1`
- `phase22b-core-agent-automation-mutation-inventory-v1`
- `phase22a-manual-review-ux-hardening-v1`
- `phase21-manual-review-workflow-release-v1`
- `phase20-provider-readiness-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`
- `phase19-readonly-approval-workflow-release-v1`
- `phase18-safety-wrap-release-v1`
- `phase17-three-core-shadow-readiness-release-v1`

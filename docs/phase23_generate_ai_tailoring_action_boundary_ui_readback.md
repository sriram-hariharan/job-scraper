# Phase 23F Generate AI Tailoring Action-Boundary UI Readback

Phase 23F builds on Phase 23E and adds a UI readback surface only for the
Generate AI Tailoring action-boundary payload.

The readback is default-off, read-only, advisory-only, and manual-review only.
It is shown only when existing page/readback data supplies a Generate AI
Tailoring action-boundary payload, or when the deterministic fixture gate
`generate_ai_tailoring_action_boundary_fixture=1` is explicitly present.

## Readback boundary

This phase makes no backend behavior changes, no API changes, no services
changes, no agent helper changes, no pipeline changes, no matching changes,
and no tailoring runtime changes.

This UI does not generate AI tailoring. This UI does not call tailoring
runtime. This UI does not call providers. This UI does not create resume
rewrites. This UI does not overwrite resumes. This UI does not submit
applications.

The only network call associated with this UI is an optional explicitly gated
POST to `/api/generate-ai-tailoring-action-boundary` when
`generate_ai_tailoring_action_boundary_api_fetch=1` is present. There are no
provider calls, no other network calls, no database writes, no persistence, no
mutation, no resume mutation, no application mutation, no execution, and no
submission.

A user trigger is required. Manual acceptance is required before any future
resume edit. Generated tailoring suggestions remain preview/manual-review only
unless user accepts edits in a later phase.

The panel repeats the safety boundary:

- no silent resume rewrite
- no automatic resume overwrite
- no real Generate AI Tailoring button or control is added in Phase 23F
- no provider calls
- no network calls except the optional explicitly gated POST
- no database writes
- no persistence
- no mutation
- no resume mutation
- no application mutation
- no execution
- no submission

## Permanent product boundary

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control remains required for final job application submission

## Release references

- `phase23e-generate-ai-tailoring-action-boundary-api-readback-v1`
- `phase23d-generate-ai-tailoring-action-boundary-contract-v1`
- `phase23c-tailoring-agent-opportunity-ui-readback-v1`
- `phase23b-tailoring-agent-opportunity-api-readback-v1`
- `phase23a-tailoring-agent-opportunity-contract-v1`
- `phase22-core-agent-evidence-materialization-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Exact Phase 23F safety markers

- UI readback only.
- Default-off, read-only, advisory-only, manual-review only.
- This UI does not generate AI tailoring.
- This UI does not call tailoring runtime.
- This UI does not call providers.
- This UI does not create resume rewrites.
- This UI does not overwrite resumes.
- This UI does not submit applications.
- User trigger is required.
- Manual acceptance is required before any future resume edit.
- Generated tailoring suggestions remain preview/manual-review only unless user accepts edits in a later phase.
- No silent resume rewrite.
- No automatic resume overwrite.

## Exact Phase 23F safety markers

- No services changes.

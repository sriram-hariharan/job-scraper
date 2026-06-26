# Phase 24B Manual Generate AI Tailoring Preview API Readback

Phase 24B builds on
`phase24a-manual-generate-ai-tailoring-preview-contract-v1` and the
`phase23-tailoring-agent-workflow-release-v1` boundary. It adds API readback
only for the manual Generate AI Tailoring preview contract.

The route is `GET /api/manual-generate-ai-tailoring-preview-contract`. It
returns deterministic readback metadata from the Phase 24A contract helper. It
does not accept user edits and does not persist user edits.

## Readback boundary

This API readback is default-off, read-only, advisory-only, manual-review
only, and preview contract only. A user trigger is required. Manual acceptance
is required before any future resume edit.

This API does not generate AI tailoring. It does not call tailoring runtime.
It does not call providers. It does not create resume rewrites. It does not
overwrite resumes. It does not mutate resumes. It does not persist data. It
does not write to database. It does not execute applications. It does not
submit applications.

This phase makes no UI changes, no services changes, no pipeline changes, and
no matching changes.

The tailoring agent remains separate from final scoring. Generated tailoring
suggestions must remain preview/manual-review only unless user accepts edits in
a later phase.

## Permanent product boundary

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- final application submission remains manually controlled by the user

## Route reference

- `/api/manual-generate-ai-tailoring-preview-contract`

## Release references

- `phase24a-manual-generate-ai-tailoring-preview-contract-v1`
- `phase23-tailoring-agent-workflow-release-v1`

## Exact Phase 24B safety markers

- API readback only.
- Default-off.
- Read-only.
- Advisory-only.
- Manual-review only.
- Preview contract only.
- User trigger required.
- Manual acceptance required.
- Does not generate AI tailoring.
- Does not call tailoring runtime.
- Does not call providers.
- Does not create resume rewrites.
- Does not overwrite resumes.
- Does not mutate resumes.
- Does not persist data.
- Does not write to database.
- Does not execute applications.
- Does not submit applications.
- No auto-apply.
- No auto-submit.
- No autonomous application execution.
- No automatic job application submission.
- No UI changes.
- No services changes.
- No pipeline changes.
- No matching changes.
- Tailoring agent remains separate from final scoring.
- Generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase.

# Phase 24A Manual Generate AI Tailoring Preview Contract

Phase 24A starts the next safe layer after
`phase23-tailoring-agent-workflow-release-v1`. It adds a contract-only helper
for a future manually triggered Generate AI Tailoring preview request.

This contract is default-off, read-only, advisory-only, manual-review only,
and preview contract only. It describes whether a future preview request would
be allowed, blocked, or incomplete. It is not a runtime generation path.

## Manual preview boundary

A user trigger is required. Manual acceptance is required before any future
resume edit. Generated tailoring suggestions must remain preview/manual-review
only unless user accepts edits in a later phase.

The helper does not generate AI tailoring. It does not call tailoring runtime.
It does not call providers. It does not create resume rewrites. It does not
overwrite resumes. It does not mutate resumes. It does not persist data. It
does not write to database. It does not execute applications. It does not
submit applications.

The tailoring agent remains separate from final scoring. Phase 24A only
describes manual preview readiness from caller-supplied metadata.

## Permanent product boundary

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- final application submission remains manually controlled by the user

## Release reference

- `phase23-tailoring-agent-workflow-release-v1`

## Exact Phase 24A safety markers

- Contract-only.
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
- Tailoring agent remains separate from final scoring.
- Generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase.

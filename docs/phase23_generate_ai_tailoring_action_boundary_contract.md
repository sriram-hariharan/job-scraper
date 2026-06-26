# Phase 23D Generate AI Tailoring Action-Boundary Contract

Phase 23D builds on Phase 23C. This phase defines the action boundary for a
future user-triggered `Generate AI Tailoring` action.

The contract is default-off, read-only, advisory-only, and manual-review only.
A user trigger is required. Even after that trigger, Phase 23D reports
readiness only. This phase does not generate AI tailoring. This phase does not
call tailoring runtime. This phase does not call providers.

## Action boundary

This phase does not add a UI button and does not add an API endpoint. This
phase does not create resume rewrites. It does not overwrite resumes. It does
not submit applications.

Manual acceptance is required before any future resume edit. Generated
tailoring suggestions must remain preview/manual-review only unless the user
accepts edits in a later phase.

The contract guarantees:

- no silent resume rewrite
- no automatic resume overwrite
- no resume mutation
- no application submission
- no provider calls
- no network calls
- no database writes
- no persistence
- no mutation
- no execution
- no submission

## Permanent product boundary

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- manual user control remains required for final job application submission

## Release references

- `phase23c-tailoring-agent-opportunity-ui-readback-v1`
- `phase23b-tailoring-agent-opportunity-api-readback-v1`
- `phase23a-tailoring-agent-opportunity-contract-v1`
- `phase22-core-agent-evidence-materialization-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Exact Phase 23D safety markers

- This phase does not call tailoring runtime.
- This phase does not submit applications.

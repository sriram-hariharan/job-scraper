# Phase 25A Manual Generate AI Tailoring Preview Request-Packet Contract

Phase 25A adds a default-off, read-only request-packet contract for a future manual Generate AI Tailoring preview flow.

This phase only describes whether a request packet may be prepared. It does not generate AI tailoring, does not call providers, does not call the tailoring runtime, does not create resume rewrites, does not overwrite resumes, does not mutate resumes, does not persist data, does not write to a database, does not execute applications, and does not submit applications.

## Safety markers

- request-packet contract only
- default-off
- read-only
- advisory-only
- manual-review only
- requires an explicit user trigger
- manual acceptance required
- no provider calls
- no network calls
- no tailoring runtime calls
- no AI tailoring generation
- no generated tailoring text
- no resume rewrite
- no resume overwrite
- no resume mutation
- no application mutation
- no database writes
- no persistence
- no execution
- no submission
- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission

The tailoring agent remains separate from final scoring. Generated tailoring suggestions must remain preview/manual-review only unless the user accepts edits in a later phase. This phase does not create real tailoring output and does not add a UI action control.

## Request-packet inputs

The helper accepts optional dictionaries for:

- Phase 24 preview contract payload
- job metadata
- selected resume metadata
- tailoring opportunity payload
- user trigger metadata

Without an explicit user trigger, the contract is blocked. With a trigger but missing inputs, the contract is incomplete and reports the missing input names. With a trigger and all inputs, the helper may prepare a deterministic request-packet description for manual review only.

## References

- phase24-manual-generate-ai-tailoring-preview-release-v1
- phase24d-manual-generate-ai-tailoring-preview-release-checkpoint-v1
- phase24c-manual-generate-ai-tailoring-preview-ui-readback-v1
- phase24b-manual-generate-ai-tailoring-preview-api-readback-v1
- phase24a-manual-generate-ai-tailoring-preview-contract-v1
- phase23-tailoring-agent-workflow-release-v1
- phase20d-no-auto-apply-safety-checkpoint-v1

## Exact Phase 25A safety markers

- User trigger required.
- Does not call tailoring runtime.
- Does not write to database.
- No mutation.

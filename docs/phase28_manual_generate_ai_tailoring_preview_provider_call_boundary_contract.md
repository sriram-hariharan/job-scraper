# Phase 28A Manual Generate AI Tailoring Preview Provider-Call Boundary Contract

Phase 28A adds a provider-call boundary contract only for a future manually triggered Generate AI Tailoring preview flow.

This phase is default-off, read-only, advisory-only, and manual-review only. User trigger required. Operator confirmation required. Manual acceptance required. Provider request-envelope required. Provider configuration required. Provider call policy required.

It describes whether a future manually controlled provider-call boundary could be reviewed later, but it does not call providers and does not call network.

## Safety markers

- Provider-call boundary contract only.
- Default-off.
- Read-only.
- Advisory-only.
- Manual-review only.
- User trigger required.
- Operator confirmation required.
- Manual acceptance required.
- Provider request-envelope required.
- Provider configuration required.
- Provider call policy required.
- Does not call providers.
- Does not call network.
- Does not dispatch.
- Does not generate AI tailoring.
- Does not call tailoring runtime.
- Does not create real tailoring output.
- Does not create resume rewrites.
- Does not overwrite resumes.
- Does not mutate resumes.
- Does not persist data.
- Does not write to database.
- Does not execute applications.
- Does not submit applications.
- No provider calls.
- No network calls.
- No database writes.
- No persistence.
- No mutation.
- No resume mutation.
- No application mutation.
- No execution.
- No submission.
- No auto-apply.
- No auto-submit.
- No autonomous application execution.
- No automatic job application submission.

Tailoring agent remains separate from final scoring. Generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase.

This phase does not create real tailoring output. This phase does not add a UI action control.

## Provider-call boundary inputs

The helper accepts optional dictionaries for:

- Phase 27 provider request-envelope payload.
- Phase 26 dispatch-boundary payload.
- Phase 25 request-packet payload.
- User trigger metadata.
- Operator confirmation metadata.
- Provider configuration metadata.
- Provider call policy metadata.

Without an explicit user trigger, provider-call readiness is blocked. Without operator confirmation, provider-call readiness is blocked. Without an accepted Phase 27 provider request-envelope payload, provider-call readiness is blocked. Without provider configuration metadata, provider-call readiness is blocked. Without provider call policy metadata, provider-call readiness is blocked.

When a user trigger, operator confirmation, accepted provider request-envelope stub, dispatch-boundary stub, request-packet stub, provider configuration stub, and provider call policy stub are present, the helper may mark the provider-call boundary ready while still performing no provider call, no network call, no dispatch, no tailoring runtime call, no AI tailoring generation, no persistence, no mutation, no execution, and no submission.

The provider call plan must not include generated tailoring text. The helper must not produce real tailoring output.

## References

- phase27-manual-generate-ai-tailoring-preview-provider-request-envelope-release-v1
- phase27d-manual-generate-ai-tailoring-preview-provider-request-envelope-release-checkpoint-v1
- phase27c-manual-generate-ai-tailoring-preview-provider-request-envelope-ui-readback-v1
- phase27b-manual-generate-ai-tailoring-preview-provider-request-envelope-api-readback-v1
- phase27a-manual-generate-ai-tailoring-preview-provider-request-envelope-contract-v1
- phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1
- phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1
- phase24-manual-generate-ai-tailoring-preview-release-v1
- phase23-tailoring-agent-workflow-release-v1
- phase20d-no-auto-apply-safety-checkpoint-v1

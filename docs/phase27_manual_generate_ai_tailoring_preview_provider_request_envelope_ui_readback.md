# Phase 27C Manual Generate AI Tailoring Preview Provider Request-Envelope UI Readback

Phase 27C adds UI readback only for the Phase 27B manual Generate AI Tailoring preview provider request-envelope API readback.

The UI passively displays the read-only payload from `/api/manual-generate-ai-tailoring-preview-provider-request-envelope-contract` using `renderManualGenerateAiTailoringPreviewProviderRequestEnvelopeReadbackSection`. It does not add a real Generate AI Tailoring button or control, no provider-call control, no network-call control, and no dispatch control.

## Readback boundary

This UI readback is provider request-envelope contract only, default-off, read-only, advisory-only, and manual-review only. User trigger required. Operator confirmation required. Manual acceptance required. Dispatch boundary required. Provider configuration required.

This UI does not call providers. It does not call network. It does not dispatch. It does not generate AI tailoring. It does not call tailoring runtime. It does not create real tailoring output. It does not create resume rewrites. It does not overwrite resumes. It does not mutate resumes. It does not persist data. It does not write to database. It does not execute applications. It does not submit applications.

No provider calls. No network calls. No database writes. No persistence. No mutation. No resume mutation. No application mutation. No execution. No submission. No auto-apply. No auto-submit. No autonomous application execution. No automatic job application submission.

This phase makes no backend behavior changes, no API changes, no services changes, no pipeline changes, no matching changes, and no tailoring runtime changes.

Tailoring agent remains separate from final scoring. Generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase.

## Route, renderer, and helper references

- `/api/manual-generate-ai-tailoring-preview-provider-request-envelope-contract`
- `renderManualGenerateAiTailoringPreviewProviderRequestEnvelopeReadbackSection`
- `build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract`

## Release references

- `phase27b-manual-generate-ai-tailoring-preview-provider-request-envelope-api-readback-v1`
- `phase27a-manual-generate-ai-tailoring-preview-provider-request-envelope-contract-v1`
- `phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1`
- `phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1`
- `phase24-manual-generate-ai-tailoring-preview-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Exact Phase 27C safety markers

- UI readback only.
- Provider request-envelope contract only.
- Default-off.
- Read-only.
- Advisory-only.
- Manual-review only.
- User trigger required.
- Operator confirmation required.
- Manual acceptance required.
- Dispatch boundary required.
- Provider configuration required.
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
- No backend behavior changes.
- No API changes.
- No services changes.
- No pipeline changes.
- No matching changes.
- No tailoring runtime changes.
- Tailoring agent remains separate from final scoring.
- Generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase.
- No real Generate AI Tailoring button or control.
- No provider-call control.
- No network-call control.
- No dispatch control.

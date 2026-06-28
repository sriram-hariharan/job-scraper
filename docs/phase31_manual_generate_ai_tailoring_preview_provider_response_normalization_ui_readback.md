# Phase 31C Manual Generate AI Tailoring Preview Provider Response Normalization UI Readback

This phase adds UI readback only for the provider response normalization contract. It is default-off, read-only, advisory-only, manual-review only, response normalization only, and provider response normalization contract only.

The UI renderer is `renderManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackSection`. Its optional gated readback uses GET against `/api/manual-generate-ai-tailoring-preview-provider-response-normalization-contract` and displays the result produced by `build_manual_generate_ai_tailoring_preview_provider_response_normalization_contract`.

Safety markers displayed by the readback:

- user trigger required
- operator confirmation required
- manual acceptance required
- provider response validation required
- provider response candidate required
- response normalization policy required
- provider configuration required
- response normalization ready
- normalized provider response accepted for future manual preview
- blocked reasons
- missing inputs
- normalization findings
- normalized provider response contract
- deterministic response normalization key
- manual user control required
- preview/manual-review only
- next safe step

The readback does not call providers, does not call network, does not dispatch, does not generate AI tailoring, does not call tailoring runtime, does not create real tailoring output, does not create resume rewrites, does not overwrite resumes, does not mutate resumes, does not persist data, does not write to database, does not execute applications, and does not submit applications.

It preserves no provider calls, no network calls, no database writes, no persistence, no mutation, no resume mutation, no application mutation, no execution, no submission, no auto-apply, and no auto-submit. It adds no real Generate AI Tailoring button or control, no provider-call control, no network-call control, and no dispatch control.

There are no backend behavior changes, no API changes, no services changes, no pipeline changes, no matching changes, and no tailoring runtime changes. The tailoring agent remains separate from final scoring. Generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase.

Traceability tags:

- phase31b-manual-generate-ai-tailoring-preview-provider-response-normalization-api-readback-v1
- phase31a-manual-generate-ai-tailoring-preview-provider-response-normalization-contract-v1
- phase30-manual-generate-ai-tailoring-preview-provider-response-validation-release-v1
- phase29-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-release-v1
- phase28-manual-generate-ai-tailoring-preview-provider-call-boundary-release-v1
- phase27-manual-generate-ai-tailoring-preview-provider-request-envelope-release-v1
- phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1
- phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1
- phase24-manual-generate-ai-tailoring-preview-release-v1
- phase23-tailoring-agent-workflow-release-v1
- phase20d-no-auto-apply-safety-checkpoint-v1

- No autonomous application execution.

- No automatic job application submission.

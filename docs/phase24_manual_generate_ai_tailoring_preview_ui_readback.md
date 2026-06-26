# Phase 24C Manual Generate AI Tailoring Preview UI Readback

Phase 24C builds on
`phase24b-manual-generate-ai-tailoring-preview-api-readback-v1`,
`phase24a-manual-generate-ai-tailoring-preview-contract-v1`, and
`phase23-tailoring-agent-workflow-release-v1`. It adds UI readback only for the
manual Generate AI Tailoring preview contract.

The UI reads the passive route
`/api/manual-generate-ai-tailoring-preview-contract` and renders it with
`renderManualGenerateAiTailoringPreviewReadbackSection`.

## Readback boundary

This UI readback is default-off, read-only, advisory-only, manual-review only,
and preview contract only. A user trigger is required. Manual acceptance is
required before any future resume edit.

This UI does not generate AI tailoring. It does not call tailoring runtime. It
does not call providers. It does not create resume rewrites. It does not
overwrite resumes. It does not mutate resumes. It does not persist data. It
does not write to database. It does not execute applications. It does not
submit applications.

There is no real Generate AI Tailoring button or control. This phase makes no
backend behavior changes, no API changes, no services changes, no pipeline
changes, no matching changes, and no tailoring runtime changes.

The tailoring agent remains separate from final scoring. Generated tailoring
suggestions must remain preview/manual-review only unless user accepts edits in
a later phase.

## Permanent product boundary

- no auto-apply
- no auto-submit
- no autonomous application execution
- no automatic job application submission
- final application submission remains manually controlled by the user

## References

- Route reference: `/api/manual-generate-ai-tailoring-preview-contract`
- Renderer reference: `renderManualGenerateAiTailoringPreviewReadbackSection`
- `phase24b-manual-generate-ai-tailoring-preview-api-readback-v1`
- `phase24a-manual-generate-ai-tailoring-preview-contract-v1`
- `phase23-tailoring-agent-workflow-release-v1`

## Exact Phase 24C safety markers

- UI readback only.
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
- No backend behavior changes.
- No API changes.
- No services changes.
- No pipeline changes.
- No matching changes.
- No tailoring runtime changes.
- Tailoring agent remains separate from final scoring.
- Generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase.
- No real Generate AI Tailoring button or control.

# Phase 33A Controlled Agent Router Read-Only

Phase 33A introduces a controlled agent router that is read-only, deterministic, advisory-only, default-off, and limited to allowlisted routing only.

The router accepts caller-supplied current job/application state and recommends the next allowed step. It does not run the step. It maps only to existing adjacent responsibilities:

- relevance prefilter
- JD intelligence / JD understanding
- final application scoring
- tailoring opportunity check
- manual Generate AI Tailoring preview preparation

Allowed routing steps are closed to:

- `run_relevance_prefilter`
- `run_jd_intelligence`
- `run_final_application_scoring`
- `check_tailoring_opportunity`
- `prepare_manual_tailoring_preview`
- `await_manual_review`

Safety guarantees:

- Does not call LLM.
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
- No auto-apply.
- No auto-submit.
- No autonomous application execution.
- No automatic job application submission.
- Manual user control remains required.

Routing behavior:

- Missing or invalid `current_state` returns `await_manual_review`.
- Missing relevance result returns `run_relevance_prefilter`.
- Not relevant returns `await_manual_review`.
- Relevant without JD intelligence returns `run_jd_intelligence`.
- JD intelligence without final score returns `run_final_application_scoring`.
- Final score below threshold returns `await_manual_review`.
- Final score meeting threshold without tailoring opportunity returns `check_tailoring_opportunity`.
- Helpful tailoring opportunity returns `prepare_manual_tailoring_preview`.
- Non-helpful tailoring opportunity returns `await_manual_review`.
- Completed safe analysis returns `await_manual_review`.

Tailoring agent remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic. LLM calls are not introduced in this phase. Persistence is not introduced in this phase.

References:

- `phase32b-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-api-readback-v1`
- `phase32a-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-contract-v1`
- `phase31-manual-generate-ai-tailoring-preview-provider-response-normalization-release-v1`
- `phase30-manual-generate-ai-tailoring-preview-provider-response-validation-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

The router does not run those stages. It only recommends the next allowed step.

# Phase 33B Controlled Agent Router Workflow State Adapter Read-Only

Phase 33B adds a controlled agent router workflow state adapter. This is a capability step on the revised path, not another safety-wrapper chain.

The adapter normalizes supplied artifacts into the Phase 33A router `current_state`, calls the Phase 33A router helper, and returns a read-only agent handoff packet. It does not run the supplied workflow stages.

Supplied artifacts may come from existing adjacent responsibilities:

- relevance prefilter
- JD intelligence / JD understanding
- final application scoring
- tailoring opportunity check
- manual Generate AI Tailoring preview preparation

The adapter does not run relevance prefilter. It does not run JD intelligence. It does not run final application scoring. It does not run tailoring opportunity check. It does not run manual Generate AI Tailoring preview preparation.

Safety guarantees:

- It does not call LLM.
- It does not call providers.
- It does not call network.
- It does not dispatch.
- It does not generate AI tailoring.
- It does not call tailoring runtime.
- It does not create real tailoring output.
- It does not create resume rewrites.
- It does not overwrite resumes.
- It does not mutate resumes.
- It does not persist data.
- It does not write to database.
- It does not execute applications.
- It does not submit applications.
- No auto-apply.
- No auto-submit.
- No autonomous application execution.
- No automatic job application submission.
- Manual user control remains required.

The handoff packet includes the selected next allowed step, why it was selected, supplied artifacts available for that step, missing inputs for that step, and the router allowlist/blocklist. It never includes an executable callback, function pointer, provider request, network request, mutation command, database write command, or application submission command.

Manual tailoring preview artifacts are presence/metadata-only in this phase. The adapter does not include generated tailoring text or real tailoring output.

Tailoring agent remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic. LLM calls are not introduced in this phase. Persistence is not introduced in this phase.

References:

- `phase33a-controlled-agent-router-readonly-v1`
- `phase32b-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-api-readback-v1`
- `phase32a-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-contract-v1`
- `phase31-manual-generate-ai-tailoring-preview-provider-response-normalization-release-v1`
- `phase30-manual-generate-ai-tailoring-preview-provider-response-validation-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

It normalizes supplied artifacts into router current_state.

It returns an agent handoff packet.

# Phase 49A controlled exact resume change-set real provider runtime adapter default-off

Phase 49A adds a controlled exact resume change-set real provider runtime adapter. This is the first real-provider-capable phase for exact resume change-set refinement.

The adapter is default-off. It requires manual trigger confirmation, `enable_real_provider_call`, provider policy `allow_real_provider_call`, a valid request packet, and either an injected provider callable or an allowed configured provider callable path before any provider execution can occur.

It can call an injected provider callable. It can resolve a configured provider callable path only after all gates pass. It prefers existing project provider runtime surfaces such as `src/tailoring/llm.py`. It does not hardcode provider function names. It does not import provider SDKs directly. It does not add dependencies.

Safety boundaries:

- It does not validate provider response.
- It does not normalize provider response.
- It does not create manual review packets.
- It does not create UI/API readback payload.
- It does not modify UI files.
- It does not modify API/service files.
- It does not persist data.
- It does not write to database.
- It does not create real tailoring output.
- It does not produce a full resume.
- It does not overwrite resumes.
- It does not mutate resumes.
- It does not execute applications.
- It does not submit applications.
- No auto-apply.
- No auto-submit.
- Manual user control remains required.
- Existing UI/manual control remains the acceptance point.
- Provider response validation happens in Phase 45.
- Provider response normalization happens in Phase 46.
- Manual review packets happen in Phase 47.
- Manual review readback happens in Phase 48.
- Resume overwrite is not needed.
- Application execution is not needed.

Real provider execution is separate from provider response validation, provider response normalization, manual review, user acceptance, resume mutation, and final scoring.

References:

- `phase48-controlled-exact-resume-change-set-manual-review-readback-adapter-release-v1`
- `phase48b-controlled-exact-resume-change-set-manual-review-readback-adapter-dry-run-command-default-off-v1`
- `phase48a-controlled-exact-resume-change-set-manual-review-readback-adapter-default-off-v1`
- `phase47-controlled-exact-resume-change-set-manual-review-packet-builder-release-v1`
- `phase46-controlled-exact-resume-change-set-provider-response-normalization-release-v1`
- `phase45-controlled-exact-resume-change-set-provider-response-validation-release-v1`
- `phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1`
- `phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1`
- `phase42-exact-resume-change-set-proposal-builder-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Phase 49A verifier marker alignment

- requires enable_real_provider_call
- requires provider policy allow_real_provider_call
- prefers existing project provider runtime surfaces such as src/tailoring/llm.py

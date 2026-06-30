# Phase 49B controlled exact resume change-set real provider runtime adapter dry-run command default-off

Phase 49B adds a controlled exact resume change-set real provider runtime adapter dry-run command. This is the first CLI phase capable of a real provider call for exact resume change-set refinement.

The command is default-off. It requires manual trigger confirmation, `enable_real_provider_call`, provider policy `allow_real_provider_call`, and a configured provider callable path before Phase 49A can perform provider execution.

The command reads supplied request packet files and reads supplied request result files. It calls the Phase 49A controlled exact resume change-set real provider runtime adapter and can pass a configured provider callable path to Phase 49A.

Safety boundaries:

- It does not import provider SDKs directly.
- It does not directly import `src/tailoring/llm.py`.
- It does not add dependencies.
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

Example command:

```bash
PYTHONPATH="$PWD" python run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py --input path/to/request_packet.json --enable-real-provider-call --manual-trigger-confirmed --allow-real-provider-call --provider-callable-path src.tailoring.llm.some_existing_callable
```

References:

- `phase49a-controlled-exact-resume-change-set-real-provider-runtime-adapter-default-off-v1`
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

## Phase 49B verifier marker alignment

- requires enable_real_provider_call
- requires provider policy allow_real_provider_call
- requires a configured provider callable path
- does not directly import src/tailoring/llm.py

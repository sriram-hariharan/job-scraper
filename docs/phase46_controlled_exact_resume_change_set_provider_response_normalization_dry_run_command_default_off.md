# Phase 46B controlled exact resume change-set provider response normalization dry-run command default-off

Phase 46B adds a controlled exact resume change-set provider response normalization dry-run command.

The command reads supplied validation result file, reads supplied provider response file, and reads supplied original change proposals file. It calls the Phase 46A controlled exact resume change-set provider response normalization helper and prints provider response normalization JSON to stdout.

It normalizes provider responses after Phase 45 validation. It is not a provider call phase. It is not a validation phase. It normalizes validated refined change proposals, preserves manual review and user acceptance requirements, and produces normalized proposal-only output.

The command does not create new proposal text. Existing UI/manual control remains the acceptance point, and exact worthy changes must be manually accepted by the user.

Safety boundaries:

- It does not call LLM.
- It does not call provider.
- It does not call network.
- It does not call tailoring runtime.
- It does not generate real tailoring output.
- It does not produce a full resume.
- It does not overwrite resumes.
- It does not mutate resumes.
- It does not persist data.
- It does not write to database.
- It does not execute applications.
- It does not submit applications.
- No auto-apply.
- No auto-submit.
- Manual user control remains required.
- Resume overwrite is not needed.
- Application execution is not needed.
- UI/manual review readback comes in a later phase.

Provider response validation, provider response normalization, UI acceptance, resume mutation, and final scoring remain separate.

Example command:

```bash
PYTHONPATH="$PWD" python run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py --input path/to/validation_result.json --original-change-proposals path/to/change_proposals.json
```

References:

- `phase46a-controlled-exact-resume-change-set-provider-response-normalization-default-off-v1`
- `phase45-controlled-exact-resume-change-set-provider-response-validation-release-v1`
- `phase45b-controlled-exact-resume-change-set-provider-response-validation-dry-run-command-default-off-v1`
- `phase45a-controlled-exact-resume-change-set-provider-response-validation-default-off-v1`
- `phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1`
- `phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1`
- `phase42-exact-resume-change-set-proposal-builder-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

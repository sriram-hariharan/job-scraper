# Phase 43B controlled exact resume change-set LLM request packet dry-run command default-off

Phase 43B adds the controlled exact resume change-set LLM request packet dry-run command. It makes the Phase 43A request packet builder usable from the terminal while preserving the default-off, read-only boundary.

The command reads supplied change proposal file input. It reads supplied proposal result file input. It reads supplied resume context file input. It reads supplied JD context file input. It reads supplied tailoring context file input. It calls the Phase 43A controlled exact resume change-set LLM request packet builder and prints provider-ready request packet JSON to stdout.

The command creates a provider-ready request packet. Provider dispatch is prepared but not executed. The LLM call comes in a later controlled provider-call phase.

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
- Existing UI/manual control remains the acceptance point.
- Exact worthy changes must be manually accepted by the user.
- Resume overwrite is not needed.
- Application execution is not needed.

Example command:

```bash
PYTHONPATH="$PWD" python run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py --input path/to/change_proposals.json --resume-context path/to/resume_context.json --jd-context path/to/jd_context.json --tailoring-context path/to/tailoring_context.json
```

References:

- `phase43a-controlled-exact-resume-change-set-llm-request-packet-default-off-v1`
- `phase42-exact-resume-change-set-proposal-builder-release-v1`
- `phase42b-exact-resume-change-set-proposal-builder-dry-run-command-default-off-v1`
- `phase42a-exact-resume-change-set-proposal-builder-default-off-v1`
- `phase41-jd-evidence-score-impact-review-queue-builder-release-v1`
- `phase40-jd-evidence-score-impact-review-packet-builder-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

# Phase 44B controlled exact resume change-set provider call boundary dry-run command default-off

Phase 44B adds the controlled exact resume change-set provider call boundary dry-run command. It makes the Phase 44A provider-call boundary testable from the terminal while preserving the default-off boundary.

The command reads supplied request packet file input. It reads supplied request result file input when provided. It reads supplied provider response fixture file input when provided. It calls the Phase 44A controlled exact resume change-set provider call boundary and prints provider call boundary JSON to stdout.

Default behavior does not call provider. Provider call is explicit/manual-triggered only. The command can use a simulated provider response fixture as an injected local callable for dry-run testing. The simulated provider callable is not a real provider SDK call.

Safety boundaries:

- It does not import provider SDKs.
- It does not call network directly.
- It keeps network_call_performed false.
- It does not call tailoring runtime.
- It does not generate real tailoring output by itself.
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
- Provider response validation comes in a later phase.

Example command:

```bash
PYTHONPATH="$PWD" python run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py --input path/to/request_packet.json
```

References:

- `phase44a-controlled-exact-resume-change-set-provider-call-boundary-default-off-v1`
- `phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1`
- `phase43b-controlled-exact-resume-change-set-llm-request-packet-dry-run-command-default-off-v1`
- `phase43a-controlled-exact-resume-change-set-llm-request-packet-default-off-v1`
- `phase42-exact-resume-change-set-proposal-builder-release-v1`
- `phase42b-exact-resume-change-set-proposal-builder-dry-run-command-default-off-v1`
- `phase42a-exact-resume-change-set-proposal-builder-default-off-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

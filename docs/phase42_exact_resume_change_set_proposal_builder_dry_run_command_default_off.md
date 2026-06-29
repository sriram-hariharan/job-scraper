# Phase 42B exact resume change-set proposal builder dry-run command default-off

Phase 42B adds the exact resume change-set proposal builder dry-run command. This is the exact worthy resume change path after the review queue. It is not another safety-wrapper chain.

The command reads a supplied review queue file, optionally reads a supplied queue result file, reads supplied resume context file, reads supplied JD context file, and reads supplied tailoring context file. It calls the Phase 42A exact resume change-set proposal builder and prints exact resume change proposal JSON to stdout.

The command produces exact worthy resume change proposals and creates proposal-only before/after changes. It does not produce a full resume, does not overwrite resumes, and does not mutate resumes.

Example command:

```bash
PYTHONPATH="$PWD" python run_exact_resume_change_set_proposal_builder_dry_run.py --input path/to/review_queue.json --resume-context path/to/resume_context.json --jd-context path/to/jd_context.json --tailoring-context path/to/tailoring_context.json
```

Safety boundaries:

- It does not call LLM.
- It does not call provider.
- It does not call network.
- It does not call tailoring runtime.
- It does not generate real tailoring output.
- It does not produce final application score.
- It does not change scoring logic.
- It does not call matching/scoring modules.
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

References:

- `phase42a-exact-resume-change-set-proposal-builder-default-off-v1`
- `phase41-jd-evidence-score-impact-review-queue-builder-release-v1`
- `phase41b-jd-evidence-score-impact-review-queue-builder-dry-run-command-default-off-v1`
- `phase41a-jd-evidence-score-impact-review-queue-builder-default-off-v1`
- `phase40-jd-evidence-score-impact-review-packet-builder-release-v1`
- `phase39-jd-evidence-score-impact-planning-artifact-annotator-release-v1`
- `phase38-jd-evidence-score-impact-preview-release-v1`
- `phase37-jd-evidence-scoring-contribution-preview-release-v1`
- `phase36-jd-evidence-final-scoring-feature-adapter-release-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

## Phase 42B verifier marker alignment

- reads supplied review queue file.
- reads supplied queue result file.


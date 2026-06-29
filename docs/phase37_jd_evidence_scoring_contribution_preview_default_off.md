# Phase 37A JD evidence scoring contribution preview default-off

Phase 37A adds the JD evidence scoring contribution preview. This is a capability step on the revised path. It is not another safety-wrapper chain.

The helper performs deterministic contribution preview. It converts final-scoring-ready feature packets into advisory contribution previews and produces bounded advisory contribution points. It preserves existing score fields.

Safety boundaries:

- It does not produce final application score.
- It does not change existing scoring logic.
- It does not call matching/scoring modules.
- It does not run relevance prefilter.
- It does not run JD intelligence extraction.
- It does not run evidence matching.
- It does not run scoring feature preparation.
- It does not run tailoring opportunity check.
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

JD intelligence remains separate from final scoring. Evidence matching remains separate from final scoring. Scoring feature preparation remains separate from final scoring. Contribution preview remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic.

References:

- `phase36-jd-evidence-final-scoring-feature-adapter-release-v1`
- `phase36b-jd-evidence-final-scoring-feature-adapter-dry-run-command-default-off-v1`
- `phase36a-jd-evidence-final-scoring-feature-adapter-default-off-v1`
- `phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1`
- `phase35b-jd-signal-planning-artifact-evidence-enricher-default-off-v1`
- `phase35a-jd-signal-resume-evidence-matrix-default-off-v1`
- `phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

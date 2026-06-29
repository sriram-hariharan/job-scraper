# Phase 38B JD evidence score impact preview dry-run command default-off

Phase 38B adds the JD evidence score impact preview dry-run command. This is a capability step on the revised path. It is not another safety-wrapper chain.

The command performs deterministic score impact preview from operator-supplied files. It reads supplied contribution packet file inputs, supports JSON, JSONL, and CSV contribution row inputs, supports supplied contribution rows, calls the Phase 38A JD evidence score impact preview helper, and prints hypothetical score impact preview JSON to stdout.

The command does not write output files. It produces hypothetical score preview values, preserves existing score fields, and does not produce final application score. It does not change existing scoring logic and does not call matching/scoring modules.

Safety boundaries:

- It does not run relevance prefilter.
- It does not run JD intelligence extraction.
- It does not run evidence matching.
- It does not run scoring feature preparation.
- It does not run contribution preview.
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

JD intelligence remains separate from final scoring. Evidence matching remains separate from final scoring. Scoring feature preparation remains separate from final scoring. Contribution preview remains separate from final scoring. Score impact preview remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic.

Example command:

```bash
PYTHONPATH="$PWD" python run_jd_evidence_score_impact_preview_dry_run.py --input path/to/contribution_packet.json
```

References:

- `phase38a-jd-evidence-score-impact-preview-default-off-v1`
- `phase37-jd-evidence-scoring-contribution-preview-release-v1`
- `phase37b-jd-evidence-scoring-contribution-preview-dry-run-command-default-off-v1`
- `phase37a-jd-evidence-scoring-contribution-preview-default-off-v1`
- `phase36-jd-evidence-final-scoring-feature-adapter-release-v1`
- `phase36b-jd-evidence-final-scoring-feature-adapter-dry-run-command-default-off-v1`
- `phase36a-jd-evidence-final-scoring-feature-adapter-default-off-v1`
- `phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1`
- `phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

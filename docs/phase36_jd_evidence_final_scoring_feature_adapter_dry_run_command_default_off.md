# Phase 36B JD evidence final-scoring feature adapter dry-run command default-off

Phase 36B adds the JD evidence final-scoring feature adapter dry-run command. This is a capability step on the revised path. It is not another safety-wrapper chain.

The command performs deterministic scoring feature preparation. It reads supplied planning artifact file input, supports JSON, JSONL, and CSV planning-like row inputs, supports supplied evidence results, calls the Phase 36A JD evidence final-scoring feature adapter, and prints final-scoring-ready feature packets to stdout. It does not write output files.

The dry-run command preserves existing score fields.

Safety boundaries:

- It does not produce final application score.
- It does not change existing scoring logic.
- It does not call matching/scoring modules.
- It does not run relevance prefilter.
- It does not run JD intelligence extraction.
- It does not run evidence matching.
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

JD intelligence remains separate from final scoring. Evidence matching remains separate from final scoring. Scoring feature preparation remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic.

Example command:

```bash
PYTHONPATH="$PWD" python run_jd_evidence_final_scoring_feature_adapter_dry_run.py --input path/to/planning_rows.json --evidence-results path/to/evidence_results.json
```

References:

- `phase36a-jd-evidence-final-scoring-feature-adapter-default-off-v1`
- `phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1`
- `phase35b-jd-signal-planning-artifact-evidence-enricher-default-off-v1`
- `phase35a-jd-signal-resume-evidence-matrix-default-off-v1`
- `phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1`
- `phase34b-jd-intelligence-planning-artifact-enricher-default-off-v1`
- `phase34a-jd-intelligence-llm-signal-extractor-default-off-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

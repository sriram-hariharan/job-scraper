# Phase 35C JD signal planning artifact evidence enrichment dry-run command default-off

Phase 35C adds the JD signal planning artifact evidence enrichment dry-run command. This is a capability step on the revised path. It is not another safety-wrapper chain.

The command performs deterministic evidence matching. It reads supplied planning artifact file input, reads supplied resume/profile evidence, calls the Phase 35B JD signal planning artifact evidence enricher, and prints evidence coverage JSON to stdout. It does not write output files.

The command supports JSON, JSONL, and CSV planning-like row inputs. It supports JSON, JSONL, CSV, TXT, and MD resume evidence inputs.

The dry-run output aggregates required skill coverage, aggregates preferred skill coverage, aggregates tool coverage, and aggregates responsibility coverage. It reports missing required skills by row, reports missing tools by row, and reports red flag findings by row.

Safety boundaries:

- It does not produce final application score.
- It does not change existing scoring logic.
- It does not run relevance prefilter.
- It does not run JD intelligence extraction.
- It does not run matching/scoring modules.
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

JD intelligence remains separate from final scoring. Evidence matching remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic.

Example command:

```bash
PYTHONPATH="$PWD" python run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py --input path/to/planning_rows.json --resume-evidence path/to/resume.txt
```

References:

- `phase35b-jd-signal-planning-artifact-evidence-enricher-default-off-v1`
- `phase35a-jd-signal-resume-evidence-matrix-default-off-v1`
- `phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1`
- `phase34b-jd-intelligence-planning-artifact-enricher-default-off-v1`
- `phase34a-jd-intelligence-llm-signal-extractor-default-off-v1`
- `phase33e-controlled-agent-router-planning-artifact-dry-run-command-readonly-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

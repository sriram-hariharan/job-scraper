# Phase 34C JD intelligence planning artifact enrichment dry-run command default-off

Phase 34C adds the JD intelligence planning artifact enrichment dry-run command. This is a capability step on the revised path. It is not another safety-wrapper chain.

The command is LLM-capable and default-off. It requires explicit `--enable-llm`, reads a supplied planning artifact file, supports JSON, JSONL, and CSV planning-like row inputs, supports supplied provider responses, calls the Phase 34B JD intelligence planning artifact enricher, and prints grouped next-step routing and JD enrichment JSON to stdout. It does not write output files.

Example command:

```bash
PYTHONPATH="$PWD" python run_jd_intelligence_planning_artifact_enrichment_dry_run.py --input path/to/planning_rows.json --enable-llm --provider-responses path/to/provider_responses.json
```

Safety boundaries:

- It does not directly import provider SDKs.
- It does not directly call network.
- It does not run relevance prefilter.
- It does not run final application scoring.
- It does not run matching/scoring.
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

JD intelligence remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic.

References:

- `phase34b-jd-intelligence-planning-artifact-enricher-default-off-v1`
- `phase34a-jd-intelligence-llm-signal-extractor-default-off-v1`
- `phase33e-controlled-agent-router-planning-artifact-dry-run-command-readonly-v1`
- `phase33d-controlled-agent-router-planning-artifact-mapper-readonly-v1`
- `phase33c-controlled-agent-router-batch-handoff-plan-readonly-v1`
- `phase33b-controlled-agent-router-workflow-state-adapter-readonly-v1`
- `phase33a-controlled-agent-router-readonly-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

It reads supplied planning artifact file inputs.

# Phase 33E controlled agent router planning artifact dry-run command read-only

Phase 33E adds the controlled agent router planning artifact dry-run command. This is a capability step on the revised path. It is not another safety-wrapper chain.

The command reads a supplied planning artifact file, supports JSON, JSONL, and CSV planning-like row inputs, calls the Phase 33D planning artifact mapper, and prints grouped next-step router handoff JSON to stdout. It does not write output files.

Example command:

```bash
PYTHONPATH="$PWD" python run_controlled_agent_router_planning_artifact_dry_run.py --input path/to/planning_rows.json
```

Safety boundaries:

- It does not run relevance prefilter.
- It does not run JD intelligence.
- It does not run final application scoring.
- It does not run tailoring opportunity check.
- It does not run manual Generate AI Tailoring preview preparation.
- It does not call LLM.
- It does not call providers.
- It does not call network.
- It does not dispatch.
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

Tailoring agent remains separate from final scoring. Final scoring remains deterministic and controlled by scoring logic. LLM calls are not introduced in this phase. Persistence is not introduced in this phase.

References:

- `phase33d-controlled-agent-router-planning-artifact-mapper-readonly-v1`
- `phase33c-controlled-agent-router-batch-handoff-plan-readonly-v1`
- `phase33b-controlled-agent-router-workflow-state-adapter-readonly-v1`
- `phase33a-controlled-agent-router-readonly-v1`
- `phase32b-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-api-readback-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

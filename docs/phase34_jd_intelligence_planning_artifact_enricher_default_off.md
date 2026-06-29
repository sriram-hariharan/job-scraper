# Phase 34B JD intelligence planning artifact enricher default-off

Phase 34B adds the JD intelligence planning artifact enricher. This is a capability step on the revised path. It is not another safety-wrapper chain.

The enricher is LLM-capable and default-off. It requires explicit `enable_llm=True`, calls the Phase 34A JD intelligence LLM signal extractor, calls the Phase 33D planning artifact mapper, and enriches planning-like rows with structured JD intelligence results.

It supports supplied provider responses and supports an injected provider callable through Phase 34A. It does not directly import provider SDKs and does not directly call network.

Safety boundaries:

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

- `phase34a-jd-intelligence-llm-signal-extractor-default-off-v1`
- `phase33e-controlled-agent-router-planning-artifact-dry-run-command-readonly-v1`
- `phase33d-controlled-agent-router-planning-artifact-mapper-readonly-v1`
- `phase33c-controlled-agent-router-batch-handoff-plan-readonly-v1`
- `phase33b-controlled-agent-router-workflow-state-adapter-readonly-v1`
- `phase33a-controlled-agent-router-readonly-v1`
- `phase23-tailoring-agent-workflow-release-v1`
- `phase20d-no-auto-apply-safety-checkpoint-v1`

It supports injected provider callable through Phase 34A.

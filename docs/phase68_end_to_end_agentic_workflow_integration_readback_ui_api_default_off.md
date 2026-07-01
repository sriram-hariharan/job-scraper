# Phase 68B — End-to-end agentic workflow integration readback UI/API, default-off

Phase 68B hardens the existing Phase 68A end-to-end agentic workflow integration readback in the existing scan and planning workspace API/UI surfaces.

The readback makes the integrated workflow visible:

1. user-started scan/evaluation
2. workflow-automatic core LLM inference where explicitly configured
3. JD signal extraction
4. skills extraction
5. requirements extraction
6. resume evidence
7. scoring/ranking readback
8. planning workspace next actions
9. human-only handoff readiness

The API readback and UI readback expose:

- `agentic_workflow_integration_enabled`
- `agentic_workflow_integration_requested`
- `agentic_workflow_integration_performed`
- `user_started_scan_or_evaluation`
- `core_llm_inference_workflow_automatic`
- JD signal extraction, skills extraction, requirements extraction, resume evidence, LLM evaluation, and scoring/ranking status fields
- planning workspace next actions
- tailoring suggestion and exact-change proposal actions as explicit next actions only
- `manual_mutation_requires_operator_action`
- `human_only_application_boundary`
- source resume unchanged/source resume overwrite flags
- no ATS automation, no application submission, and no apply queue enqueue
- validation status, fallback used, fallback reason, and fallback error class

Core LLM inference such as JD signal extraction, skills extraction, requirement extraction, and bounded LLM evaluation may run automatically inside an explicitly user-started scan/evaluation workflow. Manual mutation requires operator action, and manual mutation actions remain operator-gated.

The readback is passive. It can surface existing provider/LLM intent, configuration, fallback status, and stored readback metadata, but tests use deterministic fakes and make no live LLM call in tests.

The human-only application boundary remains visible in the API/UI readback.

Safety boundaries:

- no resume artifact creation
- no source resume overwrite
- no silent resume mutation
- no ATS automation
- no application submission
- no apply queue enqueue
- no auto-apply
- no scoring formula or scoring weight changes

Phase 68B preserves Phase 63 application-readiness packet readback, Phase 64 manual handoff packet readback, Phase 65 handoff audit trail readback, Phase 66 safety boundary summary readback, Phase 67 workflow readiness checkpoint readback, and Phase 68A focused behavior.

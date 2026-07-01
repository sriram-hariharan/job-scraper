# Phase 68A — End-to-end agentic workflow integration wiring, default-off

Phase 68A wires a real end-to-end agentic workflow integration readback into the existing app flow. It connects the user-started scan/evaluation path to existing analysis and planning readbacks:

scan/evaluation -> JD signal extraction -> skills extraction -> requirements extraction -> resume evidence -> bounded LLM evaluation where configured -> scoring/ranking readback -> planning workspace next actions -> human-only handoff readiness.

This phase does not change scoring formulas or scoring weights. Deterministic prefiltering remains separate from LLM evaluation, JD intelligence remains separate from resume evidence, final scoring/ranking remains separate from LLM evaluation, and manual mutation/handoff remains separate from analysis automation.

## Corrected LLM inference policy

Workflow-automatic core LLM inference may run inside an explicitly user-started scan/evaluation workflow. This includes bounded JD signal extraction, skills extraction, requirement extraction, and relevance/evaluation support when configured.

Manual mutation requires operator action. Tailoring suggestions and exact resume change proposals remain explicit planning workspace next actions, not silent resume mutations.

ATS automation, application submission, apply queue enqueue, source resume overwrite, and auto-apply are forbidden forever, not gated features.

## Readback behavior

The readback exposes:

- `agentic_workflow_integration_enabled`
- `agentic_workflow_integration_requested`
- `agentic_workflow_integration_performed`
- `user_started_scan_or_evaluation`
- `core_llm_inference_workflow_automatic`
- JD signal extraction availability/status
- skills extraction availability/status
- requirements extraction availability/status
- resume evidence availability/status
- LLM evaluation availability/status
- scoring/ranking availability/status
- planning workspace next actions availability
- tailoring suggestion action availability
- exact change proposal action availability
- manual mutation operator gating
- human-only application boundary
- source resume unchanged/overwritten status
- no ATS automation, no application submission, and no apply queue enqueue
- validation status and deterministic fallback metadata

## Safety boundary

Tests use deterministic local stubs with no live LLM call in tests and no live provider call in tests. The integration readback does not create resume artifacts, overwrite the source resume, mutate source resume state, automate ATS actions, submit applications, enqueue future apply/submit actions, mark jobs as applied, or add auto-apply.

Safety markers: no resume artifact creation, no source resume overwrite, no ATS automation, no application submission, no auto-apply.

Phase 68A preserves Phase 63 application-readiness packet readback, Phase 64 manual handoff packet readback, Phase 65 handoff audit trail readback, Phase 66 safety boundary summary readback, and Phase 67 workflow readiness checkpoint readback.

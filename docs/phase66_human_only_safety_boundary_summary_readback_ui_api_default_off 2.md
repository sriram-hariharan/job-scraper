# Phase 66B — Human-only safety boundary summary readback UI/API, default-off

Phase 66B hardens the Phase 66A human-only safety boundary summary readback through
the existing planning workspace API/UI surface.

This is readback hardening only. API/UI readback displays existing safety-boundary
summary data and does not create a summary packet by itself.

## Corrected LLM inference policy

The readback represents the corrected policy:

- core LLM inference may be workflow-automatic inside an explicitly user-started
  scan/evaluation workflow
- manual mutation requires operator action
- ATS automation is forbidden
- application submission is forbidden
- apply queue enqueue is forbidden
- source resume overwrite is forbidden
- auto-apply is forbidden

This readback action itself performs no live LLM call and no provider call.

## API/UI readback fields

The app can display:

- `safety_boundary_summary_enabled`
- `safety_boundary_summary_requested`
- `safety_boundary_summary_created`
- `safety_boundary_summary_id` / stable summary key
- `handoff_audit_trail_id` / stable audit key
- `manual_handoff_packet_id` / stable handoff packet key
- `application_readiness_packet_id` / stable readiness packet key
- `artifact_id` / stable artifact key
- `human_only_application_boundary`
- `core_llm_inference_workflow_automatic`
- `manual_mutation_requires_operator_action`
- `llm_capable_action_count`
- `mutation_capable_action_count`
- `forbidden_path_count`
- `ats_automation_performed`
- `application_submission_performed`
- `apply_queue_enqueued`
- `validation_status`
- `fallback_used`
- fallback reason / error class when present
- `source_resume_unchanged`
- `source_resume_overwritten`

## Safety boundaries

- default-off
- human-only safety boundary summary readback
- planning workspace action
- api readback
- ui readback
- deterministic fallback
- no live llm call from this readback action
- no provider call from this readback action
- no resume artifact creation
- no source resume overwrite
- no resume mutation
- no ats automation
- no application submission
- no apply queue enqueue
- no auto-apply
- no scoring formula changes
- no scoring weight changes

Phase 66B preserves Phase 60 artifact verification readback, Phase 61 operator review
packet readback, Phase 62 operator decision readback, Phase 63 application-readiness
packet readback, Phase 64 manual handoff packet readback, Phase 65 handoff audit
trail readback, and Phase 66A focused behavior.


## Verifier marker

- workflow-automatic core llm inference

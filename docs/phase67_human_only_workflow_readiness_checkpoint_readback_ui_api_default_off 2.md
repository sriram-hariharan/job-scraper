# Phase 67B — Human-only workflow readiness checkpoint readback UI/API, default-off

Phase 67B hardens the existing Phase 67A human-only workflow readiness checkpoint readback through the planning workspace API/UI surface. It does not create a new checkpoint by itself; checkpoint creation remains default-off and requires the explicit Phase 67A planning workspace action with a valid safety boundary summary.

The readback is for human-only workflow readiness visibility. It exposes the checkpoint state, stable keys, validation status, fallback metadata, and safety boundaries already produced by the Phase 67A wiring.

## Corrected LLM inference policy

The readback preserves the corrected llm inference policy:

- workflow-automatic core llm inference may run inside an explicitly user-started scan or evaluation workflow;
- bounded JD signal extraction, skills extraction, requirement extraction, and relevance/evaluation support may be part of that workflow;
- manual mutation requires operator action and remains operator-gated;
- ATS automation, application submission, apply queue enqueue, source resume overwrite, and auto-apply are forbidden forever;
- there is no live llm call from this readback action, and there is no provider call from this readback action.

## API/readback fields

The planning workspace readback includes:

- `workflow_readiness_checkpoint_enabled`
- `workflow_readiness_checkpoint_requested`
- `workflow_readiness_checkpoint_created`
- `workflow_readiness_checkpoint_id` / stable checkpoint key
- `safety_boundary_summary_id` / stable summary key
- `handoff_audit_trail_id` / stable audit key
- `manual_handoff_packet_id` / stable handoff packet key
- `application_readiness_packet_id` / stable readiness packet key
- `artifact_id` / stable artifact key
- `human_only_application_boundary`
- `core_llm_inference_workflow_automatic`
- `manual_mutation_requires_operator_action`
- `workflow_ready_for_human_handoff`
- `llm_capable_action_count`
- `mutation_capable_action_count`
- `forbidden_path_count`
- `ats_automation_performed`
- `application_submission_performed`
- `apply_queue_enqueued`
- `validation_status`
- `fallback_used`, fallback reason, and fallback error class
- `source_resume_unchanged`
- `source_resume_overwritten`

## UI/readback behavior

The UI readback displays existing response data only. It does not call Phase 67A helpers, does not call providers, does not call an LLM, and does not create a workflow readiness checkpoint packet by itself.

## Safety boundary

Phase 67B preserves deterministic fallback and Phase 63 through Phase 67A behavior. It performs no resume artifact creation, no source resume overwrite, no source resume mutation, no ATS automation, no application submission, no apply queue enqueue, and no auto-apply.


## Verifier marker

- api readback

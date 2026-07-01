# Phase 64B — Human-only manual application handoff packet readback UI/API, default-off

Phase 64B hardens the existing Phase 64A human-only manual application handoff
packet readback through the planning workspace API/UI surface.

This is readback hardening only. It reuses the Phase 64A manual action and does not
create a new automation path.

## Readback fields

The planning workspace readback exposes:

- `manual_handoff_packet_enabled`
- `manual_handoff_packet_requested`
- `manual_handoff_packet_created`
- `manual_handoff_packet_id` / stable packet key
- `application_readiness_packet_id` / stable readiness packet key
- `artifact_id` / stable artifact key
- `operator_decision_value`
- `human_only_application_boundary`
- `ats_automation_performed`
- `application_submission_performed`
- `apply_queue_enqueued`
- `validation_status`
- `fallback_used`
- fallback reason / error class when present
- `source_resume_unchanged`
- `source_resume_overwritten`

The UI readback is passive. It displays existing response data and does not create
manual handoff packets by itself.

## Safety boundaries

- default-off
- human-only manual application handoff packet readback
- planning workspace action
- api readback
- deterministic fallback
- no live llm call
- no provider call
- no network call
- no resume artifact creation
- no artifact creation
- no source resume overwrite
- no resume mutation
- no source resume state mutation
- no ats automation
- no application execution
- no application submission
- no apply queue enqueue
- no execution queue enqueue
- no auto-apply
- no scoring formula changes
- no scoring weight changes

Manual handoff packet creation still requires the explicit Phase 64A manual action
flag/path and a valid Phase 63 application-readiness packet. The packet is for
human-only manual application outside the app; it never automates ATS actions,
submits applications, or enqueues future apply/submit actions.

# Phase 65B — Human-only handoff audit trail readback UI/API, default-off

Phase 65B hardens the existing Phase 65A human-only handoff audit trail readback
through the planning workspace API/UI surface.

This is readback hardening only. The UI and API expose the audit trail metadata that
Phase 65A already creates when the explicit planning workspace action is enabled with
a valid manual handoff packet. They do not create audit trails by themselves.

## API readback

The planning workspace state response includes:

- `handoff_audit_trail_enabled`
- `handoff_audit_trail_requested`
- `handoff_audit_trail_created`
- `handoff_audit_trail_id` / stable audit key
- `manual_handoff_packet_id` / stable handoff packet key
- `application_readiness_packet_id` / stable readiness packet key
- `artifact_id` / stable artifact key
- `human_only_application_boundary`
- `audit_event_count`
- `ats_automation_performed`
- `application_submission_performed`
- `apply_queue_enqueued`
- `validation_status`
- `fallback_used`
- fallback reason / error class when present
- `source_resume_unchanged`
- `source_resume_overwritten`

## UI readback

The planning workspace UI readback displays the existing response data only. It shows
the human-only boundary, audit key, handoff key, readiness key, artifact key, fallback
state, validation state, audit event count, ATS automation status, application
submission status, apply queue status, and source-resume status.

## Safety boundaries

- default-off
- human-only handoff audit trail readback
- planning workspace action
- api readback
- ui readback
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

Phase 65B preserves the Phase 60 artifact verification readback, Phase 61 operator
review packet readback, Phase 62 operator decision readback, Phase 63
application-readiness packet readback, Phase 64 manual handoff packet readback, and
Phase 65A focused behavior.

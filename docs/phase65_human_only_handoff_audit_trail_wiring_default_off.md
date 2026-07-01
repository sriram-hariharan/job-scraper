# Phase 65A — Human-only handoff audit trail wiring, default-off

Phase 65A wires a planning workspace action that creates a human-only handoff audit
trail from an existing Phase 64 human-only manual application handoff packet.

The audit trail records the safety chain from proposal through manual handoff. It is an
audit/readback packet only and is not an application automation path.

## Requirements

The action is default-off and requires:

- an explicit manual action flag/path
- `manual_handoff_packet_id` / stable handoff packet key
- `application_readiness_packet_id` / stable readiness packet key when supplied
- `artifact_id` / stable artifact key when supplied

## Output

The readback includes:

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

## Safety boundaries

- default-off
- human-only handoff audit trail
- planning workspace action
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

Phase 65A preserves the Phase 60 artifact verification readback, Phase 61 operator
review packet readback, Phase 62 operator decision readback, Phase 63
application-readiness packet readback, and Phase 64 manual handoff packet readback.
It does not mark any job as applied because no automation submits anything.

# Phase 64A — Human-only manual application handoff packet wiring, default-off

Phase 64A wires a planning workspace action that creates a human-only manual
application handoff packet from an existing Phase 63 operator-approved artifact
application-readiness packet.

The packet is a final checklist/readback for the human user to apply manually outside
the app. It is not an application automation path.

## Requirements

The action is default-off and requires:

- an explicit manual action flag/path
- `application_readiness_packet_id` / stable readiness packet key
- `artifact_id` / stable artifact key when supplied
- accepted operator decision status from the readiness packet

## Output

The readback includes:

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

## Safety boundaries

- default-off
- human-only manual application handoff packet
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

Phase 64A preserves the Phase 60 artifact verification readback, Phase 61 operator
review packet readback, Phase 62 operator decision readback, and Phase 63
application-readiness packet readback. It does not mark any job as applied because no
automation submits anything.

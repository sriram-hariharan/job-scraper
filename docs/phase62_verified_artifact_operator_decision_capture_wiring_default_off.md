# Phase 62A — Verified artifact operator decision capture wiring, default-off

Phase 62A wires a planning workspace action for verified artifact operator decision capture.
It consumes the existing Phase 61 verified-artifact operator review packet readback and
returns a deterministic operator decision packet/readback only.

The action is default-off. Without the explicit planning workspace action flag, no operator
decision is captured and existing workspace behavior is unchanged.

## Required input

- Explicit manual planning workspace action enablement.
- Existing `operator_review_packet_id` or stable packet key from Phase 61.
- Existing `artifact_id` or stable artifact key associated with the review packet.
- Operator decision value: `accepted`, `rejected`, or `needs_changes`.

## Output

The response includes:

- `operator_decision_enabled`
- `operator_decision_requested`
- `operator_decision_captured`
- `operator_decision_value`
- `operator_decision_id` / stable decision key
- `operator_review_packet_id` / stable packet key
- `artifact_id` / stable artifact key
- `artifact_verification_passed`
- `validation_status`
- `fallback_used`
- fallback reason / error class when applicable
- `source_resume_unchanged`
- `source_resume_overwritten`

The packet is a decision packet/readback only. It does not apply the decision to a resume.

## Safety boundaries

- default-off
- verified artifact operator decision capture
- planning workspace action
- deterministic fallback
- no live llm call
- no provider call
- no network call
- no artifact creation
- no source resume overwrite
- no resume mutation
- no source resume state mutation
- no application execution
- no application submission
- no auto-apply
- no scoring formula changes
- no scoring weight changes

Invalid or missing packet IDs, artifact IDs, unverified artifacts, missing decision values, or
unsupported decision values return structured fallback readback instead of capturing a decision.

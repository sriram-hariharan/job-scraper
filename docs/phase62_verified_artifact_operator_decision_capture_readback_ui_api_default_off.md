# Phase 62B — Verified artifact operator decision capture readback UI/API, default-off

Phase 62B hardens the app-facing readback for verified artifact operator decision capture.
It reuses the Phase 62A planning workspace action and exposes the decision capture state
through the existing saved-scan API and passive scan workspace readback UI.

The behavior remains default-off. API and UI readback do not capture an operator decision by
themselves. Decision capture still requires the explicit Phase 62A manual action flag/path,
a valid operator review packet ID, the matching verified artifact ID, and a supported decision
value.

## Readback fields

The hardened readback includes:

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
- fallback reason / error class when present
- `source_resume_unchanged`
- `source_resume_overwritten`
- `readback_phase=62B`
- `phase62b_readback_hardened`

## Safety boundaries

- default-off
- verified artifact operator decision capture readback
- planning workspace action
- api readback
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

Fallback readback is returned for missing or invalid review packet IDs, missing or mismatched
artifact IDs, unverified artifact metadata, missing decision values, and unsupported decision
values.

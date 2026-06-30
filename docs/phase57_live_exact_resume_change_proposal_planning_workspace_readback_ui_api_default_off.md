# Phase 57B live exact resume change proposal planning workspace readback UI/API default-off

Phase 57B hardens the Phase 57A live exact resume change proposal readback for the existing planning workspace API and UI surface.

It remains default-off. The planning workspace action must explicitly request live exact resume change proposal generation before any provider call can be attempted through the Phase57A path.

Readback fields include:

- `exact_change_llm_enabled`
- `exact_change_llm_call_attempted`
- `exact_change_llm_call_performed`
- `fallback_used`
- `validation_status`
- provider/model/prompt version when present
- token/cost/latency when present
- proposed change count
- proposed change IDs or stable proposed-change keys when present
- fallback reason and fallback error class when present

The API readback preserves Phase55 live JD LLM planning scan readback and Phase56 live tailoring suggestion readback. The UI readback is passive: it displays existing response data and does not trigger live LLM or provider calls by itself.

Deterministic fallback remains required for invalid provider responses, provider exceptions, missing scan context, validation failure, or normalization failure.

Safety boundaries:

- no resume mutation
- no resume overwrite
- no resume artifact creation
- no suggestion application
- no proposal approval
- no approved-change plan creation
- no application execution
- no application submission
- no auto-apply
- no auto-submit
- no scoring formula changes
- no scoring weight changes

## Phase 57B required markers

- default-off
- live exact resume change proposal readback
- planning workspace action
- api readback
- deterministic fallback
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply


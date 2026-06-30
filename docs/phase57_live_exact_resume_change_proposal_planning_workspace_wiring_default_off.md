# Phase 57A live exact resume change proposal planning workspace wiring default-off

Phase 57A wires live exact resume change proposal generation into the real planning workspace action path. It is default-off and only runs when the planning workspace request explicitly sets the live exact change proposal enable flag.

This is live exact resume change proposal wiring for the planning workspace action. It reuses the existing controlled exact resume change-set chain:

1. Phase42 proposal builder
2. Phase43 request packet
3. Phase49 runtime adapter
4. Phase45 validation
5. Phase46 normalization

The planning workspace readback exposes metadata only: `exact_change_llm_enabled`, `exact_change_llm_call_attempted`, `exact_change_llm_call_performed`, `fallback_used`, `validation_status`, provider/model/prompt version when present, token/cost/latency when present, proposed change count, and proposed change identifiers.

When disabled, the action does not read the saved scan for exact-change context and does not call the provider. When enabled, provider failure, invalid provider response, missing scan context, or normalization failure uses deterministic fallback and surfaces fallback metadata safely.

Safety boundaries:

- no resume mutation
- no resume overwrite
- no resume artifact creation
- no suggestion application
- no approved-change plan
- no proposal approval
- no application execution
- no application submission
- no auto-apply
- no auto-submit
- does not change scoring formulas
- does not change scoring weights
- final scoring remains deterministic

Phase57A preserves Phase55 live JD LLM planning scan readback and Phase56 live tailoring suggestion planning workspace readback. UI readback is passive: it displays response metadata and does not trigger provider calls by itself.

## Phase 57A required markers

- default-off
- live exact resume change proposal wiring
- planning workspace action
- deterministic fallback
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply


# Phase 56A — live tailoring suggestion planning workspace wiring, default-off

Phase 56A wires the existing live tailoring suggestion capability into the real planning workspace action path.

The wiring is default-off. The saved-scan workspace action does not call the live tailoring LLM unless the request explicitly includes `enable_live_tailoring_suggestion=true`.

## Integration point

- Existing action: `POST /planning/saved-scan/{scan_id}/state`
- Existing helper reused: `build_manual_tailoring_suggestion_dry_run_payload`
- New response/readback key: `live_tailoring_suggestion_readback`

The readback includes `tailoring_llm_enabled`, `tailoring_llm_call_attempted`, `tailoring_llm_call_performed`, `fallback_used`, `validation_status`, provider/model/prompt metadata when present, token/cost/latency metadata when present, suggestion counts, and suggestion identifiers.

## Safety boundaries

- Default-off behavior is unchanged.
- Provider failures, invalid JSON, or missing scan context use deterministic fallback.
- The phase does not mutate resumes.
- The phase does not overwrite resumes.
- The phase does not create resume artifacts.
- The phase does not apply suggestions.
- The phase does not create approved-change plans.
- The phase does not call exact resume change-set refinement.
- The phase does not execute applications.
- The phase does not submit applications.
- The phase does not add automatic application behavior.
- The phase does not change final scoring formulas or scoring weights.

Phase 55 JD LLM extraction readback remains separate and intact.

## Phase 56A required markers

- default-off
- live tailoring suggestion wiring
- planning workspace action
- deterministic fallback
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply


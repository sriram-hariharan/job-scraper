# Phase 56B — live tailoring suggestion planning workspace readback UI/API, default-off

Phase 56B hardens the app-facing readback for the Phase 56A live tailoring suggestion planning workspace action.

The integration remains default-off. The API/UI readback does not call the live tailoring LLM by itself. A live tailoring suggestion call still requires the explicit Phase 56A action flag: `enable_live_tailoring_suggestion=true`.

## Readback surface

- Existing action: `POST /planning/saved-scan/{scan_id}/state`
- Existing response key: `live_tailoring_suggestion_readback`
- API readback: enabled
- UI readback: enabled through the existing scan workspace metadata display

The readback includes:

- `tailoring_llm_enabled`
- `tailoring_llm_call_attempted`
- `tailoring_llm_call_performed`
- `fallback_used`
- `validation_status`
- provider/model/prompt version metadata when present
- token/cost/latency metadata when present
- suggestion count
- suggestion IDs / stable suggestion keys
- fallback reason and fallback error class when present

## Safety boundaries

- Default-off behavior is unchanged.
- Deterministic fallback is preserved for disabled, invalid provider output, provider exceptions, or missing scan context.
- Phase 55 JD LLM planning scan readback remains separate and intact.
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

## Phase 56B required markers

- default-off
- live tailoring suggestion readback
- planning workspace action
- api readback
- ui readback
- deterministic fallback
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply

# Phase 55A — live JD LLM extraction planning scan wiring, default-off

Phase 55A wires the existing JD LLM extraction capability into the real planning/start-scan service path.

The wiring is default-off. `/planning/start-scan` keeps live JD LLM extraction disabled unless the request explicitly includes `enable_jd_llm_extraction=true`.

## Planning scan path

The integration point is the real saved-scan creation flow in `src/app/services.py`. The scan review is still built from the deterministic scan path, and then JD LLM extraction metadata is attached under `jd_llm_extraction`.

When enabled, the service reuses the existing Phase 34B planning artifact enricher and Phase 34A JD LLM signal extractor. The provider callable is the existing live JD intelligence provider adapter already used by the manual JD intelligence dry-run surface.

## Deterministic fallback

When disabled, when the provider is unavailable, when provider JSON is invalid, or when validation fails, the scan payload falls back safely and keeps deterministic scan output present.

Run-level observability includes `llm_enabled`, `llm_call_attempted`, `llm_call_performed`, provider/model/prompt metadata when available, token/cost/latency when available, `fallback_used`, and `validation_status`.

## Safety boundary

Phase 55A does not mutate resumes, does not overwrite resumes, does not create resume artifacts, does not execute applications, does not submit applications, and does not add automatic application behavior.

The LLM does not determine final score or scoring weights. Existing deterministic scoring remains the source of the scan score.

## Phase 55A required markers

- default-off
- live jd llm wiring
- planning scan path
- deterministic fallback
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply


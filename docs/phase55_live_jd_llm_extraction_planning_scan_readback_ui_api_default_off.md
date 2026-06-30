# Phase 55B — live JD LLM planning-scan readback, default-off

Phase 55B exposes the Phase 55A live JD LLM extraction metadata through the existing planning scan API/readback and scan workspace UI surface.

The integration remains default-off. The app does not call the live JD LLM unless the explicit Phase 55A planning/start-scan enable flag is present on the scan request.

## Readback surface

- `POST /planning/start-scan` returns `jd_llm_extraction_readback` at the response top level and inside `scan_review_payload`.
- `GET /planning/saved-scan/{scan_id}` returns the same readback shape for stored scan reports.
- The scan workspace UI renders the existing metadata only; it does not trigger provider calls.

The readback includes:

- live JD LLM enabled flag
- call attempted
- call performed
- fallback used
- validation status and validation errors
- provider, model, and prompt version when present
- token usage, cost, and latency when present
- extracted structured JD signals metadata when present

## Safety boundaries

Readback is metadata-only. It does not mutate resumes, overwrite resumes, does not create resume artifacts, does not execute applications, does not submit applications, does not add automatic application behavior, does not change final scoring formulas, and does not change scoring weights.

Provider invalid JSON and provider exceptions remain deterministic fallback states. The LLM does not determine the final score or scoring weights.

## Phase 55B required markers

- default-off
- live jd llm readback
- planning scan path
- api readback
- deterministic fallback
- no resume mutation
- no artifact creation
- no application execution
- no auto-apply


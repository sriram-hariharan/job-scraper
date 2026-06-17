# Phase 5W Shadow Sidecar Trace Readback UI Readiness Audit

This checkpoint is documentation/test only.

No UI code was added in this phase.

No API/service behavior changed.

No runtime behavior change is introduced.

No production pipeline behavior is changed.

No storage schema is changed.

Default-off pipeline hook call site exists: 1.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

## Exact Inspected Files

Repository files inspected for this trace readback UI readiness audit:

- `src/app/static/agentic_review.js`
- `src/app/static/app_redesign.css`
- `src/app/api.py`
- `src/app/services.py`
- `docs/phase5_shadow_sidecar_trace_readback_readiness_audit.md`
- `tests/test_shadow_sidecar_trace_readback_api_default_off_no_ui.py`
- `tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py`
- `tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py`
- `tests/test_agent_trace_ui_contract.py`
- `tests/test_agentic_review_ui_compaction_polish_no_backend_change.py`
- `tests/test_agentic_review_ui_portfolio_polish_no_backend_change.py`
- `tests/test_portfolio_demo_readiness_wrap_checkpoint.py`

Protected UI/static, API, service, storage, and pipeline files were inspected only. They were not modified for this audit.

## Existing UI Trace/Review Files

Existing UI trace/review files discovered from the repo:

- `src/app/static/agentic_review.js`
- `src/app/static/app_redesign.css`
- `tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py`
- `tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py`
- `tests/test_agent_trace_ui_contract.py`
- `tests/test_agentic_review_ui_compaction_polish_no_backend_change.py`
- `tests/test_agentic_review_ui_portfolio_polish_no_backend_change.py`

`src/app/static/agentic_review.js` already contains the read-only Agent Trace panel and manual review controls:

- `renderAgentTraceReadOnlyPanel`
- `renderAgentTraceEvidencePackSection`
- `renderAgentTraceDetailedSections`
- `renderAgentTraceReadOnlyDetails`
- `fetchAgentTraceReadOnlyPayload`
- `fetchReadOnlyAgentTrace`

The existing panel already renders read-only trace summary, trace evidence pack, stage trace bundle, stage trace health, stage trace readiness, safety metadata, empty trace states, not-found states, fetch failure states, and collapsed debug details.

## Existing API/Service Readback Files

Existing API/service readback files available for future UI use:

- `src/app/api.py`
- `src/app/services.py`
- `src/agents/shadow_sidecar_trace_readback.py`

The available default-off readback route is:

- `POST /api/shadow-sidecar/trace-readback`

The available service helper is:

- `shadow_sidecar_trace_readback_service_payload`

The isolated helper is:

- `build_shadow_sidecar_trace_readback_payload`

Future UI should call the API only from an explicit user-opened readback panel or button. It should not auto-refresh in a way that calls providers or changes deterministic pipeline behavior.

## Recommended Future UI Insertion Point

Recommended future UI insertion point:

- Add a compact read-only section inside the existing `renderAgentTraceReadOnlyPanel` in `src/app/static/agentic_review.js`, near `renderAgentTraceEvidencePackSection(tracePayload?.trace_evidence_pack)` and before lower-level debug details.

This keeps shadow sidecar trace readback inside the existing Agent Trace / review UI surface instead of inventing a new dashboard architecture.

The future section should reuse existing UI conventions:

- `agent-trace-summary`
- `agentic-feedback-action`
- `agentic-review-muted`
- `renderWorkflowSummaryMetric`
- `renderAgentTraceReadOnlyDetails`
- `escapeHtml`

## Required Feature Flag

Required future readback feature flag:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED`

The readback flag remains default-off.

The global sidecar flag remains default-off.

The trace persistence flag remains default-off.

The kill switch disables trace capture/persistence/readback/UI readback.

## Required UI Constraints

Any future UI implementation must preserve all of these constraints:

- Read-only display.
- No auto-refresh that calls providers.
- No mutation buttons.
- No scoring override.
- No ranking override.
- No scoring/ranking override.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.
- No application execution/submission.
- Safe empty/not-enabled state.
- Safe blocked-by-kill-switch state.
- Safe no-trace/no-source state.
- Safe invalid-context state.
- Safe failed-non-blocking state.
- Stage-level logging must be preserved.
- Existing metrics flow must be preserved.
- Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.

## Proposed Next Implementation Sequence

1. Add UI-only readback panel behind existing trace/review surface.
2. Fetch default-off readback API only when user opens the panel.
3. Render status, source context, safety metadata, and no-mutation summary.
4. Add UI tests.
5. Only later add richer dashboard.
6. Only later allow human-approved influence.
7. Only much later guarded automation.

## Explicit Non-Goals

- No UI code in this phase.
- No API/service code in this phase.
- No runtime behavior change.
- No automated decisions.
- No mutation.
- No scoring mutation.
- No ranking mutation.
- No queue mutation.
- No approval mutation.
- No resume mutation.
- No execution request mutation.
- No execution launch request mutation.
- No application execution.
- No application submission.
- No application execution/submission.

## Audit Decision

Phase 5W is a UI readiness audit only.

Future shadow sidecar trace readback UI should reuse the existing Agent Trace panel in `src/app/static/agentic_review.js`.

Future UI should use the existing default-off API readback route and service helper only after an explicit user action.

No UI/dashboard was added.

No API/service behavior changed.

No runtime behavior changed.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

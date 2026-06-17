# Phase 6D Shadow Score Comparison UI Readiness Audit

This checkpoint is documentation/test only.

No UI code was added in this phase.

No API/service behavior changed in this phase.

No runtime behavior changed in this phase.

No production pipeline behavior changed in this phase.

No provider calls were added.

No storage schema was changed.

No scoring, ranking, queue, approval, resume, execution request, execution launch request, application execution, or application submission mutation was added.

Default-off pipeline hook call site exists: 1.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

## Exact Inspected Files

Repository files inspected for this UI readiness audit:

- `src/app/static/agentic_review.js`
- `src/app/static/app_redesign.css`
- `src/app/api.py`
- `src/app/services.py`
- `src/agents/shadow_sidecar_score_comparison.py`
- `tests/test_shadow_sidecar_score_comparison_api_default_off_no_ui.py`
- `tests/test_shadow_sidecar_score_comparison_service_helper_no_api_ui.py`
- `tests/test_portfolio_demo_readiness_wrap_checkpoint.py`

Protected pipeline runtime, API route, service, UI/static, scoring, ranking, queue, approval, execution, and storage schema files were inspected only. They were not modified for this audit.

## Existing UI Trace And Review Files

Existing UI trace/review files discovered from the repo:

- `src/app/static/agentic_review.js`
- `src/app/static/app_redesign.css`

Existing Agent Trace / review UI patterns discovered:

- `renderAgentTraceReadOnlyPanel`
- `renderAgentTraceReadOnlyDetails`
- `renderAgentTraceEvidencePackSection`
- `renderAgentTraceDetailedSections`
- `renderShadowSidecarTraceReadbackSection`
- `fetchAgentTraceReadOnlyPayload`
- Manual read-only button/status patterns near the Agent Trace panel.

The recommended future UI insertion point is inside the existing Agent Trace panel, near the manual shadow sidecar trace readback section, using the existing read-only detail renderer and manual action/status pattern.

## Existing API And Service Comparison Files

Existing API/service comparison files available for future UI use:

- `src/agents/shadow_sidecar_score_comparison.py`
- `src/app/services.py`
- `src/app/api.py`
- `tests/test_shadow_sidecar_score_comparison_readonly.py`
- `tests/test_shadow_sidecar_score_comparison_service_helper_no_api_ui.py`
- `tests/test_shadow_sidecar_score_comparison_api_default_off_no_ui.py`

Existing default-off API route available for future UI use:

- `POST /api/shadow-sidecar/score-comparison`

Existing read-only service helper available for future UI use:

- `shadow_sidecar_score_comparison_service_payload`

## Required Flags And States

Required default-off comparison flag:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_SCORE_COMPARISON_ENABLED`

Required kill switch:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH`

Future UI must render safe states for:

- safe empty/not-enabled state
- safe blocked-by-kill-switch state
- safe missing deterministic context state
- safe missing shadow snapshot state
- safe comparison failure state

The future UI must never auto-refresh in a way that calls providers. The comparison API is default-off and should be called only when an operator opens or explicitly requests the comparison panel.

## Required UI Constraints

Future UI constraints:

- read-only display
- operator-review only
- no auto-refresh that calls providers
- no mutation buttons
- no scoring override
- no ranking override
- no queue mutation
- no approval mutation
- no resume mutation
- no execution request mutation
- no execution launch request mutation
- no application execution/submission
- safe empty/not-enabled state
- safe blocked-by-kill-switch state
- safe missing deterministic context state
- safe missing shadow snapshot state
- no application execution
- no application submission

The future UI should display only advisory comparison output:

- deterministic score
- deterministic decision
- shadow snapshot status
- agreement level
- comparison findings
- no-mutation safety summary

The shadow comparison must not influence deterministic scoring, ranking, queue ordering, approval state, resume content, execution request creation, execution launch request creation, application execution, or application submission.

## Preserve Existing Operational Flow

Existing stage-level logging and metrics flow must be preserved.

Existing retry, rate-limit, cache, deduplication, and ATS health checks must not be removed.

Existing deterministic pipeline outputs must remain the source of truth.

Existing shadow comparison output must remain advisory and operator-review only.

## Separation Of Concerns

Required separation:

- prefilter relevance stays separate from shadow score comparison
- LLM evaluation stays separate from shadow score comparison
- final application scoring stays separate from shadow score comparison
- shadow comparison stays separate from deterministic final application scoring
- shadow comparison does not override scoring or ranking

## Proposed Next Implementation Sequence

1. add UI-only comparison panel behind existing trace/review surface
2. fetch default-off comparison API only when user opens the panel
3. render deterministic score/decision, shadow snapshot status, agreement level, findings, and no-mutation summary
4. add UI tests
5. only later add human-reviewed influence preview
6. only later add approval-gated influence
7. only much later guarded automation

## Explicit Non-Goals

- no UI code in this phase
- no API/service code in this phase
- no runtime behavior change
- no automated decisions
- no mutation
- no scoring mutation
- no ranking mutation
- no queue mutation
- no approval mutation
- no resume mutation
- no execution request mutation
- no execution launch request mutation
- no application execution/submission
- no application execution
- no application submission

## Audit Decision

Phase 6D is a UI readiness audit only.

The existing Agent Trace panel is the recommended future insertion point for a read-only shadow score comparison display.

The existing default-off API and service helper are sufficient for a future UI-only panel.

No UI code was added in this phase.

No API/service behavior changed in this phase.

No runtime behavior changed in this phase.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

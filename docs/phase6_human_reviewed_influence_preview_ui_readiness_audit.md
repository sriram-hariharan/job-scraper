# Phase 6J Human-reviewed Influence Preview UI Readiness Audit

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
- `src/agents/human_reviewed_influence_preview.py`
- `docs/phase6_human_reviewed_influence_preview_readiness_audit.md`
- `tests/test_human_reviewed_influence_preview_api_default_off_no_ui.py`
- `tests/test_human_reviewed_influence_preview_service_helper_no_api_ui.py`
- `tests/test_human_reviewed_influence_preview_readonly.py`
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
- `renderShadowSidecarScoreComparisonSection`
- `fetchAgentTraceReadOnlyPayload`
- Manual read-only button/status patterns near the Agent Trace panel.

The recommended future UI insertion point is inside the existing Agent Trace panel, near the manual shadow sidecar score comparison section, using the existing read-only detail renderer and manual action/status pattern.

## Existing API And Service Influence Preview Files

Existing API/service influence preview files available for future UI use:

- `src/agents/human_reviewed_influence_preview.py`
- `src/app/services.py`
- `src/app/api.py`
- `tests/test_human_reviewed_influence_preview_readonly.py`
- `tests/test_human_reviewed_influence_preview_service_helper_no_api_ui.py`
- `tests/test_human_reviewed_influence_preview_api_default_off_no_ui.py`

Existing default-off API route available for future UI use:

- `POST /api/human-reviewed-influence-preview`

Existing read-only service helper available for future UI use:

- `human_reviewed_influence_preview_service_payload`

## Required Flags And States

Required default-off influence preview flag:

- `APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_PREVIEW_ENABLED`

Required kill switch:

- `APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH`

Future UI must render safe states for:

- safe empty/not-enabled state
- safe blocked-by-kill-switch state
- safe missing deterministic context state
- safe missing shadow comparison state
- safe preview failure state

The future UI must never auto-refresh in a way that calls providers. The influence preview API is default-off and should be called only when an operator opens or explicitly requests the preview panel.

## Required UI Constraints

Future UI constraints:

- read-only display
- advisory only
- human-review required
- approval-gate required before any later influence
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
- safe missing shadow comparison state
- no application execution
- no application submission

The future UI should display only advisory influence preview output:

- deterministic score context
- shadow comparison context
- proposed influence summary
- proposed score adjustment preview
- proposed ranking effect preview
- human-review requirement
- approval-gate requirement
- no-mutation summary

The human-reviewed influence preview must not influence deterministic scoring, ranking, queue ordering, approval state, resume content, execution request creation, execution launch request creation, application execution, or application submission.

## Preserve Existing Operational Flow

Existing stage-level logging and metrics flow must be preserved.

Existing retry, rate-limit, cache, deduplication, and ATS health checks must not be removed.

Existing deterministic pipeline outputs must remain the source of truth.

Existing shadow score comparison output must remain advisory and operator-review only.

Existing human-reviewed influence preview output must remain advisory only and must require human review plus an approval gate before any later influence.

## Separation Of Concerns

Required separation:

- prefilter relevance stays separate from human-reviewed influence preview
- LLM evaluation stays separate from human-reviewed influence preview
- final application scoring stays separate from human-reviewed influence preview
- shadow score comparison stays separate from human-reviewed influence preview
- influence preview stays separate from deterministic final application scoring
- influence preview does not override scoring or ranking

## Proposed Next Implementation Sequence

1. add UI-only influence preview panel behind existing trace/review surface
2. fetch default-off influence preview API only when user opens the panel
3. render deterministic score context, shadow comparison context, proposed influence summary, score adjustment preview, ranking effect preview, human-review requirement, approval-gate requirement, and no-mutation summary
4. add UI tests
5. only later add approval-gated influence request
6. only later allow approved influence to affect downstream ranking/scoring
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

Phase 6J is a UI readiness audit only.

The existing Agent Trace panel is the recommended future insertion point for a read-only human-reviewed influence preview display.

The existing default-off API and service helper are sufficient for a future UI-only panel.

No UI code was added in this phase.

No API/service behavior changed in this phase.

No runtime behavior changed in this phase.

Live provider-backed automated agents remain zero.

Mutation-authorized agents remain zero.

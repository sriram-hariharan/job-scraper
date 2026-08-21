from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
PREFERENCES_JS_PATH = ROOT / "src/app/static/preferences_workflow.js"
PREFERENCES_CSS_PATH = ROOT / "src/app/static/preferences.css"

EXPECTED_DIAGNOSTIC_RENDERERS = (
    "renderEvidenceChainReadbackCard",
    "renderAgentTraceEvidencePackSection",
    "renderShadowSidecarTraceReadbackSection",
    "renderShadowSidecarScoreComparisonSection",
    "renderHumanReviewedInfluencePreviewSection",
    "renderHumanReviewedInfluenceApprovalRequestSection",
    "renderAgentRecommendationOverlaySection",
    "renderPipelineGeneratedAgentRecommendationOverlayReadbackSection",
    "renderPipelineGeneratedAgentRecommendationOverlayReadinessSummarySection",
    "renderPipelineGeneratedOverlayReviewPacketSection",
    "renderVectorEvidenceSection",
    "renderPgvectorExtensionProbeSection",
    "renderVectorEvidenceReadbackSection",
    "renderThreeAgentLlmopsObservabilitySection",
    "renderProviderRuntimeReadbackSection",
    "renderJdProviderRuntimeReadbackSection",
    "renderJdLiveProviderCanaryReadbackSection",
    "renderThreeCoreShadowOperatorCanaryReadbackSection",
    "renderThreeCoreApprovalPreviewServiceReadbackSection",
    "renderThreeCoreApprovalPreviewOperatorDecisionPreviewSection",
    "renderOperatorDecisionCaptureReadbackSection",
    "renderProviderCallReadinessReadbackSection",
    "renderManualReviewReadinessReadbackSection",
    "renderCoreAgentEvidenceMaterializationReadbackSection",
    "renderTailoringAgentOpportunityReadbackSection",
    "renderGenerateAiTailoringActionBoundaryReadbackSection",
    "renderManualGenerateAiTailoringPreviewReadbackSection",
    "renderManualGenerateAiTailoringPreviewRequestPacketReadbackSection",
    "renderManualGenerateAiTailoringPreviewDispatchBoundaryReadbackSection",
    "renderManualGenerateAiTailoringPreviewProviderRequestEnvelopeReadbackSection",
    "renderManualGenerateAiTailoringPreviewProviderCallBoundaryReadbackSection",
    "renderManualGenerateAiTailoringPreviewProviderCallDryRunPacketReadbackSection",
    "renderManualGenerateAiTailoringPreviewProviderResponseValidationReadbackSection",
    "renderManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackSection",
    "renderAgentTraceCriticEvaluatorSection",
    "renderManualJdIntelligenceDryRunSection",
    "renderManualResumeMatchDryRunSection",
    "renderManualTailoringSuggestionDryRunSection",
    "renderManualCriticGuardrailDryRunSection",
    "renderManualStrategyRecommendationDryRunSection",
    "renderManualShadowAgenticWorkflowChainDryRunSection",
    "renderManualShadowRecommendationHandoffDryRunSection",
    "renderManualHumanDecisionCaptureDryRunSection",
    "renderManualHumanApprovedActionPlanDryRunSection",
    "renderManualReviewPacketPreviewDryRunSection",
    "renderManualApprovalRequestPreviewDryRunSection",
    "renderManualApprovalCreationGateDryRunSection",
    "renderManualGuardedApprovalRequestCreateSection",
    "renderManualGuardedApprovalCreationObservabilitySection",
    "renderManualApprovalRequestReadbackSection",
    "renderManualApprovalStatusTransitionPreviewSection",
    "renderManualGuardedApprovalStatusTransitionSection",
    "renderManualApprovalStatusTransitionObservabilitySection",
    "renderManualQueueHandoffReadinessPreviewSection",
    "renderManualGuardedQueueHandoffCreateSection",
    "renderManualQueueHandoffCreationObservabilitySection",
    "renderManualExecutionReadinessPreviewSection",
    "renderManualExecutionLaunchGatePreviewSection",
    "renderManualExecutionLaunchGateObservabilitySection",
    "renderManualExecutionRequestPacketPreviewSection",
    "renderManualGuardedExecutionRequestCreateSection",
    "renderManualGuardedExecutionRequestObservabilitySection",
    "renderManualExecutionRequestReadbackSection",
    "renderManualExecutionRequestStatusTransitionPreviewSection",
    "renderManualGuardedExecutionRequestStatusTransitionSection",
    "renderManualGuardedExecutionRequestStatusTransitionObservabilitySection",
    "renderManualApplicationExecutionSimulationPreviewSection",
    "renderManualApplicationExecutionSimulationObservabilitySection",
    "renderManualApplicationExecutionPreflightChecklistSection",
    "renderManualApplicationExecutionPreflightObservabilitySection",
    "renderManualGuardedApplicationExecutionLaunchRequestCreateSection",
    "renderManualGuardedApplicationExecutionLaunchRequestObservabilitySection",
    "renderManualApplicationExecutionLaunchRequestReadbackSection",
    "renderManualExecutionLaunchRequestStatusTransitionPreviewSection",
    "renderManualGuardedExecutionLaunchRequestStatusTransitionSection",
    "renderManualGuardedExecutionLaunchRequestStatusTransitionObservabilitySection",
    "renderAgentTraceDetailedSections",
)


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _diagnostic_helpers() -> str:
    source = _source()
    start = source.index("function agentTraceDiagnosticText")
    end = source.index("function renderAgentTraceReadOnlyState", start)
    return source[start:end]


def _diagnostic_registry() -> str:
    source = _source()
    start = source.index("const diagnosticItems = buildAgentTraceDiagnosticItems([")
    end = source.index("  ]);", start)
    return source[start:end]


def _run_node(assertions: str) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the focused diagnostic interaction test")
    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(REVIEW_JS_PATH))}, "utf8");
const diagnosticButtons = [];
const listeners = {{}};
const elements = {{ agenticReviewDiagnosticDetail: {{ innerHTML: "" }} }};
function classListFor() {{
  const values = new Set();
  return {{
    toggle(name, force) {{ force ? values.add(name) : values.delete(name); }},
    contains(name) {{ return values.has(name); }},
  }};
}}
const document = {{
  getElementById(id) {{ return elements[id] || null; }},
  querySelector() {{ return null; }},
  querySelectorAll(selector) {{
    return selector === "[data-agent-trace-diagnostic-key]" ? diagnosticButtons : [];
  }},
  addEventListener(type, handler) {{ listeners[type] = handler; }},
}};
let fetchCalls = 0;
let manualActionCalls = 0;
const window = {{ addEventListener() {{}}, fetch() {{ fetchCalls += 1; }} }};
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
const qs = (id) => document.getElementById(id);
const renderWorkflowSummaryMetric = (label, value) => `
  <div class="agentic-workflow-metric"><span>${{escapeHtml(label)}}</span><strong>${{escapeHtml(value)}}</strong></div>
`;
const context = {{ window, document, console, Map, Set, Object, Array, String, Boolean, Number, Error, JSON, escapeHtml, qs, renderWorkflowSummaryMetric }};
vm.createContext(context);
vm.runInContext(source, context);
const hooks = vm.runInContext(`({{
  buildAgentTraceDiagnosticItems,
  syncAgentTraceDiagnosticSelection,
  renderAgentTraceDiagnosticMasterItems,
  renderAgentTraceDiagnosticDetail,
  renderAgentTraceDiagnosticWorkspace,
  selectAgentTraceDiagnostic,
  bindAgentTraceDiagnosticMasterDetail,
  renderAgentTraceEvidencePackSection,
}})`, context);
{assertions}
"""
    completed = subprocess.run(
        [node, "-e", script],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_preferences_reference_and_complete_ordered_diagnostic_inventory_are_preserved():
    preferences_js = PREFERENCES_JS_PATH.read_text(encoding="utf-8")
    preferences_css = PREFERENCES_CSS_PATH.read_text(encoding="utf-8")
    registry = _diagnostic_registry()

    assert "function showStep" in preferences_js
    assert "data-preferences-step-target" in preferences_js
    assert ".preferences-workflow .preferences-step-navigation" in preferences_css
    assert ".preferences-workflow .preferences-editor-shell" in preferences_css

    observed = tuple(re.findall(r"\b(render[A-Za-z0-9_]+)\(", registry))
    assert observed == EXPECTED_DIAGNOSTIC_RENDERERS
    assert len(observed) == 77
    assert registry.index('"Evidence Chain"') < registry.index('"Trace Evidence Pack"')
    assert registry.index('"Trace Evidence Pack"') < registry.index('"Shadow Sidecar Trace Readback"')
    assert registry.index('"Human-reviewed Influence Preview"') < registry.index('"Detailed trace sections"')


def test_diagnostic_workspace_defaults_to_first_and_renders_only_selected_full_content():
    result = _run_node(
        """
const items = hooks.buildAgentTraceDiagnosticItems([
  ["evidence", "Evidence Chain", '<article><span class="agentic-workflow-badge">Read-only</span><div class="full-evidence">Evidence full content</div></article>'],
  ["pack", "Trace Evidence Pack", '<article><span class="agentic-workflow-badge">Ready</span><div class="full-pack">Pack full content</div></article>'],
  ["shadow", "Shadow Sidecar Trace Readback", '<article><span class="agentic-workflow-badge">Default-off</span><div class="full-shadow">Shadow full content</div></article>'],
]);
const markup = hooks.renderAgentTraceDiagnosticWorkspace(items);
console.log(JSON.stringify({
  selectedKey: vm.runInContext("agenticReviewDiagnosticState.selectedDiagnosticKey", context),
  selectedCount: (markup.match(/aria-pressed="true"/g) || []).length,
  hasMaster: markup.includes('id="agenticReviewDiagnosticMasterList"'),
  hasDetail: markup.includes('id="agenticReviewDiagnosticDetail"'),
  titlesReachable: ["Evidence Chain", "Trace Evidence Pack", "Shadow Sidecar Trace Readback"].every((title) => markup.includes(title)),
  evidenceFull: markup.includes("Evidence full content"),
  packFull: markup.includes("Pack full content"),
  shadowFull: markup.includes("Shadow full content"),
  realButtons: (markup.match(/<button/g) || []).length,
}));
"""
    )

    assert result == {
        "selectedKey": "evidence",
        "selectedCount": 1,
        "hasMaster": True,
        "hasDetail": True,
        "titlesReachable": True,
        "evidenceFull": True,
        "packFull": False,
        "shadowFull": False,
        "realButtons": 3,
    }


def test_diagnostic_selection_swaps_detail_without_fetch_action_or_payload_mutation():
    result = _run_node(
        """
const sourceDefinitions = [
  ["evidence", "Evidence Chain", '<article>Evidence detail</article>'],
  ["human", "Human-reviewed Influence Preview", '<article>Human detail<button data-human-reviewed-influence-preview>Preview</button></article>'],
];
const original = JSON.stringify(sourceDefinitions);
const items = hooks.buildAgentTraceDiagnosticItems(sourceDefinitions);
hooks.syncAgentTraceDiagnosticSelection(items);
for (const key of ["evidence", "human"]) {
  diagnosticButtons.push({
    dataset: { agentTraceDiagnosticKey: key },
    classList: classListFor(),
    setAttribute(name, value) { this[name] = value; },
  });
}
hooks.bindAgentTraceDiagnosticMasterDetail();
listeners.click({
  target: {
    closest(selector) {
      return selector === "[data-agent-trace-diagnostic-key]" ? diagnosticButtons[1] : null;
    },
  },
});
console.log(JSON.stringify({
  changed: vm.runInContext("agenticReviewDiagnosticState.selectedDiagnosticKey", context) === "human",
  selectedKey: vm.runInContext("agenticReviewDiagnosticState.selectedDiagnosticKey", context),
  firstPressed: diagnosticButtons[0]["aria-pressed"],
  secondPressed: diagnosticButtons[1]["aria-pressed"],
  detail: elements.agenticReviewDiagnosticDetail.innerHTML,
  sourceUnchanged: original === JSON.stringify(sourceDefinitions),
  fetchCalls,
  manualActionCalls,
}));
"""
    )

    assert result["changed"] is True
    assert result["selectedKey"] == "human"
    assert result["firstPressed"] == "false"
    assert result["secondPressed"] == "true"
    assert "Human detail" in result["detail"]
    assert "data-human-reviewed-influence-preview" in result["detail"]
    assert result["sourceUnchanged"] is True
    assert result["fetchCalls"] == 0
    assert result["manualActionCalls"] == 0


def test_trace_evidence_pack_selected_detail_uses_existing_fields_only():
    result = _run_node(
        """
const pack = {
  ok: false,
  readiness_status: "review",
  health_status: "warning",
  stage_count: 3,
  available_sections: ["trace_summary", "stage_trace_bundle"],
  missing_sections: ["stage_trace_readiness"],
  decision_reason_codes: ["missing_readiness"],
  blocking_findings: ["readiness_missing"],
  warning_findings: ["health_warning"],
  safety_metadata: {
    did_write_database: false,
    did_call_llm: false,
    did_execute_application: false,
    did_submit_application: false,
  },
};
const packMarkup = hooks.renderAgentTraceEvidencePackSection(pack);
const items = hooks.buildAgentTraceDiagnosticItems([["pack", "Trace Evidence Pack", packMarkup]]);
const detail = hooks.renderAgentTraceDiagnosticDetail(items[0]);
console.log(JSON.stringify({ detail }));
"""
    )

    detail = result["detail"]
    for marker in (
        "Trace Evidence Pack",
        "Evidence",
        "Readiness",
        "Health",
        "Stage count",
        "Writes",
        "LLM calls",
        "Execution",
        "Submission",
        "Available sections",
        "Missing sections",
        "Decision reason codes",
        "Blocking findings",
        "Warning findings",
        "Safety metadata",
        "missing_readiness",
    ):
        assert marker in detail
    assert 'data-collapsed-by-default="true"' in detail


def test_manual_diagnostic_actions_remain_explicit_and_selection_adds_no_authority():
    source = _source()
    helpers = _diagnostic_helpers()
    registry = _diagnostic_registry()

    for marker in (
        "renderShadowSidecarScoreComparisonSection",
        "renderHumanReviewedInfluencePreviewSection",
        "renderHumanReviewedInfluenceApprovalRequestSection",
        "renderManualApprovalRequestReadbackSection",
    ):
        assert marker in registry
    for marker in (
        "data-shadow-sidecar-score-comparison",
        "data-human-reviewed-influence-preview",
        "data-human-reviewed-influence-approval-request",
    ):
        assert marker in source

    for forbidden in (
        "fetch(",
        "fetchJson(",
        "localStorage",
        "/application-actions",
        'method: "POST"',
        'method: "PUT"',
        'method: "PATCH"',
        'method: "DELETE"',
        ".click(",
        "did_mutate_queue: true",
        "did_mutate_resume: true",
        "did_execute_application: true",
        "did_submit_application: true",
    ):
        assert forbidden not in helpers


def test_scoped_visual_language_and_advanced_tabs_defeat_global_cta_gradient():
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    correction = css[css.index("/* Item 6B6.5C:") :]

    assert "#agenticReviewAdvancedTab .agentic-review-advanced-tab" in correction
    advanced = correction[correction.index("#agenticReviewAdvancedTab .agentic-review-advanced-tab {") :]
    advanced = advanced[: advanced.index("}") + 1]
    assert "background: var(--app-surface) !important" in advanced
    assert "background-image: none !important" in advanced
    assert "color: var(--app-text-2) !important" in advanced
    assert "linear-gradient" not in advanced
    assert ".agent-trace-panel .agent-trace-extended-diagnostics" in css

    for marker in (
        ".agent-trace-diagnostic-workspace",
        ".agent-trace-diagnostic-master__list",
        "overflow-y: auto",
        "#agenticReviewDiagnosticMasterList .agent-trace-diagnostic-item.is-selected",
        "#agenticReviewDiagnosticMasterList .agent-trace-diagnostic-item:focus-visible",
        '[data-agent-trace-diagnostic-category="evidence"]',
        '[data-agent-trace-diagnostic-category="shadow"]',
        '[data-agent-trace-diagnostic-category="comparison"]',
        '[data-agent-trace-diagnostic-category="human"]',
        '[data-agent-trace-diagnostic-category="approval"]',
        '[data-agent-trace-diagnostic-category="safety"]',
        ".agent-trace-diagnostic-detail__header",
    ):
        assert marker in correction


def test_main_trace_empty_state_advanced_views_and_search_fix_remain_separate():
    source = _source()
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    panel = source[source.index("function renderAgentTraceReadOnlyPanel") : source.index("function renderAgentTracePanel")]
    search_start = source.index("function setAgenticReviewQueueSearch")
    search_end = source.index("function clearAgenticReviewQueueFilters", search_start)
    search = source[search_start:search_end]

    assert "renderAgentTraceMasterDetail(tracePayload)" in panel
    assert "renderAgentTraceDiagnosticWorkspace(diagnosticItems)" in panel
    assert "No persisted trace found for this run." in panel
    assert "No ordered agent steps returned for this trace." in panel
    assert panel.index("renderAgentTraceMasterDetail(tracePayload)") < panel.index(
        "renderAgentTraceDiagnosticWorkspace(diagnosticItems)"
    )
    assert 'String(searchQuery || "")' in search
    assert ".trim()" not in search

    for label, panel_id in (
        ("Workflow", "agenticReviewOverviewTab"),
        ("Agent Trace", "agenticReviewTraceTab"),
        ("Diagnostics", "agenticReviewDiagnosticsTab"),
        ("Source Views", "agenticReviewSourceViewsPanel"),
    ):
        assert f'data-agentic-advanced-target="{panel_id}">{label}</button>' in profile

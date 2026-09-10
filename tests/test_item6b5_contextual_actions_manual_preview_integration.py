from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
PLANNING_UI_PATH = ROOT / "src/app/planning_ui.py"
PLANNING_JS_PATH = ROOT / "src/app/static/planning.js"


def _review_js() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _run_node(assertions: str) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the focused Agentic Review preview integration test")
    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(REVIEW_JS_PATH))}, "utf8");
const listeners = {{}};
let modalHidden = true;
const elements = {{
  agenticReviewQueuePanel: {{
    innerHTML: "",
    addEventListener(type, handler) {{ listeners[type] = handler; }},
  }},
  agenticReviewSelectedJobPanel: {{ innerHTML: "" }},
  agenticReviewTailoringPanel: {{ innerHTML: "" }},
  manualProviderPreviewConfirmBtn: {{ disabled: false, textContent: "Generate preview", focus() {{}} }},
  manualProviderPreviewCancelBtn: {{ disabled: false, addEventListener() {{}} }},
  manualProviderPreviewConfirmModal: {{
    classList: {{
      add() {{ modalHidden = true; }},
      remove() {{ modalHidden = false; }},
      contains() {{ return modalHidden; }},
    }},
    addEventListener() {{}},
  }},
}};
const document = {{
  getElementById(id) {{ return elements[id] || null; }},
  querySelector(selector) {{
    if (selector === "[data-agentic-review-run-id]") return {{ dataset: {{ agenticReviewRunId: "run-a" }} }};
    if (selector.startsWith("[data-manual-provider-preview-action]")) return {{ focus() {{}} }};
    return null;
  }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
}};
let fetchCalls = 0;
const window = {{
  addEventListener() {{}},
  fetch() {{ fetchCalls += 1; throw new Error("unexpected fetch"); }},
  CSS: {{ escape(value) {{ return value; }} }},
}};
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
const qs = (id) => document.getElementById(id);
const renderWorkflowSummaryMetric = (label, value) => `<div><span>${{escapeHtml(label)}}</span><strong>${{escapeHtml(value)}}</strong></div>`;
const context = {{ window, document, console, Map, Set, Object, Array, String, Boolean, Error, JSON, escapeHtml, qs, renderWorkflowSummaryMetric }};
vm.createContext(context);
vm.runInContext(source, context);
const hooks = vm.runInContext(`({{
  consolidateAgenticReviewRows,
  renderAgenticReviewNextStep,
  renderAgenticReviewSelectedJobSummary,
  renderManualProviderPreviewResult,
  validateManualProviderPreviewResponse,
  openManualProviderPreviewConfirmation,
  closeManualProviderPreviewConfirmation,
  submitManualProviderPreview,
  setAgenticReviewQueueRecords,
  selectAgenticReviewQueueJob,
  bindAgenticReviewQueue,
}})`, context);
(async () => {{
{assertions}
}})().catch((error) => {{ console.error(error); process.exit(1); }});
"""
    completed = subprocess.run(
        [node, "-e", script],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_selected_inspector_owns_preview_action_and_honest_unavailable_state():
    result = _run_node(
        """
vm.runInContext('manualProviderPreviewState.readiness = "eligible";', context);
const eligible = hooks.consolidateAgenticReviewRows([], [{
  job_id: "job-a",
  title: "Engineer",
  company: "Acme",
  tailoring_decision: "tailor_before_apply",
}], [])[0];
const unavailable = hooks.consolidateAgenticReviewRows(
  [{ job_id: "job-b", title: "Analyst", company: "Beta" }],
  [],
  [],
)[0];
console.log(JSON.stringify({
  eligible: hooks.renderAgenticReviewNextStep(eligible),
  unavailable: hooks.renderAgenticReviewNextStep(unavailable),
}));
"""
    )

    assert "Next step" in result["eligible"]
    assert "AI Tailoring Preview" in result["eligible"]
    assert "Preview only — your resume will not be changed." in result["eligible"]
    assert 'data-job-id="job-a"' in result["eligible"]
    assert "Generate AI Preview" in result["eligible"]
    assert "disabled" not in result["eligible"]
    assert 'href="/planning"' in result["eligible"]
    assert 'data-job-id="job-b"' in result["unavailable"]
    assert "Tailoring evaluation not available" in result["unavailable"]
    assert "disabled" in result["unavailable"]


def test_tailoring_source_keeps_advisory_data_without_competing_preview_entry():
    source = _review_js()
    initial = source[
        source.index('"agenticReviewTailoringPanel"') :
        source.index('"agenticReviewOperatorPanel"')
    ]
    rerender_start = source.index("function rerenderManualProviderPreviewWorkspace")
    rerender = source[rerender_start : source.index("async function loadManualProviderPreviewReadiness", rerender_start)]

    for snippet in (initial, rerender):
        assert 'key: "company", label: "Company"' in snippet
        assert 'key: "title", label: "Title"' in snippet
        assert 'key: "tailoring_decision", label: "Tailoring decision"' in snippet
        assert 'key: "tailoring_reason_codes", label: "Reasons"' in snippet
        assert 'label: "AI preview", type: "manual_provider_preview_action"' not in snippet

    assert source.count("/api/manual-generate-ai-tailoring-preview-live") == 1
    assert source.count("async function submitManualProviderPreview") == 1
    assert "renderManualProviderPreviewAction(previewRow" in source


def test_selection_is_silent_and_click_cancel_preserves_explicit_invocation():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows([], [
  { job_id: "job-a", title: "First", company: "Acme" },
  { job_id: "job-b", title: "Second", company: "Beta" },
], []);
hooks.bindAgenticReviewQueue();
hooks.setAgenticReviewQueueRecords(records);
listeners.click({ target: { closest() { return { dataset: { agenticReviewQueueJobId: "job-b" } }; } } });
const afterSelectionCalls = fetchCalls;
vm.runInContext('manualProviderPreviewState.readiness = "eligible";', context);
hooks.openManualProviderPreviewConfirmation({ dataset: { jobId: "job-b" }, focus() {} });
const pendingAfterClick = vm.runInContext("manualProviderPreviewState.pendingJobId", context);
const modalAfterClick = modalHidden;
hooks.closeManualProviderPreviewConfirmation();
console.log(JSON.stringify({
  afterSelectionCalls,
  pendingAfterClick,
  modalAfterClick,
  pendingAfterCancel: vm.runInContext("manualProviderPreviewState.pendingJobId", context),
  finalCalls: fetchCalls,
}));
"""
    )

    assert result == {
        "afterSelectionCalls": 0,
        "pendingAfterClick": "job-b",
        "modalAfterClick": False,
        "pendingAfterCancel": "",
        "finalCalls": 0,
    }


def test_in_flight_result_stays_with_request_job_across_selection_change():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows([], [
  { job_id: "job-a", title: "First", company: "Acme", tailoring_decision: "tailor_before_apply" },
  { job_id: "job-b", title: "Second", company: "Beta", tailoring_decision: "light_tailoring" },
], []);
hooks.setAgenticReviewQueueRecords(records);
vm.runInContext('manualProviderPreviewState.readiness = "eligible"; manualProviderPreviewState.pendingJobId = "job-a"; manualProviderPreviewState.tailoringRows = [];', context);
let resolveRequest;
const calls = [];
window.fetch = (url, options) => {
  calls.push({ url, options });
  return new Promise((resolve) => { resolveRequest = resolve; });
};
const request = hooks.submitManualProviderPreview();
hooks.selectAgenticReviewQueueJob("job-b");
const duplicate = hooks.submitManualProviderPreview();
resolveRequest({
  ok: true,
  json: async () => ({
    ok: true,
    status: "manual_provider_preview_ready",
    preview_status: "advisory",
    manual_only: true,
    manual_review_required: true,
    normalized_preview: true,
    suggestions: [{
      suggestion_id: "suggestion-a",
      source_evidence_ids: ["evidence-a"],
      preview_text: "Job A grounded preview.",
      claims: [],
      rationale: "Job A evidence supports this wording.",
      risk_flags: [],
    }],
    provider_metadata: { provider: "synthetic", model: "qualified-model" },
    resume_mutation_authorized: false,
    automatic_acceptance_authorized: false,
    application_mutation_authorized: false,
    auto_apply_authorized: false,
    auto_submit_authorized: false,
  }),
});
await Promise.all([request, duplicate]);
const selectedBMarkup = elements.agenticReviewSelectedJobPanel.innerHTML;
const resultA = vm.runInContext('manualProviderPreviewState.results.has("job-a")', context);
const resultB = vm.runInContext('manualProviderPreviewState.results.has("job-b")', context);
hooks.selectAgenticReviewQueueJob("job-a");
const selectedAMarkup = elements.agenticReviewSelectedJobPanel.innerHTML;
console.log(JSON.stringify({
  callCount: calls.length,
  requestBody: JSON.parse(calls[0].options.body),
  resultA,
  resultB,
  bShowsA: selectedBMarkup.includes("Job A grounded preview."),
  aShowsA: selectedAMarkup.includes("Job A grounded preview."),
}));
"""
    )

    assert result["callCount"] == 1
    assert result["requestBody"] == {
        "pipeline_run_id": "run-a",
        "job_id": "job-a",
        "manual_triggered": True,
        "operator_confirmed": True,
    }
    assert result["resultA"] is True
    assert result["resultB"] is False
    assert result["bShowsA"] is False
    assert result["aShowsA"] is True


def test_unsafe_authority_responses_still_fail_closed():
    result = _run_node(
        """
const safePayload = {
  ok: true,
  status: "manual_provider_preview_ready",
  preview_status: "advisory",
  manual_only: true,
  manual_review_required: true,
  normalized_preview: true,
  suggestions: [{
    suggestion_id: "suggestion-1",
    source_evidence_ids: ["evidence-1"],
    preview_text: "Grounded preview.",
    claims: [],
    rationale: "Grounded rationale.",
    risk_flags: [],
  }],
  provider_metadata: {},
  resume_mutation_authorized: false,
  automatic_acceptance_authorized: false,
  application_mutation_authorized: false,
  auto_apply_authorized: false,
  auto_submit_authorized: false,
};
const fields = [
  "resume_mutation_authorized",
  "automatic_acceptance_authorized",
  "application_mutation_authorized",
  "auto_apply_authorized",
  "auto_submit_authorized",
];
const rejected = fields.map((field) => {
  try {
    hooks.validateManualProviderPreviewResponse({ ...safePayload, [field]: true });
    return false;
  } catch (_) {
    return true;
  }
});
console.log(JSON.stringify({ rejected }));
"""
    )

    assert result["rejected"] == [True, True, True, True, True]


def test_preview_renderer_uses_only_actual_safe_fields_and_optional_risks():
    result = _run_node(
        """
const base = {
  previewStatus: "advisory",
  manualReviewRequired: true,
  provider: "synthetic",
  model: "qualified-model",
  suggestions: [{
    suggestionId: "suggestion-1",
    previewText: "Use grounded evidence.",
    rationale: "The evidence supports this wording.",
    evidenceIds: ["evidence-1"],
    claims: [],
    riskFlags: [],
  }],
};
const withoutRisk = hooks.renderManualProviderPreviewResult({ kind: "success", preview: base });
const withRisk = hooks.renderManualProviderPreviewResult({
  kind: "success",
  preview: { ...base, suggestions: [{ ...base.suggestions[0], riskFlags: ["manual_review"] }] },
});
console.log(JSON.stringify({ withoutRisk, withRisk }));
"""
    )

    assert "Use grounded evidence." in result["withoutRisk"]
    assert "The evidence supports this wording." in result["withoutRisk"]
    assert "evidence-1" in result["withoutRisk"]
    assert "synthetic · qualified-model" in result["withoutRisk"]
    assert "Risk flags" not in result["withoutRisk"]
    assert "Risk flags" in result["withRisk"]
    assert "manual review" in result["withRisk"]
    for forbidden in ("undefined", "null", "provider_response_candidate", "JSON.stringify"):
        assert forbidden not in result["withoutRisk"]


def test_planning_route_regression_and_absolute_safety_contracts():
    source = _review_js()
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    planning_ui = PLANNING_UI_PATH.read_text(encoding="utf-8")
    planning_js = PLANNING_JS_PATH.read_text(encoding="utf-8")
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")

    assert '@router.get("/planning", response_class=HTMLResponse)' in planning_ui
    assert 'const AGENTIC_REVIEW_PLANNING_PATH = "/planning";' in source
    assert 'href="${AGENTIC_REVIEW_PLANNING_PATH}"' in source
    assert "AGENTIC_REVIEW_PLANNING_PATH = \"/planning?" not in source
    assert 'params.get("pipeline_run_id")' not in planning_js
    assert 'params.get("job_id")' not in planning_js

    for marker in (
        'id="agenticReviewQueuePanel"',
        'id="agenticReviewSelectedJobPanel"',
        'id="agenticReviewSourceViews"',
        'id="agenticReviewDiagnosticsTab"',
        'id="manualProviderPreviewConfirmModal"',
    ):
        assert marker in profile

    for marker in (
        "Recommendation",
        'id="agenticReviewInspectorWhyHeading">Why',
        'id="agenticReviewInspectorEvidenceHeading">Evidence',
        'id="agenticReviewInspectorAgentViewsHeading">Agent views',
        'id="agenticReviewInspectorNextStepHeading">Next step',
    ):
        assert marker in source

    assert "#agenticReviewQueuePanel .agentic-review-queue-item" in css
    assert ".agentic-review-next-step-panel" in css
    assert "#agenticReviewSelectedJobPanel .manual-provider-preview-action" in css
    assert ".agentic-review-planning-link" in css

    queue_start = source.index("const AGENTIC_REVIEW_QUEUE_GROUPS")
    queue_end = source.index("function renderAgenticReviewRows", queue_start)
    queue_and_inspector = source[queue_start:queue_end]
    for forbidden in (
        "/application-actions",
        "window.fetch",
        "fetchJson(",
        "localStorage",
        "tailoring_json=",
        "packet_json=",
        "resume=",
        "status=",
        "queue_mutation",
        "resume_mutation",
        "application_mutation",
        "approval_mutation",
        "ATS submission",
        "recruiter messaging",
        "consensus",
    ):
        assert forbidden not in queue_and_inspector

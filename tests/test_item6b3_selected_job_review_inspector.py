from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _review_js() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _run_node(assertions: str) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the focused Agentic Review inspector test")
    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(REVIEW_JS_PATH))}, "utf8");
const listeners = {{}};
const elements = {{
  agenticReviewQueuePanel: {{
    innerHTML: "",
    addEventListener(type, handler) {{ listeners[type] = handler; }},
  }},
  agenticReviewSelectedJobPanel: {{ innerHTML: "" }},
}};
const document = {{
  getElementById(id) {{ return elements[id] || null; }},
  querySelector() {{ return null; }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
}};
let fetchCalls = 0;
const window = {{
  addEventListener() {{}},
  fetch() {{ fetchCalls += 1; throw new Error("selection must not fetch"); }},
  CSS: {{ escape(value) {{ return value; }} }},
}};
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
const qs = (id) => document.getElementById(id);
const context = {{ window, document, console, Map, Set, Object, Array, String, Boolean, Error, JSON, escapeHtml, qs }};
vm.createContext(context);
vm.runInContext(source, context);
const hooks = vm.runInContext(`({{
  consolidateAgenticReviewRows,
  agenticReviewInspectorRecommendationLabel,
  agenticReviewInspectorRecommendationDescription,
  agenticReviewOperatorReasonCodes,
  agenticReviewReasonDisplayLabel,
  renderAgenticReviewInspectorReasons,
  renderAgenticReviewEvaluationCoverage,
  renderAgenticReviewSelectedJobSummary,
  setAgenticReviewQueueRecords,
  bindAgenticReviewQueue,
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


def test_inspector_header_prioritizes_identity_and_operator_recommendation():
    result = _run_node(
        """
const record = hooks.consolidateAgenticReviewRows([], [], [{
  job_id: "job-ready",
  title: "Platform Engineer",
  company: "ApplyLens Labs",
  source: "greenhouse",
  existing_action: "APPLY",
  operator_review_lane: "ready_to_apply",
  operator_review_reason_codes: "deterministic_match",
}])[0];
const missing = hooks.consolidateAgenticReviewRows(
  [{ job_id: "job-missing", title: "Data Engineer", company: "Acme" }],
  [],
  [],
)[0];
console.log(JSON.stringify({
  readyMarkup: hooks.renderAgenticReviewSelectedJobSummary(record),
  missingMarkup: hooks.renderAgenticReviewSelectedJobSummary(missing),
  readyLabel: hooks.agenticReviewInspectorRecommendationLabel(record),
  missingLabel: hooks.agenticReviewInspectorRecommendationLabel(missing),
}));
"""
    )

    assert result["readyLabel"] == "Ready"
    assert result["missingLabel"] == "Not fully evaluated"
    assert "Platform Engineer" in result["readyMarkup"]
    assert "ApplyLens Labs" in result["readyMarkup"]
    assert 'data-agentic-review-machine-lane="ready_to_apply"' in result["readyMarkup"]
    assert "Recommendation" in result["readyMarkup"]
    assert result["readyMarkup"].index("Recommendation") < result["readyMarkup"].index("Why")
    assert "Not fully evaluated" in result["missingMarkup"]


def test_lane_explanations_are_fixed_deterministic_presentation_copy():
    result = _run_node(
        """
const lanes = [
  "ready_to_apply",
  "tailor_then_apply",
  "review_before_action",
  "hold_or_skip",
  "source_watch",
];
const descriptions = Object.fromEntries(lanes.map((lane) => [
  lane,
  hooks.agenticReviewInspectorRecommendationDescription({ operator: { operator_review_lane: lane } }),
]));
descriptions.missing = hooks.agenticReviewInspectorRecommendationDescription({ operator: null });
console.log(JSON.stringify(descriptions));
"""
    )

    assert result == {
        "ready_to_apply": "The operator review currently classifies this job as ready.",
        "tailor_then_apply": "The operator review recommends tailoring before moving forward.",
        "review_before_action": "The operator review recommends human review before the next action.",
        "hold_or_skip": "The operator review recommends holding or skipping this job.",
        "source_watch": "The operator review recommends monitoring the source before acting.",
        "missing": "Operator review was not recorded for this job.",
    }


def test_why_uses_pipe_delimited_operator_reasons_without_changing_codes():
    result = _run_node(
        """
const raw = "deterministic_match|resume_identity_conflict|manual_review_required|source_needs_watch|packet_blocked|critic_risk";
const operator = { operator_review_reason_codes: raw };
const record = { operator };
const before = JSON.stringify(operator);
console.log(JSON.stringify({
  codes: hooks.agenticReviewOperatorReasonCodes(record),
  label: hooks.agenticReviewReasonDisplayLabel("resume_identity_conflict"),
  markup: hooks.renderAgenticReviewInspectorReasons(record),
  emptyMarkup: hooks.renderAgenticReviewInspectorReasons({ operator: {} }),
  unchanged: before === JSON.stringify(operator),
}));
"""
    )

    assert result["codes"] == [
        "deterministic_match",
        "resume_identity_conflict",
        "manual_review_required",
        "source_needs_watch",
        "packet_blocked",
        "critic_risk",
    ]
    assert result["label"] == "Resume identity conflict"
    assert result["unchanged"] is True
    for code in result["codes"]:
        assert f'data-agentic-review-reason-code="{code}"' in result["markup"]
    assert "Show 2 more reasons" in result["markup"]
    assert "No operator review reasons were recorded for this job." in result["emptyMarkup"]


def test_evaluation_coverage_reports_existence_without_quality_claims():
    result = _run_node(
        """
const partial = {
  prioritization: { job_id: "job-a" },
  tailoring: null,
  operator: { job_id: "job-a" },
};
console.log(JSON.stringify({ markup: hooks.renderAgenticReviewEvaluationCoverage(partial) }));
"""
    )

    assert "Prioritization" in result["markup"]
    assert "Tailoring" in result["markup"]
    assert "Operator Review" in result["markup"]
    assert result["markup"].count(">Evaluated<") == 2
    assert result["markup"].count(">Not evaluated<") == 1
    for forbidden in ("successful", "agreement", "confidence", "quality"):
        assert forbidden not in result["markup"].lower()


def test_queue_selection_rerenders_inspector_without_a_network_request():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [{ job_id: "job-a", title: "First", company: "Acme" }],
  [],
  [{ job_id: "job-b", title: "Second", company: "Beta", operator_review_lane: "source_watch" }],
);
hooks.bindAgenticReviewQueue();
hooks.setAgenticReviewQueueRecords(records);
const initialMarkup = elements.agenticReviewSelectedJobPanel.innerHTML;
listeners.click({ target: { closest() { return { dataset: { agenticReviewQueueJobId: "job-b" } }; } } });
console.log(JSON.stringify({
  initialMarkup,
  selectedMarkup: elements.agenticReviewSelectedJobPanel.innerHTML,
  selectedJobId: vm.runInContext("agenticReviewQueueState.selectedJobId", context),
  fetchCalls,
}));
"""
    )

    assert "First" in result["initialMarkup"]
    assert "Second" in result["selectedMarkup"]
    assert "Source watch" in result["selectedMarkup"]
    assert result["selectedJobId"] == "job-b"
    assert result["fetchCalls"] == 0


def test_inspector_preserves_source_views_preview_and_read_only_boundary():
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    source = _review_js()
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    start = source.index("const AGENTIC_REVIEW_QUEUE_GROUPS")
    end = source.index("function renderAgenticReviewRows", start)
    inspector_snippet = source[start:end]

    for marker in (
        'id="agenticReviewSourceViews"',
        'id="agenticReviewPriorityPanel"',
        'id="agenticReviewTailoringPanel"',
        'id="agenticReviewOperatorPanel"',
        'id="manualProviderPreviewConfirmModal"',
        'aria-label="Selected job review inspector"',
    ):
        assert marker in profile

    for marker in (
        "renderManualProviderPreviewAction",
        "openManualProviderPreviewConfirmation",
        "submitManualProviderPreview",
        "manualProviderPreviewState.tailoringRows",
    ):
        assert marker in source

    for marker in (
        ".agentic-review-inspector-recommendation",
        ".agentic-review-inspector-reasons",
        ".agentic-review-inspector-context",
        'data-agentic-review-lane="ready_to_apply"',
        'data-agentic-review-lane="tailor_then_apply"',
        'data-agentic-review-lane="review_before_action"',
        'data-agentic-review-lane="hold_or_skip"',
        'data-agentic-review-lane="source_watch"',
    ):
        assert marker in css

    for forbidden in (
        "/application-actions",
        "window.fetch",
        "fetchJson(",
        "localStorage",
        "MANUAL_PROVIDER_PREVIEW_ENDPOINT",
        'method: "POST"',
        'method: "PUT"',
        'method: "PATCH"',
        'method: "DELETE"',
        "consensus",
        "Agents aligned",
        "Agents disagree",
        "confidence aggregation",
        "resume_mutation",
        "application_mutation",
    ):
        assert forbidden not in inspector_snippet

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
        pytest.skip("Node is required for the focused Agentic Review interaction test")
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
  agenticReviewQueueGroup,
  agenticReviewQueueLaneLabel,
  groupAgenticReviewQueueRecords,
  normalizeAgenticReviewQueueFilterLane,
  agenticReviewQueueRecordMatchesLane,
  agenticReviewQueueRecordMatchesSearch,
  filterAgenticReviewQueueRecords,
  visibleAgenticReviewQueueRecords,
  renderAgenticReviewQueue,
  renderAgenticReviewSelectedJobSummary,
  setAgenticReviewQueueRecords,
  selectAgenticReviewQueueJob,
  setAgenticReviewQueueFilter,
  setAgenticReviewQueueSearch,
  clearAgenticReviewQueueFilters,
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


def test_union_consolidation_keeps_each_job_once_without_fuzzy_joining():
    result = _run_node(
        """
const prioritization = [
  { job_id: "job-a", title: "Engineer", company: "Acme", advisory_priority: "apply_now" },
  { job_id: "job-b", title: "Shared title", company: "Shared company", advisory_priority: "manual_review" },
];
const tailoring = [
  { job_id: "job-a", title: "Engineer", company: "Acme", tailoring_decision: "no_tailoring_needed" },
  { job_id: "job-c", title: "Shared title", company: "Shared company", tailoring_decision: "tailor_before_apply" },
];
const operator = [
  { job_id: "job-a", title: "Engineer", company: "Acme", operator_review_lane: "ready_to_apply" },
  { job_id: "job-d", title: "Analyst", company: "Delta", operator_review_lane: "review_before_action" },
];
const records = hooks.consolidateAgenticReviewRows(prioritization, tailoring, operator);
console.log(JSON.stringify({ records, order: records.map((record) => record.job_id) }));
"""
    )

    records = {record["job_id"]: record for record in result["records"]}
    assert result["order"] == ["job-a", "job-b", "job-c", "job-d"]
    assert len(records) == 4
    assert all(records["job-a"][stage] is not None for stage in ("prioritization", "tailoring", "operator"))
    assert records["job-b"]["prioritization"] is not None
    assert records["job-b"]["tailoring"] is None
    assert records["job-b"]["operator"] is None
    assert records["job-c"]["prioritization"] is None
    assert records["job-c"]["tailoring"] is not None
    assert records["job-c"]["operator"] is None
    assert records["job-d"]["prioritization"] is None
    assert records["job-d"]["tailoring"] is None
    assert records["job-d"]["operator"] is not None
    assert records["job-b"]["job_id"] != records["job-c"]["job_id"]


def test_lane_grouping_preserves_machine_values_and_keeps_missing_operator_neutral():
    result = _run_node(
        """
const operator = { job_id: "job-a", operator_review_lane: "tailor_then_apply" };
const original = JSON.stringify(operator);
const records = hooks.consolidateAgenticReviewRows(
  [{ job_id: "job-b", title: "Engineer", company: "Beta" }],
  [],
  [operator],
);
const withLane = records.find((record) => record.job_id === "job-a");
const missingLane = records.find((record) => record.job_id === "job-b");
console.log(JSON.stringify({
  machineLane: withLane.operator.operator_review_lane,
  laneLabel: hooks.agenticReviewQueueLaneLabel(withLane),
  laneGroup: hooks.agenticReviewQueueGroup(withLane).key,
  missingLabel: hooks.agenticReviewQueueLaneLabel(missingLane),
  missingGroup: hooks.agenticReviewQueueGroup(missingLane).key,
  sourceUnchanged: original === JSON.stringify(operator),
}));
"""
    )

    assert result == {
        "machineLane": "tailor_then_apply",
        "laneLabel": "Tailor first",
        "laneGroup": "tailor_then_apply",
        "missingLabel": "Not evaluated",
        "missingGroup": "not_fully_evaluated",
        "sourceUnchanged": True,
    }


def test_default_and_clicked_selection_are_frontend_only_and_deterministic():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [
    { job_id: "job-a", title: "First job", company: "Acme" },
    { job_id: "job-b", title: "Second job", company: "Beta" },
  ],
  [],
  [],
);
hooks.bindAgenticReviewQueue();
hooks.setAgenticReviewQueueRecords(records);
const defaultSelected = vm.runInContext("agenticReviewQueueState.selectedJobId", context);
const defaultSelectedCount = (elements.agenticReviewQueuePanel.innerHTML.match(/aria-pressed="true"/g) || []).length;
listeners.click({ target: { closest() { return { dataset: { agenticReviewQueueJobId: "job-b" } }; } } });
const clickedSelected = vm.runInContext("agenticReviewQueueState.selectedJobId", context);
const clickedSelectedCount = (elements.agenticReviewQueuePanel.innerHTML.match(/aria-pressed="true"/g) || []).length;
console.log(JSON.stringify({ defaultSelected, defaultSelectedCount, clickedSelected, clickedSelectedCount, fetchCalls }));
"""
    )

    assert result == {
        "defaultSelected": "job-a",
        "defaultSelectedCount": 1,
        "clickedSelected": "job-b",
        "clickedSelectedCount": 1,
        "fetchCalls": 0,
    }


def test_empty_queue_is_non_error_and_missing_perspectives_are_explicit():
    result = _run_node(
        """
hooks.setAgenticReviewQueueRecords([]);
const partial = hooks.consolidateAgenticReviewRows(
  [{ job_id: "job-a", title: "Engineer", company: "Acme" }],
  [],
  [],
)[0];
const summary = hooks.renderAgenticReviewSelectedJobSummary(partial);
console.log(JSON.stringify({
  emptyMarkup: elements.agenticReviewQueuePanel.innerHTML,
  selectedMarkup: elements.agenticReviewSelectedJobPanel.innerHTML,
  partialSummary: summary,
}));
"""
    )

    assert "No advisory review data was produced for this run." in result["emptyMarkup"]
    assert 'role="status"' in result["emptyMarkup"]
    assert 'role="alert"' not in result["emptyMarkup"]
    assert "No job selected" in result["selectedMarkup"]
    assert result["partialSummary"].count("Not evaluated") == 5
    assert "Not fully evaluated" in result["partialSummary"]
    assert "Evaluated" in result["partialSummary"]


def test_queue_markup_and_source_views_preserve_existing_advisory_contracts():
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    source = _review_js()
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")

    for marker in (
        'id="agenticReviewQueuePanel"',
        'id="agenticReviewSelectedJobPanel"',
        'id="agenticReviewSourceViews"',
        "Advisory source views",
        'id="agenticReviewPriorityPanel"',
        'id="agenticReviewTailoringPanel"',
        'id="agenticReviewOperatorPanel"',
        'data-agentic-advisory-target="agenticReviewPriorityPanel"',
        'data-agentic-advisory-target="agenticReviewTailoringPanel"',
        'data-agentic-advisory-target="agenticReviewOperatorPanel"',
        'id="manualProviderPreviewConfirmModal"',
    ):
        assert marker in profile

    for marker in (
        "renderAgenticReviewAdvisoryPanel",
        "renderManualProviderPreviewAction",
        "openManualProviderPreviewConfirmation",
        "submitManualProviderPreview",
        "manualProviderPreviewState.tailoringRows",
    ):
        assert marker in source

    for marker in (
        ".agentic-review-workspace-grid",
        ".agentic-review-queue-item.is-selected",
        ".agentic-review-queue-empty",
        ".agentic-review-source-views",
        "data-agentic-review-lane=\"ready_to_apply\"",
        "data-agentic-review-lane=\"tailor_then_apply\"",
        "data-agentic-review-lane=\"review_before_action\"",
        "data-agentic-review-lane=\"hold_or_skip\"",
        "data-agentic-review-lane=\"source_watch\"",
    ):
        assert marker in css


def test_queue_helpers_and_selection_add_no_network_or_mutation_authority():
    source = _review_js()
    start = source.index("const AGENTIC_REVIEW_QUEUE_GROUPS")
    end = source.index("function renderAgenticReviewRows", start)
    queue_snippet = source[start:end]

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
        "approval",
        "resume_mutation",
        "application_mutation",
    ):
        assert forbidden not in queue_snippet

    init_start = source.index("async function initAgenticReviewPage")
    init_end = source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    init_snippet = source[init_start:init_end]
    assert "bindAgenticReviewQueue();" in init_snippet
    assert "selectAgenticReviewQueueJob(" not in init_snippet
    assert "submitManualProviderPreview()" not in init_snippet

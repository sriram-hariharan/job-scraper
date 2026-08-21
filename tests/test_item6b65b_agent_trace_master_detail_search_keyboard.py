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
PREFERENCES_JS_PATH = ROOT / "src/app/static/preferences_workflow.js"
PREFERENCES_CSS_PATH = ROOT / "src/app/static/preferences.css"


def _source() -> str:
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
const traceButtons = [];
function classListFor(values = []) {{
  const state = new Set(values);
  return {{
    toggle(name, force) {{ force ? state.add(name) : state.delete(name); }},
    contains(name) {{ return state.has(name); }},
  }};
}}
const elements = {{
  agenticReviewQueuePanel: {{ innerHTML: "", addEventListener(type, handler) {{ listeners[`queue:${{type}}`] = handler; }} }},
  agenticReviewSelectedJobPanel: {{ innerHTML: "" }},
  agenticReviewQueueSearch: {{ value: "", addEventListener(type, handler) {{ listeners[`search:${{type}}`] = handler; }} }},
  agenticReviewTraceDetail: {{ innerHTML: "" }},
}};
const tabButtons = [
  {{ dataset: {{ agenticTabTarget: "first" }}, focus() {{}}, classList: classListFor(), setAttribute() {{}} }},
  {{ dataset: {{ agenticTabTarget: "second" }}, focus() {{}}, classList: classListFor(), setAttribute() {{}} }},
];
const tablist = {{
  addEventListener(type, handler) {{ listeners[`tab:${{type}}`] = handler; }},
  querySelectorAll() {{ return tabButtons; }},
}};
const document = {{
  getElementById(id) {{ return elements[id] || null; }},
  querySelector(selector) {{ return selector === ".agentic-review-tabs" ? tablist : null; }},
  querySelectorAll(selector) {{
    if (selector === "[data-agent-trace-item-key]") return traceButtons;
    return [];
  }},
  addEventListener(type, handler) {{ listeners[`document:${{type}}`] = handler; }},
}};
let fetchCalls = 0;
const window = {{
  addEventListener() {{}},
  fetch() {{ fetchCalls += 1; throw new Error("frontend selection must not fetch"); }},
  CSS: {{ escape(value) {{ return value; }} }},
}};
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
const qs = (id) => document.getElementById(id);
const renderWorkflowSummaryMetric = (label, value) => `<div class="pipeline-run-detail-row"><span>${{escapeHtml(label)}}</span><strong>${{escapeHtml(value)}}</strong></div>`;
const context = {{ window, document, console, Map, Set, Object, Array, String, Boolean, Number, Error, JSON, escapeHtml, qs, renderWorkflowSummaryMetric }};
vm.createContext(context);
vm.runInContext(source, context);
const hooks = vm.runInContext(`({{
  consolidateAgenticReviewRows,
  agenticReviewQueueRecordMatchesSearch,
  setAgenticReviewQueueRecords,
  setAgenticReviewQueueSearch,
  bindAgenticReviewQueue,
  bindAgenticReviewTablist,
  agentTraceItemKey,
  buildAgentTraceSelectionItems,
  syncAgentTraceSelection,
  renderAgentTraceMasterDetail,
  renderAgentTraceSelectedStep,
  selectAgentTraceItem,
  bindAgentTraceMasterDetail,
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


def test_preferences_master_detail_reference_was_inspected_without_becoming_a_dependency():
    preferences_js = PREFERENCES_JS_PATH.read_text(encoding="utf-8")
    preferences_css = PREFERENCES_CSS_PATH.read_text(encoding="utf-8")
    source = _source()

    assert "function showStep" in preferences_js
    assert "data-preferences-step-target" in preferences_js
    assert ".preferences-workflow .preferences-step-navigation" in preferences_css
    assert ".preferences-workflow .preferences-editor-shell" in preferences_css
    assert "preferences_workflow" not in source


def test_trace_master_list_preserves_order_identity_status_and_deterministic_default():
    result = _run_node(
        """
const payload = {
  found: true,
  step_count: 2,
  agent_run: { agent_run_id: "run-42", status: "warning", started_at: "2026-08-21T10:00:00Z" },
  agent_steps: [
    { agent_step_id: "step-a", agent_name: "Prioritization", status: "succeeded", started_at: "2026-08-21T10:00:01Z", latency_ms: 12 },
    { agent_step_id: "step-b", agent_name: "Operator Review", status: "failed", started_at: "2026-08-21T10:00:02Z", latency_ms: 18, error: "blocked fixture" },
  ],
  trace_summary: { step_count: 2, completed_step_count: 1, error_step_count: 1, warning_step_count: 0 },
};
const items = hooks.buildAgentTraceSelectionItems(payload);
const markup = hooks.renderAgentTraceMasterDetail(payload);
console.log(JSON.stringify({
  keys: items.map((item) => item.key),
  defaultKey: vm.runInContext("agenticReviewTraceState.selectedTraceKey", context),
  selectedCount: (markup.match(/aria-pressed="true"/g) || []).length,
  ordered: markup.indexOf("step-a") < markup.indexOf("step-b"),
  hasStatus: markup.includes("succeeded") && markup.includes("failed"),
  hasTimestamp: markup.includes("2026-08-21T10:00:02Z"),
  hasLatency: markup.includes("18 ms"),
  hasRealButtons: markup.includes('<button') && markup.includes('data-agent-trace-item-key='),
}));
"""
    )

    assert result == {
        "keys": ["run-42:step-a", "run-42:step-b"],
        "defaultKey": "run-42:step-a",
        "selectedCount": 1,
        "ordered": True,
        "hasStatus": True,
        "hasTimestamp": True,
        "hasLatency": True,
        "hasRealButtons": True,
    }


def test_trace_selection_updates_frontend_detail_only_and_preserves_payload():
    result = _run_node(
        """
const payload = {
  found: true,
  agent_run: { agent_run_id: "run-7", status: "succeeded" },
  agent_steps: [
    { agent_step_id: "one", agent_name: "First Agent", status: "succeeded", output_json: { value: "first" } },
    { agent_step_id: "two", agent_name: "Second Agent", status: "warning", output_json: { value: "second" } },
  ],
};
const original = JSON.stringify(payload);
hooks.syncAgentTraceSelection(payload);
for (const key of ["run-7:one", "run-7:two"]) {
  traceButtons.push({
    dataset: { agentTraceItemKey: key },
    classList: classListFor(),
    setAttribute(name, value) { this[name] = value; },
  });
}
const changed = hooks.selectAgentTraceItem("run-7:two");
console.log(JSON.stringify({
  changed,
  selectedKey: vm.runInContext("agenticReviewTraceState.selectedTraceKey", context),
  selectedButton: traceButtons[1]["aria-pressed"],
  firstButton: traceButtons[0]["aria-pressed"],
  detail: elements.agenticReviewTraceDetail.innerHTML,
  payloadUnchanged: original === JSON.stringify(payload),
  fetchCalls,
}));
"""
    )

    assert result["changed"] is True
    assert result["selectedKey"] == "run-7:two"
    assert result["selectedButton"] == "true"
    assert result["firstButton"] == "false"
    assert "Second Agent" in result["detail"]
    assert "second" in result["detail"]
    assert result["payloadUnchanged"] is True
    assert result["fetchCalls"] == 0


def test_selected_trace_detail_preserves_step_information_with_progressive_disclosure():
    result = _run_node(
        """
const payload = { agent_run: { agent_run_id: "run-9", metadata: { source: "fixture" } } };
const item = {
  key: "run-9:step-9",
  index: 0,
  step: {
    agent_step_id: "step-9",
    agent_name: "Tailoring Agent",
    agent_version: "v2",
    status: "failed",
    started_at: "2026-08-21T11:00:00Z",
    completed_at: "2026-08-21T11:00:01Z",
    model_provider: "fixture-provider",
    model_name: "fixture-model",
    latency_ms: 34,
    input_json: { job_id: "job-1" },
    output_json: { decision: "review" },
    validation_json: { validation_status: "warning", warnings: ["check evidence"] },
    token_usage_json: { input_tokens: 10, output_tokens: 4 },
    cost_json: { estimated_cost: 0.001 },
    safety_metadata: { read_only: true },
    error: "fixture failure",
  },
};
const markup = hooks.renderAgentTraceSelectedStep(item, payload);
console.log(JSON.stringify({ markup }));
"""
    )

    markup = result["markup"]
    for marker in (
        "Tailoring Agent",
        "fixture-provider / fixture-model",
        "34 ms",
        "Input",
        "Output",
        "Validation and safety",
        "Model, tokens, cost, and latency",
        "Token usage",
        "Cost",
        "Raw / debug",
        "fixture failure",
        "Validation warning",
    ):
        assert marker in markup
    assert markup.count('data-collapsed-by-default="true"') >= 6
    assert 'role="alert"' in markup


def test_trace_panel_keeps_empty_error_and_extended_observability_contracts():
    source = _source()
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    panel = source[source.index("function renderAgentTraceReadOnlyPanel") : source.index("function renderAgentTracePanel")]

    for marker in (
        "No persisted trace found for this run.",
        "Empty trace: agent run metadata is available",
        "Fetch failure:",
        "Extended trace diagnostics",
        "renderAgentTraceEvidencePackSection",
        "renderAgentTraceDetailedSections",
        "renderAgentTraceMasterDetail",
    ):
        assert marker in panel
    assert 'id="agenticReviewTracePanel"' in profile
    assert 'id="agenticReviewTraceTab"' in profile
    assert ".agent-trace-master-detail" in css
    assert ".agent-trace-master-list" in css
    assert "overflow-y: auto" in css
    assert ".agent-trace-master-item.is-selected" in css
    assert ".agent-trace-master-item:focus-visible" in css
    assert "@media (max-width: 880px)" in css


def test_queue_search_input_preserves_spaces_and_normal_keyboard_editing():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [
    { job_id: "one", title: "Senior Data Engineer", company: "Acme Labs" },
    { job_id: "two", title: "Senior Engineer", company: "Data Works" },
  ],
  [],
  [],
);
hooks.bindAgenticReviewQueue();
hooks.setAgenticReviewQueueRecords(records);
elements.agenticReviewQueueSearch.value = "senior ";
listeners["search:input"]({ target: elements.agenticReviewQueueSearch });
const trailingState = vm.runInContext("agenticReviewQueueState.searchQuery", context);
const trailingValue = elements.agenticReviewQueueSearch.value;
elements.agenticReviewQueueSearch.value = "senior data";
listeners["search:input"]({ target: elements.agenticReviewQueueSearch });
const spacedState = vm.runInContext("agenticReviewQueueState.searchQuery", context);
const matches = records.map((record) => hooks.agenticReviewQueueRecordMatchesSearch(record, "SeNiOr DaTa"));
hooks.bindAgenticReviewTablist(".agentic-review-tabs", ".agentic-review-tab", "[data-agentic-tab-panel]", "agenticTabTarget");
const keyboardResults = {};
for (const key of [" ", "Backspace", "ArrowLeft", "ArrowRight", "Home", "End"]) {
  let prevented = false;
  listeners["tab:keydown"]({
    key,
    target: { closest() { return null; } },
    preventDefault() { prevented = true; },
  });
  keyboardResults[key] = prevented;
}
console.log(JSON.stringify({ trailingState, trailingValue, spacedState, matches, keyboardResults, fetchCalls }));
"""
    )

    assert result["trailingState"] == "senior "
    assert result["trailingValue"] == "senior "
    assert result["spacedState"] == "senior data"
    assert result["matches"] == [True, False]
    assert all(prevented is False for prevented in result["keyboardResults"].values())
    assert result["fetchCalls"] == 0


def test_trace_selection_and_search_fix_add_no_network_or_mutation_authority():
    source = _source()
    trace_start = source.index("function agentTraceItemKey")
    trace_end = source.index("function renderAgentTraceReadOnlyState", trace_start)
    trace_selection = source[trace_start:trace_end]
    search_start = source.index("function setAgenticReviewQueueSearch")
    search_end = source.index("function clearAgenticReviewQueueFilters", search_start)
    search_setter = source[search_start:search_end]

    for forbidden in (
        "fetch(",
        "fetchJson(",
        "localStorage",
        "/application-actions",
        "method: \"POST\"",
        "method: \"PUT\"",
        "method: \"PATCH\"",
        "method: \"DELETE\"",
        "did_mutate_queue: true",
        "did_mutate_resume: true",
        "did_execute_application: true",
        "did_submit_application: true",
        "Agents aligned",
        "Agents disagree",
        "Consensus",
    ):
        assert forbidden not in trace_selection
    assert '.trim()' not in search_setter
    assert "String(searchQuery || \"\")" in search_setter
    assert "fetch(" not in search_setter

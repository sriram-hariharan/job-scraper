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
        pytest.skip("Node is required for the focused Agentic Review evidence test")
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
  agenticReviewRecordedFact,
  agenticReviewEvidenceGroups,
  agenticReviewAgentViews,
  agenticReviewAgentViewResult,
  renderAgenticReviewEvidence,
  renderAgenticReviewAgentViews,
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


def test_evidence_renders_only_recorded_facts_with_explicit_provenance():
    result = _run_node(
        """
const prioritization = {
  job_id: "job-a",
  deterministic_winner_score: "0.71",
  packet_generation_allowed: false,
  packet_generation_block_reason: "missing_required_evidence",
  fallback_only_no_deterministic_match: "false",
};
const tailoring = {
  job_id: "job-a",
  deterministic_winner_score: "0.76",
  winner_resume: "backend_resume.pdf",
  resolved_resume: "resolved_resume.pdf",
};
const operator = {
  job_id: "job-a",
  deterministic_winner_score: "0.82",
  operator_review_lane: "review_before_action",
};
const record = hooks.consolidateAgenticReviewRows([prioritization], [tailoring], [operator])[0];
const before = JSON.stringify({ prioritization, tailoring, operator });
console.log(JSON.stringify({
  groups: hooks.agenticReviewEvidenceGroups(record),
  markup: hooks.renderAgenticReviewEvidence(record),
  unchanged: before === JSON.stringify({ prioritization, tailoring, operator }),
}));
"""
    )

    facts = {
        fact["field"]: fact
        for group in result["groups"]
        for fact in group["facts"]
    }
    assert facts["deterministic_winner_score"]["value"] == "0.82"
    assert facts["deterministic_winner_score"]["sourceLabel"] == "Operator Review"
    assert facts["winner_resume"]["value"] == "backend_resume.pdf"
    assert facts["winner_resume"]["sourceLabel"] == "Tailoring"
    assert facts["resolved_resume"]["value"] == "resolved_resume.pdf"
    assert facts["packet_generation_allowed"]["value"] is False
    assert facts["packet_generation_allowed"]["sourceLabel"] == "Prioritization"
    assert facts["fallback_only_no_deterministic_match"]["value"] == "false"
    assert result["unchanged"] is True
    assert "Deterministic match score" in result["markup"]
    assert "Selected resume" in result["markup"]
    assert "Packet generation allowed" in result["markup"]
    assert "Fallback only / no deterministic match" in result["markup"]
    assert "From Operator Review" in result["markup"]
    assert "From Tailoring" in result["markup"]
    assert "From Prioritization" in result["markup"]


def test_missing_evidence_is_not_fabricated_or_rendered_as_zero():
    result = _run_node(
        """
const record = hooks.consolidateAgenticReviewRows(
  [{ job_id: "job-empty", title: "Engineer", company: "Acme" }],
  [],
  [],
)[0];
console.log(JSON.stringify({
  groups: hooks.agenticReviewEvidenceGroups(record),
  score: hooks.agenticReviewRecordedFact(record, "deterministic_winner_score"),
  markup: hooks.renderAgenticReviewEvidence(record),
}));
"""
    )

    assert result["groups"] == []
    assert result["score"] is None
    assert "No supporting evidence was recorded for this job." in result["markup"]
    assert "Deterministic match score" not in result["markup"]
    assert 'data-agentic-review-evidence-field="deterministic_winner_score"' not in result["markup"]
    assert ">0<" not in result["markup"]


def test_evidence_copy_does_not_reinterpret_score_or_packet_gating():
    result = _run_node(
        """
const record = hooks.consolidateAgenticReviewRows([], [{
  job_id: "job-a",
  deterministic_winner_score: "0.63",
  packet_generation_allowed: "false",
  packet_generation_block_reason: "packet_inputs_missing",
}], [])[0];
console.log(JSON.stringify({ markup: hooks.renderAgenticReviewEvidence(record) }));
"""
    )

    normalized = result["markup"].lower()
    assert "deterministic match score" in normalized
    assert "packet generation allowed" in normalized
    assert "packet inputs missing" in normalized
    for forbidden in (
        "confidence",
        "probability",
        "chance of success",
        "application likelihood",
        "application permission",
        "authorized to apply",
    ):
        assert forbidden not in normalized


def test_agent_views_keep_stage_results_independent_and_machine_values_unchanged():
    result = _run_node(
        """
const prioritization = {
  job_id: "job-a",
  advisory_priority: "apply_now",
  advisory_reason_codes: "score_above_review_threshold|packet_ready",
};
const tailoring = {
  job_id: "job-a",
  tailoring_decision: "tailor_before_apply",
  tailoring_reason_codes: "supported_gap_found",
  critic_decision: "reject",
  critic_reason_codes: "unsupported_claim|identity_conflict",
};
const operator = {
  job_id: "job-a",
  operator_review_lane: "tailor_then_apply",
  operator_review_reason_codes: "tailoring_required",
  critic_decision: "reject",
};
const original = JSON.stringify({ prioritization, tailoring, operator });
const record = hooks.consolidateAgenticReviewRows([prioritization], [tailoring], [operator])[0];
console.log(JSON.stringify({
  views: hooks.agenticReviewAgentViews(record).map((view) => ({
    key: view.key,
    result: hooks.agenticReviewAgentViewResult(view),
  })),
  markup: hooks.renderAgenticReviewAgentViews(record),
  unchanged: original === JSON.stringify({ prioritization, tailoring, operator }),
}));
"""
    )

    views = {view["key"]: view["result"] for view in result["views"]}
    assert views["prioritization"] == {
        "label": "Apply now",
        "machineValue": "apply_now",
        "missing": False,
    }
    assert views["tailoring"] == {
        "label": "Tailor before apply",
        "machineValue": "tailor_before_apply",
        "missing": False,
    }
    assert views["operator"] == {
        "label": "Tailor first",
        "machineValue": "tailor_then_apply",
        "missing": False,
    }
    assert views["critic"] == {
        "label": "Reject",
        "machineValue": "reject",
        "missing": False,
    }
    assert result["unchanged"] is True
    for machine_value in ("apply_now", "tailor_before_apply", "tailor_then_apply", "reject"):
        assert f'data-agentic-review-machine-value="{machine_value}"' in result["markup"]
    assert 'data-agentic-review-agent-reason-code="unsupported_claim"' in result["markup"]
    assert "From Tailoring" in result["markup"]
    assert "Reasons shown in Why" in result["markup"]


def test_partial_agent_views_are_explicit_and_selection_updates_without_fetching():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [{ job_id: "job-a", title: "First", company: "Acme", advisory_priority: "manual_review" }],
  [],
  [{
    job_id: "job-b",
    title: "Second",
    company: "Beta",
    operator_review_lane: "source_watch",
    deterministic_winner_score: "0.58",
  }],
);
const partialMarkup = hooks.renderAgenticReviewAgentViews(records[0]);
hooks.bindAgenticReviewQueue();
hooks.setAgenticReviewQueueRecords(records);
listeners.click({ target: { closest() { return { dataset: { agenticReviewQueueJobId: "job-b" } }; } } });
console.log(JSON.stringify({
  partialMarkup,
  selectedMarkup: elements.agenticReviewSelectedJobPanel.innerHTML,
  selectedJobId: vm.runInContext("agenticReviewQueueState.selectedJobId", context),
  fetchCalls,
}));
"""
    )

    assert "Manual review" in result["partialMarkup"]
    assert result["partialMarkup"].count("Not evaluated") == 3
    assert "Second" in result["selectedMarkup"]
    assert "Source watch" in result["selectedMarkup"]
    assert "0.58" in result["selectedMarkup"]
    assert result["selectedJobId"] == "job-b"
    assert result["fetchCalls"] == 0


def test_agent_views_preserve_source_surfaces_and_read_only_safety_boundary():
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
        ".agentic-review-evidence-disclosure",
        ".agentic-review-evidence-group",
        ".agentic-review-agent-view-list",
        ".agentic-review-agent-view[data-agentic-review-agent=\"tailoring\"]",
        ".agentic-review-agent-view[data-agentic-review-agent=\"operator\"]",
        ".agentic-review-agent-view[data-agentic-review-agent=\"critic\"]",
        "@media (max-width: 620px)",
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
        "Agents aligned",
        "Agents disagree",
        "consensus",
        "voting",
        "majority",
        "agreement score",
        "queue_mutation",
        "resume_mutation",
        "application_mutation",
        "approval_mutation",
        "ATS submission",
        "recruiter messaging",
    ):
        assert forbidden not in inspector_snippet

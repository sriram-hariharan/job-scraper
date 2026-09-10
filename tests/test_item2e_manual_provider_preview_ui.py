from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _review_js() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _function(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}")
    end = source.index(f"function {next_name}", start)
    return source[start:end]


def _run_node(assertions: str) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the owned static-JS interaction test")
    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(REVIEW_JS_PATH))}, "utf8");
const elements = {{
  manualProviderPreviewConfirmBtn: {{ disabled: false, textContent: "Generate preview", focus() {{}} }},
  manualProviderPreviewCancelBtn: {{ disabled: false, addEventListener() {{}} }},
  manualProviderPreviewConfirmModal: {{
    classList: {{ add() {{}}, remove() {{}}, contains() {{ return true; }} }},
    addEventListener() {{}},
  }},
}};
const document = {{
  getElementById(id) {{ return elements[id] || null; }},
  querySelector(selector) {{
    if (selector === "[data-agentic-review-run-id]") return {{ dataset: {{ agenticReviewRunId: "run-a" }} }};
    return {{ focus() {{}} }};
  }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
}};
const window = {{ addEventListener() {{}}, CSS: {{ escape(value) {{ return value; }} }} }};
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
const qs = (id) => document.getElementById(id);
const context = {{ window, document, console, Map, Set, Object, Array, String, Boolean, Error, JSON, escapeHtml, qs }};
vm.createContext(context);
vm.runInContext(source, context);
const hooks = vm.runInContext(`({{
  manualProviderPreviewReadiness,
  manualProviderPreviewRequestBody,
  renderManualProviderPreviewAction,
  validateManualProviderPreviewResponse,
  renderManualProviderPreviewResult,
  openManualProviderPreviewConfirmation,
  closeManualProviderPreviewConfirmation,
  submitManualProviderPreview,
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


def test_action_is_in_selected_job_inspector_and_modal_is_explicit():
    source = _review_js()
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    review_css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    tailoring = source[
        source.index('"agenticReviewTailoringPanel"') :
        source.index('"agenticReviewOperatorPanel"')
    ]
    next_step = _function(
        source,
        "renderAgenticReviewNextStep",
        "renderAgenticReviewInspectorContext",
    )

    assert 'label: "AI preview", type: "manual_provider_preview_action"' not in tailoring
    assert "renderManualProviderPreviewAction(previewRow" in next_step
    assert "Generate AI Preview" in source
    assert "data-manual-provider-preview-result" in next_step
    assert 'id="manualProviderPreviewConfirmModal"' in profile
    assert 'role="dialog"' in profile
    assert 'aria-modal="true"' in profile
    assert "one call to your currently qualified AI provider" in profile
    assert "Nothing is automatically applied to your resume" in profile
    assert "nothing is submitted to an employer" in profile
    assert ".manual-provider-preview-modal-card" in css
    assert ".manual-provider-preview-result" in css
    assert ".agentic-review-next-step" in review_css
    assert "#agenticReviewSelectedJobPanel .manual-provider-preview-action" in review_css


def test_readiness_is_owner_routing_driven_and_page_load_never_posts():
    source = _review_js()
    readiness = _function(
        source,
        "manualProviderPreviewReadiness",
        "manualProviderPreviewRequestBody",
    )
    loader = _function(
        source,
        "loadManualProviderPreviewReadiness",
        "openManualProviderPreviewConfirmation",
    )
    init = source[
        source.index("async function initAgenticReviewPage") :
        source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    ]

    assert 'item?.workload_id === MANUAL_PROVIDER_PREVIEW_WORKLOAD' in readiness
    assert 'route.recommendation_status === "blocked_non_live"' in readiness
    assert 'route.execution_mode === "qualified_provider_model"' in readiness
    assert 'window.fetch("/ai/settings/recommended-routes"' in loader
    assert 'method: "GET"' in loader
    assert "loadManualProviderPreviewReadiness();" in init
    assert "submitManualProviderPreview()" not in init
    assert 'method: "POST"' not in init
    assert "MANUAL_PROVIDER_PREVIEW_ENDPOINT" not in init


def test_blocked_and_unknown_states_fail_closed_and_qualified_state_enables():
    result = _run_node(
        """
const blocked = hooks.manualProviderPreviewReadiness({ ok: true, workloads: [{
  workload_id: "manual_provider_preview",
  recommendation_status: "blocked_non_live",
  execution_mode: "blocked_non_live",
  qualified_options: [],
  effective_selection: null,
}] });
const unknown = hooks.manualProviderPreviewReadiness({ ok: true, workloads: [] });
const eligible = hooks.manualProviderPreviewReadiness({ ok: true, workloads: [{
  workload_id: "manual_provider_preview",
  recommendation_status: "recommended",
  execution_mode: "qualified_provider_model",
  qualified_options: [{ provider: "synthetic", model: "qualified-model" }],
  effective_selection: { provider: "synthetic", model: "qualified-model" },
}] });
let calls = 0;
window.fetch = async () => { calls += 1; throw new Error("must not call"); };
vm.runInContext('manualProviderPreviewState.readiness = "blocked"; manualProviderPreviewState.pendingJobId = "job-a";', context);
await hooks.submitManualProviderPreview();
const blockedMarkup = vm.runInContext('renderManualProviderPreviewAction({job_id: "job-a"})', context);
vm.runInContext('manualProviderPreviewState.readiness = "unknown";', context);
const unknownMarkup = vm.runInContext('renderManualProviderPreviewAction({job_id: "job-a"})', context);
vm.runInContext('manualProviderPreviewState.readiness = "eligible";', context);
const eligibleMarkup = vm.runInContext('renderManualProviderPreviewAction({job_id: "job-a"})', context);
console.log(JSON.stringify({ blocked, unknown, eligible, calls, blockedMarkup, unknownMarkup, eligibleMarkup }));
"""
    )

    assert result["blocked"]["state"] == "blocked"
    assert result["unknown"]["state"] == "unknown"
    assert result["eligible"]["state"] == "eligible"
    assert result["calls"] == 0
    assert "Provider route not ready" in result["blockedMarkup"]
    assert "Preview readiness unavailable" in result["unknownMarkup"]
    assert "disabled" in result["blockedMarkup"]
    assert "disabled" in result["unknownMarkup"]
    assert "Ready for manual preview" in result["eligibleMarkup"]
    assert "disabled" not in result["eligibleMarkup"]


def test_confirmation_submit_is_exactly_one_post_and_pending_duplicate_is_ignored():
    result = _run_node(
        """
let calls = [];
let finish;
window.fetch = (url, options) => {
  calls.push({ url, options });
  return new Promise((resolve) => { finish = resolve; });
};
vm.runInContext('manualProviderPreviewState.readiness = "eligible"; manualProviderPreviewState.pendingJobId = "job-a";', context);
const first = hooks.submitManualProviderPreview();
const duplicate = hooks.submitManualProviderPreview();
finish({
  ok: true,
  json: async () => ({
    ok: true,
    status: "manual_provider_preview_ready",
    preview_status: "advisory",
    manual_only: true,
    manual_review_required: true,
    normalized_preview: true,
    suggestions: [{
      suggestion_id: "suggestion-1",
      source_evidence_ids: ["evidence-1"],
      preview_text: "Use grounded evidence.",
      claims: ["Grounded claim"],
      rationale: "Matches the authorized evidence.",
      risk_flags: ["Manual review"],
    }],
    provider_metadata: { provider: "synthetic", model: "qualified-model", fallback_used: false },
    resume_mutation_authorized: false,
    automatic_acceptance_authorized: false,
    application_mutation_authorized: false,
    auto_apply_authorized: false,
    auto_submit_authorized: false,
  }),
});
await Promise.all([first, duplicate]);
const call = calls[0];
console.log(JSON.stringify({
  count: calls.length,
  url: call.url,
  method: call.options.method,
  body: JSON.parse(call.options.body),
}));
"""
    )

    assert result == {
        "count": 1,
        "url": "/api/manual-generate-ai-tailoring-preview-live",
        "method": "POST",
        "body": {
            "pipeline_run_id": "run-a",
            "job_id": "job-a",
            "manual_triggered": True,
            "operator_confirmed": True,
        },
    }


def test_cancel_has_no_post_and_request_body_has_only_server_contract_fields():
    source = _review_js()
    body = _function(
        source,
        "manualProviderPreviewRequestBody",
        "manualProviderPreviewErrorMessage",
    )
    binder = _function(
        source,
        "bindManualProviderPreviewControls",
        "bindAgenticReviewTabs",
    )

    assert set(
        _run_node(
            """
const body = hooks.manualProviderPreviewRequestBody("run-a", "job-a");
console.log(JSON.stringify({ keys: Object.keys(body).sort(), body }));
"""
        )["keys"]
    ) == {"pipeline_run_id", "job_id", "manual_triggered", "operator_confirmed"}
    confirmation = _run_node(
        """
let calls = 0;
window.fetch = async () => { calls += 1; };
vm.runInContext('manualProviderPreviewState.readiness = "eligible";', context);
hooks.openManualProviderPreviewConfirmation({ dataset: { jobId: "job-a" }, focus() {} });
const pendingBeforeCancel = vm.runInContext('manualProviderPreviewState.pendingJobId', context);
hooks.closeManualProviderPreviewConfirmation();
const pendingAfterCancel = vm.runInContext('manualProviderPreviewState.pendingJobId', context);
console.log(JSON.stringify({ calls, pendingBeforeCancel, pendingAfterCancel }));
"""
    )
    assert confirmation == {
        "calls": 0,
        "pendingBeforeCancel": "job-a",
        "pendingAfterCancel": "",
    }
    for forbidden in (
        "owner_user_id",
        "provider:",
        "model:",
        "api_key",
        "credential",
        "resume_text",
        "evidence:",
        "system_prompt",
        "prompt:",
        "routing_override",
        "qualification_override",
    ):
        assert forbidden not in body
    cancel = binder[binder.index('qs("manualProviderPreviewCancelBtn")') :]
    cancel = cancel[: cancel.index('qs("manualProviderPreviewConfirmBtn")')]
    assert "closeManualProviderPreviewConfirmation" in cancel
    assert "submitManualProviderPreview" not in cancel
    assert "window.fetch" not in cancel


def test_success_requires_normalized_status_and_renders_only_safe_review_fields():
    source = _review_js()
    validator = _function(
        source,
        "validateManualProviderPreviewResponse",
        "renderManualProviderPreviewResult",
    )
    renderer = source[
        source.index("function renderManualProviderPreviewResult") :
        source.index("function recommendationExplainerValues")
    ]

    for required in (
        'payload.status !== "manual_provider_preview_ready"',
        'payload.preview_status !== "advisory"',
        "payload.manual_only !== true",
        "payload.manual_review_required !== true",
        "payload.normalized_preview !== true",
    ):
        assert required in validator
    for visible in (
        "Preview · Manual review",
        "AI tailoring suggestions",
        "Evidence IDs",
        "Rationale",
        "Risk flags",
    ):
        assert visible in renderer
    assert "escapeHtml(suggestion.previewText)" in renderer
    assert "escapeHtml(suggestion.rationale)" in renderer
    assert "provider_response_candidate" not in renderer
    assert "JSON.stringify" not in renderer
    for forbidden_control in (
        "Accept all",
        "Apply automatically",
        "Save to resume",
        "Overwrite resume",
        "Submit application",
        "Apply now",
        "Send to ATS",
    ):
        assert forbidden_control not in renderer
    assert "dry-run" not in renderer.lower()

    rendered = _run_node(
        """
const preview = hooks.validateManualProviderPreviewResponse({
  ok: true,
  status: "manual_provider_preview_ready",
  preview_status: "advisory",
  manual_only: true,
  manual_review_required: true,
  normalized_preview: true,
  suggestions: [{
    suggestion_id: "suggestion-1",
    source_evidence_ids: ["evidence-<one>"],
    preview_text: "Grounded <script>preview</script>",
    claims: ["Grounded claim"],
    rationale: "Because <strong>evidence</strong> supports it.",
    risk_flags: ["Review <carefully>"],
  }],
  provider_metadata: { provider: "synthetic", model: "qualified-model", fallback_used: false },
  resume_mutation_authorized: false,
  automatic_acceptance_authorized: false,
  application_mutation_authorized: false,
  auto_apply_authorized: false,
  auto_submit_authorized: false,
  provider_response_candidate: "must-not-render",
  reasoning: "must-not-render",
});
const html = hooks.renderManualProviderPreviewResult({ kind: "success", preview });
console.log(JSON.stringify({ html }));
"""
    )["html"]
    for visible in ("Evidence IDs", "Rationale", "Risk flags", "Preview · Manual review"):
        assert visible in rendered
    assert "&lt;script&gt;preview&lt;/script&gt;" in rendered
    assert "&lt;strong&gt;evidence&lt;/strong&gt;" in rendered
    assert "evidence-&lt;one&gt;" in rendered
    assert "Review &lt;carefully&gt;" in rendered
    assert "must-not-render" not in rendered
    assert "<script>" not in rendered


def test_bounded_errors_do_not_render_raw_backend_details():
    source = _review_js()
    category = _function(
        source,
        "manualProviderPreviewErrorCategory",
        "submitManualProviderPreview",
    )
    renderer = source[
        source.index("function renderManualProviderPreviewResult") :
        source.index("function recommendationExplainerValues")
    ]

    for error_category in (
        "activation_disabled",
        "route_unavailable",
        "credential_not_configured",
        "credential_unavailable",
        "provider_failure",
        "malformed_provider_response",
        "schema_invalid",
        "ungrounded_claim",
        "provider_response_too_large",
    ):
        assert error_category in source
    assert "detail.error_category" in category
    assert "detail.message" not in category
    assert "detail.state" not in category
    assert "stack" not in renderer
    assert "raw" not in renderer.lower()


def test_historical_phase24_through_phase32_readbacks_remain_distinct():
    source = _review_js()

    for marker in (
        "renderManualGenerateAiTailoringPreviewReadbackSection",
        "renderManualGenerateAiTailoringPreviewRequestPacketReadbackSection",
        "renderManualGenerateAiTailoringPreviewDispatchBoundaryReadbackSection",
        "renderManualGenerateAiTailoringPreviewProviderRequestEnvelopeReadbackSection",
        "renderManualGenerateAiTailoringPreviewProviderCallBoundaryReadbackSection",
        "renderManualGenerateAiTailoringPreviewProviderCallDryRunPacketReadbackSection",
        "renderManualGenerateAiTailoringPreviewProviderResponseValidationReadbackSection",
        "renderManualGenerateAiTailoringPreviewProviderResponseNormalizationReadbackSection",
    ):
        assert marker in source
    assert "Manual Generate AI Tailoring Preview Readback" in source
    assert "Live AI tailoring preview for manual review" in source
    assert source.count("/api/manual-generate-ai-tailoring-preview-live") == 1


def test_static_javascript_syntax_is_valid():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for static-JS syntax validation")
    subprocess.run(
        [node, "--check", str(REVIEW_JS_PATH)],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _profile() -> str:
    return PROFILE_UI_PATH.read_text(encoding="utf-8")


def _review_js() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _function(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}")
    end = source.index(f"function {next_name}", start)
    return source[start:end]


def _run_tab_interaction() -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the focused Agentic Review tab interaction test")
    source = _review_js()
    functions = _function(
        source,
        "activateAgenticReviewPanel",
        "bindAgenticReviewTablist",
    ) + _function(
        source,
        "bindAgenticReviewTablist",
        "rerenderManualProviderPreviewWorkspace",
    )
    script = f"""
const vm = require("vm");
const listeners = {{}};
let focused = "";
let fetchCalls = 0;
const classList = (initial = []) => ({{
  values: new Set(initial),
  toggle(name, force) {{ force ? this.values.add(name) : this.values.delete(name); }},
  contains(name) {{ return this.values.has(name); }},
}});
const makeButton = (id, target, active = false) => ({{
  id,
  dataset: {{ agenticTabTarget: target }},
  attributes: {{}},
  classList: classList(active ? ["is-active"] : []),
  setAttribute(name, value) {{ this.attributes[name] = value; }},
  closest(selector) {{ return selector === ".agentic-review-tab" ? this : null; }},
  focus() {{ focused = this.id; }},
}});
const makePanel = (id, hidden = false) => ({{
  id,
  attributes: {{}},
  classList: classList(hidden ? ["hidden"] : []),
  setAttribute(name, value) {{ this.attributes[name] = value; }},
}});
const review = makeButton("review", "agenticReviewAdvisoryTab", true);
const advanced = makeButton("advanced", "agenticReviewAdvancedTab");
const reviewPanel = makePanel("agenticReviewAdvisoryTab");
const advancedPanel = makePanel("agenticReviewAdvancedTab", true);
const tablist = {{
  addEventListener(type, handler) {{ listeners[type] = handler; }},
  querySelectorAll() {{ return [review, advanced]; }},
}};
const document = {{
  querySelector(selector) {{ return selector === ".agentic-review-tabs" ? tablist : null; }},
  querySelectorAll(selector) {{
    if (selector === ".agentic-review-tab") return [review, advanced];
    if (selector === "[data-agentic-tab-panel]") return [reviewPanel, advancedPanel];
    return [];
  }},
}};
const preserved = {{ selectedJobId: "job-b", previewResults: new Map([["job-b", {{ kind: "success" }}]]) }};
const context = {{ document, console, Array, String }};
vm.createContext(context);
vm.runInContext({json.dumps(functions)}, context);
const bind = vm.runInContext("bindAgenticReviewTablist", context);
bind(".agentic-review-tabs", ".agentic-review-tab", "[data-agentic-tab-panel]", "agenticTabTarget");
listeners.click({{ target: advanced }});
const afterAdvanced = {{
  advancedActive: advanced.classList.contains("is-active"),
  reviewHidden: reviewPanel.classList.contains("hidden"),
  advancedHidden: advancedPanel.classList.contains("hidden"),
}};
listeners.click({{ target: review }});
let prevented = false;
listeners.keydown({{ key: "ArrowRight", target: review, preventDefault() {{ prevented = true; }} }});
const afterArrow = {{
  focused,
  prevented,
  reviewSelected: review.attributes["aria-selected"],
  reviewTabindex: review.attributes.tabindex,
  advancedSelected: advanced.attributes["aria-selected"],
  advancedTabindex: advanced.attributes.tabindex,
  reviewAriaHidden: reviewPanel.attributes["aria-hidden"],
  advancedAriaHidden: advancedPanel.attributes["aria-hidden"],
}};
console.log(JSON.stringify({{
  afterAdvanced,
  afterArrow,
  selectedJobId: preserved.selectedJobId,
  previewKind: preserved.previewResults.get("job-b").kind,
  fetchCalls,
}}));
"""
    completed = subprocess.run(
        [node, "-e", script],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_review_and_advanced_are_the_only_primary_modes_and_review_is_default():
    profile = _profile()
    nav = profile[
        profile.index('<nav class="agentic-review-tabs"') :
        profile.index("</nav>", profile.index('<nav class="agentic-review-tabs"'))
    ]

    assert nav.count("data-agentic-tab-target=") == 2
    assert ">Review</button>" in nav
    assert ">Advanced</button>" in nav
    assert all(f">{label}</button>" not in nav for label in (
        "Overview",
        "Review Queue",
        "Agent Trace",
        "Artifacts / Diagnostics",
    ))
    assert 'class="agentic-review-tab is-active" id="agenticReviewReviewTabButton"' in nav
    assert 'aria-selected="true" aria-controls="agenticReviewAdvisoryTab" tabindex="0"' in nav
    assert 'aria-selected="false" aria-controls="agenticReviewAdvancedTab" tabindex="-1"' in nav
    assert profile.index('id="agenticReviewStatusCard"') < profile.index(nav)
    assert 'class="agentic-review-tab-panel" id="agenticReviewAdvisoryTab"' in profile
    assert 'class="agentic-review-tab-panel hidden" id="agenticReviewAdvancedTab"' in profile


def test_review_owns_the_workspace_and_advanced_owns_diagnostic_surfaces_once():
    profile = _profile()
    review_start = profile.index('<section class="agentic-review-tab-panel" id="agenticReviewAdvisoryTab"')
    advanced_start = profile.index('<section class="agentic-review-tab-panel hidden" id="agenticReviewAdvancedTab"')
    review = profile[review_start:advanced_start]
    advanced = profile[advanced_start:profile.index("</main>", advanced_start)]

    for marker in (
        'id="agenticReviewQueuePanel"',
        'id="agenticReviewSelectedJobPanel"',
        "Review Workspace",
    ):
        assert marker in review
        assert marker not in advanced

    for marker in (
        'id="agenticWorkflowSummaryPanel"',
        'id="agenticWorkflowVerificationPanel"',
        'id="agenticReviewTracePanel"',
        'id="agenticReviewDiagnosticsPanel"',
        'id="agenticReviewSourceViews"',
    ):
        assert marker not in review
        assert marker in advanced
        assert profile.count(marker) == 1

    assert advanced.index('id="agenticWorkflowSummaryPanel"') < advanced.index('id="agenticReviewTracePanel"')
    assert advanced.index('id="agenticReviewTracePanel"') < advanced.index('id="agenticReviewDiagnosticsPanel"')
    assert advanced.index('id="agenticReviewDiagnosticsPanel"') < advanced.index('id="agenticReviewSourceViews"')


def test_primary_and_advanced_tabs_have_complete_accessible_relationships():
    profile = _profile()
    source = _review_js()

    for button_id, panel_id in (
        ("agenticReviewReviewTabButton", "agenticReviewAdvisoryTab"),
        ("agenticReviewAdvancedTabButton", "agenticReviewAdvancedTab"),
        ("agenticReviewWorkflowTabButton", "agenticReviewOverviewTab"),
        ("agenticReviewTraceTabButton", "agenticReviewTraceTab"),
        ("agenticReviewDiagnosticsTabButton", "agenticReviewDiagnosticsTab"),
        ("agenticReviewSourceViewsTabButton", "agenticReviewSourceViewsPanel"),
    ):
        assert f'id="{button_id}"' in profile
        assert f'aria-controls="{panel_id}"' in profile
        assert f'id="{panel_id}" role="tabpanel" aria-labelledby="{button_id}"' in profile

    assert 'aria-label="Agentic Review primary views" role="tablist"' in profile
    assert 'aria-label="Advanced inspection views" role="tablist"' in profile
    assert '"ArrowLeft", "ArrowRight"' in source
    assert 'button.setAttribute("tabindex", isActive ? "0" : "-1")' in source
    assert 'panel.setAttribute("aria-hidden", isActive ? "false" : "true")' in source


def test_mode_switching_and_arrow_navigation_preserve_frontend_review_state():
    result = _run_tab_interaction()

    assert result == {
        "afterAdvanced": {
            "advancedActive": True,
            "reviewHidden": True,
            "advancedHidden": False,
        },
        "afterArrow": {
            "focused": "advanced",
            "prevented": True,
            "reviewSelected": "false",
            "reviewTabindex": "-1",
            "advancedSelected": "true",
            "advancedTabindex": "0",
            "reviewAriaHidden": "true",
            "advancedAriaHidden": "false",
        },
        "selectedJobId": "job-b",
        "previewKind": "success",
        "fetchCalls": 0,
    }


def test_advanced_progressive_disclosure_preserves_renderers_preview_and_safety():
    profile = _profile()
    source = _review_js()
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    tab_start = source.index("function activateAgenticReviewPanel")
    tab_end = source.index("function rerenderManualProviderPreviewWorkspace", tab_start)
    tab_logic = source[tab_start:tab_end]

    assert 'data-agentic-advanced-target="agenticReviewOverviewTab">Workflow' in profile
    assert 'data-agentic-advanced-target="agenticReviewTraceTab">Agent Trace' in profile
    assert 'data-agentic-advanced-target="agenticReviewDiagnosticsTab">Diagnostics' in profile
    assert 'data-agentic-advanced-target="agenticReviewSourceViewsPanel">Source Views' in profile
    assert '<details class="agentic-review-source-views" id="agenticReviewSourceViews">' in profile
    assert " open" not in profile[profile.index('id="agenticReviewSourceViews"') - 70:profile.index('id="agenticReviewSourceViews"') + 60]

    for marker in (
        "renderAgenticReviewQueueWorkspace",
        "renderAgenticReviewSelectedJobSummary",
        "renderAgenticReviewAdvisoryPanel",
        "renderAgenticReviewDiagnosticsPanel",
        "renderAgentTraceReadOnlyPanel",
        "submitManualProviderPreview",
        "MANUAL_PROVIDER_PREVIEW_ENDPOINT",
        'href="${AGENTIC_REVIEW_PLANNING_PATH}"',
    ):
        assert marker in source

    for marker in (
        "window.fetch",
        "fetchJson(",
        "localStorage",
        "/application-actions",
        'method: "POST"',
        'method: "PUT"',
        'method: "PATCH"',
        'method: "DELETE"',
        "queue_mutation",
        "resume_mutation",
        "application_mutation",
        "approval_mutation",
        "consensus",
    ):
        assert marker not in tab_logic

    assert 'href="/tailoring' not in source
    assert 'href="/tailoring' not in profile

    for marker in (
        ".agentic-review-advanced-shell",
        ".agentic-review-advanced-tabs",
        ".agentic-review-advanced-tab.is-active",
        ".agentic-review-advanced-panel.hidden",
        "@media (max-width: 560px)",
    ):
        assert marker in css

from __future__ import annotations

from pathlib import Path

from tests.test_item6b65c_extended_trace_diagnostics_master_detail import (
    EXPECTED_DIAGNOSTIC_RENDERERS,
    _diagnostic_registry,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
UI_SHELL_PATH = ROOT / "src/app/ui_shell.py"


def _profile() -> str:
    return PROFILE_UI_PATH.read_text(encoding="utf-8")


def _css() -> str:
    return REVIEW_CSS_PATH.read_text(encoding="utf-8")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _header() -> str:
    profile = _profile()
    start = profile.index(
        '<header class="page-header app-page-header agentic-review-header">'
    )
    return profile[start : profile.index("</header>", start)]


def _css_rule(css: str, selector: str) -> str:
    start = css.index(selector)
    return css[start : css.index("}", start) + 1]


def test_back_route_label_and_visible_arrow_cue_are_preserved():
    header = _header()
    link_start = header.index(
        '<a class="agentic-review-back-link" href="/profile?tab=pipeline-runs">'
    )
    icon = header.index(
        '<span class="agentic-review-back-link__icon" aria-hidden="true">←</span>',
        link_start,
    )
    label = header.index("<span>Back to pipeline runs</span>", icon)
    link_end = header.index("</a>", label)

    assert link_start < icon < label < link_end
    assert "Back to tailoring" not in header
    assert "/tailoring" not in header


def test_back_navigation_is_owned_by_left_page_header_content_not_detached_actions():
    header = _header()
    main = header.index('<div class="app-page-header__main">')
    back = header.index('class="agentic-review-back-link"')
    title = header.index('class="app-page-header__title-row"')
    subtitle = header.index('id="agenticReviewSubtitle"')

    assert main < back < title < subtitle
    assert "app-page-header__actions" not in header
    assert "header-actions" not in header

    css = _css()
    header_rule = _css_rule(
        css,
        "body .agentic-review-page.page > .agentic-review-header.app-page-header {",
    )
    assert "display: flex !important" in header_rule
    assert "flex-direction: column !important" in header_rule
    assert "gap: 0 !important" in header_rule
    assert "position: absolute" not in header_rule
    assert "position: fixed" not in header_rule
    assert ".agentic-review-header .app-page-header__actions" not in css


def test_back_navigation_uses_compact_accent_secondary_visual_contract():
    css = _css()
    back_rule = _css_rule(css, ".agentic-review-header .agentic-review-back-link {")
    hover_rule = _css_rule(css, ".agentic-review-header .agentic-review-back-link:hover {")

    assert "display: inline-flex !important" in back_rule
    assert "align-self: flex-start" in back_rule
    assert "min-height: 32px !important" in back_rule
    assert "padding: 6px 10px" in back_rule
    assert "var(--app-primary) 42%" in back_rule
    assert "var(--app-primary) 10%" in back_rule
    assert "font-weight: 700" in back_rule
    assert "box-shadow: none !important" in back_rule
    assert "linear-gradient" not in back_rule

    assert "var(--app-primary) 68%" in hover_rule
    assert "var(--app-primary) 16%" in hover_rule
    assert ".agentic-review-header .agentic-review-back-link:focus-visible" in css
    assert "outline: 3px solid var(--app-focus) !important" in css


def test_agentic_review_stylesheet_cache_key_loads_the_placement_fix():
    profile = _profile()

    assert (
        '<link rel="stylesheet" '
        'href="/static/agentic_review.css?v=item6c3_back_navigation_r1" />'
        in profile
    )
    assert "agentic_review.css?v=item6b65a_queue_usability_r1" not in profile
    assert "agentic_review.js?v=item6b65a_queue_usability_r1" not in profile
    assert '<script src="/static/agentic_review.js?v=item6_final_agentic_review_r1"></script>' in profile


def test_global_shell_controls_and_destinations_remain_unchanged():
    shell = UI_SHELL_PATH.read_text(encoding="utf-8")

    for marker in (
        'id="notificationButton"',
        'id="themeToggleBtn"',
        'class="app-shell-primary-link"',
        'href="/scan-workspace"',
        'aria-label="New Scan"',
        'id="profileMenuButton"',
        'class="profile-avatar-btn"',
    ):
        assert marker in shell


def test_item6_architecture_and_presentation_only_safety_are_preserved():
    profile = _profile()
    source = _source()
    registry = _diagnostic_registry()

    for marker in (
        'data-agentic-tab-target="agenticReviewAdvisoryTab">Review</button>',
        'data-agentic-tab-target="agenticReviewAdvancedTab">Advanced</button>',
        'id="agenticReviewStatusCard"',
        'id="agenticReviewQueuePanel"',
        'id="agenticReviewSelectedJobPanel"',
    ):
        assert marker in profile

    assert 'class="agent-trace-master-detail"' in source
    assert 'class="agent-trace-diagnostic-workspace"' in source
    assert len(EXPECTED_DIAGNOSTIC_RENDERERS) == 77
    assert sum(registry.count(f"{renderer}(") for renderer in EXPECTED_DIAGNOSTIC_RENDERERS) == 77
    assert "renderManualProviderPreviewAction" in source
    assert "/application-actions" not in source
    assert ".checked = true" not in source

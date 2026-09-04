"""Focused contracts for the shared matte-eucalyptus action and shell release."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
LEGACY_CSS = (ROOT / "src/app/static/styles.css").read_text(encoding="utf-8")
EXECUTIVE_CSS = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
RELEASE_MARKER = "eucalyptus_primary_shell_r1"
ACTION_RELEASE_MARKER = "eucalyptus_action_cascade_r2"


def _rule(signature: str, source: str = APP_CSS) -> str:
    return source.split(signature, 1)[1].split("}", 1)[0]


def _last_rule(signature: str, source: str = APP_CSS) -> str:
    return source.rsplit(signature, 1)[1].split("}", 1)[0]


def _contrast_with_white(hex_color: str) -> float:
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    return 1.05 / (luminance + 0.05)


def test_approved_light_and_dark_eucalyptus_action_tokens_are_authoritative() -> None:
    for declaration in (
        "--app-action-primary: #56746d",
        "--app-action-hover: #49655f",
        "--app-action-pressed: #3f5953",
        "--app-action-soft: #edf2f0",
        "--app-action-soft-hover: #e4ece9",
        "--app-action-border: #c9d6d2",
        "--app-action-strong: #36534c",
        "--app-action-focus: rgba(86, 116, 109, 0.2)",
        "--app-action-primary: #526a64",
        "--app-action-hover: #5b776f",
    ):
        assert declaration in APP_CSS


def test_filled_action_base_and_hover_colors_keep_normal_text_contrast() -> None:
    root = _rule(":root,\nhtml[data-theme=\"dark\"] {")
    light = _rule('html[data-theme="light"] {')
    for theme in (root, light):
        for token in ("primary", "hover", "pressed"):
            match = re.search(rf"--app-action-{token}: (#[0-9a-f]{{6}})", theme)
            assert match is not None
            assert _contrast_with_white(match.group(1)) >= 4.5


def test_shared_primary_cta_has_solid_eucalyptus_interaction_states() -> None:
    base = _rule(".primary-btn,\n.btn-primary,\n.app-shell-primary-link {")
    hover = _rule(
        ".primary-btn:not(:disabled):hover,\n"
        ".btn-primary:not(:disabled):hover,\n"
        '.app-shell-primary-link:not([aria-disabled="true"]):hover {'
    )
    pressed = _rule(
        ".primary-btn:not(:disabled):active,\n"
        ".btn-primary:not(:disabled):active,\n"
        '.app-shell-primary-link:not([aria-disabled="true"]):active {'
    )
    focus = _rule(
        ".primary-btn:focus-visible,\n"
        ".btn-primary:focus-visible,\n"
        ".app-shell-primary-link:focus-visible,"
    )

    assert "background: var(--app-action-primary) !important" in base
    assert "background: var(--app-action-hover) !important" in hover
    assert "background: var(--app-action-pressed) !important" in pressed
    assert "outline: 3px solid var(--app-action-focus) !important" in focus
    for block in (base, hover, pressed):
        assert "background-image: none !important" in block
        assert "linear-gradient" not in block
        for old_primary in ("#2563eb", "#4f46e5", "#7c3aed", "var(--app-violet)"):
            assert old_primary not in block


def test_disabled_shared_primary_controls_are_neutral_not_action_colored() -> None:
    disabled = _rule(
        ".primary-btn:disabled,\n"
        ".btn-primary:disabled,\n"
        '.app-shell-primary-link[aria-disabled="true"] {'
    )
    assert "background: var(--app-action-disabled-bg) !important" in disabled
    assert "border-color: var(--app-action-disabled-border) !important" in disabled
    assert "color: var(--app-action-disabled-text) !important" in disabled
    assert "opacity: 1 !important" in disabled


def test_new_scan_and_binary_active_controls_use_the_shared_action_tokens() -> None:
    new_scan = _rule(
        ".app-shell-top-right:not(.app-shell-top-right--flow) .app-shell-primary-link {"
    )
    binary = _rule(".binary-toggle-option input:checked + span {")
    binary_hover = _rule(".binary-toggle-option input:checked + span:hover {")

    assert "background: var(--app-action-primary) !important" in new_scan
    assert "background-image: none !important" in new_scan
    assert "background: var(--app-action-primary) !important" in binary
    assert "border-color: var(--app-action-primary) !important" in binary
    assert "background: var(--app-action-hover) !important" in binary_hover


def test_semantic_and_approved_component_scoped_controls_remain_intact() -> None:
    danger = _last_rule("#resumeDeleteModal .profile-resume-delete-action {")
    warning = _rule(
        "#advancedDiagnosticsReviewDialog .advanced-diagnostics-dialog-action--warning {",
        EXECUTIVE_CSS,
    )
    bulk = _rule(
        "#planningWorklistRoot .planning-react-bulk-generate {",
        EXECUTIVE_CSS,
    )

    assert "background: #a95757 !important" in danger
    assert "background: var(--diag-warning-soft) !important" in warning
    assert "background: #d3e8e2" in bulk
    assert ":not(.planning-react-bulk-generate)" in APP_CSS


def test_component_owned_segmented_states_use_shared_eucalyptus_tokens() -> None:
    for signature in (
        ".planning-react-segmented button.is-active {",
        ".executive-queue-segmented button.is-active {",
        ".executive-queue-view-toggle button.is-active {",
        ".applications-tabs .applications-tab.is-active {",
        ".scheduler-runs-tabs .scheduler-runs-tab.is-active {",
    ):
        active = _rule(signature, EXECUTIVE_CSS)
        assert "var(--app-action-primary" in active
        assert "background-image: none" in active
        assert "linear-gradient" not in active


def test_component_primary_fallbacks_share_the_same_action_token() -> None:
    executive_apply = _rule(".executive-queue-apply-btn {", EXECUTIVE_CSS)
    pipeline_primary = _rule(
        ".pipeline-dashboard-btn--primary,\n"
        ".pipeline-status-error button,\n"
        ".pipeline-idle-banner button {",
        EXECUTIVE_CSS,
    )
    operational_apply = _rule(
        ".operational-filter-actions .operational-primary-action {",
        EXECUTIVE_CSS,
    )
    pipeline_confirm = _rule("#confirmPipelineRunBtn {")

    for primary in (
        executive_apply,
        pipeline_primary,
        operational_apply,
        pipeline_confirm,
    ):
        assert "var(--app-action-primary" in primary
        assert "background-image: none" in primary
        assert "linear-gradient" not in primary


def test_legacy_high_specificity_primary_ids_delegate_to_action_tokens() -> None:
    base = LEGACY_CSS.split("/* Legacy ID aliases", 1)[1].split("}", 1)[0]
    hover = LEGACY_CSS.split("#runPipelineBtn:hover,", 1)[1].split("}", 1)[0]
    pressed = LEGACY_CSS.split("#runPipelineBtn:active:not(:disabled),", 1)[1].split("}", 1)[0]
    focus = LEGACY_CSS.split("#runPipelineBtn:focus-visible,", 1)[1].split("}", 1)[0]

    for control_id in (
        "#runPipelineBtn",
        "#planningApplyFiltersBtn",
        "#decisionApplyFiltersBtn",
        "#applicationApplyFiltersBtn",
    ):
        assert control_id in base
    assert "var(--app-action-primary, #56746d)" in base
    assert "var(--app-action-hover, #49655f)" in hover
    assert "var(--app-action-pressed, #3f5953)" in pressed
    assert "var(--app-action-focus, rgba(86, 116, 109, 0.2))" in focus
    for block in (base, hover, pressed):
        assert "background-image: none !important" in block
        assert "var(--app-primary)" not in block


def test_react_secondary_actions_use_the_shared_neutral_exclusion_contract() -> None:
    planning = (ROOT / "frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(
        encoding="utf-8"
    )
    pipeline = (
        ROOT / "frontend/executive-kpi/src/pipeline/PipelineDashboard.tsx"
    ).read_text(encoding="utf-8")
    assert "`${SHARED_NEUTRAL_CONTROL_CLASS} planning-filter-clear`" in planning
    assert "`${SHARED_NEUTRAL_CONTROL_CLASS} pipeline-dashboard-btn pipeline-dashboard-btn--secondary`" in pipeline

    neutral = _rule(".preferences-secondary-action {", EXECUTIVE_CSS)
    assert "background: var(--queue-surface-strong)" in neutral
    assert "border: 1px solid var(--queue-border-strong)" in neutral
    assert "background-image: none" in neutral


def test_filter_action_rows_share_height_and_clear_icon_contract() -> None:
    planning = (ROOT / "frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(encoding="utf-8")
    operational = (ROOT / "frontend/executive-kpi/src/OperationalDashboards.tsx").read_text(encoding="utf-8")
    executive = (ROOT / "frontend/executive-kpi/src/ExecutiveQueue.tsx").read_text(encoding="utf-8")

    assert "<RotateCcw size={15} aria-hidden=\"true\" /> Clear" in planning
    assert operational.count("<RotateCcw size={15} aria-hidden=\"true\" /> Clear") == 2
    assert "<RotateCcw size={15} aria-hidden=\"true\" /> Clear" in executive
    for signature in (
        ".executive-queue-filter-actions button {",
        ".planning-react-filter-actions button {",
        ".operational-filter-actions button {",
    ):
        assert "min-height: var(--filter-control-height)" in _rule(signature, EXECUTIVE_CSS)


def test_shared_filter_control_sizing_tokens_are_defined_once() -> None:
    tokens = _rule(":root {", EXECUTIVE_CSS)
    assert "--filter-control-height: 46px" in tokens
    assert "--filter-control-radius: 12px" in tokens
    assert "--filter-control-font-size: 14px" in tokens
    assert "--filter-control-font-weight: 650" in tokens
    assert EXECUTIVE_CSS.count("--filter-control-height:") == 1


def test_every_filter_row_field_resolves_to_the_shared_control_height() -> None:
    """Selects, text/number inputs and segmented toggles share the button height."""
    for signature in (
        ".shared-filter-select__trigger {",
        ".planning-react-limit-field input {",
        ".executive-queue-limit-field input {",
        ".planning-react-segmented {",
        ".executive-queue-segmented {",
    ):
        rule = _rule(signature, EXECUTIVE_CSS)
        assert "height: var(--filter-control-height)" in rule, signature
        assert "border-radius: var(--filter-control-radius)" in rule, signature

    operational_input = _rule(".operational-filter-grid input {", EXECUTIVE_CSS)
    assert "height: var(--filter-control-height)" in operational_input
    assert "border-radius: var(--filter-control-radius)" in operational_input

    for stale in ("height: 50px", "height: 44px"):
        assert stale not in _rule(".planning-react-segmented {", EXECUTIVE_CSS)


def test_filter_row_sizing_owner_outranks_both_legacy_high_specificity_owners() -> None:
    """The global 34px button rule and the global 8px input rule both used
    !important; one scoped owner re-points filter rows at the shared contract."""
    owner = APP_CSS.split("filter_control_height_r1", 1)[1]
    fields = owner.split("body .planning-react-limit-field input", 1)[1].split("}", 1)[0]
    actions = owner.split("body #planningApplyFiltersBtn", 1)[1].split("}", 1)[0]

    assert "min-height: var(--filter-control-height, 46px) !important" in fields
    assert "border-top-left-radius: var(--filter-control-radius, 12px) !important" in fields

    for control_id in ("#decisionApplyFiltersBtn", "#applicationApplyFiltersBtn"):
        assert control_id in actions
    for container in (
        ".planning-react-filter-actions > button",
        ".operational-filter-actions > button",
        ".executive-queue-filter-actions > button",
    ):
        assert container in actions
    assert "min-height: var(--filter-control-height, 46px) !important" in actions
    assert "font-size: var(--filter-control-font-size, 14px) !important" in actions

    # the global sizing rule now excludes the three Apply Filters owners
    global_sizing = APP_CSS.split("body .ghost-btn,\nbody .btn-sm {")
    assert len(global_sizing) == 3
    for selector_text in global_sizing[:-1]:
        selector_text = selector_text.rsplit("body button", 1)[-1]
        for excluded in (
            ":not(.planning-filter-apply)",
            ":not(.operational-primary-action)",
            ":not(.executive-queue-apply-btn)",
        ):
            assert excluded in selector_text


def test_shared_table_utility_controls_keep_their_compact_sizing() -> None:
    """preferences-secondary-action is shared with small table controls, so the
    46px filter contract must never be attached to the bare class."""
    neutral = _rule(".preferences-secondary-action {", EXECUTIVE_CSS)
    assert "--filter-control-height" not in neutral
    assert "min-height" not in neutral

    for signature, expected in (
        (".shared-table-sort-btn {", "min-height: 24px"),
        (".shared-table-expand-btn {", "min-height: 28px"),
        (".shared-info-popover__trigger {", "min-height: 20px"),
    ):
        assert expected in _rule(signature, EXECUTIVE_CSS), signature

    pagination = _rule(
        ".shared-table-pagination button,\n.shared-table-error button,\n.planning-react-empty button {",
        EXECUTIVE_CSS,
    )
    assert "min-height: 34px" in pagination

    owner = APP_CSS.split("filter_control_height_r1", 1)[1].split("\n}\n", 2)
    joined = "".join(owner[:2])
    for utility in (
        "shared-table-sort-btn",
        "shared-table-expand-btn",
        "shared-info-popover__trigger",
        "shared-table-pagination",
    ):
        assert utility not in joined


def test_filter_action_callbacks_and_payloads_are_unchanged() -> None:
    planning = (ROOT / "frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(encoding="utf-8")
    operational = (ROOT / "frontend/executive-kpi/src/OperationalDashboards.tsx").read_text(encoding="utf-8")
    executive = (ROOT / "frontend/executive-kpi/src/ExecutiveQueue.tsx").read_text(encoding="utf-8")

    assert 'publishPlanningAction({ type: "apply_filters", filters })' in planning
    assert 'publishPlanningAction({ type: "clear_filters" })' in planning
    assert operational.count('{ type: "apply_filters", filters }') == 2
    assert operational.count('{ type: "clear_filters" }') >= 2
    assert 'publishQueueAction({ type: "apply_filters", filters })' in executive
    assert 'publishQueueAction({ type: "clear_filters" })' in executive

    # the empty-state control keeps its own label and is not folded into the
    # filter-bar Clear contract
    assert ">Clear Filters</button>" in executive


def test_empty_state_clear_filters_is_not_converted_to_the_filter_bar_contract() -> None:
    executive = (ROOT / "frontend/executive-kpi/src/ExecutiveQueue.tsx").read_text(encoding="utf-8")
    empty_state = executive.split('className={NEUTRAL_CONTROL_CLASS}', 1)[1].split(">", 2)
    assert "RotateCcw" not in "".join(empty_state[:2])
    assert "executive-queue-clear-btn" not in "".join(empty_state[:2])


def test_every_real_host_busts_both_changed_shared_assets_consistently() -> None:
    hosts = tuple((ROOT / "src/app").glob("*_ui.py")) + (ROOT / "src/app/ui.py",)
    seen_app_css = 0
    seen_shell_js = 0
    seen_bundle_css = 0
    seen_bundle_js = 0

    for host in hosts:
        source = host.read_text(encoding="utf-8")
        if "/static/app_redesign.css?v=" in source:
            seen_app_css += source.count("/static/app_redesign.css?v=")
            assert source.count(f"/static/app_redesign.css?v={RELEASE_MARKER}") == source.count(
                "/static/app_redesign.css?v="
            )
        if "/static/shell.js?v=" in source:
            seen_shell_js += source.count("/static/shell.js?v=")
            assert source.count(f"/static/shell.js?v={RELEASE_MARKER}") == source.count(
                "/static/shell.js?v="
            )
        for asset, counter_name in (
            ("/static/build/executive-kpi/executive-kpi.css?v=", "css"),
            ("/static/build/executive-kpi/executive-kpi.js?v=", "js"),
        ):
            if asset not in source:
                continue
            assert (
                source.count(f"{asset}{RELEASE_MARKER}")
                + source.count(f"{asset}{ACTION_RELEASE_MARKER}")
                == source.count(asset)
            )
            if counter_name == "css":
                seen_bundle_css += source.count(asset)
            else:
                seen_bundle_js += source.count(asset)

    assert seen_app_css == 18
    assert seen_shell_js == 16
    assert seen_bundle_css == 8
    assert seen_bundle_js == 8


def test_affected_action_hosts_use_fresh_styles_and_bundle_markers() -> None:
    """Every host that renders a control the legacy ID map restyles serves the
    post-change styles.css, and the shared bundle keeps one marker everywhere."""
    affected = (
        ROOT / "src/app/ui.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/decisions_ui.py",
        ROOT / "src/app/application_hub_ui.py",
    )
    sources = tuple(path.read_text(encoding="utf-8") for path in affected)
    # ui.py, planning (x2: planning + scan workspace), decisions, applications
    assert sum(source.count(f"styles.css?v={ACTION_RELEASE_MARKER}") for source in sources) == 5

    scan_workspace = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
    scan_route = scan_workspace.split("def scan_workspace(", 1)[1]
    assert 'id="scanWorkspaceProcessingOkBtn"' in scan_route
    assert f"styles.css?v={ACTION_RELEASE_MARKER}" in scan_route.split("</head>", 1)[0]

    for asset in ("executive-kpi.css", "executive-kpi.js"):
        for source in sources:
            assert f"{asset}?v={ACTION_RELEASE_MARKER}" not in source
        assert sum(source.count(f"{asset}?v={RELEASE_MARKER}") for source in sources) == 8

"""Focused contracts for the Saved Scans library surface (/profile/saved-scans).

Presentation-only changeover: the route, the data endpoint, the open-report
contract and the delete lifecycle are all asserted to be unchanged.
"""

import re
from pathlib import Path

from src.app.profile_ui import saved_scans_page


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
PROFILE_JS = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
APP_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
CSS_MARKER = "saved_scans_library_r1"


def _html() -> str:
    return saved_scans_page()


def _fn(name: str) -> str:
    """Slice one top-level function body out of profile.js."""
    start = PROFILE_JS.index(f"function {name}(")
    tail = PROFILE_JS[start:]
    end = tail.index("\n}\n")
    return tail[: end + 2]


def _scans_css() -> str:
    return APP_CSS.split(CSS_MARKER, 1)[1]


# --- 1-2. route and data contract -------------------------------------------


def test_saved_scans_route_and_data_endpoint_are_unchanged() -> None:
    assert '@router.get("/profile/saved-scans", response_class=HTMLResponse)' in PROFILE_UI
    assert "def saved_scans_page() -> str:" in PROFILE_UI

    html = _html()
    assert "<h1>Saved Scans</h1>" in html
    assert "Review New Scan reports generated from submitted resumes and job descriptions." in html

    assert 'fetchJson("/profile/saved-scans/data?limit=50")' in PROFILE_JS
    assert PROFILE_JS.count("/profile/saved-scans/data") == 1


# --- 3-5. the eight-column table --------------------------------------------


def test_table_renders_exactly_the_eight_approved_columns() -> None:
    html = _html()
    head = html.split("<thead>", 1)[1].split("</thead>", 1)[0]

    assert head.count("<th>") + head.count("<th ") == 8
    for column in ("Scanned", "Company", "Role", "Resume", "Source", "Status", "Match"):
        assert f"<th>{column}</th>" in head
    assert '<th class="saved-scans-actions-head">Actions</th>' in head


def test_old_action_column_and_blank_delete_column_are_gone() -> None:
    html = _html()
    head = html.split("<thead>", 1)[1].split("</thead>", 1)[0]

    assert "<th>Action</th>" not in head
    assert "<th></th>" not in head
    assert 'colspan="8"' in html
    assert 'colspan="9"' not in html
    assert "saved-scan-row-delete-cell" not in PROFILE_JS


def test_action_badge_presentation_is_removed_from_rendered_rows() -> None:
    row = _fn("savedScanRowHtml")
    assert "saved-scan-action-badge" not in row
    assert "saved-scan-status-badge" not in row
    # the underlying status metadata is still consulted
    assert "savedScanStatusMeta(scan.scan_status)" in row
    # ...and the pastel per-status row tint is gone
    assert "saved-scan-row-${" not in row


# --- 6-8. open report contract ----------------------------------------------


def test_open_report_uses_the_existing_helper_and_route() -> None:
    row = _fn("savedScanRowHtml")
    helper = _fn("getSavedScanOpenHref")

    assert "getSavedScanOpenHref(scan)" in row
    assert 'status !== "ready" && status !== "complete"' in helper
    assert "/scan-workspace?saved_scan_id=${encodeURIComponent(scanId)}" in helper
    # no second navigation path was invented
    assert PROFILE_JS.count("saved_scan_id=") == 1
    assert "/profile/saved-scans/" not in row


def test_ready_scans_stay_openable_and_others_stay_non_openable() -> None:
    row = _fn("savedScanRowHtml")
    openable = row.split("const openAction = openHref", 1)[1]
    ready, unavailable = openable.split(": `<button", 1)

    assert 'href="${escapeHtml(openHref)}"' in ready
    assert 'aria-label="Open saved scan report"' in ready

    # the non-openable branch is a disabled control, never a dead link
    assert "disabled" in unavailable
    assert 'aria-disabled="true"' in unavailable
    assert 'aria-label="Report unavailable"' in unavailable
    assert "href=" not in unavailable


# --- 9-11. delete lifecycle --------------------------------------------------


def test_delete_keeps_its_binding_confirmation_and_endpoint() -> None:
    row = _fn("savedScanRowHtml")
    assert 'data-saved-scan-delete="${escapeHtml(scan.scan_id || "")}"' in row
    assert "data-saved-scan-name=" in row
    assert 'aria-label="Delete saved scan"' in row

    binding = PROFILE_JS.split("function bindSavedScansPage()", 1)[1]
    assert 'event.target.closest("[data-saved-scan-delete]")' in binding
    assert "openSavedScanDeleteModal(scan)" in binding
    # the row click handler never deletes directly
    assert "deleteSavedScan()" not in binding.split("savedScanDeleteConfirmBtn", 1)[0]

    delete_fn = _fn("deleteSavedScan")
    assert "`/profile/saved-scans/${encodeURIComponent(scanId)}`" in delete_fn
    assert 'method: "DELETE"' in delete_fn
    assert "closeSavedScanDeleteModal()" in delete_fn
    assert "await loadSavedScans()" in delete_fn

    assert "savedScanDeleteModal" in _html()


# --- 12-15. client-side search ----------------------------------------------


def test_search_is_client_side_only_and_never_calls_the_api() -> None:
    binding = PROFILE_JS.split("function bindSavedScansPage()", 1)[1].split("\n}\n", 1)[0]
    handler = binding.split('searchInput.addEventListener("input"', 1)[1].split("});", 1)[0]

    assert "paintSavedScans(" in handler
    for network in ("fetchJson", "fetch(", "loadSavedScans", "?limit=", "XMLHttpRequest"):
        assert network not in handler


def test_search_matches_company_role_resume_source_and_status() -> None:
    haystack = _fn("savedScanSearchHaystack")
    for field in (
        "scan?.job_company",
        "scan?.job_title",
        "scan?.resume_name",
        "scan?.resume_filename",
        "normalizeSavedScanSource(scan?.resume_source)",
        "savedScanStatusMeta(scan?.scan_status).label",
        "scan?.scan_id",
    ):
        assert field in haystack
    assert ".toLowerCase()" in haystack
    # backend-only review payloads are never searched
    assert "review" not in haystack
    assert "payload" not in haystack

    assert "includes(needle)" in _fn("filterSavedScans")


def test_zero_result_search_has_its_own_empty_state() -> None:
    paint = _fn("paintSavedScans")
    assert "No saved scans yet." in paint
    assert "No saved scans match this search." in paint

    empty_branch = paint.split("if (!scans.length)", 1)[1]
    no_scans, no_matches = empty_branch.split("if (!visible.length)", 1)
    assert "No saved scans yet." in no_scans
    assert "No saved scans match this search." not in no_scans
    assert "No saved scans match this search." in no_matches


def test_meta_text_reports_filtered_and_total_counts() -> None:
    meta = _fn("savedScansMetaText")
    assert "${visibleCount} of ${label}" in meta
    assert "saved scan${totalCount === 1" in meta
    assert "shown" not in meta


# --- 16. refresh -------------------------------------------------------------


def test_refresh_still_calls_the_existing_load_path() -> None:
    html = _html()
    assert 'id="refreshSavedScansBtn"' in html
    assert "saved-scans-refresh-btn" in html

    binding = PROFILE_JS.split("function bindSavedScansPage()", 1)[1]
    refresh = binding.split('refreshBtn.addEventListener("click"', 1)[1].split("});", 1)[0]
    assert "loadSavedScans()" in refresh
    # the loader repaints through the same filter, so the query survives refresh
    assert "paintSavedScans({ ok, error })" in _fn("renderSavedScans")


# --- 17-19. status and match -------------------------------------------------


def test_status_uses_a_compact_dot_plus_label_with_text() -> None:
    row = _fn("savedScanRowHtml")
    assert 'class="saved-scan-status is-${escapeHtml(statusMeta.tone)}"' in row
    assert 'class="saved-scan-status-dot" aria-hidden="true"' in row
    assert "${escapeHtml(statusMeta.label)}" in row

    css = _scans_css()
    assert ".saved-scan-status.is-ready" in css
    assert "#edf7f3" in css
    assert "#cbe4db" in css
    assert "#1f9d78" in css
    assert "#27665a" in css

    # savedScanStatusMeta classification itself is untouched
    meta = _fn("savedScanStatusMeta")
    assert 'status === "ready" || status === "complete"' in meta
    assert 'tone: "ready"' in meta
    assert 'tone: "failed"' in meta


def test_match_keeps_the_stored_score_and_only_adds_a_visual_bar() -> None:
    row = _fn("savedScanRowHtml")
    assert "formatPercent(scan.match_rate)" in row
    assert "savedScanMatchBarWidth(scan.match_rate)" in row
    assert "${escapeHtml(scoreText)}" in row
    assert 'aria-label="${escapeHtml(matchLabel)}"' in row

    bar = _fn("savedScanMatchBarWidth")
    # the bar is clamped for layout only; nothing rescales or recomputes
    assert "Math.max(0, Math.min(100, number))" in bar
    assert "return null" in bar
    assert "*" not in bar and "/" not in bar

    assert "#e7ecea" in _scans_css()
    assert "#56746d" in _scans_css()


# --- 20-21. two direct row actions -------------------------------------------


def test_exactly_two_direct_row_actions_and_no_overflow_menu() -> None:
    row = _fn("savedScanRowHtml")
    assert row.count("saved-scan-action-btn") >= 2
    assert "saved-scan-action-btn--open" in row
    assert "saved-scan-action-btn--delete" in row

    for overflow in (
        "data-saved-scan-menu",
        "saved-scan-overflow",
        "aria-haspopup",
        "&hellip;",
        "More actions",
        "…",
    ):
        assert overflow not in row
    assert "..." not in row.split("const openAction", 1)[0]


def test_row_action_controls_have_accessible_names_and_one_tooltip_source() -> None:
    row = _fn("savedScanRowHtml")
    for name in (
        'aria-label="Open saved scan report"',
        'aria-label="Report unavailable"',
        'aria-label="Delete saved scan"',
    ):
        assert name in row
    # native title is the only tooltip mechanism on this page
    assert 'title="Open report"' in row
    assert 'title="Report unavailable"' in row
    assert 'title="Delete saved scan"' in row
    assert "data-tooltip" not in row


# --- 22. storage disclosure ---------------------------------------------------


def test_storage_disclosure_is_preserved_but_no_longer_a_full_width_banner() -> None:
    html = _html()
    assert "New Scan rows now store the generated match score and review payload in Postgres." in html
    assert 'class="saved-scans-storage-note"' in html
    assert 'class="saved-scans-note"' not in html

    note = _scans_css().split(".saved-scans-storage-note {", 1)[1].split("}", 1)[0]
    assert "display: inline-flex" in note
    assert "font-size: 11.5px" in note
    assert "var(--scans-muted)" in note
    assert "background" not in note


# --- visual system ------------------------------------------------------------


def test_saved_scans_surface_is_neutral_eucalyptus_without_blue_or_zebra() -> None:
    css = _scans_css()

    for rejected in (
        "#2563eb",
        "#1d4ed8",
        "#7c3aed",
        "#4f46e5",
        "#6d3df2",
        "#93c5fd",
        "#a78bfa",
        "linear-gradient",
    ):
        assert rejected not in css, rejected

    # zebra banding is explicitly neutralised rather than merely unset
    zebra = css.split("tbody tr:nth-child(even) td", 1)[1].split("}", 1)[0]
    assert "var(--scans-surface) !important" in zebra

    tokens = css.split(".profile-saved-scans-section {", 1)[1].split("}", 1)[0]
    assert "--scans-accent: #56746d" in tokens
    assert "--scans-accent-hover: #49655f" in tokens
    assert "--scans-accent-soft: #edf2f0" in tokens
    assert "--scans-accent-border: #c9d6d2" in tokens
    assert "--scans-accent-strong: #36534c" in tokens
    assert "--scans-text: #101828" in tokens
    assert "--scans-secondary: #667085" in tokens
    assert "--scans-row-hover: #f6f9f8" in tokens


def test_search_input_uses_the_restrained_eucalyptus_focus_ring() -> None:
    css = _scans_css()
    focus = css.split(".saved-scans-search-input:focus,", 1)[1].split("}", 1)[0]
    assert "var(--scans-focus-border)" in focus
    assert "0 0 0 3px var(--scans-focus)" in focus
    assert "outline: 0 !important" in focus

    tokens = css.split(".profile-saved-scans-section {", 1)[1].split("}", 1)[0]
    assert "--scans-focus-border: #6f9f93" in tokens
    assert "--scans-focus: rgba(86, 116, 109, 0.14)" in tokens
    assert "--scans-border: #d9e4e0" in tokens


def test_saved_scans_surface_keeps_a_dark_theme_definition() -> None:
    css = _scans_css()
    assert 'html:not([data-theme="light"]) .profile-saved-scans-section' in css
    assert 'html[data-theme="dark"] .profile-saved-scans-section' in css
    dark = css.split('html[data-theme="dark"] .profile-saved-scans-section {', 1)[1].split("}", 1)[0]
    assert "--scans-surface: #111a24" in dark
    assert "--scans-text: #e8edf3" in dark


def test_row_action_buttons_are_excluded_from_the_global_primary_button_owner() -> None:
    """They are compact icon controls, like the pipeline run icon buttons."""
    legacy = (ROOT / "src/app/static/styles.css").read_text(encoding="utf-8")
    for source in (APP_CSS, legacy):
        assert source.count(":not(.pipeline-run-icon-btn)") == source.count(
            ":not(.saved-scan-action-btn)"
        )
        assert source.count(":not(.saved-scan-action-btn)") > 0


# --- cache delivery -----------------------------------------------------------


def test_changed_saved_scans_assets_are_cache_busted_for_this_route_only() -> None:
    html = _html()
    assert "/static/app_redesign.css?v=saved_scans_library_r1" in html
    assert (
        "/static/profile.js?v=profile_saved_scans_e5_discard_icon"
        "_profile_resume_roles_r10_saved_scans_library_r1" in html
    )
    # no other profile route's markers move
    assert PROFILE_UI.count("app_redesign.css?v=saved_scans_library_r1") == 1
    assert PROFILE_UI.count("profile.js?v=agentic_review_v1") == 1
    assert PROFILE_UI.count("profile.js?v=preferences_guided_parity_r9") == 1
    assert PROFILE_UI.count("profile.js?v=item2_phase4_profile_corrections_r1") == 1


# --- backend safety -----------------------------------------------------------


def test_no_search_or_pagination_backend_was_added() -> None:
    api = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    for invented in (
        "/profile/saved-scans/search",
        "saved_scans_search",
        "saved_scans_page_size",
    ):
        assert invented not in api
        assert invented not in PROFILE_UI
    assert "saved-scans/data" in PROFILE_JS
    assert "limit=50" in PROFILE_JS


# --- delete confirmation dialog ----------------------------------------------


def _modal_html() -> str:
    return _html().split('id="savedScanDeleteModal"', 1)[1].split("</section>", 1)[0]


def _modal_css() -> str:
    return APP_CSS.split("#savedScanDeleteModal {", 1)[1]


def _rule_body(css: str, class_name: str) -> str:
    """Body of the rule whose selector is exactly this one class (not a group)."""
    match = re.search(
        rf"(?<!,)\n#savedScanDeleteModal \.{re.escape(class_name)} \{{([^}}]*)\}}",
        css,
    )
    assert match is not None, class_name
    return match.group(1)


def test_delete_dialog_still_exists_and_keeps_its_wiring() -> None:
    html = _html()
    assert 'id="savedScanDeleteModal"' in html
    for control in (
        "savedScanDeleteCloseBtn",
        "savedScanDeleteCancelBtn",
        "savedScanDeleteConfirmBtn",
        "savedScanDeleteName",
    ):
        assert f'id="{control}"' in html

    binding = PROFILE_JS.split("function bindSavedScansPage()", 1)[1]
    assert 'qs("savedScanDeleteCloseBtn")?.addEventListener("click", closeSavedScanDeleteModal)' in binding
    assert 'qs("savedScanDeleteCancelBtn")?.addEventListener("click", closeSavedScanDeleteModal)' in binding
    assert 'qs("savedScanDeleteConfirmBtn")?.addEventListener("click"' in binding
    assert "await deleteSavedScan();" in binding


def test_delete_dialog_identity_still_comes_from_open_modal_and_pending_id() -> None:
    open_fn = _fn("openSavedScanDeleteModal")
    assert 'profileState.pendingDeleteScanId = String(scan?.scan_id || "").trim()' in open_fn
    assert "scan?.job_company" in open_fn
    assert "scan?.job_title" in open_fn
    assert "scan?.resume_name || scan?.resume_filename" in open_fn
    # the joined label element is preserved, now alongside structured fields
    assert 'qs("savedScanDeleteName").textContent = label' in open_fn
    for field in ("savedScanDeleteCompany", "savedScanDeleteRole", "savedScanDeleteResume"):
        assert field in open_fn
        assert f'id="{field}"' in _modal_html()
    # no extra data is fetched to populate the dialog
    for network in ("fetchJson", "fetch(", "await "):
        assert network not in open_fn

    close_fn = _fn("closeSavedScanDeleteModal")
    assert "profileState.pendingDeleteScanId = null" in close_fn
    assert 'name.textContent = "this saved scan"' in close_fn


def test_delete_dialog_still_calls_the_existing_delete_endpoint() -> None:
    delete_fn = _fn("deleteSavedScan")
    assert "`/profile/saved-scans/${encodeURIComponent(scanId)}`" in delete_fn
    assert 'method: "DELETE"' in delete_fn
    assert "if (!scanId) return;" in delete_fn


def test_delete_dialog_uses_its_own_compact_classes() -> None:
    modal = _modal_html()
    for cls in (
        "saved-scan-delete-card",
        "saved-scan-delete-close",
        "saved-scan-delete-icon",
        "saved-scan-delete-summary",
        "saved-scan-delete-cancel-btn",
        "saved-scan-delete-confirm-btn",
    ):
        assert cls in modal

    card = _modal_css().split(".saved-scan-delete-card {", 1)[1].split("}", 1)[0]
    assert "width: min(496px" in card
    assert "border-radius: 20px !important" in card
    assert "padding: 26px !important" in card


def test_delete_dialog_close_is_an_icon_control_with_an_accessible_name() -> None:
    modal = _modal_html()
    close = modal.split('id="savedScanDeleteCloseBtn"', 1)[0].rsplit("<button", 1)[1]
    close += modal.split('id="savedScanDeleteCloseBtn"', 1)[1].split("</button>", 1)[0]
    assert 'aria-label="Close delete saved scan dialog"' in close
    assert "<svg" in close
    assert ">Close<" not in modal
    assert "ghost-btn" not in modal
    assert "modal-close-btn" not in modal


def test_delete_dialog_footer_uses_cancel_and_a_destructive_confirm() -> None:
    modal = _modal_html()
    assert ">\n            Cancel\n          </button>" in modal
    assert ">\n            Delete scan\n          </button>" in modal
    assert ">No<" not in modal
    assert "Yes, delete" not in modal


def test_delete_dialog_drops_the_old_run_on_confirmation_sentence() -> None:
    modal = _modal_html()
    assert "Are you sure you want to delete" not in modal
    assert "</strong>?" not in modal
    # structured summary replaces it
    assert "<dt>Company</dt>" in modal
    assert "<dt>Role</dt>" in modal
    assert "<dt>Resume</dt>" in modal


def test_delete_confirm_is_destructive_coral_never_eucalyptus_primary() -> None:
    css = _modal_css()
    confirm = _rule_body(css, "saved-scan-delete-confirm-btn")
    hover = css.split(".saved-scan-delete-confirm-btn:hover {", 1)[1].split("}", 1)[0]

    assert "var(--scan-dlg-danger)" in confirm
    assert "color: #ffffff !important" in confirm
    assert "var(--scan-dlg-danger-hover)" in hover
    for rejected in ("--app-action-primary", "#56746d", "#49655f", "linear-gradient"):
        assert rejected not in confirm
        assert rejected not in hover

    tokens = css.split("}", 1)[0]
    assert "--scan-dlg-danger: #b85f58" in tokens
    assert "--scan-dlg-danger-hover: #a7504a" in tokens
    assert "--scan-dlg-danger-pressed: #93443f" in tokens
    assert "--scan-dlg-danger-focus: rgba(184, 95, 88, 0.2)" in tokens
    # no fire-engine red / glow
    for harsh in ("#ff0000", "#e11d48", "#dc2626", "#ef4444", "box-shadow: 0 0 20px"):
        assert harsh not in css


def test_delete_dialog_cancel_is_neutral_secondary() -> None:
    cancel = _rule_body(_modal_css(), "saved-scan-delete-cancel-btn")
    assert "var(--scan-dlg-neutral-border)" in cancel
    assert "var(--scan-dlg-surface)" in cancel
    assert "var(--scan-dlg-text)" in cancel
    for rejected in ("#56746d", "#b85f58", "#2563eb"):
        assert rejected not in cancel


def test_delete_dialog_keeps_the_shared_accessibility_pattern() -> None:
    html = _html()
    opening = html.split('id="savedScanDeleteModal"', 1)[0].rsplit("<section", 1)[1]
    opening += html.split('id="savedScanDeleteModal"', 1)[1].split(">", 1)[0]
    assert 'role="dialog"' in opening
    assert 'aria-modal="true"' in opening
    assert 'aria-labelledby="savedScanDeleteTitle"' in opening
    assert 'aria-describedby="savedScanDeleteDescription"' in opening

    modal = _modal_html()
    assert 'tabindex="-1"' in modal
    assert 'id="savedScanDeleteTitle"' in modal
    assert 'id="savedScanDeleteDescription"' in modal

    binding = PROFILE_JS.split("function bindSavedScansPage()", 1)[1]
    escape_handler = binding.split(
        'qs("savedScanDeleteModal")?.addEventListener("keydown"', 1
    )[1].split("});", 1)[0]
    assert 'event.key === "Escape"' in escape_handler
    assert "closeSavedScanDeleteModal()" in escape_handler

    assert "modal._returnFocus = document.activeElement" in _fn("openSavedScanDeleteModal")
    assert "returnFocus.focus()" in _fn("closeSavedScanDeleteModal")


def test_profile_resume_delete_dialog_is_not_restyled_by_this_change() -> None:
    """The saved-scan dialog used to share .resume-delete-* rules; it now owns
    its own classes so the resume dialog keeps exactly what it had."""
    modal = _modal_html()
    for shared in (
        "resume-delete-modal-card",
        "resume-delete-modal-close-btn",
        "resume-delete-modal-actions",
        "resume-delete-cancel-btn",
        "resume-delete-confirm-btn",
    ):
        assert shared not in modal

    assert "profile-resume-delete-dialog" in PROFILE_UI
    assert 'id="closeResumeDeleteModalBtn"' in PROFILE_UI
    assert "#resumeDeleteModal .resume-delete-confirm-btn" in APP_CSS
    # the saved-scan dialog no longer rides on the shared destructive rule
    assert "#savedScanDeleteModal .resume-delete-confirm-btn" not in _modal_css()


def test_row_delete_icon_reads_destructive_at_rest() -> None:
    css = _scans_css()
    rest = css.split("body .saved-scan-action-btn--delete {", 1)[1].split("}", 1)[0]
    assert "color: var(--scans-danger-ink) !important" in rest
    assert "border-color: var(--scans-danger-border) !important" in rest

    tokens = css.split(".profile-saved-scans-section {", 1)[1].split("}", 1)[0]
    assert "--scans-danger-ink: #b45f57" in tokens
    assert "--scans-danger-border: #e6c8c4" in tokens
    # still an icon control, not a filled danger button
    assert "background: var(--scans-surface) !important" in css.split(
        "body .saved-scan-action-btn {", 1
    )[1].split("}", 1)[0]

"""Focused contracts for the compact Profile Resume document library."""

from html.parser import HTMLParser
from pathlib import Path

from starlette.requests import Request

from src.app.profile_ui import profile_page


ROOT = Path(__file__).resolve().parents[1]
PROFILE_JS = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
STYLES_CSS = (ROOT / "src/app/static/styles.css").read_text(encoding="utf-8")
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")


def _request(query_string: bytes = b"") -> Request:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profile",
            "query_string": query_string,
            "headers": [],
        }
    )
    request.state.auth_user = {
        "user_id": "resume-document-library-user",
        "access_level": "user",
        "is_admin": False,
    }
    return request


class _IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element_id = dict(attrs).get("id")
        if element_id:
            self.ids.append(str(element_id))


def _ids(html: str) -> list[str]:
    parser = _IdCollector()
    parser.feed(html)
    return parser.ids


def _resume_css() -> str:
    return APP_REDESIGN_CSS.split("profile_resume_document_library_r1", 1)[1].split(
        "profile_pipeline_run_stats_summary_r1", 1
    )[0]


def test_normal_profile_is_a_compact_library_with_modal_owned_upload_controls():
    html = profile_page(_request())
    resume_section = html.split('id="resumeSection"', 1)[1].split(
        'id="profilePipelineRunsSection"', 1
    )[0]

    assert 'class="profile-section-card profile-resume-library"' in html
    assert 'id="openResumeUploadModalBtn"' in html
    assert "</span> Add resume" in html
    assert 'id="profileResumeUploadModal" role="dialog" aria-modal="true"' in html
    assert 'id="resumeDropzone"' not in resume_section
    assert html.index('id="profileResumeUploadModal"') < html.index('id="resumeDropzone"')
    assert "resume-manager-grid" not in resume_section


def test_normal_profile_contains_exactly_one_functional_upload_control_set():
    html = profile_page(_request())

    for element_id in ("resumeDropzone", "resumeUploadInput", "resumeBrowseBtn"):
        assert html.count(f'id="{element_id}"') == 1
    ids = _ids(html)
    assert len(ids) == len(set(ids))
    assert "multiple" in html
    assert 'accept=".pdf,application/pdf"' in html


def test_onboarding_keeps_one_direct_uploader_without_profile_management_ui():
    html = profile_page(_request(b"onboarding=resume_upload"))
    resume_section = html.split('id="resumeSection"', 1)[1]

    assert 'data-profile-resume-onboarding="true"' in html
    assert 'class="profile-resume-onboarding-uploader"' in resume_section
    assert 'id="resumeDropzone"' in resume_section
    assert 'id="resumeUploadInput"' in resume_section
    assert html.count('id="resumeDropzone"') == 1
    assert 'id="profileResumeUploadModal"' not in html
    assert 'id="openResumeUploadModalBtn"' not in html
    assert 'class="profile-tabs"' not in html
    assert 'id="profilePipelineRunsSection"' not in html
    assert 'id="profileAdminUsersSection"' not in html


def test_resume_rendering_uses_document_rows_not_cards_or_mapping_accordions():
    assert 'class="profile-resume-document-row"' in PROFILE_JS
    assert 'class="profile-resume-file-icon"' in PROFILE_JS
    assert 'class="profile-resume-file-name" title=' in PROFILE_JS
    assert "formatBytes(resume.size_bytes" in PROFILE_JS
    assert "formatResumeDate(resume.modified_at" in PROFILE_JS
    assert 'class="profile-resume-role-chip' in PROFILE_JS
    assert "No role families" in PROFILE_JS
    assert 'class="resume-row"' not in PROFILE_JS.split("if (isResumeOnboardingMode())", 1)[1].split(
        "async function loadResumeRoleMappings", 1
    )[0].split("return;", 1)[1]
    assert "renderResumeRoleMappingPanel" not in PROFILE_JS


def test_rows_expose_exactly_two_direct_scoped_icon_actions_without_overflow():
    row_template = PROFILE_JS.split(
        '<article class="profile-resume-document-row">', 1
    )[1].split('  `).join("");', 1)[0]

    assert row_template.count('class="profile-resume-row-action ') == 2
    assert 'class="profile-resume-row-action profile-resume-manage-role-action"' in row_template
    assert 'class="profile-resume-row-action profile-resume-delete-row-action"' in row_template
    assert "data-manage-resume-roles" in row_template
    assert "data-resume-delete" in row_template
    assert "data-resume-menu-toggle" not in PROFILE_JS
    assert "profile-resume-menu" not in PROFILE_JS
    assert "closeResumeMenus" not in PROFILE_JS
    assert "•••" not in PROFILE_JS


def test_direct_row_actions_are_accessible_and_route_to_existing_modal_flows():
    assert 'aria-label="Manage role families for ${escapeHtml(resume.resume_name || "resume")}"' in PROFILE_JS
    assert 'title="Manage role families for ${escapeHtml(resume.resume_name || "resume")}"' in PROFILE_JS
    assert 'aria-label="Delete ${escapeHtml(resume.resume_name || "resume")}"' in PROFILE_JS
    assert 'title="Delete ${escapeHtml(resume.resume_name || "resume")}"' in PROFILE_JS
    assert 'openResumeRoleModal(manageButton.dataset.manageResumeRoles || "", manageButton)' in PROFILE_JS
    assert "openResumeDeleteModal(resumeName, button)" in PROFILE_JS
    assert "profileResumeManageRoleIcon" in PROFILE_JS
    assert 'class="profile-resume-row-action-icon profile-resume-delete-icon"' in PROFILE_JS


def test_resume_overflow_removal_does_not_remove_unrelated_account_menu():
    html = profile_page(_request())

    assert 'id="profileMenuShell"' in html
    assert 'id="profileMenuButton"' in html
    assert 'id="profileDropdown"' in html


def test_role_mapping_and_default_operations_keep_the_existing_backend_flow():
    assert 'fetchJson("/profile/resume-role-mappings")' in PROFILE_JS
    assert 'postJson("/profile/resume-role-mappings"' in PROFILE_JS
    assert "data-resume-role-toggle" in PROFILE_JS
    assert "data-resume-role-default" in PROFILE_JS
    assert "is_default_for_role: Boolean(isDefaultForRole)" in PROFILE_JS
    assert "deleteResumeRoleMapping" in PROFILE_JS
    assert "Changes save automatically." in profile_page(_request())


def test_upload_delete_callout_and_focus_flows_remain_bound():
    html = profile_page(_request())

    assert '`/profile/resumes/upload?filename=${encodeURIComponent(file.name)}`' in PROFILE_JS
    assert 'dropzone.addEventListener("drop"' in PROFILE_JS
    assert 'fetchJson("/profile/resumes")' in PROFILE_JS
    assert 'method: "DELETE"' in PROFILE_JS
    assert 'id="resumeDeleteModal" role="dialog" aria-modal="true"' in html
    assert 'id="resumeDeleteCancelBtn"' in html
    assert 'id="resumeDeleteConfirmBtn"' in html
    assert 'id="profilePlanningUploadCallout"' in html
    assert 'qs("profilePlanningUploadCallout")?.classList.remove("hidden")' in PROFILE_JS
    assert "trapProfileResumeModalFocus" in PROFILE_JS
    assert "modal._returnFocus" in PROFILE_JS
    assert 'modal.dataset.returnResumeAction = "manage"' in PROFILE_JS
    assert 'modal.dataset.returnResumeAction = "delete"' in PROFILE_JS


def test_unrelated_profile_tabs_and_sections_remain_present():
    html = profile_page(_request())

    assert '<span>Resumes</span>' in html
    assert '<span>Pipeline runs</span>' in html
    assert 'id="profilePipelineRunsSection"' in html
    assert 'id="refreshPipelineRunsBtn"' in html


def test_document_library_css_is_single_column_dense_and_responsive():
    css = _resume_css()

    row = css.split(".profile-resume-document-row {", 1)[1].split("}", 1)[0]
    assert "min-height: 76px" in row
    assert "border-bottom" in row
    assert "grid-template-columns" in row
    assert ".profile-resume-document-list" in css
    assert "repeat(2, minmax" not in css
    assert "@media (max-width: 760px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert 'html[data-theme="dark"] .profile-resume-document-row' in css


def test_resume_action_colors_override_known_global_gradient_without_leaking():
    css = _resume_css()
    legacy = APP_REDESIGN_CSS.split("profile_resume_document_library_r1", 1)[0]

    assert "#resumeBrowseBtn" in STYLES_CSS
    assert "background: var(--app-primary) !important" in STYLES_CSS
    assert "button:not(.agentic-review-tab)" in legacy
    assert "linear-gradient(135deg, var(--app-primary), var(--app-violet)) !important" in legacy
    assert "--profile-resume-accent: #3c746a" in css
    assert "--profile-resume-accent-hover: #315f57" in css
    assert "--profile-resume-accent-pressed: #294f49" in css
    assert "--profile-resume-accent-soft: #e7f0ed" in css
    assert "--profile-resume-accent-border: #b9d1cb" in css
    assert "--profile-resume-accent-text: #28564f" in css
    assert "#resumeSection .profile-resume-primary-action" in css
    assert "#resumeSection .profile-resume-primary-action:active" in css
    assert "#profileResumeUploadModal #resumeBrowseBtn" in css
    assert "#resumeList .profile-resume-row-action" in css
    assert "#resumeList .profile-resume-manage-role-action:hover" in css
    assert "#resumeList .profile-resume-delete-row-action:hover" in css
    assert 'mask: url("/static/media/discard_img.svg")' in css
    assert "background-image: none !important" in css
    assert "linear-gradient" not in css
    assert "var(--app-primary)" not in css
    assert "var(--app-violet)" not in css
    assert "#807e94" not in css
    assert "#706e82" not in css
    assert "profile-resume-menu" not in css
    assert "maroon" not in css.lower()
    assert "burgundy" not in css.lower()


def test_role_and_upload_interaction_states_use_scoped_eucalyptus_accents():
    css = _resume_css()

    assert ".profile-resume-role-chip" in css
    assert ".profile-resume-role-option.is-selected .profile-resume-role-toggle" in css
    assert ".profile-resume-role-default:not(:has(input:disabled))" in css
    assert "accent-color: var(--profile-resume-accent)" in css
    assert ".profile-resume-dropzone.drag-active" in css
    assert ".profile-resume-upload-icon" in css
    assert "color: var(--profile-resume-accent-text)" in css

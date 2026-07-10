# phase110b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961

from pathlib import Path


PLANNING_JS = Path("src/app/static/planning.js")
PLANNING_UI = Path("src/app/planning_ui.py")


def _source() -> str:
    return PLANNING_JS.read_text(encoding="utf-8")


def _function_source(source: str, name: str) -> str:
    start = source.index(f"function {name}")
    paren = source.index("(", start)
    depth = 0
    brace = -1
    for index in range(paren, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                brace = source.index("{", index)
                break
    assert brace >= 0
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"could not extract function {name}")


def _async_function_source(source: str, name: str) -> str:
    start = source.index(f"async function {name}")
    paren = source.index("(", start)
    depth = 0
    brace = -1
    for index in range(paren, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                brace = source.index("{", index)
                break
    assert brace >= 0
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"could not extract async function {name}")


def test_generate_suggestions_button_uses_existing_workspace_when_artifacts_exist():
    source = _source()
    button_source = _function_source(source, "buildTailoringButtonHtml")

    assert "hasTailoringWorkspaceArtifacts(row)" in button_source
    assert 'hasArtifacts ? "Open Workspace"' in button_source
    assert '"Generate Suggestions"' in button_source
    assert 'data-view-tailoring="true"' in button_source
    assert 'data-generate-suggestions="true"' in button_source
    assert '"Regenerate"' not in button_source
    assert '"Generate LLM tailoring"' not in button_source


def test_generate_suggestions_payload_uses_existing_regenerate_endpoint_contract():
    source = _source()
    payload_source = _function_source(source, "buildGenerateSuggestionsPayload")
    handler_source = _async_function_source(source, "handleGenerateSuggestionsClick")

    assert 'job_doc_id: row?.job_doc_id || ""' in payload_source
    assert 'queue_rank: row?.queue_rank || ""' in payload_source
    assert "selected_resume: resolveGenerateSuggestionsSelectedResume(row)" in payload_source
    assert "generate_llm_tailoring: true" in payload_source
    assert "refresh_llm_tailoring: false" in payload_source
    assert 'postJson("/planning/regenerate-selected-resume", payload)' in handler_source


def test_generate_suggestions_loader_steps_and_states_are_present():
    source = _source()
    markup = PLANNING_UI.read_text(encoding="utf-8")

    for label in [
        "Loading job and resume context",
        "Reading job requirements",
        "Finding match gaps",
        "Building tailoring strategy",
        "Generating suggestions",
        "Running safety review",
        "Opening workspace",
    ]:
        assert label in source

    for element_id in [
        "generateSuggestionsLoader",
        "generateSuggestionsStepList",
        "generateSuggestionsError",
        "generateSuggestionsRetryBtn",
        "generateSuggestionsOpenWorkspaceBtn",
        "generateSuggestionsCancelBtn",
    ]:
        assert element_id in markup

    loader_source = _function_source(source, "setGenerateSuggestionsLoaderState")
    assert '"success"' in loader_source
    assert '"running"' in loader_source
    assert '"Could not generate suggestions"' in loader_source
    assert '"Opening workspace"' in loader_source


def test_generate_suggestions_opens_tailoring_workspace_after_success():
    source = _source()
    handler_source = _async_function_source(source, "handleGenerateSuggestionsClick")

    assert "buildGenerateSuggestionsWorkspaceRow(row, response || {})" in handler_source
    assert "buildTailoringWorkspaceUrl(workspaceRow)" in handler_source
    assert "generateSuggestionsState.lastWorkspaceUrl = workspaceUrl" in handler_source
    assert "window.location.href = workspaceUrl" in handler_source


def test_generate_suggestions_click_is_separate_from_workspace_open_click():
    source = _source()
    click_source = source.split('qs("planningTableBody").addEventListener("click"', 1)[1].split(
        'qs("closeApplicationModalBtn")',
        1,
    )[0]

    assert 'event.target.closest("[data-view-tailoring=\'true\']")' in click_source
    assert "handleTailoringClick(tailoringButton)" in click_source
    assert 'event.target.closest("[data-generate-suggestions=\'true\']")' in click_source
    assert "handleGenerateSuggestionsClick(generateSuggestionsButton)" in click_source
    assert click_source.index("handleTailoringClick(tailoringButton)") < click_source.index(
        "handleGenerateSuggestionsClick(generateSuggestionsButton)"
    )


def test_generate_suggestions_static_change_does_not_add_application_mutation_paths():
    source = _source()
    snippets = "\n".join(
        [
            _function_source(source, "buildGenerateSuggestionsPayload"),
            _async_function_source(source, "handleGenerateSuggestionsClick"),
            _function_source(source, "retryGenerateSuggestions"),
            _function_source(source, "buildTailoringButtonHtml"),
        ]
    )

    forbidden = [
        "application_status",
        "auto_apply",
        "autoApply",
        "ATS",
        "recruiter",
        "source_resume",
        "overwrite",
        "apply_click",
        "submitApplication",
    ]
    for marker in forbidden:
        assert marker not in snippets


def test_phase110b_does_not_touch_backend_runtime_contracts():
    for path in [
        Path("src/app/api.py"),
        Path("src/app/services.py"),
        Path("src/pipeline/collector.py"),
    ]:
        text = path.read_text(encoding="utf-8")
        assert "generateSuggestions" not in text
        assert "Generate Suggestions" not in text

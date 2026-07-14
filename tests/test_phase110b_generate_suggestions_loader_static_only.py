# phase110b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961

from pathlib import Path
import json
import subprocess


PLANNING_JS = Path("src/app/static/planning.js")
PLANNING_UI = Path("src/app/planning_ui.py")
STYLES_CSS = Path("src/app/static/styles.css")


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


def _evaluate_generate_suggestions_cases():
    source = _source()
    function_names = [
        "normalizeResumeName",
        "hasTailoringWorkspaceArtifacts",
        "hasPlanningPacketArtifact",
        "resolvePlanningRowSelectedResume",
        "resolveGenerateSuggestionsAllowedResume",
        "resolveGenerateSuggestionsSelectedResume",
        "canGenerateSuggestionsForRow",
        "buildGenerateSuggestionsPayload",
        "resolvePlanningRowOutputDir",
        "buildGenerateSuggestionsEndpoint",
        "getWorkspaceBlockedReason",
        "buildTailoringButtonHtml",
    ]
    functions = "\n\n".join(_function_source(source, name) for name in function_names)
    script = f"""
const escapeHtml = (value) => String(value ?? "");
{functions}
const labelFor = (row) => {{
  const html = buildTailoringButtonHtml(row);
  const match = html.match(/>\\s*([^<]+?)\\s*<\\/button>/);
  return {{
    label: match ? match[1].trim() : "",
    html,
    payload: buildGenerateSuggestionsPayload(row),
    endpoint: buildGenerateSuggestionsEndpoint(row),
    selected: resolvePlanningRowSelectedResume(row),
    hasReadyArtifacts: hasTailoringWorkspaceArtifacts(row),
    hasPacket: hasPlanningPacketArtifact(row),
  }};
}};
const rows = {{
  packetSelected: labelFor({{
    job_doc_id: "job-1",
    selected_resume: "Stale.pdf",
    winner_resume: "Winner.pdf",
    runner_up_resume: "Runner.pdf",
    packet_json: "packet.json",
    planning_output_dir: "tmp/pipeline runs/user one/run 1/application_planning",
  }}),
  runScoped: labelFor({{
    job_doc_id: "job-run-scoped",
    winner_resume: "RunWinner.pdf",
    planning_output_dir: "outputs/application_planning",
    pipeline_run_id: "run-123",
  }}),
  packetResolved: labelFor({{
    queue_rank: "2",
    resolved_resume: "Resolved.pdf",
    winner_resume: "WinnerOnly.pdf",
    packet_json_key: "job_packets/packet.json",
  }}),
  selectorFallback: labelFor({{
    queue_rank: "3",
    selector_winner_resume: "Selector.pdf",
    winner_resume: "WinnerFallback.pdf",
    packet_json: "packet.json",
  }}),
  stalePacketResume: labelFor({{
    job_doc_id: "job-stale-packet",
    packet_resume: "StalePacket.pdf",
    winner_resume: "AllowedWinner.pdf",
    runner_up_resume: "AllowedRunner.pdf",
    packet_json: "packet.json",
  }}),
  operatorRunnerUp: labelFor({{
    job_doc_id: "job-runner-up",
    operator_selected_resume: "AllowedRunner.pdf",
    winner_resume: "AllowedWinner.pdf",
    runner_up_resume: "AllowedRunner.pdf",
    packet_json: "packet.json",
  }}),
  onlyWinner: labelFor({{
    job_doc_id: "job-only-winner",
    winner_resume: "OnlyWinner.pdf",
    packet_json: "packet.json",
    planning_output_dir: "tmp/pipeline_runs/user/run/application_planning/",
  }}),
  outputDirFallback: labelFor({{
    job_doc_id: "job-output-dir",
    winner_resume: "OutputWinner.pdf",
    output_dir: "tmp/pipeline_runs/output-dir/application_planning",
    packet_json: "packet.json",
  }}),
  packetOutputDirFallback: labelFor({{
    job_doc_id: "job-packet-output-dir",
    winner_resume: "PacketOutputWinner.pdf",
    packet_output_dir: "tmp/pipeline_runs/packet-output/application_planning",
    packet_json: "packet.json",
  }}),
  tailoringJson: labelFor({{
    job_doc_id: "job-4",
    winner_resume: "Winner.pdf",
    tailoring_json: "tailoring.json",
  }}),
  tailoringMd: labelFor({{
    queue_rank: "5",
    packet_resume: "Packet.pdf",
    tailoring_md: "tailoring.md",
  }}),
  noIdentity: labelFor({{
    selected_resume: "Selected.pdf",
    packet_json: "packet.json",
  }}),
  noResume: labelFor({{
    job_doc_id: "job-7",
    packet_json: "packet.json",
  }}),
}};
console.log(JSON.stringify(rows));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


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


def test_packet_only_rows_render_generate_suggestions_not_open_workspace():
    cases = _evaluate_generate_suggestions_cases()

    packet_selected = cases["packetSelected"]
    assert packet_selected["label"] == "Generate Suggestions"
    assert packet_selected["hasReadyArtifacts"] is False
    assert packet_selected["hasPacket"] is True
    assert 'data-generate-suggestions="true"' in packet_selected["html"]
    assert 'data-view-tailoring="true"' not in packet_selected["html"]
    assert 'data-packet-json="packet.json"' in packet_selected["html"]
    assert packet_selected["payload"]["selected_resume"] == "Winner.pdf"

    packet_resolved = cases["packetResolved"]
    assert packet_resolved["label"] == "Generate Suggestions"
    assert packet_resolved["payload"]["queue_rank"] == "2"
    assert packet_resolved["payload"]["selected_resume"] == "WinnerOnly.pdf"

    selector_fallback = cases["selectorFallback"]
    assert selector_fallback["label"] == "Generate Suggestions"
    assert selector_fallback["payload"]["selected_resume"] == "WinnerFallback.pdf"


def test_generate_suggestions_payload_uses_backend_allowed_resume_names():
    cases = _evaluate_generate_suggestions_cases()

    stale_packet = cases["stalePacketResume"]
    assert stale_packet["label"] == "Generate Suggestions"
    assert stale_packet["selected"] == "StalePacket.pdf"
    assert stale_packet["payload"]["selected_resume"] == "AllowedWinner.pdf"

    stale_selected = cases["packetSelected"]
    assert stale_selected["selected"] == "Stale.pdf"
    assert stale_selected["payload"]["selected_resume"] == "Winner.pdf"

    operator_runner_up = cases["operatorRunnerUp"]
    assert operator_runner_up["label"] == "Generate Suggestions"
    assert operator_runner_up["payload"]["selected_resume"] == "AllowedRunner.pdf"

    only_winner = cases["onlyWinner"]
    assert only_winner["label"] == "Generate Suggestions"
    assert only_winner["payload"]["selected_resume"] == "OnlyWinner.pdf"


def test_generate_suggestions_request_url_uses_run_scoped_job_corpus_when_available():
    cases = _evaluate_generate_suggestions_cases()

    packet_selected = cases["packetSelected"]
    assert packet_selected["endpoint"].startswith("/planning/regenerate-selected-resume?")
    assert "output_dir=tmp%2Fpipeline+runs%2Fuser+one%2Frun+1%2Fapplication_planning" in packet_selected["endpoint"]
    assert (
        "job_corpus=tmp%2Fpipeline+runs%2Fuser+one%2Frun+1%2Fapplication_planning%2Fcurrent_run_job_corpus.jsonl"
        in packet_selected["endpoint"]
    )

    run_scoped = cases["runScoped"]
    assert run_scoped["endpoint"] == "/planning/regenerate-selected-resume"
    assert run_scoped["payload"]["pipeline_run_id"] == "run-123"

    only_winner = cases["onlyWinner"]
    assert (
        "job_corpus=tmp%2Fpipeline_runs%2Fuser%2Frun%2Fapplication_planning%2Fcurrent_run_job_corpus.jsonl"
        in only_winner["endpoint"]
    )
    assert "%2F%2Fcurrent_run_job_corpus" not in only_winner["endpoint"]

    output_dir_fallback = cases["outputDirFallback"]
    assert (
        "job_corpus=tmp%2Fpipeline_runs%2Foutput-dir%2Fapplication_planning%2Fcurrent_run_job_corpus.jsonl"
        in output_dir_fallback["endpoint"]
    )

    packet_output_dir_fallback = cases["packetOutputDirFallback"]
    assert (
        "job_corpus=tmp%2Fpipeline_runs%2Fpacket-output%2Fapplication_planning%2Fcurrent_run_job_corpus.jsonl"
        in packet_output_dir_fallback["endpoint"]
    )

    no_resume = cases["noResume"]
    assert no_resume["endpoint"] == "/planning/regenerate-selected-resume"
    assert "current_run_job_corpus.jsonl" not in no_resume["endpoint"]


def test_tailoring_artifact_rows_still_open_workspace():
    cases = _evaluate_generate_suggestions_cases()

    tailoring_json = cases["tailoringJson"]
    assert tailoring_json["label"] == "Open Workspace"
    assert tailoring_json["hasReadyArtifacts"] is True
    assert 'data-view-tailoring="true"' in tailoring_json["html"]
    assert 'data-generate-suggestions="true"' not in tailoring_json["html"]

    tailoring_md = cases["tailoringMd"]
    assert tailoring_md["label"] == "Open Workspace"
    assert tailoring_md["hasReadyArtifacts"] is True
    assert 'data-view-tailoring="true"' in tailoring_md["html"]


def test_generate_suggestions_requires_identity_and_selected_resume():
    cases = _evaluate_generate_suggestions_cases()

    no_identity = cases["noIdentity"]
    assert no_identity["label"] == "Unavailable"
    assert "disabled" in no_identity["html"]
    assert 'data-generate-suggestions="true"' not in no_identity["html"]

    no_resume = cases["noResume"]
    assert no_resume["label"] == "Unavailable"
    assert "disabled" in no_resume["html"]
    assert no_resume["payload"]["selected_resume"] == ""


def test_generate_suggestions_payload_uses_existing_regenerate_endpoint_contract():
    source = _source()
    payload_source = _function_source(source, "buildGenerateSuggestionsPayload")
    endpoint_source = _function_source(source, "buildGenerateSuggestionsEndpoint")
    handler_source = _async_function_source(source, "handleGenerateSuggestionsClick")

    assert 'job_doc_id: row?.job_doc_id || ""' in payload_source
    assert 'queue_rank: row?.queue_rank || ""' in payload_source
    assert "selected_resume: resolveGenerateSuggestionsSelectedResume(row)" in payload_source
    assert "generate_llm_tailoring: true" in payload_source
    assert "refresh_llm_tailoring: false" in payload_source
    assert 'params.set("output_dir", outputDir)' in endpoint_source
    assert 'params.set("job_corpus", `${normalizedOutputDir}/current_run_job_corpus.jsonl`)' in endpoint_source
    assert 'return "/planning/regenerate-selected-resume";' in endpoint_source
    assert "postJson(buildGenerateSuggestionsEndpoint(row), payload)" in handler_source


def test_selected_resume_resolution_matches_real_planning_row_fields():
    source = _source()
    display_resolver_source = _function_source(source, "resolvePlanningRowSelectedResume")
    payload_resolver_source = _function_source(source, "resolveGenerateSuggestionsAllowedResume")
    output_dir_resolver_source = _function_source(source, "resolvePlanningRowOutputDir")
    artifact_source = _function_source(source, "hasTailoringWorkspaceArtifacts")

    expected_order = [
        "operator_selected_resume",
        "selected_resume",
        "packet_resume",
        "resolved_resume",
        "selector_winner_resume",
        "winner_resume",
    ]
    positions = [display_resolver_source.index(field) for field in expected_order]
    assert positions == sorted(positions)
    assert "runner_up_resume" in payload_resolver_source
    assert "runnerup_resume" in payload_resolver_source
    assert "packet_resume" not in payload_resolver_source
    assert "resolved_resume" not in payload_resolver_source
    assert "selector_winner_resume" not in payload_resolver_source
    output_dir_order = [
        "planning_output_dir",
        "output_dir",
        "packet_output_dir",
        "artifact_output_dir",
    ]
    output_dir_positions = [output_dir_resolver_source.index(field) for field in output_dir_order]
    assert output_dir_positions == sorted(output_dir_positions)

    assert "packet_json" not in artifact_source
    assert "packet_json_key" not in artifact_source
    assert "function hasPlanningPacketArtifact(row)" in source


def test_generate_suggestions_loader_steps_and_states_are_present():
    source = _source()
    markup = PLANNING_UI.read_text(encoding="utf-8")

    for label in [
        "Reading job details",
        "Checking resume evidence",
        "Building targeted edits",
        "Preparing review packet",
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

    assert "generate-suggestions-fullpage" in markup
    assert "generate-suggestions-fullpage-card" in markup
    assert "generate-suggestions-current-step" in markup
    assert "resume-choice-loading-steps generate-suggestions-step-list" not in markup
    styles = STYLES_CSS.read_text(encoding="utf-8")
    assert ".workflow-overlay" in styles
    assert "position: fixed" in styles
    assert "inset: 0" in styles

    loader_source = _function_source(source, "setGenerateSuggestionsLoaderState")
    runner_source = _function_source(source, "buildGenerateSuggestionsStepRunnerHtml")
    render_source = _function_source(source, "renderGenerateSuggestionsSteps")
    assert '"success"' in loader_source
    assert '"running"' in loader_source
    assert '"Could not generate suggestions"' in loader_source
    assert '"Tailoring workspace is ready"' in loader_source
    assert "generate-suggestions-step-item" in runner_source
    assert "workflow-step-track" in runner_source
    assert "workflow-step__indicator" in runner_source
    assert 'isComplete ? "is-complete"' in runner_source
    assert 'isFailed ? "is-error"' in runner_source
    assert 'isActive ? "is-active"' in runner_source
    assert '"is-pending"' in runner_source
    assert "generate-suggestions-step-progress" not in runner_source
    assert "buildResumeChoiceLoadingStepsHtml" not in render_source
    assert "GENERATE_SUGGESTIONS_STEPS.map" not in render_source
    timer_source = _function_source(source, "startGenerateSuggestionsStepTimer")
    assert "window.setInterval" in timer_source
    assert "lastProcessingCue" in timer_source
    assert "GENERATE_SUGGESTIONS_STEPS.length - 2" in timer_source


def test_generate_suggestions_error_state_keeps_fullpage_retry_cancel_controls():
    source = _source()
    markup = PLANNING_UI.read_text(encoding="utf-8")
    loader_source = _function_source(source, "setGenerateSuggestionsLoaderState")
    close_source = _function_source(source, "closeGenerateSuggestionsLoader")
    handler_source = _async_function_source(source, "handleGenerateSuggestionsClick")

    assert "Could not generate suggestions" in loader_source
    assert "generateSuggestionsRetryBtn" in markup
    assert "generateSuggestionsCancelBtn" in markup
    assert "retryBtn) retryBtn.classList.remove" in loader_source
    assert "cancelBtn.disabled = false" in loader_source
    assert "cancelledRequestSeq" in close_source
    assert "cancelledRequestSeq === requestSeq" in handler_source


def test_generate_suggestions_waits_for_workspace_action_after_success():
    source = _source()
    handler_source = _async_function_source(source, "handleGenerateSuggestionsClick")
    open_source = _function_source(source, "openGenerateSuggestionsWorkspace")

    assert "buildGenerateSuggestionsWorkspaceRow(row, response || {})" in handler_source
    assert "buildTailoringWorkspaceUrl(workspaceRow)" in handler_source
    assert "generateSuggestionsState.lastWorkspaceUrl = workspaceUrl" in handler_source
    assert "window.location.href" not in handler_source
    assert "window.location.href = generateSuggestionsState.lastWorkspaceUrl" in open_source
    assert "Open Tailoring Workspace" in PLANNING_UI.read_text(encoding="utf-8")


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

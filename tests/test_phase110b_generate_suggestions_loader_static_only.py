# phase110b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961

from pathlib import Path
import json
import subprocess


PLANNING_JS = Path("src/app/static/planning.js")
APP_JS = Path("src/app/static/app.js")
PLANNING_UI = Path("src/app/planning_ui.py")
STYLES_CSS = Path("src/app/static/styles.css")
FRONTEND_STYLES_CSS = Path("frontend/executive-kpi/src/styles.css")
TAILORING_PREMIUM_CSS = Path("src/app/static/tailoring_workspace_premium.css")
SCAN_WORKSPACE_CSS = Path("src/app/static/scan_workspace.css")
SCAN_WORKSPACE_REVIEW_CSS = Path("src/app/static/scan_workspace_review.css")
SCAN_WORKSPACE_PREMIUM_CSS = Path("src/app/static/scan_workspace_premium.css")
SCAN_WORKSPACE_JS = Path("src/app/static/scan_workspace.js")


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
        "buildBulkGenerateSuggestionsPayload",
        "resolvePlanningRowOutputDir",
        "buildGenerateSuggestionsEndpoint",
        "getWorkspaceBlockedReason",
        "resolvePlanningWorklistAction",
        "getPlanningBulkSuggestionSummary",
        "buildTailoringButtonHtml",
    ]
    functions = "\n\n".join(_function_source(source, name) for name in function_names)
    script = f"""
const escapeHtml = (value) => String(value ?? "");
const BULK_GENERATE_SUGGESTIONS_PARSE_RETRY_LIMIT = 0;
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
const bulkRows = [
  {{ job_doc_id: "packet", winner_resume: "Winner.pdf", packet_json: "packet.json" }},
  {{ job_doc_id: "ready", winner_resume: "Winner.pdf", tailoring_json: "tailoring.json", tailoring_workspace_state: "ready", tailoring_actionable_replacement_count: 2 }},
  {{ job_doc_id: "blocked", winner_resume: "Winner.pdf", tailoring_json: "blocked.json", tailoring_workspace_state: "unavailable", tailoring_actionable_replacement_count: 0 }},
  {{ job_doc_id: "missing-resume" }},
];
const bulkSummary = getPlanningBulkSuggestionSummary(bulkRows);
rows.bulkSummary = {{
  eligibleCount: bulkSummary.eligibleCount,
  alreadyPrepared: bulkSummary.alreadyPrepared,
  unavailable: bulkSummary.unavailable,
  candidateIds: bulkSummary.candidateRows.map((row) => row.job_doc_id),
  payload: buildBulkGenerateSuggestionsPayload(bulkSummary.candidateRows[0]),
  singleRowPayload: buildGenerateSuggestionsPayload(bulkSummary.candidateRows[0]),
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


def _evaluate_bulk_generate_suggestions_execution():
    source = _source()
    execute_source = _async_function_source(source, "executeBulkGenerateSuggestions")
    acknowledge_source = _async_function_source(
        source, "acknowledgeBulkGenerateSuggestionsCompletion"
    )
    script = f"""
let bulkGenerateSuggestionsState = {{
  candidateRows: [{{ job_doc_id: "A" }}, {{ job_doc_id: "B" }}, {{ job_doc_id: "C" }}],
  total: 3,
  completed: 0,
  succeeded: 0,
  needsAttention: 0,
  currentIndex: -1,
  isRunning: false,
  stopRequested: false,
  results: [],
}};
let active = 0;
let maxActive = 0;
let order = [];
let renderStates = [];
let publishCalls = 0;
let refreshCalls = 0;
let retryLimits = [];
const publishPlanningWorklistState = () => {{ publishCalls += 1; }};
const renderBulkGenerateSuggestionsOverlay = (state) => {{ renderStates.push(state); }};
const buildGenerateSuggestionsEndpoint = () => "/planning/regenerate-selected-resume";
const buildGenerateSuggestionsPayload = (row, {{ parseRetryLimit = 1 }} = {{}}) => ({{ job_doc_id: row.job_doc_id, generate_llm_tailoring: true, refresh_llm_tailoring: false, parse_retry_limit: parseRetryLimit === 0 ? 0 : 1 }});
const BULK_GENERATE_SUGGESTIONS_PARSE_RETRY_LIMIT = 0;
const buildBulkGenerateSuggestionsPayload = (row) => buildGenerateSuggestionsPayload(row, {{ parseRetryLimit: BULK_GENERATE_SUGGESTIONS_PARSE_RETRY_LIMIT }});
const bulkGenerateSuggestionsJobLabel = (row) => row.job_doc_id;
const classifyBulkGenerateSuggestionsResponse = (row) => ({{ status: "success", label: row.job_doc_id, error: "" }});
const extractGenerateSuggestionsError = () => "safe failure";
let postJson = async (_url, payload) => {{
  order.push(`start-${{payload.job_doc_id}}`);
  retryLimits.push(payload.parse_retry_limit);
  active += 1;
  maxActive = Math.max(maxActive, active);
  await Promise.resolve();
  active -= 1;
  order.push(`end-${{payload.job_doc_id}}`);
  if (payload.job_doc_id === "B") throw new Error("failure");
  return {{ ok: true }};
}};
{execute_source}
const getBulkGenerateSuggestionsOverlay = () => ({{ dataset: {{ workflowState: "complete" }} }});
const closeBulkGenerateSuggestionsOverlay = () => undefined;
const loadPlanningTable = async () => {{ refreshCalls += 1; }};
{acknowledge_source}
(async () => {{
  await executeBulkGenerateSuggestions();
  const completed = {{
    order: order.slice(),
    maxActive,
    completed: bulkGenerateSuggestionsState.completed,
    succeeded: bulkGenerateSuggestionsState.succeeded,
    needsAttention: bulkGenerateSuggestionsState.needsAttention,
    statuses: bulkGenerateSuggestionsState.results.map((result) => result.status),
    publishCalls,
    retryLimits: retryLimits.slice(),
  }};
  await acknowledgeBulkGenerateSuggestionsCompletion();
  completed.refreshCalls = refreshCalls;

  order = [];
  bulkGenerateSuggestionsState = {{
    candidateRows: [{{ job_doc_id: "A" }}, {{ job_doc_id: "B" }}, {{ job_doc_id: "C" }}],
    total: 3,
    completed: 0,
    succeeded: 0,
    needsAttention: 0,
    currentIndex: -1,
    isRunning: false,
    stopRequested: false,
    results: [],
  }};
  const originalPost = postJson;
  postJson = async (url, payload) => {{
    const response = await originalPost(url, payload);
    bulkGenerateSuggestionsState.stopRequested = true;
    return response;
  }};
  await executeBulkGenerateSuggestions();
  const stopped = {{
    order: order.slice(),
    completed: bulkGenerateSuggestionsState.completed,
    succeeded: bulkGenerateSuggestionsState.succeeded,
    needsAttention: bulkGenerateSuggestionsState.needsAttention,
    remaining: bulkGenerateSuggestionsState.total - bulkGenerateSuggestionsState.completed,
    finalRender: renderStates[renderStates.length - 1],
  }};
  console.log(JSON.stringify({{ completed, stopped }}));
}})();
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_planning_and_executive_legacy_limit_normalizers_preserve_high_values():
    planning_normalize = _function_source(_source(), "normalizePlanningFilters")
    executive_normalize = _function_source(
        APP_JS.read_text(encoding="utf-8"), "normalizeQueueFilters"
    )
    script = f"""
const normalizePlanningFilterValues = (values) => Array.isArray(values) ? values : [];
{planning_normalize}
{executive_normalize}
console.log(JSON.stringify({{
  planning: normalizePlanningFilters({{ limit: 1000 }}).limit,
  executive: normalizeQueueFilters({{ limit: 1000 }}).limit,
}}));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(completed.stdout) == {"planning": 1000, "executive": 1000}
    assert "Math.min(100" not in planning_normalize
    assert "Math.min(200" not in executive_normalize


def _evaluate_bulk_generate_suggestions_selection():
    source = _source()
    functions = "\n\n".join(
        (
            _function_source(source, "normalizeBulkGenerateSuggestionsCount"),
            _function_source(source, "getPlanningBulkSuggestionSelection"),
            _function_source(source, "resetBulkGenerateSuggestionsConfiguration"),
        )
    )
    script = f"""
let bulkGenerateSuggestionsState = {{}};
const planningTableState = {{ bulkSuggestionRows: [] }};
const resetBulkGenerateSuggestionsState = () => undefined;
const resolvePlanningWorklistAction = (row) => ({{ kind: row.kind }});
{functions}
const rows = [
  {{ job_doc_id: "D", kind: "generate_suggestions", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "B", kind: "generate_suggestions", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "A", kind: "generate_suggestions", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "C", kind: "generate_suggestions", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "E", kind: "generate_suggestions", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "F", kind: "generate_suggestions", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "other-match", kind: "generate_suggestions", action: "APPLY", winner_bucket: "solid", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "other-state", kind: "generate_suggestions", action: "APPLY", winner_bucket: "weak", tailoring_workspace_state: "missing", role_family: "applied_ai" }},
  {{ job_doc_id: "other-preference", kind: "generate_suggestions", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "data_engineering" }},
  {{ job_doc_id: "other-review", kind: "generate_suggestions", action: "MAYBE_TAILOR", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "open", kind: "open_workspace", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "blocked", kind: "blocked", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
  {{ job_doc_id: "unavailable", kind: "unavailable", action: "APPLY", winner_bucket: "strong", tailoring_workspace_state: "ready", role_family: "applied_ai" }},
];
const config = {{
  requestedCount: 3,
  reviewAction: "APPLY",
  winnerBucket: "strong",
  preferenceId: "applied_ai",
}};
const limited = getPlanningBulkSuggestionSelection(rows, config);
const overAvailable = getPlanningBulkSuggestionSelection(rows, {{ ...config, requestedCount: 20 }});
const unbounded = getPlanningBulkSuggestionSelection(rows, {{ ...config, requestedCount: 1000 }});
resetBulkGenerateSuggestionsConfiguration(24);
const defaultLarge = bulkGenerateSuggestionsState.requestedCount;
resetBulkGenerateSuggestionsConfiguration(4);
const defaultSmall = bulkGenerateSuggestionsState.requestedCount;
console.log(JSON.stringify({{
  limited: {{
    eligibleCount: limited.eligibleCount,
    filteredCount: limited.filteredCount,
    selectedCount: limited.selectedCount,
    ids: limited.candidateRows.map((row) => row.job_doc_id),
  }},
  unbounded: {{
    overAvailableCount: overAvailable.selectedCount,
    selectedCount: unbounded.selectedCount,
    ids: unbounded.candidateRows.map((row) => row.job_doc_id),
  }},
  defaults: [defaultLarge, defaultSmall],
  normalized: [
    normalizeBulkGenerateSuggestionsCount("1000"),
    normalizeBulkGenerateSuggestionsCount("0"),
    normalizeBulkGenerateSuggestionsCount("1.5"),
  ],
}}));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _evaluate_tailoring_workspace_regeneration_cases():
    source = _source()
    functions = "\n".join(
        (
            _function_source(source, "setTailoringWorkspaceRegenerateBusyState"),
            _async_function_source(source, "regenerateTailoringWorkspaceSuggestions"),
        )
    )
    script = f"""
const label = {{ textContent: "Regenerate Suggestions" }};
const button = {{
  disabled: false,
  dataset: {{ busy: "false" }},
  attributes: {{}},
  setAttribute(name, value) {{ this.attributes[name] = value; }},
  querySelector() {{ return label; }},
}};
const meta = {{ textContent: "Existing suggestions" }};
const qs = (id) => id === "tailoringWorkspaceRegenerateBtn" ? button : meta;
const normalizeResumeName = (value) => String(value || "").trim();
const getTailoringWorkspaceContext = () => ({{
  jobDocId: "job-1",
  resumeName: "resume.pdf",
  planningOutputDir: "tmp/run-1/application_planning",
}});
let regenerationCalls = 0;
let loaderCalls = 0;
let errorCalls = 0;
let resolveRegeneration;
let mode = "pending";
const regenerateSelectedResumeChoice = (...args) => {{
  regenerationCalls += 1;
  globalThis.lastArgs = args;
  if (mode === "failure") return Promise.reject(new Error("failed"));
  return new Promise((resolve) => {{ resolveRegeneration = resolve; }});
}};
const initTailoringWorkspacePage = async () => {{ loaderCalls += 1; }};
const showAppError = () => {{ errorCalls += 1; }};
{functions}
(async () => {{
  const first = regenerateTailoringWorkspaceSuggestions();
  await regenerateTailoringWorkspaceSuggestions();
  const busy = {{
    regenerationCalls,
    disabled: button.disabled,
    ariaBusy: button.attributes["aria-busy"],
    label: label.textContent,
  }};
  resolveRegeneration();
  await first;
  const success = {{
    regenerationCalls,
    loaderCalls,
    disabled: button.disabled,
    ariaBusy: button.attributes["aria-busy"],
    label: label.textContent,
    options: globalThis.lastArgs[2],
  }};
  mode = "failure";
  meta.textContent = "Existing suggestions";
  await regenerateTailoringWorkspaceSuggestions();
  const failure = {{
    loaderCalls,
    errorCalls,
    disabled: button.disabled,
    label: label.textContent,
    meta: meta.textContent,
  }};
  console.log(JSON.stringify({{ busy, success, failure }}));
}})().catch((err) => {{ console.error(err); process.exit(1); }});
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _evaluate_selected_resume_regeneration_endpoints():
    source = _source()
    functions = "\n".join(
        (
            _function_source(source, "resolvePlanningRowOutputDir"),
            _function_source(source, "buildGenerateSuggestionsEndpoint"),
            _async_function_source(source, "regenerateSelectedResumeChoice"),
        )
    )
    script = f"""
const requests = [];
const postJson = async (endpoint, payload) => {{ requests.push({{ endpoint, payload }}); }};
{functions}
(async () => {{
  await regenerateSelectedResumeChoice({{ job_doc_id: "job-unscoped" }}, "resume.pdf");
  await regenerateSelectedResumeChoice(
    {{ job_doc_id: "job-scoped" }},
    "resume.pdf",
    {{ outputDir: "tmp/run-1/application_planning" }}
  );
  console.log(JSON.stringify(requests));
}})().catch((err) => {{ console.error(err); process.exit(1); }});
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _evaluate_tailoring_workspace_ai_optional_lane_cases():
    source = _source()
    functions = "\n\n".join(
        _function_source(source, name)
        for name in [
            "getTailoringReplacementCandidateId",
            "getTailoringWorkspaceActionableLanes",
            "getTailoringWorkspaceSelectableItems",
            "buildTailoringWorkspaceCandidateLookup",
            "collectTailoringWorkspaceSelectableCandidateIds",
            "normalizeTailoringWorkspaceSelectedCandidateIds",
            "getTailoringWorkspacePayload",
            "getRenderableTailoringAnchorCards",
            "getTailoringWorkspaceSuggestionBuckets",
            "renderReplacementDecisionSection",
        ]
    )
    script = f"""
const tailoringWorkspaceState = {{ artifact: null }};
const escapeHtml = (value) => String(value ?? "");
const getTailoringWorkspaceDisplayBulletText = (item) => String(item?.original_text || "");
const getTailoringWorkspaceCurrentReviewDecisionMap = () => ({{}});
const getReplacementReviewState = () => "pending";
const getTailoringWorkspaceReviewDecisionLabel = (value) => value;
const getTailoringWorkspaceReviewDecisionTone = () => "muted";
const buildTailoringTonePill = (label) => `<span>${{label}}</span>`;
const humanizeUnderscoreLabel = (value) => String(value || "");
const renderTailoringWorkspaceScorePills = () => "";
const renderScanWorkspaceCriticAdvisoryDetails = () => "";
{functions}
const candidate = (id, status) => ({{
  replacement_candidate_id: id,
  replacement_status: status,
  original_text: `Original ${{id}}`,
  final_replacement_text: `Replacement ${{id}}`,
}});
const summarize = (payload) => {{
  tailoringWorkspaceState.artifact = {{ kind: "json", data: payload }};
  const buckets = getTailoringWorkspaceSuggestionBuckets();
  const lookup = buildTailoringWorkspaceCandidateLookup(payload);
  return {{
    readyIds: buckets.ready.map(getTailoringReplacementCandidateId),
    reviewIds: buckets.reviewGuidance.map(getTailoringReplacementCandidateId),
    lookupIds: Array.from(lookup.keys()),
    selectableIds: collectTailoringWorkspaceSelectableCandidateIds(payload),
    normalizedAi: normalizeTailoringWorkspaceSelectedCandidateIds(payload, ["ai-1"]),
    normalizedDirection: normalizeTailoringWorkspaceSelectedCandidateIds(payload, ["direction-1"]),
    automaticSelection: normalizeTailoringWorkspaceSelectedCandidateIds(payload, []),
  }};
}};
const aiOnlyPayload = {{
  app_ready_replacements: [],
  direct_apply_optional_replacements: [],
  ai_optimize_optional_replacements: [candidate("ai-1", "ai_optimize_optional")],
  direction_only_replacements: [candidate("direction-1", "direction_only")],
  anchor_cards: [],
}};
const mixedPayload = {{
  app_ready_replacements: [candidate("ready-1", "direct_apply_ready")],
  direct_apply_optional_replacements: [candidate("direct-1", "direct_apply_optional")],
  ai_optimize_optional_replacements: [candidate("ai-1", "ai_optimize_optional")],
  direction_only_replacements: [candidate("direction-1", "direction_only")],
  anchor_cards: [],
}};
const emptyAiPayload = {{
  ...mixedPayload,
  ai_optimize_optional_replacements: [],
}};
const duplicatePayload = {{
  app_ready_replacements: [candidate("duplicate", "direct_apply_ready")],
  direct_apply_optional_replacements: [candidate("duplicate", "direct_apply_optional")],
  ai_optimize_optional_replacements: [candidate("duplicate", "ai_optimize_optional")],
  direction_only_replacements: [],
  anchor_cards: [],
}};
const renderedAiCard = renderReplacementDecisionSection({{
  title: "AI optimize optional",
  items: aiOnlyPayload.ai_optimize_optional_replacements,
  mode: "replacement",
  selectionEnabled: true,
  selectedCandidateIds: [],
  workspacePresentation: true,
}});
console.log(JSON.stringify({{
  aiOnly: summarize(aiOnlyPayload),
  mixed: summarize(mixedPayload),
  emptyAi: summarize(emptyAiPayload),
  duplicate: summarize(duplicatePayload),
  renderedAiCard,
}}));
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
    resolver_source = _function_source(source, "resolvePlanningWorklistAction")
    action_source = resolver_source + button_source

    assert "hasTailoringWorkspaceArtifacts(row)" in action_source
    assert 'hasArtifacts ? "Open Workspace"' in action_source
    assert '"Generate Suggestions"' in action_source
    assert 'data-view-tailoring="true"' in button_source
    assert 'data-generate-suggestions="true"' in button_source
    assert '"Regenerate"' not in button_source
    assert '"Generate LLM tailoring"' not in button_source


def test_bulk_generation_reuses_exact_action_resolution_and_single_row_payload():
    cases = _evaluate_generate_suggestions_cases()
    bulk = cases["bulkSummary"]

    assert bulk == {
        "eligibleCount": 1,
        "alreadyPrepared": 1,
        "unavailable": 2,
        "candidateIds": ["packet"],
        "payload": {
            "pipeline_run_id": "",
            "job_doc_id": "packet",
            "queue_rank": "",
            "selected_resume": "Winner.pdf",
            "generate_llm_tailoring": True,
            "refresh_llm_tailoring": False,
            "parse_retry_limit": 0,
        },
        "singleRowPayload": {
            "pipeline_run_id": "",
            "job_doc_id": "packet",
            "queue_rank": "",
            "selected_resume": "Winner.pdf",
            "generate_llm_tailoring": True,
            "refresh_llm_tailoring": False,
            "parse_retry_limit": 1,
        },
    }

    source = _source()
    summary_source = _function_source(source, "getPlanningBulkSuggestionSummary")
    assert "resolvePlanningWorklistAction(row)" in summary_source
    assert 'action.kind === "generate_suggestions"' in summary_source
    assert 'action.kind === "open_workspace"' in summary_source


def test_bulk_generation_start_is_one_prompt_server_owned_request():
    source = _source()
    execute_source = _async_function_source(source, "executeBulkGenerateSuggestions")
    assert "Promise.all" not in execute_source
    assert "buildBulkGenerateSuggestionsPayload(row)" in execute_source
    assert "const BULK_GENERATE_SUGGESTIONS_PARSE_RETRY_LIMIT = 0;" in source
    assert 'await postJson("/planning/bulk-generation/start"' in execute_source
    assert "/planning/regenerate-selected-resume" not in execute_source
    assert "for (let index" not in execute_source
    assert "requested_count: rows.length" in execute_source
    assert "closeBulkGenerateSuggestionsOverlay()" in execute_source
    assert "ApplyLensBulkGeneration?.refresh" in execute_source
    assert "loadPlanningTable" not in execute_source
    assert "retry" not in execute_source.lower()


def test_bulk_configuration_intersects_filters_preserves_order_and_has_no_count_cap():
    cases = _evaluate_bulk_generate_suggestions_selection()

    assert cases["limited"] == {
        "eligibleCount": 10,
        "filteredCount": 6,
        "selectedCount": 3,
        "ids": ["D", "B", "A"],
    }
    assert cases["unbounded"] == {
        "overAvailableCount": 6,
        "selectedCount": 6,
        "ids": ["D", "B", "A", "C", "E", "F"],
    }
    assert cases["defaults"] == [10, 4]
    assert cases["normalized"] == [1000, 0, 0]


def test_bulk_http_200_llm_failure_is_not_counted_as_prepared_success():
    source = _source()
    classify_source = _function_source(
        source, "classifyBulkGenerateSuggestionsResponse"
    )
    failure_message_source = _function_source(
        source, "generateSuggestionsLlmFailureMessage"
    )
    script = f"""
const bulkGenerateSuggestionsJobLabel = (row) => row.job_title;
const buildGenerateSuggestionsWorkspaceRow = (row, response) => ({{ ...row, ...response }});
const resolvePlanningWorklistAction = (row) => ({{
  kind: row.tailoring_workspace_state === "ready" ? "open_workspace" : "unavailable",
  blockedReason: row.tailoring_workspace_state === "ready" ? "" : "No usable workspace",
}});
{failure_message_source}
{classify_source}
console.log(JSON.stringify({{
  failed: classifyBulkGenerateSuggestionsResponse(
    {{ job_title: "A" }},
    {{ ok: true, llm_tailoring_status: "failed", tailoring_workspace_state: "ready" }}
  ),
  ready: classifyBulkGenerateSuggestionsResponse(
    {{ job_title: "B" }},
    {{ ok: true, llm_tailoring_status: "generated", tailoring_workspace_state: "ready" }}
  ),
  unusable: classifyBulkGenerateSuggestionsResponse(
    {{ job_title: "C" }},
    {{ ok: true, llm_tailoring_status: "generated", tailoring_workspace_state: "unavailable" }}
  ),
  empty: classifyBulkGenerateSuggestionsResponse(
    {{ job_title: "D" }},
    {{ ok: true, llm_tailoring_status: "generated", tailoring_workspace_state: "empty" }}
  ),
  noSafeRewrites: classifyBulkGenerateSuggestionsResponse(
    {{ job_title: "E" }},
    {{ ok: true, llm_tailoring_status: "generated", tailoring_workspace_state: "no_safe_rewrites" }}
  ),
}}));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        text=True,
        capture_output=True,
        check=True,
    )
    cases = json.loads(completed.stdout)
    assert cases["failed"]["status"] == "needs_attention"
    assert cases["failed"]["outcome"] == "failed"
    assert "no suggestions were" in cases["failed"]["error"]
    assert "Nothing was submitted." in cases["failed"]["error"]
    assert cases["ready"]["status"] == "success"
    assert cases["ready"]["outcome"] == "generated"
    assert cases["unusable"]["status"] == "needs_attention"
    assert cases["empty"] == {
        "status": "success",
        "outcome": "empty",
        "label": "D",
        "error": "",
    }
    assert cases["noSafeRewrites"] == {
        "status": "success",
        "outcome": "no_safe_rewrites",
        "label": "E",
        "error": "",
    }


def test_bulk_completion_detail_separates_empty_review_and_failure_outcomes():
    render_source = _function_source(_source(), "renderBulkGenerateSuggestionsResults")

    assert 'result.outcome === "empty"' in render_source
    assert 'result.outcome === "no_safe_rewrites"' in render_source
    assert 'result.status === "needs_attention"' in render_source
    assert "No grounded rewrite evidence" in render_source
    assert "Review guidance" in render_source
    assert "Needs attention" in render_source


def test_bulk_tailoring_primary_action_uses_restrained_soft_plum_tokens():
    styles = STYLES_CSS.read_text(encoding="utf-8")
    tailoring_tokens = styles.split(".workflow-overlay--tailoring {", 1)[1].split("}", 1)[0]
    light_tokens = styles.split(
        'html[data-theme="light"] .workflow-overlay--tailoring {', 1
    )[1].split("}", 1)[0]

    for tokens in (tailoring_tokens, light_tokens):
        assert "--workflow-action-bg: #72587c;" in tokens
        assert "linear-gradient" not in tokens
        assert "#4f46e5" not in tokens
        assert "#7c3aed" not in tokens
    assert "--workflow-accent: #bfaac5;" in tailoring_tokens
    assert "--workflow-accent: #72587c;" in light_tokens


def test_no_global_important_background_rule_can_match_the_bulk_control():
    """The earlier exclusion covered only one selector family and missed this one.

    Any broad `background ... !important` rule whose rightmost compound is a
    bare <button> and whose ancestors the Bulk control actually has will beat
    the component rule regardless of specificity, so every such family must
    carry the opt-out.
    """

    import re

    # Ancestors the Bulk button really has inside the Planning worklist card.
    allowed_ancestors = {
        "html", "body", "main", "#planningWorklistRoot",
        ".planning-dashboard-page", ".page", ".planning-dashboard-shell",
        ".shared-table-card", ".shared-table-heading-with-actions",
        ".shared-table-heading-actions", ".shared-table-heading",
    }

    def ancestors_reachable(prefix: str) -> bool:
        if not prefix.strip():
            return True
        for token in [t for t in re.split(r"[\s>+~]+", prefix.strip()) if t]:
            token = re.sub(r":[a-z-]+(\([^)]*\))?$", "", token)
            if token in ("html", "body", "main", "*") or token.startswith("html["):
                continue
            if token in allowed_ancestors:
                continue
            parts = re.findall(r"[.#][\w-]+", token)
            if parts and all(part in allowed_ancestors for part in parts):
                continue
            return False
        return True

    offenders = []
    for sheet in (STYLES_CSS, Path("src/app/static/app_redesign.css")):
        css = sheet.read_text(encoding="utf-8")
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            body = match.group(2)
            if "!important" not in body:
                continue
            if not re.search(r"background(-color|-image)?\s*:", body):
                continue
            line = css[: match.start()].count("\n") + 1
            for selector in match.group(1).split(","):
                selector = " ".join(selector.split())
                if not selector or "/*" in selector:
                    continue
                parts = re.split(r"\s*[\s>+~]\s*", selector)
                last, prefix = parts[-1], " ".join(parts[:-1])
                if not re.match(r"^button([:.\[]|$)", last):
                    continue
                negations = [n.strip() for n in re.findall(r":not\(([^)]*)\)", last)]
                if ".planning-react-bulk-generate" in negations:
                    continue
                # A class/attribute-qualified button selector (e.g.
                # "button.saved-scan-action-btn--open") can only match that
                # component, never the Bulk control, so it is not a global
                # override risk. Only generic "button" rules are.
                qualifier = re.sub(r":not\([^)]*\)", "", last)
                qualifier = re.sub(r"^button", "", qualifier)
                if re.search(r"[.\[]", qualifier):
                    continue
                if not ancestors_reachable(prefix):
                    continue
                offenders.append(f"{sheet.name}:{line} {selector[:80]}")

    assert not offenders, "Global !important background can override Bulk: " + "; ".join(offenders)

    # The specific family that was missed the first time.
    styles = STYLES_CSS.read_text(encoding="utf-8")
    assert (
        "button:not(.primary-btn):not(.app-shell-primary-link)" in styles
    )
    for match in re.finditer(r"button:not\(\.primary-btn\)(?::not\([^)]*\))*", styles):
        assert ".planning-react-bulk-generate" in match.group(0)


def test_sticky_action_cells_own_an_isolated_foreground_paint_shield():
    """Runtime showed ordinary cells geometrically overlap the sticky column.

    A table cell's own background is not a reliable cover for the *content* of
    cells scrolling beneath it, so the sticky cell isolates a stacking context
    and paints an explicit shield above them but below its own contents.
    """

    styles = FRONTEND_STYLES_CSS.read_text(encoding="utf-8")

    # Shield exists for both tables, on the real TablePrimitives hook.
    for selector in (
        ".shared-table-viewport td.is-sticky-action::before",
        ".shared-table-viewport th.is-sticky-action::before",
        ".executive-queue-table-viewport td.is-sticky-action::before",
        ".executive-queue-table-viewport th.is-sticky-action::before",
    ):
        assert selector in styles

    shield_start = styles.index(".shared-table-viewport th.is-sticky-action::before")
    shield = styles[shield_start : styles.index("}", shield_start)]
    assert 'content: "";' in shield
    assert "position: absolute;" in shield
    assert "inset: 0;" in shield
    assert "z-index: 0;" in shield
    assert "background: var(--sticky-action-bg);" in shield
    assert "pointer-events: none;" in shield

    # Sticky cell isolates its own stacking context; contents sit above shield.
    assert "isolation: isolate;" in styles
    lift_start = styles.index(".shared-table-viewport th.is-sticky-action > *")
    lift = styles[lift_start : styles.index("}", lift_start)]
    assert "position: relative;" in lift
    assert "z-index: 1;" in lift

    # Shield surface comes from the existing opaque row tokens only.
    for token in (
        "--sticky-action-bg: var(--queue-row-default);",
        "--sticky-action-bg: var(--queue-surface-muted);",
        "--sticky-action-bg: var(--queue-row-alternate);",
        "--sticky-action-bg: var(--queue-row-hover);",
        "--sticky-action-bg: var(--queue-row-expanded);",
        "--sticky-action-bg: var(--queue-row-focus);",
    ):
        assert token in styles

    # Opaque one-pixel seam at the left boundary.
    assert "-1px 0 0 var(--queue-border)" in styles

    # Table safety invariants preserved.
    assert "z-index: 9999" not in styles
    assert styles.count("border-collapse: separate;") >= 2
    assert styles.count("overflow: auto;") >= 2


def test_sticky_action_column_owns_an_opaque_paint_layer_in_both_tables():
    """Adjacent columns must never paint through the final sticky column."""

    styles = FRONTEND_STYLES_CSS.read_text(encoding="utf-8")

    # Both viewports establish their own stacking context and still scroll.
    assert ".shared-table-viewport {\n  isolation: isolate;" in styles
    assert ".executive-queue-table-viewport {\n  isolation: isolate;" in styles
    assert styles.count("overflow: auto;") >= 2

    # The sticky cell is a real covering layer, not just a positioned cell.
    for marker in (
        "opacity: 1;",
        "background-image: none;",
        "background-clip: border-box;",
    ):
        assert marker in styles
    # Scope this to the sticky action column: unrelated components (e.g. the
    # filter-menu scrollbar thumb) legitimately use padding-box.
    for _block in styles.split("is-sticky-action")[1:]:
        assert "background-clip: padding-box" not in _block.split("}", 1)[0]

    # Generic sticky hook applied by TablePrimitives, plus the column ids.
    assert ".shared-table-viewport th.is-sticky-action," in styles
    assert ".shared-table-viewport td.is-sticky-action," in styles
    assert ".executive-queue-table-viewport td.is-sticky-action {" in styles

    # Every row state paints an opaque row token on the sticky cell.
    for token in (
        "var(--queue-row-default)",
        "var(--queue-row-alternate)",
        "var(--queue-row-hover)",
        "var(--queue-row-expanded)",
        "var(--queue-row-focus)",
    ):
        assert token in styles
    assert "td.is-sticky-action { background: var(--queue-row-alternate); }" in styles
    assert "td.is-sticky-action { background: var(--queue-row-hover); }" in styles
    assert "td.is-sticky-action { background: var(--queue-row-expanded); }" in styles

    # Sticky header sits above sticky body, which sits above ordinary cells.
    assert "z-index: 5;" in styles
    assert "z-index: 6; background: var(--queue-surface-muted); }" in styles
    assert "z-index: 9999" not in styles


def test_packet_status_is_a_separate_column_from_the_sticky_next_step_cell():
    """Proves a visible `Packet ready` inside the sticky region is bleed."""

    worklist = (
        Path("frontend/executive-kpi/src/PlanningWorklist.tsx")
    ).read_text(encoding="utf-8")

    assert 'id: "packet_status"' in worklist
    assert 'stickyColumnId="next_step"' in worklist
    packet_index = worklist.index('id: "packet_status"')
    next_step_index = worklist.index('id: "next_step"')
    assert packet_index != next_step_index


def test_executive_pipeline_run_meta_is_retained_but_visually_hidden():
    """app.js still resolves the node; the idle pill is not rendered."""

    ui_source = Path("src/app/ui.py").read_text(encoding="utf-8")
    app_js = Path("src/app/static/app.js").read_text(encoding="utf-8")

    assert 'id="pipelineRunMeta"' in ui_source
    assert 'class="subtext pipeline-run-meta hidden" id="pipelineRunMeta"' in ui_source
    assert ui_source.index('id="sourceYieldRoot"') < ui_source.index('id="pipelineRunMeta"')
    assert ui_source.index('id="pipelineRunMeta"') < ui_source.index('id="executiveQueueRoot"')
    assert 'qs("pipelineRunMeta")' in app_js


def test_bulk_configuration_progress_and_safety_contract_is_explicit_and_bounded():
    source = _source()
    ui = PLANNING_UI.read_text(encoding="utf-8")
    styles = STYLES_CSS.read_text(encoding="utf-8")
    frontend_styles = FRONTEND_STYLES_CSS.read_text(encoding="utf-8")
    open_source = _function_source(source, "openBulkGenerateSuggestionsConfirmation")
    update_source = _function_source(source, "updateBulkGenerateSuggestionsConfiguration")
    start_source = _async_function_source(source, "startBulkGenerateSuggestionsExecution")
    keydown_source = _function_source(source, "handleBulkGenerateSuggestionsDialogKeydown")
    execute_source = _async_function_source(source, "executeBulkGenerateSuggestions")
    stop_source = _function_source(source, "stopBulkGenerateSuggestionsAfterCurrent")
    overlay_source = _function_source(source, "renderBulkGenerateSuggestionsOverlay")

    for element_id in (
        "bulkGenerateSuggestionsOverlay",
        "bulkGenerateSuggestionsControls",
        "bulkGenerateSuggestionsNumber",
        "bulkGenerateSuggestionsReviewFilter",
        "bulkGenerateSuggestionsMatchFilter",
        "bulkGenerateSuggestionsPreferenceFilter",
        "bulkGenerateSuggestionsSummary",
        "bulkGenerateSuggestionsCurrent",
        "bulkGenerateSuggestionsResults",
        "bulkGenerateSuggestionsSecondaryBtn",
        "bulkGenerateSuggestionsPrimaryBtn",
    ):
        assert f'id="{element_id}"' in ui
        assert f'qs("{element_id}")' in source

    assert 'id="bulkGenerateSuggestionsTailoringFilter"' not in ui
    assert 'qs("bulkGenerateSuggestionsTailoringFilter")' not in source

    assert "Nothing will be submitted to employers." in ui
    assert "Choose which eligible Planning jobs should receive tailoring suggestions." in ui
    assert "Enter a positive whole number." in ui
    assert "bulk-generate-suggestions-summary" in styles
    assert "getPlanningBulkSuggestionSummary()" in open_source
    assert "resetBulkGenerateSuggestionsConfiguration(scopeSummary.eligibleCount)" in open_source
    assert 'renderBulkGenerateSuggestionsOverlay("confirm", getPlanningBulkSuggestionSelection())' in open_source
    assert "getPlanningBulkSuggestionSelection()" in update_source
    assert "resetBulkGenerateSuggestionsState(selection.candidateRows)" in start_source
    assert "await executeBulkGenerateSuggestions()" in start_source
    assert "postJson" not in open_source + update_source
    # The one overlay serves both flows: the initial CTA is unchanged, and the
    # re-run flow reuses the same settings step with re-run copy.
    assert '? `Re-run selected (${selection.selectedCount})`' in overlay_source
    assert ': "Generate suggestions"' in overlay_source
    assert '"Re-run bulk suggestions"' in overlay_source
    assert '"Bulk generate suggestions"' in overlay_source
    assert "Review the settings before re-running suggestions for the selected jobs." in overlay_source
    assert "Generate suggestion for 1 job" not in overlay_source
    assert "Generate suggestions for ${selection.selectedCount} jobs" not in overlay_source
    assert "primaryBtn.disabled = selection.selectedCount === 0" in overlay_source
    assert 'event.key === "Escape" && state === "confirm"' in keydown_source
    assert 'event.key !== "Tab"' in keydown_source
    assert "closeBulkGenerateSuggestionsOverlay()" in keydown_source
    assert "generateSuggestionsState.isRunning" in open_source
    assert "bulkGenerateSuggestionsState.isRunning" in open_source
    assert "Stop after current" in overlay_source
    assert "were not started" in overlay_source
    assert "setInterval" not in overlay_source + execute_source
    assert "abort" not in stop_source.lower()
    assert 'overlay.setAttribute("aria-busy", state === "running" ? "true" : "false")' in overlay_source
    assert execute_source.index("bulkGenerateSuggestionsState.isRunning = true") < execute_source.index(
        'postJson("/planning/bulk-generation/start"'
    )
    assert "for (let index" not in execute_source
    assert "ApplyLensBulkGeneration?.stop" in stop_source
    assert '.workflow-overlay--tailoring[data-workflow-state="running"] .workflow-dialog-status-icon::after {' in styles
    assert '.workflow-overlay--tailoring:not(.is-success):not(.is-error) .workflow-dialog-status-icon::after {' not in styles
    assert '.bulk-generate-suggestions-fullpage[data-workflow-state="confirm"] .workflow-dialog-status-icon::after {' in styles
    assert "animation: none;" in styles
    assert ".workflow-overlay--tailoring.is-stopped .workflow-dialog-status-icon" in styles

    # Bulk action is a compact neutral/plum product control, ID-scoped so no
    # generic button rule can win, in both themes.
    assert (
        "#planningWorklistRoot .planning-react-bulk-generate {" in frontend_styles
    )
    assert "border: 1px solid #9fc7bb;" in frontend_styles
    assert "background: #d3e8e2;" in frontend_styles
    assert "color: #16322d;" in frontend_styles
    assert (
        "#planningWorklistRoot .planning-react-bulk-generate__icon {"
        in frontend_styles
    )
    assert "color: #356f63;" in frontend_styles
    assert (
        "#planningWorklistRoot .planning-react-bulk-generate small {"
        in frontend_styles
    )
    assert "color: #466e65;" in frontend_styles
    assert 'html[data-theme="dark"] #planningWorklistRoot .planning-react-bulk-generate {' in frontend_styles
    assert "border-color: #3f6c64;" in frontend_styles
    assert "background: #24433f;" in frontend_styles
    assert "color: #a8d4ca;" in frontend_styles
    assert "color: #f3faf8;" in frontend_styles
    assert (
        'html[data-theme="dark"] #planningWorklistRoot .planning-react-bulk-generate small {'
        in frontend_styles
    )
    assert "color: #c7dfda;" in frontend_styles
    bulk_style_start = frontend_styles.index(
        "#planningWorklistRoot .planning-react-bulk-generate {"
    )
    bulk_style_end = frontend_styles.index(
        ".shared-table-title-line", bulk_style_start
    )
    bulk_styles = frontend_styles[bulk_style_start:bulk_style_end]
    # The control must never regress to a gradient CTA, and must not need
    # !important to beat the generic `button` rule.
    assert "gradient" not in bulk_styles
    assert "!important" not in bulk_styles

    guarded_bulk_source = open_source + update_source + start_source + execute_source + stop_source + overlay_source
    for forbidden in (
        "/application-actions",
        "mark_applied",
        "submit_application",
        "application_status",
        "Promise.all",
    ):
        assert forbidden not in guarded_bulk_source


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


def test_tailoring_workspace_renders_header_commands_with_ai_optimize_and_regenerate():
    markup = PLANNING_UI.read_text(encoding="utf-8")
    actions_position = markup.index('class="tailoring-workspace-context-actions"')
    optimize_position = markup.index('id="tailoringWorkspaceOpenScanBtn"')
    regenerate_position = markup.index('id="tailoringWorkspaceRegenerateBtn"')
    actions_end = markup.index("</div>", regenerate_position)

    assert actions_position < optimize_position < regenerate_position < actions_end
    assert 'class="tailoring-ai-optimize-btn"' in markup
    assert 'class="tailoring-regenerate-btn"' in markup
    assert 'type="button"' in markup[regenerate_position : regenerate_position + 400]
    assert "Regenerate Suggestions" in markup[regenerate_position : regenerate_position + 600]
    assert "Generate a fresh set of AI tailoring suggestions" in markup


def test_tailoring_workspace_regeneration_reuses_scoped_endpoint_and_workspace_loader():
    source = _source()
    helper_source = _async_function_source(source, "regenerateSelectedResumeChoice")
    handler_source = _async_function_source(source, "regenerateTailoringWorkspaceSuggestions")
    binder_source = _function_source(source, "bindTailoringWorkspaceRegenerateAction")

    assert 'outputDir = ""' in helper_source
    assert 'buildGenerateSuggestionsEndpoint({ planning_output_dir: outputDir })' in helper_source
    assert ': "/planning/regenerate-selected-resume"' in helper_source
    assert "button.disabled || button.dataset.busy === \"true\"" in handler_source
    assert 'jobDocId = String(context?.jobDocId || "").trim()' in handler_source
    assert 'selectedResume = normalizeResumeName(context?.resumeName || "")' in handler_source
    assert "generateLlmTailoring: true" in handler_source
    assert "refreshLlmTailoring: true" in handler_source
    assert "outputDir: context.planningOutputDir" in handler_source
    assert "await initTailoringWorkspacePage()" in handler_source
    assert handler_source.index("await regenerateSelectedResumeChoice") < handler_source.index(
        "await initTailoringWorkspacePage()"
    )
    assert "setTailoringWorkspaceRegenerateBusyState(false)" in handler_source
    assert "tailoringWorkspaceState.artifact = null" not in handler_source
    assert 'button.disabled = !hasRequiredIdentity' in binder_source
    assert 'button.addEventListener("click", regenerateTailoringWorkspaceSuggestions)' in binder_source


def test_selected_resume_regeneration_forwards_run_scoped_corpus_and_keeps_unscoped_compatibility():
    requests = _evaluate_selected_resume_regeneration_endpoints()

    assert requests[0]["endpoint"] == "/planning/regenerate-selected-resume"
    assert requests[1]["endpoint"].startswith("/planning/regenerate-selected-resume?")
    assert "output_dir=tmp%2Frun-1%2Fapplication_planning" in requests[1]["endpoint"]
    assert (
        "job_corpus=tmp%2Frun-1%2Fapplication_planning%2Fcurrent_run_job_corpus.jsonl"
        in requests[1]["endpoint"]
    )


def test_tailoring_workspace_header_commands_stay_compact_across_themes():
    styles = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    action_source = styles.split(".tailoring-workspace-context-actions {", 1)[1].split("}", 1)[0]
    button_source = styles.split(".tailoring-regenerate-btn {", 1)[1].split("}", 1)[0]

    assert "display: flex" in action_source
    assert "justify-content: flex-end" in action_source
    assert "height: 36px" in styles
    assert "background: color-mix" in button_source
    assert 'html[data-theme="light"] .tailoring-workspace-page' in styles
    assert 'html[data-theme="dark"] .tailoring-workspace-layout' in styles


def test_tailoring_workspace_regeneration_busy_success_and_failure_behavior():
    cases = _evaluate_tailoring_workspace_regeneration_cases()

    assert cases["busy"] == {
        "regenerationCalls": 1,
        "disabled": True,
        "ariaBusy": "true",
        "label": "Regenerating…",
    }
    assert cases["success"]["regenerationCalls"] == 1
    assert cases["success"]["loaderCalls"] == 1
    assert cases["success"]["disabled"] is False
    assert cases["success"]["ariaBusy"] == "false"
    assert cases["success"]["label"] == "Regenerate Suggestions"
    assert cases["success"]["options"] == {
        "generateLlmTailoring": True,
        "refreshLlmTailoring": True,
        "outputDir": "tmp/run-1/application_planning",
    }
    assert cases["failure"]["loaderCalls"] == 1
    assert cases["failure"]["errorCalls"] == 1
    assert cases["failure"]["disabled"] is False
    assert cases["failure"]["label"] == "Regenerate Suggestions"
    assert "current suggestions are still available" in cases["failure"]["meta"]


def test_tailoring_workspace_consumes_ai_optimize_optional_as_ready_and_selectable():
    cases = _evaluate_tailoring_workspace_ai_optional_lane_cases()

    assert cases["aiOnly"]["readyIds"] == ["ai-1"]
    assert cases["aiOnly"]["reviewIds"] == ["direction-1"]
    assert "ai-1" in cases["aiOnly"]["lookupIds"]
    assert cases["aiOnly"]["selectableIds"] == ["ai-1"]
    assert cases["aiOnly"]["normalizedAi"] == ["ai-1"]
    assert cases["aiOnly"]["normalizedDirection"] == []
    assert cases["aiOnly"]["automaticSelection"] == []
    assert cases["mixed"]["readyIds"] == ["ready-1", "direct-1", "ai-1"]
    assert cases["emptyAi"]["readyIds"] == ["ready-1", "direct-1"]
    assert cases["duplicate"]["readyIds"] == ["duplicate"]


def test_tailoring_workspace_ai_optional_card_and_human_save_preview_contract():
    cases = _evaluate_tailoring_workspace_ai_optional_lane_cases()
    source = _source()
    preview_source = _async_function_source(source, "previewTailoringWorkspaceSelection")
    save_source = _async_function_source(source, "saveTailoringWorkspaceSelection")
    summary_source = _function_source(source, "renderTailoringInteractiveSummaryInto")

    assert "AI optimize optional" in cases["renderedAiCard"]
    assert "tailoring-workspace-review-item--ready" in cases["renderedAiCard"]
    assert "tailoring-workspace-review-item-header" in cases["renderedAiCard"]
    assert "tailoring-workspace-review-item-body" in cases["renderedAiCard"]
    assert "tailoring-workspace-review-content--current" in cases["renderedAiCard"]
    assert "tailoring-workspace-review-content--suggested" in cases["renderedAiCard"]
    assert "tailoring-workspace-review-item-footer" in cases["renderedAiCard"]
    assert 'data-tailoring-focus-candidate="ai-1"' in cases["renderedAiCard"]
    assert 'data-tailoring-select-candidate="ai-1"' in cases["renderedAiCard"]
    assert "Add" in cases["renderedAiCard"]
    assert "aiOptimizeOptionalHtml" in summary_source
    assert "selected_patch_candidate_ids: selectedIds" in preview_source
    assert "selected_patch_candidate_ids: selectedIds" in save_source
    assert "getTailoringWorkspaceSelectedCandidateIds()" in preview_source
    assert "getTailoringWorkspaceSelectedCandidateIds()" in save_source


def test_tailoring_workspace_lane_fix_does_not_change_scan_workspace_consumers():
    source = _source()

    for function_name in [
        "getScanWorkspaceTrustedSuggestions",
        "getScanWorkspaceAiSuggestions",
        "getScanWorkspaceGuidance",
        "getScanWorkspaceReplacementSuggestions",
    ]:
        assert "getTailoringWorkspaceActionableLanes" not in _function_source(
            source,
            function_name,
        )


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
        "Building targeted edits",
        "Preparing review packet",
        "Opening workspace",
    ]:
        assert label in source
    assert source.index("Building targeted edits") < source.index("Preparing review packet")
    assert source.index("Preparing review packet") < source.index("Opening workspace")
    assert "Reading job details" not in source
    assert "Checking resume evidence" not in source

    for element_id in [
        "generateSuggestionsLoader",
        "generateSuggestionsStepList",
        "generateSuggestionsError",
        "generateSuggestionsRetryBtn",
        "generateSuggestionsOpenWorkspaceBtn",
        "generateSuggestionsCancelBtn",
        "generateSuggestionsStatusIcon",
    ]:
        assert element_id in markup

    assert 'aria-labelledby="generateSuggestionsLoaderTitle"' in markup
    assert 'aria-describedby="generateSuggestionsLoaderText"' in markup
    assert 'aria-busy="false"' in markup
    assert "Suggestions stay in review until you open the workspace." in markup

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
    assert "GENERATE_SUGGESTIONS_STEP_DESCRIPTIONS" in runner_source
    assert 'aria-current="step"' in runner_source
    assert 'isComplete ? "is-complete"' in runner_source
    assert 'isFailed ? "is-error"' in runner_source
    assert 'isActive ? "is-active"' in runner_source
    assert '"is-pending"' in runner_source
    assert "generate-suggestions-step-progress" not in runner_source
    assert "buildResumeChoiceLoadingStepsHtml" not in render_source
    assert "GENERATE_SUGGESTIONS_STEPS.map" not in render_source
    assert 'step.setAttribute("aria-current", "step")' in render_source
    assert 'step.removeAttribute("aria-current")' in render_source
    assert "getGenerateSuggestionsStepPositionClass" not in render_source
    assert "renderGenerateSuggestionsSteps(generateSuggestionsState.stepIndex, false)" in loader_source
    assert "renderGenerateSuggestionsSteps(GENERATE_SUGGESTIONS_STEPS.length - 1, true)" in loader_source
    timer_source = _function_source(source, "startGenerateSuggestionsStepTimer")
    assert "window.setInterval" in timer_source
    assert "lastProcessingCue" in timer_source
    assert "GENERATE_SUGGESTIONS_STEPS.length - 2" in timer_source


def test_generate_suggestions_error_state_keeps_fullpage_retry_cancel_controls():
    source = _source()
    markup = PLANNING_UI.read_text(encoding="utf-8")
    loader_source = _function_source(source, "setGenerateSuggestionsLoaderState")
    close_source = _function_source(source, "closeGenerateSuggestionsLoader")
    acknowledge_source = _async_function_source(
        source, "acknowledgeGenerateSuggestionsLoader"
    )
    handler_source = _async_function_source(source, "handleGenerateSuggestionsClick")

    assert "Could not generate suggestions" in loader_source
    assert "generateSuggestionsRetryBtn" in markup
    assert "generateSuggestionsCancelBtn" in markup
    assert "retryBtn) retryBtn.classList.remove" in loader_source
    assert "cancelBtn.disabled = false" in loader_source
    assert "cancelledRequestSeq" in close_source
    assert "cancelledRequestSeq === requestSeq" in handler_source
    assert 'workflowState === "success"' in acknowledge_source
    assert acknowledge_source.index("closeGenerateSuggestionsLoader()") < (
        acknowledge_source.index("if (!wasSuccessful) return")
    )
    assert acknowledge_source.index("if (!wasSuccessful) return") < (
        acknowledge_source.index("loadPlanningTable({ forceNetwork: true })")
    )


def test_generate_suggestions_success_uses_acknowledgement_and_planning_refresh():
    source = _source()
    loader_source = _function_source(source, "setGenerateSuggestionsLoaderState")
    handler_source = _async_function_source(source, "handleGenerateSuggestionsClick")
    acknowledge_source = _async_function_source(
        source, "acknowledgeGenerateSuggestionsLoader"
    )
    open_source = _function_source(source, "openGenerateSuggestionsWorkspace")
    success_branch = loader_source.split('if (state === "success")', 1)[1].split(
        "return;", 1
    )[0]

    assert "buildGenerateSuggestionsWorkspaceRow(row, response || {})" in handler_source
    assert "buildTailoringWorkspaceUrl(workspaceRow)" in handler_source
    assert "generateSuggestionsState.lastWorkspaceUrl = workspaceUrl" in handler_source
    assert "window.location.href" not in handler_source
    assert 'state === "success" ? "Okay" : "Cancel"' in loader_source
    assert 'openBtn.classList.remove("hidden")' not in success_branch
    assert "closeGenerateSuggestionsLoader()" in acknowledge_source
    assert "await loadPlanningTable({ forceNetwork: true })" in acknowledge_source
    assert "window.location" not in acknowledge_source
    assert (
        'qs("generateSuggestionsCancelBtn").addEventListener("click", '
        "acknowledgeGenerateSuggestionsLoader)"
    ) in source
    assert source.index("function resolvePlanningWorklistAction") < source.index(
        "async function loadPlanningTable"
    )
    assert 'hasArtifacts ? "Open Workspace"' in _function_source(
        source, "resolvePlanningWorklistAction"
    )
    assert "window.location.href = generateSuggestionsState.lastWorkspaceUrl" in open_source
    assert "Open Tailoring Workspace" in PLANNING_UI.read_text(encoding="utf-8")


def test_generate_suggestions_click_is_separate_from_workspace_open_click():
    source = _source()
    click_source = source.split('window.addEventListener(PLANNING_WORKLIST_ACTION_EVENT_NAME', 1)[1].split(
        'qs("closeApplicationModalBtn")',
        1,
    )[0]

    assert 'action.type !== "next_step"' in click_source
    assert 'actionState.kind === "open_workspace"' in click_source
    assert "handleTailoringClick(buttonLike)" in click_source
    assert 'actionState.kind === "generate_suggestions"' in click_source
    assert "handleGenerateSuggestionsClick(buttonLike)" in click_source
    assert click_source.index("handleTailoringClick(buttonLike)") < click_source.index(
        "handleGenerateSuggestionsClick(buttonLike)"
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


def test_tailoring_workspace_ui_e_unlinks_scan_css_and_loads_premium_last():
    source = PLANNING_UI.read_text(encoding="utf-8")
    route = source.split('@router.get("/tailoring-workspace"', 1)[1].split(
        '@router.get("/advanced-diagnostics"', 1
    )[0]

    premium_css = 'tailoring_workspace_premium.css?v=tailoring_workspace_finish_r3'
    assert "scan_workspace.css" not in route
    assert premium_css in route
    assert route.index("vendor/tabler/tabler.min.css") < route.index("styles.css?v=")
    assert route.index("styles.css?v=") < route.index("app_redesign.css?v=")
    assert route.index("app_redesign.css?v=") < route.index(premium_css)

    scan_route = source.split("def scan_workspace(", 1)[1]
    assert premium_css not in scan_route
    assert "scan_workspace_review.css" not in scan_route
    assert "scan_workspace_premium.css?v=scan_workspace_premium_r1" in scan_route
    assert SCAN_WORKSPACE_CSS.exists()
    assert SCAN_WORKSPACE_REVIEW_CSS.exists()
    assert SCAN_WORKSPACE_PREMIUM_CSS.exists()


def test_tailoring_workspace_ui_a_preserves_behavior_dom_contracts():
    source = PLANNING_UI.read_text(encoding="utf-8")
    route = source.split('@router.get("/tailoring-workspace"', 1)[1].split(
        '@router.get("/advanced-diagnostics"', 1
    )[0]

    required_ids = [
        "tailoringWorkspaceStatusValue",
        "tailoringWorkspaceRegenerateBtn",
        "tailoringWorkspaceMeta",
        "tailoringWorkspaceSelectedTabsShell",
        "tailoringWorkspaceSelectedTabRow",
        "tailoringWorkspaceInteractiveSummary",
        "tailoringWorkspaceSavedSelectionCard",
        "tailoringWorkspacePreviewName",
        "tailoringWorkspaceModeToggleBtn",
        "tailoringWorkspaceSelectionStatus",
        "tailoringWorkspaceDiscardBtn",
        "tailoringWorkspaceDownloadBtn",
        "tailoringWorkspaceSaveSelectionBtn",
        "tailoringWorkspaceZoomOutBtn",
        "tailoringWorkspaceZoomResetBtn",
        "tailoringWorkspaceZoomInBtn",
        "tailoringWorkspacePreviewMeta",
        "tailoringWorkspaceModeBody",
        "tailoringWorkspaceLiveDraftPreview",
        "tailoringWorkspacePdfScroller",
        "tailoringWorkspacePdfPages",
        "tailoringWorkspaceExportModal",
        "closeTailoringWorkspaceExportModalBtn",
        "tailoringWorkspaceExportPdfBtn",
        "tailoringWorkspaceExportWordBtn",
    ]
    for element_id in required_ids:
        assert f'id="{element_id}"' in route

    for class_name in [
        "tailoring-workspace-layout",
        "tailoring-workspace-pane--left",
        "tailoring-workspace-pane--right",
    ]:
        assert class_name in route


def test_tailoring_workspace_ui_a_preserves_actions_tabs_and_scan_destination():
    source = PLANNING_UI.read_text(encoding="utf-8")
    route = source.split('@router.get("/tailoring-workspace"', 1)[1].split(
        '@router.get("/advanced-diagnostics"', 1
    )[0]

    assert 'id="tailoringWorkspaceOpenScanBtn"' in route
    assert 'href="{scan_href_safe}"' in route
    assert 'escape(f"/scan-workspace?{scan_query}", quote=True)' in route

    tabs = {
        "tailoringWorkspaceSelectedReadyTab": "ready",
        "tailoringWorkspaceSelectedReviewTab": "review",
        "tailoringWorkspaceSelectedFreeEditTab": "free_edit",
    }
    for element_id, state in tabs.items():
        assert f'id="{element_id}"' in route
        assert f'data-tailoring-selected-tab="{state}"' in route


def test_tailoring_workspace_ui_a_css_is_scoped_themed_responsive_and_dependency_free():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    route = PLANNING_UI.read_text(encoding="utf-8").split(
        '@router.get("/tailoring-workspace"', 1
    )[1].split('@router.get("/advanced-diagnostics"', 1)[0]

    assert ".tailoring-workspace-page" in css
    assert "#tailoringWorkspaceExportModal" in css
    assert 'html[data-theme="light"]' in css
    assert 'html[data-theme="dark"]' in css
    assert "@media (max-width:" in css
    assert ":focus-visible" in css
    assert "grid-template-columns: minmax(340px, 38%) minmax(0, 62%)" in css
    assert "--tw-primary: var(--app-primary)" in css

    dependency_markers = [
        "react-resizable-panels",
        "@base-ui/react",
        "@radix-ui",
        "tailwindcss",
        "createRoot(",
    ]
    combined = route + css
    for marker in dependency_markers:
        assert marker not in combined


def test_tailoring_workspace_ui_b_preserves_inner_control_behavior_attributes():
    source = _source()
    telemetry_source = _function_source(
        source, "buildTailoringWorkspaceReviewFilterChip"
    )
    telemetry_renderer = _function_source(
        source, "renderTailoringWorkspaceReviewTelemetryStrip"
    )
    review_source = _function_source(source, "renderReplacementDecisionSection")
    free_edit_source = _function_source(
        source, "renderTailoringWorkspaceFreeEditSection"
    )

    assert 'data-tailoring-review-filter="${escapeHtml(item.key || "")}"' in telemetry_source
    assert "tailoring-review-filter-chip-dot" in telemetry_source
    assert "tailoring-workspace-review-progress" in telemetry_renderer
    assert "Review progress" in telemetry_renderer
    assert 'data-${actionPrefix}-review-action="accepted"' in review_source
    assert 'data-${actionPrefix}-review-action="rejected"' in review_source
    assert 'data-${actionPrefix}-review-edit="${escapeHtml(candidateId)}"' in review_source
    assert 'data-${actionPrefix}-review-candidate="${escapeHtml(candidateId)}"' in review_source
    assert "Accept as-is" in review_source
    assert "Edit manually" in review_source
    assert "Reject" in review_source
    assert 'data-tailoring-free-edit-key="${escapeHtml(row.bulletKey)}"' in free_edit_source
    assert 'data-tailoring-free-edit-score="${escapeHtml(row.bulletKey)}"' in free_edit_source
    assert 'data-tailoring-free-edit-action="${escapeHtml(row.bulletKey)}"' in free_edit_source


def test_tailoring_workspace_ui_b_places_commands_in_job_context_header():
    source = PLANNING_UI.read_text(encoding="utf-8")
    route = source.split('@router.get("/tailoring-workspace"', 1)[1].split(
        '@router.get("/advanced-diagnostics"', 1
    )[0]

    title_position = route.index('<h1 class="tailoring-workspace-title">Tailor resume</h1>')
    status_position = route.index('id="tailoringWorkspaceStatusValue"')
    context_position = route.index('class="tailoring-workspace-context-actions"')
    layout_position = route.index('class="tailoring-workspace-layout"')
    assert title_position < status_position < context_position < layout_position
    assert 'id="tailoringWorkspaceOpenScanBtn"' in route[context_position:layout_position]
    assert 'href="{scan_href_safe}"' in route[context_position:layout_position]
    assert 'id="tailoringWorkspaceRegenerateBtn"' in route[context_position:layout_position]
    assert "tailoring-section-title-actions" not in route


def test_tailoring_workspace_ui_b_styles_compact_filters_cards_and_editors():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    ui_b = css

    assert css.startswith("/* Tailoring Workspace UI-E — canonical route-owned visual system. */")
    assert ".tailoring-selected-tab-row" in ui_b
    assert "margin: 0 18px 16px" in ui_b
    assert ".tailoring-review-filter-chip" in ui_b
    assert ".tailoring-workspace-review-progress" in ui_b
    assert "grid-template-columns: repeat(var(--tw-progress-columns), minmax(0, 1fr))" in ui_b
    assert "background: color-mix" in ui_b
    assert ".tailoring-workspace-review-item-header" in ui_b
    assert ".tailoring-workspace-review-item-body" in ui_b
    assert ".tailoring-workspace-review-content--current" in ui_b
    assert ".tailoring-workspace-review-content--suggested" in ui_b
    assert ".tailoring-workspace-review-signals" in ui_b
    assert ".tailoring-workspace-review-item-footer" in ui_b
    assert ".tailoring-workspace-review-action-btn" in ui_b
    assert ".tailoring-free-edit-textarea" in ui_b
    assert ".tailoring-workspace-free-edit-action" in ui_b
    assert ".tailoring-workspace-anchor-section" in ui_b
    assert ".tailoring-workspace-anchor-item" in ui_b


def test_tailoring_workspace_ui_b_styles_joined_document_controls():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    ui_b = css

    assert ".tailoring-workspace-mode-toggle" in ui_b
    assert "border: 0 !important" in ui_b
    assert ".tailoring-workspace-preview-header-actions" in ui_b
    assert "padding: 2px !important" in ui_b
    assert ".tailoring-workspace-icon-btn" in ui_b
    assert ".tailoring-workspace-icon-btn--save:not(:disabled)" in ui_b
    assert ".tailoring-workspace-icon-btn--save:disabled" in ui_b
    assert ".tailoring-workspace-zoom-btn" in ui_b
    assert ".tailoring-workspace-zoom-value" in ui_b


def test_tailoring_workspace_ui_b_pdf_viewport_is_centered_vertical_only_and_resize_aware():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    ui_b = css
    source = _source()
    state_source = source.split("const tailoringWorkspacePdfState = {", 1)[1].split("};", 1)[0]
    binder_source = _function_source(source, "bindTailoringWorkspacePreviewControls")
    fit_source = _async_function_source(source, "computeTailoringWorkspaceFitPageScale")

    assert ".tailoring-workspace-pdf-scroller" in ui_b
    assert "overflow-x: hidden" in ui_b
    assert "overflow-y: auto" in ui_b
    assert ".tailoring-workspace-pdf-pages" in ui_b
    assert "align-items: center" in ui_b
    assert ".tailoring-workspace-pdf-page" in ui_b
    assert "margin-inline: auto" in ui_b
    assert "resizeObserver: null" in state_source
    assert 'typeof ResizeObserver !== "undefined"' in binder_source
    assert "resizeObserver.observe(pdfScroller)" in binder_source
    assert "scheduleTailoringWorkspaceFitPageRerender()" in binder_source
    assert "metrics.availableWidth / baseViewport.width" in fit_source


def test_tailoring_workspace_ui_b_structural_markup_is_workspace_only():
    source = _source()
    renderer = _function_source(source, "renderReplacementDecisionSection")
    interactive = _function_source(source, "renderTailoringInteractiveSummaryInto")

    assert "workspacePresentation = false" in renderer
    assert 'rootId === "tailoringWorkspaceInteractiveSummary"' in interactive
    assert "tailoring-workspace-review-item-header" in renderer
    assert "tailoring-workspace-review-item-body" in renderer
    assert "tailoring-workspace-review-item-footer" in renderer
    assert "workspacePresentation," in interactive


def test_tailoring_workspace_ui_c_preserves_full_progress_and_anchor_content_contracts():
    source = _source()
    filter_source = _function_source(source, "getTailoringWorkspaceReviewFilterItems")
    chip_source = _function_source(source, "buildTailoringWorkspaceReviewFilterChip")
    icon_source = _function_source(source, "buildTailoringWorkspaceReviewFilterIcon")
    anchor_source = _function_source(source, "renderTailoringAnchorEvidenceSection")

    for label in ["Remaining", "Accepted as-is", "Edited after accept", "Rejected"]:
        assert f'label: "{label}"' in filter_source
    assert 'data-tailoring-review-filter="${escapeHtml(item.key || "")}"' in chip_source
    assert "tailoring-review-filter-chip-label" in chip_source
    assert "tailoring-review-filter-chip-count" in chip_source
    assert "accepted_as_is" in icon_source
    assert "edited_after_accept" in icon_source
    assert "rejected" in icon_source

    for contract in [
        "item.jd_signal_terms",
        "item.source",
        "item.current_evidence",
        "item.parent_bullet",
        "getTailoringAnchorReviewLabel(item)",
        "getTailoringAnchorReviewNote(item)",
    ]:
        assert contract in anchor_source
    assert "tailoring-workspace-review-item--anchor" in anchor_source
    assert "tailoring-workspace-anchor-source" in anchor_source
    assert "tailoring-workspace-anchor-evidence" in anchor_source
    assert 'workspacePresentation ? "Evidence" : "Current bullet"' in anchor_source


def test_tailoring_workspace_ui_c_uses_inline_stroke_icons_and_preserves_toolbar_ids():
    source = PLANNING_UI.read_text(encoding="utf-8")
    route = source.split('@router.get("/tailoring-workspace"', 1)[1].split(
        '@router.get("/advanced-diagnostics"', 1
    )[0]

    for element_id in [
        "tailoringWorkspaceModeToggleBtn",
        "tailoringWorkspaceDiscardBtn",
        "tailoringWorkspaceDownloadBtn",
        "tailoringWorkspaceSaveSelectionBtn",
        "tailoringWorkspaceZoomOutBtn",
        "tailoringWorkspaceZoomResetBtn",
        "tailoringWorkspaceZoomInBtn",
        "tailoringWorkspacePdfScroller",
        "tailoringWorkspacePdfPages",
    ]:
        assert f'id="{element_id}"' in route

    assert route.count('class="tailoring-workspace-toolbar-icon') >= 6
    assert 'stroke="currentColor"' in route
    assert "tailoring-workspace-icon--discard" not in route
    assert "tailoring-workspace-icon--download" not in route
    assert "tailoring-workspace-icon--save" not in route


def test_tailoring_workspace_ui_c_converges_spacing_progress_toolbar_and_anchor_styles():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    ui_c = css

    assert ".tailoring-workspace-selected-tabs" in ui_c
    assert "padding: 0" in ui_c
    assert "margin: 0 18px 12px" in ui_c
    assert ".tailoring-workspace-review-progress" in ui_c
    assert "background: color-mix" in ui_c
    assert ".tailoring-review-filter-chip--caution.is-active" in ui_c
    assert ".tailoring-review-filter-chip--safe.is-active" in ui_c
    assert ".tailoring-review-filter-chip--neutral.is-active" in ui_c
    assert ".tailoring-review-filter-chip--danger.is-active" in ui_c
    assert "overflow-x: hidden" in ui_c
    assert "white-space: normal" in ui_c
    assert ".tailoring-workspace-toolbar-icon" in ui_c
    assert ".tailoring-workspace-preview-header-actions" in ui_c
    assert "border: 0 !important" in ui_c
    assert ".tailoring-workspace-preview-toolbar-left" in ui_c
    assert ".tailoring-workspace-pdf-scroller" in ui_c
    assert "padding: 14px clamp(18px, 3vw, 36px) 34px" in ui_c
    assert "overflow-x: hidden" in ui_c
    assert "overflow-y: auto" in ui_c
    assert ".tailoring-workspace-anchor-item" in ui_c
    assert ".tailoring-workspace-anchor-evidence" in ui_c


def test_tailoring_workspace_ui_d_retires_legacy_page_visual_owners():
    legacy = STYLES_CSS.read_text(encoding="utf-8")

    retired_selectors = [
        ".tailoring-workspace-page {",
        ".tailoring-workspace-header {",
        ".tailoring-workspace-layout {",
        ".tailoring-workspace-pane {",
        ".tailoring-workspace-selected-tabs {",
        ".tailoring-workspace-preview-header {",
        ".tailoring-workspace-preview-toolbar {",
        ".tailoring-workspace-mode-toggle {",
        ".tailoring-workspace-review-telemetry-row {",
        ".tailoring-review-filter-chip {",
        "#tailoringWorkspaceExportModal",
    ]
    for selector in retired_selectors:
        assert selector not in legacy

    for retired_marker in [
        "tailoring workspace export modal",
        "tailoring workspace canonical layout",
        "tailoring tabs stability fix",
    ]:
        assert retired_marker not in legacy


def test_tailoring_workspace_ui_d_keeps_scan_document_rendering_primitives_shared():
    shared_css = STYLES_CSS.read_text(encoding="utf-8")
    scan_css = SCAN_WORKSPACE_CSS.read_text(encoding="utf-8")
    scan_js = SCAN_WORKSPACE_JS.read_text(encoding="utf-8")
    shared_primitives = [
        "tailoring-workspace-doc-page",
        "tailoring-workspace-doc-line",
        "tailoring-workspace-doc-bullet-row",
        "tailoring-workspace-doc-line-copy",
        "tailoring-workspace-doc-bullet-copy",
        "tailoring-workspace-doc-section-rule",
        "tailoring-workspace-doc-link",
    ]

    for class_name in shared_primitives:
        assert f".{class_name}" in shared_css or f".{class_name}" in scan_css
        assert class_name in scan_js

    premium_css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    assert ".tailoring-workspace-page .tailoring-workspace-doc-link" in premium_css

    # Generic edit-card primitives also serve the Planning modal; the premium
    # sheet supplies the route-scoped Tailoring Workspace presentation.
    assert ".tailoring-edit-card," in shared_css
    assert "workspacePresentation = false" in _source()


def test_tailoring_workspace_ui_e_has_one_canonical_major_component_base_each():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    canonical_bases = [
        ".tailoring-workspace-selected-tabs {",
        ".tailoring-selected-tab-row {",
        "#tailoringWorkspacePage .tailoring-selected-tab-btn {",
        ".tailoring-workspace-review-progress {",
        ".tailoring-workspace-review-telemetry-row {",
        "#tailoringWorkspacePage .tailoring-review-filter-chip {",
        "#tailoringWorkspacePage .tailoring-workspace-mode-toggle {",
        ".tailoring-workspace-preview-header-actions {",
        "#tailoringWorkspacePage .tailoring-workspace-icon-btn {",
        ".tailoring-workspace-preview-toolbar-left {",
        ".tailoring-workspace-zoom-value {",
        ".tailoring-workspace-export-modal {",
    ]

    assert "canonical route-owned visual system" in css
    for selector in canonical_bases:
        assert css.count(f"\n{selector}") == 1


def test_tailoring_workspace_ui_e_progress_uses_flat_semantic_metric_states():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    chip_base = css.split(".tailoring-review-filter-chip {", 1)[1].split("}", 1)[0]

    assert "background: transparent !important" in chip_base
    assert "border-left: 1px solid var(--tw-border) !important" in chip_base
    for modifier in ["safe", "caution", "neutral", "danger"]:
        assert f".tailoring-review-filter-chip--{modifier}.is-active" in css
        assert f".tailoring-review-filter-chip--{modifier} .tailoring-review-filter-chip-dot" in css


def test_tailoring_workspace_ui_f_pdf_render_signature_skips_only_equivalent_requests():
    source = _source()
    signature_source = _function_source(
        source, "buildTailoringWorkspacePdfRenderSignature"
    )
    skip_source = _function_source(source, "shouldSkipTailoringWorkspacePdfRender")
    script = f"""
{signature_source}
const tailoringWorkspacePdfState = {{
  pendingRenderSignature: "",
  renderedSignature: "",
}};
{skip_source}
const base = {{
  documentId: 7,
  availableWidth: 640,
  scale: 1.125,
  previewMode: "pdf",
  previewModeRevision: 2,
  deviceScale: 2,
}};
const signature = buildTailoringWorkspacePdfRenderSignature(base);
tailoringWorkspacePdfState.renderedSignature = signature;
const completedDuplicateSkipped = shouldSkipTailoringWorkspacePdfRender(signature);
tailoringWorkspacePdfState.renderedSignature = "";
tailoringWorkspacePdfState.pendingRenderSignature = signature;
const pendingDuplicateSkipped = shouldSkipTailoringWorkspacePdfRender(signature);
const changesPermitRender = [
  {{ ...base, documentId: 8 }},
  {{ ...base, availableWidth: 641 }},
  {{ ...base, scale: 1.205 }},
  {{ ...base, previewModeRevision: 3 }},
].every((request) => !shouldSkipTailoringWorkspacePdfRender(
  buildTailoringWorkspacePdfRenderSignature(request)
));
console.log(JSON.stringify({{
  completedDuplicateSkipped,
  pendingDuplicateSkipped,
  changesPermitRender,
}}));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result == {
        "completedDuplicateSkipped": True,
        "pendingDuplicateSkipped": True,
        "changesPermitRender": True,
    }


def test_tailoring_workspace_ui_f_noop_render_returns_before_pdf_dom_changes():
    source = _source()
    render_source = _async_function_source(source, "renderTailoringWorkspacePdfPages")
    guard = "if (shouldSkipTailoringWorkspacePdfRender(renderSignature)) return;"

    assert guard in render_source
    assert render_source.index(guard) < render_source.index(
        "tailoringWorkspacePdfState.pendingRenderSignature = renderSignature"
    )
    assert render_source.index(guard) < render_source.index(
        'pagesRoot.classList.add("hidden")'
    )
    assert "pagesRoot.replaceChildren(fragment)" in render_source
    assert 'pagesRoot.innerHTML = ""' not in render_source
    assert "hasRenderedPages" in render_source


def test_tailoring_workspace_ui_f_review_progress_is_a_non_scrolling_responsive_grid():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    source = _source()
    telemetry_source = _function_source(
        source, "renderTailoringWorkspaceReviewTelemetryStrip"
    )
    filter_source = _function_source(source, "getTailoringWorkspaceReviewFilterItems")
    row_rule = css.split(
        ".tailoring-workspace-review-telemetry-row {", 1
    )[1].split("}", 1)[0]

    assert "display: grid" in row_rule
    assert "grid-template-columns: repeat(var(--tw-progress-columns), minmax(0, 1fr))" in row_rule
    assert "overflow-x: hidden" in row_rule
    assert "overflow-x: auto" not in row_rule
    assert "overflow-x: scroll" not in row_rule
    assert "--tw-progress-columns: 2" in css
    assert "--tw-progress-columns: 1" in css
    assert "items.map(buildTailoringWorkspaceReviewFilterChip)" in telemetry_source
    for label in ["Remaining", "Accepted as-is", "Edited after accept", "Rejected"]:
        assert f'label: "{label}"' in filter_source


def test_tailoring_workspace_ui_g_enlarges_document_controls_and_preserves_ids():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    route = PLANNING_UI.read_text(encoding="utf-8").split(
        '@router.get("/tailoring-workspace"', 1
    )[1].split('@router.get("/advanced-diagnostics"', 1)[0]
    mode_rule = css.split(
        "#tailoringWorkspacePage .tailoring-workspace-mode-toggle {", 1
    )[1].split("}", 1)[0]
    icon_rule = css.split(
        "#tailoringWorkspacePage .tailoring-workspace-icon-btn {", 1
    )[1].split("}", 1)[0]
    mode_icon_rule = css.split(
        "#tailoringWorkspacePage .tailoring-workspace-mode-toggle .tailoring-workspace-toolbar-icon {",
        1,
    )[1].split("}", 1)[0]

    assert "min-height: 40px" in mode_rule
    assert "width: 40px" in icon_rule
    assert "height: 40px" in icon_rule
    assert "width: 18px" in mode_icon_rule
    assert "height: 18px" in mode_icon_rule
    for element_id in [
        "tailoringWorkspaceModeToggleBtn",
        "tailoringWorkspaceDiscardBtn",
        "tailoringWorkspaceDownloadBtn",
        "tailoringWorkspaceSaveSelectionBtn",
        "tailoringWorkspaceZoomOutBtn",
        "tailoringWorkspaceZoomResetBtn",
        "tailoringWorkspaceZoomInBtn",
    ]:
        assert f'id="{element_id}"' in route


def test_tailoring_workspace_ui_g_progress_is_two_by_two_with_compact_single_item():
    css = TAILORING_PREMIUM_CSS.read_text(encoding="utf-8")
    source = _source()
    filter_source = _function_source(source, "getTailoringWorkspaceReviewFilterItems")
    row_rule = css.split(
        ".tailoring-workspace-review-telemetry-row {", 1
    )[1].split("}", 1)[0]
    single_rule = css.split(
        "#tailoringWorkspacePage .tailoring-review-filter-chip:only-child {", 1
    )[1].split("}", 1)[0]
    single_label_rule = css.split(
        "#tailoringWorkspacePage .tailoring-review-filter-chip:only-child .tailoring-review-filter-chip-label {",
        1,
    )[1].split("}", 1)[0]

    assert "--tw-progress-columns: 2" in css
    assert "grid-template-columns: repeat(var(--tw-progress-columns), minmax(0, 1fr))" in row_rule
    assert "overflow-x: hidden" in row_rule
    assert "overflow-x: auto" not in row_rule
    assert "grid-column: 1 / -1" in single_rule
    assert "justify-self: start" in single_rule
    assert "width: min(100%, 180px)" in single_rule
    assert "white-space: nowrap" in single_label_rule
    assert 'label: "Manual edits"' in filter_source
    for label in ["Remaining", "Accepted as-is", "Edited after accept", "Rejected"]:
        assert f'label: "{label}"' in filter_source


def test_tailoring_workspace_ui_g_centers_explicit_pdf_focus_in_right_scroller():
    source = _source()
    center_source = _function_source(
        source, "centerTailoringWorkspacePdfHighlightInScroller"
    )
    script = f"""
const calls = [];
const scroller = {{
  scrollTop: 200,
  clientHeight: 400,
  scrollHeight: 1000,
  getBoundingClientRect: () => ({{ top: 100 }}),
  scrollTo: (options) => calls.push(options),
}};
const qs = (id) => id === "tailoringWorkspacePdfScroller" ? scroller : null;
{center_source}
const highlight = {{
  getBoundingClientRect: () => ({{ top: 390, height: 20 }}),
}};
centerTailoringWorkspacePdfHighlightInScroller(highlight, {{ smooth: true }});
console.log(JSON.stringify(calls[0]));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {"top": 300, "behavior": "smooth"}
    assert 'qs("tailoringWorkspacePdfScroller")' in center_source
    assert "scroller.clientHeight / 2" in center_source
    assert "scroller.scrollHeight - scroller.clientHeight" in center_source


def test_tailoring_workspace_ui_g_centers_only_explicit_focus_and_keeps_render_guard():
    source = _source()
    binder_source = _function_source(source, "bindTailoringWorkspaceSelectionHandlers")
    sync_source = _function_source(source, "syncTailoringWorkspacePreviewHighlight")
    render_source = _async_function_source(source, "renderTailoringWorkspacePdfPages")
    schedule_source = _function_source(source, "scheduleTailoringWorkspaceFitPageRerender")
    highlight_source = _function_source(source, "applyTailoringWorkspacePdfHighlight")

    assert "explicitFocusOptions = { centerInScroller: true, smooth: true }" in binder_source
    assert "focusTailoringWorkspaceCandidateInPreview(" in binder_source
    assert "focusTailoringWorkspaceBulletKeyInPreview(" in binder_source
    assert "explicitFocusOptions" in binder_source
    assert "focusTailoringWorkspaceBulletKeyInPreview(focusedBulletKey);" in sync_source
    assert "focusTailoringWorkspaceCandidateInPreview(selectedIds[selectedIds.length - 1]);" in sync_source
    assert "centerTailoringWorkspacePdfHighlightInScroller" not in render_source
    assert "centerInScroller" not in render_source
    assert "centerTailoringWorkspacePdfHighlightInScroller" not in schedule_source
    assert "scrollIntoView" not in highlight_source
    assert "if (centerInScroller)" in highlight_source
    assert "shouldSkipTailoringWorkspacePdfRender(renderSignature)" in render_source
    assert "pendingRenderSignature" in render_source


def test_tailoring_workspace_ui_e_removes_legacy_visual_classes_from_route_markup():
    source = PLANNING_UI.read_text(encoding="utf-8")
    route = source.split('@router.get("/tailoring-workspace"', 1)[1].split(
        '@router.get("/advanced-diagnostics"', 1
    )[0]

    for legacy_class in [
        'class="card',
        "scheduler-table-tabs",
        "scheduler-tab-row",
        "scheduler-tab-btn",
        "ghost-btn",
        "btn-sm",
        'class="modal-card',
        'class="modal-header',
    ]:
        assert legacy_class not in route

    for dedicated_class in [
        "tailoring-workspace-selected-tabs",
        "tailoring-selected-tabs-shell",
        "tailoring-selected-tab-row",
        "tailoring-selected-tab-btn",
        "tailoring-workspace-icon-btn",
        "tailoring-workspace-zoom-btn",
        "tailoring-workspace-export-format-btn",
    ]:
        assert dedicated_class in route


def test_tailoring_workspace_ui_e_generated_actions_use_dedicated_visual_classes():
    source = _source()
    free_edit = _function_source(source, "renderTailoringWorkspaceFreeEditSection")
    inline_score = _function_source(source, "refreshTailoringWorkspaceInlineScoreControls")
    replacement = _function_source(source, "renderReplacementDecisionSection")

    assert 'class="tailoring-workspace-free-edit-action"' in free_edit
    assert 'classList.toggle("tailoring-workspace-free-edit-action--save"' in inline_score
    assert 'workspacePresentation ? "tailoring-workspace-review-action-btn"' in replacement
    assert 'workspacePresentation ? "tailoring-workspace-select-btn"' in replacement


def test_bulk_rerun_reuses_the_existing_settings_overlay_and_start_path():
    """Re-run is the same settings step and the same executor, only scoped."""
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    rerun_source = planning[
        planning.index("async function startBulkGenerateSuggestionsRerun") :
        planning.index("function updateBulkGenerateSuggestionsConfiguration")
    ]
    selection_source = planning[
        planning.index("function getPlanningBulkSuggestionSelection") :
        planning.index("function buildPlanningWorklistBridgeState")
    ]

    # Superseded: the Results Center re-run now starts DIRECTLY and must not
    # reopen the first-run configuration overlay.
    assert 'renderBulkGenerateSuggestionsOverlay("confirm"' not in rerun_source
    assert "resetBulkGenerateSuggestionsConfiguration(" not in rerun_source
    assert "getBulkGenerateSuggestionsOverlay()" in rerun_source  # admission guard only
    # No parallel executor: it delegates to the one existing executor.
    assert "await executeBulkGenerateSuggestions()" in rerun_source
    code_only = "\n".join(
        line for line in rerun_source.splitlines()
        if not line.strip().startswith(("*", "/*", "//"))
    )
    for forbidden in ("postJson", "fetch(", "/planning/bulk-generation/start"):
        assert forbidden not in code_only
    # Existing admission guards are still respected before opening.
    assert "bulkGenerateSuggestionsState.isRunning" in rerun_source
    assert "generateSuggestionsState.isRunning" in rerun_source
    # Selected jobs are the MAXIMUM scope; filters can only narrow it.
    assert 'String(config.mode || "initial") === "rerun"' in selection_source
    assert "rerunScope" in selection_source
    assert "scopeRows.filter(" in selection_source


def test_planning_exposes_only_the_public_brandfetch_client_id():
    ui = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    config_source = ui[
        ui.index("def _planning_public_config_script") :
        ui.index("_PLANNING_JSON_CONTEXT_SUFFIXES")
    ]
    assert 'os.getenv("BRANDFETCH_CLIENT_ID", "")' in config_source
    assert "_safe_json_script(" in config_source
    # Never a private Brandfetch key, and no other credential family.
    for forbidden in ("BRANDFETCH_API_KEY", "BRANDFETCH_SECRET", "API_KEY"):
        assert forbidden not in config_source
    assert "window.__APPLYLENS_PLANNING_CONFIG__" in ui


def test_company_logo_resolution_is_bridge_owned_deduplicated_and_unpersisted():
    """planning.js owns every logo request; the React island stays network-free."""
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    resolver = planning[
        planning.index("const planningCompanyLogoDomains") :
        planning.index("function resetBulkGenerateResultsState")
    ]

    # One in-memory page-lifetime cache, one request per unresolved company.
    assert "new Map()" in resolver
    assert "planningCompanyLogoDomains.has(normalized)" in resolver
    assert "planningCompanyLogoDomains.set(normalized, pending)" in resolver
    # Deterministic matching only: exact normalized name, verified tie-break.
    assert "normalizePlanningCompanyName(entry?.name) === normalized" in resolver
    assert "verified.length === 1" in resolver
    # Never persisted anywhere.
    for forbidden in ("localStorage", "sessionStorage", "postJson", "INSERT", "indexedDB"):
        assert forbidden not in resolver
    # Requests are scoped to the modal, not the whole page load.
    assert 'action.type === "bulk_view_results"' in planning
    assert "void resolveBulkResultCompanyLogos();" in planning
    # Absent client id short-circuits before any network call.
    assert "if (!clientId) return;" in resolver

    react = Path("frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(encoding="utf-8")
    assert "fetch(" not in react
    assert "cdn.brandfetch.io" in react
    assert 'loading="lazy"' in react
    assert "api.brandfetch.io" not in react


def test_company_logo_matching_is_slug_tolerant_but_still_exact():
    """`andurilindustries` (ATS board slug) and `Anduril Industries` must reduce
    to the same identity, without introducing fuzzy matching."""
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    resolver = planning[
        planning.index("function normalizePlanningCompanyName") :
        planning.index("function resetBulkGenerateResultsState")
    ]

    # Whitespace is removed entirely, so a slug and a spaced brand name match.
    assert 'replace(/[^a-z0-9]+/g, "")' in resolver
    assert 'replace(/[^a-z0-9]+/g, " ")' not in resolver

    # Brandfetch commonly returns several identically named brands on different
    # domains; its own `verified` flag is the deterministic tie-break.
    assert "entry?.verified === true" in resolver
    assert "verified.length === 1" in resolver
    assert "named.length === 1" in resolver

    # Still exact-only: no similarity, ranking, or first-result-wins.
    for forbidden in ("levenshtein", "includes(", "startsWith(", "results[0]", "_score", "sort("):
        assert forbidden not in resolver


def test_company_logo_uses_the_explicit_brandfetch_domain_route():
    react = Path("frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(encoding="utf-8")
    assert "cdn.brandfetch.io/domain/" in react
    assert "/w/64/h/64/fallback/lettermark/type/icon" in react
    assert 'loading="lazy"' in react
    # No referrer policy override: Brandfetch requires a normal browser Referer.
    assert "no-referrer" not in react


def test_bulk_results_controls_opt_out_of_the_global_important_skin():
    """The page-level `button`/`input` skins use !important, which no stylesheet
    specificity can beat. Modal controls must join the existing :not() opt-out
    chain, exactly like .planning-react-bulk-generate already does."""
    button_classes = (
        "planning-bulk-results__close",
        "planning-bulk-results__pill",
        "planning-bulk-results__clear",
        "planning-bulk-results__secondary",
        "planning-bulk-results__primary",
    )
    input_classes = (
        "planning-bulk-results__search-input",
        "planning-bulk-results__checkbox",
    )

    def split_selectors(selector_line):
        """Split a selector list while ignoring commas inside :not()/:where()."""
        depth = 0
        start = 0
        selectors = []
        for index, character in enumerate(selector_line):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
            elif character == "," and depth == 0:
                selectors.append(selector_line[start:index])
                start = index + 1
        selectors.append(selector_line[start:].removesuffix(" {").removesuffix("{"))
        return [selector.strip() for selector in selectors]

    for path in ("src/app/static/app_redesign.css", "src/app/static/styles.css"):
        css = Path(path).read_text(encoding="utf-8")
        assert "::placeholder:where(" not in css
        for line in css.splitlines():
            stripped = line.strip()
            # Excluded via a single zero-specificity :where(:not(...)) list so
            # the surrounding cascade keeps its exact original weight.
            for selector in (
                selector for selector in split_selectors(stripped)
                if selector.startswith("button:not(") or selector.startswith("body button:not(")
            ):
                for name in button_classes:
                    assert f".{name}" in selector, f"{path}: button skin does not exclude {name}"
                assert ":where(:not(" in selector
            for selector in (
                selector for selector in split_selectors(stripped)
                if selector.startswith("input:not(")
                or selector.startswith('html[data-theme="light"] input:not(')
            ):
                for name in input_classes:
                    assert f".{name}" in selector, f"{path}: input skin does not exclude {name}"
                assert ":where(:not(" in selector
            if stripped.startswith(":where(a, button, input, select, textarea, [tabindex])"):
                assert ":where(:not(.planning-bulk-results__search-input))" in stripped


def test_bulk_results_search_parent_is_the_only_visual_field_surface():
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    shell_selector = ".planning-bulk-results .planning-bulk-results__search {"
    shell = css[css.index(shell_selector) : css.index("}", css.index(shell_selector))]
    for visual_owner in ("border:", "border-radius:", "background:"):
        assert visual_owner in shell

    input_selector = ".planning-bulk-results .planning-bulk-results__search-input {"
    input_rule = css[css.index(input_selector) : css.index("}", css.index(input_selector))]
    for reset in (
        "border: 0",
        "border-radius: 0",
        "outline: none",
        "appearance: none",
        "background: transparent",
        "background-image: none",
        "box-shadow: none",
    ):
        assert reset in input_rule


def test_bulk_results_clear_selection_is_a_compact_secondary_button():
    react = Path("frontend/executive-kpi/src/PlanningWorklist.tsx").read_text(encoding="utf-8")
    clear_control = react[
        react.index('className="planning-bulk-results__clear"') - 80 :
        react.index("Clear selection") + len("Clear selection")
    ]
    assert '<button' in clear_control
    assert 'type="button"' in clear_control

    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    selector = ".planning-bulk-results .planning-bulk-results__clear {"
    rule = css[css.index(selector) : css.index("}", css.index(selector))]
    assert "height: 36px" in rule
    assert "padding: 0 12px" in rule
    assert "border: 1px solid var(--bulk-control-border)" in rule
    assert "border-radius: 8px" in rule
    assert "background: var(--bulk-control-bg)" in rule
    assert "box-shadow: none" in rule
    assert "text-decoration: none" in rule


def test_bulk_results_theme_blocks_define_palette_tokens_only():
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    dark_selector = (
        'html:not([data-theme="light"]) .planning-bulk-results,\n'
        'html[data-theme="dark"] .planning-bulk-results {'
    )
    light_selector = 'html[data-theme="light"] .planning-bulk-results {'
    for selector in (dark_selector, light_selector):
        start = css.index(selector)
        rule = css[start : css.index("}", start)]
        body = rule.split("{", 1)[1]
        declarations = [line.strip() for line in body.splitlines() if line.strip()]
        assert len(declarations) > 30
        assert all(line.startswith("--bulk-") for line in declarations)
        for token in (
            "--bulk-bg:",
            "--bulk-text-strong:",
            "--bulk-control-bg:",
            "--bulk-table-head:",
            "--bulk-row-selected:",
            "--bulk-neutral-bg:",
            "--bulk-primary-bg:",
        ):
            assert token in rule


def test_bulk_results_header_adds_top_breathing_room_without_growing():
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    selector = ".planning-bulk-results .planning-bulk-results__head {"
    rule = css[css.index(selector) : css.index("}", css.index(selector))]
    assert "height: 78px" in rule
    assert "box-sizing: border-box" in rule
    assert "padding: 10px 18px 0 20px" in rule


def test_bulk_results_neutral_badge_and_active_filter_use_theme_tokens():
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    neutral_selector = ".planning-bulk-results .planning-bulk-results__badge.is-neutral {"
    neutral = css[css.index(neutral_selector) : css.index("}", css.index(neutral_selector))]
    for token in ("--bulk-neutral-text", "--bulk-neutral-bg", "--bulk-neutral-border"):
        assert token in neutral

    active_selector = ".planning-bulk-results .planning-bulk-results__pill.is-active {"
    active = css[css.index(active_selector) : css.index("}", css.index(active_selector))]
    # Superseded contract: selection now ONLY outlines; the pill keeps its
    # own semantic tone, so .is-active declares no background or text colour.
    assert "border-color: var(--bulk-accent)" in active
    assert "var(--bulk-accent-ring)" in active
    assert "background:" not in active


def test_bulk_results_bridge_publishes_truthful_resume_score_pair_fields():
    javascript = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    score_start = javascript.index("function planningResumeMatchScore")
    score_fn = javascript[score_start : javascript.index("/** Join persisted Bulk history", score_start)]
    assert "normalizeResumeName(selectedResume)" in score_fn
    assert "normalizeResumeName(row.winner_resume)" in score_fn
    assert "row.winner_score" in score_fn
    assert "row.runner_up_resume || row.runnerup_resume" in score_fn
    assert "row.runner_up_score ?? row.runnerup_score" in score_fn

    merge_start = javascript.index("function mergeBulkResultItems")
    merge_fn = javascript[merge_start : javascript.index("/**\n * Company -> employer", merge_start)]
    for field in ("winner_resume:", "winner_score:", "runner_up_resume:", "runner_up_score:", "match_score:"):
        assert field in merge_fn


def test_bulk_results_rows_own_a_canonical_theme_cell_surface():
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    selector = (
        ".planning-bulk-results .planning-bulk-results__table "
        "tbody .planning-bulk-results__row > td {"
    )
    rule = css[css.index(selector) : css.index("}", css.index(selector))]
    assert "background:" in rule
    assert "color:" in rule
    assert rule.count("!important") == 2
    for state in (":hover > td", ".is-selected > td", ".is-selected:hover > td"):
        assert state in css


def test_bulk_results_modal_allocates_all_spare_height_to_the_table():
    """Header/cards/toolbar must not push the table below the fold."""
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    shell = css[
        css.index(".planning-bulk-results {") :
        css.index(".planning-bulk-results:focus-visible")
    ]
    assert "display: grid" in shell
    assert "grid-template-rows: auto auto auto minmax(0, 1fr) auto" in shell
    assert "min-height: 0" in shell

    table_wrap = css[
        css.index(".planning-bulk-results .planning-bulk-results__table-wrap {") :
    ][:400]
    assert "min-height: 0" in table_wrap
    assert "overflow-y: auto" in table_wrap
    assert "overflow-x: hidden" in table_wrap


def _bulk_results_base_selectors(css_text):
    """Base (non-state, non-media) `.planning-bulk-results*` selectors."""
    import collections
    import re as _re

    text = _re.sub(r"/\*.*?\*/", "", css_text, flags=_re.S)
    state = _re.compile(r"(:hover|:focus|:focus-within|:focus-visible|:disabled|:checked|::[a-z-]+|\.is-[a-z-]+|\[)")
    counts = collections.Counter()
    depth = media = 0
    for match in _re.finditer(r"@media[^{]*\{|\{|\}|[^{}]+", text):
        token = match.group(0)
        if token.startswith("@media"):
            media += 1
            depth += 1
            continue
        if token == "{":
            depth += 1
            continue
        if token == "}":
            depth -= 1
            if media and depth < media:
                media -= 1
            continue
        if depth != media or media:
            continue
        for selector in token.split(","):
            selector = " ".join(selector.split())
            if ".planning-bulk-results" not in selector or state.search(selector):
                continue
            counts[selector] += 1
    return counts


def test_bulk_results_css_has_exactly_one_base_block_per_selector():
    """Maintainability guard: no stacking a second copy of a selector later in
    the file. State (:hover/.is-active/...) and @media overrides are allowed."""
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    counts = _bulk_results_base_selectors(css)
    duplicates = {sel: n for sel, n in counts.items() if n > 1}
    assert not duplicates, f"duplicate base selectors: {sorted(duplicates)}"
    # The modal really is defined here (guards against an empty/no-op audit).
    assert len(counts) > 25


def test_served_stylesheets_carry_only_a_zero_specificity_modal_opt_out():
    """app_redesign.css / styles.css must hold NO modal design - only the
    :where(:not(...)) exclusion, which contributes zero specificity so the
    existing shell cascade (notification/theme/profile buttons) is untouched."""
    for path in ("src/app/static/app_redesign.css", "src/app/static/styles.css"):
        css = Path(path).read_text(encoding="utf-8")
        mentions = css.count("planning-bulk-results")
        inside_where = css.count(":where(:not(.planning-bulk-results")
        assert mentions > 0
        # Every single mention lives inside a :where() opt-out list.
        assert mentions == sum(
            line.count("planning-bulk-results")
            for line in css.splitlines()
            if ":where(:not(.planning-bulk-results" in line
        ), f"{path} contains modal styling outside the opt-out"
        assert inside_where > 0
        # No modal colour/layout leaked into the shared sheets.
        for leaked in (".planning-bulk-results--dark", ".planning-bulk-results__table {"):
            assert leaked not in css


def test_modal_opt_out_does_not_touch_shared_shell_controls():
    """The opt-out must never change which rules match the shell toolbar."""
    import re as _re

    shell = ("notification-btn", "theme-toggle-btn", "profile-avatar-btn",
             "profile-menu-button", "notification-chip")
    where = _re.compile(r":where\(:not\([^()]*\)\)")
    for path in ("src/app/static/app_redesign.css", "src/app/static/styles.css"):
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if ":where(:not(.planning-bulk-results" not in stripped:
                continue
            # The opt-out lists modal classes only - never a shell control.
            opt_out = where.search(stripped).group(0)
            for name in shell:
                assert name not in opt_out
            # The entire exclusion remains inside :where(), so the inner
            # :not() contributes zero selector specificity.
            assert opt_out.startswith(":where(:not(")


def _bulk_theme_vars(css_text, selector):
    """Read the --bulk-* custom properties from one modal theme block."""
    import re as _re

    start = css_text.index(selector)
    block = css_text[start:css_text.index("}", start)]
    return dict(_re.findall(r"(--bulk-[a-z0-9-]+)\s*:\s*([^;]+);", block))


def _relative_luminance(hex_colour):
    value = hex_colour.strip().lstrip("#")
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground, background):
    a, b = _relative_luminance(foreground), _relative_luminance(background)
    high, low = max(a, b), min(a, b)
    return (high + 0.05) / (low + 0.05)


def test_filter_pills_carry_a_semantic_tone_in_both_themes():
    """Every filter has its OWN default background, present whether or not it
    is selected. Tones are composed from existing semantic tokens."""
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    expected = {
        "is-tone-all": "--bulk-accent-fill",
        "is-tone-generated": "--bulk-success-bg",
        "is-tone-safe": "--bulk-neutral-bg",
        "is-tone-attention": "--bulk-attention-bg",
    }
    for modifier, token in expected.items():
        anchor = f".planning-bulk-results .planning-bulk-results__pill.{modifier} {{"
        assert anchor in css, f"missing tone modifier {modifier}"
        block = css[css.index(anchor):css.index("}", css.index(anchor))]
        assert "--pill-bg:" in block and token in block
        for variable in ("--pill-border:", "--pill-text:", "--pill-count-bg:", "--pill-count-text:"):
            assert variable in block, f"{modifier} missing {variable}"

    # Both themes define every token those tones consume.
    for selector in (".planning-bulk-results {", 'html[data-theme="light"] .planning-bulk-results {'):
        variables = _bulk_theme_vars(css, selector)
        for token in ("--bulk-accent-fill", "--bulk-success-bg", "--bulk-neutral-bg",
                      "--bulk-attention-bg", "--bulk-neutral-border", "--bulk-neutral-text"):
            assert token in variables, f"{selector} missing {token}"


def test_active_filter_only_adds_an_outline_and_never_replaces_the_tone():
    """Selection must not repaint the pill: no background/colour in .is-active."""
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    anchor = ".planning-bulk-results .planning-bulk-results__pill.is-active {"
    block = css[css.index(anchor):css.index("}", css.index(anchor))]

    assert "border-color: var(--bulk-accent)" in block
    assert "box-shadow:" in block
    # The selected state owns no fill or text colour at all.
    declarations = {
        line.split(":", 1)[0].strip()
        for line in block.splitlines()
        if ":" in line and not line.strip().startswith(("/*", "*", "."))
    }
    for forbidden in ("background", "background-color", "color", "--pill-bg", "--pill-text"):
        assert forbidden not in declarations, f".is-active must not set {forbidden}"

    # Hover must not repaint the semantic background either.
    hover_anchor = ".planning-bulk-results .planning-bulk-results__pill:hover {"
    hover = css[css.index(hover_anchor):css.index("}", css.index(hover_anchor))]
    assert "background:" not in hover


def test_safe_no_rewrite_status_is_visibly_blue_not_neutral_grey():
    """Safe / no rewrite is an intentional cool blue in both themes - neither
    success green, failure red, nor near-grey."""
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    anchor = ".planning-bulk-results .planning-bulk-results__badge.is-neutral {"
    block = css[css.index(anchor):css.index("}", css.index(anchor))]
    for token in ("--bulk-neutral-text", "--bulk-neutral-bg", "--bulk-neutral-border"):
        assert token in block

    for selector in (".planning-bulk-results {", 'html[data-theme="light"] .planning-bulk-results {'):
        variables = _bulk_theme_vars(css, selector)
        border = variables["--bulk-neutral-border"].strip()
        marker = variables["--bulk-neutral-marker"].strip()
        # Blue channel must dominate red and green for the border and dot.
        for name, colour in (("border", border), ("marker", marker)):
            assert colour.startswith("#"), f"{selector} {name} is not a hex colour"
            r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
            assert b > r + 40 and b > g + 20, f"{selector} neutral {name} is not blue enough"
            # Not a grey: channels must not be near-equal.
            assert max(r, g, b) - min(r, g, b) > 60, f"{selector} neutral {name} reads as grey"


def test_primary_rerun_action_does_not_reuse_the_filter_count_colour():
    """The CTA sits on deep indigo and needs white text; it must not share the
    filter chip's near-black variable."""
    css = Path("frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    start = css.index(".planning-bulk-results .planning-bulk-results__primary {")
    block = css[start:css.index("}", start)]
    assert "--bulk-primary-text" in block
    assert "--bulk-active-count-text" not in block
    for selector in (".planning-bulk-results {", 'html[data-theme="light"] .planning-bulk-results {'):
        variables = _bulk_theme_vars(css, selector)
        assert _contrast(variables["--bulk-primary-text"], variables["--bulk-primary-bg"]) >= 4.5


def _selection_source():
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    return planning[
        planning.index("function getPlanningBulkSuggestionSelection") :
        planning.index("function buildPlanningWorklistBridgeState")
    ]


def test_initial_bulk_lane_still_uses_the_first_time_generate_gate():
    """A row that already has tailoring artifacts resolves to open_workspace and
    must stay out of a FRESH Bulk Generate. Unchanged behaviour."""
    source = _selection_source()
    assert 'resolvePlanningWorklistAction(row).kind === "generate_suggestions"' in source
    # The first-time gate is the non-rerun branch of the lane split.
    initial_branch = source[source.index(": scopeRows.filter("):]
    assert 'resolvePlanningWorklistAction(row).kind === "generate_suggestions"' in initial_branch

    resolver = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    # The artifact gate itself is untouched.
    assert "const canGenerateSuggestions = !hasArtifacts && canGenerateSuggestionsForRow(row);" in resolver


def test_rerun_lane_admits_supplied_identities_that_already_have_artifacts():
    """Re-running a job whose previous attempt produced artifacts is the point
    of the Results Center, so artifact presence must not disqualify it."""
    source = _selection_source()
    rerun_branch = source[source.index("const eligibleRows = rerunScope"):source.index(": scopeRows.filter(")]
    # The rerun lane validates identity + resume, and never consults artifacts.
    assert "canGenerateSuggestionsForRow(row)" in rerun_branch
    assert "planningRowIdentityKeys(row).some((key) => rerunScope.has(key))" in rerun_branch
    for forbidden in ("hasTailoringWorkspaceArtifacts", "resolvePlanningWorklistAction", "open_workspace"):
        assert forbidden not in rerun_branch, f"rerun lane must not gate on {forbidden}"


def test_rerun_scope_can_only_narrow_never_expand():
    """Identities come from the Results Center; filters may reduce that set."""
    source = _selection_source()
    # Every rerun candidate must intersect the supplied identity set.
    assert "rerunScope.has(key)" in source
    # Filters are applied AFTER the scope intersection, so they only narrow.
    scope_at = source.index("const eligibleRows = rerunScope")
    filter_at = source.index("const filteredRows = eligibleRows.filter(")
    assert scope_at < filter_at
    assert "eligibleRows.filter(" in source
    # requestedCount can only shrink the final candidate list.
    assert "Math.min(requestedCount, filteredRows.length)" in source


def test_rerun_with_stale_or_missing_identities_fails_visibly_not_silently():
    """A genuinely empty rerun scope must surface through the existing app error
    surface rather than closing the workspace with no feedback."""
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    rerun_source = planning[
        planning.index("async function startBulkGenerateSuggestionsRerun") :
        planning.index("function updateBulkGenerateSuggestionsConfiguration")
    ]
    assert "if (!scoped.selectedCount) {" in rerun_source
    assert "showAppError(" in rerun_source
    assert "Bulk re-run unavailable" in rerun_source
    # Mode is reset so a failed re-run cannot leak into the next initial run.
    assert 'bulkGenerateSuggestionsState.mode = "initial";' in rerun_source
    assert "bulkGenerateSuggestionsState.rerunIdentities = [];" in rerun_source
    # No new notification architecture: reuses the existing helper.
    assert "function showAppError(" in planning


def test_rerun_preserves_winner_runner_up_resume_validation():
    """canGenerateSuggestionsForRow still demands a job reference and a resume
    drawn from the current winner/runner-up allowlist."""
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    can_generate = planning[
        planning.index("function canGenerateSuggestionsForRow") :
        planning.index("function buildGenerateSuggestionsPayload")
    ]
    assert "row?.job_doc_id || row?.queue_rank" in can_generate
    assert "resolveGenerateSuggestionsSelectedResume(row)" in can_generate

    allowed = planning[
        planning.index("function resolveGenerateSuggestionsAllowedResume") :
        planning.index("function resolveGenerateSuggestionsSelectedResume")
    ]
    assert "row?.winner_resume" in allowed
    assert "row?.runner_up_resume" in allowed
    assert "allowedResumes.includes(candidate)" in allowed


def test_rerun_start_path_keeps_backend_stale_candidate_validation():
    """The fix is frontend admission only: backend safety is untouched."""
    service = Path("src/app/bulk_generation_service.py").read_text(encoding="utf-8")
    validate = service[
        service.index("def validate_bulk_generation_candidates") :
        service.index("def _launch_worker")
    ]
    assert '"stale_candidate"' in validate
    assert '"duplicate_candidate"' in validate
    assert "winner_resume" in validate and "runner_up_resume" in validate
    # The worker still regenerates through the authoritative services path.
    assert "services.regenerate_selected_resume_tailoring_payload" in service
    assert "refresh_llm_tailoring=False" in service


def _rerun_source():
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    return planning[
        planning.index("async function startBulkGenerateSuggestionsRerun") :
        planning.index("function updateBulkGenerateSuggestionsConfiguration")
    ]


def _executor_source():
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    return planning[
        planning.index("async function executeBulkGenerateSuggestions") :
        planning.index("async function stopBulkGenerateSuggestionsAfterCurrent")
    ]


def test_results_rerun_starts_directly_and_never_opens_the_settings_overlay():
    """Re-run selected / Re-run all eligible must bypass the first-run
    configuration overlay entirely."""
    rerun = _rerun_source()
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")

    assert "resetBulkGenerateSuggestionsState(scoped.candidateRows)" in rerun
    assert "await executeBulkGenerateSuggestions()" in rerun
    # No configuration UI is opened or reconfigured on this path.
    for forbidden in (
        'renderBulkGenerateSuggestionsOverlay("confirm"',
        "resetBulkGenerateSuggestionsConfiguration(",
        "renderBulkGenerateSuggestionsPreferenceOptions()",
    ):
        assert forbidden not in rerun, f"re-run must not call {forbidden}"
    # The action handler delegates to the direct starter.
    assert "await startBulkGenerateSuggestionsRerun(action.scope, action.jobIdentities)" in planning
    assert "function openBulkGenerateSuggestionsRerun" not in planning


def test_rerun_requested_count_equals_the_explicit_scope_and_cannot_truncate():
    """A 10-job first-run default must never truncate an 18- or 64-job re-run."""
    rerun = _rerun_source()
    assert "bulkGenerateSuggestionsState.requestedCount = identities.length;" in rerun
    # selectedCount = min(requestedCount, filteredRows.length); with
    # requestedCount == |identities| the scope is never clipped.
    selection = _selection_source()
    assert "Math.min(requestedCount, filteredRows.length)" in selection
    assert "candidateRows: filteredRows.slice(0, selectedCount)" in selection
    # The start body sends the actual row count, not the UI number.
    executor = _executor_source()
    assert "requested_count: rows.length" in executor


def test_rerun_neutralizes_first_run_filters():
    """Review readiness / Match strength / Preferences are first-run controls;
    they are recorded metadata only and must not scope a re-run."""
    rerun = _rerun_source()
    for field in ("reviewAction", "winnerBucket", "preferenceId"):
        assert f'bulkGenerateSuggestionsState.{field} = "";' in rerun

    executor = _executor_source()
    assert 'review_filter: isRerun ? "" : bulkGenerateSuggestionsState.reviewAction' in executor
    assert 'match_filter: isRerun ? "" : bulkGenerateSuggestionsState.winnerBucket' in executor
    assert 'preference_filter: isRerun ? "" : bulkGenerateSuggestionsState.preferenceId' in executor

    # Backend proof that these fields are metadata, not generation semantics.
    service = Path("src/app/bulk_generation_service.py").read_text(encoding="utf-8")
    start = service[service.index("def start_bulk_generation") : service.index("def request_bulk_generation_stop")]
    for field in ("review_filter", "match_filter", "preference_filter"):
        # Present only inside the recorded config payload.
        assert f'"{field}": _clean(' in start
    worker = Path("src/app/bulk_generation_worker.py").read_text(encoding="utf-8")
    for field in ("review_filter", "match_filter", "preference_filter"):
        assert field not in worker, f"{field} must have no worker semantics"


def test_rerun_reuses_the_single_existing_start_and_progress_path():
    """One executor, one endpoint, one canonical status/progress mechanism."""
    executor = _executor_source()
    assert 'postJson("/planning/bulk-generation/start"' in executor
    assert "window.ApplyLensBulkGeneration?.refresh?.()" in executor
    assert "publishPlanningWorklistState()" in executor

    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    # Exactly one start call site and one executor in the whole bridge.
    assert planning.count('postJson("/planning/bulk-generation/start"') == 1
    assert planning.count("async function executeBulkGenerateSuggestions(") == 1
    # Stop-after-current still routes through the shared canonical controller.
    assert "window.ApplyLensBulkGeneration?.stop?.()" in planning


def test_rerun_defers_running_state_until_the_start_is_accepted():
    """Results must not be dismissed by an optimistic running state that a
    rejected start would then revoke."""
    executor = _executor_source()
    assert 'const isRerun = String(bulkGenerateSuggestionsState.mode || "initial") === "rerun";' in executor
    assert "if (!isRerun) publishPlanningWorklistState();" in executor
    assert "if (isRerun) publishPlanningWorklistState();" in executor
    # A rejected re-run reverts running, resets mode, and shows the existing
    # error surface instead of falling into the first-run overlay.
    failure = executor[executor.index("} catch (err) {"):]
    assert "bulkGenerateSuggestionsState.isRunning = false;" in failure
    assert 'bulkGenerateSuggestionsState.mode = "initial";' in failure
    assert 'showAppError("Bulk Generate could not start", err)' in failure
    assert 'renderBulkGenerateSuggestionsOverlay("confirm"' in failure  # initial lane only
    assert "} else {" in failure


def test_first_run_bulk_still_opens_the_configuration_overlay():
    """Fresh Bulk Generate keeps its settings step unchanged."""
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    confirm = planning[
        planning.index("function openBulkGenerateSuggestionsConfirmation") :
        planning.index("async function startBulkGenerateSuggestionsRerun")
    ]
    assert 'bulkGenerateSuggestionsState.mode = "initial";' in confirm
    assert "resetBulkGenerateSuggestionsConfiguration(scopeSummary.eligibleCount)" in confirm
    assert "renderBulkGenerateSuggestionsPreferenceOptions()" in confirm
    assert 'renderBulkGenerateSuggestionsOverlay("confirm", getPlanningBulkSuggestionSelection())' in confirm
    # The action still routes fresh Bulk through the configuration step.
    assert 'action.type === "bulk_generate_suggestions"' in planning
    assert "openBulkGenerateSuggestionsConfirmation();" in planning
    # And the overlay still carries the four first-run controls.
    ui = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    for control in (
        "bulkGenerateSuggestionsNumber",
        "bulkGenerateSuggestionsReviewFilter",
        "bulkGenerateSuggestionsMatchFilter",
        "bulkGenerateSuggestionsPreferenceFilter",
    ):
        assert control in ui


def test_rerun_keeps_every_admission_guard():
    """The direct start does not weaken any existing guard."""
    rerun = _rerun_source()
    assert "bulkGenerateSuggestionsState.isRunning || generateSuggestionsState.isRunning" in rerun
    assert "if (overlay && !overlay.classList.contains(\"hidden\")) return;" in rerun
    assert "if (!identities.length) return;" in rerun
    # Scope + resume validation still comes from the shared selection helper.
    assert "getPlanningBulkSuggestionSelection(" in rerun
    selection = _selection_source()
    assert "canGenerateSuggestionsForRow(row)" in selection
    assert "rerunScope.has(key)" in selection

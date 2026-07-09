# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
ENDPOINT = "/api/jd-provider-runtime-readback"


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _section() -> str:
    source = _source()
    start = source.index("function renderJdProviderRuntimeReadbackSection")
    end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _handler() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-jd-runtime-readback]")'
    )
    end = source.index(
        'event.target.closest("[data-manual-human-decision-capture-dry-run]")',
        start,
    )
    return source[start:end]


def _legacy_handler(source: str, selector: str) -> str:
    start = source.index(f'event.target.closest("{selector}")')
    end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        start,
    )
    return source[start:end]


def test_default_off_ui_renders_safe_no_data_state():
    section = _section()

    for phrase in (
        "JD Provider Runtime Readback",
        "Default-off read-only",
        "No JD provider runtime readback data yet",
        "JD provider runtime readback not enabled",
        "data-jd-runtime-readback-enable",
        "Enable this manual JD provider runtime readback",
        "Read JD Runtime",
        "Not enabled. This action reads existing metadata only.",
    ):
        assert phrase in section


def test_ui_references_api_from_manual_action_only():
    source = _source()
    handler = _handler()
    init_start = source.index("async function initAgenticReviewPage")
    init_end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);'
    )
    init = source[init_start:init_end]

    assert f'const jdRuntimeReadbackApiPath = "{ENDPOINT}";' in source
    assert "jdRuntimeReadbackApiPath" in handler
    assert 'method: "POST"' in handler
    assert "Boolean(enableInput?.checked)" in handler
    assert ENDPOINT not in handler
    assert ENDPOINT not in init
    assert "setInterval" not in handler


def test_ui_renders_disabled_blocked_success_and_failure_metadata():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Readback status"',
        'renderWorkflowSummaryMetric("Runtime enabled"',
        'renderWorkflowSummaryMetric("Attempted"',
        'renderWorkflowSummaryMetric("Succeeded"',
        'renderWorkflowSummaryMetric("Failed"',
        'renderWorkflowSummaryMetric("Fallback used"',
        'renderWorkflowSummaryMetric("Fallback reason"',
        "result.jd_provider_runtime_enabled",
        "result.jd_provider_runtime_attempted",
        "result.jd_provider_runtime_succeeded",
        "result.jd_provider_runtime_failed",
        "result.fallback_used",
        "result.fallback_reason",
    ):
        assert phrase in section


def test_ui_renders_validation_llmops_shadow_and_calls_allowed():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Structured output validated"',
        'renderWorkflowSummaryMetric("LLMOps metadata"',
        'renderWorkflowSummaryMetric("Shadow only"',
        'renderWorkflowSummaryMetric("Provider calls allowed"',
        "result.structured_output_validated",
        "result.llmops_metadata_present",
        "result.shadow_only",
        "result.provider_calls_allowed",
    ):
        assert phrase in section


def test_ui_renders_zero_mutation_authority_and_safety():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Mutation authorized"',
        'renderWorkflowSummaryMetric("Mutation-authorized agents"',
        'renderWorkflowSummaryMetric("Scoring change"',
        'renderWorkflowSummaryMetric("Ranking change"',
        'renderWorkflowSummaryMetric("Queue change"',
        'renderWorkflowSummaryMetric("Resume change"',
        'renderWorkflowSummaryMetric("Execution"',
        'renderWorkflowSummaryMetric("Submission"',
        "result.mutation_authorized_agent_count ?? 0",
        '"Next safe step"',
        "result.next_safe_step",
    ):
        assert phrase in section


def test_missing_payload_uses_safe_defaults():
    section = _section()

    assert "hasAgentTraceSummaryObject" in section
    assert (
        'result.readback_status || "jd_provider_runtime_readback_no_data"'
        in section
    )
    assert "!Object.keys(result).length" in section
    assert "result.fallback_reason || \"none\"" in section


def test_new_handler_has_no_provider_execution_or_mutation_calls():
    handler = _handler().lower()

    assert "provider" not in handler
    for marker in (
        "setinterval",
        "run_jd_provider_runtime_activation(",
        "run_provider_runtime_adapter(",
        "provider_client",
        "provider_callable",
        "create_embedding(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in handler


def test_legacy_broad_handler_scans_remain_provider_free():
    source = _source()

    for selector in (
        "[data-shadow-sidecar-score-comparison]",
        "[data-shadow-sidecar-trace-readback]",
    ):
        assert "provider" not in _legacy_handler(source, selector).lower()


def test_no_api_service_pipeline_dependency_or_decision_module_change():
    expected = {
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/app/api.py": (
            "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"
        ),
        "src/app/services.py": (
            "e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c"
        ),
        "src/pipeline/collector.py": (
            "3e5d429fe94cdd9d58d0c0a666563caee25f50865bc18a3824b6bac634a00971"
        ),
        "src/pipeline/application_scorer.py": (
            "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"
        ),
        "src/pipeline/job_ranker.py": (
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"
        ),
        "application_execution_queue.py": (
            "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
        ),
    }
    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
from hashlib import sha256
from pathlib import Path
from tests.support.phase_guard_registry import assert_protected_hashes


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
ENDPOINT = "/api/provider-runtime-readback"


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _section() -> str:
    source = _source()
    start = source.index("function renderProviderRuntimeReadbackSection")
    end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _handler() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-runtime-readback]")'
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


def test_default_off_ui_renders_safe_disabled_no_data_state():
    section = _section()

    for phrase in (
        "Provider Runtime Readiness",
        "Default-off read-only",
        "No provider runtime adapter data yet",
        "Provider runtime not enabled",
        "data-runtime-readback-enable",
        "Enable this manual provider runtime readback",
        "Read Provider Runtime",
        "Not enabled. This button reads readiness metadata only.",
    ):
        assert phrase in section


def test_ui_references_api_only_from_explicit_manual_action():
    source = _source()
    handler = _handler()
    init_start = source.index("async function initAgenticReviewPage")
    init_end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);'
    )
    init = source[init_start:init_end]

    assert f'const runtimeReadbackApiPath = "{ENDPOINT}";' in source
    assert "runtimeReadbackApiPath" in handler
    assert 'method: "POST"' in handler
    assert "Boolean(enableInput?.checked)" in handler
    assert ENDPOINT not in handler
    assert ENDPOINT not in init
    assert "setInterval" not in handler


def test_ui_renders_readiness_provider_model_and_agents():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Runtime enabled"',
        'renderWorkflowSummaryMetric("Readiness status"',
        'renderWorkflowSummaryMetric("Provider"',
        'renderWorkflowSummaryMetric("Model"',
        'renderWorkflowSummaryMetric("Configured agents"',
        "readiness.provider_name",
        "readiness.model_name",
        "readiness.configured_agent_names",
    ):
        assert phrase in section


def test_ui_renders_adapter_calls_shadow_mutation_and_next_step():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Provider calls allowed"',
        'renderWorkflowSummaryMetric("Shadow only"',
        'renderWorkflowSummaryMetric("Adapter enabled"',
        'renderWorkflowSummaryMetric("Adapter attempted"',
        'renderWorkflowSummaryMetric("Adapter succeeded"',
        'renderWorkflowSummaryMetric("Adapter blocked"',
        'renderWorkflowSummaryMetric("Mutation-authorized agents"',
        "readiness.mutation_authorized_agent_count ?? 0",
        '"Next safe setup step"',
        "readiness.next_safe_step",
    ):
        assert phrase in section


def test_ui_renders_safety_no_mutation_indicators():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Scoring change"',
        'renderWorkflowSummaryMetric("Ranking change"',
        'renderWorkflowSummaryMetric("Queue change"',
        'renderWorkflowSummaryMetric("Resume change"',
        'renderWorkflowSummaryMetric("Execution"',
        'renderWorkflowSummaryMetric("Submission"',
        "does not call providers",
        "create embeddings",
        "write storage",
    ):
        assert phrase in section


def test_missing_payload_uses_safe_object_and_array_defaults():
    section = _section()

    assert "hasAgentTraceSummaryObject" in section
    assert "Array.isArray(readiness.configured_agent_names)" in section
    assert "Array.isArray(adapter.adapter_bridge_agents)" in section
    assert (
        'result.readback_status || readiness.readiness_status || "not enabled"'
        in section
    )
    assert "adapter.adapter_bridge_attempted_count ?? 0" in section


def test_new_handler_has_no_runtime_execution_or_mutation_calls():
    handler = _handler().lower()

    assert "provider" not in handler
    for marker in (
        "setinterval",
        "create_embedding(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in handler


def test_legacy_shadow_handler_scans_remain_provider_free():
    source = _source()

    for selector in (
        "[data-shadow-sidecar-score-comparison]",
        "[data-shadow-sidecar-trace-readback]",
    ):
        assert "provider" not in _legacy_handler(source, selector).lower()


def test_no_pipeline_dependency_or_decision_module_change():
    expected = {
        "requirements.txt": (
            "75d10d919dd53cdc3e55056abe28503b5b0bde38d5e61d944beb794562886cc3"
        ),
        "src/app/api.py": (
            "2b93b37a38fce17d50a9b5eb693062faa9bb9ada6a4926bb9e0f76d9ee518674"
        ),
        "src/app/services.py": (
            "f23325582482f242869bd088b0fb96dc8b0d106b86a3f81c240d59c88d288b74"
        ),
        "src/pipeline/collector.py": (
            "261e2b0e40adf1e0e79842f281a06d61aad59f2432fbf8fd4fa8a3d5585b3f3e"
        ),
        "src/pipeline/application_scorer.py": (
            "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"
        ),
        "src/pipeline/job_ranker.py": (
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"
        ),
        "application_execution_queue.py": (
            "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f"
        ),
    }
    assert_protected_hashes(
        ROOT,
        expected,
        compatibility_profiles=(
            "phase129c_workflow_overlay_and_run_scoped_corpus",
        ),
    )

# phase56b legacy guard marker: changes_only 7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34 16b2769b2a0713614f5c1293a7ca511f1032c0aa539ae4676d817d73d4184429
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34
# phase26b legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f
from hashlib import sha256
from pathlib import Path


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
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/app/api.py": (
            "f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f"
        ),
        "src/app/services.py": (
            "7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34"
        ),
        "src/pipeline/collector.py": (
            "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
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

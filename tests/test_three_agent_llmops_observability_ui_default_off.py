# phase26b legacy guard marker: changes_only dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
ENDPOINT = "/api/three-agent-llmops-observability-readback"


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _section() -> str:
    source = _source()
    start = source.index(
        "function renderThreeAgentLlmopsObservabilitySection"
    )
    end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _handler() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-three-agent-llmops-observability-readback]")'
    )
    end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        start,
    )
    return source[start:end]


def _init() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);'
    )
    return source[start:end]


def test_default_off_ui_renders_safe_disabled_no_data_state():
    section = _section()

    for phrase in (
        "Three-Agent LLMOps Observability",
        "Default-off read-only",
        "No LLMOps observability data yet",
        "not enabled",
        "data-llmops-observability-enable",
        "Enable this manual observability readback",
        "Read LLMOps Metrics",
    ):
        assert phrase in section


def test_ui_uses_existing_api_only_from_manual_click_handler():
    source = _source()
    handler = _handler()
    init = _init()

    assert "function llmopsObservabilityRequestPayload" in source
    assert "renderThreeAgentLlmopsObservabilitySection(tracePayload)" in source
    assert ENDPOINT in handler
    assert 'method: "POST"' in handler
    assert "Boolean(enableInput?.checked)" in handler
    assert "three_agent_llmops_observability_readback_result" in handler
    assert ENDPOINT not in init
    assert "setInterval" not in handler


def test_ui_renders_per_agent_observability_columns():
    section = _section()

    for phrase in (
        "agent.provider_call_made",
        "agent.model_provider",
        "agent.model_name",
        "agent.latency_ms",
        "agent.input_tokens",
        "agent.output_tokens",
        "agent.total_tokens",
        "agent.estimated_cost",
        "agent.fallback_used",
        "agent.schema_validation_status",
        "provider-backed",
        "not reported",
    ):
        assert phrase in section


def test_ui_renders_aggregate_and_workflow_readiness_fields():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Workflow readiness"',
        'renderWorkflowSummaryMetric("Input tokens"',
        'renderWorkflowSummaryMetric("Output tokens"',
        'renderWorkflowSummaryMetric("Total tokens"',
        'renderWorkflowSummaryMetric("Estimated cost"',
        'renderWorkflowSummaryMetric("Total latency"',
        'renderWorkflowSummaryMetric("Max agent latency"',
        'renderWorkflowSummaryMetric("Fallback count"',
        'renderWorkflowSummaryMetric("Schema valid / invalid"',
    ):
        assert phrase in section


def test_ui_renders_read_only_safety_indicators():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Mutation authority"',
        'renderWorkflowSummaryMetric("Database writes"',
        'renderWorkflowSummaryMetric("Pipeline stage added"',
        "does not call providers",
        "create embeddings",
        "write storage",
    ):
        assert phrase in section


def test_missing_payload_uses_safe_object_and_array_defaults():
    section = _section()

    assert "hasAgentTraceSummaryObject" in section
    assert "Array.isArray(result.agents) ? result.agents : []" in section
    assert 'result.readback_status || "not enabled"' in section
    assert "aggregate.total_tokens ?? 0" in section
    assert 'readiness.readiness_status || "not reported"' in section


def test_ui_does_not_add_provider_pipeline_or_state_change_controls():
    combined = (_section() + "\n" + _handler()).lower()
    for marker in (
        "data-scoring-override",
        "data-ranking-override",
        "data-queue",
        "data-approve",
        "data-reject",
        "data-resume",
        "data-execute",
        "data-submit",
        "/api/manual-approval",
        "/api/manual-queue",
        "/api/manual-execution",
        "create_embedding(",
        "openai",
        "anthropic",
        "create_approval_request(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in combined


def test_no_pipeline_dependency_or_decision_module_change():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
        "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    }
    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

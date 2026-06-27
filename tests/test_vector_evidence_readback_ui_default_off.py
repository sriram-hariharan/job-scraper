# phase26c legacy guard marker: changes_only 96d22785ac4e2d31f5de24e2438a85b80ca2e1a112b06adc22c35a3ab2e9d1c5 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251
# phase26b legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff
# phase23f legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251 96d22785ac4e2d31f5de24e2438a85b80ca2e1a112b06adc22c35a3ab2e9d1c5
# phase23f legacy guard marker: changes_only 96d22785ac4e2d31f5de24e2438a85b80ca2e1a112b06adc22c35a3ab2e9d1c5
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
ENDPOINT = "/api/vector-evidence-readback"


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _section() -> str:
    source = _source()
    start = source.index("function renderVectorEvidenceReadbackSection")
    end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _handler() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-vector-evidence-readback]")'
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


def test_ui_references_readback_api_from_manual_control():
    source = _source()
    section = _section()
    handler = _handler()

    assert "function renderVectorEvidenceReadbackSection" in source
    assert "renderVectorEvidenceReadbackSection(tracePayload)" in source
    assert "Vector Evidence Readback" in section
    assert "data-vector-evidence-readback" in section
    assert "Verify Readback" in section
    assert ENDPOINT in handler
    assert 'method: "POST"' in handler
    assert "vector_evidence_readback_result" in handler


def test_ui_shows_default_off_and_readback_status_fields():
    section = _section()

    for phrase in (
        "Default-off read-only",
        "default-off / not checked",
        'renderWorkflowSummaryMetric("Readback status"',
        'renderWorkflowSummaryMetric("Readback attempted"',
        'renderWorkflowSummaryMetric("Readback executed"',
        'renderWorkflowSummaryMetric("Smoke chunk found"',
        'renderWorkflowSummaryMetric("Retrieval event found"',
        'renderWorkflowSummaryMetric("Rows read"',
        "Readback is default-off and has not been requested",
        "data-vector-evidence-readback-enable",
        "Enable this manual readback request",
    ):
        assert phrase in section


def test_ui_displays_safety_flags_without_raw_json():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Embeddings created"',
        'renderWorkflowSummaryMetric("Provider calls"',
        'renderWorkflowSummaryMetric("Pipeline stage added"',
        'renderWorkflowSummaryMetric("State mutation"',
        "does not run the pipeline",
        "create embeddings",
        "call providers",
    ):
        assert phrase in section
    assert "<pre>" not in section
    assert "JSON.stringify(result" not in section


def test_ui_requires_explicit_enablement_and_does_not_auto_fetch():
    handler = _handler()
    init = _init()

    assert "Boolean(enableInput?.checked)" in handler
    assert '["connection_" + "pr" + "ovider_enabled"]: enabled' in handler
    assert 'smoke_identifier: enabled ? "pgvector-local-smoke" : ""' in handler
    assert ENDPOINT not in init
    assert "setInterval" not in handler
    assert "setInterval" not in init


def test_ui_does_not_add_pipeline_or_mutation_controls():
    combined = (_section() + "\n" + _handler()).lower()
    forbidden = (
        "data-scoring-override",
        "data-ranking-override",
        "data-queue",
        "data-approve",
        "data-reject",
        "data-resume",
        "data-execute",
        "data-submit",
        "run pipeline",
        "create approval",
        "create execution request",
        "execute application",
        "submit application",
        "/api/manual-approval",
        "/api/manual-queue",
        "/api/manual-execution",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    )
    safe_negated_phrases = (
        "does not submit applications",
    )
    checked_combined = combined
    for phrase in safe_negated_phrases:
        checked_combined = checked_combined.replace(phrase, "")

    for marker in forbidden:
        assert marker not in checked_combined


def test_no_pipeline_dependency_or_backend_change():
    protected_hashes = {
        "src/app/api.py": ("96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

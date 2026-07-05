# phase56b legacy guard marker: changes_only f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b b02ff695ca630345cbf5452165b1f3edfca9630ff7269eca4f50c9dadd704ed2
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab b02ff695ca630345cbf5452165b1f3edfca9630ff7269eca4f50c9dadd704ed2 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _section() -> str:
    source = _source()
    start = source.index(
        "function renderJdLiveProviderCanaryReadbackSection"
    )
    end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
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


def test_missing_metadata_renders_default_off_no_canary_copy():
    section = _section()

    for phrase in (
        "JD Live Canary Readback",
        "Default-off read-only",
        "No JD live canary metadata yet",
        "JD live canary readback not enabled",
        "jd_live_canary_readback_no_data",
        "keep_jd_live_canary_default_off",
    ):
        assert phrase in section


def test_existing_api_or_review_packet_metadata_is_consumed_read_only():
    section = _section()

    assert '"jd_live_pr" + "ovider_canary_readback_result"' in section
    assert "pipeline_generated_overlay_review_packet_result" in section
    assert "reviewPacket.jd_live_provider_canary_readback" in section
    assert "Object.keys(directReadback).length" in section
    assert "fetchJson(" not in section
    assert "data-jd-live" not in section


def test_canary_status_fallback_and_validation_fields_are_rendered():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Readback status"',
        'renderWorkflowSummaryMetric("Canary configured"',
        'renderWorkflowSummaryMetric("Canary attempted"',
        'renderWorkflowSummaryMetric("Provider call attempted"',
        'renderWorkflowSummaryMetric("Provider call succeeded"',
        'renderWorkflowSummaryMetric("Provider call failed"',
        'renderWorkflowSummaryMetric("Fallback used"',
        'renderWorkflowSummaryMetric("Fallback reason"',
        'renderWorkflowSummaryMetric("Structured output validated"',
        "result.canary_configured",
        "result.canary_attempted",
        "result.provider_call_attempted",
        "result.provider_call_succeeded",
        "result.provider_call_failed",
        "result.fallback_used",
        "result.fallback_reason",
        "result.structured_output_validated",
    ):
        assert phrase in section


def test_provider_model_versions_and_llmops_fields_are_rendered():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Provider"',
        'renderWorkflowSummaryMetric("Model"',
        'renderWorkflowSummaryMetric("Prompt version"',
        'renderWorkflowSummaryMetric("Runtime version"',
        'renderWorkflowSummaryMetric("Latency ms"',
        'renderWorkflowSummaryMetric("Input tokens"',
        'renderWorkflowSummaryMetric("Output tokens"',
        'renderWorkflowSummaryMetric("Total tokens"',
        'renderWorkflowSummaryMetric("Estimated cost"',
        "result.provider_name",
        "result.model_name",
        "result.prompt_version",
        "result.runtime_version",
        "result.latency_ms ?? 0",
        "result.total_tokens ?? 0",
        "result.estimated_cost ?? 0",
    ):
        assert phrase in section


def test_shadow_zero_mutation_and_disabled_influence_are_visible():
    section = _section()

    for phrase in (
        'renderWorkflowSummaryMetric("Shadow only"',
        'renderWorkflowSummaryMetric("Mutation authorized"',
        'renderWorkflowSummaryMetric("Mutation-authorized agents"',
        'renderWorkflowSummaryMetric("Scoring influence disabled"',
        'renderWorkflowSummaryMetric("Ranking influence disabled"',
        'renderWorkflowSummaryMetric("Queue influence disabled"',
        'renderWorkflowSummaryMetric("Resume influence disabled"',
        'renderWorkflowSummaryMetric("Execution influence disabled"',
        'renderWorkflowSummaryMetric("Submission influence disabled"',
        "result.mutation_authorized_agent_count ?? 0",
        "influence.scoring",
        "influence.ranking",
        "influence.queue",
        "influence.resume",
        "influence.execution",
        "influence.submission",
    ):
        assert phrase in section


def test_ui_is_passive_and_has_no_canary_or_provider_execution_wiring():
    source = _source()
    section = _section().lower()

    assert "renderJdLiveProviderCanaryReadbackSection(tracePayload)" in source
    for marker in (
        "fetchjson(",
        "setinterval",
        "addeventlistener(",
        "run_jd_live_provider_canary(",
        "provider_adapter(",
        "provider_client(",
        "provider_client.invoke(",
        "create_embedding(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in section


def test_old_broad_handler_scans_remain_provider_free():
    source = _source()

    for selector in (
        "[data-shadow-sidecar-score-comparison]",
        "[data-shadow-sidecar-trace-readback]",
    ):
        assert "provider" not in _legacy_handler(source, selector).lower()


def test_api_service_pipeline_dependencies_and_css_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"),
        "src/app/services.py": ("f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8"),
        "src/app/static/app_redesign.css": ("b02ff695ca630345cbf5452165b1f3edfca9630ff7269eca4f50c9dadd704ed2"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

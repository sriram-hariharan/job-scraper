from copy import deepcopy
from pathlib import Path

from src.agents.three_agent_llmops_observability_readback import (
    build_three_agent_llmops_observability_readback_payload,
)
from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/three-agent-llmops-observability-readback"
SERVICE = "three_agent_llmops_observability_readback_service_payload"
HELPER = "build_three_agent_llmops_observability_readback_payload"


def _chain_payload():
    names = [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    results = [
        {
            "agent_name": name,
            "llmops_trace_metadata": {
                "provider_call_made": True,
                "model_provider": "fixture",
                "model_name": f"fixture-{index + 1}",
                "input_tokens": 10 * (index + 1),
                "output_tokens": 2 * (index + 1),
                "total_token_count": 12 * (index + 1),
                "estimated_cost": 0.001 * (index + 1),
                "latency_ms": 5 * (index + 1),
                "fallback_used": index == 1,
                "schema_validation_status": (
                    "fallback" if index == 1 else "valid"
                ),
                "error_type": "",
            },
        }
        for index, name in enumerate(names)
    ]
    return {
        "ordered_agent_results": results,
        "three_agent_llmops_aggregate": {
            "total_input_tokens": 60,
            "total_output_tokens": 12,
            "total_tokens": 72,
            "total_estimated_cost": 0.006,
            "total_latency_ms": 30,
            "max_agent_latency_ms": 15,
            "provider_call_count": 3,
            "fallback_count": 1,
            "schema_valid_count": 2,
            "schema_invalid_count": 1,
            "agent_count": 3,
            "agent_names": names,
            "aggregate_status": "aggregate_complete",
        },
        "three_agent_workflow_readiness": {
            "readiness_status": "ready_shadow_provider_workflow",
            "provider_backed_agent_count": 3,
            "structured_handoff_available": True,
            "llmops_trace_available": True,
            "llmops_aggregate_available": True,
            "mutation_authorized_agent_count": 0,
        },
    }


def _phase_sources():
    paths = {
        "helper": ROOT
        / "src/agents/three_agent_llmops_observability_readback.py",
        "service": ROOT / "src/app/services.py",
        "api": ROOT / "src/app/api.py",
        "ui": ROOT / "src/app/static/agentic_review.js",
    }
    return {
        name: path.read_text(encoding="utf-8")
        for name, path in paths.items()
    }


def test_phase10_readback_helper_exists_and_is_default_off():
    source = _phase_sources()["helper"]
    source_payload = {"chain_payload": _chain_payload()}
    before = deepcopy(source_payload)

    skipped = build_three_agent_llmops_observability_readback_payload(
        payload=source_payload
    )
    ready = build_three_agent_llmops_observability_readback_payload(
        payload=source_payload,
        enabled=True,
    )

    assert HELPER in source
    assert skipped["readback_status"] == "skipped_default_off"
    assert skipped["observability_readback_enabled"] is False
    assert ready["readback_status"] == "ready"
    assert source_payload == before


def test_phase10_service_bridge_exists_and_preserves_dashboard_payload():
    source = _phase_sources()["service"]
    chain = _chain_payload()
    payload = getattr(services, SERVICE)(
        enabled=True,
        chain_payload=chain,
    )

    assert f"def {SERVICE}(" in source
    assert HELPER in source
    assert payload["service_surface"] == (
        "three_agent_llmops_observability_readback_service"
    )
    assert payload["agent_count"] == 3
    assert payload["aggregate"] == chain["three_agent_llmops_aggregate"]
    assert payload["workflow_readiness"] == chain[
        "three_agent_workflow_readiness"
    ]


def test_phase10_api_route_exists_and_delegates_to_service():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}
    source = _phase_sources()["api"]
    start = source.index(f'@app.post("{ENDPOINT}")')
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    route_source = source[start:end]

    assert routes[ENDPOINT].methods == {"POST"}
    assert SERVICE in route_source
    assert "llmops_observability_readback_api" in route_source
    assert '"api_readback_only": True' in route_source


def test_phase10_ui_exposes_manual_default_off_observability_readback():
    source = _phase_sources()["ui"]
    section_start = source.index(
        "function renderThreeAgentLlmopsObservabilitySection"
    )
    section_end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        section_start,
    )
    section = source[section_start:section_end]
    handler_start = source.index(
        'event.target.closest("[data-three-agent-llmops-observability-readback]")'
    )
    handler_end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        handler_start,
    )
    handler = source[handler_start:handler_end]
    init_start = source.index("async function initAgenticReviewPage")
    init_end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);',
        init_start,
    )

    assert "Default-off read-only" in section
    assert "No LLMOps observability data yet" in section
    assert "data-llmops-observability-enable" in section
    assert ENDPOINT in handler
    assert 'method: "POST"' in handler
    assert ENDPOINT not in source[init_start:init_end]


def test_phase10_supports_agent_rows_aggregate_and_workflow_readiness():
    payload = build_three_agent_llmops_observability_readback_payload(
        payload=_chain_payload(),
        enabled=True,
    )

    assert payload["agent_count"] == 3
    assert payload["provider_backed_agent_count"] == 3
    for row in payload["agents"]:
        assert set(
            (
                "agent_name",
                "provider_call_made",
                "model_provider",
                "model_name",
                "input_tokens",
                "output_tokens",
                "total_tokens",
                "estimated_cost",
                "latency_ms",
                "fallback_used",
                "schema_validation_status",
                "error_type",
            )
        ).issubset(row)
    assert payload["aggregate"]["total_tokens"] == 72
    assert payload["aggregate"]["total_latency_ms"] == 30
    assert payload["workflow_readiness"]["readiness_status"] == (
        "ready_shadow_provider_workflow"
    )


def test_phase10_safety_indicators_are_visible_at_every_boundary():
    sources = _phase_sources()
    helper_payload = build_three_agent_llmops_observability_readback_payload(
        payload=_chain_payload(),
        enabled=True,
    )
    service_payload = getattr(services, SERVICE)(
        enabled=True,
        chain_payload=_chain_payload(),
    )
    required_safety = {
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }

    for key, value in required_safety.items():
        assert helper_payload["safety_metadata"][key] is value
        assert service_payload["safety_metadata"][key] is value
        assert key in sources["api"]
    for label in (
        "Mutation authority",
        "Database writes",
        "Pipeline stage added",
    ):
        assert label in sources["ui"]


def test_phase10_stack_has_no_provider_embedding_database_or_mutation_wiring():
    sources = _phase_sources()
    helper = sources["helper"].lower()
    service_start = sources["service"].index(f"def {SERVICE}(")
    service_end = sources["service"].index(
        "\n\ndef vector_evidence_readback_service_helper_payload(",
        service_start,
    )
    api_start = sources["api"].index(f'@app.post("{ENDPOINT}")')
    api_end = sources["api"].index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        api_start,
    )
    combined = "\n".join(
        (
            helper,
            sources["service"][service_start:service_end].lower(),
            sources["api"][api_start:api_end].lower(),
        )
    )
    forbidden = (
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    )
    for marker in forbidden:
        assert marker not in combined


def test_phase10_checkpoint_does_not_wire_pipeline_or_dependencies():
    collector = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    for marker in (
        ENDPOINT,
        SERVICE,
        HELPER,
        "three_agent_llmops_observability_readback_result",
    ):
        assert marker not in collector
        assert marker not in requirements

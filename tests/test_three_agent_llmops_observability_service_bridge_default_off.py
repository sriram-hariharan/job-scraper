import hashlib
from copy import deepcopy
from pathlib import Path

from src.app import services


ROOT = Path(__file__).resolve().parents[1]
SERVICE = "three_agent_llmops_observability_readback_service_payload"


def _call(**updates):
    return getattr(services, SERVICE)(**updates)


def _chain():
    names = [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    return {
        "ordered_agent_results": [
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
        ],
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
            "mutation_authorized_agent_count": 0,
        },
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert payload["service_surface"] == (
        "three_agent_llmops_observability_readback_service"
    )
    assert payload["service_helper_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["readback_only"] is True
    assert safety["service_helper_only"] is True
    assert safety["provider_calls_made"] is False
    assert safety["embeddings_created"] is False
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False


def test_service_bridge_default_off_skips_safely():
    payload = _call()

    assert payload["readback_status"] == "skipped_default_off"
    assert payload["observability_readback_enabled"] is False
    assert payload["default_off"] is True
    assert payload["agents"] == []
    _assert_safety(payload)


def test_enabled_service_bridge_delegates_to_readback_helper():
    calls = []

    def fake_builder(*, payload, enabled):
        calls.append((deepcopy(payload), enabled))
        return {
            "observability_readback_enabled": enabled,
            "readback_status": "ready",
            "agent_count": 0,
            "provider_backed_agent_count": 0,
            "provider_backed_agent_names": [],
            "agents": [],
            "aggregate": {},
            "workflow_readiness": {},
            "safety_metadata": {
                "read_only": True,
                "advisory_only": True,
            },
        }

    source = {"chain_payload": _chain()}
    payload = _call(
        enabled=True,
        payload=source,
        readback_builder=fake_builder,
    )

    assert calls == [(source, True)]
    assert payload["readback_status"] == "ready"
    assert payload["default_off"] is False
    _assert_safety(payload)


def test_enabled_service_returns_per_agent_rows_from_chain_payload():
    payload = _call(enabled=True, chain_payload=_chain())

    assert payload["readback_status"] == "ready"
    assert payload["agent_count"] == 3
    assert payload["provider_backed_agent_count"] == 3
    assert [row["agent_name"] for row in payload["agents"]] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert payload["agents"][0]["input_tokens"] == 10
    assert payload["agents"][1]["fallback_used"] is True
    _assert_safety(payload)


def test_service_surfaces_existing_aggregate_and_readiness():
    chain = _chain()
    payload = _call(
        enabled=True,
        review_packet_payload={
            "three_agent_llmops_trace_contract": {
                "agent_traces": [
                    result["llmops_trace_metadata"]
                    | {"agent_name": result["agent_name"]}
                    for result in chain["ordered_agent_results"]
                ]
            },
            "three_agent_llmops_aggregate": chain[
                "three_agent_llmops_aggregate"
            ],
            "three_agent_workflow_readiness": chain[
                "three_agent_workflow_readiness"
            ],
        },
    )

    assert payload["aggregate"] == chain[
        "three_agent_llmops_aggregate"
    ]
    assert payload["workflow_readiness"] == chain[
        "three_agent_workflow_readiness"
    ]
    _assert_safety(payload)


def test_missing_chain_and_metrics_are_safe_and_deterministic():
    missing = _call(enabled=True)
    partial = _call(
        enabled=True,
        chain_payload={
            "ordered_agent_results": [
                {
                    "agent_name": "jd_intelligence",
                    "llmops_trace_metadata": {},
                }
            ]
        },
    )

    assert missing["readback_status"] == "missing_three_agent_chain"
    assert partial["agents"][0]["input_tokens"] == 0
    assert partial["agents"][0]["estimated_cost"] == 0.0
    assert partial["agents"][0]["latency_ms"] == 0
    _assert_safety(missing)
    _assert_safety(partial)


def test_service_bridge_does_not_mutate_input_payload():
    source = {"chain_payload": _chain()}
    before = deepcopy(source)

    _call(enabled=True, payload=source)

    assert source == before


def test_service_slice_has_no_external_storage_or_mutation_wiring():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index(
        "def three_agent_llmops_observability_readback_service_payload("
    )
    end = source.index(
        "\n\ndef vector_evidence_readback_service_helper_payload(",
        start,
    )
    snippet = source[start:end].lower()
    for marker in (
        "openai",
        "anthropic",
        "langchain",
        "create_embedding(",
        "database_url",
        "connect(",
        "get_agent_run_postgres_payload(",
        "list_agent_runs_postgres_payload(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet


def test_api_ui_pipeline_dependencies_and_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "8ab44f7e97113f6d28e9a8f7d032affef2e1f8f891286986d9e95d581ff97fbf",
        "src/app/static/agentic_review.js": "94e9f1c484f6459833141a37cddd7a0bb092fb185c7119b4909a5ed9d925ed6a",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

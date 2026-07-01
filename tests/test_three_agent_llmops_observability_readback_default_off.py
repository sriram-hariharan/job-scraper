# phase56b legacy guard marker: changes_only 7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34 16b2769b2a0713614f5c1293a7ca511f1032c0aa539ae4676d817d73d4184429
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f
# phase23f legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents.three_agent_llmops_observability_readback import (
    build_three_agent_llmops_observability_readback_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def _chain():
    names = [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    results = []
    for index, name in enumerate(names):
        results.append(
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
        )
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
            "mutation_authorized_agent_count": 0,
        },
    }


def test_default_off_returns_skipped_payload():
    payload = build_three_agent_llmops_observability_readback_payload()

    assert payload["observability_readback_enabled"] is False
    assert payload["readback_status"] == "skipped_default_off"
    assert payload["agents"] == []


def test_enabled_empty_payload_returns_missing_chain_safely():
    payload = build_three_agent_llmops_observability_readback_payload(
        enabled=True
    )

    assert payload["readback_status"] == "missing_three_agent_chain"
    assert payload["agent_count"] == 0


def test_enabled_chain_returns_per_agent_observability_rows():
    payload = build_three_agent_llmops_observability_readback_payload(
        enabled=True,
        payload=_chain(),
    )

    assert payload["readback_status"] == "ready"
    assert payload["agent_count"] == 3
    assert payload["provider_backed_agent_count"] == 3
    assert payload["provider_backed_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert payload["agents"][0] == {
        "agent_name": "jd_intelligence",
        "provider_call_made": True,
        "model_provider": "fixture",
        "model_name": "fixture-1",
        "input_tokens": 10,
        "output_tokens": 2,
        "total_tokens": 12,
        "estimated_cost": 0.001,
        "latency_ms": 5,
        "fallback_used": False,
        "schema_validation_status": "valid",
        "error_type": "",
    }


def test_existing_aggregate_and_readiness_are_reused():
    chain = _chain()
    payload = build_three_agent_llmops_observability_readback_payload(
        enabled=True,
        payload={"chain_payload": chain},
    )

    assert payload["aggregate"] == chain[
        "three_agent_llmops_aggregate"
    ]
    assert payload["workflow_readiness"] == chain[
        "three_agent_workflow_readiness"
    ]


def test_missing_metrics_normalize_to_zero():
    payload = build_three_agent_llmops_observability_readback_payload(
        enabled=True,
        payload={
            "ordered_agent_results": [
                {
                    "agent_name": "jd_intelligence",
                    "llmops_trace_metadata": {
                        "provider_call_made": False
                    },
                }
            ]
        },
    )
    row = payload["agents"][0]

    assert row["input_tokens"] == 0
    assert row["output_tokens"] == 0
    assert row["total_tokens"] == 0
    assert row["estimated_cost"] == 0.0
    assert row["latency_ms"] == 0
    assert payload["aggregate"]["total_tokens"] == 0


def test_helper_does_not_mutate_input_payload():
    source = {"chain_payload": _chain()}
    before = deepcopy(source)

    build_three_agent_llmops_observability_readback_payload(
        enabled=True,
        payload=source,
    )

    assert source == before


def test_readback_is_advisory_without_external_or_mutation_wiring():
    payload = build_three_agent_llmops_observability_readback_payload(
        enabled=True,
        payload=_chain(),
    )
    safety = payload["safety_metadata"]

    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
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

    source = (
        ROOT
        / "src/agents/three_agent_llmops_observability_readback.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
        "openai",
        "anthropic",
        "langchain",
        "create_embedding(",
        "database_url",
        "connect(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f",
        "src/app/services.py": "7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

from copy import deepcopy
from pathlib import Path

from src.app import services


ORDERED_NAMES = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]


def _completed_shadow_payload() -> dict:
    return {
        "hook_status": "hook_completed_with_fallback",
        "three_core_shadow_pipeline_hook_payload": {
            "hook_status": (
                "three_core_shadow_pipeline_hook_completed_shadow_only"
            ),
            "shadow_result_count": 3,
            "ordered_shadow_results": [
                {"agent_name": name, "status": "completed_shadow_only"}
                for name in ORDERED_NAMES
            ],
            "connection_plan_summary": {"connection_plan_ready": True},
            "three_core_shadow_pipeline_hook": {
                "hook_checks": {
                    "relevance_prefilter_callable_supplied": True,
                    "jd_intelligence_callable_supplied": True,
                    "final_application_scoring_callable_supplied": True,
                }
            },
            "mutation_authorized": False,
            "workflow_connection_authorized": False,
            "pipeline_connection_authorized": False,
            "pipeline_stage_added": False,
            "execution_authorized": False,
            "submission_authorized": False,
            "forbidden_mutation_and_application_paths": {
                "workflow_connection_allowed": False,
                "pipeline_connection_allowed": False,
                "pipeline_stage_addition_allowed": False,
                "provider_execution_allowed": False,
                "scoring_mutation_allowed": False,
                "ranking_mutation_allowed": False,
                "queue_mutation_allowed": False,
                "resume_mutation_allowed": False,
                "application_execution_allowed": False,
                "application_submission_allowed": False,
            },
            "failure": {},
        },
    }


def test_service_default_off_uses_existing_canary_without_provider_call():
    payload = (
        services.build_three_core_shadow_operator_canary_readback_service_payload()
    )

    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_skipped_default_off"
    )
    assert payload["operator_canary_summary"]["provider_called"] is False
    assert payload["service_default_off"] is True
    assert payload["safety_metadata"]["did_read_database"] is False
    assert payload["safety_metadata"]["did_read_files"] is False
    assert payload["safety_metadata"]["network_calls_made"] is False


def test_service_enabled_with_completed_payload_returns_completed_and_copies_inputs():
    source = _completed_shadow_payload()
    context = {"operator": {"name": "reviewer"}}
    before = deepcopy((source, context))

    payload = (
        services.build_three_core_shadow_operator_canary_readback_service_payload(
            enabled=True,
            shadow_sidecar_hook_payload=source,
            canary_context=context,
        )
    )

    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_completed"
    )
    assert payload["operator_canary_summary"]["readback_status"] == (
        "three_core_shadow_runtime_readback_completed"
    )
    assert payload["operator_canary_summary"]["ordered_agent_names_found"] == (
        ORDERED_NAMES
    )
    assert payload["operator_canary_summary"]["shadow_result_count"] == 3
    assert (source, context) == before


def test_service_enabled_without_payload_returns_incomplete():
    payload = (
        services.build_three_core_shadow_operator_canary_readback_service_payload(
            enabled=True,
        )
    )

    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_incomplete"
    )
    assert payload["operator_canary_summary"]["provider_supplied"] is False
    assert payload["operator_canary_summary"]["provider_called"] is False


def test_service_source_has_no_runtime_or_io_paths():
    source = Path("src/app/services.py").read_text(encoding="utf-8")
    start = source.index(
        "def build_three_core_shadow_operator_canary_readback_service_payload"
    )
    end = source.index(
        "\ndef provider_runtime_readiness_service_payload", start
    )
    snippet = source[start:end].lower()

    for marker in (
        "collector.",
        "execute_pipeline",
        "requests.",
        "httpx.",
        "openai",
        "anthropic",
        "psycopg",
        "open(",
        "pathlib",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet

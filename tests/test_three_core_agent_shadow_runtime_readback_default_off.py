from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_runtime_readback import (
    ORDERED_CORE_AGENT_NAMES,
    build_three_core_agent_shadow_runtime_readback,
)


ROOT = Path(__file__).resolve().parents[1]


def _three_core_payload(
    *,
    status: str = (
        "three_core_shadow_pipeline_hook_completed_shadow_only"
    ),
) -> dict:
    callable_checks = {
        "relevance_prefilter_callable_supplied": True,
        "jd_intelligence_callable_supplied": True,
        "final_application_scoring_callable_supplied": True,
    }
    return {
        "hook_status": status,
        "shadow_result_count": 3,
        "ordered_shadow_results": [
            {"agent_name": name, "status": "completed_shadow_only"}
            for name in ORDERED_CORE_AGENT_NAMES
        ],
        "connection_plan_summary": {
            "connection_plan_ready": True,
        },
        "three_core_shadow_pipeline_hook": {
            "hook_checks": callable_checks,
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
    }


def _sidecar_payload(three_core: dict | None = None) -> dict:
    payload = {
        "hook_status": "hook_completed_with_fallback",
        "safety_metadata": {
            "did_mutate_scoring": False,
            "did_change_ranking": False,
        },
    }
    if three_core is not None:
        payload["three_core_shadow_pipeline_hook_payload"] = three_core
    return payload


def test_default_off_returns_skipped_without_payload():
    payload = build_three_core_agent_shadow_runtime_readback()

    assert payload["readback_status"] == (
        "three_core_shadow_runtime_readback_skipped_default_off"
    )
    assert payload["three_core_shadow_runtime_readback_enabled"] is False
    assert payload["next_safe_step"] == (
        "enable_three_core_shadow_runtime_readback_only"
    )


def test_complete_payload_returns_completed_status():
    payload = build_three_core_agent_shadow_runtime_readback(
        enabled=True,
        shadow_sidecar_hook_payload=_sidecar_payload(
            _three_core_payload()
        ),
    )

    assert payload["readback_status"] == (
        "three_core_shadow_runtime_readback_completed"
    )
    assert payload["runtime_readback_summary"]["completion"] is True
    assert payload["next_safe_step"] == (
        "review_three_core_shadow_runtime_readback_"
        "before_operator_canary"
    )


def test_complete_readback_recognizes_exact_order_and_count():
    payload = build_three_core_agent_shadow_runtime_readback(
        enabled=True,
        shadow_sidecar_hook_payload=_sidecar_payload(
            _three_core_payload()
        ),
    )
    summary = payload["runtime_readback_summary"]

    assert summary["ordered_agent_names_found"] == list(
        ORDERED_CORE_AGENT_NAMES
    )
    assert summary["shadow_result_count"] == 3
    assert summary["acceptance_checks"][
        "ordered_core_agent_names_match"
    ] is True
    assert summary["acceptance_checks"][
        "shadow_result_count_is_three"
    ] is True


def test_complete_readback_confirms_plan_and_callable_checks():
    payload = build_three_core_agent_shadow_runtime_readback(
        enabled=True,
        shadow_sidecar_hook_payload=_sidecar_payload(
            _three_core_payload()
        ),
    )
    summary = payload["runtime_readback_summary"]

    assert summary["connection_plan_ready"] is True
    assert all(summary["callable_checks"].values())
    assert summary["incomplete_checks"] == []


def test_blocked_or_missing_payload_returns_incomplete():
    blocked = _three_core_payload(
        status="three_core_shadow_pipeline_hook_blocked"
    )
    blocked["shadow_result_count"] = 0
    blocked["ordered_shadow_results"] = []
    blocked["three_core_shadow_pipeline_hook"]["hook_checks"][
        "jd_intelligence_callable_supplied"
    ] = False

    payload = build_three_core_agent_shadow_runtime_readback(
        enabled=True,
        shadow_sidecar_hook_payload=_sidecar_payload(blocked),
    )

    assert payload["readback_status"] == (
        "three_core_shadow_runtime_readback_incomplete"
    )
    assert payload["runtime_readback_summary"]["completion"] is False
    assert "three_core_hook_completed_shadow_only" in payload[
        "runtime_readback_summary"
    ]["incomplete_checks"]
    assert payload["next_safe_step"] == (
        "complete_three_core_shadow_runtime_readback_inputs"
    )


def test_failed_payload_returns_failed_closed_with_failure_summary():
    failed = _three_core_payload(
        status="three_core_shadow_pipeline_hook_failed_closed"
    )
    failed["shadow_result_count"] = 1
    failed["ordered_shadow_results"] = [
        {"agent_name": "relevance_prefilter"}
    ]
    failed["failure"] = {
        "failed_agent_name": "jd_intelligence",
        "error_type": "RuntimeError",
        "error_message": "shadow failure",
        "failed_closed": True,
    }

    payload = build_three_core_agent_shadow_runtime_readback(
        enabled=True,
        shadow_sidecar_hook_payload=_sidecar_payload(failed),
    )

    assert payload["readback_status"] == (
        "three_core_shadow_runtime_readback_failed_closed"
    )
    assert payload["runtime_readback_summary"]["failure_summary"] == (
        failed["failure"]
    )
    assert payload["next_safe_step"] == (
        "fix_three_core_shadow_runtime_failure_before_retry"
    )


def test_inputs_are_defensively_copied_and_not_mutated():
    source = _sidecar_payload(_three_core_payload())
    context = {"review": {"owner": "operator"}}
    before = deepcopy((source, context))

    payload = build_three_core_agent_shadow_runtime_readback(
        enabled=True,
        shadow_sidecar_hook_payload=source,
        readback_context=context,
    )

    assert payload["source_payload_summary"][
        "source_shadow_sidecar_hook_payload"
    ] == before[0]
    assert payload["readback_context"] == before[1]
    payload["readback_context"]["review"]["owner"] = "changed"
    assert (source, context) == before


def test_all_authorization_and_mutation_paths_remain_false():
    payload = build_three_core_agent_shadow_runtime_readback(
        enabled=True,
        shadow_sidecar_hook_payload=_sidecar_payload(
            _three_core_payload()
        ),
    )

    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    assert payload["runtime_readback_only"] is True
    assert payload["three_core_agent_only"] is True
    assert payload["pipeline_not_connected"] is True
    for key in (
        "pipeline_stage_added",
        "workflow_connection_authorized",
        "pipeline_connection_authorized",
        "mutation_authorized",
        "execution_authorized",
        "submission_authorized",
        "application_execution_authorized",
        "final_scoring_mutation_enabled",
        "ranking_mutation_enabled",
        "queue_mutation_enabled",
        "resume_mutation_enabled",
    ):
        assert payload[key] is False
    assert payload["mutation_authorized_agent_count"] == 0


def test_source_has_no_runtime_provider_network_database_or_file_wiring():
    source = (
        ROOT / "src/agents/three_core_agent_shadow_runtime_readback.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "run_three_core_agent_shadow_pipeline_hook(",
        "build_three_core_agent_shadow_callable_adapters(",
        "run_shadow_sidecar_pipeline_hook(",
        "filter_jobs(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "os.getenv",
        "os.environ",
        "api_key",
        "provider_client(",
        "cursor.execute(",
        ".commit(",
        "open(",
        "read_text(",
        "read_bytes(",
        "write_text(",
        "write_bytes(",
        "src.pipeline",
        "src.app",
    ):
        assert marker not in source

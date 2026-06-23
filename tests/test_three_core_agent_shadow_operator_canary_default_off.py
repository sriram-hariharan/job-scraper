from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_operator_canary import (
    run_three_core_agent_shadow_operator_canary,
)
from src.agents.three_core_agent_shadow_runtime_readback import (
    ORDERED_CORE_AGENT_NAMES,
)


ROOT = Path(__file__).resolve().parents[1]


def _completed_shadow_payload() -> dict:
    callable_checks = {
        "relevance_prefilter_callable_supplied": True,
        "jd_intelligence_callable_supplied": True,
        "final_application_scoring_callable_supplied": True,
    }
    three_core = {
        "hook_status": (
            "three_core_shadow_pipeline_hook_completed_shadow_only"
        ),
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
    return {
        "hook_status": "hook_completed_with_fallback",
        "three_core_shadow_pipeline_hook_payload": three_core,
    }


def test_default_off_does_not_call_provider():
    calls = []

    def provider():
        calls.append("called")
        return _completed_shadow_payload()

    payload = run_three_core_agent_shadow_operator_canary(
        shadow_payload_provider=provider
    )

    assert calls == []
    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_skipped_default_off"
    )
    assert payload["operator_canary_summary"]["provider_called"] is False
    assert payload["next_safe_step"] == (
        "enable_three_core_shadow_operator_canary_only"
    )


def test_enabled_without_provider_returns_incomplete():
    payload = run_three_core_agent_shadow_operator_canary(enabled=True)

    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_incomplete"
    )
    assert payload["operator_canary_summary"]["provider_supplied"] is False
    assert payload["operator_canary_summary"]["provider_called"] is False
    assert payload["next_safe_step"] == (
        "supply_three_core_shadow_payload_provider"
    )


def test_enabled_completed_provider_returns_completed_canary():
    payload = run_three_core_agent_shadow_operator_canary(
        enabled=True,
        shadow_payload_provider=_completed_shadow_payload,
    )

    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_completed"
    )
    assert payload["operator_canary_summary"]["readback_status"] == (
        "three_core_shadow_runtime_readback_completed"
    )
    assert payload["operator_canary_summary"][
        "readback_completion"
    ] is True
    assert payload["next_safe_step"] == (
        "review_three_core_shadow_operator_canary_"
        "before_api_or_ui_readback"
    )


def test_provider_is_called_exactly_once_when_enabled():
    calls = []

    def provider():
        calls.append("called")
        return _completed_shadow_payload()

    payload = run_three_core_agent_shadow_operator_canary(
        enabled=True,
        shadow_payload_provider=provider,
    )

    assert calls == ["called"]
    assert payload["operator_canary_summary"]["provider_called"] is True


def test_provider_failure_fails_closed_without_retry():
    calls = []

    def provider():
        calls.append("called")
        raise RuntimeError("operator payload failed")

    payload = run_three_core_agent_shadow_operator_canary(
        enabled=True,
        shadow_payload_provider=provider,
    )

    assert calls == ["called"]
    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_failed_closed"
    )
    assert payload["operator_canary_summary"]["failure_summary"] == {
        "error_type": "RuntimeError",
        "error_message": "operator payload failed",
        "failed_closed": True,
    }
    assert payload["next_safe_step"] == (
        "fix_three_core_shadow_operator_canary_"
        "failure_before_retry"
    )


def test_canary_surfaces_readback_order_and_count():
    payload = run_three_core_agent_shadow_operator_canary(
        enabled=True,
        shadow_payload_provider=_completed_shadow_payload,
    )
    summary = payload["operator_canary_summary"]

    assert summary["ordered_agent_names_found"] == list(
        ORDERED_CORE_AGENT_NAMES
    )
    assert summary["shadow_result_count"] == 3
    assert payload["runtime_readback"]["readback_status"] == (
        "three_core_shadow_runtime_readback_completed"
    )


def test_failed_runtime_readback_fails_canary_closed():
    source = _completed_shadow_payload()
    three_core = source["three_core_shadow_pipeline_hook_payload"]
    three_core["hook_status"] = (
        "three_core_shadow_pipeline_hook_failed_closed"
    )
    three_core["failure"] = {
        "failed_agent_name": "jd_intelligence",
        "error_type": "ValueError",
        "error_message": "shadow failure",
        "failed_closed": True,
    }

    payload = run_three_core_agent_shadow_operator_canary(
        enabled=True,
        shadow_payload_provider=lambda: source,
    )

    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_failed_closed"
    )
    assert payload["operator_canary_summary"]["readback_status"] == (
        "three_core_shadow_runtime_readback_failed_closed"
    )
    assert payload["operator_canary_summary"]["failure_summary"] == (
        three_core["failure"]
    )


def test_inputs_and_provider_payload_are_defensively_copied():
    source = _completed_shadow_payload()
    context = {"review": {"owner": "operator"}}
    before = deepcopy((source, context))

    payload = run_three_core_agent_shadow_operator_canary(
        enabled=True,
        shadow_payload_provider=lambda: source,
        canary_context=context,
    )

    assert payload["source_shadow_payload_summary"][
        "source_shadow_payload"
    ] == before[0]
    assert payload["canary_context"] == before[1]
    payload["canary_context"]["review"]["owner"] = "changed"
    payload["source_shadow_payload_summary"]["source_shadow_payload"][
        "hook_status"
    ] = "changed"
    assert (source, context) == before


def test_all_authorization_and_mutation_paths_remain_false():
    payload = run_three_core_agent_shadow_operator_canary(
        enabled=True,
        shadow_payload_provider=_completed_shadow_payload,
    )

    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    assert payload["operator_canary_only"] is True
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


def test_source_has_no_pipeline_provider_network_database_or_file_wiring():
    source = (
        ROOT / "src/agents/three_core_agent_shadow_operator_canary.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "src.pipeline",
        "collector",
        "run_shadow_sidecar_pipeline_hook(",
        "run_three_core_agent_shadow_pipeline_hook(",
        "build_three_core_agent_shadow_callable_adapters(",
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
        "src.app",
    ):
        assert marker not in source

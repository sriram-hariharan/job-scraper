from copy import deepcopy
from pathlib import Path

from src.agents.jd_live_intelligence_runtime_preflight import (
    build_live_jd_intelligence_runtime_preflight,
)


ROOT = Path(__file__).resolve().parents[1]


def _phase16a_plan() -> dict:
    return {
        "runtime_readiness_plan_status": (
            "runtime_readiness_plan_ready_for_review_no_runtime"
        ),
        "runtime_readiness_plan_only": True,
        "planning_only": True,
        "approval_gate_open": False,
        "execution_authorized": False,
        "runtime_authorized": False,
        "rollout_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "external_adapter_required": True,
        "config_gate_required": True,
        "future_runtime_requires_separate_explicit_phase": True,
        "decision_boundaries": {
            "prefilter_relevance_is_separate": True,
            "jd_intelligence_evaluation_is_separate": True,
            "final_application_scoring_is_separate": True,
        },
        "forbidden_mutation_and_application_paths": {
            "scoring_influence_allowed": False,
            "ranking_influence_allowed": False,
            "queue_influence_allowed": False,
            "resume_mutation_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
        },
    }


def _config_gate() -> dict:
    return {
        "gate_status": "live_config_gate_allowed_for_future_canary",
        "canary_allowed": True,
        "shadow_only": True,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
    }


def _runbook() -> dict:
    return {
        "runbook_status": (
            "jd_live_canary_runbook_ready_for_operator_review"
        ),
        "manual_execution_only": True,
        "one_job_only": True,
        "shadow_only_required": True,
        "allowed_agent_name": "jd_intelligence",
        "external_adapter_required": True,
        "config_gate_allow_required": True,
        "execution_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
    }


def _ready_preflight(context: dict | None = None) -> dict:
    return build_live_jd_intelligence_runtime_preflight(
        enabled=True,
        phase16a_runtime_readiness_plan=_phase16a_plan(),
        provider_live_config_gate=_config_gate(),
        jd_live_canary_runbook=_runbook(),
        preflight_context=context,
    )


def test_runtime_preflight_is_default_off_and_review_only():
    preflight = build_live_jd_intelligence_runtime_preflight()

    assert preflight["runtime_preflight_enabled"] is False
    assert preflight["runtime_preflight_status"] == (
        "runtime_preflight_skipped_default_off"
    )
    assert preflight["default_off"] is True
    assert preflight["read_only"] is True
    assert preflight["shadow_only"] is True
    assert preflight["advisory_only"] is True
    assert preflight["runtime_preflight_only"] is True
    assert preflight["planning_only"] is True
    assert preflight["next_safe_step"] == (
        "enable_phase16b_runtime_preflight_only"
    )


def test_enabled_preflight_still_authorizes_no_runtime_or_invocation():
    preflight = _ready_preflight()

    assert preflight["runtime_preflight_status"] == (
        "runtime_preflight_ready_for_review_no_runtime"
    )
    assert preflight["approval_gate_open"] is False
    assert preflight["approval_recorded"] is False
    assert preflight["operator_approval_recorded"] is False
    assert preflight["execution_authorized"] is False
    assert preflight["runtime_authorized"] is False
    assert preflight["rollout_authorized"] is False
    assert preflight["canary_execution_authorized"] is False
    assert preflight["adapter_invocation_authorized"] is False
    assert preflight["mutation_authorized"] is False
    assert preflight["mutation_authorized_agent_count"] == 0
    assert preflight["next_safe_step"] == (
        "review_phase16b_runtime_preflight_without_runtime"
    )


def test_inputs_are_summarized_separately_and_not_mutated():
    phase16a = _phase16a_plan()
    gate = _config_gate()
    runbook = _runbook()
    context = {"preflight": {"reviewer": "operator"}}
    before = deepcopy((phase16a, gate, runbook, context))
    preflight = build_live_jd_intelligence_runtime_preflight(
        enabled=True,
        phase16a_runtime_readiness_plan=phase16a,
        provider_live_config_gate=gate,
        jd_live_canary_runbook=runbook,
        preflight_context=context,
    )

    assert preflight["phase16a_runtime_readiness_plan_summary"][
        "source_phase16a_plan"
    ] == before[0]
    assert preflight["provider_live_config_gate_summary"][
        "source_config_gate"
    ] == before[1]
    assert preflight["jd_live_canary_runbook_summary"][
        "source_runbook"
    ] == before[2]
    assert preflight["phase16b_runtime_preflight"]["scope"] == (
        "live_jd_intelligence_runtime_preflight"
    )
    assert preflight["preflight_context"] == before[3]
    assert (phase16a, gate, runbook, context) == before


def test_checks_recognize_complete_safe_preflight_shape():
    preflight = _ready_preflight({"review": "phase16b"})
    checks = preflight["phase16b_runtime_preflight"][
        "runtime_preflight_checks"
    ]

    for key in (
        "phase16a_plan_supplied",
        "phase16a_runtime_readiness_plan_only",
        "phase16a_execution_not_authorized",
        "phase16a_runtime_not_authorized",
        "phase16a_rollout_not_authorized",
        "phase16a_mutation_not_authorized",
        "phase16a_approval_gate_closed",
        "phase16a_external_adapter_required",
        "phase16a_config_gate_required",
        "provider_live_config_gate_supplied",
        "provider_live_config_gate_allowed",
        "provider_live_config_gate_shadow_only",
        "provider_live_config_gate_no_mutation_authority",
        "jd_live_canary_runbook_supplied",
        "runbook_manual_only",
        "runbook_one_job_only",
        "runbook_shadow_only_required",
        "runbook_jd_intelligence_only",
        "runbook_external_adapter_required",
        "runbook_config_gate_required",
        "canary_execution_not_authorized",
        "adapter_invocation_not_authorized",
        "scoring_influence_blocked",
        "ranking_influence_blocked",
        "queue_influence_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "preflight_context_supplied",
    ):
        assert checks[key] is True


def test_config_gate_allow_does_not_authorize_execution():
    preflight = _ready_preflight()

    assert preflight["provider_live_config_gate_summary"][
        "canary_allowed_by_config_gate"
    ] is True
    assert preflight["canary_execution_authorized"] is False
    assert preflight["adapter_invocation_authorized"] is False
    state = preflight["phase16b_runtime_preflight"][
        "preflight_state"
    ]
    assert state["canary_execution_authorized"] is False
    assert state["adapter_invocation_authorized"] is False


def test_forbidden_mutation_and_application_paths_are_all_false():
    preflight = build_live_jd_intelligence_runtime_preflight(
        enabled=True
    )

    assert all(
        value is False
        for value in preflight[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase16b_contract_exactly():
    safety = build_live_jd_intelligence_runtime_preflight(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_preflight_only": True,
        "planning_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "one_job_only": True,
        "manual_only": True,
        "external_adapter_required": True,
        "config_gate_required": True,
        "future_runtime_requires_separate_explicit_phase": True,
        "provider_execution_added": False,
        "provider_client_constructed": False,
        "provider_sdk_imported": False,
        "environment_secrets_read": False,
        "network_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_read_files": False,
        "did_write_files": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def test_source_has_no_provider_network_database_or_file_wiring():
    source = (
        ROOT / "src/agents/jd_live_intelligence_runtime_preflight.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
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
        "run_jd_live_provider_canary(",
        "run_manual_jd_live_provider_canary_command(",
        "invoke_jd_live_provider_external_adapter(",
        "external_adapter(",
        "connect(",
        "cursor.execute(",
        ".commit(",
        "open(",
        "read_text(",
        "read_bytes(",
        "write_text(",
        "write_bytes(",
    ):
        assert marker not in source

from copy import deepcopy
from pathlib import Path

from src.agents.jd_live_intelligence_approval_gate import (
    build_live_jd_intelligence_approval_gate,
)
from src.agents.jd_live_intelligence_evidence_review import (
    build_live_jd_intelligence_evidence_review,
)
from src.agents.jd_live_intelligence_expansion_plan import (
    build_live_jd_intelligence_expansion_plan,
)
from src.agents.jd_live_intelligence_operator_decision import (
    build_live_jd_intelligence_operator_decision,
)
from src.agents.jd_live_intelligence_phase_wrap import (
    build_live_jd_intelligence_phase_wrap,
)
from src.agents.jd_live_intelligence_review_readiness import (
    build_live_jd_intelligence_review_readiness,
)
from src.agents.jd_live_intelligence_rollout_handoff import (
    build_live_jd_intelligence_rollout_handoff,
)
from src.agents.jd_live_intelligence_runtime_readiness_plan import (
    build_live_jd_intelligence_runtime_readiness_plan,
)
from src.agents.jd_live_provider_canary_runbook import (
    build_jd_live_provider_canary_runbook,
)
from src.agents.provider_live_activation_safety_plan import (
    build_provider_live_activation_safety_plan,
)
from src.agents.provider_live_config_gate import (
    evaluate_provider_live_config_gate,
)
from src.agents.provider_runtime_activation_plan import (
    build_provider_runtime_activation_plan,
)
from src.agents.provider_runtime_readiness import (
    build_provider_runtime_readiness_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def _phase15_wrap() -> dict:
    evidence = {
        "manual_command_enabled": True,
        "one_job_only": True,
        "jd_only": True,
        "shadow_only": True,
        "provider_call_attempted": True,
        "provider_call_succeeded": True,
        "fallback_used": False,
        "structured_output_validated": True,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "llmops_metadata": {
            "model_provider": "approved-provider",
            "model_name": "approved-model",
            "schema_validation_status": "valid",
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
        },
    }
    phase15a = build_live_jd_intelligence_expansion_plan(
        enabled=True,
        phase14_manual_canary_evidence=evidence,
    )
    phase15b = build_live_jd_intelligence_review_readiness(
        enabled=True,
        phase15a_expansion_plan=phase15a,
    )
    phase15c = build_live_jd_intelligence_evidence_review(
        enabled=True,
        phase15a_expansion_plan=phase15a,
        phase15b_review_readiness=phase15b,
        phase14_manual_canary_evidence=evidence,
    )
    phase15d = build_live_jd_intelligence_operator_decision(
        enabled=True,
        phase15c_evidence_review=phase15c,
    )
    phase15e = build_live_jd_intelligence_approval_gate(
        enabled=True,
        phase15d_operator_decision=phase15d,
    )
    phase15f = build_live_jd_intelligence_rollout_handoff(
        enabled=True,
        phase15e_approval_gate=phase15e,
    )
    return build_live_jd_intelligence_phase_wrap(
        enabled=True,
        phase15a_expansion_plan=phase15a,
        phase15b_review_readiness=phase15b,
        phase15c_evidence_review=phase15c,
        phase15d_operator_decision=phase15d,
        phase15e_approval_gate=phase15e,
        phase15f_rollout_handoff=phase15f,
    )


def _valid_live_config() -> dict:
    return {
        "live_canary_enabled": True,
        "agent_name": "jd_intelligence",
        "shadow_only": True,
        "provider_name": "approved-provider",
        "model_name": "approved-model",
        "allowed_provider_names": ["approved-provider"],
        "allowed_model_names": ["approved-model"],
        "timeout_seconds": 10,
        "retry_limit": 1,
        "max_input_tokens": 4_000,
        "max_output_tokens": 1_000,
        "max_estimated_cost": 0.25,
        "structured_output_validation_required": True,
        "deterministic_fallback_required": True,
        "llmops_metadata_required": True,
        "prompt_version": "jd-shadow-prompt-v1",
        "runtime_version": "jd-live-canary-runtime-v1",
        "no_mutation_authority": True,
        "mutation_authorized": False,
        "final_scoring_influence_enabled": False,
        "ranking_influence_enabled": False,
        "queue_influence_enabled": False,
        "resume_mutation_enabled": False,
        "execution_enabled": False,
        "submission_enabled": False,
    }


def _planning_inputs() -> tuple[dict, ...]:
    runtime = build_provider_runtime_readiness_payload(
        enabled=True,
        config={
            "provider_name": "approved-provider",
            "model_name": "approved-model",
            "configured_agent_names": ["jd_intelligence"],
            "shadow_only": True,
            "mutation_authorized": False,
        },
    )
    activation = build_provider_runtime_activation_plan(enabled=True)
    safety = build_provider_live_activation_safety_plan(enabled=True)
    gate = evaluate_provider_live_config_gate(
        enabled=True,
        config=_valid_live_config(),
    )
    runbook = build_jd_live_provider_canary_runbook(enabled=True)
    return runtime, activation, safety, gate, runbook


def _ready_plan(context: dict | None = None) -> dict:
    runtime, activation, safety, gate, runbook = _planning_inputs()
    return build_live_jd_intelligence_runtime_readiness_plan(
        enabled=True,
        phase15_wrap=_phase15_wrap(),
        provider_runtime_readiness=runtime,
        provider_runtime_activation_plan=activation,
        provider_live_safety_plan=safety,
        provider_live_config_gate=gate,
        jd_live_canary_runbook=runbook,
        runtime_readiness_context=context,
    )


def test_runtime_readiness_plan_is_default_off_and_planning_only():
    plan = build_live_jd_intelligence_runtime_readiness_plan()

    assert plan["runtime_readiness_plan_enabled"] is False
    assert plan["runtime_readiness_plan_status"] == (
        "runtime_readiness_plan_skipped_default_off"
    )
    assert plan["default_off"] is True
    assert plan["read_only"] is True
    assert plan["shadow_only"] is True
    assert plan["advisory_only"] is True
    assert plan["runtime_readiness_plan_only"] is True
    assert plan["planning_only"] is True
    assert plan["next_safe_step"] == (
        "enable_phase16a_runtime_readiness_plan_only"
    )


def test_enabled_plan_still_authorizes_no_runtime_or_mutation():
    plan = _ready_plan()

    assert plan["runtime_readiness_plan_status"] == (
        "runtime_readiness_plan_ready_for_review_no_runtime"
    )
    assert plan["approval_gate_open"] is False
    assert plan["approval_recorded"] is False
    assert plan["operator_approval_recorded"] is False
    assert plan["execution_authorized"] is False
    assert plan["rollout_authorized"] is False
    assert plan["runtime_authorized"] is False
    assert plan["mutation_authorized"] is False
    assert plan["mutation_authorized_agent_count"] == 0
    assert plan["next_safe_step"] == (
        "review_phase16a_runtime_readiness_plan_without_runtime"
    )


def test_inputs_are_summarized_separately_and_not_mutated():
    phase15 = _phase15_wrap()
    planning = _planning_inputs()
    context = {"review": {"owner": "operator"}}
    phase15_before = deepcopy(phase15)
    planning_before = deepcopy(planning)
    context_before = deepcopy(context)
    plan = build_live_jd_intelligence_runtime_readiness_plan(
        enabled=True,
        phase15_wrap=phase15,
        provider_runtime_readiness=planning[0],
        provider_runtime_activation_plan=planning[1],
        provider_live_safety_plan=planning[2],
        provider_live_config_gate=planning[3],
        jd_live_canary_runbook=planning[4],
        runtime_readiness_context=context,
    )

    assert plan["phase15_wrap_summary"]["source_phase15_wrap"] == (
        phase15_before
    )
    summaries = plan["provider_planning_summaries"]
    for index, key in enumerate(
        (
            "provider_runtime_readiness",
            "provider_runtime_activation_plan",
            "provider_live_safety_plan",
            "provider_live_config_gate",
            "jd_live_canary_runbook",
        )
    ):
        assert summaries[key]["source_payload"] == planning_before[index]
    assert plan["phase16a_runtime_readiness_planning"]["scope"] == (
        "live_jd_intelligence_runtime_readiness_plan"
    )
    assert plan["runtime_readiness_context"] == context_before
    assert phase15 == phase15_before
    assert planning == planning_before
    assert context == context_before


def test_checks_recognize_complete_safe_planning_shape():
    plan = _ready_plan({"review": "phase16a"})
    checks = plan["phase16a_runtime_readiness_planning"][
        "runtime_readiness_checks"
    ]

    for key in (
        "phase15_wrap_supplied",
        "phase15_wrap_review_only",
        "phase15_execution_not_authorized",
        "phase15_rollout_not_authorized",
        "phase15_mutation_not_authorized",
        "phase15_approval_gate_closed",
        "phase15_future_runtime_requires_explicit_phase",
        "provider_runtime_readiness_supplied",
        "provider_runtime_activation_plan_supplied",
        "provider_live_safety_plan_supplied",
        "provider_live_config_gate_supplied",
        "jd_live_canary_runbook_supplied",
        "external_adapter_required",
        "config_gate_required",
        "manual_only_boundary_preserved",
        "one_job_only_boundary_preserved",
        "shadow_only_boundary_preserved",
        "jd_intelligence_only_boundary_preserved",
        "scoring_influence_blocked",
        "ranking_influence_blocked",
        "queue_influence_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "runtime_readiness_context_supplied",
    ):
        assert checks[key] is True


def test_forbidden_mutation_and_application_paths_are_all_false():
    plan = build_live_jd_intelligence_runtime_readiness_plan(
        enabled=True
    )

    assert all(
        value is False
        for value in plan[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase16a_contract_exactly():
    safety = build_live_jd_intelligence_runtime_readiness_plan(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_readiness_plan_only": True,
        "planning_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "future_runtime_requires_separate_explicit_phase": True,
        "external_adapter_required": True,
        "config_gate_required": True,
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
        ROOT
        / "src/agents/jd_live_intelligence_runtime_readiness_plan.py"
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

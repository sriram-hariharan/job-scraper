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


ROOT = Path(__file__).resolve().parents[1]


def _phase15_chain() -> tuple[dict, ...]:
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
        operator_decision_context={"operator": "human-reviewer"},
    )
    phase15e = build_live_jd_intelligence_approval_gate(
        enabled=True,
        phase15d_operator_decision=phase15d,
        approval_gate_context={"approval": "closed-review"},
    )
    phase15f = build_live_jd_intelligence_rollout_handoff(
        enabled=True,
        phase15e_approval_gate=phase15e,
        rollout_handoff_context={"handoff": "review-only"},
    )
    return phase15a, phase15b, phase15c, phase15d, phase15e, phase15f


def _wrapped_chain(context: dict | None = None) -> dict:
    phase15a, phase15b, phase15c, phase15d, phase15e, phase15f = (
        _phase15_chain()
    )
    return build_live_jd_intelligence_phase_wrap(
        enabled=True,
        phase15a_expansion_plan=phase15a,
        phase15b_review_readiness=phase15b,
        phase15c_evidence_review=phase15c,
        phase15d_operator_decision=phase15d,
        phase15e_approval_gate=phase15e,
        phase15f_rollout_handoff=phase15f,
        phase_wrap_context=context,
    )


def test_phase_wrap_is_default_off_read_only_and_review_only():
    wrap = build_live_jd_intelligence_phase_wrap()

    assert wrap["phase_wrap_enabled"] is False
    assert wrap["phase_wrap_status"] == (
        "phase15_wrap_skipped_default_off"
    )
    assert wrap["default_off"] is True
    assert wrap["read_only"] is True
    assert wrap["shadow_only"] is True
    assert wrap["advisory_only"] is True
    assert wrap["phase_wrap_review_only"] is True
    assert wrap["approval_gate_closed"] is True
    assert wrap["next_safe_step"] == (
        "enable_phase15g_wrap_review_only"
    )


def test_enabled_wrap_remains_closed_non_executing_and_non_mutating():
    wrap = _wrapped_chain()

    assert wrap["phase_wrap_status"] == (
        "phase15_wrap_ready_for_review_no_runtime"
    )
    assert wrap["approval_gate_open"] is False
    assert wrap["approval_recorded"] is False
    assert wrap["operator_approval_recorded"] is False
    assert wrap["execution_authorized"] is False
    assert wrap["rollout_authorized"] is False
    assert wrap["mutation_authorized"] is False
    assert wrap["mutation_authorized_agent_count"] == 0
    assert wrap[
        "future_runtime_requires_separate_explicit_phase"
    ] is True
    assert wrap["next_safe_step"] == (
        "review_phase15g_wrap_without_runtime"
    )


def test_phase_inputs_and_wrap_context_are_separate_and_not_mutated():
    phases = _phase15_chain()
    context = {"wrap": {"reviewer": "operator"}}
    phases_before = deepcopy(phases)
    context_before = deepcopy(context)
    wrap = build_live_jd_intelligence_phase_wrap(
        enabled=True,
        phase15a_expansion_plan=phases[0],
        phase15b_review_readiness=phases[1],
        phase15c_evidence_review=phases[2],
        phase15d_operator_decision=phases[3],
        phase15e_approval_gate=phases[4],
        phase15f_rollout_handoff=phases[5],
        phase_wrap_context=context,
    )

    summaries = wrap["phase15a_to_phase15f_summaries"]
    for index, phase_name in enumerate(
        ("phase15a", "phase15b", "phase15c", "phase15d", "phase15e", "phase15f")
    ):
        assert summaries[phase_name]["source_payload"] == phases_before[index]
    assert wrap["phase15g_wrap_review"]["scope"] == (
        "live_jd_intelligence_phase_wrap_review"
    )
    assert wrap["phase_wrap_context"] == context_before
    assert phases == phases_before
    assert context == context_before


def test_phase_wrap_checks_recognize_complete_closed_review_chain():
    wrap = _wrapped_chain({"review": "phase15g"})
    checks = wrap["phase15g_wrap_review"]["phase_wrap_checks"]

    for key in (
        "phase15a_supplied",
        "phase15b_supplied",
        "phase15c_supplied",
        "phase15d_supplied",
        "phase15e_supplied",
        "phase15f_supplied",
        "phase15a_planning_only",
        "phase15b_review_only",
        "phase15c_evidence_review_only",
        "phase15d_operator_decision_review_only",
        "phase15e_approval_gate_review_only",
        "phase15f_rollout_handoff_review_only",
        "phase15e_approval_gate_closed",
        "phase15f_approval_gate_closed",
        "no_phase_authorized_execution",
        "no_phase_authorized_rollout",
        "no_phase_authorized_mutation",
        "no_phase_recorded_approval",
        "future_runtime_requires_separate_explicit_phase",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "phase_wrap_context_supplied",
    ):
        assert checks[key] is True


def test_forbidden_mutation_and_application_paths_are_all_false():
    wrap = build_live_jd_intelligence_phase_wrap(enabled=True)

    assert all(
        value is False
        for value in wrap[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase15g_contract_exactly():
    safety = build_live_jd_intelligence_phase_wrap(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "phase_wrap_review_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
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
        ROOT / "src/agents/jd_live_intelligence_phase_wrap.py"
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

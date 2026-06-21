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
from src.agents.jd_live_intelligence_review_readiness import (
    build_live_jd_intelligence_review_readiness,
)


ROOT = Path(__file__).resolve().parents[1]


def _phase15d_decision() -> dict:
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
    return build_live_jd_intelligence_operator_decision(
        enabled=True,
        phase15c_evidence_review=phase15c,
        operator_decision_context={"operator": "human-reviewer"},
    )


def test_approval_gate_is_default_off_read_only_and_closed():
    gate = build_live_jd_intelligence_approval_gate()

    assert gate["approval_gate_enabled"] is False
    assert gate["approval_gate_status"] == (
        "approval_gate_skipped_default_off"
    )
    assert gate["default_off"] is True
    assert gate["read_only"] is True
    assert gate["shadow_only"] is True
    assert gate["advisory_only"] is True
    assert gate["approval_gate_review_only"] is True
    assert gate["approval_gate_open"] is False
    assert gate["approval_recorded"] is False
    assert gate["operator_approval_recorded"] is False
    assert gate[
        "operator_approval_required_before_any_future_runtime"
    ] is True
    assert gate["next_safe_step"] == (
        "enable_phase15e_approval_gate_review_only"
    )


def test_enabled_gate_remains_closed_non_executing_and_non_mutating():
    gate = build_live_jd_intelligence_approval_gate(
        enabled=True,
        phase15d_operator_decision=_phase15d_decision(),
    )

    assert gate["approval_gate_status"] == (
        "approval_gate_ready_for_review_closed"
    )
    assert gate["approval_gate_open"] is False
    assert gate["approval_recorded"] is False
    assert gate["operator_approval_recorded"] is False
    assert gate["execution_authorized"] is False
    assert gate["rollout_authorized"] is False
    assert gate["mutation_authorized"] is False
    assert gate["mutation_authorized_agent_count"] == 0
    assert gate["next_safe_step"] == (
        "review_phase15e_closed_approval_gate_without_execution"
    )


def test_phase15d_and_gate_context_are_separate_and_not_mutated():
    phase15d = _phase15d_decision()
    context = {"approval_ticket": "phase15e-closed-review"}
    phase15d_before = deepcopy(phase15d)
    context_before = deepcopy(context)
    gate = build_live_jd_intelligence_approval_gate(
        enabled=True,
        phase15d_operator_decision=phase15d,
        approval_gate_context=context,
    )

    summary = gate["phase15d_operator_decision_summary"]
    phase15e = gate["phase15e_approval_gate_review"]

    assert summary["source_operator_decision"] == phase15d_before
    assert summary["operator_decision_status"] == (
        "operator_decision_ready_for_human_review"
    )
    assert phase15e["scope"] == (
        "live_jd_intelligence_approval_gate_review"
    )
    assert gate["approval_gate_context"] == context_before
    assert phase15d == phase15d_before
    assert context == context_before


def test_approval_checks_recognize_successful_phase15d_review():
    gate = build_live_jd_intelligence_approval_gate(
        enabled=True,
        phase15d_operator_decision=_phase15d_decision(),
        approval_gate_context={"reviewer": "human"},
    )
    checks = gate["phase15e_approval_gate_review"][
        "approval_gate_checks"
    ]

    for key in (
        "phase15d_operator_decision_supplied",
        "phase15d_operator_decision_review_only",
        "phase15d_execution_not_authorized",
        "phase15d_rollout_not_authorized",
        "phase15d_mutation_not_authorized",
        "phase15d_operator_approval_not_recorded",
        "phase15d_human_review_required",
        "phase15d_execution_not_triggered",
        "phase15d_rollout_not_triggered",
        "phase15d_successful_evidence_chain_present",
        "scoring_influence_blocked",
        "ranking_influence_blocked",
        "queue_influence_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "approval_gate_context_supplied",
        "approval_gate_remains_closed",
        "future_runtime_requires_separate_explicit_phase",
    ):
        assert checks[key] is True


def test_forbidden_mutation_and_application_paths_are_all_false():
    gate = build_live_jd_intelligence_approval_gate(enabled=True)

    assert all(
        value is False
        for value in gate[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase15e_contract_exactly():
    safety = build_live_jd_intelligence_approval_gate(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "approval_gate_review_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
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
        ROOT / "src/agents/jd_live_intelligence_approval_gate.py"
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

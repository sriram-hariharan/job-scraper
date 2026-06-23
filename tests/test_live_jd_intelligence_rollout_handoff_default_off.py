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
from src.agents.jd_live_intelligence_rollout_handoff import (
    build_live_jd_intelligence_rollout_handoff,
)


ROOT = Path(__file__).resolve().parents[1]


def _phase15e_gate() -> dict:
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
    return build_live_jd_intelligence_approval_gate(
        enabled=True,
        phase15d_operator_decision=phase15d,
        approval_gate_context={"approval": "closed-review"},
    )


def test_rollout_handoff_is_default_off_and_review_only():
    handoff = build_live_jd_intelligence_rollout_handoff()

    assert handoff["rollout_handoff_enabled"] is False
    assert handoff["rollout_handoff_status"] == (
        "rollout_handoff_skipped_default_off"
    )
    assert handoff["default_off"] is True
    assert handoff["read_only"] is True
    assert handoff["shadow_only"] is True
    assert handoff["advisory_only"] is True
    assert handoff["rollout_handoff_review_only"] is True
    assert handoff["approval_gate_open"] is False
    assert handoff["next_safe_step"] == (
        "enable_phase15f_rollout_handoff_review_only"
    )


def test_enabled_handoff_still_authorizes_no_runtime_or_mutation():
    handoff = build_live_jd_intelligence_rollout_handoff(
        enabled=True,
        phase15e_approval_gate=_phase15e_gate(),
    )

    assert handoff["rollout_handoff_status"] == (
        "rollout_handoff_ready_for_review_no_runtime"
    )
    assert handoff["approval_gate_open"] is False
    assert handoff["approval_recorded"] is False
    assert handoff["operator_approval_recorded"] is False
    assert handoff["execution_authorized"] is False
    assert handoff["rollout_authorized"] is False
    assert handoff["mutation_authorized"] is False
    assert handoff["mutation_authorized_agent_count"] == 0
    assert handoff[
        "future_runtime_requires_separate_explicit_phase"
    ] is True
    assert handoff["next_safe_step"] == (
        "review_phase15f_rollout_handoff_without_runtime"
    )


def test_phase15e_summary_and_phase15f_review_are_separate():
    gate = _phase15e_gate()
    context = {"handoff": {"reviewer": "operator"}}
    gate_before = deepcopy(gate)
    context_before = deepcopy(context)
    handoff = build_live_jd_intelligence_rollout_handoff(
        enabled=True,
        phase15e_approval_gate=gate,
        rollout_handoff_context=context,
    )

    summary = handoff["phase15e_approval_gate_summary"]
    review = handoff["phase15f_rollout_handoff_review"]

    assert summary["source_approval_gate"] == gate_before
    assert summary["approval_gate_status"] == (
        "approval_gate_ready_for_review_closed"
    )
    assert summary["approval_gate_open"] is False
    assert review["scope"] == (
        "live_jd_intelligence_rollout_handoff_review"
    )
    assert handoff["rollout_handoff_context"] == context_before
    assert gate == gate_before
    assert context == context_before


def test_rollout_handoff_checks_preserve_closed_review_chain():
    handoff = build_live_jd_intelligence_rollout_handoff(
        enabled=True,
        phase15e_approval_gate=_phase15e_gate(),
        rollout_handoff_context={"review": "phase15f"},
    )
    checks = handoff["phase15f_rollout_handoff_review"][
        "rollout_handoff_checks"
    ]

    for key in (
        "phase15e_approval_gate_supplied",
        "phase15e_approval_gate_review_only",
        "phase15e_approval_gate_closed",
        "phase15e_execution_not_authorized",
        "phase15e_rollout_not_authorized",
        "phase15e_mutation_not_authorized",
        "phase15e_approval_not_recorded",
        "phase15e_operator_approval_not_recorded",
        "phase15e_future_runtime_requires_explicit_phase",
        "successful_review_chain_present",
        "scoring_influence_blocked",
        "ranking_influence_blocked",
        "queue_influence_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "rollout_handoff_context_supplied",
    ):
        assert checks[key] is True


def test_forbidden_mutation_and_application_paths_are_all_false():
    handoff = build_live_jd_intelligence_rollout_handoff(enabled=True)

    assert all(
        value is False
        for value in handoff[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase15f_contract_exactly():
    safety = build_live_jd_intelligence_rollout_handoff(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "rollout_handoff_review_only": True,
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
        ROOT / "src/agents/jd_live_intelligence_rollout_handoff.py"
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

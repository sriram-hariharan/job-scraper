from copy import deepcopy
from pathlib import Path

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


def _phase15c_review() -> dict:
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
    return build_live_jd_intelligence_evidence_review(
        enabled=True,
        phase15a_expansion_plan=phase15a,
        phase15b_review_readiness=phase15b,
        phase14_manual_canary_evidence=evidence,
    )


def test_operator_decision_is_default_off_read_only_and_review_only():
    decision = build_live_jd_intelligence_operator_decision()

    assert decision["operator_decision_enabled"] is False
    assert decision["operator_decision_status"] == (
        "operator_decision_skipped_default_off"
    )
    assert decision["default_off"] is True
    assert decision["read_only"] is True
    assert decision["shadow_only"] is True
    assert decision["advisory_only"] is True
    assert decision["operator_decision_review_only"] is True
    assert decision["operator_approval_recorded"] is False
    assert decision[
        "operator_approval_required_before_any_future_runtime"
    ] is True
    assert decision["next_safe_step"] == (
        "enable_phase15d_operator_decision_review_only"
    )


def test_enabled_decision_remains_non_executing_and_non_mutating():
    decision = build_live_jd_intelligence_operator_decision(
        enabled=True,
        phase15c_evidence_review=_phase15c_review(),
    )

    assert decision["operator_decision_status"] == (
        "operator_decision_ready_for_human_review"
    )
    assert decision["execution_authorized"] is False
    assert decision["rollout_authorized"] is False
    assert decision["operator_approval_recorded"] is False
    assert decision["mutation_authorized"] is False
    assert decision["mutation_authorized_agent_count"] == 0
    assert decision["next_safe_step"] == (
        "human_review_phase15d_operator_decision_without_execution"
    )


def test_phase15c_and_operator_context_are_separate_and_not_mutated():
    phase15c = _phase15c_review()
    context = {"operator_ticket": "phase15d-review-only"}
    phase15c_before = deepcopy(phase15c)
    context_before = deepcopy(context)
    decision = build_live_jd_intelligence_operator_decision(
        enabled=True,
        phase15c_evidence_review=phase15c,
        operator_decision_context=context,
    )

    summary = decision["phase15c_evidence_review_summary"]
    phase15d = decision["phase15d_operator_decision_review"]

    assert summary["source_evidence_review"] == phase15c_before
    assert summary["review_outcome"] == (
        "evidence_review_ready_for_operator_review"
    )
    assert phase15d["scope"] == (
        "live_jd_intelligence_operator_decision_review"
    )
    assert decision["operator_decision_context"] == context_before
    assert phase15c == phase15c_before
    assert context == context_before


def test_operator_checks_recognize_successful_phase15c_review():
    decision = build_live_jd_intelligence_operator_decision(
        enabled=True,
        phase15c_evidence_review=_phase15c_review(),
        operator_decision_context={"operator": "human-reviewer"},
    )
    checks = decision["phase15d_operator_decision_review"][
        "operator_decision_checks"
    ]

    for key in (
        "phase15c_evidence_review_supplied",
        "phase15c_evidence_review_only",
        "phase15c_execution_not_authorized",
        "phase15c_rollout_not_authorized",
        "phase15c_mutation_not_authorized",
        "phase15c_provider_call_succeeded",
        "phase15c_structured_output_validated",
        "phase15c_schema_validation_valid",
        "phase15c_fallback_not_used",
        "phase15c_zero_mutation_authority_preserved",
        "scoring_influence_blocked",
        "ranking_influence_blocked",
        "queue_influence_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "operator_context_supplied",
    ):
        assert checks[key] is True


def test_forbidden_mutation_and_application_paths_are_all_false():
    decision = build_live_jd_intelligence_operator_decision(
        enabled=True
    )

    assert all(
        value is False
        for value in decision[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase15d_contract_exactly():
    safety = build_live_jd_intelligence_operator_decision(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "operator_decision_review_only": True,
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
        ROOT / "src/agents/jd_live_intelligence_operator_decision.py"
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

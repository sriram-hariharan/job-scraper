from copy import deepcopy
from pathlib import Path

from src.agents.jd_live_intelligence_evidence_review import (
    build_live_jd_intelligence_evidence_review,
)
from src.agents.jd_live_intelligence_expansion_plan import (
    build_live_jd_intelligence_expansion_plan,
)
from src.agents.jd_live_intelligence_review_readiness import (
    build_live_jd_intelligence_review_readiness,
)


ROOT = Path(__file__).resolve().parents[1]


def _phase14_evidence() -> dict:
    return {
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
        "readback": {
            "provider_call_attempted": True,
            "provider_call_succeeded": True,
            "structured_output_validated": True,
            "source_validation_status": "valid",
        },
    }


def _phase15_payloads() -> tuple[dict, dict]:
    phase15a = build_live_jd_intelligence_expansion_plan(
        enabled=True,
        phase14_manual_canary_evidence=_phase14_evidence(),
    )
    phase15b = build_live_jd_intelligence_review_readiness(
        enabled=True,
        phase15a_expansion_plan=phase15a,
    )
    return phase15a, phase15b


def test_evidence_review_is_default_off_read_only_and_review_only():
    review = build_live_jd_intelligence_evidence_review()

    assert review["evidence_review_enabled"] is False
    assert review["review_outcome"] == (
        "evidence_review_skipped_default_off"
    )
    assert review["default_off"] is True
    assert review["read_only"] is True
    assert review["shadow_only"] is True
    assert review["advisory_only"] is True
    assert review["evidence_review_only"] is True
    assert review["execution_authorized"] is False
    assert review["rollout_authorized"] is False
    assert review["next_safe_step"] == (
        "enable_phase15c_evidence_review_only"
    )


def test_enabled_review_remains_non_executing_and_non_mutating():
    phase15a, phase15b = _phase15_payloads()
    review = build_live_jd_intelligence_evidence_review(
        enabled=True,
        phase15a_expansion_plan=phase15a,
        phase15b_review_readiness=phase15b,
        phase14_manual_canary_evidence=_phase14_evidence(),
    )

    assert review["review_outcome"] == (
        "evidence_review_ready_for_operator_review"
    )
    assert review["jd_intelligence_only"] is True
    assert review["execution_authorized"] is False
    assert review["rollout_authorized"] is False
    assert review["mutation_authorized"] is False
    assert review["mutation_authorized_agent_count"] == 0
    assert review["next_safe_step"] == (
        "operator_review_phase15c_evidence_without_execution"
    )


def test_phase_inputs_are_separate_and_are_not_mutated():
    phase14 = _phase14_evidence()
    phase15a, phase15b = _phase15_payloads()
    context = {"review_ticket": "phase15c-input-only"}
    before14 = deepcopy(phase14)
    before15a = deepcopy(phase15a)
    before15b = deepcopy(phase15b)
    before_context = deepcopy(context)

    review = build_live_jd_intelligence_evidence_review(
        enabled=True,
        phase15a_expansion_plan=phase15a,
        phase15b_review_readiness=phase15b,
        phase14_manual_canary_evidence=phase14,
        evidence_context=context,
    )

    assert review["phase14_manual_canary_evidence_summary"][
        "source_evidence"
    ] == before14
    assert review["phase15a_expansion_plan_summary"][
        "source_plan"
    ] == before15a
    assert review["phase15b_review_readiness_summary"][
        "source_readiness"
    ] == before15b
    assert phase14 == before14
    assert phase15a == before15a
    assert phase15b == before15b
    assert context == before_context


def test_successful_manual_one_job_evidence_is_recognized():
    phase15a, phase15b = _phase15_payloads()
    review = build_live_jd_intelligence_evidence_review(
        enabled=True,
        phase15a_expansion_plan=phase15a,
        phase15b_review_readiness=phase15b,
        phase14_manual_canary_evidence=_phase14_evidence(),
    )
    checks = review["evidence_review_checks"]

    for key in (
        "phase14_evidence_supplied",
        "provider_call_attempted",
        "provider_call_succeeded",
        "fallback_not_used",
        "structured_output_validated",
        "schema_validation_valid",
        "mutation_authority_remained_false",
        "mutation_authorized_agent_count_zero",
        "jd_source_was_manual_single_job",
        "provider_model_recorded",
        "token_usage_recorded",
        "phase15a_plan_supplied",
        "phase15a_planning_only",
        "phase15a_execution_not_authorized",
        "phase15b_review_readiness_supplied",
        "phase15b_review_only",
        "phase15b_rollout_not_authorized",
        "scoring_influence_blocked",
        "ranking_influence_blocked",
        "queue_influence_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
    ):
        assert checks[key] is True


def test_forbidden_mutation_and_application_paths_are_all_false():
    review = build_live_jd_intelligence_evidence_review(enabled=True)

    assert all(
        value is False
        for value in review[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase15c_contract_exactly():
    safety = build_live_jd_intelligence_evidence_review(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "evidence_review_only": True,
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
        ROOT / "src/agents/jd_live_intelligence_evidence_review.py"
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

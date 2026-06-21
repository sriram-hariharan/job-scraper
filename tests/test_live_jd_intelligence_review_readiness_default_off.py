from copy import deepcopy
from pathlib import Path

from src.agents.jd_live_intelligence_expansion_plan import (
    build_live_jd_intelligence_expansion_plan,
)
from src.agents.jd_live_intelligence_review_readiness import (
    build_live_jd_intelligence_review_readiness,
)


ROOT = Path(__file__).resolve().parents[1]


def _phase15a_plan() -> dict:
    return build_live_jd_intelligence_expansion_plan(
        enabled=True,
        phase14_manual_canary_evidence={
            "provider_call_succeeded": True,
            "structured_output_validated": True,
            "fallback_used": False,
            "mutation_authorized": False,
            "shadow_only": True,
        },
    )


def test_review_readiness_is_default_off_and_read_only():
    readiness = build_live_jd_intelligence_review_readiness()

    assert readiness["review_readiness_enabled"] is False
    assert readiness["readiness_status"] == (
        "live_jd_review_readiness_skipped_default_off"
    )
    assert readiness["default_off"] is True
    assert readiness["read_only"] is True
    assert readiness["shadow_only"] is True
    assert readiness["advisory_only"] is True
    assert readiness["review_readiness_only"] is True
    assert readiness["execution_authorized"] is False
    assert readiness["rollout_authorized"] is False
    assert readiness["next_safe_step"] == (
        "enable_phase15b_review_only"
    )


def test_enabled_state_remains_non_executing_and_non_mutating():
    readiness = build_live_jd_intelligence_review_readiness(
        enabled=True,
        phase15a_expansion_plan=_phase15a_plan(),
    )

    assert readiness["readiness_status"] == (
        "live_jd_review_readiness_ready_for_review"
    )
    assert readiness["jd_intelligence_only"] is True
    assert readiness["execution_authorized"] is False
    assert readiness["rollout_authorized"] is False
    assert readiness["mutation_authorized"] is False
    assert readiness["mutation_authorized_agent_count"] == 0
    assert readiness["next_safe_step"] == (
        "review_phase15b_jd_readiness_without_execution"
    )


def test_phase15a_plan_is_summarized_separately_without_mutation():
    plan = _phase15a_plan()
    context = {"review_ticket": "phase15b-review-only"}
    plan_before = deepcopy(plan)
    context_before = deepcopy(context)
    readiness = build_live_jd_intelligence_review_readiness(
        enabled=True,
        phase15a_expansion_plan=plan,
        review_context=context,
    )

    summary = readiness["phase15a_plan_summary"]
    review = readiness["phase15b_review_readiness"]
    checks = review["review_checks"]
    boundaries = review["decision_boundaries"]

    assert summary["plan_status"] == (
        "live_jd_expansion_plan_ready_for_review"
    )
    assert summary["planning_only"] is True
    assert summary["execution_authorized"] is False
    assert summary["provider_execution_added"] is False
    assert summary["phase14_manual_canary_evidence"][
        "source_phase"
    ] == "phase_14_manual_one_job_canary"
    assert checks["phase15a_plan_reviewed"] is True
    assert checks["phase14_canary_evidence_reviewed"] is True
    assert checks["jd_only_scope_preserved"] is True
    assert checks["shadow_only_scope_preserved"] is True
    assert checks[
        "one_job_manual_evidence_boundary_preserved"
    ] is True
    assert checks["structured_output_validation_preserved"] is True
    assert checks["deterministic_fallback_preserved"] is True
    assert checks["llmops_readback_fields_preserved"] is True
    assert checks["runtime_cost_limits_preserved"] is True
    assert checks[
        "rollback_off_switch_requirements_preserved"
    ] is True
    assert checks["zero_mutation_authority_preserved"] is True
    assert boundaries["prefilter_relevance_is_separate"] is True
    assert boundaries[
        "jd_intelligence_evaluation_is_separate"
    ] is True
    assert boundaries["final_application_scoring_is_separate"] is True
    assert plan == plan_before
    assert context == context_before


def test_forbidden_mutation_and_application_paths_are_all_false():
    readiness = build_live_jd_intelligence_review_readiness(
        enabled=True,
        phase15a_expansion_plan=_phase15a_plan(),
    )

    forbidden = readiness[
        "forbidden_mutation_and_application_paths"
    ]
    assert all(value is False for value in forbidden.values())


def test_safety_metadata_matches_phase15b_contract_exactly():
    safety = build_live_jd_intelligence_review_readiness(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "review_readiness_only": True,
        "jd_intelligence_only": True,
        "provider_execution_added": False,
        "provider_client_constructed": False,
        "provider_sdk_imported": False,
        "environment_secrets_read": False,
        "network_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def test_source_has_no_provider_network_database_or_write_wiring():
    source = (
        ROOT / "src/agents/jd_live_intelligence_review_readiness.py"
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
        "write_text(",
        "write_bytes(",
    ):
        assert marker not in source

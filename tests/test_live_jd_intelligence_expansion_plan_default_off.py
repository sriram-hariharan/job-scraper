from copy import deepcopy
from pathlib import Path

from src.agents.jd_live_intelligence_expansion_plan import (
    build_live_jd_intelligence_expansion_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def _successful_phase14_evidence() -> dict:
    return {
        "provider_call_succeeded": True,
        "structured_output_validated": True,
        "fallback_used": False,
        "mutation_authorized": False,
        "shadow_only": True,
    }


def test_expansion_plan_is_default_off_and_planning_only():
    plan = build_live_jd_intelligence_expansion_plan()

    assert plan["plan_enabled"] is False
    assert plan["plan_status"] == (
        "live_jd_expansion_plan_skipped_default_off"
    )
    assert plan["default_off"] is True
    assert plan["planning_only"] is True
    assert plan["execution_authorized"] is False


def test_phase14_evidence_is_separate_from_phase15a_planning():
    evidence = _successful_phase14_evidence()
    before = deepcopy(evidence)
    plan = build_live_jd_intelligence_expansion_plan(
        enabled=True,
        phase14_manual_canary_evidence=evidence,
    )

    phase14 = plan["phase14_manual_canary_evidence"]
    phase15 = plan["phase15a_expansion_planning"]
    forbidden = plan["forbidden_mutation_and_application_paths"]

    assert phase14["source_phase"] == "phase_14_manual_one_job_canary"
    assert phase14["manual_one_job_canary_succeeded"] is True
    assert phase14["structured_output_validated"] is True
    assert phase14["fallback_not_used"] is True
    assert phase14["mutation_authority_remained_false"] is True
    assert phase15["scope"] == "read_only_live_jd_intelligence_expansion"
    assert phase15["agent_name"] == "jd_intelligence"
    assert phase15["provider_execution_added"] is False
    assert forbidden["application_submission_allowed"] is False
    assert evidence == before


def test_safety_metadata_matches_phase15a_contract():
    safety = build_live_jd_intelligence_expansion_plan(
        enabled=True
    )["safety_metadata"]

    expected = {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "jd_intelligence_only": True,
        "planning_only": True,
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
    assert safety == expected


def test_no_decision_or_application_influence_is_allowed():
    plan = build_live_jd_intelligence_expansion_plan(enabled=True)
    forbidden = plan["forbidden_mutation_and_application_paths"]

    assert plan["mutation_authorized"] is False
    assert plan["mutation_authorized_agent_count"] == 0
    assert all(value is False for value in forbidden.values())


def test_plan_does_not_execute_or_construct_provider_runtime():
    source = (
        ROOT / "src/agents/jd_live_intelligence_expansion_plan.py"
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
    ):
        assert marker not in source

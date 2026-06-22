from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_workflow_readiness import (
    ORDERED_CORE_AGENT_NAMES,
    build_three_core_agent_workflow_readiness,
)


ROOT = Path(__file__).resolve().parents[1]


def _descriptors() -> tuple[dict, dict, dict]:
    return (
        {
            "agent_name": "relevance_prefilter_agent",
            "agent_version": "prefilter-wrapper-v1",
            "status": "completed",
        },
        {
            "agent_name": "jd_intelligence_agent",
            "agent_version": "jd-intelligence-wrapper-v1",
            "status": "completed",
        },
        {
            "agent_name": "final_application_scoring_agent",
            "agent_version": "final-application-scoring-wrapper-v1",
            "status": "completed",
        },
    )


def _preflight() -> dict:
    return {
        "runtime_preflight_status": (
            "runtime_preflight_ready_for_review_no_runtime"
        ),
        "runtime_preflight_only": True,
        "canary_execution_authorized": False,
        "adapter_invocation_authorized": False,
        "execution_authorized": False,
        "runtime_authorized": False,
        "mutation_authorized": False,
    }


def _ready(context: dict | None = None) -> dict:
    prefilter, jd, scoring = _descriptors()
    return build_three_core_agent_workflow_readiness(
        enabled=True,
        relevance_prefilter_descriptor=prefilter,
        jd_intelligence_descriptor=jd,
        final_application_scoring_descriptor=scoring,
        phase16b_runtime_preflight=_preflight(),
        workflow_readiness_context=context,
    )


def test_readiness_is_default_off_read_only_and_not_connected():
    readiness = build_three_core_agent_workflow_readiness()

    assert readiness["three_core_workflow_readiness_enabled"] is False
    assert readiness["readiness_status"] == (
        "three_core_workflow_readiness_skipped_default_off"
    )
    assert readiness["default_off"] is True
    assert readiness["read_only"] is True
    assert readiness["shadow_only"] is True
    assert readiness["advisory_only"] is True
    assert readiness["workflow_readiness_only"] is True
    assert readiness["three_core_agent_only"] is True
    assert readiness["pipeline_not_connected"] is True
    assert readiness["next_safe_step"] == (
        "enable_three_core_workflow_readiness_only"
    )


def test_complete_readiness_still_authorizes_no_connection_or_mutation():
    readiness = _ready()

    assert readiness["readiness_status"] == (
        "three_core_workflow_readiness_ready_no_pipeline_connection"
    )
    assert readiness["workflow_connection_authorized"] is False
    assert readiness["pipeline_stage_added"] is False
    assert readiness["execution_authorized"] is False
    assert readiness["submission_authorized"] is False
    assert readiness["application_execution_authorized"] is False
    assert readiness["final_scoring_mutation_enabled"] is False
    assert readiness["ranking_mutation_enabled"] is False
    assert readiness["queue_mutation_enabled"] is False
    assert readiness["resume_mutation_enabled"] is False
    assert readiness["mutation_authorized"] is False
    assert readiness["mutation_authorized_agent_count"] == 0
    assert readiness["next_safe_step"] == (
        "review_three_core_workflow_readiness_before_shadow_connection"
    )


def test_inputs_are_summarized_separately_and_not_mutated():
    descriptors = _descriptors()
    preflight = _preflight()
    context = {"review": {"owner": "operator"}}
    before = deepcopy((descriptors, preflight, context))
    readiness = build_three_core_agent_workflow_readiness(
        enabled=True,
        relevance_prefilter_descriptor=descriptors[0],
        jd_intelligence_descriptor=descriptors[1],
        final_application_scoring_descriptor=descriptors[2],
        phase16b_runtime_preflight=preflight,
        workflow_readiness_context=context,
    )

    summaries = readiness["core_agent_summaries"]
    for index, name in enumerate(ORDERED_CORE_AGENT_NAMES):
        assert summaries[name]["source_descriptor"] == before[0][index]
        assert summaries[name]["canonical_agent_name"] == name
    assert readiness["phase16b_runtime_preflight_summary"][
        "source_preflight"
    ] == before[1]
    assert readiness["three_core_workflow_readiness"]["scope"] == (
        "three_core_agent_workflow_readiness"
    )
    assert readiness["workflow_readiness_context"] == before[2]
    assert (descriptors, preflight, context) == before


def test_checks_recognize_complete_three_core_agent_shape():
    readiness = _ready({"review": "phase16c"})
    checks = readiness["three_core_workflow_readiness"][
        "readiness_checks"
    ]

    for key in (
        "relevance_prefilter_supplied",
        "jd_intelligence_supplied",
        "final_application_scoring_supplied",
        "phase16b_preflight_supplied",
        "ordered_core_agent_names_match",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "workflow_connection_not_authorized",
        "pipeline_stage_not_added",
        "mutation_not_authorized",
        "scoring_mutation_blocked",
        "ranking_mutation_blocked",
        "queue_mutation_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "provider_runtime_not_required_for_prefilter",
        "provider_runtime_not_invoked_by_readiness",
        "runtime_preflight_keeps_canary_execution_blocked",
        "runtime_preflight_keeps_adapter_invocation_blocked",
        "workflow_readiness_context_supplied",
    ):
        assert checks[key] is True
    assert tuple(readiness["ordered_core_agent_names"]) == (
        ORDERED_CORE_AGENT_NAMES
    )


def test_incomplete_inputs_produce_incomplete_status():
    readiness = build_three_core_agent_workflow_readiness(
        enabled=True,
        relevance_prefilter_descriptor=_descriptors()[0],
    )

    assert readiness["readiness_status"] == (
        "three_core_workflow_readiness_incomplete"
    )
    assert readiness["workflow_connection_authorized"] is False
    assert readiness["next_safe_step"] == (
        "complete_three_core_workflow_readiness_inputs"
    )


def test_forbidden_mutation_and_application_paths_are_all_false():
    readiness = build_three_core_agent_workflow_readiness(enabled=True)

    assert all(
        value is False
        for value in readiness[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase16c_contract_exactly():
    safety = build_three_core_agent_workflow_readiness(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "workflow_readiness_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
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
        ROOT / "src/agents/three_core_agent_workflow_readiness.py"
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

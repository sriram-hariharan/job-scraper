from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_pipeline_connection_plan import (
    ORDERED_CORE_AGENT_NAMES,
    build_three_core_agent_shadow_pipeline_connection_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def _readback() -> dict:
    return {
        "readback_status": "three_core_shadow_dry_run_readback_ready",
        "dry_run_readback_only": True,
        "workflow_connection_authorized": False,
        "dry_run_execution_authorized": False,
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "mutation_authorized": False,
    }


def _connections() -> tuple[dict, dict, dict]:
    return (
        {
            "agent_name": "relevance_prefilter",
            "source_stage": "job_collection",
            "target_stage": "relevance_prefilter_shadow",
            "shadow_only": True,
        },
        {
            "agent_name": "jd_intelligence",
            "source_stage": "relevance_prefilter_shadow",
            "target_stage": "jd_intelligence_shadow",
            "shadow_only": True,
        },
        {
            "agent_name": "final_application_scoring",
            "source_stage": "jd_intelligence_shadow",
            "target_stage": "final_application_scoring_shadow",
            "shadow_only": True,
        },
    )


def _ready_plan(context: dict | None = None) -> dict:
    connections = _connections()
    return build_three_core_agent_shadow_pipeline_connection_plan(
        enabled=True,
        dry_run_readback=_readback(),
        pipeline_entrypoint_descriptor={
            "entrypoint_name": "future_guarded_shadow_entrypoint",
            "stage_name": "post_collection_shadow_preview",
            "shadow_only": True,
        },
        prefilter_connection_descriptor=connections[0],
        jd_intelligence_connection_descriptor=connections[1],
        final_scoring_connection_descriptor=connections[2],
        connection_plan_context=context,
    )


def test_plan_is_default_off_read_only_and_not_connected():
    plan = build_three_core_agent_shadow_pipeline_connection_plan()

    assert plan[
        "three_core_shadow_pipeline_connection_plan_enabled"
    ] is False
    assert plan["connection_plan_status"] == (
        "three_core_shadow_pipeline_connection_plan_skipped_default_off"
    )
    assert plan["default_off"] is True
    assert plan["read_only"] is True
    assert plan["shadow_only"] is True
    assert plan["advisory_only"] is True
    assert plan["connection_plan_only"] is True
    assert plan["pipeline_connection_plan_only"] is True
    assert plan["three_core_agent_only"] is True
    assert plan["pipeline_not_connected"] is True
    assert plan["pipeline_stage_not_added"] is True
    assert plan["next_safe_step"] == (
        "enable_three_core_shadow_pipeline_connection_plan_only"
    )


def test_complete_plan_authorizes_no_connection_or_execution():
    plan = _ready_plan()

    assert plan["connection_plan_status"] == (
        "three_core_shadow_pipeline_connection_plan_"
        "ready_no_pipeline_change"
    )
    assert plan["workflow_connection_authorized"] is False
    assert plan["pipeline_connection_authorized"] is False
    assert plan["pipeline_stage_added"] is False
    assert plan["real_agent_execution_authorized"] is False
    assert plan["dry_run_execution_authorized"] is False
    assert plan["execution_authorized"] is False
    assert plan["submission_authorized"] is False
    assert plan["application_execution_authorized"] is False
    assert plan["final_scoring_mutation_enabled"] is False
    assert plan["ranking_mutation_enabled"] is False
    assert plan["queue_mutation_enabled"] is False
    assert plan["resume_mutation_enabled"] is False
    assert plan["mutation_authorized"] is False
    assert plan["mutation_authorized_agent_count"] == 0
    assert plan["next_safe_step"] == (
        "review_three_core_shadow_connection_plan_"
        "before_guarded_pipeline_integration"
    )


def test_inputs_are_summarized_separately_and_not_mutated():
    readback = _readback()
    entrypoint = {
        "entrypoint_name": "future_guarded_shadow_entrypoint",
        "stage_name": "post_collection_shadow_preview",
        "shadow_only": True,
    }
    connections = _connections()
    context = {"review": {"owner": "operator"}}
    before = deepcopy((readback, entrypoint, connections, context))
    plan = build_three_core_agent_shadow_pipeline_connection_plan(
        enabled=True,
        dry_run_readback=readback,
        pipeline_entrypoint_descriptor=entrypoint,
        prefilter_connection_descriptor=connections[0],
        jd_intelligence_connection_descriptor=connections[1],
        final_scoring_connection_descriptor=connections[2],
        connection_plan_context=context,
    )

    assert plan["dry_run_readback_summary"]["source_readback"] == (
        before[0]
    )
    assert plan["pipeline_entrypoint_summary"][
        "source_entrypoint_descriptor"
    ] == before[1]
    summaries = plan["planned_core_agent_connections"]
    for index, name in enumerate(ORDERED_CORE_AGENT_NAMES):
        assert summaries[name]["source_descriptor"] == before[2][index]
    assert plan["three_core_shadow_pipeline_connection_plan"][
        "scope"
    ] == "three_core_agent_shadow_pipeline_connection_plan"
    assert plan["connection_plan_context"] == before[3]
    assert (readback, entrypoint, connections, context) == before


def test_checks_recognize_complete_shadow_connection_plan():
    plan = _ready_plan({"review": "phase16g"})
    checks = plan["three_core_shadow_pipeline_connection_plan"][
        "connection_plan_checks"
    ]

    for key in (
        "dry_run_readback_supplied",
        "dry_run_readback_ready",
        "pipeline_entrypoint_descriptor_supplied",
        "prefilter_connection_descriptor_supplied",
        "jd_intelligence_connection_descriptor_supplied",
        "final_scoring_connection_descriptor_supplied",
        "ordered_core_agent_names_match",
        "planned_connections_are_shadow_only",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "workflow_connection_not_authorized",
        "pipeline_connection_not_authorized",
        "pipeline_stage_not_added",
        "real_agent_execution_not_authorized",
        "dry_run_execution_not_authorized",
        "mutation_not_authorized",
        "scoring_mutation_blocked",
        "ranking_mutation_blocked",
        "queue_mutation_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "connection_plan_context_supplied",
    ):
        assert checks[key] is True
    assert tuple(plan["ordered_core_agent_names"]) == (
        ORDERED_CORE_AGENT_NAMES
    )
    assert all(
        item["shadow_only"]
        for item in plan["ordered_planned_connections"]
    )


def test_incomplete_inputs_produce_incomplete_status():
    plan = build_three_core_agent_shadow_pipeline_connection_plan(
        enabled=True,
        dry_run_readback=_readback(),
    )

    assert plan["connection_plan_status"] == (
        "three_core_shadow_pipeline_connection_plan_incomplete"
    )
    assert plan["pipeline_connection_authorized"] is False
    assert plan["next_safe_step"] == (
        "complete_three_core_shadow_pipeline_connection_plan_inputs"
    )


def test_forbidden_mutation_and_application_paths_are_all_false():
    plan = build_three_core_agent_shadow_pipeline_connection_plan(
        enabled=True
    )

    assert all(
        value is False
        for value in plan[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase16g_contract_exactly():
    safety = build_three_core_agent_shadow_pipeline_connection_plan(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "connection_plan_only": True,
        "pipeline_connection_plan_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_not_added": True,
        "real_agent_execution_not_authorized": True,
        "dry_run_execution_not_authorized": True,
        "provider_runtime_not_invoked": True,
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


def test_source_has_no_agent_provider_network_database_or_file_wiring():
    source = (
        ROOT
        / "src/agents/three_core_agent_shadow_pipeline_connection_plan.py"
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
        "filter_jobs(",
        "analyze_job_description(",
        "score_applications(",
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

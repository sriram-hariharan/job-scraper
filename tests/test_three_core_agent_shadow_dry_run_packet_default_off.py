from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_dry_run_packet import (
    ORDERED_CORE_AGENT_NAMES,
    build_three_core_agent_shadow_dry_run_packet,
)


ROOT = Path(__file__).resolve().parents[1]


def _contract() -> dict:
    return {
        "contract_status": (
            "three_core_shadow_workflow_contract_"
            "ready_no_pipeline_connection"
        ),
        "shadow_workflow_contract_only": True,
        "workflow_connection_authorized": False,
        "real_agent_execution_authorized": False,
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "mutation_authorized": False,
    }


def _traces() -> tuple[dict, dict, dict]:
    return (
        {
            "agent_name": "relevance_prefilter_agent",
            "agent_version": "prefilter-wrapper-v1",
            "status": "completed",
            "validation_json": {"is_valid": True},
        },
        {
            "agent_name": "jd_intelligence_agent",
            "agent_version": "jd-intelligence-wrapper-v1",
            "status": "completed",
            "validation_json": {"is_valid": True},
        },
        {
            "agent_name": "final_application_scoring_agent",
            "agent_version": "final-application-scoring-wrapper-v1",
            "status": "completed",
            "validation_json": {"is_valid": True},
        },
    )


def _ready_packet(context: dict | None = None) -> dict:
    traces = _traces()
    return build_three_core_agent_shadow_dry_run_packet(
        enabled=True,
        shadow_workflow_contract=_contract(),
        job_context_descriptor={
            "job_id": "job-1",
            "run_id": "run-1",
        },
        prefilter_trace_descriptor=traces[0],
        jd_intelligence_trace_descriptor=traces[1],
        final_scoring_trace_descriptor=traces[2],
        dry_run_context=context,
    )


def test_packet_is_default_off_read_only_and_not_executable():
    packet = build_three_core_agent_shadow_dry_run_packet()

    assert packet["three_core_shadow_dry_run_packet_enabled"] is False
    assert packet["packet_status"] == (
        "three_core_shadow_dry_run_packet_skipped_default_off"
    )
    assert packet["default_off"] is True
    assert packet["read_only"] is True
    assert packet["shadow_only"] is True
    assert packet["advisory_only"] is True
    assert packet["dry_run_packet_only"] is True
    assert packet["three_core_agent_only"] is True
    assert packet["pipeline_not_connected"] is True
    assert packet["provider_runtime_not_invoked"] is True
    assert packet["next_safe_step"] == (
        "enable_three_core_shadow_dry_run_packet_only"
    )


def test_complete_packet_authorizes_no_dry_run_or_mutation():
    packet = _ready_packet()

    assert packet["packet_status"] == (
        "three_core_shadow_dry_run_packet_ready_no_execution"
    )
    assert packet["workflow_connection_authorized"] is False
    assert packet["pipeline_stage_added"] is False
    assert packet["real_agent_execution_authorized"] is False
    assert packet["dry_run_execution_authorized"] is False
    assert packet["execution_authorized"] is False
    assert packet["submission_authorized"] is False
    assert packet["application_execution_authorized"] is False
    assert packet["final_scoring_mutation_enabled"] is False
    assert packet["ranking_mutation_enabled"] is False
    assert packet["queue_mutation_enabled"] is False
    assert packet["resume_mutation_enabled"] is False
    assert packet["mutation_authorized"] is False
    assert packet["mutation_authorized_agent_count"] == 0
    assert packet["next_safe_step"] == (
        "review_three_core_shadow_dry_run_packet_before_readback"
    )


def test_inputs_are_summarized_separately_and_not_mutated():
    contract = _contract()
    job = {"job_id": "job-1", "run_id": "run-1"}
    traces = _traces()
    context = {"review": {"owner": "operator"}}
    before = deepcopy((contract, job, traces, context))
    packet = build_three_core_agent_shadow_dry_run_packet(
        enabled=True,
        shadow_workflow_contract=contract,
        job_context_descriptor=job,
        prefilter_trace_descriptor=traces[0],
        jd_intelligence_trace_descriptor=traces[1],
        final_scoring_trace_descriptor=traces[2],
        dry_run_context=context,
    )

    assert packet["shadow_workflow_contract_summary"][
        "source_contract"
    ] == before[0]
    assert packet["job_context_summary"]["source_job_context"] == (
        before[1]
    )
    summaries = packet["core_agent_trace_summaries"]
    for index, name in enumerate(ORDERED_CORE_AGENT_NAMES):
        assert summaries[name]["source_trace_descriptor"] == (
            before[2][index]
        )
    assert packet["three_core_shadow_dry_run_packet"]["scope"] == (
        "three_core_agent_shadow_dry_run_packet"
    )
    assert packet["dry_run_context"] == before[3]
    assert (contract, job, traces, context) == before


def test_checks_recognize_complete_shadow_packet_shape():
    packet = _ready_packet({"review": "phase16e"})
    checks = packet["three_core_shadow_dry_run_packet"][
        "packet_checks"
    ]

    for key in (
        "shadow_workflow_contract_supplied",
        "shadow_workflow_contract_ready",
        "job_context_descriptor_supplied",
        "prefilter_trace_descriptor_supplied",
        "jd_intelligence_trace_descriptor_supplied",
        "final_scoring_trace_descriptor_supplied",
        "ordered_core_agent_names_match",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "workflow_connection_not_authorized",
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
        "dry_run_context_supplied",
    ):
        assert checks[key] is True
    assert tuple(packet["ordered_core_agent_names"]) == (
        ORDERED_CORE_AGENT_NAMES
    )
    assert [
        item["agent_name"]
        for item in packet["ordered_core_agent_trace_descriptors"]
    ] == list(ORDERED_CORE_AGENT_NAMES)


def test_incomplete_inputs_produce_incomplete_status():
    packet = build_three_core_agent_shadow_dry_run_packet(
        enabled=True,
        shadow_workflow_contract=_contract(),
    )

    assert packet["packet_status"] == (
        "three_core_shadow_dry_run_packet_incomplete"
    )
    assert packet["dry_run_execution_authorized"] is False
    assert packet["next_safe_step"] == (
        "complete_three_core_shadow_dry_run_packet_inputs"
    )


def test_forbidden_mutation_and_application_paths_are_all_false():
    packet = build_three_core_agent_shadow_dry_run_packet(
        enabled=True
    )

    assert all(
        value is False
        for value in packet[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase16e_contract_exactly():
    safety = build_three_core_agent_shadow_dry_run_packet(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "dry_run_packet_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "real_agent_execution_not_authorized": True,
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
        ROOT / "src/agents/three_core_agent_shadow_dry_run_packet.py"
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

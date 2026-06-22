from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_dry_run_readback import (
    ORDERED_CORE_AGENT_NAMES,
    build_three_core_agent_shadow_dry_run_readback,
)


ROOT = Path(__file__).resolve().parents[1]


def _packet() -> dict:
    rows = []
    for agent_name, source_name, version in (
        (
            "relevance_prefilter",
            "relevance_prefilter_agent",
            "prefilter-wrapper-v1",
        ),
        (
            "jd_intelligence",
            "jd_intelligence_agent",
            "jd-intelligence-wrapper-v1",
        ),
        (
            "final_application_scoring",
            "final_application_scoring_agent",
            "final-application-scoring-wrapper-v1",
        ),
    ):
        descriptor = {
            "agent_name": source_name,
            "agent_version": version,
            "status": "completed",
            "validation_json": {"is_valid": True},
        }
        rows.append(
            {
                "descriptor_supplied": True,
                "agent_name": agent_name,
                "source_agent_name": source_name,
                "agent_version": version,
                "status": "completed",
                "validation_status": "valid",
                "source_trace_descriptor": descriptor,
            }
        )
    return {
        "packet_status": (
            "three_core_shadow_dry_run_packet_ready_no_execution"
        ),
        "dry_run_packet_only": True,
        "dry_run_execution_authorized": False,
        "workflow_connection_authorized": False,
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "ordered_core_agent_trace_descriptors": rows,
        "mutation_authorized": False,
    }


def _ready_readback(context: dict | None = None) -> dict:
    return build_three_core_agent_shadow_dry_run_readback(
        enabled=True,
        dry_run_packet=_packet(),
        readback_context=context,
    )


def test_readback_is_default_off_read_only_and_not_executable():
    readback = build_three_core_agent_shadow_dry_run_readback()

    assert readback[
        "three_core_shadow_dry_run_readback_enabled"
    ] is False
    assert readback["readback_status"] == (
        "three_core_shadow_dry_run_readback_skipped_default_off"
    )
    assert readback["default_off"] is True
    assert readback["read_only"] is True
    assert readback["shadow_only"] is True
    assert readback["advisory_only"] is True
    assert readback["readback_only"] is True
    assert readback["dry_run_readback_only"] is True
    assert readback["three_core_agent_only"] is True
    assert readback["pipeline_not_connected"] is True
    assert readback["provider_runtime_not_invoked"] is True
    assert readback["next_safe_step"] == (
        "enable_three_core_shadow_dry_run_readback_only"
    )


def test_complete_readback_authorizes_no_execution_or_mutation():
    readback = _ready_readback()

    assert readback["readback_status"] == (
        "three_core_shadow_dry_run_readback_ready"
    )
    assert readback["workflow_connection_authorized"] is False
    assert readback["pipeline_stage_added"] is False
    assert readback["real_agent_execution_authorized"] is False
    assert readback["dry_run_execution_authorized"] is False
    assert readback["execution_authorized"] is False
    assert readback["submission_authorized"] is False
    assert readback["application_execution_authorized"] is False
    assert readback["final_scoring_mutation_enabled"] is False
    assert readback["ranking_mutation_enabled"] is False
    assert readback["queue_mutation_enabled"] is False
    assert readback["resume_mutation_enabled"] is False
    assert readback["mutation_authorized"] is False
    assert readback["mutation_authorized_agent_count"] == 0
    assert readback["next_safe_step"] == (
        "review_three_core_shadow_dry_run_readback_"
        "before_pipeline_connection_plan"
    )


def test_input_is_summarized_separately_and_not_mutated():
    packet = _packet()
    context = {"readback": {"owner": "operator"}}
    before = deepcopy((packet, context))
    readback = build_three_core_agent_shadow_dry_run_readback(
        enabled=True,
        dry_run_packet=packet,
        readback_context=context,
    )

    assert readback["dry_run_packet_summary"]["source_packet"] == (
        before[0]
    )
    assert readback["three_core_shadow_dry_run_readback"]["scope"] == (
        "three_core_agent_shadow_dry_run_readback"
    )
    assert readback["readback_context"] == before[1]
    assert (packet, context) == before


def test_checks_recognize_complete_three_row_readback_shape():
    readback = _ready_readback({"review": "phase16f"})
    checks = readback["three_core_shadow_dry_run_readback"][
        "readback_checks"
    ]

    for key in (
        "dry_run_packet_supplied",
        "dry_run_packet_ready",
        "ordered_core_agent_names_match",
        "ordered_trace_descriptor_count_is_three",
        "prefilter_trace_readback_available",
        "jd_intelligence_trace_readback_available",
        "final_scoring_trace_readback_available",
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
        "readback_context_supplied",
    ):
        assert checks[key] is True
    rows = readback["agent_trace_readback_rows"]
    assert len(rows) == 3
    assert tuple(row["agent_name"] for row in rows) == (
        ORDERED_CORE_AGENT_NAMES
    )
    assert all(row["descriptor_available"] for row in rows)


def test_incomplete_inputs_produce_incomplete_status():
    readback = build_three_core_agent_shadow_dry_run_readback(
        enabled=True,
        dry_run_packet={
            "packet_status": (
                "three_core_shadow_dry_run_packet_incomplete"
            )
        },
    )

    assert readback["readback_status"] == (
        "three_core_shadow_dry_run_readback_incomplete"
    )
    assert readback["dry_run_execution_authorized"] is False
    assert readback["next_safe_step"] == (
        "complete_three_core_shadow_dry_run_readback_inputs"
    )


def test_forbidden_mutation_and_application_paths_are_all_false():
    readback = build_three_core_agent_shadow_dry_run_readback(
        enabled=True
    )

    assert all(
        value is False
        for value in readback[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase16f_contract_exactly():
    safety = build_three_core_agent_shadow_dry_run_readback(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "readback_only": True,
        "dry_run_readback_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
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
        ROOT / "src/agents/three_core_agent_shadow_dry_run_readback.py"
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

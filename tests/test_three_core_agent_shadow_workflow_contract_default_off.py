from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_workflow_contract import (
    ORDERED_CORE_AGENT_NAMES,
    build_three_core_agent_shadow_workflow_contract,
)


ROOT = Path(__file__).resolve().parents[1]


def _readiness() -> dict:
    return {
        "readiness_status": (
            "three_core_workflow_readiness_"
            "ready_no_pipeline_connection"
        ),
        "workflow_readiness_only": True,
        "workflow_connection_authorized": False,
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "mutation_authorized": False,
    }


def _outputs() -> tuple[dict, dict, dict]:
    return (
        {
            "agent_name": "relevance_prefilter",
            "agent_version": "prefilter-wrapper-v1",
            "status": "described",
        },
        {
            "agent_name": "jd_intelligence",
            "agent_version": "jd-intelligence-wrapper-v1",
            "status": "described",
        },
        {
            "agent_name": "final_application_scoring",
            "agent_version": "final-application-scoring-wrapper-v1",
            "status": "described",
        },
    )


def _ready_contract(context: dict | None = None) -> dict:
    outputs = _outputs()
    return build_three_core_agent_shadow_workflow_contract(
        enabled=True,
        three_core_readiness=_readiness(),
        job_context_descriptor={
            "job_id": "job-1",
            "run_id": "run-1",
        },
        prefilter_output_descriptor=outputs[0],
        jd_intelligence_output_descriptor=outputs[1],
        final_scoring_output_descriptor=outputs[2],
        shadow_workflow_context=context,
    )


def test_contract_is_default_off_read_only_and_not_connected():
    contract = build_three_core_agent_shadow_workflow_contract()

    assert contract[
        "three_core_shadow_workflow_contract_enabled"
    ] is False
    assert contract["contract_status"] == (
        "three_core_shadow_workflow_contract_skipped_default_off"
    )
    assert contract["default_off"] is True
    assert contract["read_only"] is True
    assert contract["shadow_only"] is True
    assert contract["advisory_only"] is True
    assert contract["contract_only"] is True
    assert contract["shadow_workflow_contract_only"] is True
    assert contract["three_core_agent_only"] is True
    assert contract["pipeline_not_connected"] is True
    assert contract["next_safe_step"] == (
        "enable_three_core_shadow_workflow_contract_only"
    )


def test_complete_contract_authorizes_no_execution_or_mutation():
    contract = _ready_contract()

    assert contract["contract_status"] == (
        "three_core_shadow_workflow_contract_"
        "ready_no_pipeline_connection"
    )
    assert contract["workflow_connection_authorized"] is False
    assert contract["pipeline_stage_added"] is False
    assert contract["real_agent_execution_authorized"] is False
    assert contract["execution_authorized"] is False
    assert contract["submission_authorized"] is False
    assert contract["application_execution_authorized"] is False
    assert contract["final_scoring_mutation_enabled"] is False
    assert contract["ranking_mutation_enabled"] is False
    assert contract["queue_mutation_enabled"] is False
    assert contract["resume_mutation_enabled"] is False
    assert contract["mutation_authorized"] is False
    assert contract["mutation_authorized_agent_count"] == 0
    assert contract["next_safe_step"] == (
        "review_three_core_shadow_contract_before_dry_run"
    )


def test_inputs_are_summarized_separately_and_not_mutated():
    readiness = _readiness()
    job = {"job_id": "job-1", "run_id": "run-1"}
    outputs = _outputs()
    context = {"review": {"owner": "operator"}}
    before = deepcopy((readiness, job, outputs, context))
    contract = build_three_core_agent_shadow_workflow_contract(
        enabled=True,
        three_core_readiness=readiness,
        job_context_descriptor=job,
        prefilter_output_descriptor=outputs[0],
        jd_intelligence_output_descriptor=outputs[1],
        final_scoring_output_descriptor=outputs[2],
        shadow_workflow_context=context,
    )

    assert contract["three_core_readiness_summary"][
        "source_readiness"
    ] == before[0]
    assert contract["job_context_summary"][
        "source_job_context"
    ] == before[1]
    summaries = contract["planned_core_agent_outputs"]
    for index, name in enumerate(ORDERED_CORE_AGENT_NAMES):
        assert summaries[name]["source_descriptor"] == before[2][index]
    assert contract["three_core_shadow_workflow_contract"]["scope"] == (
        "three_core_agent_shadow_workflow_contract"
    )
    assert contract["shadow_workflow_context"] == before[3]
    assert (readiness, job, outputs, context) == before


def test_checks_recognize_complete_shadow_contract_shape():
    contract = _ready_contract({"review": "phase16d"})
    checks = contract["three_core_shadow_workflow_contract"][
        "contract_checks"
    ]

    for key in (
        "three_core_readiness_supplied",
        "three_core_readiness_ready",
        "job_context_descriptor_supplied",
        "prefilter_output_descriptor_supplied",
        "jd_intelligence_output_descriptor_supplied",
        "final_scoring_output_descriptor_supplied",
        "ordered_core_agent_names_match",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "workflow_connection_not_authorized",
        "pipeline_stage_not_added",
        "real_agent_execution_not_authorized",
        "mutation_not_authorized",
        "scoring_mutation_blocked",
        "ranking_mutation_blocked",
        "queue_mutation_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "shadow_workflow_context_supplied",
    ):
        assert checks[key] is True
    assert tuple(contract["ordered_core_agent_names"]) == (
        ORDERED_CORE_AGENT_NAMES
    )
    assert [
        item["agent_name"]
        for item in contract["ordered_shadow_output_descriptors"]
    ] == list(ORDERED_CORE_AGENT_NAMES)


def test_incomplete_inputs_produce_incomplete_status():
    contract = build_three_core_agent_shadow_workflow_contract(
        enabled=True,
        three_core_readiness=_readiness(),
    )

    assert contract["contract_status"] == (
        "three_core_shadow_workflow_contract_incomplete"
    )
    assert contract["workflow_connection_authorized"] is False
    assert contract["next_safe_step"] == (
        "complete_three_core_shadow_workflow_contract_inputs"
    )


def test_forbidden_mutation_and_application_paths_are_all_false():
    contract = build_three_core_agent_shadow_workflow_contract(
        enabled=True
    )

    assert all(
        value is False
        for value in contract[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase16d_contract_exactly():
    safety = build_three_core_agent_shadow_workflow_contract(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "contract_only": True,
        "shadow_workflow_contract_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "real_agent_execution_not_authorized": True,
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
        / "src/agents/three_core_agent_shadow_workflow_contract.py"
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

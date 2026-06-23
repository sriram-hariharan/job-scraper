from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_pipeline_connection_plan import (
    build_three_core_agent_shadow_pipeline_connection_plan,
)
from src.agents.three_core_agent_shadow_pipeline_hook import (
    ORDERED_CORE_AGENT_NAMES,
    run_three_core_agent_shadow_pipeline_hook,
)


ROOT = Path(__file__).resolve().parents[1]


def _ready_plan() -> dict:
    names = list(ORDERED_CORE_AGENT_NAMES)
    connections = [
        {
            "agent_name": names[0],
            "source_stage": "job_collection",
            "target_stage": "relevance_prefilter_shadow",
            "shadow_only": True,
        },
        {
            "agent_name": names[1],
            "source_stage": "relevance_prefilter_shadow",
            "target_stage": "jd_intelligence_shadow",
            "shadow_only": True,
        },
        {
            "agent_name": names[2],
            "source_stage": "jd_intelligence_shadow",
            "target_stage": "final_application_scoring_shadow",
            "shadow_only": True,
        },
    ]
    return build_three_core_agent_shadow_pipeline_connection_plan(
        enabled=True,
        dry_run_readback={
            "readback_status": "three_core_shadow_dry_run_readback_ready",
            "dry_run_readback_only": True,
            "workflow_connection_authorized": False,
            "dry_run_execution_authorized": False,
            "ordered_core_agent_names": names,
            "mutation_authorized": False,
        },
        pipeline_entrypoint_descriptor={
            "entrypoint_name": "future_guarded_shadow_entrypoint",
            "stage_name": "post_collection_shadow_preview",
            "shadow_only": True,
        },
        prefilter_connection_descriptor=connections[0],
        jd_intelligence_connection_descriptor=connections[1],
        final_scoring_connection_descriptor=connections[2],
    )


def test_default_off_read_only_hook_does_not_invoke_callables():
    calls = []

    def supplied(request):
        calls.append(request)
        return {"unexpected": True}

    payload = run_three_core_agent_shadow_pipeline_hook(
        connection_plan=_ready_plan(),
        job_context={"job_id": "job-17a"},
        relevance_prefilter_callable=supplied,
        jd_intelligence_callable=supplied,
        final_application_scoring_callable=supplied,
    )

    assert calls == []
    assert payload["three_core_shadow_pipeline_hook_enabled"] is False
    assert payload["hook_status"] == (
        "three_core_shadow_pipeline_hook_skipped_default_off"
    )
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    assert payload["shadow_pipeline_hook_only"] is True
    assert payload["three_core_agent_only"] is True
    assert payload["pipeline_not_connected"] is True
    assert payload["pipeline_stage_not_added"] is True
    assert payload["ordered_shadow_results"] == []
    assert payload["next_safe_step"] == (
        "enable_three_core_shadow_pipeline_hook_only"
    )


def test_enabled_incomplete_hook_invokes_no_callables():
    calls = []

    def supplied(request):
        calls.append(request)
        return {}

    payload = run_three_core_agent_shadow_pipeline_hook(
        enabled=True,
        job_context={"job_id": "job-17a"},
        relevance_prefilter_callable=supplied,
        jd_intelligence_callable=supplied,
        final_application_scoring_callable=supplied,
    )

    assert calls == []
    assert payload["hook_status"] == (
        "three_core_shadow_pipeline_hook_blocked"
    )
    assert payload["next_safe_step"] == (
        "complete_three_core_shadow_pipeline_hook_inputs"
    )


def test_complete_hook_invokes_callables_in_order_with_previous_outputs():
    calls = []

    def prefilter(request):
        calls.append(deepcopy(request))
        return {"kept": True}

    def jd(request):
        calls.append(deepcopy(request))
        return {"skills": ["python"]}

    def scoring(request):
        calls.append(deepcopy(request))
        return {"score": 91}

    payload = run_three_core_agent_shadow_pipeline_hook(
        enabled=True,
        connection_plan=_ready_plan(),
        job_context={"job_id": "job-17a", "title": "AI Engineer"},
        relevance_prefilter_callable=prefilter,
        jd_intelligence_callable=jd,
        final_application_scoring_callable=scoring,
        hook_context={"phase": "17a"},
    )

    assert [call["agent_name"] for call in calls] == list(
        ORDERED_CORE_AGENT_NAMES
    )
    assert calls[0]["previous_outputs"] == {}
    assert calls[1]["previous_outputs"] == {
        "relevance_prefilter": {"kept": True}
    }
    assert calls[2]["previous_outputs"] == {
        "relevance_prefilter": {"kept": True},
        "jd_intelligence": {"skills": ["python"]},
    }
    for call in calls:
        assert call["ordered_core_agent_names"] == list(
            ORDERED_CORE_AGENT_NAMES
        )
        assert call["shadow_only"] is True
        assert call["mutation_authorized"] is False
        assert call["workflow_connection_authorized"] is False
        assert call["pipeline_stage_added"] is False
    assert payload["hook_status"] == (
        "three_core_shadow_pipeline_hook_completed_shadow_only"
    )
    assert [
        result["agent_name"]
        for result in payload["ordered_shadow_results"]
    ] == list(ORDERED_CORE_AGENT_NAMES)
    assert payload["shadow_result_count"] == 3
    assert payload["next_safe_step"] == (
        "review_three_core_shadow_pipeline_hook_before_pipeline_wiring"
    )


def test_callable_failure_fails_closed_and_stops_later_callables():
    calls = []

    def prefilter(request):
        calls.append(request["agent_name"])
        return {"kept": True}

    def jd(request):
        calls.append(request["agent_name"])
        raise ValueError("shadow evaluation failed")

    def scoring(request):
        calls.append(request["agent_name"])
        return {"unexpected": True}

    payload = run_three_core_agent_shadow_pipeline_hook(
        enabled=True,
        connection_plan=_ready_plan(),
        job_context={"job_id": "job-17a"},
        relevance_prefilter_callable=prefilter,
        jd_intelligence_callable=jd,
        final_application_scoring_callable=scoring,
    )

    assert calls == ["relevance_prefilter", "jd_intelligence"]
    assert payload["hook_status"] == (
        "three_core_shadow_pipeline_hook_failed_closed"
    )
    assert payload["shadow_result_count"] == 1
    assert payload["failure"] == {
        "failed_agent_name": "jd_intelligence",
        "error_type": "ValueError",
        "error_message": "shadow evaluation failed",
        "failed_closed": True,
    }
    assert payload["mutation_authorized"] is False
    assert payload["pipeline_connection_authorized"] is False
    assert payload["next_safe_step"] == (
        "fix_three_core_shadow_pipeline_hook_error_before_retry"
    )


def test_inputs_are_summarized_separately_and_not_mutated():
    plan = _ready_plan()
    job = {"job_id": "job-17a", "nested": {"skills": ["python"]}}
    context = {"review": {"owner": "operator"}}
    before = deepcopy((plan, job, context))

    def mutating_callable(request):
        request["job_context"]["nested"]["skills"].append("changed")
        return {"request": request}

    payload = run_three_core_agent_shadow_pipeline_hook(
        enabled=True,
        connection_plan=plan,
        job_context=job,
        relevance_prefilter_callable=mutating_callable,
        jd_intelligence_callable=mutating_callable,
        final_application_scoring_callable=mutating_callable,
        hook_context=context,
    )

    assert payload["connection_plan_summary"][
        "source_connection_plan"
    ] == before[0]
    assert payload["job_context_summary"]["source_job_context"] == before[1]
    assert payload["hook_context_summary"]["source_hook_context"] == before[2]
    assert (plan, job, context) == before


def test_hook_checks_recognize_complete_three_core_shadow_shape():
    payload = run_three_core_agent_shadow_pipeline_hook(
        enabled=True,
        connection_plan=_ready_plan(),
        job_context={"job_id": "job-17a"},
        relevance_prefilter_callable=lambda request: {"step": 1},
        jd_intelligence_callable=lambda request: {"step": 2},
        final_application_scoring_callable=lambda request: {"step": 3},
        hook_context={"phase": "17a"},
    )
    checks = payload["three_core_shadow_pipeline_hook"]["hook_checks"]

    for key in (
        "connection_plan_supplied",
        "connection_plan_ready",
        "job_context_supplied",
        "relevance_prefilter_callable_supplied",
        "jd_intelligence_callable_supplied",
        "final_application_scoring_callable_supplied",
        "ordered_core_agent_names_match",
        "planned_connections_are_shadow_only",
        "pipeline_not_connected",
        "pipeline_stage_not_added",
        "workflow_connection_not_authorized",
        "pipeline_connection_not_authorized",
        "mutation_not_authorized",
        "scoring_mutation_blocked",
        "ranking_mutation_blocked",
        "queue_mutation_blocked",
        "resume_mutation_blocked",
        "application_execution_blocked",
        "application_submission_blocked",
        "prefilter_relevance_separation_preserved",
        "jd_intelligence_evaluation_separation_preserved",
        "final_application_scoring_separation_preserved",
        "hook_context_supplied",
    ):
        assert checks[key] is True
    assert tuple(payload["ordered_core_agent_names"]) == (
        ORDERED_CORE_AGENT_NAMES
    )


def test_forbidden_mutation_and_application_paths_are_all_false():
    payload = run_three_core_agent_shadow_pipeline_hook(enabled=True)

    for key in (
        "workflow_connection_authorized",
        "pipeline_connection_authorized",
        "pipeline_stage_added",
        "execution_authorized",
        "submission_authorized",
        "application_execution_authorized",
        "final_scoring_mutation_enabled",
        "ranking_mutation_enabled",
        "queue_mutation_enabled",
        "resume_mutation_enabled",
        "mutation_authorized",
    ):
        assert payload[key] is False
    assert payload["mutation_authorized_agent_count"] == 0
    assert all(
        value is False
        for value in payload[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_safety_metadata_matches_phase17a_contract_exactly():
    safety = run_three_core_agent_shadow_pipeline_hook(
        enabled=True
    )["safety_metadata"]

    assert safety == {
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "shadow_pipeline_hook_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_not_added": True,
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


def test_source_has_no_real_agent_provider_network_database_or_file_wiring():
    source = (
        ROOT / "src/agents/three_core_agent_shadow_pipeline_hook.py"
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

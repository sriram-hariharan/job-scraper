from copy import deepcopy
from pathlib import Path

from src.agents.three_core_agent_shadow_callable_adapters import (
    ORDERED_CORE_AGENT_NAMES,
    build_three_core_agent_shadow_callable_adapters,
)
from src.agents.three_core_agent_shadow_pipeline_connection_plan import (
    build_three_core_agent_shadow_pipeline_connection_plan,
)
from src.agents.three_core_agent_shadow_pipeline_hook import (
    run_three_core_agent_shadow_pipeline_hook,
)


ROOT = Path(__file__).resolve().parents[1]


def _request(
    agent_name: str,
    previous_outputs: dict | None = None,
) -> dict:
    return {
        "agent_name": agent_name,
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "job_context": {
            "job_id": "phase17e-job",
            "job_payload": {
                "title": "Applied AI Engineer",
                "required_skills": ["Python"],
                "preferred_skills": ["SQL"],
                "workflows": ["model monitoring"],
                "nested": {"values": ["original"]},
            },
        },
        "previous_outputs": deepcopy(previous_outputs or {}),
        "shadow_only": True,
        "mutation_authorized": False,
        "workflow_connection_authorized": False,
        "pipeline_stage_added": False,
    }


def _ready_plan() -> dict:
    names = list(ORDERED_CORE_AGENT_NAMES)
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
            "entrypoint_name": "phase17e_test_shadow_entrypoint",
            "stage_name": "post_final_scoring",
            "shadow_only": True,
        },
        prefilter_connection_descriptor={
            "agent_name": names[0],
            "source_stage": "application_priority_scored_jobs",
            "target_stage": "relevance_prefilter_shadow",
            "shadow_only": True,
        },
        jd_intelligence_connection_descriptor={
            "agent_name": names[1],
            "source_stage": "relevance_prefilter_shadow",
            "target_stage": "jd_intelligence_shadow",
            "shadow_only": True,
        },
        final_scoring_connection_descriptor={
            "agent_name": names[2],
            "source_stage": "jd_intelligence_shadow",
            "target_stage": "final_application_scoring_shadow",
            "shadow_only": True,
        },
    )


def test_default_off_returns_no_callables():
    context = {"review": {"owner": "operator"}}
    before = deepcopy(context)

    payload = build_three_core_agent_shadow_callable_adapters(
        adapter_context=context
    )

    assert payload["adapter_status"] == (
        "three_core_shadow_callable_adapters_skipped_default_off"
    )
    assert payload["callable_count"] == 0
    assert payload["callable_map"] == {}
    assert payload["ordered_callable_adapters"] == []
    assert payload["adapter_context"] == before
    assert context == before
    assert payload["next_safe_step"] == (
        "enable_three_core_shadow_callable_adapters_only"
    )


def test_enabled_returns_exactly_three_ordered_callables():
    payload = build_three_core_agent_shadow_callable_adapters(
        enabled=True
    )

    assert payload["adapter_status"] == (
        "three_core_shadow_callable_adapters_ready_shadow_only"
    )
    assert payload["callable_count"] == 3
    assert tuple(payload["ordered_core_agent_names"]) == (
        ORDERED_CORE_AGENT_NAMES
    )
    assert [
        item["agent_name"]
        for item in payload["ordered_callable_adapters"]
    ] == list(ORDERED_CORE_AGENT_NAMES)
    assert all(
        callable(item["callable"])
        for item in payload["ordered_callable_adapters"]
    )


def test_each_callable_accepts_phase17a_request_and_returns_dict():
    payload = build_three_core_agent_shadow_callable_adapters(
        enabled=True
    )

    for agent_name in ORDERED_CORE_AGENT_NAMES:
        result = payload["callable_map"][agent_name](
            _request(agent_name)
        )
        assert isinstance(result, dict)
        assert result["agent_name"] == agent_name
        assert result["shadow_only"] is True
        assert result["advisory_only"] is True
        assert result["mutation_authorized"] is False
        assert result["workflow_connection_authorized"] is False
        assert result["pipeline_connection_authorized"] is False
        assert result["pipeline_stage_added"] is False
        assert isinstance(result["wrapper_result"], dict)


def test_callables_do_not_mutate_request_inputs():
    payload = build_three_core_agent_shadow_callable_adapters(
        enabled=True
    )

    for agent_name in ORDERED_CORE_AGENT_NAMES:
        request = _request(agent_name)
        before = deepcopy(request)
        payload["callable_map"][agent_name](request)
        assert request == before


def test_previous_outputs_are_preserved_as_copied_trace_context():
    payload = build_three_core_agent_shadow_callable_adapters(
        enabled=True
    )
    previous = {
        "relevance_prefilter": {
            "nested": {"values": ["kept"]}
        }
    }
    request = _request("jd_intelligence", previous)
    result = payload["callable_map"]["jd_intelligence"](request)

    assert result["previous_outputs"] == previous
    result["previous_outputs"]["relevance_prefilter"]["nested"][
        "values"
    ].append("changed")
    assert request["previous_outputs"] == previous


def test_adapter_outputs_preserve_three_responsibility_boundaries():
    payload = build_three_core_agent_shadow_callable_adapters(
        enabled=True
    )
    outputs = {
        agent_name: payload["callable_map"][agent_name](
            _request(agent_name)
        )
        for agent_name in ORDERED_CORE_AGENT_NAMES
    }

    assert outputs["relevance_prefilter"]["separation"] == {
        "prefilter_relevance": "described_only",
        "jd_intelligence_evaluation": "not_called",
        "final_application_scoring": "not_called",
    }
    assert outputs["jd_intelligence"]["separation"] == {
        "prefilter_relevance": "not_called",
        "jd_intelligence_evaluation": "described_only",
        "final_application_scoring": "not_called",
    }
    assert outputs["final_application_scoring"]["separation"] == {
        "prefilter_relevance": "not_called",
        "jd_intelligence_evaluation": "not_called",
        "final_application_scoring": "described_only",
    }
    assert outputs["relevance_prefilter"]["wrapper_result"][
        "did_call_live_filter"
    ] is False
    assert outputs["jd_intelligence"]["wrapper_result"][
        "did_call_live_jd_extraction"
    ] is False
    assert outputs["jd_intelligence"]["wrapper_result"][
        "required_skills"
    ] == ["Python"]
    assert outputs["final_application_scoring"]["wrapper_result"][
        "did_call_live_final_application_scoring"
    ] is False


def test_top_level_authorization_and_mutation_paths_are_false():
    payload = build_three_core_agent_shadow_callable_adapters(
        enabled=True
    )

    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    assert payload["callable_adapters_only"] is True
    assert payload["three_core_agent_only"] is True
    assert payload["pipeline_not_connected"] is True
    for key in (
        "pipeline_stage_added",
        "workflow_connection_authorized",
        "pipeline_connection_authorized",
        "mutation_authorized",
        "execution_authorized",
        "submission_authorized",
        "application_execution_authorized",
        "final_scoring_mutation_enabled",
        "ranking_mutation_enabled",
        "queue_mutation_enabled",
        "resume_mutation_enabled",
    ):
        assert payload[key] is False
    assert payload["mutation_authorized_agent_count"] == 0


def test_adapters_match_phase17a_injected_callable_contract():
    adapters = build_three_core_agent_shadow_callable_adapters(
        enabled=True
    )
    callables = adapters["callable_map"]

    payload = run_three_core_agent_shadow_pipeline_hook(
        enabled=True,
        connection_plan=_ready_plan(),
        job_context=_request("relevance_prefilter")["job_context"],
        relevance_prefilter_callable=callables["relevance_prefilter"],
        jd_intelligence_callable=callables["jd_intelligence"],
        final_application_scoring_callable=callables[
            "final_application_scoring"
        ],
    )

    assert payload["hook_status"] == (
        "three_core_shadow_pipeline_hook_completed_shadow_only"
    )
    assert [
        result["agent_name"]
        for result in payload["ordered_shadow_results"]
    ] == list(ORDERED_CORE_AGENT_NAMES)
    assert payload["mutation_authorized"] is False
    assert payload["pipeline_connection_authorized"] is False


def test_source_has_no_pipeline_provider_network_database_or_file_wiring():
    source = (
        ROOT
        / "src/agents/three_core_agent_shadow_callable_adapters.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "filter_jobs(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
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
        "cursor.execute(",
        ".commit(",
        "open(",
        "read_text(",
        "read_bytes(",
        "write_text(",
        "write_bytes(",
        "src.pipeline",
        "src.app",
    ):
        assert marker not in source

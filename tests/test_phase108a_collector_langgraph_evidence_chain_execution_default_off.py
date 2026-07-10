# phase108a legacy guard marker: changes_only collector_langgraph_evidence_chain_execution d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 src/app/api.py
import ast
from copy import deepcopy
from pathlib import Path

from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
BASE_GATE = "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_ENABLED"
LANGGRAPH_GATE = (
    "APPLYLENS_AGENTIC_PIPELINE_LANGGRAPH_EVIDENCE_CHAIN_EXECUTION_ENABLED"
)
TRACE_GATE = "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_TRACE_PERSISTENCE_ENABLED"


def _env(**overrides):
    payload = {
        BASE_GATE: "",
        LANGGRAPH_GATE: "",
        TRACE_GATE: "",
        "APPLYLENS_AGENT_TRACE_ENABLED": "",
        "APPLYLENS_AGENT_TRACE_STRICT": "",
        "JOB_APP_PIPELINE_RUN_ID": "phase108a-run",
        "JOB_STACK_OWNER_USER_ID": "phase108a-owner",
        "APPLYLENS_AGENT_CONTEXT_ID": "phase108a-context",
    }
    payload.update(overrides)
    return payload


def _jobs():
    return [
        {
            "job_id": "job-108a-1",
            "title": "AI Platform Engineer",
            "company": "Example AI",
            "ai_fit_score": 9,
            "priority_score": 14.5,
            "intelligence": {
                "skills": {
                    "required": ["Python", "SQL"],
                    "preferred": ["RAG"],
                    "all": ["Python", "SQL", "RAG"],
                }
            },
        },
        {
            "job_id": "job-108a-2",
            "title": "Backend Engineer",
            "company": "Example Cloud",
            "ai_fit_score": 7,
            "priority_score": 9.5,
            "intelligence": {"skills": {"required": ["Python"], "all": ["Python"]}},
        },
    ]


def _trace_payload(job_id="job-108a-1"):
    return {
        "artifact_type": "agent_evidence_chain_trace_payload",
        "chain_id": f"phase108a:{job_id}:evidence-chain",
        "pipeline_run_id": "phase108a-run",
        "owner_user_id": "phase108a-owner",
        "context_id": "phase108a-context",
        "steps": [],
    }


def _langgraph_result(**overrides):
    payload = {
        "artifact_type": "langgraph_evidence_chain_execution",
        "graph_runtime": "langgraph",
        "attempted": True,
        "executed": True,
        "reason": "langgraph_evidence_chain_completed",
        "automatic_internal_decisioning_performed": True,
        "per_job_results": [
            {
                "job_id": "job-108a-1",
                "status": "succeeded",
                "artifacts": {
                    "agent_evidence_chain_trace_payload": _trace_payload(),
                },
            }
        ],
        "provider_call_performed": False,
        "live_llm_call_performed": False,
        "trace_persistence_performed": False,
        "database_write_performed": False,
    }
    payload.update(overrides)
    return payload


def _deterministic_result(**overrides):
    payload = {
        "artifact_type": "controlled_evidence_chain_execution_result",
        "attempted": True,
        "executed": True,
        "reason": "evidence_chain_execution_completed",
        "automatic_internal_decisioning_performed": True,
        "per_job_results": [],
        "provider_call_performed": False,
        "live_llm_call_performed": False,
        "trace_persistence_performed": False,
        "database_write_performed": False,
    }
    payload.update(overrides)
    return payload


def _wrapper_source() -> str:
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            == "_maybe_run_controlled_evidence_chain_execution_after_application_priority"
        ):
            return ast.get_source_segment(source, node) or ""
    raise AssertionError("collector evidence-chain wrapper missing")


def test_base_gate_off_prevents_langgraph_even_when_langgraph_gate_is_enabled():
    calls = []
    jobs = _jobs()
    before = deepcopy(jobs)

    def fail_langgraph(*_args, **_kwargs):
        calls.append("langgraph")
        raise AssertionError("langgraph must not run when base gate is off")

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{BASE_GATE: "", LANGGRAPH_GATE: "1"}),
        langgraph_execution_helper=fail_langgraph,
    )

    assert result is None
    assert calls == []
    assert jobs == before


def test_base_gate_on_langgraph_gate_off_uses_existing_deterministic_executor():
    calls = []

    def deterministic(received_jobs, **kwargs):
        calls.append(("deterministic", received_jobs, kwargs))
        return _deterministic_result()

    def fail_langgraph(*_args, **_kwargs):
        raise AssertionError("langgraph must not run when its gate is off")

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        _jobs(),
        env=_env(**{BASE_GATE: "1", LANGGRAPH_GATE: ""}),
        execution_helper=deterministic,
        langgraph_execution_helper=fail_langgraph,
    )

    assert [call[0] for call in calls] == ["deterministic"]
    assert result["execution_engine"] == "deterministic"
    assert result["langgraph_execution_enabled"] is False
    assert result["execution_result"]["artifact_type"] == (
        "controlled_evidence_chain_execution_result"
    )
    assert calls[0][2]["execution_gate_enabled"] is True
    assert "enabled" not in calls[0][2]


def test_base_gate_on_langgraph_gate_on_uses_langgraph_executor():
    calls = []

    def fail_deterministic(*_args, **_kwargs):
        raise AssertionError("deterministic executor must not run when langgraph is on")

    def langgraph(received_jobs, **kwargs):
        calls.append((received_jobs, kwargs))
        return _langgraph_result()

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        _jobs(),
        env=_env(**{BASE_GATE: "1", LANGGRAPH_GATE: "1"}),
        execution_helper=fail_deterministic,
        langgraph_execution_helper=langgraph,
    )

    assert len(calls) == 1
    assert result["execution_engine"] == "langgraph"
    assert result["langgraph_gate_name"] == LANGGRAPH_GATE
    assert result["langgraph_execution_enabled"] is True
    assert result["execution_result"]["artifact_type"] == (
        "langgraph_evidence_chain_execution"
    )
    assert calls[0][1]["enabled"] is True
    assert "execution_gate_enabled" not in calls[0][1]


def test_langgraph_executor_receives_bounded_defensive_copy_and_sidecar_only_result():
    jobs = _jobs()
    before = deepcopy(jobs)
    captured = {}

    def langgraph(received_jobs, **_kwargs):
        captured["jobs"] = received_jobs
        received_jobs[0]["priority_score"] = -999
        received_jobs[0]["agent_evidence_chain_bundle"] = {"mutated": True}
        return _langgraph_result()

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{BASE_GATE: "1", LANGGRAPH_GATE: "1"}),
        langgraph_execution_helper=langgraph,
        sample_limit=1,
    )

    assert captured["jobs"] is not jobs
    assert captured["jobs"][0] is not jobs[0]
    assert len(captured["jobs"]) == 1
    assert result["sidecar_only"] is True
    assert result["sample_limit"] == 1
    assert result["jobs_received_count"] == 2
    assert result["jobs_sampled_count"] == 1
    assert jobs == before


def test_langgraph_trace_payload_remains_compatible_with_existing_persistence_extractor():
    execution = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        _jobs(),
        env=_env(**{BASE_GATE: "1", LANGGRAPH_GATE: "1"}),
        langgraph_execution_helper=lambda *_args, **_kwargs: _langgraph_result(),
    )

    payloads = collector._valid_evidence_chain_trace_payloads_from_execution_result(
        execution
    )

    assert [payload["artifact_type"] for payload in payloads] == [
        "agent_evidence_chain_trace_payload"
    ]
    assert payloads[0]["chain_id"] == "phase108a:job-108a-1:evidence-chain"


def test_langgraph_execution_can_flow_through_existing_trace_persistence_helper():
    execution = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        _jobs(),
        env=_env(**{BASE_GATE: "1", LANGGRAPH_GATE: "1"}),
        langgraph_execution_helper=lambda *_args, **_kwargs: _langgraph_result(),
    )
    persisted_payloads = []

    def persist(trace_payload, **_kwargs):
        persisted_payloads.append(trace_payload)
        return {
            "attempted": True,
            "recorded": True,
            "reason": "",
            "record_count": 2,
            "run_count": 1,
            "step_count": 1,
            "agent_run_id": "run-phase108a",
        }

    result = collector._maybe_persist_controlled_evidence_chain_execution_trace(
        execution,
        env=_env(
            **{
                BASE_GATE: "1",
                LANGGRAPH_GATE: "1",
                TRACE_GATE: "1",
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            }
        ),
        execute_callback=lambda *_args, **_kwargs: None,
        persistence_helper=persist,
    )

    assert result["trace_persistence_performed"] is True
    assert result["payloads_found_count"] == 1
    assert persisted_payloads[0]["artifact_type"] == (
        "agent_evidence_chain_trace_payload"
    )


def test_collector_langgraph_wiring_adds_no_provider_api_ui_or_mutation_calls():
    source = _wrapper_source()
    forbidden_tokens = [
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "job_fit_evaluator",
        "manual_critic_guardrail",
        "provider_adapter",
        "submit_application",
        "click_apply",
        "mark_applied",
        "send_recruiter",
        "cursor.execute",
        "commit(",
        "src.app.api",
        "src.app.services",
        "src.app.static",
        "templates",
    ]

    for token in forbidden_tokens:
        assert token not in source
    assert "execute_langgraph_evidence_chain" in source
    assert LANGGRAPH_GATE in (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )

from copy import deepcopy
from pathlib import Path
import ast
import subprocess
import types

import pytest
from fastapi import HTTPException

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]


SAFETY_FALSE_FLAGS = [
    "database_write_performed",
    "trace_persistence_performed",
    "provider_call_performed",
    "live_llm_call_performed",
    "collector_execution_performed",
    "workflow_runner_executed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "queue_mutation_performed",
    "review_queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
    "external_action_automation_performed",
]


def _request(owner_user_id="owner-101b"):
    return types.SimpleNamespace(
        state=types.SimpleNamespace(
            auth_user={"user_id": owner_user_id} if owner_user_id else {}
        )
    )


def _run(
    agent_run_id="agent_evidence_chain_trace:chain-101b:ctx-101b",
    *,
    owner_user_id="owner-101b",
    pipeline_run_id="run-101b",
    context_id="ctx-101b",
    source_agent="evidence_chain_composition",
    status="succeeded",
    summary_json=None,
):
    if summary_json is None:
        summary_json = {
            "source_agent": source_agent,
            "chain_id": "chain-101b",
            "chain_status": "complete",
            "chain_readiness": "ready_for_human_review",
        }
    return {
        "agent_run_id": agent_run_id,
        "owner_user_id": owner_user_id,
        "pipeline_run_id": pipeline_run_id,
        "context_id": context_id,
        "status": status,
        "started_at": "2026-07-08T12:00:00+00:00",
        "completed_at": "2026-07-08T12:00:01+00:00",
        "summary_json": summary_json,
        "error": "",
    }


def _step(
    agent_step_id="step-101b",
    *,
    agent_run_id="agent_evidence_chain_trace:chain-101b:ctx-101b",
    owner_user_id="owner-101b",
    pipeline_run_id="run-101b",
    context_id="ctx-101b",
    agent_name="operator_review",
    status="succeeded",
    output_json=None,
    validation_json=None,
):
    if output_json is None:
        output_json = {
            "agent_key": agent_name,
            "artifact_present": True,
            "artifact_valid": True,
        }
    if validation_json is None:
        validation_json = {"validation_status": "passed"}
    return {
        "agent_step_id": agent_step_id,
        "agent_run_id": agent_run_id,
        "owner_user_id": owner_user_id,
        "pipeline_run_id": pipeline_run_id,
        "context_id": context_id,
        "agent_name": agent_name,
        "agent_version": "agent-evidence-chain-trace-payload-v1",
        "status": status,
        "started_at": "2026-07-08T12:00:00+00:00",
        "completed_at": "2026-07-08T12:00:01+00:00",
        "input_json": {"source_artifact_type": "agent_evidence_chain_bundle"},
        "output_json": output_json,
        "validation_json": validation_json,
        "token_usage_json": {},
        "cost_json": {},
        "error": "",
    }


def _install_store(monkeypatch, *, runs=None, steps=None):
    captured = {"runs": [], "steps": [], "get_run": []}

    def list_runs(**kwargs):
        captured["runs"].append(kwargs)
        return {"runs": deepcopy(runs or [])}

    def list_steps(**kwargs):
        captured["steps"].append(kwargs)
        return {"steps": deepcopy(steps or [])}

    def get_run(**kwargs):
        captured["get_run"].append(kwargs)
        target = kwargs.get("agent_run_id")
        for run in runs or []:
            if run.get("agent_run_id") == target:
                return {"found": True, "run": deepcopy(run)}
        return {"found": False, "run": {}}

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", list_runs)
    monkeypatch.setattr(services, "list_agent_steps_postgres_payload", list_steps)
    monkeypatch.setattr(services, "get_agent_run_postgres_payload", get_run)
    return captured


def _assert_safety(payload):
    assert payload["safety_metadata"]["read_only"] is True
    assert payload["read_only"] is True
    for flag in SAFETY_FALSE_FLAGS:
        assert payload[flag] is False
        assert payload["safety_metadata"][flag] is False


def test_service_empty_result_is_stable_read_only_and_compact(monkeypatch):
    _install_store(monkeypatch, runs=[], steps=[])

    payload = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
    )

    assert payload["artifact_type"] == "evidence_chain_trace_readback"
    assert payload["artifact_version"] == "evidence-chain-trace-readback-v1"
    assert payload["found"] is False
    assert payload["run_count"] == 0
    assert payload["step_count"] == 0
    assert payload["latest_run"] == {}
    assert payload["agent_steps"] == []
    assert payload["per_agent_status"] == {}
    _assert_safety(payload)


def test_service_filters_evidence_chain_rows_only(monkeypatch):
    evidence_prefix_run = _run(source_agent="")
    evidence_summary_run = _run(
        "generic-id-but-evidence-summary",
        summary_json={"source_agent": "evidence_chain_composition"},
    )
    generic_run = _run(
        "generic-agent-run",
        summary_json={"source_agent": "relevance_prefilter"},
    )
    steps = [
        _step("step-prefix", agent_run_id=evidence_prefix_run["agent_run_id"]),
        _step(
            "step-summary",
            agent_run_id=evidence_summary_run["agent_run_id"],
            agent_name="resume_match",
        ),
        _step("step-generic", agent_run_id=generic_run["agent_run_id"]),
    ]
    _install_store(
        monkeypatch,
        runs=[generic_run, evidence_prefix_run, evidence_summary_run],
        steps=steps,
    )

    payload = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
    )

    assert payload["found"] is True
    assert payload["run_count"] == 2
    assert payload["step_count"] == 2
    assert {step["agent_step_id"] for step in payload["agent_steps"]} == {
        "step-prefix",
        "step-summary",
    }
    assert "generic-agent-run" not in {
        step["agent_run_id"] for step in payload["agent_steps"]
    }


def test_service_scopes_rows_by_owner_pipeline_and_context(monkeypatch):
    allowed_run = _run()
    other_owner = _run(owner_user_id="owner-other")
    other_run = _run(pipeline_run_id="run-other")
    other_context = _run(context_id="ctx-other")
    _install_store(
        monkeypatch,
        runs=[allowed_run, other_owner, other_run, other_context],
        steps=[
            _step(agent_run_id=allowed_run["agent_run_id"]),
            _step(
                "step-other-owner",
                agent_run_id=other_owner["agent_run_id"],
                owner_user_id="owner-other",
            ),
            _step(
                "step-other-run",
                agent_run_id=other_run["agent_run_id"],
                pipeline_run_id="run-other",
            ),
            _step(
                "step-other-context",
                agent_run_id=other_context["agent_run_id"],
                context_id="ctx-other",
            ),
        ],
    )

    payload = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
        context_id="ctx-101b",
    )

    assert payload["run_count"] == 1
    assert payload["step_count"] == 1
    assert payload["latest_run"]["context_id"] == "ctx-101b"
    assert payload["agent_steps"][0]["agent_step_id"] == "step-101b"


def test_optional_filters_and_limits_are_respected(monkeypatch):
    run_a = _run("agent_evidence_chain_trace:a:ctx-a", context_id="ctx-a")
    run_b = _run("agent_evidence_chain_trace:b:ctx-a", context_id="ctx-a")
    run_c = _run("agent_evidence_chain_trace:c:ctx-a", context_id="ctx-a")
    _install_store(
        monkeypatch,
        runs=[run_a, run_b, run_c],
        steps=[
            _step("step-a", agent_run_id=run_a["agent_run_id"], context_id="ctx-a"),
            _step("step-b", agent_run_id=run_b["agent_run_id"], context_id="ctx-a"),
            _step("step-c", agent_run_id=run_c["agent_run_id"], context_id="ctx-a"),
        ],
    )

    limited = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
        context_id="ctx-a",
        limit_runs=2,
        limit_steps=1,
    )
    specific = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
        context_id="ctx-a",
        agent_run_id=run_b["agent_run_id"],
    )

    assert limited["run_count"] == 2
    assert limited["step_count"] == 1
    assert specific["run_count"] == 1
    assert specific["latest_run"]["agent_run_id"] == run_b["agent_run_id"]
    assert specific["agent_steps"][0]["agent_step_id"] == "step-b"


def test_compact_payload_exposes_per_agent_status_without_raw_payload(monkeypatch):
    _install_store(
        monkeypatch,
        runs=[_run()],
        steps=[
            _step("step-resume", agent_name="resume_match"),
            _step(
                "step-critic",
                agent_name="critic",
                status="warning",
                output_json={"agent_key": "critic", "artifact_present": True, "artifact_valid": False},
                validation_json={"validation_status": "warning"},
            ),
        ],
    )

    payload = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
    )

    assert payload["latest_run"] == {
        "agent_run_id": "agent_evidence_chain_trace:chain-101b:ctx-101b",
        "context_id": "ctx-101b",
        "status": "succeeded",
        "started_at": "2026-07-08T12:00:00+00:00",
        "completed_at": "2026-07-08T12:00:01+00:00",
        "chain_id": "chain-101b",
        "chain_status": "complete",
        "chain_readiness": "ready_for_human_review",
        "source_agent": "evidence_chain_composition",
        "error": "",
    }
    assert payload["per_agent_status"]["resume_match"]["status"] == "succeeded"
    assert payload["per_agent_status"]["critic"]["validation_status"] == "warning"
    assert "recording_payload" not in str(payload)
    assert "agent_step_compatible_summaries" not in str(payload)


def test_malformed_rows_do_not_crash_and_report_warnings(monkeypatch):
    _install_store(
        monkeypatch,
        runs=[
            _run(
                "agent_evidence_chain_trace:malformed:ctx-101b",
                summary_json="not-json",
            )
        ],
        steps=[
            _step(
                "step-malformed",
                agent_run_id="agent_evidence_chain_trace:malformed:ctx-101b",
                output_json="bad-output",
                validation_json="bad-validation",
            )
        ],
    )

    payload = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
    )

    assert payload["found"] is True
    assert payload["warning_count"] == 2
    assert payload["warnings"] == [
        "malformed_run_summary_json",
        "malformed_step_json",
    ]
    assert payload["agent_steps"][0]["agent_name"] == "operator_review"


def test_store_failure_returns_safe_empty_payload(monkeypatch):
    def fail_read(**_kwargs):
        raise subprocess.SubprocessError("psql unavailable")

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", fail_read)
    monkeypatch.setattr(services, "list_agent_steps_postgres_payload", fail_read)

    payload = services.get_evidence_chain_trace_readback_payload(
        owner_user_id="owner-101b",
        pipeline_run_id="run-101b",
    )

    assert payload["found"] is False
    assert payload["warnings"] == ["trace_store_read_failed"]
    assert payload["database_write_performed"] is False
    _assert_safety(payload)


def test_api_requires_auth_and_derives_owner_from_request(monkeypatch):
    captured = {}

    def fake_readback(**kwargs):
        captured.update(kwargs)
        return {"artifact_type": "evidence_chain_trace_readback", "owner_user_id": kwargs["owner_user_id"]}

    monkeypatch.setattr(services, "get_evidence_chain_trace_readback_payload", fake_readback)

    with pytest.raises(HTTPException) as exc_info:
        api.profile_pipeline_run_evidence_chain_trace("run-101b", _request(""))
    assert exc_info.value.status_code == 401

    payload = api.profile_pipeline_run_evidence_chain_trace(
        "run-101b",
        _request("owner-from-auth"),
        context_id="ctx-api",
        agent_run_id="agent-run-api",
        limit_runs=3,
        limit_steps=4,
    )

    assert payload["owner_user_id"] == "owner-from-auth"
    assert captured == {
        "owner_user_id": "owner-from-auth",
        "pipeline_run_id": "run-101b",
        "context_id": "ctx-api",
        "agent_run_id": "agent-run-api",
        "limit_runs": 3,
        "limit_steps": 4,
    }


def test_api_route_returns_compact_payload_without_changing_agent_trace_route(monkeypatch):
    expected = {
        "artifact_type": "evidence_chain_trace_readback",
        "found": False,
        "run_count": 0,
        "step_count": 0,
    }

    monkeypatch.setattr(
        services,
        "get_evidence_chain_trace_readback_payload",
        lambda **_kwargs: dict(expected),
    )

    payload = api.profile_pipeline_run_evidence_chain_trace(
        "run-101b",
        _request("owner-101b"),
        limit_runs=1,
        limit_steps=1,
    )

    assert payload == expected


def test_source_safety_no_collector_persistence_provider_ui_or_apply_paths():
    service_source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    api_source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    tree = ast.parse(service_source)
    helper_source = ""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "get_evidence_chain_trace_readback_payload"
        ):
            helper_source = ast.get_source_segment(service_source, node) or ""
            break
    assert helper_source

    assert "/profile/pipeline-runs/{run_id}/evidence-chain-trace" in api_source
    assert "owner_user_id: str" not in api_source[
        api_source.index("def profile_pipeline_run_evidence_chain_trace"):
        api_source.index("@app.post(\"/api/shadow-sidecar/trace-readback\")")
    ]
    for forbidden in [
        "src.pipeline.collector",
        "persist_agent_evidence_chain_trace_payload",
        "execute_controlled_evidence_chain",
        "workflow_runner",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "src.app.static",
        "submit_application",
        "click_apply",
        "mark_applied",
        "send_recruiter",
        "insert_",
        "upsert_",
        "delete_",
        ".execute(",
    ]:
        assert forbidden not in helper_source


import types

from fastapi import HTTPException
import requests

from src.app import api, services


def _request(owner_user_id="user_1"):
    return types.SimpleNamespace(
        state=types.SimpleNamespace(auth_user={"user_id": owner_user_id} if owner_user_id else {})
    )


def test_agent_trace_api_test_does_not_stub_requests_module():
    assert hasattr(requests, "Session")


def test_agent_trace_empty_payload_is_stable(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"ok": True, "runs": [], "count": 0},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"ok": True, "steps": [], "count": 0},
    )

    payload = services.agent_trace_payload(owner_user_id="user_1", pipeline_run_id="run_1")

    assert payload == {
        "pipeline_run_id": "run_1",
        "owner_user_id": "user_1",
        "agent_runs": [],
        "counts": {
            "agent_runs": 0,
            "agent_steps": 0,
            "failed_steps": 0,
            "warning_steps": 0,
            "succeeded_steps": 0,
        },
    }


def test_agent_trace_payload_nests_one_run_and_step(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {
            "ok": True,
            "runs": [
                {
                    "agent_run_id": "agent_run_1",
                    "owner_user_id": "user_1",
                    "pipeline_run_id": "run_1",
                    "context_id": "ctx_1",
                    "status": "succeeded",
                    "started_at": "2026-05-29T12:00:00+00:00",
                    "completed_at": "2026-05-29T12:00:02+00:00",
                    "summary_json": {"rows": 3},
                    "error": "",
                }
            ],
        },
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {
            "ok": True,
            "steps": [
                {
                    "agent_step_id": "agent_step_1",
                    "agent_run_id": "agent_run_1",
                    "owner_user_id": "user_1",
                    "pipeline_run_id": "run_1",
                    "context_id": "ctx_1",
                    "agent_name": "resume_match_agent",
                    "agent_version": "v1",
                    "status": "succeeded",
                    "started_at": "2026-05-29T12:00:01+00:00",
                    "completed_at": "2026-05-29T12:00:02+00:00",
                    "latency_ms": 17,
                    "model_provider": "",
                    "model_name": "",
                    "input_json": {"jobs": 3},
                    "output_json": {"selected": 2},
                    "validation_json": {"validation_status": "passed"},
                    "token_usage_json": {},
                    "cost_json": {},
                    "error": "",
                }
            ],
        },
    )

    payload = services.agent_trace_payload(owner_user_id="user_1", pipeline_run_id="run_1")

    assert payload["counts"] == {
        "agent_runs": 1,
        "agent_steps": 1,
        "failed_steps": 0,
        "warning_steps": 0,
        "succeeded_steps": 1,
    }
    assert payload["agent_runs"][0]["summary_json"] == {"rows": 3}
    assert payload["agent_runs"][0]["steps"][0]["agent_name"] == "resume_match_agent"
    assert payload["agent_runs"][0]["steps"][0]["input_json"] == {"jobs": 3}


def test_agent_trace_steps_are_ordered_by_started_at(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {
            "runs": [
                {
                    "agent_run_id": "agent_run_1",
                    "owner_user_id": "user_1",
                    "pipeline_run_id": "run_1",
                    "context_id": "",
                }
            ]
        },
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {
            "steps": [
                {
                    "agent_step_id": "step_late",
                    "agent_run_id": "agent_run_1",
                    "owner_user_id": "user_1",
                    "pipeline_run_id": "run_1",
                    "started_at": "2026-05-29T12:00:03+00:00",
                    "status": "succeeded",
                },
                {
                    "agent_step_id": "step_early",
                    "agent_run_id": "agent_run_1",
                    "owner_user_id": "user_1",
                    "pipeline_run_id": "run_1",
                    "started_at": "2026-05-29T12:00:01+00:00",
                    "status": "failed",
                    "error": "boom",
                },
            ]
        },
    )

    payload = services.agent_trace_payload(owner_user_id="user_1", pipeline_run_id="run_1")

    steps = payload["agent_runs"][0]["steps"]
    assert [step["agent_step_id"] for step in steps] == ["step_early", "step_late"]
    assert payload["counts"]["failed_steps"] == 1
    assert payload["counts"]["succeeded_steps"] == 1


def test_agent_trace_warning_count_uses_validation_status(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {
            "runs": [
                {
                    "agent_run_id": "agent_run_1",
                    "owner_user_id": "user_1",
                    "pipeline_run_id": "run_1",
                }
            ]
        },
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {
            "steps": [
                {
                    "agent_step_id": "step_warning",
                    "agent_run_id": "agent_run_1",
                    "owner_user_id": "user_1",
                    "pipeline_run_id": "run_1",
                    "status": "succeeded",
                    "validation_json": {"validation_status": "warning"},
                }
            ]
        },
    )

    payload = services.agent_trace_payload(owner_user_id="user_1", pipeline_run_id="run_1")

    assert payload["counts"]["warning_steps"] == 1


def test_agent_trace_filters_wrong_owner_and_pipeline_rows(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {
            "runs": [
                {"agent_run_id": "other_owner", "owner_user_id": "user_2", "pipeline_run_id": "run_1"},
                {"agent_run_id": "other_run", "owner_user_id": "user_1", "pipeline_run_id": "run_2"},
            ]
        },
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {
            "steps": [
                {
                    "agent_step_id": "leaked_step",
                    "agent_run_id": "other_owner",
                    "owner_user_id": "user_2",
                    "pipeline_run_id": "run_1",
                }
            ]
        },
    )

    payload = services.agent_trace_payload(owner_user_id="user_1", pipeline_run_id="run_1")

    assert payload["agent_runs"] == []
    assert payload["counts"]["agent_steps"] == 0


def test_agent_trace_payload_can_filter_specific_agent_run(monkeypatch):
    captured = {}

    def fake_get_agent_run_postgres_payload(**kwargs):
        captured["get_run"] = dict(kwargs)
        return {
            "found": True,
            "run": {
                "agent_run_id": "agent_run_2",
                "owner_user_id": "user_1",
                "pipeline_run_id": "run_1",
                "context_id": "ctx_2",
            },
        }

    def fake_list_agent_steps_postgres_payload(**kwargs):
        captured["list_steps"] = dict(kwargs)
        return {"steps": []}

    monkeypatch.setattr(services, "get_agent_run_postgres_payload", fake_get_agent_run_postgres_payload)
    monkeypatch.setattr(services, "list_agent_steps_postgres_payload", fake_list_agent_steps_postgres_payload)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        context_id="ctx_2",
        agent_run_id="agent_run_2",
    )

    assert payload["counts"]["agent_runs"] == 1
    assert captured["get_run"]["owner_user_id"] == "user_1"
    assert captured["list_steps"]["agent_run_id"] == "agent_run_2"
    assert captured["list_steps"]["context_id"] == "ctx_2"


def test_profile_pipeline_run_agent_trace_route_uses_authenticated_owner(monkeypatch):
    captured = {}

    def fake_agent_trace_payload(**kwargs):
        captured.update(kwargs)
        return {
            "pipeline_run_id": kwargs["pipeline_run_id"],
            "owner_user_id": kwargs["owner_user_id"],
            "agent_runs": [],
            "counts": {
                "agent_runs": 0,
                "agent_steps": 0,
                "failed_steps": 0,
                "warning_steps": 0,
                "succeeded_steps": 0,
            },
        }

    monkeypatch.setattr(services, "agent_trace_payload", fake_agent_trace_payload)

    payload = api.profile_pipeline_run_agent_trace(
        "run_route",
        _request("user_route"),
        context_id="ctx_route",
        agent_run_id="agent_run_route",
    )

    assert payload["owner_user_id"] == "user_route"
    assert captured == {
        "owner_user_id": "user_route",
        "pipeline_run_id": "run_route",
        "context_id": "ctx_route",
        "agent_run_id": "agent_run_route",
        "include_trace_summary": False,
    }


def test_profile_pipeline_run_agent_trace_route_preserves_default_shape(monkeypatch):
    captured = {}

    def fake_agent_trace_payload(**kwargs):
        captured.update(kwargs)
        return {
            "pipeline_run_id": kwargs["pipeline_run_id"],
            "owner_user_id": kwargs["owner_user_id"],
            "agent_runs": [],
            "counts": {
                "agent_runs": 0,
                "agent_steps": 0,
                "failed_steps": 0,
                "warning_steps": 0,
                "succeeded_steps": 0,
            },
        }

    monkeypatch.setattr(services, "agent_trace_payload", fake_agent_trace_payload)

    payload = api.profile_pipeline_run_agent_trace("run_route", _request("user_route"))

    assert "trace_summary" not in payload
    assert captured["include_trace_summary"] is False


def test_profile_pipeline_run_agent_trace_route_can_opt_in_trace_summary(monkeypatch):
    captured = {}

    def fake_agent_trace_payload(**kwargs):
        captured.update(kwargs)
        payload = {
            "pipeline_run_id": kwargs["pipeline_run_id"],
            "owner_user_id": kwargs["owner_user_id"],
            "agent_runs": [],
            "counts": {
                "agent_runs": 0,
                "agent_steps": 0,
                "failed_steps": 0,
                "warning_steps": 0,
                "succeeded_steps": 0,
            },
        }
        if kwargs["include_trace_summary"]:
            payload["trace_summary"] = {
                "summary_type": "agent_trace",
                "run_count": 0,
                "step_count": 0,
            }
        return payload

    monkeypatch.setattr(services, "agent_trace_payload", fake_agent_trace_payload)

    for value in ["1", "true", "yes", "on", " TRUE "]:
        captured.clear()
        payload = api.profile_pipeline_run_agent_trace(
            "run_route",
            _request("user_route"),
            include_trace_summary=value,
        )
        assert captured["include_trace_summary"] is True
        assert payload["trace_summary"]["summary_type"] == "agent_trace"


def test_profile_pipeline_run_agent_trace_route_false_flags_preserve_default_shape(monkeypatch):
    captured_values = []

    def fake_agent_trace_payload(**kwargs):
        captured_values.append(kwargs["include_trace_summary"])
        return {
            "pipeline_run_id": kwargs["pipeline_run_id"],
            "owner_user_id": kwargs["owner_user_id"],
            "agent_runs": [],
            "counts": {
                "agent_runs": 0,
                "agent_steps": 0,
                "failed_steps": 0,
                "warning_steps": 0,
                "succeeded_steps": 0,
            },
        }

    monkeypatch.setattr(services, "agent_trace_payload", fake_agent_trace_payload)

    for value in ["", "0", "false", "no", "off", "summary"]:
        payload = api.profile_pipeline_run_agent_trace(
            "run_route",
            _request("user_route"),
            include_trace_summary=value,
        )
        assert "trace_summary" not in payload

    assert captured_values == [False, False, False, False, False, False]


def test_profile_pipeline_run_agent_trace_route_does_not_invoke_summary_helper_by_default(monkeypatch):
    called = {"summary_helper": False}

    def fail_summary_helper(**kwargs):
        called["summary_helper"] = True
        raise AssertionError("summary helper must not run for default route response")

    monkeypatch.setattr(services, "build_agent_trace_summary_payload", fail_summary_helper)
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"ok": True, "runs": [], "count": 0},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"ok": True, "steps": [], "count": 0},
    )

    payload = api.profile_pipeline_run_agent_trace("run_route", _request("user_route"))

    assert "trace_summary" not in payload
    assert called["summary_helper"] is False


def test_profile_pipeline_run_agent_trace_route_requires_auth():
    try:
        api.profile_pipeline_run_agent_trace("run_route", _request(""))
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected route to require authenticated owner.")


def test_pipeline_child_env_propagates_agent_trace_flags():
    child_env = services._pipeline_child_env(
        base_env={
            "APPLYLENS_AGENT_TRACE_ENABLED": "1",
            "APPLYLENS_AGENT_TRACE_STRICT": "true",
            "UNRELATED_SECRET": "do-not-copy",
            "PATH": "/usr/bin",
        },
        extra_env={},
    )

    assert child_env["APPLYLENS_AGENT_TRACE_ENABLED"] == "1"
    assert child_env["APPLYLENS_AGENT_TRACE_STRICT"] == "true"
    assert "UNRELATED_SECRET" not in child_env

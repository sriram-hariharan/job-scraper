from src.app import services


def _run(**overrides):
    row = {
        "agent_run_id": "agent_run_1",
        "owner_user_id": "user_1",
        "pipeline_run_id": "run_1",
        "context_id": "",
        "status": "succeeded",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:02Z",
        "summary_json": {"jobs": 2},
        "error": "",
    }
    row.update(overrides)
    return row


def _step(**overrides):
    row = {
        "agent_step_id": "agent_step_1",
        "agent_run_id": "agent_run_1",
        "owner_user_id": "user_1",
        "pipeline_run_id": "run_1",
        "context_id": "",
        "agent_name": "resume_match_agent",
        "agent_version": "v1",
        "input_json": {"jobs": 2},
        "output_json": {"selected": 1},
        "validation_json": {"validation_status": "passed"},
        "status": "succeeded",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "latency_ms": 100,
        "model_provider": "",
        "model_name": "",
        "token_usage_json": {},
        "cost_json": {},
        "error": "",
    }
    row.update(overrides)
    return row


def test_agent_trace_payload_includes_read_only_trace_summary(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": [_run()]},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {
            "steps": [
                _step(),
                _step(
                    agent_step_id="agent_step_2",
                    agent_name="critic_agent",
                    status="failed",
                    error="invalid suggestion",
                    latency_ms=300,
                ),
            ]
        },
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

    assert payload["counts"] == {
        "agent_runs": 1,
        "agent_steps": 2,
        "failed_steps": 1,
        "warning_steps": 0,
        "succeeded_steps": 1,
    }

    trace_summary = payload["trace_summary"]
    assert trace_summary["ok"] is True
    assert trace_summary["summary_type"] == "agent_trace"
    assert trace_summary["run_count"] == 1
    assert trace_summary["step_count"] == 2
    assert trace_summary["error_step_count"] == 1
    assert trace_summary["agent_counts"] == {
        "critic_agent": 1,
        "resume_match_agent": 1,
    }
    assert trace_summary["latency_summary"] == {
        "count": 2,
        "total_ms": 400,
        "min_ms": 100,
        "max_ms": 300,
        "average_ms": 200.0,
    }
    assert trace_summary["all_required_fields_present"] is True
    assert trace_summary["safety_metadata"]["did_read_database"] is False
    assert trace_summary["safety_metadata"]["did_write_database"] is False
    assert trace_summary["safety_metadata"]["did_call_llm"] is False
    assert trace_summary["safety_metadata"]["did_execute_application"] is False
    assert trace_summary["safety_metadata"]["did_submit_application"] is False


def test_agent_trace_payload_default_does_not_include_stage_trace_bundle(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": [_run()]},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": [_step()]},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
    )

    assert "trace_summary" not in payload
    assert "stage_trace_bundle" not in payload
    assert "stage_trace_health" not in payload
    assert "stage_trace_readiness" not in payload
    assert "trace_evidence_pack" not in payload


def test_agent_trace_payload_includes_opt_in_stage_trace_bundle_without_extra_reads(monkeypatch):
    calls = {"runs": 0, "steps": 0}

    def runs_payload(**kwargs):
        calls["runs"] += 1
        return {"runs": [_run()]}

    def steps_payload(**kwargs):
        calls["steps"] += 1
        return {
            "steps": [
                _step(
                    agent_name="relevance_prefilter_agent",
                    step_name="relevance_prefilter_trace_wrapper",
                ),
                _step(
                    agent_step_id="agent_step_2",
                    agent_name="deduplication_agent",
                    step_name="deduplication_trace_wrapper",
                ),
            ]
        }

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", runs_payload)
    monkeypatch.setattr(services, "list_agent_steps_postgres_payload", steps_payload)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_bundle=True,
    )

    assert calls == {"runs": 1, "steps": 1}
    assert "trace_summary" not in payload
    bundle = payload["stage_trace_bundle"]
    assert bundle["bundle_type"] == "stage_trace_bundle"
    assert bundle["step_count"] == 2
    assert bundle["trace_summary"]["step_count"] == 2
    assert bundle["stage_names"] == [
        "relevance_prefilter_trace_wrapper",
        "deduplication_trace_wrapper",
    ]
    assert bundle["missing_expected_stages"] == [
        "jd_intelligence_trace_wrapper",
        "final_application_scoring_trace_wrapper",
    ]
    assert bundle["safety_metadata"]["did_write_database"] is False
    assert bundle["safety_metadata"]["did_call_llm"] is False
    assert bundle["safety_metadata"]["did_change_ranking"] is False
    assert bundle["safety_metadata"]["did_change_scoring"] is False
    assert bundle["safety_metadata"]["did_change_approval"] is False
    assert bundle["safety_metadata"]["did_execute_application"] is False
    assert bundle["safety_metadata"]["did_submit_application"] is False


def test_agent_trace_payload_includes_opt_in_stage_trace_health_without_extra_reads(monkeypatch):
    calls = {"runs": 0, "steps": 0}

    def runs_payload(**kwargs):
        calls["runs"] += 1
        return {"runs": [_run()]}

    def steps_payload(**kwargs):
        calls["steps"] += 1
        return {
            "steps": [
                _step(
                    agent_name="relevance_prefilter_agent",
                    step_name="relevance_prefilter_trace_wrapper",
                ),
                _step(
                    agent_step_id="agent_step_2",
                    agent_name="deduplication_agent",
                    step_name="deduplication_trace_wrapper",
                ),
            ]
        }

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", runs_payload)
    monkeypatch.setattr(services, "list_agent_steps_postgres_payload", steps_payload)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_health=True,
    )

    assert calls == {"runs": 1, "steps": 1}
    assert "stage_trace_bundle" not in payload
    health = payload["stage_trace_health"]
    assert health["ok"] is False
    assert health["health_status"] == "warning"
    assert "missing_expected_stages" in health["findings"]
    assert health["safety_metadata"]["did_write_database"] is False
    assert health["safety_metadata"]["did_call_llm"] is False
    assert health["safety_metadata"]["did_change_ranking"] is False
    assert health["safety_metadata"]["did_change_scoring"] is False
    assert health["safety_metadata"]["did_change_approval"] is False
    assert health["safety_metadata"]["did_execute_application"] is False
    assert health["safety_metadata"]["did_submit_application"] is False


def test_agent_trace_payload_includes_opt_in_stage_trace_readiness_without_extra_reads(monkeypatch):
    calls = {"runs": 0, "steps": 0}

    def runs_payload(**kwargs):
        calls["runs"] += 1
        return {"runs": [_run()]}

    def steps_payload(**kwargs):
        calls["steps"] += 1
        return {
            "steps": [
                _step(
                    agent_name="relevance_prefilter_agent",
                    step_name="relevance_prefilter_trace_wrapper",
                ),
                _step(
                    agent_step_id="agent_step_2",
                    agent_name="deduplication_agent",
                    step_name="deduplication_trace_wrapper",
                ),
            ]
        }

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", runs_payload)
    monkeypatch.setattr(services, "list_agent_steps_postgres_payload", steps_payload)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_readiness=True,
    )

    assert calls == {"runs": 1, "steps": 1}
    assert "stage_trace_bundle" not in payload
    assert "stage_trace_health" not in payload
    readiness = payload["stage_trace_readiness"]
    assert readiness["ok"] is False
    assert readiness["readiness_status"] == "blocked"
    assert "missing_expected_stages" in readiness["decision_reason_codes"]
    assert readiness["safety_metadata"]["did_write_database"] is False
    assert readiness["safety_metadata"]["did_call_llm"] is False
    assert readiness["safety_metadata"]["did_change_ranking"] is False
    assert readiness["safety_metadata"]["did_change_scoring"] is False
    assert readiness["safety_metadata"]["did_change_approval"] is False
    assert readiness["safety_metadata"]["did_execute_application"] is False
    assert readiness["safety_metadata"]["did_submit_application"] is False


def test_agent_trace_payload_includes_opt_in_trace_evidence_pack_without_extra_reads(monkeypatch):
    calls = {"runs": 0, "steps": 0}

    def runs_payload(**kwargs):
        calls["runs"] += 1
        return {"runs": [_run()]}

    def steps_payload(**kwargs):
        calls["steps"] += 1
        return {
            "steps": [
                _step(
                    agent_name="relevance_prefilter_agent",
                    step_name="relevance_prefilter_trace_wrapper",
                ),
                _step(
                    agent_step_id="agent_step_2",
                    agent_name="deduplication_agent",
                    step_name="deduplication_trace_wrapper",
                ),
            ]
        }

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", runs_payload)
    monkeypatch.setattr(services, "list_agent_steps_postgres_payload", steps_payload)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_evidence_pack=True,
    )

    assert calls == {"runs": 1, "steps": 1}
    assert "trace_summary" not in payload
    assert "stage_trace_bundle" not in payload
    assert "stage_trace_health" not in payload
    assert "stage_trace_readiness" not in payload
    evidence_pack = payload["trace_evidence_pack"]
    assert evidence_pack["evidence_pack_type"] == "agent_trace_evidence_pack"
    assert evidence_pack["ok"] is False
    assert evidence_pack["summary_status"] == "available"
    assert evidence_pack["stage_count"] == 2
    assert evidence_pack["health_status"] == "warning"
    assert evidence_pack["readiness_status"] == "blocked"
    assert evidence_pack["available_sections"] == [
        "trace_summary",
        "stage_trace_bundle",
        "stage_trace_health",
        "stage_trace_readiness",
    ]
    assert evidence_pack["missing_sections"] == []
    assert "missing_expected_stages" in evidence_pack["decision_reason_codes"]
    assert evidence_pack["safety_metadata"]["did_write_database"] is False
    assert evidence_pack["safety_metadata"]["did_call_llm"] is False
    assert evidence_pack["safety_metadata"]["did_change_ranking"] is False
    assert evidence_pack["safety_metadata"]["did_change_scoring"] is False
    assert evidence_pack["safety_metadata"]["did_change_approval"] is False
    assert evidence_pack["safety_metadata"]["did_execute_application"] is False
    assert evidence_pack["safety_metadata"]["did_submit_application"] is False


def test_agent_trace_payload_empty_result_includes_empty_trace_summary(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

    assert payload["agent_runs"] == []
    assert payload["counts"]["agent_runs"] == 0
    assert payload["counts"]["agent_steps"] == 0
    assert payload["trace_summary"]["run_count"] == 0
    assert payload["trace_summary"]["step_count"] == 0
    assert payload["trace_summary"]["all_required_fields_present"] is True
    assert payload["trace_summary"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_empty_result_includes_safe_stage_trace_bundle(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_bundle=True,
    )

    assert payload["agent_runs"] == []
    assert payload["stage_trace_bundle"]["step_count"] == 0
    assert payload["stage_trace_bundle"]["stage_names"] == []
    assert payload["stage_trace_bundle"]["missing_expected_stages"] == [
        "relevance_prefilter_trace_wrapper",
        "deduplication_trace_wrapper",
        "jd_intelligence_trace_wrapper",
        "final_application_scoring_trace_wrapper",
    ]
    assert payload["stage_trace_bundle"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_empty_result_includes_safe_stage_trace_health(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_health=True,
    )

    assert payload["agent_runs"] == []
    assert "stage_trace_bundle" not in payload
    assert payload["stage_trace_health"]["ok"] is False
    assert payload["stage_trace_health"]["health_status"] == "warning"
    assert payload["stage_trace_health"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_empty_result_includes_safe_stage_trace_readiness(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_readiness=True,
    )

    assert payload["agent_runs"] == []
    assert "stage_trace_bundle" not in payload
    assert "stage_trace_health" not in payload
    assert payload["stage_trace_readiness"]["readiness_status"] == "blocked"
    assert payload["stage_trace_readiness"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_empty_result_includes_safe_trace_evidence_pack(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_evidence_pack=True,
    )

    assert payload["agent_runs"] == []
    assert "trace_summary" not in payload
    assert "stage_trace_bundle" not in payload
    assert "stage_trace_health" not in payload
    assert "stage_trace_readiness" not in payload
    assert payload["trace_evidence_pack"]["readiness_status"] == "blocked"
    assert payload["trace_evidence_pack"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_exception_fallback_includes_empty_trace_summary(monkeypatch):
    def fail_runs(**kwargs):
        raise SystemExit("database unavailable")

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", fail_runs)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

    assert payload["agent_runs"] == []
    assert payload["counts"] == {
        "agent_runs": 0,
        "agent_steps": 0,
        "failed_steps": 0,
        "warning_steps": 0,
        "succeeded_steps": 0,
    }
    assert payload["trace_summary"]["run_count"] == 0
    assert payload["trace_summary"]["step_count"] == 0
    assert payload["trace_summary"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_exception_fallback_includes_safe_stage_trace_bundle(monkeypatch):
    def fail_runs(**kwargs):
        raise SystemExit("database unavailable")

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", fail_runs)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_bundle=True,
    )

    assert payload["agent_runs"] == []
    assert payload["stage_trace_bundle"]["step_count"] == 0
    assert payload["stage_trace_bundle"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_exception_fallback_includes_safe_stage_trace_health(monkeypatch):
    def fail_runs(**kwargs):
        raise SystemExit("database unavailable")

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", fail_runs)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_health=True,
    )

    assert payload["agent_runs"] == []
    assert payload["stage_trace_health"]["health_status"] == "warning"
    assert payload["stage_trace_health"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_exception_fallback_includes_safe_stage_trace_readiness(monkeypatch):
    def fail_runs(**kwargs):
        raise SystemExit("database unavailable")

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", fail_runs)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_stage_trace_readiness=True,
    )

    assert payload["agent_runs"] == []
    assert payload["stage_trace_readiness"]["readiness_status"] == "blocked"
    assert payload["stage_trace_readiness"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_exception_fallback_includes_safe_trace_evidence_pack(monkeypatch):
    def fail_runs(**kwargs):
        raise SystemExit("database unavailable")

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", fail_runs)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_evidence_pack=True,
    )

    assert payload["agent_runs"] == []
    assert payload["trace_evidence_pack"]["readiness_status"] == "blocked"
    assert payload["trace_evidence_pack"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_default_shape_preserves_existing_api_contract(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

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


def test_agent_trace_payload_default_shape_preserves_existing_api_contract(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
    )

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

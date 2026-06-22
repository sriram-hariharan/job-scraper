from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_hook
from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
THREE_CORE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_SHADOW_PIPELINE_HOOK_ENABLED"
)
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def _jobs() -> list[dict]:
    return [
        {
            "id": "job-phase17d",
            "title": "Applied AI Engineer",
            "application_priority_score": 0.94,
            "nested": {"skills": ["python"]},
        }
    ]


def _clear_flags(monkeypatch) -> None:
    monkeypatch.delenv(GLOBAL_FLAG, raising=False)
    monkeypatch.delenv(THREE_CORE_FLAG, raising=False)


def test_default_off_collector_does_not_attach_three_core_payload(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        _jobs()
    )

    assert "three_core_shadow_pipeline_hook_payload" not in payload


def test_enabled_collector_supplies_ready_plan_but_no_callables(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(THREE_CORE_FLAG, "true")
    jobs = _jobs()
    before = deepcopy(jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        jobs
    )

    bridge = payload["three_core_shadow_pipeline_hook_payload"]
    checks = bridge["three_core_shadow_pipeline_hook"]["hook_checks"]
    assert bridge["hook_status"] == (
        "three_core_shadow_pipeline_hook_blocked"
    )
    assert bridge["connection_plan_summary"][
        "connection_plan_ready"
    ] is True
    assert checks["connection_plan_supplied"] is True
    assert checks["connection_plan_ready"] is True
    assert checks["ordered_core_agent_names_match"] is True
    assert checks["planned_connections_are_shadow_only"] is True
    assert checks["relevance_prefilter_callable_supplied"] is False
    assert checks["jd_intelligence_callable_supplied"] is False
    assert checks[
        "final_application_scoring_callable_supplied"
    ] is False
    assert bridge["ordered_shadow_results"] == []
    assert bridge["shadow_result_count"] == 0
    assert jobs == before


def test_collector_connection_plan_has_expected_ordered_shadow_shape(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(THREE_CORE_FLAG, "true")
    captured = {}

    def capture_hook(**kwargs):
        captured.update(kwargs)
        return {"hook_status": "captured"}

    monkeypatch.setattr(
        shadow_sidecar_hook,
        "run_shadow_sidecar_pipeline_hook",
        capture_hook,
    )

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        _jobs()
    )

    plan = captured["three_core_connection_plan"]
    assert payload == {"hook_status": "captured"}
    assert plan["connection_plan_status"] == (
        "three_core_shadow_pipeline_connection_plan_"
        "ready_no_pipeline_change"
    )
    assert tuple(plan["ordered_core_agent_names"]) == (
        ORDERED_CORE_AGENT_NAMES
    )
    assert [
        item["agent_name"]
        for item in plan["ordered_planned_connections"]
    ] == list(ORDERED_CORE_AGENT_NAMES)
    assert all(
        item["shadow_only"]
        for item in plan["ordered_planned_connections"]
    )
    assert plan["pipeline_entrypoint_summary"]["stage_name"] == (
        "post_final_scoring"
    )
    assert plan["pipeline_not_connected"] is True
    assert plan["pipeline_stage_not_added"] is True


def test_connection_plan_is_built_only_when_three_core_flag_is_enabled(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    captured = {}

    def capture_hook(**kwargs):
        captured.update(kwargs)
        return {"hook_status": "captured"}

    monkeypatch.setattr(
        shadow_sidecar_hook,
        "run_shadow_sidecar_pipeline_hook",
        capture_hook,
    )

    collector._maybe_run_shadow_sidecar_after_application_priority(_jobs())

    assert captured["three_core_shadow_pipeline_hook_enabled"] is False
    assert captured["three_core_connection_plan"] is None
    assert captured["three_core_job_context"] is None


def test_global_sidecar_gate_still_controls_connection_plan_path(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(THREE_CORE_FLAG, "true")
    calls = []

    def fail_if_called(**kwargs):
        calls.append(kwargs)
        return {}

    monkeypatch.setattr(
        shadow_sidecar_hook,
        "run_shadow_sidecar_pipeline_hook",
        fail_if_called,
    )

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        _jobs()
    )

    assert payload is None
    assert calls == []


def test_collector_passes_no_three_core_callables_and_mutates_nothing(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(THREE_CORE_FLAG, "true")
    jobs = _jobs()
    before = deepcopy(jobs)
    captured = {}

    def capture_hook(**kwargs):
        captured.update(kwargs)
        return {"hook_status": "captured"}

    monkeypatch.setattr(
        shadow_sidecar_hook,
        "run_shadow_sidecar_pipeline_hook",
        capture_hook,
    )

    collector._maybe_run_shadow_sidecar_after_application_priority(jobs)

    assert "three_core_relevance_prefilter_callable" not in captured
    assert "three_core_jd_intelligence_callable" not in captured
    assert "three_core_final_application_scoring_callable" not in captured
    assert jobs == before


def test_collector_connection_plan_region_has_no_forbidden_behavior():
    source = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    start = source.index("        three_core_connection_plan = None")
    end = source.index(
        "        payload = run_shadow_sidecar_pipeline_hook(",
        start,
    )
    region = source[start:end].lower()

    assert source.count("run_shadow_sidecar_pipeline_hook(") == 1
    assert "three_core_agent_shadow_pipeline_hook" not in region
    for marker in (
        "src.agents.relevance_prefilter",
        "src.agents.jd_intelligence",
        "src.agents.final_application_scoring",
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "cursor.execute(",
        ".commit(",
        "write_text(",
        "write_bytes(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in region

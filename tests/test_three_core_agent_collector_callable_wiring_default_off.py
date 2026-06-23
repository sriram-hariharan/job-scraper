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
            "id": "job-phase17f",
            "title": "Applied AI Engineer",
            "application_priority_score": 0.96,
            "required_skills": ["Python"],
            "preferred_skills": ["SQL"],
            "workflows": ["model monitoring"],
            "nested": {"values": ["original"]},
        }
    ]


def _clear_flags(monkeypatch) -> None:
    monkeypatch.delenv(GLOBAL_FLAG, raising=False)
    monkeypatch.delenv(THREE_CORE_FLAG, raising=False)


def test_default_off_does_not_build_or_pass_callable_adapters(
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

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        _jobs()
    )

    assert payload == {"hook_status": "captured"}
    assert captured["three_core_shadow_pipeline_hook_enabled"] is False
    assert "three_core_relevance_prefilter_callable" not in captured
    assert "three_core_jd_intelligence_callable" not in captured
    assert "three_core_final_application_scoring_callable" not in captured


def test_enabled_collector_completes_three_core_shadow_outputs(
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
    assert bridge["hook_status"] == (
        "three_core_shadow_pipeline_hook_completed_shadow_only"
    )
    assert bridge["shadow_result_count"] == 3
    assert [
        result["agent_name"]
        for result in bridge["ordered_shadow_results"]
    ] == list(ORDERED_CORE_AGENT_NAMES)
    assert bridge["connection_plan_summary"][
        "connection_plan_ready"
    ] is True
    assert jobs == before


def test_enabled_collector_passes_exactly_three_callable_adapters(
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

    collector._maybe_run_shadow_sidecar_after_application_priority(
        _jobs()
    )

    callable_keys = {
        key
        for key in captured
        if key.startswith("three_core_") and key.endswith("_callable")
    }
    assert callable_keys == {
        "three_core_relevance_prefilter_callable",
        "three_core_jd_intelligence_callable",
        "three_core_final_application_scoring_callable",
    }
    assert all(callable(captured[key]) for key in callable_keys)


def test_global_sidecar_gate_prevents_adapter_and_hook_execution(
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


def test_enabled_shadow_outputs_keep_all_mutation_paths_false(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(THREE_CORE_FLAG, "true")

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        _jobs()
    )
    bridge = payload["three_core_shadow_pipeline_hook_payload"]

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
        assert bridge[key] is False
    assert all(
        value is False
        for value in bridge[
            "forbidden_mutation_and_application_paths"
        ].values()
    )


def test_collector_callable_wiring_region_has_no_forbidden_behavior():
    source = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    start = source.index(
        "            from src.agents."
        "three_core_agent_shadow_callable_adapters import"
    )
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

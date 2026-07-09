from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_hook
from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
# phase79b legacy guard marker: changes_only
# d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab
# Mechanical guard compatibility for collector protected-hash updates; does
# not widen runtime safety assertions.
GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
THREE_CORE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_SHADOW_PIPELINE_HOOK_ENABLED"
)
PIPELINE_RUN_ID = "JOB_STACK_PIPELINE_RUN_ID"
PIPELINE_BATCH_ID = "JOB_STACK_PIPELINE_BATCH_ID"


def _scored_jobs() -> list[dict]:
    return [
        {
            "id": "job-phase17c",
            "title": "AI Engineer",
            "company": "ExampleCo",
            "application_priority_score": 0.93,
            "nested": {"skills": ["python"]},
        }
    ]


def _clear_flags(monkeypatch) -> None:
    for name in (
        GLOBAL_FLAG,
        JD_FLAG,
        THREE_CORE_FLAG,
        PIPELINE_RUN_ID,
        PIPELINE_BATCH_ID,
    ):
        monkeypatch.delenv(name, raising=False)


def test_default_off_collector_path_preserves_existing_hook_payload(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(JD_FLAG, "true")
    jobs = _scored_jobs()
    before = deepcopy(jobs)

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        jobs
    )

    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert "three_core_shadow_pipeline_hook_payload" not in payload
    assert jobs == before


def test_enabled_collector_path_attaches_completed_three_core_payload(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(JD_FLAG, "true")
    monkeypatch.setenv(THREE_CORE_FLAG, "true")
    monkeypatch.setenv(PIPELINE_RUN_ID, "phase17c-run")
    monkeypatch.setenv(PIPELINE_BATCH_ID, "phase17c-batch")
    jobs = _scored_jobs()
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
    ] == [
        "relevance_prefilter",
        "jd_intelligence",
        "final_application_scoring",
    ]
    assert bridge["job_context_summary"]["source_job_context"] == {
        "run_id": "phase17c-run",
        "batch_id": "phase17c-batch",
        "job_id": "application_priority_scored_jobs",
        "stage_name": "post_final_scoring",
        "job_payload": before[0],
    }
    assert jobs == before


def test_enabled_collector_propagates_plan_flag_and_copied_context(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(THREE_CORE_FLAG, "true")
    jobs = _scored_jobs()
    before = deepcopy(jobs)
    captured = {}

    def capture_hook(**kwargs):
        captured.update(kwargs)
        kwargs["three_core_job_context"]["job_payload"]["nested"][
            "skills"
        ].append("mutated")
        return {"hook_status": "captured"}

    monkeypatch.setattr(
        shadow_sidecar_hook,
        "run_shadow_sidecar_pipeline_hook",
        capture_hook,
    )

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        jobs
    )

    assert payload == {"hook_status": "captured"}
    assert captured["three_core_shadow_pipeline_hook_enabled"] is True
    assert captured["three_core_job_context"]["run_id"] == "collector"
    assert captured["three_core_job_context"]["batch_id"] == (
        "application_priority"
    )
    assert captured["three_core_connection_plan"][
        "connection_plan_status"
    ] == (
        "three_core_shadow_pipeline_connection_plan_"
        "ready_no_pipeline_change"
    )
    assert callable(captured["three_core_relevance_prefilter_callable"])
    assert callable(captured["three_core_jd_intelligence_callable"])
    assert callable(
        captured["three_core_final_application_scoring_callable"]
    )
    assert jobs == before


def test_three_core_flag_does_not_bypass_existing_global_sidecar_gate(
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
        _scored_jobs()
    )

    assert payload is None
    assert calls == []


def test_collector_wiring_preserves_all_mutation_safety_flags(
    monkeypatch,
):
    _clear_flags(monkeypatch)
    monkeypatch.setenv(GLOBAL_FLAG, "true")
    monkeypatch.setenv(THREE_CORE_FLAG, "true")

    payload = collector._maybe_run_shadow_sidecar_after_application_priority(
        _scored_jobs()
    )

    safety = payload["safety_metadata"]
    for key in (
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_mutate_resume",
        "did_execute_application",
        "did_submit_application",
        "pipeline_wiring_added",
        "auto_apply_enabled",
    ):
        assert safety[key] is False

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


def test_collector_has_one_sidecar_call_and_no_direct_core_hook_imports():
    source = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )

    assert source.count("run_shadow_sidecar_pipeline_hook(") == 1
    assert "import three_core_agent_shadow_pipeline_hook" not in source
    assert "from src.agents.three_core_agent_shadow_pipeline_hook" not in (
        source
    )
    assert "src.agents.relevance_prefilter" not in source
    assert "src.agents.final_application_scoring" not in source


def test_new_collector_wiring_region_has_no_forbidden_behavior():
    source = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    start = source.index("        run_id = str(")
    end = source.index("        logger.info(", start)
    wiring = source[start:end].lower()

    for marker in (
        "three_core_agent_shadow_pipeline_hook",
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
        assert marker not in wiring

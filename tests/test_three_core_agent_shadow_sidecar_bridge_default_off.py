import sys
import subprocess
from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_hook
from src.agents.three_core_agent_shadow_pipeline_connection_plan import (
    build_three_core_agent_shadow_pipeline_connection_plan,
)


ROOT = Path(__file__).resolve().parents[1]
THREE_CORE_HOOK_MODULE = (
    "src.agents.three_core_agent_shadow_pipeline_hook"
)
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


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


def _sidecar_hook(**kwargs) -> dict:
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="phase17b-run",
        batch_id="phase17b-batch",
        job_id="phase17b-job",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.9,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["score_above_threshold"],
        job_payload={"job_id": "phase17b-job", "title": "AI Engineer"},
        existing_trace_context={"trace_id": "phase17b-trace"},
        **kwargs,
    )


def _assert_mutation_paths_blocked(payload: dict) -> None:
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


def test_default_off_bridge_preserves_payload_and_invokes_nothing():
    calls = []

    def supplied(request):
        calls.append(request)
        return {"unexpected": True}

    sys.modules.pop(THREE_CORE_HOOK_MODULE, None)
    baseline = _sidecar_hook()
    payload = _sidecar_hook(
        three_core_shadow_pipeline_hook_enabled=False,
        three_core_connection_plan=_ready_plan(),
        three_core_job_context={"job_id": "phase17b-job"},
        three_core_relevance_prefilter_callable=supplied,
        three_core_jd_intelligence_callable=supplied,
        three_core_final_application_scoring_callable=supplied,
    )

    assert payload == baseline
    assert calls == []
    assert THREE_CORE_HOOK_MODULE not in sys.modules
    assert "three_core_shadow_pipeline_hook_payload" not in payload


def test_enabled_bridge_attaches_payload_and_invokes_exact_order():
    calls = []

    def supplied(request):
        calls.append(deepcopy(request))
        return {"completed_agent": request["agent_name"]}

    payload = _sidecar_hook(
        three_core_shadow_pipeline_hook_enabled=True,
        three_core_connection_plan=_ready_plan(),
        three_core_job_context={"job_id": "phase17b-job"},
        three_core_relevance_prefilter_callable=supplied,
        three_core_jd_intelligence_callable=supplied,
        three_core_final_application_scoring_callable=supplied,
        three_core_hook_context={"phase": "17b"},
    )

    bridge = payload["three_core_shadow_pipeline_hook_payload"]
    assert bridge["hook_status"] == (
        "three_core_shadow_pipeline_hook_completed_shadow_only"
    )
    assert [call["agent_name"] for call in calls] == list(
        ORDERED_CORE_AGENT_NAMES
    )
    assert [
        item["agent_name"] for item in bridge["ordered_shadow_results"]
    ] == list(ORDERED_CORE_AGENT_NAMES)
    _assert_mutation_paths_blocked(payload)


def test_enabled_bridge_with_missing_callables_is_blocked():
    calls = []

    def supplied(request):
        calls.append(request)
        return {"unexpected": True}

    payload = _sidecar_hook(
        three_core_shadow_pipeline_hook_enabled=True,
        three_core_connection_plan=_ready_plan(),
        three_core_job_context={"job_id": "phase17b-job"},
        three_core_relevance_prefilter_callable=supplied,
    )

    bridge = payload["three_core_shadow_pipeline_hook_payload"]
    assert calls == []
    assert bridge["hook_status"] == (
        "three_core_shadow_pipeline_hook_blocked"
    )
    assert bridge["ordered_shadow_results"] == []
    _assert_mutation_paths_blocked(payload)


def test_callable_failure_fails_closed_and_stops_later_callables():
    calls = []

    def prefilter(request):
        calls.append(request["agent_name"])
        return {"kept": True}

    def jd(request):
        calls.append(request["agent_name"])
        raise RuntimeError("phase17b shadow failure")

    def scoring(request):
        calls.append(request["agent_name"])
        return {"unexpected": True}

    payload = _sidecar_hook(
        three_core_shadow_pipeline_hook_enabled=True,
        three_core_connection_plan=_ready_plan(),
        three_core_job_context={"job_id": "phase17b-job"},
        three_core_relevance_prefilter_callable=prefilter,
        three_core_jd_intelligence_callable=jd,
        three_core_final_application_scoring_callable=scoring,
    )

    bridge = payload["three_core_shadow_pipeline_hook_payload"]
    assert calls == ["relevance_prefilter", "jd_intelligence"]
    assert bridge["hook_status"] == (
        "three_core_shadow_pipeline_hook_failed_closed"
    )
    assert bridge["failure"]["failed_agent_name"] == "jd_intelligence"
    assert bridge["failure"]["error_type"] == "RuntimeError"
    assert bridge["shadow_result_count"] == 1
    _assert_mutation_paths_blocked(payload)


def test_bridge_inputs_are_defensively_copied_and_not_mutated():
    plan = _ready_plan()
    job = {"job_id": "phase17b-job", "nested": {"skills": ["python"]}}
    context = {"review": {"owner": "operator"}}
    before = deepcopy((plan, job, context))

    def mutating_callable(request):
        request["job_context"]["nested"]["skills"].append("changed")
        return {"request": request}

    payload = _sidecar_hook(
        three_core_shadow_pipeline_hook_enabled=True,
        three_core_connection_plan=plan,
        three_core_job_context=job,
        three_core_relevance_prefilter_callable=mutating_callable,
        three_core_jd_intelligence_callable=mutating_callable,
        three_core_final_application_scoring_callable=mutating_callable,
        three_core_hook_context=context,
    )

    assert (plan, job, context) == before
    bridge = payload["three_core_shadow_pipeline_hook_payload"]
    assert bridge["connection_plan_summary"][
        "source_connection_plan"
    ] == before[0]
    assert bridge["job_context_summary"]["source_job_context"] == before[1]
    assert bridge["hook_context_summary"]["source_hook_context"] == before[2]


def test_bridge_does_not_change_unapproved_api_service_or_static_files():
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    changed.update(
        subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )

    approved_phase17i_paths = {
        "src/app/auth_ui.py",
        "src/app/api.py",
        "src/app/planning_ui.py",
        "src/app/services.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/app/static/media/adv_diagnostics_img.svg",
        "src/app/static/shell.js",
        "src/app/ui.py",
        "src/app/ui_shell.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.css",
            "src/app/static/scan_workspace_review.css",
            "src/app/static/styles.css",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.js",
    }
    unexpected_app_changes = [
        path
        for path in changed
        if (
            path in {"src/app/api.py", "src/app/services.py"}
            or path.startswith("src/app/static/")
        )
        and path not in approved_phase17i_paths
    ]
    assert unexpected_app_changes == []


def test_new_bridge_region_has_no_forbidden_runtime_or_mutation_wiring():
    source = (
        ROOT / "src/agents/shadow_sidecar_hook.py"
    ).read_text(encoding="utf-8")
    start = source.index(
        "def _attach_three_core_shadow_pipeline_hook_payload"
    )
    end = source.index("def run_shadow_sidecar_pipeline_hook", start)
    bridge_source = source[start:end].lower()

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
        "subprocess",
        "os.getenv",
        "os.environ",
        "api_key",
        "cursor.execute(",
        ".commit(",
        "open(",
        "read_text(",
        "write_text(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in bridge_source

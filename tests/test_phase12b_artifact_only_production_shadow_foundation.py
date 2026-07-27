from __future__ import annotations

import ast
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path

import pytest

from src.agents.production_shadow_artifact_adapter import (
    ARTIFACT_FILENAMES,
    ProductionShadowAdapterError,
    project_completed_authoritative_artifacts,
)
from src.agents.production_shadow_graph import (
    PRODUCTION_SHADOW_NODE_ORDER,
    build_production_shadow_graph,
    execute_production_shadow_graph,
)
from src.agents.production_shadow_state import (
    PRODUCTION_SHADOW_STATE_VERSION,
    build_initial_production_shadow_state,
    validate_production_shadow_state,
)
from src.pipeline import post_planning_shadow as lifecycle_owner


ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _artifacts(tmp_path: Path, *, jobs: int = 1) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    output = tmp_path / "planning"
    output.mkdir()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "".join(
            json.dumps(
                {
                    "doc_id": f"job-{index}",
                    "title": "Synthetic Engineer",
                    "company": "Synthetic Co",
                    "description": "must never enter shadow state",
                }
            )
            + "\n"
            for index in range(jobs)
        ),
        encoding="utf-8",
    )
    identities = [f"job-{index}" for index in range(jobs)]
    _write_csv(
        output / ARTIFACT_FILENAMES["best_resume"],
        [
            {"job_doc_id": job, "winner_resume": f"resume-{index}"}
            for index, job in enumerate(identities)
        ],
    )
    _write_csv(
        output / ARTIFACT_FILENAMES["execution_queue"],
        [
            {
                "job_doc_id": job,
                "job_company": "Synthetic Co",
                "job_title": "Synthetic Engineer",
                "queue_rank": index + 1,
                "action": "REVIEW",
                "winner_resume": f"resume-{index}",
                "resolved_resume": f"resume-{index}",
                "requires_manual_review": "true",
                "deterministic_winner_score": "0.650000",
                "deterministic_winner_available": "true",
                "fallback_only_no_deterministic_match": "false",
                "packet_generation_allowed": "true",
                "packet_generation_block_reason": "",
            }
            for index, job in enumerate(identities)
        ],
    )
    _write_csv(
        output / ARTIFACT_FILENAMES["packet_manifest"],
        [
            {
                "job_doc_id": job,
                "packet_resume": f"resume-{index}",
                "llm_provider": "cached-provider",
                "llm_model": "cached-model",
            }
            for index, job in enumerate(identities)
        ],
    )
    _write_csv(
        output / ARTIFACT_FILENAMES["advisory_priority"],
        [
            {
                "job_id": job,
                "advisory_priority": "manual_review",
                "advisory_reason_codes": "borderline_deterministic_score",
                "existing_action": "REVIEW",
                "packet_generation_allowed": "true",
            }
            for job in identities
        ],
    )
    _write_csv(
        output / ARTIFACT_FILENAMES["tailoring_decision"],
        [
            {
                "job_id": job,
                "tailoring_decision": "manual_review_before_tailoring",
                "tailoring_reason_codes": "review_requested",
                "winner_resume": f"resume-{index}",
            }
            for index, job in enumerate(identities)
        ],
    )
    _write_csv(
        output / ARTIFACT_FILENAMES["operator_review"],
        [
            {
                "job_id": job,
                "operator_review_lane": "review_before_action",
                "operator_review_reason_codes": "operator_required",
                "winner_resume": f"resume-{index}",
                "packet_generation_allowed": "true",
            }
            for index, job in enumerate(identities)
        ],
    )
    return {
        "job_corpus": corpus,
        **{
            name: output / filename
            for name, filename in ARTIFACT_FILENAMES.items()
            if name != "job_corpus"
        },
    }


def _project(paths: dict[str, Path], job_ids: list[str] | None = None):
    return project_completed_authoritative_artifacts(
        job_ids=job_ids or ["job-0"],
        owner_user_id="owner-12b",
        pipeline_run_id="run-12b",
        context_id="context-12b",
        artifact_paths=paths,
    )


def _initial(paths: dict[str, Path]):
    return build_initial_production_shadow_state(
        _project(paths)["projections"][0]
    )


def _digests(paths: dict[str, Path]) -> dict[str, str]:
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
    }


def test_state_version_exact_safety_fields_and_prohibited_fields(tmp_path):
    state = _initial(_artifacts(tmp_path))
    assert state["graph_state_schema_version"] == PRODUCTION_SHADOW_STATE_VERSION
    assert state["read_only"] is True
    for field in (
        "authoritative",
        "provider_calls_allowed",
        "mutation_authorized",
        "application_authorized",
        "ats_authorized",
    ):
        assert state[field] is False
    for field in (
        "provider_call_count",
        "production_write_count",
        "mutation_count",
        "application_count",
        "ats_count",
    ):
        assert state[field] == 0
    for prohibited in (
        "resume_text",
        "job_description",
        "generated_tailoring_content",
        "raw_provider_output",
        "prompt",
        "reasoning",
        "credentials",
        "database_url",
        "artifact_path",
    ):
        invalid = dict(state)
        invalid[prohibited] = "secret"
        with pytest.raises(ValueError, match="(prohibited|unknown)"):
            validate_production_shadow_state(invalid)


def test_state_and_adapter_are_deep_copy_contained(tmp_path):
    paths = _artifacts(tmp_path)
    adapted = _project(paths)
    projection = adapted["projections"][0]
    state = build_initial_production_shadow_state(projection)
    state["authoritative_projection"]["queue_priority_facts"][
        "advisory_priority"
    ] = "changed"
    assert projection["queue_priority_facts"]["advisory_priority"] == (
        "manual_review"
    )


def test_adapter_projects_completed_facts_without_raw_text_or_recomputation(
    tmp_path,
):
    projection = _project(_artifacts(tmp_path))["projections"][0]
    rendered = json.dumps(projection, sort_keys=True)
    assert projection["queue_priority_facts"]["queue_rank"] == 1
    assert projection["queue_priority_facts"]["queue_action"] == "REVIEW"
    assert projection["queue_priority_facts"]["advisory_priority"] == (
        "manual_review"
    )
    assert projection["tailoring_decision_facts"]["tailoring_decision"] == (
        "manual_review_before_tailoring"
    )
    assert projection["operator_review_facts"]["operator_review_lane"] == (
        "review_before_action"
    )
    assert projection["provider_metadata"] == {
        "llm_provider": "cached-provider",
        "llm_model": "cached-model",
    }
    assert "must never enter shadow state" not in rendered
    assert "description" not in rendered


def test_unique_job_and_selected_resume_identity_fail_closed(tmp_path):
    paths = _artifacts(tmp_path, jobs=2)
    with pytest.raises(ProductionShadowAdapterError, match="duplicate_job"):
        _project(paths, ["job-0", "job-0"])
    manifest = paths["packet_manifest"]
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    rows[0]["packet_resume"] = "different-resume"
    _write_csv(manifest, rows)
    with pytest.raises(
        ProductionShadowAdapterError, match="selected_resume_conflict"
    ):
        _project(paths)


def test_partial_conflicting_and_unsafe_artifact_sets_fail_closed(tmp_path):
    paths = _artifacts(tmp_path, jobs=2)
    priority = paths["advisory_priority"]
    rows = list(csv.DictReader(priority.open(encoding="utf-8")))
    _write_csv(priority, rows[1:])
    with pytest.raises(ProductionShadowAdapterError, match="partial_artifact"):
        _project(paths)

    missing = dict(paths)
    missing.pop("operator_review")
    with pytest.raises(ProductionShadowAdapterError, match="incomplete"):
        _project(missing)

    unsafe = _artifacts(tmp_path / "second")
    symlink = tmp_path / "linked.csv"
    symlink.symlink_to(unsafe["operator_review"])
    unsafe["operator_review"] = symlink
    with pytest.raises(ProductionShadowAdapterError, match="path_unsafe"):
        _project(unsafe)
    traversed = dict(unsafe)
    traversed["operator_review"] = (
        unsafe["operator_review"].parent
        / "subdirectory"
        / ".."
        / unsafe["operator_review"].name
    )
    with pytest.raises(ProductionShadowAdapterError, match="traversal"):
        _project(traversed)


def test_graph_is_langgraph_with_deterministic_node_order(tmp_path):
    builder = build_production_shadow_graph()
    assert builder.__class__.__name__ == "StateGraph"
    result = execute_production_shadow_graph(
        job_ids=["job-0"],
        owner_user_id="owner-12b",
        pipeline_run_id="run-12b",
        context_id="context-12b",
        artifact_paths=_artifacts(tmp_path),
    )
    assert result["results"][0]["completed_node_order"] == list(
        PRODUCTION_SHADOW_NODE_ORDER
    )
    graph_source = (
        ROOT / "src/agents/production_shadow_graph.py"
    ).read_text(encoding="utf-8")
    assert "StateGraph" in graph_source
    assert ".add_node(" in graph_source


def test_execution_is_read_only_zero_activity_and_stops_for_operator(tmp_path):
    paths = _artifacts(tmp_path)
    before = _digests(paths)
    path_args = dict(paths)
    job_args = ["job-0"]
    result = execute_production_shadow_graph(
        job_ids=job_args,
        owner_user_id="owner-12b",
        pipeline_run_id="run-12b",
        context_id="context-12b",
        artifact_paths=path_args,
    )
    row = result["results"][0]
    assert result["artifacts_unchanged"] is True
    assert result["artifact_digests_before"] == result["artifact_digests_after"]
    assert _digests(paths) == before
    assert row["pending_node"] == "operator_review"
    assert row["operator_review_required"] is True
    assert row["operator_review_facts"]["operator_decision_consumed"] is False
    for scope in ("provider_call", "production_write", "mutation", "application", "ats"):
        assert result[f"{scope}_count"] == 0
        assert row[f"{scope}_count"] == 0
    assert path_args == paths
    assert job_args == ["job-0"]
    rendered = json.dumps(result)
    assert "_path" not in rendered
    assert "must never enter shadow state" not in rendered


def test_gate_off_does_no_process_graph_or_output_work(tmp_path, monkeypatch):
    monkeypatch.setattr(
        lifecycle_owner,
        "_run_shadow_command",
        lambda *_a, **_k: pytest.fail("process launched"),
    )
    lifecycle = lifecycle_owner.prepare_post_planning_shadow(
        {lifecycle_owner.PRODUCTION_SHADOW_FLAG: "true"}
    )
    assert lifecycle.enabled is False
    assert lifecycle.armed is False
    assert lifecycle.directory is None
    assert lifecycle.planning_arguments == []
    assert not list(tmp_path.iterdir())


def test_enabled_fake_lifecycle_selects_production_graph_and_old_mode_stays_old(
    tmp_path, monkeypatch
):
    paths = _artifacts(tmp_path)
    output = paths["execution_queue"].parent
    env = {
        lifecycle_owner.SHADOW_FLAG: "true",
        lifecycle_owner.PRODUCTION_SHADOW_FLAG: "true",
        "JOB_STACK_OWNER_USER_ID": "owner-12b",
        "JOB_APP_PIPELINE_RUN_ID": "run-12b",
    }
    production = lifecycle_owner.prepare_post_planning_shadow(env)
    old = lifecycle_owner.prepare_post_planning_shadow(
        {
            lifecycle_owner.SHADOW_FLAG: "true",
            "JOB_STACK_OWNER_USER_ID": "owner-12b",
            "JOB_APP_PIPELINE_RUN_ID": "run-12b",
        }
    )
    commands: list[list[str]] = []

    def fake(command):
        commands.append(command)
        return {
            "classification": "shadow_completed",
            "shadow_completed": 1,
            "shadow_parity_matches": 0,
            "shadow_parity_mismatches": 0,
        }

    monkeypatch.setattr(lifecycle_owner, "_run_shadow_command", fake)
    monkeypatch.setattr(
        "src.pipeline.runtime_status.update_counts", lambda **_counts: None
    )
    try:
        assert production.production_graph is True
        assert production.planning_arguments == []
        outcome = production.complete_after_authoritative_success(
            job_corpus_path=paths["job_corpus"],
            output_dir=output,
        )
        assert outcome["classification"] == "shadow_completed"
        assert len(commands) == 1
        assert "--production-shadow" in commands[0]
        assert "--resume-evidence" not in commands[0]
        assert old.production_graph is False
        assert "--shadow-resume-evidence-output" in old.planning_arguments
    finally:
        production.cleanup()
        old.cleanup()


def test_enabled_lifecycle_executes_real_production_shadow_worker(
    tmp_path, monkeypatch
):
    paths = _artifacts(tmp_path)
    before = _digests(paths)
    lifecycle = lifecycle_owner.prepare_post_planning_shadow(
        {
            lifecycle_owner.SHADOW_FLAG: "true",
            lifecycle_owner.PRODUCTION_SHADOW_FLAG: "true",
            "JOB_STACK_OWNER_USER_ID": "owner-12b",
            "JOB_APP_PIPELINE_RUN_ID": "run-12b",
        }
    )
    lifecycle.observation_root = tmp_path / "observations"
    monkeypatch.setattr(
        "src.pipeline.runtime_status.update_counts", lambda **_counts: None
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=paths["job_corpus"],
        output_dir=paths["execution_queue"].parent,
    )
    assert outcome["classification"] == "shadow_completed"
    assert outcome["shadow_completed"] == 1
    assert outcome["shadow_parity_matches"] == 1
    assert outcome["shadow_write_suppression_violations"] == 0
    assert _digests(paths) == before
    assert lifecycle.directory is not None
    assert not lifecycle.directory.exists()


def test_new_owners_have_no_production_provider_scraper_or_writer_imports():
    forbidden = (
        "scraper",
        "collector",
        "llm_client",
        "provider",
        "dotenv",
        "tailoring_generator",
        "database",
        "application_writer",
        "operator_review_agent",
    )
    for relative in (
        "src/agents/production_shadow_state.py",
        "src/agents/production_shadow_artifact_adapter.py",
        "src/agents/production_shadow_graph.py",
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        rendered = " ".join(imports).lower()
        assert all(token not in rendered for token in forbidden)

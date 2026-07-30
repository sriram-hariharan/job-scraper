from __future__ import annotations

import ast
from copy import deepcopy
import csv
import json
from pathlib import Path

import pytest

from src.agents.production_shadow_graph import (
    PRODUCTION_PRIORITY_OWNER_NODE,
    PRODUCTION_SHADOW_NODE_ORDER,
    execute_production_shadow_graph,
    production_shadow_node_order,
)
from src.agents.production_shadow_job_priority_owner import (
    PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION,
    invoke_job_prioritization_owner,
)
from src.pipeline import post_planning_shadow as lifecycle_owner
from src.pipeline.shadow_observation_contract import parse_observation_json
from tests.test_phase12b_artifact_only_production_shadow_foundation import (
    _artifacts,
    _digests,
    _write_csv,
)


ROOT = Path(__file__).resolve().parents[1]


def _input_facts(**overrides):
    facts = {
        "job_id": "job-0",
        "company": "Synthetic Co",
        "title": "Synthetic Engineer",
        "action": "REVIEW",
        "deterministic_winner_score": "0.650000",
        "deterministic_winner_available": "true",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
    }
    facts.update(overrides)
    return facts


def _authoritative(**overrides):
    facts = {
        "job_id": "job-0",
        "advisory_priority": "manual_review",
        "advisory_reason_codes": ["borderline_deterministic_score"],
        "existing_action": "REVIEW",
        "packet_generation_allowed": True,
    }
    facts.update(overrides)
    return facts


def _rendered(**overrides):
    row = {
        "job_id": "job-0",
        "advisory_priority": "manual_review",
        "advisory_reason_codes": "borderline_deterministic_score",
        "existing_action": "REVIEW",
        "packet_generation_allowed": "true",
    }
    row.update(overrides)
    return [row]


def test_wrapper_imports_exact_canonical_callable_without_algorithm_copy():
    source = (
        ROOT / "src/agents/production_shadow_job_priority_owner.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        (node.module, tuple(alias.name for alias in node.names))
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert (
        "src.agents.job_prioritization_agent",
        ("render_job_prioritization_recommendation_rows",),
    ) in imports
    defined = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    assert "recommend_job_priority" not in defined
    assert "write_job_prioritization_artifacts" not in source
    assert "render_tailoring_decision_rows" not in source
    assert "operator_review" not in source


def test_new_gate_defaults_off_and_does_not_import_or_invoke_renderer(
    tmp_path, monkeypatch
):
    imports: list[str] = []
    real_import = __import__

    def tracked(name, *args, **kwargs):
        if name == "src.agents.job_prioritization_agent":
            imports.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", tracked)
    assert lifecycle_owner.deterministic_owner_enabled({}) is False
    paths = _artifacts(tmp_path)
    result = execute_production_shadow_graph(
        job_ids=["job-0"],
        owner_user_id="owner-12d",
        pipeline_run_id="run-12d",
        context_id="context-12d",
        artifact_paths=paths,
    )
    row = result["results"][0]
    assert imports == []
    assert row["deterministic_owner_enabled"] is False
    assert row["deterministic_owner_status"] == "owner_not_enabled"
    assert row["deterministic_owner_invocation_count"] == 0
    assert row["completed_node_order"] == list(PRODUCTION_SHADOW_NODE_ORDER)
    assert PRODUCTION_PRIORITY_OWNER_NODE not in row["completed_node_order"]
    assert row["parity"]["parity_status"] == "passed"


def test_gate_on_invokes_exact_renderer_once_on_deep_copy(tmp_path, monkeypatch):
    from src.agents import job_prioritization_agent as canonical

    real_renderer = canonical.render_job_prioritization_recommendation_rows
    calls: list[list[dict]] = []

    def spy(rows):
        calls.append(deepcopy(rows))
        rows[0]["company"] = "renderer-local-mutation"
        return real_renderer(calls[-1])

    monkeypatch.setattr(
        canonical, "render_job_prioritization_recommendation_rows", spy
    )
    paths = _artifacts(tmp_path)
    before = _digests(paths)
    result = execute_production_shadow_graph(
        job_ids=["job-0"],
        owner_user_id="owner-12d",
        pipeline_run_id="run-12d",
        context_id="context-12d",
        artifact_paths=paths,
        deterministic_owner_enabled=True,
    )
    row = result["results"][0]
    assert len(calls) == 1
    assert calls[0][0]["company"] == "Synthetic Co"
    assert row["deterministic_owner_invocation_count"] == 1
    assert row["deterministic_owner_status"] == "owner_parity_passed"
    assert row["direct_owner_parity"]["status"] == "passed"
    assert row["rendered_priority_facts"]["advisory_priority"] == (
        "manual_review"
    )
    assert _digests(paths) == before
    assert row["completed_node_order"] == list(
        production_shadow_node_order(True)
    )
    assert row["completed_node_order"][3] == PRODUCTION_PRIORITY_OWNER_NODE


def test_wrapper_version_containment_and_incomplete_input_prevents_call():
    calls = []
    facts = _input_facts()
    authoritative = _authoritative()
    before_facts, before_authoritative = deepcopy(facts), deepcopy(authoritative)

    result = invoke_job_prioritization_owner(
        input_facts=facts,
        authoritative_priority_facts=authoritative,
        _renderer=lambda rows: calls.append(rows) or _rendered(),
    )
    assert result["wrapper_version"] == (
        PRODUCTION_SHADOW_PRIORITY_OWNER_VERSION
    )
    assert result["status"] == "owner_parity_passed"
    assert len(calls) == 1
    calls[0][0]["title"] = "changed after call"
    assert facts == before_facts
    assert authoritative == before_authoritative

    incomplete = _input_facts()
    incomplete.pop("deterministic_winner_score")
    result = invoke_job_prioritization_owner(
        input_facts=incomplete,
        authoritative_priority_facts=authoritative,
        _renderer=lambda _rows: pytest.fail("renderer invoked"),
    )
    assert result["status"] == "owner_input_incomplete"
    assert result["invocation_count"] == 0


@pytest.mark.parametrize(
    ("output", "status"),
    [
        ([], "owner_output_invalid"),
        (_rendered(job_id="different-job"), "owner_output_invalid"),
        (_rendered(advisory_priority="unknown"), "owner_output_invalid"),
        (_rendered(advisory_priority=""), "owner_invocation_completed"),
    ],
)
def test_output_validation_and_missing_rendered_fact_fail_closed(
    output, status
):
    result = invoke_job_prioritization_owner(
        input_facts=_input_facts(),
        authoritative_priority_facts=_authoritative(),
        _renderer=lambda _rows: deepcopy(output),
    )
    assert result["status"] == status
    if status == "owner_invocation_completed":
        assert result["direct_owner_parity"]["status"] == "incomplete"


def test_exception_text_is_not_retained():
    marker = "SENSITIVE_EXCEPTION_PAYLOAD"

    def fail(_rows):
        raise RuntimeError(marker)

    result = invoke_job_prioritization_owner(
        input_facts=_input_facts(),
        authoritative_priority_facts=_authoritative(),
        _renderer=fail,
    )
    assert result["status"] == "owner_invocation_failed"
    assert result["failure_code"] == "renderer_invocation_failed"
    assert marker not in json.dumps(result)


@pytest.mark.parametrize(
    ("authoritative_override", "rendered_override", "status"),
    [
        (
            {},
            {"advisory_priority": "apply_now"},
            "owner_parity_mismatch",
        ),
        (
            {},
            {"advisory_reason_codes": "different_reason"},
            "owner_parity_mismatch",
        ),
        (
            {"advisory_priority": None},
            {},
            "owner_invocation_completed",
        ),
    ],
)
def test_direct_owner_parity_mismatch_and_missing_authoritative(
    authoritative_override, rendered_override, status
):
    result = invoke_job_prioritization_owner(
        input_facts=_input_facts(),
        authoritative_priority_facts=_authoritative(
            **authoritative_override
        ),
        _renderer=lambda _rows: _rendered(**rendered_override),
    )
    assert result["status"] == status
    assert result["direct_owner_parity"]["status"] in {
        "mismatch",
        "incomplete",
    }


def test_duplicate_identity_prevents_owner_invocation(tmp_path, monkeypatch):
    from src.agents import job_prioritization_agent as canonical

    monkeypatch.setattr(
        canonical,
        "render_job_prioritization_recommendation_rows",
        lambda _rows: pytest.fail("renderer invoked"),
    )
    paths = _artifacts(tmp_path)
    queue_path = paths["execution_queue"]
    rows = list(csv.DictReader(queue_path.open(encoding="utf-8")))
    _write_csv(queue_path, [rows[0], rows[0]])
    result = execute_production_shadow_graph(
        job_ids=["job-0"],
        owner_user_id="owner-12d",
        pipeline_run_id="run-12d",
        context_id="context-12d",
        artifact_paths=paths,
        deterministic_owner_enabled=True,
    )
    assert result["results"][0]["status"] == "input_rejected"
    assert result["deterministic_owner_invocation_count"] == 0


def test_one_owner_failure_does_not_block_another_job(tmp_path, monkeypatch):
    from src.agents import job_prioritization_agent as canonical

    real_renderer = canonical.render_job_prioritization_recommendation_rows
    calls = []

    def selective(rows):
        calls.append(rows[0]["job_id"])
        if rows[0]["job_id"] == "job-0":
            raise RuntimeError("private failure")
        return real_renderer(rows)

    monkeypatch.setattr(
        canonical, "render_job_prioritization_recommendation_rows", selective
    )
    result = execute_production_shadow_graph(
        job_ids=["job-0", "job-1"],
        owner_user_id="owner-12d",
        pipeline_run_id="run-12d",
        context_id="context-12d",
        artifact_paths=_artifacts(tmp_path, jobs=2),
        deterministic_owner_enabled=True,
    )
    assert calls == ["job-0", "job-1"]
    assert [row["deterministic_owner_status"] for row in result["results"]] == [
        "owner_invocation_failed",
        "owner_parity_passed",
    ]
    assert all(row["parity"]["parity_status"] == "passed" for row in result["results"])


def test_zero_activity_counts_and_bounded_observation_summary(
    tmp_path, monkeypatch
):
    paths = _artifacts(tmp_path)
    execution = execute_production_shadow_graph(
        job_ids=["job-0"],
        owner_user_id="owner-12d",
        pipeline_run_id="run-12d",
        context_id="context-12d",
        artifact_paths=paths,
        deterministic_owner_enabled=True,
    )
    for scope in (
        "provider_call",
        "production_write",
        "mutation",
        "application",
        "ats",
    ):
        assert execution[f"{scope}_count"] == 0
    aggregate = lifecycle_owner._classify_command_payload(execution)
    aggregate.update(
        {"cleanup_categories": {}, "process_liveness_confirmed": True}
    )
    lifecycle = lifecycle_owner.prepare_post_planning_shadow(
        {
            lifecycle_owner.SHADOW_FLAG: "true",
            lifecycle_owner.PRODUCTION_SHADOW_FLAG: "true",
            lifecycle_owner.DETERMINISTIC_OWNER_FLAG: "true",
            "JOB_STACK_OWNER_USER_ID": "owner-12d",
            "JOB_APP_PIPELINE_RUN_ID": "run-12d",
        }
    )
    lifecycle.observation_root = tmp_path / "observations"
    monkeypatch.setattr(
        lifecycle_owner, "_run_shadow_command", lambda _command: aggregate
    )
    monkeypatch.setattr(
        "src.pipeline.runtime_status.update_counts", lambda **_counts: None
    )
    outcome = lifecycle.complete_after_authoritative_success(
        job_corpus_path=paths["job_corpus"],
        output_dir=paths["execution_queue"].parent,
    )
    assert outcome["observation_store_status"] == "stored"
    record = parse_observation_json(
        next(lifecycle.observation_root.glob("*.jsonl")).read_bytes()
    )
    summary = record.deterministic_owner
    assert summary == aggregate["deterministic_owner"]
    rendered = json.dumps(summary)
    assert "job-0" not in rendered
    assert "Synthetic" not in rendered
    assert "advisory_priority" not in rendered


def test_owner_flag_requires_production_shadow_and_disabled_writes_nothing(
    tmp_path,
):
    lifecycle = lifecycle_owner.prepare_post_planning_shadow(
        {lifecycle_owner.DETERMINISTIC_OWNER_FLAG: "true"}
    )
    lifecycle.observation_root = tmp_path / "observations"
    assert lifecycle.enabled is False
    assert lifecycle.deterministic_owner is False
    lifecycle.complete_after_authoritative_success(
        job_corpus_path=tmp_path / "unused",
        output_dir=tmp_path / "unused-output",
    )
    assert not lifecycle.observation_root.exists()

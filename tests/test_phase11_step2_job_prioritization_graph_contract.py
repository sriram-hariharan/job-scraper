from __future__ import annotations

import ast
from copy import deepcopy
import math
from pathlib import Path

import pytest

from src.agents import evidence_chain_langgraph_harness as evidence_harness
from src.agents import job_prioritization_agent
from src.agents import job_prioritization_graph_verification as verification


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src/agents/job_prioritization_graph_verification.py"
QUEUE_PATH = ROOT / "application_execution_queue.py"


def _row(index: int = 1, **overrides):
    row = {
        "job_doc_id": f"job-{index}",
        "job_company": f"Company {index}",
        "job_title": f"Role {index}",
        "source": "test-source",
        "action": "APPLY",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.750000",
        "winner_score": "0.750000",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
    }
    row.update(overrides)
    return row


def _execute(rows):
    return verification.execute_job_prioritization_graph_verification(
        rows=rows,
        pipeline_run_id="test-run",
        owner_user_id="test-owner",
        context_id="test-context",
        source_artifact_reference="metadata-only.csv",
    )


def test_contract_is_explicit_call_only_and_not_wired_to_application_queue():
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    queue_source = QUEUE_PATH.read_text(encoding="utf-8")

    assert "if __name__" not in module_source
    assert "os.environ" not in module_source
    assert "getenv(" not in module_source
    assert "execute_job_prioritization_graph_verification" not in queue_source

    result = _execute([_row()])
    assert result["explicit_call_only"] is True
    assert result["non_authoritative"] is True


def test_graph_has_exactly_one_named_node_and_no_finalize_or_checkpointer():
    graph = verification._build_graph()
    drawable = graph.compile().get_graph()

    assert verification.NODE_KEY == "job_prioritization"
    assert set(drawable.nodes) == {"__start__", "job_prioritization", "__end__"}
    assert {(edge.source, edge.target) for edge in drawable.edges} == {
        ("__start__", "job_prioritization"),
        ("job_prioritization", "__end__"),
    }


def test_exact_production_renderer_is_called_once(monkeypatch):
    real_renderer = job_prioritization_agent.render_job_prioritization_recommendation_rows
    calls = []

    def recording_renderer(rows):
        calls.append(deepcopy(rows))
        return real_renderer(rows)

    monkeypatch.setattr(
        verification,
        "render_job_prioritization_recommendation_rows",
        recording_renderer,
    )

    rows = [_row()]
    result = _execute(rows)

    assert calls == [rows]
    assert result["rendered_recommendation_rows"] == real_renderer(rows)


def test_graph_owner_contains_no_copied_priority_algorithm():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    forbidden = {
        "recommend_job_priority",
        "_priority_reason",
        "_priority_reason_codes",
        "_score",
        "_packet_generation_allowed",
    }

    assert not function_names.intersection(forbidden)
    assert "render_job_prioritization_recommendation_rows" in {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "src.agents.job_prioritization_agent"
        for alias in node.names
    }


@pytest.mark.parametrize("row_count", range(1, 11))
def test_one_through_ten_rows_are_accepted_in_order_without_input_mutation(row_count):
    rows = [_row(index) for index in range(row_count)]
    before = deepcopy(rows)

    result = _execute(rows)
    direct = job_prioritization_agent.render_job_prioritization_recommendation_rows(
        rows
    )

    assert result["input_row_count"] == row_count
    assert result["output_row_count"] == row_count
    assert result["rendered_recommendation_rows"] == direct
    assert [row["job_id"] for row in direct] == [
        row["job_doc_id"] for row in rows
    ]
    assert rows == before
    assert result["input_unchanged"] is True


def test_more_than_ten_rows_and_empty_rows_fail_closed():
    with pytest.raises(ValueError, match="row_count_exceeds_maximum"):
        _execute([_row(index) for index in range(11)])
    with pytest.raises(ValueError, match="rows_must_not_be_empty"):
        _execute([])


@pytest.mark.parametrize("rows", [None, {}, "rows", [_row(), "bad-row"]])
def test_invalid_row_container_or_item_types_fail_closed(rows):
    with pytest.raises(TypeError):
        _execute(rows)


@pytest.mark.parametrize(
    ("field_name", "overrides"),
    [
        ("owner_user_id", {"owner_user_id": " "}),
        ("pipeline_run_id", {"pipeline_run_id": ""}),
        ("context_id", {"context_id": None}),
    ],
)
def test_missing_identity_fields_fail_closed(field_name, overrides):
    kwargs = {
        "rows": [_row()],
        "pipeline_run_id": "test-run",
        "owner_user_id": "test-owner",
        "context_id": "test-context",
        "source_artifact_reference": "metadata-only.csv",
        **overrides,
    }

    with pytest.raises(ValueError, match=f"{field_name}_required"):
        verification.execute_job_prioritization_graph_verification(**kwargs)


def test_deterministic_inputs_have_stable_digests_and_invocation_identity():
    first = _execute([_row(1), _row(2)])
    second = _execute([_row(1), _row(2)])

    assert first["input_digest"] == second["input_digest"]
    assert first["output_digest"] == second["output_digest"]
    assert first["invocation_identity"] == second["invocation_identity"]


def test_changed_order_changes_input_digest_and_invocation_identity():
    first = _execute([_row(1), _row(2)])
    reordered = _execute([_row(2), _row(1)])

    assert first["input_digest"] != reordered["input_digest"]
    assert first["invocation_identity"] != reordered["invocation_identity"]


def test_duplicate_jobs_are_preserved():
    duplicate = _row(1)
    result = _execute([duplicate, deepcopy(duplicate)])

    assert result["input_row_count"] == 2
    assert result["output_row_count"] == 2
    assert len(result["rendered_recommendation_rows"]) == 2


@pytest.mark.parametrize(
    "unsupported",
    [
        float("nan"),
        float("inf"),
        -float("inf"),
        object(),
        {1, 2},
    ],
)
def test_non_finite_and_non_json_values_fail_closed(unsupported):
    rows = [_row(extra=unsupported)]
    expected_error = ValueError if isinstance(unsupported, float) and not math.isfinite(unsupported) else TypeError

    with pytest.raises(expected_error):
        _execute(rows)


def test_renderer_exception_propagates_once_without_retry(monkeypatch):
    calls = []

    def failing_renderer(rows):
        calls.append(rows)
        raise RuntimeError("bounded-renderer-failure")

    monkeypatch.setattr(
        verification,
        "render_job_prioritization_recommendation_rows",
        failing_renderer,
    )

    with pytest.raises(RuntimeError, match="bounded-renderer-failure"):
        _execute([_row()])
    assert len(calls) == 1


def test_result_has_complete_false_safety_declarations():
    result = _execute([_row()])
    expected_keys = {
        "authoritative_output_changed",
        "queue_mutation_performed",
        "ranking_changed",
        "selected_resume_changed",
        "production_trace_written",
        "advisory_artifact_written",
        "database_write_performed",
        "file_write_performed",
        "live_llm_call_performed",
        "durable_connection_performed",
        "checkpoint_persisted",
        "finalize_executed",
        "application_action_created",
        "application_status_changed",
        "ats_submission_performed",
        "apply_click_performed",
        "recruiter_message_sent",
        "resume_mutation_performed",
        "tailoring_mutation_performed",
        "scheduler_mutation_performed",
    }

    assert set(result["safety_metadata"]) == expected_keys
    assert all(value is False for value in result["safety_metadata"].values())
    assert result["deterministic"] is True
    assert result["read_only"] is True
    assert result["non_persistent"] is True


def test_graph_owner_has_no_write_llm_durability_or_action_imports_and_calls():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    forbidden_fragments = (
        "trace",
        "artifact",
        "database",
        "postgres",
        "checkpointer",
        "durable",
        "finalize",
        "submit",
        "application_action",
        "llm",
        "provider",
    )

    assert not any(
        fragment in name.lower()
        for name in call_names | imported_modules
        for fragment in forbidden_fragments
    )


def test_existing_six_node_evidence_graph_contract_is_unchanged():
    graph = evidence_harness._build_graph().compile().get_graph()

    assert evidence_harness.ARTIFACT_KEYS_BY_AGENT == {
        "jd_intelligence": "jd_intelligence",
        "resume_match": "resume_match_jd_evidence",
        "critic": "critic_resume_match_jd_evidence",
        "job_prioritization": "job_prioritization_critic_evidence",
        "tailoring_decision": "tailoring_decision_priority_evidence",
        "operator_review": "operator_review_tailoring_evidence",
    }
    assert {
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
        "finalize",
    }.issubset(set(graph.nodes))
    assert evidence_harness._job_prioritization_node.__name__ == (
        "_job_prioritization_node"
    )

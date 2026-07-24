from __future__ import annotations

import ast
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import multiprocessing
from pathlib import Path
import signal
import sqlite3
import sys
import threading
import time

import pytest

import application_execution_queue as queue
from src.agents import evidence_chain_langgraph_harness as evidence_harness
from src.agents import job_prioritization_agent as production
from src.agents import job_prioritization_graph_integration as integration
from src.agents import job_prioritization_graph_verification as graph_contract


ROOT = Path(__file__).resolve().parents[1]
FLAG = "APPLYLENS_DETERMINISTIC_JOB_PRIORITIZATION_GRAPH_VERIFY_ENABLED"


def _row(index: int = 1, **overrides):
    row = {
        "queue_rank": str(index),
        "job_doc_id": f"job-{index}",
        "job_company": f"Company {index}",
        "job_title": f"Role {index}",
        "source": "test-source",
        "action": "APPLY",
        "winner_resume": f"resume-{index}",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.750000",
        "winner_score": "0.750000",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
    }
    row.update(overrides)
    return row


def _enabled_env(**overrides):
    env = {
        FLAG: "1",
        "JOB_APP_PIPELINE_RUN_ID": "step3-run",
        "JOB_STACK_OWNER_USER_ID": "step3-owner",
        "APPLYLENS_AGENT_CONTEXT_ID": "step3-context",
    }
    env.update(overrides)
    return env


def _summary_from_stdout(capsys):
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    prefix = "Job prioritization graph verification: "
    assert output[0].startswith(prefix)
    return json.loads(output[0][len(prefix) :])


@pytest.fixture(autouse=True)
def _clear_process_local_duplicates():
    integration._reset_process_local_duplicate_suppression_for_tests()
    yield
    integration._reset_process_local_duplicate_suppression_for_tests()


@pytest.mark.parametrize("flag_value", [None, "", "0", "false", "no", "off"])
def test_flag_absent_or_false_preserves_default_path_without_integration_import(
    monkeypatch,
    flag_value,
    capsys,
):
    calls = []
    real_import = __import__

    def recording_import(name, *args, **kwargs):
        if name == "src.agents.job_prioritization_graph_integration":
            calls.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", recording_import)
    env = {} if flag_value is None else {FLAG: flag_value}
    rows = [_row()]
    before = deepcopy(rows)

    result = queue._with_priority_overlay(rows, env=env)

    assert calls == []
    assert rows == before
    assert result[0]["advisory_priority"] == "apply_now"
    assert capsys.readouterr().out == ""


def test_enabled_valid_request_calls_graph_once_and_reports_exact_match(
    monkeypatch,
    capsys,
):
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    real_execute = graph_contract.execute_job_prioritization_graph_verification
    calls = []

    def recording_execute(**kwargs):
        calls.append(1)
        return real_execute(**kwargs)

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        recording_execute,
    )
    rows = [_row()]
    expected = queue._with_priority_overlay(rows, env={})

    result = queue._with_priority_overlay(rows, env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert calls == [1]
    assert result == expected
    assert summary["classification"] == "matched"
    assert summary["parity_matched"] is True
    assert summary["direct_output_authoritative"] is True
    assert summary["graph_output_applied"] is False
    assert signal.getsignal(signal.SIGALRM) == previous_handler
    assert signal.getitimer(signal.ITIMER_REAL) == previous_timer


def test_mismatch_is_comparison_only_and_preserves_order_resume_and_overlay(
    monkeypatch,
    capsys,
):
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    real_execute = graph_contract.execute_job_prioritization_graph_verification

    def mismatching_execute(**kwargs):
        result = real_execute(**kwargs)
        result["rendered_recommendation_rows"][0]["advisory_priority"] = (
            "manual_review"
        )
        return result

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        mismatching_execute,
    )
    rows = [_row(1), _row(2)]
    before = deepcopy(rows)
    expected = queue._with_priority_overlay(rows, env={})

    result = queue._with_priority_overlay(rows, env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert result == expected
    assert rows == before
    assert [row["queue_rank"] for row in result] == ["1", "2"]
    assert [row["winner_resume"] for row in result] == ["resume-1", "resume-2"]
    assert summary["classification"] == "mismatch"
    assert summary["rollback_required"] is True
    assert signal.getsignal(signal.SIGALRM) == previous_handler
    assert signal.getitimer(signal.ITIMER_REAL) == previous_timer


@pytest.mark.parametrize(
    "variant",
    [
        "changed_priority",
        "reordered",
        "missing_row",
        "extra_row",
        "changed_reason_codes",
        "changed_job_identity",
        "changed_renderer_field",
        "changed_selected_resume_field",
    ],
)
def test_all_graph_output_mismatch_shapes_remain_comparison_only(
    monkeypatch,
    variant,
    capsys,
):
    rows = [_row(1), _row(2)]
    rows_before = deepcopy(rows)
    direct_rows = production.render_job_prioritization_recommendation_rows(rows)
    graph_rows = deepcopy(direct_rows)

    if variant == "changed_priority":
        graph_rows[0]["advisory_priority"] = "changed"
    elif variant == "reordered":
        graph_rows.reverse()
    elif variant == "missing_row":
        graph_rows.pop()
    elif variant == "extra_row":
        graph_rows.append(deepcopy(graph_rows[0]))
    elif variant == "changed_reason_codes":
        graph_rows[0]["advisory_reason_codes"] = "changed"
    elif variant == "changed_job_identity":
        graph_rows[0]["job_id"] = "changed"
    elif variant == "changed_renderer_field":
        graph_rows[0]["source_recommendation"] = "changed"
    else:
        graph_rows[0]["winner_resume"] = "changed"

    calls = []

    def mismatching_execute(**kwargs):
        calls.append(1)
        return {
            "completed": True,
            "rendered_recommendation_rows": deepcopy(graph_rows),
            "input_unchanged": True,
            "safety_metadata": dict(graph_contract.SAFETY_METADATA),
        }

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        mismatching_execute,
    )
    expected = queue._with_priority_overlay(rows, env={})

    result = queue._with_priority_overlay(
        rows,
        env=_enabled_env(APPLYLENS_AGENT_CONTEXT_ID=f"mismatch-{variant}"),
    )
    summary = _summary_from_stdout(capsys)

    assert calls == [1]
    assert rows == rows_before
    assert result == expected
    assert [row["queue_rank"] for row in result] == ["1", "2"]
    assert [row["winner_resume"] for row in result] == ["resume-1", "resume-2"]
    assert summary["classification"] == "mismatch"
    assert summary["output_mismatch_count"] == 1
    assert summary["rollback_required"] is True


def test_graph_nested_input_mutation_is_contained(monkeypatch, capsys):
    rows = [
        _row(
            verification_nested={
                "items": [{"value": "original"}],
            }
        )
    ]
    rows_before = deepcopy(rows)
    direct_rows = production.render_job_prioritization_recommendation_rows(rows)

    def mutating_execute(**kwargs):
        kwargs["rows"][0]["verification_nested"]["items"][0]["value"] = "changed"
        return {
            "completed": True,
            "rendered_recommendation_rows": deepcopy(direct_rows),
            "input_unchanged": False,
            "safety_metadata": dict(graph_contract.SAFETY_METADATA),
        }

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        mutating_execute,
    )
    expected = queue._with_priority_overlay(rows, env={})

    result = queue._with_priority_overlay(rows, env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert rows == rows_before
    assert result == expected
    assert summary["classification"] == "mismatch"
    assert summary["graph_input_mutation_count"] == 1
    assert summary["caller_input_mutation_count"] == 0
    assert summary["authoritative_direct_mutation_count"] == 0
    assert summary["output_mismatch_count"] == 0
    assert summary["rollback_required"] is True


def test_graph_input_mutation_followed_by_exception_is_contained(
    monkeypatch,
    capsys,
):
    rows = [_row(verification_nested={"items": ["original"]})]
    rows_before = deepcopy(rows)
    calls = []

    def mutating_exception(**kwargs):
        calls.append(1)
        kwargs["rows"][0]["verification_nested"]["items"][0] = "changed"
        raise RuntimeError("bounded-private-input-failure")

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        mutating_exception,
    )
    expected = queue._with_priority_overlay(rows, env={})

    result = queue._with_priority_overlay(rows, env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert calls == [1]
    assert rows == rows_before
    assert result == expected
    assert summary["classification"] == "exception"
    assert summary["graph_input_mutation_count"] == 1
    assert summary["rollback_required"] is True


def test_graph_input_mutation_followed_by_timeout_is_contained(
    monkeypatch,
    capsys,
):
    rows = [_row(verification_nested={"items": ["original"]})]
    rows_before = deepcopy(rows)
    calls = []

    def mutating_timeout(**kwargs):
        calls.append(1)
        kwargs["rows"][0]["verification_nested"]["items"][0] = "changed"
        time.sleep(1)

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        mutating_timeout,
    )
    monkeypatch.setattr(integration, "GRAPH_VERIFICATION_TIMEOUT_SECONDS", 0.01)
    expected = queue._with_priority_overlay(rows, env={})

    result = queue._with_priority_overlay(rows, env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert calls == [1]
    assert rows == rows_before
    assert result == expected
    assert summary["classification"] == "timeout"
    assert summary["graph_input_mutation_count"] == 1
    assert summary["rollback_required"] is True


def test_graph_exception_isolated_without_retry(monkeypatch, capsys):
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    calls = []

    def failing_execute(**kwargs):
        calls.append(1)
        raise RuntimeError("bounded-step3-failure")

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        failing_execute,
    )
    rows = [_row()]
    expected = queue._with_priority_overlay(rows, env={})

    result = queue._with_priority_overlay(rows, env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert calls == [1]
    assert result == expected
    assert summary["classification"] == "exception"
    assert summary["exception_count"] == 1
    assert signal.getsignal(signal.SIGALRM) == previous_handler
    assert signal.getitimer(signal.ITIMER_REAL) == previous_timer


def test_signal_timeout_is_safe_and_leaves_no_worker_or_child(
    monkeypatch,
    capsys,
):
    calls = []

    def blocked_execute(**kwargs):
        calls.append(1)
        time.sleep(1)
        raise AssertionError("interval timer did not interrupt")

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        blocked_execute,
    )
    monkeypatch.setattr(integration, "GRAPH_VERIFICATION_TIMEOUT_SECONDS", 0.01)
    previous_handler = signal.getsignal(signal.SIGALRM)
    threads_before = {thread.ident for thread in threading.enumerate()}
    children_before = {child.pid for child in multiprocessing.active_children()}
    expected = queue._with_priority_overlay([_row()], env={})

    result = queue._with_priority_overlay([_row()], env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert calls == [1]
    assert result == expected
    assert summary["classification"] == "timeout"
    assert summary["timeout_count"] == 1
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    assert signal.getsignal(signal.SIGALRM) == previous_handler
    assert {thread.ident for thread in threading.enumerate()} == threads_before
    assert {child.pid for child in multiprocessing.active_children()} == children_before


def test_existing_active_timer_is_preserved_without_graph_execution(
    monkeypatch,
    capsys,
):
    calls = []
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def prior_handler(signum, frame):
        del signum, frame

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        lambda **kwargs: calls.append(kwargs),
    )
    signal.signal(signal.SIGALRM, prior_handler)
    signal.setitimer(signal.ITIMER_REAL, 2.0, 0.5)
    try:
        timer_before = signal.getitimer(signal.ITIMER_REAL)
        result = queue._with_priority_overlay([_row()], env=_enabled_env())
        summary = _summary_from_stdout(capsys)
        timer_after = signal.getitimer(signal.ITIMER_REAL)

        assert result[0]["advisory_priority"] == "apply_now"
        assert calls == []
        assert summary["classification"] == "exception"
        assert signal.getsignal(signal.SIGALRM) is prior_handler
        assert timer_after[1] == timer_before[1]
        assert timer_before[0] - 0.25 <= timer_after[0] <= timer_before[0]
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def test_non_main_thread_fails_isolated_without_graph_execution(
    monkeypatch,
):
    calls = []
    outputs = []
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        lambda **kwargs: calls.append(kwargs),
    )

    def invoke():
        stream = io.StringIO()
        with redirect_stdout(stream):
            result = queue._with_priority_overlay([_row()], env=_enabled_env())
        outputs.append((result, stream.getvalue()))

    worker = threading.Thread(target=invoke)
    worker.start()
    worker.join(timeout=2)

    assert not worker.is_alive()
    assert calls == []
    assert outputs[0][0][0]["advisory_priority"] == "apply_now"
    summary = json.loads(outputs[0][1].strip().split(": ", 1)[1])
    assert summary["classification"] == "exception"
    assert signal.getsignal(signal.SIGALRM) == previous_handler
    assert signal.getitimer(signal.ITIMER_REAL) == previous_timer


def test_unsupported_posix_timer_primitives_fail_isolated(
    monkeypatch,
    capsys,
):
    calls = []
    threads_before = {thread.ident for thread in threading.enumerate()}
    children_before = {child.pid for child in multiprocessing.active_children()}
    monkeypatch.delattr(integration.signal, "SIGALRM")
    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        lambda **kwargs: calls.append(kwargs),
    )

    result = queue._with_priority_overlay([_row()], env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert result[0]["advisory_priority"] == "apply_now"
    assert calls == []
    assert summary["classification"] == "exception"
    assert {thread.ident for thread in threading.enumerate()} == threads_before
    assert {child.pid for child in multiprocessing.active_children()} == children_before


@pytest.mark.parametrize(
    "env",
    [
        _enabled_env(JOB_APP_PIPELINE_RUN_ID=""),
        _enabled_env(JOB_STACK_OWNER_USER_ID=""),
        {
            FLAG: "1",
            "JOB_APP_PIPELINE_RUN_ID": "",
            "JOB_STACK_USER_PIPELINE_RUN_ID": "",
            "JOB_STACK_OWNER_USER_ID": "owner",
        },
    ],
)
def test_invalid_identity_prevents_graph_invocation(monkeypatch, env, capsys):
    calls = []
    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        lambda **kwargs: calls.append(kwargs),
    )

    result = queue._with_priority_overlay([_row()], env=env)
    summary = _summary_from_stdout(capsys)

    assert calls == []
    assert result[0]["advisory_priority"] == "apply_now"
    assert summary["classification"] == "skipped_invalid_identity"


@pytest.mark.parametrize(
    ("rows", "expected_count"),
    [([], 0), ([_row(index) for index in range(1, 12)], 11)],
)
def test_invalid_row_bound_prevents_graph_without_truncation(
    monkeypatch,
    rows,
    expected_count,
    capsys,
):
    calls = []
    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        lambda **kwargs: calls.append(kwargs),
    )

    result = queue._with_priority_overlay(rows, env=_enabled_env())
    summary = _summary_from_stdout(capsys)

    assert calls == []
    assert len(result) == expected_count
    assert summary["classification"] == "skipped_row_bound"
    assert summary["input_row_count"] == expected_count


def test_context_fallback_uses_existing_job_priority_identity_owner(capsys):
    env = _enabled_env()
    env.pop("APPLYLENS_AGENT_CONTEXT_ID")

    queue._with_priority_overlay([_row()], env=env)
    summary = _summary_from_stdout(capsys)

    assert summary["classification"] == "matched"


def test_disabled_internal_classification_is_inert():
    before = set(integration._SEEN_INVOCATION_IDENTITIES)

    summary = (
        integration.build_disabled_job_prioritization_graph_verification_summary(
            input_row_count=7
        )
    )

    assert summary["enabled"] is False
    assert summary["attempted"] is False
    assert summary["classification"] == "skipped_disabled"
    assert summary["input_row_count"] == 7
    assert set(integration._SEEN_INVOCATION_IDENTITIES) == before


def test_duplicate_is_suppressed_but_distinct_digest_run_and_context_execute(
    monkeypatch,
    capsys,
):
    real_execute = graph_contract.execute_job_prioritization_graph_verification
    calls = []

    def recording_execute(**kwargs):
        calls.append(1)
        return real_execute(**kwargs)

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        recording_execute,
    )
    rows = [_row()]

    queue._with_priority_overlay(rows, env=_enabled_env())
    assert _summary_from_stdout(capsys)["classification"] == "matched"
    queue._with_priority_overlay(rows, env=_enabled_env())
    duplicate = _summary_from_stdout(capsys)
    queue._with_priority_overlay([_row(job_title="Changed")], env=_enabled_env())
    assert _summary_from_stdout(capsys)["classification"] == "matched"
    queue._with_priority_overlay(
        rows,
        env=_enabled_env(JOB_APP_PIPELINE_RUN_ID="different-run"),
    )
    assert _summary_from_stdout(capsys)["classification"] == "matched"
    queue._with_priority_overlay(
        rows,
        env=_enabled_env(APPLYLENS_AGENT_CONTEXT_ID="different-context"),
    )
    assert _summary_from_stdout(capsys)["classification"] == "matched"

    assert duplicate["classification"] == "duplicate_suppressed"
    assert duplicate["duplicate_suppressed_count"] == 1
    assert calls == [1, 1, 1, 1]


def test_duplicate_key_distinguishes_row_order_and_owner_and_default_off_is_inert(
    monkeypatch,
    capsys,
):
    real_execute = graph_contract.execute_job_prioritization_graph_verification
    calls = []
    direct_calls = []
    real_direct = queue.render_job_prioritization_recommendation_rows

    def recording_execute(**kwargs):
        calls.append(1)
        return real_execute(**kwargs)

    def recording_direct(rows):
        direct_calls.append(1)
        return real_direct(rows)

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        recording_execute,
    )
    monkeypatch.setattr(
        queue,
        "render_job_prioritization_recommendation_rows",
        recording_direct,
    )
    rows = [_row(1), _row(2)]

    queue._with_priority_overlay(rows, env={})
    assert capsys.readouterr().out == ""
    assert integration._SEEN_INVOCATION_IDENTITIES == set()
    queue._with_priority_overlay(rows, env=_enabled_env())
    _summary_from_stdout(capsys)
    queue._with_priority_overlay(rows, env=_enabled_env())
    assert _summary_from_stdout(capsys)["classification"] == "duplicate_suppressed"
    queue._with_priority_overlay(list(reversed(rows)), env=_enabled_env())
    _summary_from_stdout(capsys)
    queue._with_priority_overlay(
        rows,
        env=_enabled_env(JOB_STACK_OWNER_USER_ID="different-owner"),
    )
    _summary_from_stdout(capsys)

    assert calls == [1, 1, 1]
    assert direct_calls == [1, 1, 1, 1, 1]


def test_existing_artifact_trace_and_downstream_overlays_remain_direct(
    monkeypatch,
    capsys,
):
    direct_rows = production.render_job_prioritization_recommendation_rows([_row()])
    real_execute = graph_contract.execute_job_prioritization_graph_verification
    prohibited = []

    def mismatching_execute(**kwargs):
        result = real_execute(**kwargs)
        result["rendered_recommendation_rows"][0]["advisory_priority"] = (
            "skip_for_now"
        )
        return result

    monkeypatch.setattr(
        graph_contract,
        "execute_job_prioritization_graph_verification",
        mismatching_execute,
    )
    monkeypatch.setattr(
        production,
        "write_job_prioritization_artifacts",
        lambda **kwargs: prohibited.append("artifact"),
    )
    monkeypatch.setattr(
        production,
        "record_job_prioritization_agent_trace",
        lambda **kwargs: prohibited.append("trace"),
    )

    priority_overlay = queue._with_priority_overlay(
        [_row()],
        env=_enabled_env(),
    )
    _summary_from_stdout(capsys)
    tailoring_overlay = queue._with_tailoring_decision_overlay(priority_overlay)

    assert prohibited == []
    assert priority_overlay[0]["advisory_priority"] == direct_rows[0][
        "advisory_priority"
    ]
    assert tailoring_overlay[0]["advisory_priority"] == direct_rows[0][
        "advisory_priority"
    ]
    assert tailoring_overlay[0]["winner_resume"] == "resume-1"


def test_verifier_performs_no_file_or_database_write(monkeypatch, capsys):
    prohibited = []

    def blocked(*args, **kwargs):
        prohibited.append(1)
        raise AssertionError("prohibited write owner reached")

    monkeypatch.setattr(Path, "write_text", blocked)
    monkeypatch.setattr(Path, "write_bytes", blocked)
    monkeypatch.setattr(sqlite3, "connect", blocked)

    result = queue._with_priority_overlay(
        [_row()],
        env=_enabled_env(),
        source_artifact_reference="metadata-only-do-not-open",
    )
    summary = _summary_from_stdout(capsys)

    assert prohibited == []
    assert result[0]["advisory_priority"] == "apply_now"
    assert summary["safety_violation_count"] == 0


def test_integration_dependencies_exclude_llm_durable_finalize_actions_and_ats():
    path = ROOT / "src/agents/job_prioritization_graph_integration.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    forbidden = (
        "src.ai",
        "src.storage",
        "evidence_chain_langgraph_harness",
        "application_actions",
        "scheduler",
        "scraper",
        "subprocess",
        "concurrent.futures",
        "multiprocessing",
    )

    assert not any(
        marker in dependency
        for dependency in imported
        for marker in forbidden
    )
    assert integration.GRAPH_VERIFICATION_TIMEOUT_SECONDS == 5


def test_observability_summary_is_bounded_and_contains_no_identity_or_rows(
    capsys,
):
    queue._with_priority_overlay([_row()], env=_enabled_env())
    summary = _summary_from_stdout(capsys)
    encoded = json.dumps(summary, sort_keys=True)

    assert set(summary) == {
        "enabled",
        "attempted",
        "completed",
        "classification",
        "input_row_count",
        "output_row_count",
        "parity_matched",
        "timeout_count",
        "exception_count",
        "duplicate_suppressed_count",
        "elapsed_ms",
        "direct_output_authoritative",
        "graph_output_applied",
        "safety_violation_count",
        "rollback_required",
        "graph_input_mutation_count",
        "caller_input_mutation_count",
        "authoritative_direct_mutation_count",
        "output_mismatch_count",
    }
    for forbidden in (
        "owner_user_id",
        "pipeline_run_id",
        "context_id",
        "rendered_recommendation_rows",
        "winner_resume",
        "job_doc_id",
    ):
        assert forbidden not in encoded


def test_activation_reach_is_limited_to_application_queue_and_no_defaults():
    references = []
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or path.suffix not in {".py", ".env", ".json", ".toml", ".yaml", ".yml"}
        ):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if FLAG in text:
            references.append(path.relative_to(ROOT).as_posix())

    assert set(references) == {
        "application_execution_queue.py",
        "tests/test_phase11_step3_job_prioritization_graph_integration.py",
    }
    for path in (
        "main.py",
        "run_application_planning.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/config/settings.py",
        ".env",
    ):
        assert FLAG not in (ROOT / path).read_text(encoding="utf-8")


def test_existing_six_node_evidence_graph_is_unchanged():
    graph = evidence_harness._build_graph().compile().get_graph()

    assert {
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
        "finalize",
    }.issubset(set(graph.nodes))
    assert evidence_harness.ARTIFACT_KEYS_BY_AGENT["job_prioritization"] == (
        "job_prioritization_critic_evidence"
    )

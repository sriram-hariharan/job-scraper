from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.agents import evidence_chain_langgraph_harness as harness
from src.storage.durable_orchestration import (
    langgraph_postgres,
    postgres_connection,
)
from tests.test_phase9_step14_langgraph_postgres_checkpointer_foundation import (
    _package_thread_counts,
)
from tests.test_phase9_step16a_durable_decision_authorization_runtime_contract import (
    _counts,
)


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tests/support/phase9_step18b_restart_process_worker.py"
GATE = "APPLYLENS_DURABLE_ORCHESTRATION_PROCESS_RESTART_TEST_ENABLED"
REPOSITORY_TARGET = "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
SAVER_TARGET = "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_TEST_DATABASE_URL"
TIMEOUT_SECONDS = 30
MAX_OUTPUT_BYTES = 4096
TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}


def _worker_module():
    spec = importlib.util.spec_from_file_location("phase9_step18b_worker", WORKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _live_targets_or_skip(configuration):
    if str(configuration.get(GATE, "") or "").strip().lower() not in TRUE_VALUES:
        pytest.skip("dedicated_step18b_process_restart_not_enabled")
    repository_target = str(configuration.get(REPOSITORY_TARGET, "") or "").strip()
    saver_target = str(configuration.get(SAVER_TARGET, "") or "").strip()
    if not repository_target:
        pytest.skip("dedicated_step18b_repository_target_missing")
    if not saver_target:
        pytest.skip("dedicated_step18b_saver_target_missing")
    for name in (
        "DATABASE_URL",
        "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL",
        "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_DATABASE_URL",
    ):
        other = str(configuration.get(name, "") or "").strip()
        if other and other in {repository_target, saver_target}:
            pytest.fail("dedicated_step18b_target_alias_rejected")
    return repository_target, saver_target


def _child_environment(configuration):
    environment = dict(configuration)
    for name in (
        GATE,
        "DATABASE_URL",
        "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL",
        "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_DATABASE_URL",
    ):
        environment.pop(name, None)
    return environment


def _parse_child(completed, *, targets=()):
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    assert len(stdout.encode("utf-8")) <= MAX_OUTPUT_BYTES
    assert len(stderr.encode("utf-8")) <= MAX_OUTPUT_BYTES
    assert completed.returncode == 0, {
        "returncode": completed.returncode,
        "stderr_present": bool(stderr),
    }
    lines = stdout.splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert isinstance(payload, dict)
    serialized = stdout + stderr
    for target in targets:
        assert target not in serialized
    for prohibited in (
        "authorization_token_hash",
        "checkpoint_envelope",
        "raw sql",
        "select ",
        "insert ",
        "update ",
        "delete from",
        "traceback",
    ):
        assert prohibited not in serialized.lower()
    return payload


def _run_child(mode, *identities, environment, targets=()):
    command = [sys.executable, str(WORKER), mode, *identities]
    assert command[0] == sys.executable
    assert all(target not in command for target in targets)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
        shell=False,
    )
    return _parse_child(completed, targets=targets)


def test_gate_defaults_off_without_starting_a_subprocess(monkeypatch):
    called = False

    def forbidden(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess must not start")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(pytest.skip.Exception):
        _live_targets_or_skip({})
    assert called is False


@pytest.mark.parametrize(
    "configuration",
    [
        {GATE: "1", SAVER_TARGET: "dedicated-saver"},
        {GATE: "1", REPOSITORY_TARGET: "dedicated-repository"},
    ],
)
def test_missing_dedicated_target_skips_safely(configuration):
    with pytest.raises(pytest.skip.Exception):
        _live_targets_or_skip(configuration)


def test_worker_rejects_unknown_mode_and_missing_identity_without_database():
    environment = _child_environment({})
    for arguments in (("unknown", "owner"), ("resume", "owner")):
        completed = subprocess.run(
            [sys.executable, str(WORKER), *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            shell=False,
        )
        assert completed.returncode != 0
        assert len(completed.stdout.splitlines()) == 1
        payload = json.loads(completed.stdout)
        assert payload["status"] == "failed"
        assert "postgres" not in completed.stdout.lower()


def test_child_output_parser_fails_closed():
    malformed = subprocess.CompletedProcess([], 0, stdout="{}\n{}\n", stderr="")
    with pytest.raises(AssertionError):
        _parse_child(malformed)
    excessive = subprocess.CompletedProcess(
        [], 0, stdout="{}\n", stderr="x" * (MAX_OUTPUT_BYTES + 1)
    )
    with pytest.raises(AssertionError):
        _parse_child(excessive)


def test_worker_is_test_only_and_has_no_production_or_generic_target():
    source = WORKER.read_text(encoding="utf-8").lower()
    assert "resume_paused_workflow(" in source
    assert "record_human_decision(" not in source
    assert "create_resume_authorization(" not in source
    assert "consume_resume_authorization(" not in source
    assert "create_pending_finalize_attempt(" not in source
    assert "terminalize_completed_run(" not in source
    assert "subprocess.run" not in source
    assert "automatic_retry" not in source
    assert "submit_application" not in source
    assert "from src.pipeline" not in source
    assert '"database_url"' not in source


def test_live_true_process_restart_resume_replay_and_wrong_owner():
    repository_target, saver_target = _live_targets_or_skip(os.environ)
    targets = (repository_target, saver_target)
    environment = _child_environment(os.environ)
    owner = f"owner-phase9-step18b-{os.getpid()}"
    wrong_owner = f"owner-phase9-step18b-wrong-{os.getpid()}"
    worker = _worker_module()
    initial_state = worker._initial_state(owner)
    graph_id = harness._build_checkpoint_envelope(initial_state)[
        "checkpoint_identity"
    ]["graph_invocation_id"]
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=repository_target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase9-step18b-parent-readback",
    )
    unrelated_before = _counts(
        factory, owner=wrong_owner, graph_id="unrelated-step18b"
    )
    saver_unrelated_before = None
    pause = None
    try:
        _run_child(
            "cleanup",
            owner,
            graph_id,
            environment=environment,
            targets=targets,
        )
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase9-step18b-parent-before",
        ) as saver:
            saver_unrelated_before = _package_thread_counts(
                saver.conn, excluded_thread_id=graph_id
            )

        pause = _run_child(
            "pause", owner, environment=environment, targets=targets
        )
        assert pause["status"] == "durable_pause_created"
        assert pause["classification"] == "applied"
        assert pause["graph_invocation_id"] == graph_id
        assert pause["evidence_nodes_executed"] == 6
        assert pause["finalize_nodes_executed"] == 0
        process_a_pid = pause["pid"]

        between = _run_child(
            "inspect",
            owner,
            graph_id,
            pause["repository_checkpoint_id"],
            environment=environment,
            targets=targets,
        )
        assert between["pid"] != process_a_pid
        assert between["run_status"] == "awaiting_decision"
        assert between["pending_finalize"] is True
        assert between["completed_evidence_count"] == 6
        assert between["final_bundle_present"] is False
        assert between["final_trace_present"] is False
        assert between["decision_count"] == 0
        assert between["authorization_count"] == 0
        assert between["consumption_count"] == 0

        resumed = _run_child(
            "resume",
            owner,
            graph_id,
            pause["repository_checkpoint_id"],
            pause["interrupt_request_id"],
            environment=environment,
            targets=targets,
        )
        process_b_pid = resumed["pid"]
        assert process_b_pid != process_a_pid
        assert resumed["status"] == "resume_completed"
        assert resumed["classification"] == "applied"
        assert resumed["evidence_nodes_executed"] == 0
        assert resumed["finalize_nodes_executed"] == 1

        completed = _run_child(
            "inspect",
            owner,
            graph_id,
            resumed["repository_checkpoint_id"],
            environment=environment,
            targets=targets,
        )
        assert completed["run_status"] == "completed"
        assert completed["pending_node_count"] == 0
        assert completed["final_bundle_present"] is True
        assert completed["final_trace_present"] is True
        assert completed["authorization_count"] == 1
        assert completed["consumption_count"] == 1
        assert completed["attempt_count"] == 1
        assert completed["checkpoint_count"] == 2
        assert completed["terminal_count"] == 1

        replay = _run_child(
            "replay",
            owner,
            graph_id,
            pause["repository_checkpoint_id"],
            pause["interrupt_request_id"],
            environment=environment,
            targets=targets,
        )
        assert replay["pid"] not in {process_a_pid, process_b_pid}
        assert replay["status"] == "already_completed"
        assert replay["evidence_nodes_executed"] == 0
        assert replay["finalize_nodes_executed"] == 0

        wrong = _run_child(
            "wrong-owner",
            wrong_owner,
            graph_id,
            pause["repository_checkpoint_id"],
            pause["interrupt_request_id"],
            environment=environment,
            targets=targets,
        )
        assert wrong["classification"] == "not_found"
        assert wrong["graph_invocation_id"] == graph_id
        assert wrong["evidence_nodes_executed"] == 0
        assert wrong["finalize_nodes_executed"] == 0

        after = _run_child(
            "inspect",
            owner,
            graph_id,
            resumed["repository_checkpoint_id"],
            environment=environment,
            targets=targets,
        )
        assert {
            key: after[key]
            for key in (
                "authorization_count",
                "consumption_count",
                "attempt_count",
                "checkpoint_count",
                "terminal_count",
            )
        } == {
            "authorization_count": 1,
            "consumption_count": 1,
            "attempt_count": 1,
            "checkpoint_count": 2,
            "terminal_count": 1,
        }
    finally:
        cleanup = _run_child(
            "cleanup",
            owner,
            graph_id,
            environment=environment,
            targets=targets,
        )
        assert cleanup["remaining_repository_rows"] == 0
        assert _counts(
            factory, owner=wrong_owner, graph_id="unrelated-step18b"
        ) == unrelated_before
        if saver_unrelated_before is not None:
            with langgraph_postgres.open_langgraph_postgres_saver(
                enabled=True,
                database_url=saver_target,
                application_name="applylens-phase9-step18b-parent-after",
            ) as saver:
                assert _package_thread_counts(
                    saver.conn, excluded_thread_id=graph_id
                ) == saver_unrelated_before

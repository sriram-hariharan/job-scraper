from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from src.pipeline import post_planning_shadow as shadow


pytestmark = pytest.mark.skipif(
    os.name != "posix",
    reason="controlled shadow process-group proof supports macOS/POSIX only",
)


def _payload() -> dict:
    return {
        "execution_version": shadow.SHADOW_EXECUTION_VERSION,
        "status": "completed",
        "job_count": 1,
        "artifacts_unchanged": True,
        "results": [
            {
                "job_id": "synthetic-job",
                "status": "parity_completed",
                "shadow_facts": {
                    "pending_node": "finalize",
                    "finalization_executed": False,
                    "final_bundle_present": False,
                    "final_trace_present": False,
                    "completed_node_order": list(shadow._EXPECTED_NODES),
                    "graph_latency_ms": 1,
                },
                "parity": {
                    "contract_version": shadow.SHADOW_PARITY_VERSION,
                    "overall_classification": "match",
                    "field_results": [],
                },
            }
        ],
    }


def _pid_live(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def test_normal_child_exit_is_reaped_and_liveness_confirmed():
    result = shadow._run_shadow_command(
        [sys.executable, "-c", f"print({json.dumps(json.dumps(_payload()))})"]
    )
    assert result["classification"] == "shadow_completed", result
    assert result["process_liveness_confirmed"] is True
    assert result["cleanup_categories"] == {}


def test_timeout_with_cooperative_sigterm_is_bounded(monkeypatch):
    monkeypatch.setattr(shadow, "SHADOW_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(shadow, "PROCESS_STOP_WAIT_SECONDS", 1.0)
    program = (
        "import signal,time;"
        "signal.signal(signal.SIGTERM,lambda *_:raise_exit());"
        "raise_exit=lambda:None;"
        "time.sleep(10)"
    )
    # Use the default SIGTERM behavior; it is the cooperative bounded case.
    program = "import time; time.sleep(10)"
    started = time.monotonic()
    result = shadow._run_shadow_command([sys.executable, "-c", program])
    assert result["classification"] == "shadow_timeout"
    assert result["process_liveness_confirmed"] is True
    assert time.monotonic() - started < 2


def test_sigterm_ignoring_child_requires_sigkill(monkeypatch):
    monkeypatch.setattr(shadow, "SHADOW_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(shadow, "PROCESS_STOP_WAIT_SECONDS", 0.1)
    sent = []
    original = os.killpg

    def tracked(group, requested_signal):
        sent.append(requested_signal)
        return original(group, requested_signal)

    monkeypatch.setattr(os, "killpg", tracked)
    result = shadow._run_shadow_command(
        [
            sys.executable,
            "-c",
            "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(10)",
        ]
    )
    assert result["classification"] == "shadow_timeout"
    assert signal.SIGTERM in sent
    assert signal.SIGKILL in sent
    assert result["process_liveness_confirmed"] is True


def test_descendant_in_owned_group_is_stopped_without_global_process_listing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(shadow, "SHADOW_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(shadow, "PROCESS_STOP_WAIT_SECONDS", 0.5)
    pid_file = tmp_path / "descendant.pid"
    program = (
        "import signal,subprocess,sys,time;"
        f"p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
        f"open({str(pid_file)!r},'w').write(str(p.pid));"
        "stop=lambda *_:(p.wait(),sys.exit(0));"
        "signal.signal(signal.SIGTERM,stop);"
        "time.sleep(10)"
    )
    result = shadow._run_shadow_command([sys.executable, "-c", program])
    descendant_pid = int(pid_file.read_text())
    assert result["classification"] == "shadow_timeout", result
    assert result["process_liveness_confirmed"] is True
    deadline = time.monotonic() + 1
    while _pid_live(descendant_pid) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not _pid_live(descendant_pid)
    source = Path(shadow.__file__).read_text(encoding="utf-8")
    assert "psutil" not in source
    assert "ps aux" not in source


def test_direct_child_is_reaped_and_exact_group_is_gone(monkeypatch):
    monkeypatch.setattr(shadow, "PROCESS_STOP_WAIT_SECONDS", 0.2)
    process = subprocess.Popen(
        [sys.executable, "-c", "import time;time.sleep(10)"],
        start_new_session=True,
    )
    pid = process.pid
    result = shadow._stop_process_group(
        process, owned_process_group_id=pid
    )
    assert result.process_liveness_confirmed is True
    assert process.returncode is not None
    assert not _pid_live(pid)
    assert shadow._process_group_live(pid) is False


def test_unconfirmed_liveness_is_bounded_safety_result(monkeypatch):
    monkeypatch.setattr(shadow, "SHADOW_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(shadow, "PROCESS_STOP_WAIT_SECONDS", 0.05)
    monkeypatch.setattr(shadow, "_process_group_live", lambda _group: None)
    result = shadow._run_shadow_command(
        [sys.executable, "-c", "print('{}')"]
    )
    assert result["classification"] == "shadow_safety_violation"
    assert result["process_liveness_confirmed"] is False
    assert "process_liveness_unconfirmed" in result["cleanup_categories"]


class _FakeProcess:
    pid = 43210
    returncode = None

    def __init__(self, *, wait_timeouts=0):
        self.wait_timeouts = wait_timeouts
        self.terminate_calls = 0
        self.kill_calls = 0

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if self.wait_timeouts:
            self.wait_timeouts -= 1
            raise subprocess.TimeoutExpired("synthetic", timeout)
        self.returncode = -9
        return self.returncode

    def terminate(self):
        self.terminate_calls += 1

    def kill(self):
        self.kill_calls += 1


def test_terminate_kill_and_wait_failures_have_only_bounded_categories(
    monkeypatch,
):
    process = _FakeProcess(wait_timeouts=2)
    calls = []

    def failed_killpg(_group, requested_signal):
        calls.append(requested_signal)
        raise OSError("SENSITIVE_PATH")

    monkeypatch.setattr(os, "killpg", failed_killpg)
    monkeypatch.setattr(shadow, "_process_group_live", lambda _group: True)
    monkeypatch.setattr(
        shadow, "_wait_for_process_group_exit", lambda *_args: False
    )
    result = shadow._stop_process_group(
        process, owned_process_group_id=process.pid
    )
    assert "process_terminate_failed" in result.categories
    assert "process_kill_failed" in result.categories
    assert "process_wait_or_drain_failed" in result.categories
    assert "SENSITIVE_PATH" not in repr(result.categories)
    assert calls.count(signal.SIGTERM) == 1
    assert calls.count(signal.SIGKILL) == 1


def test_temporary_cleanup_failure_and_target_rejection_are_visible(
    tmp_path, monkeypatch
):
    owned = tmp_path / "applylens_post_planning_shadow_synthetic"
    owned.mkdir()
    (owned / "evidence.json").write_text("synthetic")
    lifecycle = shadow.PostPlanningShadowLifecycle(
        enabled=True, armed=True, directory=owned
    )
    original = Path.unlink

    def fail_owned(path, *args, **kwargs):
        if path.name == "evidence.json":
            raise PermissionError("SENSITIVE_PATH")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_owned)
    result = lifecycle.cleanup()
    assert result.categories["temporary_cleanup_failed"] >= 1
    assert "SENSITIVE_PATH" not in repr(result.categories)

    unowned = shadow.PostPlanningShadowLifecycle(
        enabled=True, armed=True, directory=tmp_path
    )
    rejected = unowned.cleanup()
    assert rejected.categories == {"cleanup_target_rejected": 1}


def test_unresolved_group_is_never_targeted(monkeypatch):
    process = _FakeProcess()
    targeted = []
    monkeypatch.setattr(
        os, "killpg", lambda *_args: targeted.append(_args)
    )
    result = shadow._stop_process_group(
        process, owned_process_group_id=None
    )
    assert targeted == []
    assert result.process_liveness_confirmed is None
    assert result.categories["process_liveness_unconfirmed"] == 1

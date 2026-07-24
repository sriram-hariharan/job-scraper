from __future__ import annotations

from dataclasses import dataclass
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.agents import durable_evidence_chain_resume_coordinator as coordinator_module
from src.agents.durable_evidence_chain_resume_coordinator import (
    DurableEvidenceChainResumeCoordinator,
)


OWNER = "owner-step18a"
GRAPH_ID = "graph-step18a"
CHECKPOINT_ID = "checkpoint-step18a"
INTERRUPT_ID = "interrupt-step18a"
THREAD_ID = "thread-step18a"
PACKAGE_PAUSE_ID = "package-pause-step18a"
PACKAGE_FINAL_ID = "package-final-step18a"
TOKEN_HASH = "7" * 64
NOW = "2026-07-25T12:00:00Z"


@dataclass
class _Result:
    classification: str = "applied"
    record: dict | None = None


class _Graph:
    def __init__(self, operations):
        self.operations = operations
        self.invoked = False

    def get_state(self, _config):
        checkpoint_id = PACKAGE_FINAL_ID if self.invoked else PACKAGE_PAUSE_ID
        return SimpleNamespace(
            values={
                "artifacts": (
                    {
                        "agent_evidence_chain_bundle": {"status": "complete"},
                        "agent_evidence_chain_trace_payload": {"status": "complete"},
                    }
                    if self.invoked
                    else {}
                )
            },
            next=() if self.invoked else ("finalize",),
            config={
                "configurable": {
                    "thread_id": THREAD_ID,
                    "checkpoint_ns": "",
                    "checkpoint_id": checkpoint_id,
                }
            },
        )

    def invoke(self, value, _config):
        assert value is None
        self.operations.append("graph_invoke")
        self.invoked = True
        return self.get_state({}).values


class _Repository:
    def __init__(self, operations, *, fail_at=""):
        self.operations = operations
        self.fail_at = fail_at
        self.run_status = "awaiting_decision"

    def _write(self, name, record=None):
        self.operations.append(name)
        if name == self.fail_at:
            return _Result("stale_state")
        if name == "create_attempt":
            self.run_status = "resumed"
        if name == "terminalize":
            self.run_status = "completed"
        return _Result("applied", record or {})

    def read_graph_run(self, **_):
        return _Result(
            record={
                "run_status": self.run_status,
                "current_checkpoint_id": (
                    "final-checkpoint-step18a"
                    if self.run_status == "completed"
                    else CHECKPOINT_ID
                ),
            }
        )

    def read_current_checkpoint(self, **_):
        return _Result(record={"checkpoint_id": CHECKPOINT_ID})

    def read_pending_interrupt(self, **_):
        return _Result(record={"interrupt_request_id": INTERRUPT_ID})

    def read_checkpoint_binding(self, **_):
        return _Result(
            record={
                "event_payload_json": {
                    "binding_schema_version": (
                        coordinator_module.store
                        .LANGGRAPH_CHECKPOINT_BINDING_SCHEMA_VERSION
                    ),
                    "graph_invocation_id": GRAPH_ID,
                    "repository_checkpoint_id": CHECKPOINT_ID,
                    "langgraph_thread_id": THREAD_ID,
                    "langgraph_checkpoint_namespace": "",
                    "langgraph_checkpoint_id": PACKAGE_PAUSE_ID,
                }
            }
        )

    def record_human_decision(self, row):
        return self._write("record_decision", row)

    def read_current_human_decision(self, **_):
        return _Result(
            record={
                "decision_id": "decision-step18a",
                "decision_value": "continue_read_only",
            }
        )

    def create_resume_authorization(self, row, **_):
        return self._write("create_authorization", row)

    def consume_resume_authorization(self, row, **_):
        return self._write("consume_authorization", row)

    def read_resume_authorization(self, **_):
        return _Result(record={"authorization_status": "consumed"})

    def read_resume_consumption(self, **_):
        return _Result(
            record={
                "consumption_id": "consumption-step18a",
                "checkpoint_id": CHECKPOINT_ID,
                "interrupt_request_id": INTERRUPT_ID,
                "resume_invocation_id": "resume-step18a",
            }
        )

    def create_pending_finalize_attempt(self, *_args, **_kwargs):
        return self._write("create_attempt")

    def claim_attempt(self, row, *_args, **_kwargs):
        return self._write("claim_attempt", {**row, "attempt_status": "claimed"})

    def read_attempt(self, **_):
        return _Result(
            record={
                "node_attempt_id": "attempt-step18a",
                "attempt_status": "claimed",
                "lease_owner_id": "worker-step18a",
                "node_key": "finalize",
                "lock_version": 1,
            }
        )

    def commit_final_checkpoint(self, *_args, **_kwargs):
        return self._write("commit_final_checkpoint")

    def commit_checkpoint_binding(self, *_args, **_kwargs):
        return self._write("commit_final_binding")

    def record_attempt_success(self, *_args, **_kwargs):
        return self._write(
            "record_attempt_success",
            {"attempt_status": "succeeded", "node_key": "finalize"},
        )

    def terminalize_completed_run(self, *_args, **_kwargs):
        return self._write("terminalize")

    def read_terminal_result(self, **_):
        return _Result(record={"terminal_result_id": "terminal-step18a"})


def _install_builders(monkeypatch):
    monkeypatch.setattr(
        DurableEvidenceChainResumeCoordinator,
        "_validate_snapshot",
        staticmethod(lambda snapshot, **_: snapshot.values),
    )
    monkeypatch.setattr(
        coordinator_module.harness,
        "_build_checkpoint_envelope",
        lambda _state: {
            "checkpoint_identity": {
                "owner_user_id": OWNER,
                "graph_invocation_id": GRAPH_ID,
            }
        },
    )
    monkeypatch.setattr(
        coordinator_module.harness,
        "_build_operator_review_interrupt_request",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        coordinator_module.harness,
        "_checkpoint_digest",
        lambda _value: "d" * 64,
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_checkpoint_row",
        lambda *_args, **_kwargs: {
            "checkpoint_id": CHECKPOINT_ID,
            "checkpoint_envelope_digest": "a" * 64,
        },
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_interrupt_request_row",
        lambda *_args, **_kwargs: {"interrupt_request_id": INTERRUPT_ID},
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_graph_run_row",
        lambda *_args, **_kwargs: {
            "owner_user_id": OWNER,
            "graph_invocation_id": GRAPH_ID,
        },
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_human_decision_row",
        lambda *_args, **_kwargs: {"decision_id": "decision-step18a"},
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_resume_authorization_row",
        lambda *_args, **_kwargs: {"authorization_id": "authorization-step18a"},
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_resume_consumption_row",
        lambda *_args, **_kwargs: {"consumption_id": "consumption-step18a"},
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_node_attempt_row",
        lambda *_args, **_kwargs: {"node_attempt_id": "attempt-step18a"},
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_lifecycle_event_row",
        lambda *_args, **_kwargs: {"event_id": "event-step18a"},
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_final_checkpoint_row",
        lambda *_args, **_kwargs: {
            "checkpoint_id": "final-checkpoint-step18a",
            "checkpoint_envelope_digest": "f" * 64,
        },
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_langgraph_checkpoint_binding_row",
        lambda *_args, **_kwargs: {"binding": "final"},
    )
    monkeypatch.setattr(
        coordinator_module.store,
        "prepare_terminal_result_row",
        lambda *_args, **_kwargs: {"terminal_result_id": "terminal-step18a"},
    )


def _resume(repository, graph):
    coordinator = DurableEvidenceChainResumeCoordinator(
        repository=repository, saver=object(), graph=graph, enabled=True
    )
    return coordinator.resume_paused_workflow(
        owner_user_id=OWNER,
        graph_invocation_id=GRAPH_ID,
        repository_checkpoint_id=CHECKPOINT_ID,
        interrupt_request_id=INTERRUPT_ID,
        actor_id="actor-step18a",
        client_idempotency_key="client-step18a",
        decision_reason="approved read-only continuation",
        authorization_token_hash=TOKEN_HASH,
        consumer_instance_id="worker-step18a",
        created_at=NOW,
        authorization_expires_at="2026-07-25T13:00:00Z",
        lease_acquired_at="2026-07-25T12:05:00Z",
        lease_expires_at="2026-07-25T12:15:00Z",
        completed_at="2026-07-25T12:10:00Z",
        duration_ms=300_000,
    )


def test_coordinator_owns_complete_ordered_resume_boundary(monkeypatch):
    _install_builders(monkeypatch)
    operations = []
    result = _resume(_Repository(operations), _Graph(operations))
    assert result.status == "resume_completed"
    assert operations == [
        "record_decision",
        "create_authorization",
        "consume_authorization",
        "create_attempt",
        "claim_attempt",
        "graph_invoke",
        "commit_final_checkpoint",
        "commit_final_binding",
        "record_attempt_success",
        "terminalize",
    ]
    serialized = repr(result)
    for secret in (TOKEN_HASH, "postgresql://", "SELECT ", "artifacts"):
        assert secret not in serialized


@pytest.mark.parametrize(
    "failure,forbidden",
    [
        ("record_decision", "create_authorization"),
        ("create_authorization", "consume_authorization"),
        ("consume_authorization", "create_attempt"),
        ("create_attempt", "claim_attempt"),
        ("claim_attempt", "graph_invoke"),
        ("commit_final_checkpoint", "commit_final_binding"),
        ("commit_final_binding", "record_attempt_success"),
        ("record_attempt_success", "terminalize"),
    ],
)
def test_failure_stops_every_later_stage(monkeypatch, failure, forbidden):
    _install_builders(monkeypatch)
    operations = []
    result = _resume(
        _Repository(operations, fail_at=failure), _Graph(operations)
    )
    assert result.classification in {"stale_state", "reconciliation_required"}
    assert forbidden not in operations


def test_replay_and_wrong_owner_fail_before_graph_invocation(monkeypatch):
    _install_builders(monkeypatch)
    for classification, status in (
        ("applied", "completed"),
        ("not_found", "missing"),
    ):
        operations = []
        repository = _Repository(operations)
        if status == "completed":
            repository.run_status = "completed"
        else:
            repository.read_graph_run = lambda **_: _Result(classification)
        graph = _Graph(operations)
        result = _resume(repository, graph)
        assert result.classification in {"already_completed", "not_found"}
        assert "graph_invoke" not in operations


def test_public_boundary_has_no_callback_or_arbitrary_node():
    signature = inspect.signature(
        DurableEvidenceChainResumeCoordinator.resume_paused_workflow
    )
    assert "persist_final_state" not in signature.parameters
    assert "node_key" not in signature.parameters
    source = Path(coordinator_module.__file__).read_text(encoding="utf-8")
    for prohibited in (
        "os.environ",
        "getenv(",
        "DATABASE_URL",
        "automatic_retry",
        "application_action",
        "submit_application",
        "from src.pipeline",
        "llm",
    ):
        assert prohibited not in source.lower()

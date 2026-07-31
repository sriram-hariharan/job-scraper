from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import inspect

from langgraph.checkpoint.memory import MemorySaver
import pytest

import generate_tailoring_suggestions as caller
from src.agents import production_human_checkpoint_coordinator as coordinator
from src.storage.durable_orchestration import production


NOW = "2026-07-30T12:00:00Z"
EXPIRES = "2026-07-30T13:00:00Z"
TOKEN = "phase20-one-time-secret"
OWNER = "owner-phase20"


@dataclass
class _Result:
    classification: str
    record: dict | None = None


class _Repository:
    def __init__(self):
        self.runs = {}
        self.checkpoints = {}
        self.interrupts = {}
        self.bindings = {}
        self.decisions = {}
        self.authorizations = {}
        self.consumptions = {}
        self.attempts = {}
        self.terminals = {}

    def read_graph_run(self, *, owner_user_id, graph_invocation_id):
        row = self.runs.get(graph_invocation_id)
        if row is None or row["owner_user_id"] != owner_user_id:
            return _Result("not_found")
        return _Result("applied", deepcopy(row))

    def create_production_graph_run(self, row):
        existing = self.runs.get(row["graph_invocation_id"])
        if existing is not None:
            return _Result(
                "idempotent_existing"
                if existing == row
                else "duplicate_conflict",
                deepcopy(existing),
            )
        self.runs[row["graph_invocation_id"]] = deepcopy(row)
        return _Result("applied", deepcopy(row))

    def commit_checkpoint_interrupt(
        self, *, checkpoint_row, interrupt_row, **kwargs
    ):
        run = self.runs[checkpoint_row["graph_invocation_id"]]
        if (
            run["run_status"] != kwargs["expected_run_status"]
            or run["lock_version"] != kwargs["expected_lock_version"]
        ):
            return _Result("stale_state")
        self.checkpoints[checkpoint_row["checkpoint_id"]] = deepcopy(
            checkpoint_row
        )
        self.interrupts[interrupt_row["interrupt_request_id"]] = deepcopy(
            interrupt_row
        )
        run.update(
            {
                "run_status": "awaiting_decision",
                "current_checkpoint_id": checkpoint_row["checkpoint_id"],
                "lock_version": 1,
            }
        )
        return _Result("applied", deepcopy(run))

    def commit_checkpoint_binding(self, row):
        key = (row["graph_invocation_id"], row["checkpoint_id"])
        existing = self.bindings.get(key)
        if existing is not None:
            return _Result(
                "idempotent_existing"
                if existing == row
                else "duplicate_conflict",
                deepcopy(existing),
            )
        self.bindings[key] = deepcopy(row)
        return _Result("applied", deepcopy(row))

    def read_checkpoint_binding(
        self, *, owner_user_id, graph_invocation_id,
        repository_checkpoint_id
    ):
        row = self.bindings.get(
            (graph_invocation_id, repository_checkpoint_id)
        )
        if row is None or row["owner_user_id"] != owner_user_id:
            return _Result("not_found")
        return _Result("applied", deepcopy(row))

    def read_checkpoint_by_id(
        self, *, owner_user_id, graph_invocation_id, checkpoint_id
    ):
        row = self.checkpoints.get(checkpoint_id)
        if (
            row is None
            or row["owner_user_id"] != owner_user_id
            or row["graph_invocation_id"] != graph_invocation_id
        ):
            return _Result("not_found")
        return _Result("applied", deepcopy(row))

    def read_pending_interrupt(
        self, *, owner_user_id, graph_invocation_id
    ):
        for row in self.interrupts.values():
            if (
                row["owner_user_id"] == owner_user_id
                and row["graph_invocation_id"] == graph_invocation_id
                and row["interrupt_status"] == "awaiting_decision"
            ):
                return _Result("applied", deepcopy(row))
        return _Result("not_found")

    def read_pending_interrupt_full(
        self, *, owner_user_id, graph_invocation_id
    ):
        return self.read_pending_interrupt(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )

    def record_human_decision(self, row):
        for existing in self.decisions.values():
            if existing["interrupt_request_id"] == row[
                "interrupt_request_id"
            ]:
                return _Result(
                    "idempotent_existing"
                    if existing == row
                    else "duplicate_conflict",
                    deepcopy(existing),
                )
        self.decisions[row["decision_id"]] = deepcopy(row)
        run = self.runs[row["graph_invocation_id"]]
        interrupt = self.interrupts[row["interrupt_request_id"]]
        status = {
            "continue_read_only": "decision_recorded",
            "needs_revision": "decision_rejected",
            "cancel": "cancelled",
        }[row["decision_value"]]
        run.update({"run_status": status, "lock_version": 2})
        interrupt.update(
            {"interrupt_status": status, "lock_version": 1}
        )
        return _Result("applied", deepcopy(row))

    def read_current_human_decision(
        self, *, owner_user_id, interrupt_request_id
    ):
        for row in self.decisions.values():
            if (
                row["owner_user_id"] == owner_user_id
                and row["interrupt_request_id"] == interrupt_request_id
            ):
                return _Result("applied", deepcopy(row))
        return _Result("not_found")

    def create_resume_authorization(
        self, row, *, expected_run_lock_version, expected_interrupt_version
    ):
        existing = self.authorizations.get(row["decision_id"])
        if existing is not None:
            return _Result(
                "idempotent_existing"
                if existing == row
                else "duplicate_conflict",
                {
                    key: deepcopy(value)
                    for key, value in existing.items()
                    if key != "authorization_token_hash"
                },
            )
        self.authorizations[row["decision_id"]] = deepcopy(row)
        run = self.runs[row["graph_invocation_id"]]
        interrupt = self.interrupts[row["interrupt_request_id"]]
        assert run["lock_version"] == expected_run_lock_version
        assert interrupt["lock_version"] == expected_interrupt_version
        run.update({"run_status": "resume_authorized", "lock_version": 3})
        interrupt.update(
            {"interrupt_status": "resume_authorized", "lock_version": 2}
        )
        return _Result(
            "applied",
            {
                key: deepcopy(value)
                for key, value in row.items()
                if key != "authorization_token_hash"
            },
        )

    def read_resume_authorization(self, *, owner_user_id, decision_id):
        row = self.authorizations.get(decision_id)
        if row is None or row["owner_user_id"] != owner_user_id:
            return _Result("not_found")
        return _Result(
            "applied",
            {
                key: deepcopy(value)
                for key, value in row.items()
                if key != "authorization_token_hash"
            },
        )

    def consume_resume_authorization(
        self, row, *, authorization_token_hash, **_
    ):
        authorization = self.authorizations.get(row["decision_id"])
        if authorization is None:
            return _Result("not_found")
        if (
            authorization["authorization_token_hash"]
            != authorization_token_hash
        ):
            return _Result("stale_state")
        if authorization["expires_at"] <= row["claimed_at"]:
            return _Result("stale_state")
        existing = self.consumptions.get(row["authorization_id"])
        persisted = {
            key: deepcopy(value)
            for key, value in row.items()
            if key != "authorization_token_hash_proof"
        }
        if existing is not None:
            return _Result(
                "idempotent_existing"
                if existing == persisted
                else "duplicate_conflict",
                deepcopy(existing),
            )
        self.consumptions[row["authorization_id"]] = persisted
        authorization.update(
            {"authorization_status": "consumed", "lock_version": 1}
        )
        self.runs[row["graph_invocation_id"]].update(
            {"run_status": "resume_consumed", "lock_version": 4}
        )
        self.interrupts[row["interrupt_request_id"]].update(
            {"interrupt_status": "resume_consumed", "lock_version": 3}
        )
        return _Result("applied", deepcopy(persisted))

    def create_pending_finalize_attempt(
        self, consumption, graph, attempt, event,
        *, expected_run_lock_version
    ):
        run = self.runs[graph["graph_invocation_id"]]
        if run["lock_version"] != expected_run_lock_version:
            return _Result("stale_state")
        self.attempts[attempt["node_attempt_id"]] = deepcopy(attempt)
        run.update({"run_status": "resumed", "lock_version": 5})
        return _Result("applied", deepcopy(attempt))

    def claim_attempt(
        self, attempt, event, *, lease_owner_id, lease_acquired_at,
        lease_expires_at, **_
    ):
        row = self.attempts[attempt["node_attempt_id"]]
        if row["attempt_status"] != "pending":
            return _Result("stale_state")
        row.update(
            {
                "attempt_status": "claimed",
                "lease_owner_id": lease_owner_id,
                "lease_acquired_at": lease_acquired_at,
                "lease_expires_at": lease_expires_at,
                "started_at": lease_acquired_at,
                "lock_version": 1,
                "updated_at": lease_acquired_at,
            }
        )
        return _Result("applied", deepcopy(row))

    def commit_final_checkpoint(self, row, **_):
        self.checkpoints[row["checkpoint_id"]] = deepcopy(row)
        return _Result("applied", deepcopy(row))

    def record_attempt_success(
        self, attempt, event, *, output_checkpoint_id, output_digest,
        completed_at, duration_ms, **_
    ):
        row = self.attempts[attempt["node_attempt_id"]]
        row.update(
            {
                "attempt_status": "succeeded",
                "output_checkpoint_id": output_checkpoint_id,
                "output_digest": output_digest,
                "completed_at": completed_at,
                "duration_ms": duration_ms,
                "lock_version": 2,
                "updated_at": completed_at,
            }
        )
        self.runs[row["graph_invocation_id"]].update(
            {
                "current_checkpoint_id": output_checkpoint_id,
                "lock_version": 6,
            }
        )
        return _Result("applied", deepcopy(row))

    def terminalize_production_run(self, graph, terminal, event, **_):
        existing = self.terminals.get(graph["graph_invocation_id"])
        if existing is not None:
            return _Result("idempotent_existing", deepcopy(existing))
        self.terminals[graph["graph_invocation_id"]] = deepcopy(terminal)
        self.runs[graph["graph_invocation_id"]].update(
            {
                "run_status": "completed",
                "lock_version": 7,
                "terminal_at": terminal["completed_at"],
            }
        )
        return _Result("applied", deepcopy(terminal))

    def read_terminal_result(self, *, owner_user_id, graph_invocation_id):
        row = self.terminals.get(graph_invocation_id)
        if row is None or row["owner_user_id"] != owner_user_id:
            return _Result("not_found")
        return _Result("applied", deepcopy(row))


def _coordinator(repository=None, saver=None, consumer="worker-phase20"):
    return coordinator.ProductionHumanCheckpointCoordinator(
        repository=repository or _Repository(),
        saver=saver or MemorySaver(),
        consumer_instance_id=consumer,
        enabled=True,
    )


def _pause(instance):
    return instance.create_or_reopen_pause(
        bounded_tailoring_result={
            "parse_ok": True,
            "parsed": {"tailoring_actions": ["bounded synthetic fixture"]},
            "raw_response": "",
            "provider_call_count": 1,
        },
        owner_user_id=OWNER,
        pipeline_run_id="run-phase20",
        context_id="context-phase20",
        job_id="job-phase20",
        job_index=2,
        selected_resume_id="resume-phase20.pdf",
        created_at=NOW,
    )


def _authorize(instance, pause, **overrides):
    values = {
        "owner_user_id": OWNER,
        "graph_invocation_id": pause.graph_invocation_id,
        "repository_checkpoint_id": pause.repository_checkpoint_id,
        "interrupt_request_id": pause.interrupt_request_id,
        "decision_value": "continue_read_only",
        "actor_id": "operator-phase20",
        "client_idempotency_key": "decision-phase20",
        "decision_reason": "bounded read-only continuation",
        "created_at": NOW,
        "authorization_token": TOKEN,
        "authorization_expires_at": EXPIRES,
    }
    values.update(overrides)
    return instance.record_decision(**values)


def _resume(instance, pause, decision, **overrides):
    values = {
        "owner_user_id": OWNER,
        "graph_invocation_id": pause.graph_invocation_id,
        "repository_checkpoint_id": pause.repository_checkpoint_id,
        "interrupt_request_id": pause.interrupt_request_id,
        "decision_id": decision.decision_id,
        "authorization_token": TOKEN,
        "claimed_at": "2026-07-30T12:05:00Z",
        "lease_expires_at": "2026-07-30T12:15:00Z",
        "completed_at": "2026-07-30T12:10:00Z",
        "duration_ms": 300_000,
    }
    values.update(overrides)
    return instance.resume(**values)


def test_01_exact_contract_versions():
    assert production.PRODUCTION_HUMAN_REVIEW_CONTRACT_VERSION == (
        "production-human-review-contract-v1"
    )
    assert coordinator.PRODUCTION_HUMAN_CHECKPOINT_COORDINATOR_VERSION == (
        "production-human-checkpoint-coordinator-v1"
    )


def test_02_gate_default_and_truthy():
    for value, expected in (
        (None, False), ("", False), ("0", False), ("false", False),
        ("1", True), ("true", True),
    ):
        env = {} if value is None else {
            caller.PRODUCTION_HUMAN_CHECKPOINT_FLAG: value
        }
        assert caller._production_human_checkpoint_enabled(env) is expected


def test_03_coordinator_is_explicitly_default_off():
    with pytest.raises(ValueError, match="not_enabled"):
        coordinator.ProductionHumanCheckpointCoordinator(
            repository=object(),
            saver=object(),
            consumer_instance_id="worker",
        )


def test_04_required_dependencies():
    for missing in ("repository", "saver"):
        values = {
            "repository": object(),
            "saver": object(),
            "consumer_instance_id": "worker",
            "enabled": True,
        }
        values[missing] = None
        with pytest.raises(ValueError, match="required"):
            coordinator.ProductionHumanCheckpointCoordinator(**values)


def test_05_token_hash_is_deterministic_and_not_plaintext():
    first = coordinator.hash_resume_authorization_token(TOKEN)
    assert first == coordinator.hash_resume_authorization_token(TOKEN)
    assert first != TOKEN and len(first) == 64


def test_06_real_graph_pauses_before_finalize():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    binding = next(iter(repository.bindings.values()))
    payload = binding["event_payload_json"]
    snapshot = instance._graph.get_state(
        {
            "configurable": {
                "thread_id": payload["langgraph_thread_id"],
                "checkpoint_ns": payload[
                    "langgraph_checkpoint_namespace"
                ],
                "checkpoint_id": payload["langgraph_checkpoint_id"],
            }
        }
    )
    assert tuple(snapshot.next) == ("finalize",)


def test_07_checkpoint_is_deterministic():
    graph = production.prepare_graph_run_row(
        graph_version=coordinator.PRODUCTION_HUMAN_REVIEW_GRAPH_VERSION,
        state_version=coordinator.PRODUCTION_HUMAN_REVIEW_STATE_VERSION,
        owner_user_id=OWNER,
        pipeline_run_id="run",
        context_id="ctx",
        job_id="job",
        job_index=0,
        selected_resume_id="resume",
        production_node_key="operator_review",
        input_digest="a" * 64,
        created_at=NOW,
    )
    args = dict(
        artifact_digest="a" * 64,
        saved_state_digest="b" * 64,
        committed_at=NOW,
    )
    assert production.prepare_human_review_checkpoint_row(
        graph, **args
    ) == production.prepare_human_review_checkpoint_row(graph, **args)


def test_08_checkpoint_and_interrupt_retain_no_raw_artifact():
    repository = _Repository()
    _pause(_coordinator(repository, MemorySaver()))
    serialized = repr(
        (repository.checkpoints, repository.interrupts)
    ).lower()
    assert "bounded synthetic fixture" not in serialized
    checkpoint = next(iter(repository.checkpoints.values()))
    interrupt = next(iter(repository.interrupts.values()))
    assert "tailoring_result" not in checkpoint["checkpoint_envelope_json"]
    assert "tailoring_result" not in interrupt["interrupt_request_json"]


def test_09_interrupt_uses_exact_existing_decisions():
    repository = _Repository()
    _pause(_coordinator(repository, MemorySaver()))
    interrupt = next(iter(repository.interrupts.values()))
    assert interrupt["allowed_decision_values_json"] == [
        "continue_read_only", "needs_revision", "cancel"
    ]


def test_10_production_interrupt_is_truthful_and_safe():
    repository = _Repository()
    _pause(_coordinator(repository, MemorySaver()))
    interrupt = next(iter(repository.interrupts.values()))
    assert interrupt["diagnostic_only"] is False
    assert interrupt["read_only"] is True
    assert interrupt["application_authorization"] is False
    assert interrupt["resume_authorization"] is False


def test_11_decision_builder_is_deterministic():
    repository = _Repository()
    pause = _pause(_coordinator(repository, MemorySaver()))
    interrupt = next(iter(repository.interrupts.values()))
    kwargs = dict(
        decision_value="continue_read_only",
        actor_id="actor",
        client_idempotency_key="key",
        expected_interrupt_version=0,
        expected_run_lock_version=1,
        created_at=NOW,
    )
    assert production.prepare_human_review_decision_row(
        interrupt, **kwargs
    ) == production.prepare_human_review_decision_row(interrupt, **kwargs)


def test_12_unknown_decision_fails_closed():
    repository = _Repository()
    _pause(_coordinator(repository, MemorySaver()))
    interrupt = next(iter(repository.interrupts.values()))
    with pytest.raises(ValueError, match="unsupported"):
        production.prepare_human_review_decision_row(
            interrupt,
            decision_value="apply",
            actor_id="actor",
            client_idempotency_key="key",
            expected_interrupt_version=0,
            expected_run_lock_version=1,
            created_at=NOW,
        )


def test_13_revision_cannot_create_resume_authorization():
    repository = _Repository()
    _pause(_coordinator(repository, MemorySaver()))
    interrupt = next(iter(repository.interrupts.values()))
    decision = production.prepare_human_review_decision_row(
        interrupt,
        decision_value="needs_revision",
        actor_id="actor",
        client_idempotency_key="key",
        expected_interrupt_version=0,
        expected_run_lock_version=1,
        created_at=NOW,
    )
    with pytest.raises(ValueError, match="not_resume_authorizable"):
        production.prepare_human_review_authorization_row(
            decision,
            authorization_token_hash="a" * 64,
            created_at=NOW,
            expires_at=EXPIRES,
        )


def test_14_authorization_has_no_external_authority():
    repository = _Repository()
    instance = _coordinator(repository, MemorySaver())
    decision = _authorize(instance, _pause(instance))
    stored = repository.authorizations[decision.decision_id]
    assert stored["read_only"] is True
    assert stored["application_authorization"] is False
    assert stored["resume_text_mutation_authorization"] is False
    assert stored["queue_mutation_authorization"] is False
    assert stored["operator_state_mutation_authorization"] is False


def test_15_production_caller_passes_explicit_human_checkpoint(monkeypatch):
    captured = {}
    injected_coordinator = object()

    def execute(**kwargs):
        captured.update(kwargs)
        return {
            "tailoring_result": {"parse_ok": True},
            "execution_metadata": {
                "execution_mode": "langgraph",
                "production_node_count": 1,
                "node_invocation_count": 1,
                "tailoring_owner_invocation_count": 1,
                "critic_invocation_count": 0,
                "status": "completed",
            },
        }

    monkeypatch.setattr(
        caller, "_execute_durable_tailoring_graph", execute
    )
    result = caller._maybe_execute_authoritative_tailoring_generation_graph(
        packet={},
        payload={},
        run_tailoring_func=lambda **_: {},
        env={
            caller.AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_FLAG: "1",
            caller.PRODUCTION_DURABLE_GRAPH_RUNTIME_FLAG: "1",
            caller.PRODUCTION_HUMAN_CHECKPOINT_FLAG: "1",
            "JOB_APP_PIPELINE_RUN_ID": "run",
            "JOB_STACK_OWNER_USER_ID": "owner",
            "APPLYLENS_AGENT_CONTEXT_ID": "context",
        },
        job_index=0,
        human_checkpoint_coordinator=injected_coordinator,
    )
    assert result["tailoring_result"]["parse_ok"] is True
    assert captured["human_checkpoint_enabled"] is True
    assert (
        captured["human_checkpoint_coordinator"]
        is injected_coordinator
    )


def test_16_gate_off_does_not_import_or_invoke_checkpoint(monkeypatch):
    calls = []
    result = caller._maybe_execute_authoritative_tailoring_generation_graph(
        packet={},
        payload={},
        run_tailoring_func=lambda **kwargs: calls.append(kwargs),
        env={caller.PRODUCTION_HUMAN_CHECKPOINT_FLAG: "1"},
    )
    assert result is None and calls == []


def test_17_checkpoint_gate_requires_durable_runtime():
    with pytest.raises(RuntimeError, match="requires_durable_runtime"):
        caller._maybe_execute_authoritative_tailoring_generation_graph(
            packet={},
            payload={},
            run_tailoring_func=lambda **_: {},
            env={
                caller.AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_FLAG: "1",
                caller.PRODUCTION_HUMAN_CHECKPOINT_FLAG: "1",
            },
        )


def test_18_first_execution_creates_one_pause():
    repository = _Repository()
    pause = _pause(_coordinator(repository, MemorySaver()))
    assert pause.status == "awaiting_review"
    assert len(repository.runs) == len(repository.checkpoints) == 1
    assert len(repository.interrupts) == len(repository.bindings) == 1


def test_19_pending_replay_returns_exact_same_pause():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    first = _pause(instance)
    second = _pause(instance)
    assert second == first
    assert len(repository.checkpoints) == len(repository.bindings) == 1


def test_20_restart_reopens_same_pause():
    repository, saver = _Repository(), MemorySaver()
    first = _pause(_coordinator(repository, saver))
    reopened = _coordinator(repository, saver).reopen_pause(
        owner_user_id=OWNER,
        graph_invocation_id=first.graph_invocation_id,
    )
    assert reopened == first


def test_21_wrong_owner_cannot_read_pause():
    repository, saver = _Repository(), MemorySaver()
    first = _pause(_coordinator(repository, saver))
    result = _coordinator(repository, saver).reopen_pause(
        owner_user_id="wrong-owner",
        graph_invocation_id=first.graph_invocation_id,
    )
    assert result.classification == "not_found"
    assert not result.review_artifact_digest


def test_22_stale_artifact_digest_fails_closed():
    repository, saver = _Repository(), MemorySaver()
    first = _pause(_coordinator(repository, saver))
    result = _coordinator(repository, saver).reopen_pause(
        owner_user_id=OWNER,
        graph_invocation_id=first.graph_invocation_id,
        expected_artifact_digest="f" * 64,
    )
    assert result.classification == "identity_mismatch"


def test_23_safe_continuation_resumes_and_terminalizes():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    decision = _authorize(instance, pause)
    result = _resume(instance, pause, decision)
    assert result.status == "completed"
    assert result.human_review_status == "human_reviewed"
    terminal = repository.terminals[pause.graph_invocation_id]
    bounded = terminal["result_metadata_json"]["bounded_result"]
    assert bounded["decision_value"] == "continue_read_only"
    assert bounded["application_authority"] is False
    assert bounded["ats_authority"] is False


def test_24_completed_pause_is_terminally_replayable():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    completed = _resume(instance, pause, _authorize(instance, pause))
    replay = _coordinator(repository, saver).reopen_pause(
        owner_user_id=OWNER,
        graph_invocation_id=pause.graph_invocation_id,
    )
    assert replay.status == "completed_replay"
    assert replay.terminal_result_id == completed.terminal_result_id


def test_25_non_continue_decisions_never_authorize_or_resume():
    for decision_value, expected_status in (
        ("needs_revision", "revision_required"),
        ("cancel", "cancelled"),
    ):
        repository = _Repository()
        instance = _coordinator(repository, MemorySaver())
        pause = _pause(instance)
        result = _authorize(
            instance,
            pause,
            decision_value=decision_value,
            authorization_token="",
            authorization_expires_at="",
        )
        assert result.status == expected_status
        assert repository.authorizations == {}
        assert repository.consumptions == {}
        assert repository.attempts == {}


def test_26_duplicate_identical_decision_is_idempotent():
    repository = _Repository()
    instance = _coordinator(repository, MemorySaver())
    pause = _pause(instance)
    first = _authorize(instance, pause)
    result = _authorize(instance, pause)
    assert first.decision_id == result.decision_id
    assert first.authorization_id == result.authorization_id
    assert result.classification == "idempotent_existing"


def test_27_conflicting_decision_fails_closed():
    repository = _Repository()
    instance = _coordinator(repository, MemorySaver())
    pause = _pause(instance)
    _authorize(instance, pause)
    conflict = _authorize(
        instance,
        pause,
        decision_value="cancel",
        authorization_token="",
        authorization_expires_at="",
    )
    assert conflict.classification == "duplicate_conflict"


def test_28_wrong_token_hash_does_not_resume():
    repository = _Repository()
    instance = _coordinator(repository, MemorySaver())
    pause = _pause(instance)
    decision = _authorize(instance, pause)
    result = _resume(
        instance, pause, decision, authorization_token="wrong"
    )
    assert result.classification == "stale_state"
    assert repository.attempts == {}


def test_29_expired_authorization_does_not_resume():
    repository = _Repository()
    instance = _coordinator(repository, MemorySaver())
    pause = _pause(instance)
    decision = _authorize(
        instance,
        pause,
        authorization_expires_at="2026-07-30T12:01:00Z",
    )
    result = _resume(instance, pause, decision)
    assert result.classification == "stale_state"
    assert repository.attempts == {}


def test_30_concurrent_consumers_cannot_both_resume():
    repository, saver = _Repository(), MemorySaver()
    first_worker = _coordinator(repository, saver, "worker-a")
    pause = _pause(first_worker)
    decision = _authorize(first_worker, pause)
    authorization = repository.authorizations[decision.decision_id]
    first_row = production.prepare_human_review_consumption_row(
        authorization,
        consumer_instance_id="worker-a",
        claimed_at="2026-07-30T12:05:00Z",
    )
    second_row = production.prepare_human_review_consumption_row(
        authorization,
        consumer_instance_id="worker-b",
        claimed_at="2026-07-30T12:05:00Z",
    )
    token_hash = coordinator.hash_resume_authorization_token(TOKEN)
    first = repository.consume_resume_authorization(
        first_row, authorization_token_hash=token_hash
    )
    second = repository.consume_resume_authorization(
        second_row, authorization_token_hash=token_hash
    )
    assert first.classification == "applied"
    assert second.classification == "duplicate_conflict"


def test_31_module_has_no_connection_provider_or_application_owner():
    source = inspect.getsource(coordinator)
    for prohibited in (
        "DATABASE_URL",
        "load_dotenv",
        "run_tailoring",
        "llm",
        "mark_applied",
        "ats_submission",
        "recruiter_message",
    ):
        assert prohibited not in source


def test_32_dedicated_postgres_pause_decision_resume_and_cleanup():
    import os
    from urllib.parse import urlsplit

    repository_target = str(
        os.environ.get(
            "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
        )
        or ""
    ).strip()
    saver_target = str(
        os.environ.get(
            "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_TEST_DATABASE_URL"
        )
        or ""
    ).strip()
    if not repository_target or not saver_target:
        pytest.skip("dedicated Phase 9 PostgreSQL targets are not configured")
    assert urlsplit(repository_target).path.strip("/") == (
        "job_scraper_phase9_test"
    )
    assert urlsplit(saver_target).path.strip("/") == (
        "job_scraper_phase9_test"
    )
    for normal_target in (
        os.environ.get("DATABASE_URL"),
        os.environ.get(
            "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL"
        ),
        os.environ.get(
            "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_DATABASE_URL"
        ),
    ):
        if normal_target:
            assert normal_target not in {repository_target, saver_target}

    from src.storage.admin_tools.durable_orchestration import apply_schema
    from src.storage.durable_orchestration import (
        langgraph_postgres,
        postgres_connection,
        repository as repository_owner,
    )
    from tests.test_phase9_step16a_durable_decision_authorization_runtime_contract import (
        _cleanup,
        _counts,
    )

    schema_result = (
        apply_schema.DurableOrchestrationSchemaExecutor(
            enabled=True
        ).apply(database_url=repository_target)
    )
    assert schema_result.outcome == "applied"
    assert schema_result.compatibility == "compatible"
    artifact = {
        "parse_ok": True,
        "parsed": {"tailoring_actions": ["injected provider fixture"]},
        "raw_response": "",
        "provider_call_count": 1,
    }
    artifact_digest = production.canonical_digest(
        artifact, field="bounded_tailoring_review_artifact"
    )
    graph_row = production.prepare_graph_run_row(
        graph_version=coordinator.PRODUCTION_HUMAN_REVIEW_GRAPH_VERSION,
        state_version=coordinator.PRODUCTION_HUMAN_REVIEW_STATE_VERSION,
        owner_user_id="owner-phase20-postgres",
        pipeline_run_id="run-phase20-postgres",
        context_id="context-phase20-postgres",
        job_id="job-phase20-postgres",
        job_index=0,
        selected_resume_id="resume-phase20-postgres.pdf",
        production_node_key=production.PRODUCTION_HUMAN_REVIEW_NODE,
        input_digest=artifact_digest,
        created_at=NOW,
    )
    graph_id = graph_row["graph_invocation_id"]
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=repository_target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase20-repository",
    )
    _cleanup(
        factory,
        owner="owner-phase20-postgres",
        graph_id=graph_id,
    )
    try:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase20-pause",
        ) as first_saver:
            first_saver.delete_thread(graph_id)
            first = coordinator.ProductionHumanCheckpointCoordinator(
                repository=repository_owner.DurableOrchestrationRepository(
                    factory, enabled=True
                ),
                saver=first_saver,
                consumer_instance_id="worker-phase20",
                enabled=True,
            )
            pause = first.create_or_reopen_pause(
                bounded_tailoring_result=artifact,
                owner_user_id="owner-phase20-postgres",
                pipeline_run_id="run-phase20-postgres",
                context_id="context-phase20-postgres",
                job_id="job-phase20-postgres",
                job_index=0,
                selected_resume_id="resume-phase20-postgres.pdf",
                created_at=NOW,
            )
            assert pause.status == "awaiting_review"

        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase20-resume",
        ) as restarted_saver:
            restarted = (
                coordinator.ProductionHumanCheckpointCoordinator(
                    repository=(
                        repository_owner.DurableOrchestrationRepository(
                            factory, enabled=True
                        )
                    ),
                    saver=restarted_saver,
                    consumer_instance_id="worker-phase20",
                    enabled=True,
                )
            )
            reopened = restarted.reopen_pause(
                owner_user_id="owner-phase20-postgres",
                graph_invocation_id=graph_id,
            )
            assert reopened == pause
            decision = restarted.record_decision(
                owner_user_id="owner-phase20-postgres",
                graph_invocation_id=graph_id,
                repository_checkpoint_id=pause.repository_checkpoint_id,
                interrupt_request_id=pause.interrupt_request_id,
                decision_value="continue_read_only",
                actor_id="operator-phase20",
                client_idempotency_key="decision-phase20-postgres",
                decision_reason="read-only continuation",
                created_at=NOW,
                authorization_token=TOKEN,
                authorization_expires_at=EXPIRES,
            )
            assert decision.status == "resume_authorized"
            completed = restarted.resume(
                owner_user_id="owner-phase20-postgres",
                graph_invocation_id=graph_id,
                repository_checkpoint_id=pause.repository_checkpoint_id,
                interrupt_request_id=pause.interrupt_request_id,
                decision_id=decision.decision_id,
                authorization_token=TOKEN,
                claimed_at="2026-07-30T12:05:00Z",
                lease_expires_at="2026-07-30T12:15:00Z",
                completed_at="2026-07-30T12:10:00Z",
                duration_ms=300_000,
            )
            assert completed.status == "completed"
            assert restarted.reopen_pause(
                owner_user_id="owner-phase20-postgres",
                graph_invocation_id=graph_id,
            ).status == "completed_replay"
        counts = _counts(
            factory,
            owner="owner-phase20-postgres",
            graph_id=graph_id,
        )
        assert counts["orchestration_human_decisions"] == 1
        assert counts["orchestration_resume_authorizations"] == 1
        assert counts["orchestration_resume_consumptions"] == 1
        assert counts["orchestration_terminal_results"] == 1
    finally:
        _cleanup(
            factory,
            owner="owner-phase20-postgres",
            graph_id=graph_id,
        )
        assert all(
            count == 0
            for count in _counts(
                factory,
                owner="owner-phase20-postgres",
                graph_id=graph_id,
            ).values()
        )
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase20-cleanup",
        ) as cleanup_saver:
            cleanup_saver.delete_thread(graph_id)

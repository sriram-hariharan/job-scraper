from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path

import pytest

from src.storage.durable_orchestration import (
    postgres_connection,
    repository,
    store,
)
from tests.test_phase9_step16a_durable_decision_authorization_runtime_contract import (
    EXPIRES,
    NOW,
    OWNER,
    RUNTIME_GATE,
    TEST_TARGET,
    TOKEN_HASH,
    WRONG_OWNER,
    _authorization,
    _cleanup,
    _counts,
    _decision,
    _fixtures,
    _runtime_target_or_skip,
)


FINAL_BUNDLE_DIGEST = "d" * 64
FINAL_TRACE_DIGEST = "e" * 64
FINAL_OUTPUT_DIGEST = "f" * 64
CLAIMED_AT = "2026-07-24T12:05:00Z"
LEASE_EXPIRES = "2026-07-24T12:10:00Z"
RECOVERY_AT = "2026-07-24T12:20:00Z"
RECOVERY_EXPIRES = "2026-07-24T12:30:00Z"
COMPLETED_AT = "2026-07-24T12:25:00Z"


def _graph_state(graph_run, *, status, checkpoint_id, lock_version):
    row = deepcopy(graph_run)
    row["run_status"] = status
    row["current_checkpoint_id"] = checkpoint_id
    row["lock_version"] = lock_version
    row["updated_at"] = COMPLETED_AT
    return row


def _event(
    graph_run,
    *,
    event_type,
    aggregate_id,
    sequence,
    attempt=None,
    consumption=None,
    terminal=None,
):
    references = {}
    if attempt is not None:
        references["node_attempt_id"] = attempt["node_attempt_id"]
        references["checkpoint_id"] = attempt["input_checkpoint_id"]
    if consumption is not None:
        references["consumption_id"] = consumption["consumption_id"]
    if terminal is not None:
        references["terminal_result_id"] = terminal["terminal_result_id"]
        references["checkpoint_id"] = terminal["terminal_checkpoint_id"]
    return store.prepare_lifecycle_event_row(
        graph_run,
        event_type=event_type,
        aggregate_type=(
            "terminal_result" if terminal is not None else "node_attempt"
        ),
        aggregate_id=aggregate_id,
        event_sequence=sequence,
        event_payload={"status": event_type},
        event_timestamp=(
            COMPLETED_AT if "success" in event_type or terminal else CLAIMED_AT
        ),
        references=references,
    )


def _attempt(graph_run, consumption):
    return store.prepare_node_attempt_row(
        graph_run,
        input_checkpoint_id=consumption["checkpoint_id"],
        node_key="finalize",
        attempt_number=1,
        input_digest="a" * 64,
        created_at=NOW,
        resume_invocation_id=consumption["resume_invocation_id"],
    )


def test_final_checkpoint_is_deterministic_parent_bound_and_terminal_only():
    _, _, _, graph_run, checkpoint, _ = _fixtures()
    resumed = _graph_state(
        graph_run,
        status="resumed",
        checkpoint_id=checkpoint["checkpoint_id"],
        lock_version=5,
    )
    first = store.prepare_final_checkpoint_row(
        resumed,
        checkpoint,
        final_bundle_digest=FINAL_BUNDLE_DIGEST,
        final_trace_digest=FINAL_TRACE_DIGEST,
        output_artifact_digests={"bundle": FINAL_OUTPUT_DIGEST},
        committed_at=COMPLETED_AT,
    )
    second = store.prepare_final_checkpoint_row(
        resumed,
        checkpoint,
        final_bundle_digest=FINAL_BUNDLE_DIGEST,
        final_trace_digest=FINAL_TRACE_DIGEST,
        output_artifact_digests={"bundle": FINAL_OUTPUT_DIGEST},
        committed_at=COMPLETED_AT,
    )
    assert first == second
    assert first["completed_node_keys_json"][-1] == "finalize"
    assert first["next_node_key"] == store.FINAL_CHECKPOINT_NEXT_NODE_KEY
    assert first["checkpoint_id"] != checkpoint["checkpoint_id"]
    assert first["checkpoint_envelope_json"][
        "parent_repository_checkpoint_id"
    ] == checkpoint["checkpoint_id"]
    assert "state" not in first["checkpoint_envelope_json"]
    assert "interrupt" not in store.prepare_final_checkpoint_commit(
        first,
        parent_checkpoint_id=checkpoint["checkpoint_id"],
        expected_run_lock_version=5,
    )["tables"]
    conflicting = store.prepare_final_checkpoint_row(
        resumed,
        checkpoint,
        final_bundle_digest="1" * 64,
        final_trace_digest=FINAL_TRACE_DIGEST,
        output_artifact_digests={"bundle": FINAL_OUTPUT_DIGEST},
        committed_at=COMPLETED_AT,
    )
    assert conflicting["checkpoint_id"] != first["checkpoint_id"]


def test_pending_attempt_is_finalize_only_and_recovery_preserves_resume():
    _, _, _, graph_run, checkpoint, _ = _fixtures()
    consumed_graph = _graph_state(
        graph_run,
        status="resume_consumed",
        checkpoint_id=checkpoint["checkpoint_id"],
        lock_version=4,
    )
    consumption = {
        key: None for key in store._CONSUMPTION_COLUMNS
    }
    consumption.update(
        {
            "consumption_id": "consumption-step16b",
            "authorization_id": "authorization-step16b",
            "decision_id": "decision-step16b",
            "graph_invocation_id": graph_run["graph_invocation_id"],
            "checkpoint_id": checkpoint["checkpoint_id"],
            "interrupt_request_id": "interrupt-step16b",
            **{
                key: graph_run[key] for key in store._IDENTITY_COLUMNS
            },
            "resume_invocation_id": "resume-invocation-step16b",
            "consumer_instance_id": "worker-step16b",
            "claimed_at": NOW,
            "claim_status": "claimed",
            "expected_authorization_version": 0,
            "application_authorization": False,
        }
    )
    attempt = _attempt(consumed_graph, consumption)
    assert attempt["node_key"] == "finalize"
    assert attempt["resume_invocation_id"] == consumption[
        "resume_invocation_id"
    ]
    with pytest.raises(ValueError, match="node_key_unsupported"):
        store.prepare_node_attempt_row(
            consumed_graph,
            input_checkpoint_id=checkpoint["checkpoint_id"],
            node_key="arbitrary",
            attempt_number=1,
            input_digest="a" * 64,
            created_at=NOW,
            resume_invocation_id=consumption["resume_invocation_id"],
        )
    altered = deepcopy(attempt)
    altered["resume_invocation_id"] = "other"
    with pytest.raises(ValueError, match="recovery_resume_identity"):
        store.prepare_recovery_claim_inputs(
            consumption, consumed_graph, altered
        )


def test_terminalization_requires_successful_finalize_and_final_binding():
    _, _, _, graph_run, checkpoint, _ = _fixtures()
    resumed = _graph_state(
        graph_run,
        status="resumed",
        checkpoint_id=checkpoint["checkpoint_id"],
        lock_version=6,
    )
    terminal = store.prepare_terminal_result_row(
        resumed,
        terminal_checkpoint_id=checkpoint["checkpoint_id"],
        checkpoint_schema_version=store.harness.CHECKPOINT_SCHEMA_VERSION,
        terminal_status="completed",
        result_metadata={"final_bundle_digest": FINAL_BUNDLE_DIGEST},
        completed_at=COMPLETED_AT,
    )
    event = _event(
        resumed,
        event_type="terminal_result_recorded",
        aggregate_id=terminal["terminal_result_id"],
        sequence=0,
        terminal=terminal,
    )
    with pytest.raises(ValueError, match="execution_evidence_incomplete"):
        store.prepare_terminalization(
            resumed,
            terminal,
            event,
            expected_run_status="resumed",
            expected_run_lock_version=6,
            successful_attempt_row={},
        )
    assert terminal["final_node_order_json"][-1] == "finalize"


def test_repository_stays_default_off_and_has_no_graph_or_worker_runtime():
    with pytest.raises(repository.DurableOrchestrationRepositoryDisabled):
        repository.DurableOrchestrationRepository(lambda: None)
    source = Path(repository.__file__).read_text(encoding="utf-8")
    for prohibited in (
        "from langgraph",
        "graph.invoke",
        "finalize(",
        "os.environ",
        "DATABASE_URL",
        "automatic_retry",
        "background_worker",
        "application_action",
        "submit_application",
    ):
        assert prohibited not in source


def test_real_postgres_step16b_attempt_recovery_terminal_runtime():
    target = _runtime_target_or_skip(os.environ)
    _, envelope, _, graph_run, checkpoint, interrupt = _fixtures()
    graph_id = graph_run["graph_invocation_id"]
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase9-step16b-integration",
    )
    executor = repository.DurableOrchestrationRepository(
        factory, enabled=True
    )
    unrelated_before = _counts(
        factory, owner=WRONG_OWNER, graph_id="unrelated-step16b"
    )
    _cleanup(factory, owner=OWNER, graph_id=graph_id)
    try:
        executor.create_graph_run(
            envelope, created_at=graph_run["created_at"]
        )
        executor.commit_checkpoint_interrupt(
            graph_invocation_id=graph_id,
            owner_user_id=OWNER,
            expected_run_status="running",
            expected_lock_version=0,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        )
        paused_binding = store.prepare_langgraph_checkpoint_binding_row(
            graph_run,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            langgraph_thread_id=graph_id,
            langgraph_checkpoint_namespace="",
            langgraph_checkpoint_id="package-paused-step16b",
            event_timestamp=NOW,
        )
        executor.commit_checkpoint_binding(paused_binding)
        decision = _decision(interrupt)
        executor.record_human_decision(decision)
        authorization = _authorization(decision)
        executor.create_resume_authorization(
            authorization,
            expected_run_lock_version=2,
            expected_interrupt_version=1,
        )
        prepared_consumption = store.prepare_resume_consumption_row(
            authorization,
            consumer_instance_id="worker-step16b",
            claimed_at=NOW,
            expected_authorization_version=0,
        )
        executor.consume_resume_authorization(
            prepared_consumption,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        )
        consumption = dict(
            executor.read_resume_consumption(
                owner_user_id=OWNER,
                authorization_id=authorization["authorization_id"],
            ).record
        )
        consumed_graph = _graph_state(
            graph_run,
            status="resume_consumed",
            checkpoint_id=checkpoint["checkpoint_id"],
            lock_version=4,
        )
        attempt = _attempt(consumed_graph, consumption)
        recovery_event = _event(
            consumed_graph,
            event_type="recovery_claim_recorded",
            aggregate_id=attempt["node_attempt_id"],
            sequence=0,
            attempt=attempt,
            consumption=consumption,
        )
        pending = executor.create_pending_finalize_attempt(
            consumption,
            consumed_graph,
            attempt,
            recovery_event,
            expected_run_lock_version=4,
        )
        assert pending.classification == "applied"
        assert executor.create_pending_finalize_attempt(
            consumption,
            consumed_graph,
            attempt,
            recovery_event,
            expected_run_lock_version=4,
        ).classification == "idempotent_existing"

        resumed_graph = _graph_state(
            graph_run,
            status="resumed",
            checkpoint_id=checkpoint["checkpoint_id"],
            lock_version=5,
        )
        claim_event = _event(
            resumed_graph,
            event_type="node_attempt_claimed",
            aggregate_id=attempt["node_attempt_id"],
            sequence=1,
            attempt=attempt,
        )
        claimed = executor.claim_attempt(
            attempt,
            claim_event,
            lease_owner_id="worker-step16b-a",
            lease_acquired_at=CLAIMED_AT,
            lease_expires_at=LEASE_EXPIRES,
            expected_lock_version=0,
            expected_run_lock_version=5,
        )
        claimed_row = dict(claimed.record)
        assert claimed.classification == "applied"
        assert executor.claim_attempt(
            attempt,
            claim_event,
            lease_owner_id="worker-step16b-a",
            lease_acquired_at=CLAIMED_AT,
            lease_expires_at=LEASE_EXPIRES,
            expected_lock_version=0,
            expected_run_lock_version=5,
        ).classification == "idempotent_existing"
        assert executor.claim_attempt(
            attempt,
            claim_event,
            lease_owner_id="worker-step16b-b",
            lease_acquired_at="2026-07-24T12:06:00Z",
            lease_expires_at=RECOVERY_EXPIRES,
            expected_lock_version=1,
            expected_run_lock_version=5,
        ).classification == "duplicate_conflict"

        recovery_claim_event = _event(
            resumed_graph,
            event_type="node_attempt_claimed",
            aggregate_id=attempt["node_attempt_id"],
            sequence=2,
            attempt=attempt,
        )
        recovered = executor.recover_expired_attempt(
            claimed_row,
            recovery_claim_event,
            lease_owner_id="worker-step16b-recovery",
            lease_acquired_at=RECOVERY_AT,
            lease_expires_at=RECOVERY_EXPIRES,
            expected_lock_version=1,
            expected_run_lock_version=5,
        )
        recovered_row = dict(recovered.record)
        assert recovered.classification == "applied"
        assert recovered_row["resume_invocation_id"] == consumption[
            "resume_invocation_id"
        ]

        final_checkpoint = store.prepare_final_checkpoint_row(
            resumed_graph,
            checkpoint,
            final_bundle_digest=FINAL_BUNDLE_DIGEST,
            final_trace_digest=FINAL_TRACE_DIGEST,
            output_artifact_digests={"bundle": FINAL_OUTPUT_DIGEST},
            committed_at=COMPLETED_AT,
        )
        assert executor.commit_final_checkpoint(
            final_checkpoint,
            parent_checkpoint_id=checkpoint["checkpoint_id"],
            expected_run_lock_version=5,
        ).classification == "applied"
        conflicting_checkpoint = store.prepare_final_checkpoint_row(
            resumed_graph,
            checkpoint,
            final_bundle_digest="1" * 64,
            final_trace_digest=FINAL_TRACE_DIGEST,
            output_artifact_digests={"bundle": FINAL_OUTPUT_DIGEST},
            committed_at=COMPLETED_AT,
        )
        assert executor.commit_final_checkpoint(
            conflicting_checkpoint,
            parent_checkpoint_id=checkpoint["checkpoint_id"],
            expected_run_lock_version=5,
        ).classification == "duplicate_conflict"
        success_event = _event(
            resumed_graph,
            event_type="node_attempt_succeeded",
            aggregate_id=attempt["node_attempt_id"],
            sequence=3,
            attempt=attempt,
        )
        succeeded = executor.record_attempt_success(
            recovered_row,
            success_event,
            output_checkpoint_id=final_checkpoint["checkpoint_id"],
            output_digest=final_checkpoint[
                "checkpoint_envelope_digest"
            ],
            completed_at=COMPLETED_AT,
            duration_ms=1200,
            lease_owner_id="worker-step16b-recovery",
            expected_lock_version=2,
            expected_run_lock_version=5,
        )
        succeeded_row = dict(succeeded.record)
        assert succeeded.classification == "applied"

        final_binding = store.prepare_langgraph_checkpoint_binding_row(
            resumed_graph,
            repository_checkpoint_id=final_checkpoint["checkpoint_id"],
            langgraph_thread_id=graph_id,
            langgraph_checkpoint_namespace="",
            langgraph_checkpoint_id="package-final-step16b",
            event_timestamp=COMPLETED_AT,
        )
        assert executor.commit_checkpoint_binding(
            final_binding
        ).classification == "applied"
        assert executor.read_checkpoint_by_id(
            owner_user_id=OWNER,
            graph_invocation_id=graph_id,
            checkpoint_id=final_checkpoint["checkpoint_id"],
        ).record["next_node_key"] == store.FINAL_CHECKPOINT_NEXT_NODE_KEY
        assert executor.read_checkpoint_binding(
            owner_user_id=OWNER,
            graph_invocation_id=graph_id,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
        ).classification == "applied"
        assert executor.read_checkpoint_binding(
            owner_user_id=OWNER,
            graph_invocation_id=graph_id,
            repository_checkpoint_id=final_checkpoint["checkpoint_id"],
        ).classification == "applied"

        preterminal_graph = _graph_state(
            graph_run,
            status="resumed",
            checkpoint_id=final_checkpoint["checkpoint_id"],
            lock_version=6,
        )
        terminal = store.prepare_terminal_result_row(
            preterminal_graph,
            terminal_checkpoint_id=final_checkpoint["checkpoint_id"],
            checkpoint_schema_version=store.harness.CHECKPOINT_SCHEMA_VERSION,
            terminal_status="completed",
            result_metadata={
                "final_bundle_digest": FINAL_BUNDLE_DIGEST,
                "final_trace_digest": FINAL_TRACE_DIGEST,
                "resume_invocation_id": consumption[
                    "resume_invocation_id"
                ],
            },
            completed_at=COMPLETED_AT,
        )
        terminal_event = _event(
            preterminal_graph,
            event_type="terminal_result_recorded",
            aggregate_id=terminal["terminal_result_id"],
            sequence=0,
            terminal=terminal,
        )
        terminalized = executor.terminalize_completed_run(
            preterminal_graph,
            terminal,
            terminal_event,
            succeeded_row,
            final_binding,
            expected_run_lock_version=6,
        )
        assert terminalized.classification == "applied"
        assert executor.terminalize_completed_run(
            preterminal_graph,
            terminal,
            terminal_event,
            succeeded_row,
            final_binding,
            expected_run_lock_version=6,
        ).classification == "idempotent_existing"
        conflicting_terminal = store.prepare_terminal_result_row(
            preterminal_graph,
            terminal_checkpoint_id=final_checkpoint["checkpoint_id"],
            checkpoint_schema_version=store.harness.CHECKPOINT_SCHEMA_VERSION,
            terminal_status="completed",
            result_metadata={
                "final_bundle_digest": "2" * 64,
                "final_trace_digest": FINAL_TRACE_DIGEST,
                "resume_invocation_id": consumption[
                    "resume_invocation_id"
                ],
            },
            completed_at=COMPLETED_AT,
        )
        conflicting_event = _event(
            preterminal_graph,
            event_type="terminal_result_recorded",
            aggregate_id=conflicting_terminal["terminal_result_id"],
            sequence=0,
            terminal=conflicting_terminal,
        )
        assert executor.terminalize_completed_run(
            preterminal_graph,
            conflicting_terminal,
            conflicting_event,
            succeeded_row,
            final_binding,
            expected_run_lock_version=6,
        ).classification == "duplicate_conflict"
        assert executor.read_terminal_result(
            owner_user_id=OWNER,
            graph_invocation_id=graph_id,
        ).record["terminal_status"] == "completed"
        final_graph = executor.read_graph_run(
            owner_user_id=OWNER, graph_invocation_id=graph_id
        )
        assert final_graph.record["run_status"] == "completed"
        assert final_graph.record["lock_version"] == 7
        assert executor.read_attempt(
            owner_user_id=WRONG_OWNER,
            graph_invocation_id=graph_id,
            attempt_id=attempt["node_attempt_id"],
        ).classification == "not_found"
        counts = _counts(factory, owner=OWNER, graph_id=graph_id)
        assert counts["orchestration_resume_authorizations"] == 1
        assert counts["orchestration_resume_consumptions"] == 1
        assert counts["orchestration_node_attempts"] == 1
        assert counts["orchestration_checkpoints"] == 2
        assert counts["orchestration_terminal_results"] == 1
    finally:
        _cleanup(factory, owner=OWNER, graph_id=graph_id)
    assert _counts(
        factory, owner=WRONG_OWNER, graph_id="unrelated-step16b"
    ) == unrelated_before

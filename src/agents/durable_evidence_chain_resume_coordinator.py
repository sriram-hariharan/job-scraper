"""Explicit, default-off coordination for durable evidence-chain resume.

This module deliberately owns no connections.  A caller supplies an already
constructed durable repository, saver, and compiled graph.  The repository
remains the authority for authorization and attempt ownership; the LangGraph
saver remains the authority for executable graph state.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from src.agents import evidence_chain_langgraph_harness as harness
from src.storage.durable_orchestration import store


_ACCEPTED_WRITES = frozenset({"applied", "idempotent_existing"})


@dataclass(frozen=True)
class DurableResumeResult:
    status: str
    classification: str
    graph_invocation_id: str = ""
    repository_checkpoint_id: str = ""
    interrupt_request_id: str = ""
    attempt_id: str = ""
    terminal_result_id: str = ""
    langgraph_thread_id: str = ""
    langgraph_checkpoint_namespace: str = ""
    langgraph_checkpoint_id: str = ""


def _result_classification(result: Any) -> str:
    return str(getattr(result, "classification", "non_retryable_failure"))


def _result_record(result: Any) -> Mapping[str, Any]:
    record = getattr(result, "record", None)
    return record if isinstance(record, Mapping) else {}


def _bounded_failure(
    status: str,
    classification: str,
    *,
    graph_invocation_id: str = "",
) -> DurableResumeResult:
    allowed = {
        "already_completed",
        "stale_state",
        "not_found",
        "reconciliation_required",
        "retryable_database_failure",
        "non_retryable_failure",
        "invalid_saved_graph_state",
    }
    safe = classification if classification in allowed else "non_retryable_failure"
    return DurableResumeResult(
        status=status,
        classification=safe,
        graph_invocation_id=graph_invocation_id,
    )


class DurableEvidenceChainResumeCoordinator:
    """Compose existing graph and repository contracts when explicitly enabled."""

    def __init__(
        self,
        *,
        repository: Any,
        saver: Any,
        graph: Any,
        enabled: bool = False,
    ) -> None:
        if not enabled:
            raise ValueError("durable_restart_resume_not_enabled")
        if repository is None:
            raise ValueError("durable_repository_required")
        if saver is None:
            raise ValueError("langgraph_saver_required")
        if graph is None:
            raise ValueError("compiled_graph_required")
        self._repository = repository
        self._saver = saver
        self._graph = graph

    @staticmethod
    def _snapshot_config(snapshot: Any) -> dict[str, Any]:
        configurable = dict(getattr(snapshot, "config", {}).get("configurable") or {})
        if (
            not str(configurable.get("thread_id") or "").strip()
            or "checkpoint_ns" not in configurable
            or not str(configurable.get("checkpoint_id") or "").strip()
        ):
            raise ValueError("langgraph_checkpoint_identity_missing")
        return {
            "configurable": {
                "thread_id": configurable["thread_id"],
                "checkpoint_ns": configurable["checkpoint_ns"],
                "checkpoint_id": configurable["checkpoint_id"],
            }
        }

    @staticmethod
    def _validate_snapshot(snapshot: Any, *, expect_paused: bool) -> Mapping[str, Any]:
        values = getattr(snapshot, "values", None)
        if not isinstance(values, Mapping):
            raise ValueError("saved_graph_state_missing")
        if expect_paused:
            if tuple(getattr(snapshot, "next", ())) != ("finalize",):
                raise ValueError("saved_graph_pending_node_invalid")
            harness._validate_paused_operator_review_state(values)
        elif tuple(getattr(snapshot, "next", ())):
            raise ValueError("saved_graph_still_pending")
        return values

    def create_durable_pause(
        self,
        *,
        initial_state: Mapping[str, Any],
        base_config: Mapping[str, Any],
        created_at: str,
        committed_at: str,
    ) -> DurableResumeResult:
        """Run through review, then persist saver/readback before repository pause."""
        envelope = harness._build_checkpoint_envelope(initial_state)
        identity = dict(envelope["checkpoint_identity"])
        graph_id = str(identity["graph_invocation_id"])
        owner = str(identity["owner_user_id"])
        created = self._repository.create_graph_run(
            envelope, created_at=created_at
        )
        if _result_classification(created) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "durable_pause_created",
                _result_classification(created),
                graph_invocation_id=graph_id,
            )

        self._graph.invoke(deepcopy(dict(initial_state)), deepcopy(dict(base_config)))
        snapshot = self._graph.get_state(deepcopy(dict(base_config)))
        try:
            paused_state = self._validate_snapshot(snapshot, expect_paused=True)
            saved_config = self._snapshot_config(snapshot)
            exact_snapshot = self._graph.get_state(
                harness._experimental_state_lookup_config(
                    saved_config, self._saver
                )
            )
            exact_state = self._validate_snapshot(
                exact_snapshot, expect_paused=True
            )
            if harness._checkpoint_digest(paused_state) != harness._checkpoint_digest(
                exact_state
            ):
                raise ValueError("saved_graph_state_changed")
        except (TypeError, ValueError):
            return _bounded_failure(
                "durable_pause_created",
                "invalid_saved_graph_state",
                graph_invocation_id=graph_id,
            )

        paused_envelope = harness._build_checkpoint_envelope(exact_state)
        checkpoint = store.prepare_checkpoint_row(
            paused_envelope, committed_at=committed_at
        )
        interrupt_request = harness._build_operator_review_interrupt_request(
            exact_state,
            checkpoint_identity=paused_envelope["checkpoint_identity"],
        )
        interrupt = store.prepare_interrupt_request_row(
            interrupt_request,
            checkpoint_envelope=paused_envelope,
            created_at=committed_at,
        )
        committed = self._repository.commit_checkpoint_interrupt(
            graph_invocation_id=graph_id,
            owner_user_id=owner,
            expected_run_status="running",
            expected_lock_version=0,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        )
        if _result_classification(committed) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "durable_pause_created",
                "reconciliation_required",
                graph_invocation_id=graph_id,
            )
        configurable = saved_config["configurable"]
        binding = store.prepare_langgraph_checkpoint_binding_row(
            store.prepare_graph_run_row(envelope, created_at=created_at),
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            langgraph_thread_id=str(configurable["thread_id"]),
            langgraph_checkpoint_namespace=str(configurable["checkpoint_ns"]),
            langgraph_checkpoint_id=str(configurable["checkpoint_id"]),
            event_timestamp=committed_at,
        )
        bound = self._repository.commit_checkpoint_binding(binding)
        if _result_classification(bound) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "durable_pause_created",
                "reconciliation_required",
                graph_invocation_id=graph_id,
            )
        reads = (
            self._repository.read_graph_run(
                owner_user_id=owner, graph_invocation_id=graph_id
            ),
            self._repository.read_current_checkpoint(
                owner_user_id=owner, graph_invocation_id=graph_id
            ),
            self._repository.read_pending_interrupt(
                owner_user_id=owner, graph_invocation_id=graph_id
            ),
            self._repository.read_checkpoint_binding(
                owner_user_id=owner,
                graph_invocation_id=graph_id,
                repository_checkpoint_id=checkpoint["checkpoint_id"],
            ),
        )
        if any(_result_classification(item) != "applied" for item in reads):
            return _bounded_failure(
                "durable_pause_created",
                "reconciliation_required",
                graph_invocation_id=graph_id,
            )
        return DurableResumeResult(
            status="durable_pause_created",
            classification="applied",
            graph_invocation_id=graph_id,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            interrupt_request_id=interrupt["interrupt_request_id"],
            langgraph_thread_id=str(configurable["thread_id"]),
            langgraph_checkpoint_namespace=str(configurable["checkpoint_ns"]),
            langgraph_checkpoint_id=str(configurable["checkpoint_id"]),
        )

    def reopen_durable_pause(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
        repository_checkpoint_id: str,
    ) -> DurableResumeResult:
        """Validate both persistence owners without treating saver state as authority."""
        graph_result = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        classification = _result_classification(graph_result)
        if classification != "applied":
            return _bounded_failure(
                "durable_pause_reopened",
                classification,
                graph_invocation_id=graph_invocation_id,
            )
        graph_record = _result_record(graph_result)
        if graph_record.get("run_status") == "completed":
            return _bounded_failure(
                "already_completed",
                "already_completed",
                graph_invocation_id=graph_invocation_id,
            )
        if (
            graph_record.get("run_status") != "awaiting_decision"
            or graph_record.get("current_checkpoint_id")
            != repository_checkpoint_id
        ):
            return _bounded_failure(
                "durable_pause_reopened",
                "stale_state",
                graph_invocation_id=graph_invocation_id,
            )
        checkpoint = self._repository.read_current_checkpoint(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        interrupt = self._repository.read_pending_interrupt(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        binding = self._repository.read_checkpoint_binding(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=repository_checkpoint_id,
        )
        for result in (checkpoint, interrupt, binding):
            if _result_classification(result) != "applied":
                return _bounded_failure(
                    "durable_pause_reopened",
                    _result_classification(result),
                    graph_invocation_id=graph_invocation_id,
                )
        binding_payload = dict(
            _result_record(binding).get("event_payload_json") or {}
        )
        config = {
            "configurable": {
                "thread_id": binding_payload.get("langgraph_thread_id"),
                "checkpoint_ns": binding_payload.get(
                    "langgraph_checkpoint_namespace"
                ),
                "checkpoint_id": binding_payload.get("langgraph_checkpoint_id"),
            }
        }
        try:
            snapshot = self._graph.get_state(
                harness._experimental_state_lookup_config(config, self._saver)
            )
            self._validate_snapshot(snapshot, expect_paused=True)
            exact_config = self._snapshot_config(snapshot)["configurable"]
            if exact_config != config["configurable"]:
                raise ValueError("checkpoint_binding_mismatch")
        except (TypeError, ValueError):
            return _bounded_failure(
                "durable_pause_reopened",
                "invalid_saved_graph_state",
                graph_invocation_id=graph_invocation_id,
            )
        interrupt_record = _result_record(interrupt)
        return DurableResumeResult(
            status="durable_pause_reopened",
            classification="applied",
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=repository_checkpoint_id,
            interrupt_request_id=str(
                interrupt_record.get("interrupt_request_id") or ""
            ),
            langgraph_thread_id=str(exact_config["thread_id"]),
            langgraph_checkpoint_namespace=str(exact_config["checkpoint_ns"]),
            langgraph_checkpoint_id=str(exact_config["checkpoint_id"]),
        )

    def resume_paused_workflow(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
        repository_checkpoint_id: str,
        interrupt_request_id: str,
        actor_id: str,
        client_idempotency_key: str,
        decision_reason: str,
        authorization_token_hash: str,
        consumer_instance_id: str,
        created_at: str,
        authorization_expires_at: str,
        lease_acquired_at: str,
        lease_expires_at: str,
        completed_at: str,
        duration_ms: int,
    ) -> DurableResumeResult:
        """Own the complete durable ``continue_read_only`` resume transition."""
        reopened = self.reopen_durable_pause(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=repository_checkpoint_id,
        )
        if reopened.status == "already_completed":
            return reopened
        if reopened.classification != "applied":
            return reopened
        if reopened.interrupt_request_id != interrupt_request_id:
            return _bounded_failure(
                "decision_recorded",
                "stale_state",
                graph_invocation_id=graph_invocation_id,
            )

        saved_config = {
            "configurable": {
                "thread_id": reopened.langgraph_thread_id,
                "checkpoint_ns": reopened.langgraph_checkpoint_namespace,
                "checkpoint_id": reopened.langgraph_checkpoint_id,
            }
        }
        try:
            paused_snapshot = self._graph.get_state(
                harness._experimental_state_lookup_config(
                    saved_config, self._saver
                )
            )
            paused_state = self._validate_snapshot(
                paused_snapshot, expect_paused=True
            )
            paused_envelope = harness._build_checkpoint_envelope(paused_state)
            checkpoint = store.prepare_checkpoint_row(
                paused_envelope, committed_at=created_at
            )
            interrupt = store.prepare_interrupt_request_row(
                harness._build_operator_review_interrupt_request(
                    paused_state,
                    checkpoint_identity=paused_envelope["checkpoint_identity"],
                ),
                checkpoint_envelope=paused_envelope,
                created_at=created_at,
            )
        except (TypeError, ValueError):
            return _bounded_failure(
                "durable_pause_reopened",
                "invalid_saved_graph_state",
                graph_invocation_id=graph_invocation_id,
            )
        if (
            checkpoint["checkpoint_id"] != repository_checkpoint_id
            or interrupt["interrupt_request_id"] != interrupt_request_id
        ):
            return _bounded_failure(
                "decision_recorded",
                "stale_state",
                graph_invocation_id=graph_invocation_id,
            )

        graph_run = store.prepare_graph_run_row(
            paused_envelope, created_at=created_at
        )
        decision = store.prepare_human_decision_row(
            interrupt,
            decision_value="continue_read_only",
            actor_id=actor_id,
            client_idempotency_key=client_idempotency_key,
            expected_interrupt_version=0,
            expected_run_lock_version=1,
            created_at=created_at,
            reason=decision_reason,
        )
        recorded = self._repository.record_human_decision(decision)
        if _result_classification(recorded) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "decision_recorded",
                _result_classification(recorded),
                graph_invocation_id=graph_invocation_id,
            )
        decision_read = self._repository.read_current_human_decision(
            owner_user_id=owner_user_id,
            interrupt_request_id=interrupt_request_id,
        )
        if (
            _result_classification(decision_read) != "applied"
            or _result_record(decision_read).get("decision_id")
            != decision["decision_id"]
            or _result_record(decision_read).get("decision_value")
            != "continue_read_only"
        ):
            return _bounded_failure(
                "decision_recorded",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )

        authorization = store.prepare_resume_authorization_row(
            decision,
            authorization_token_hash=authorization_token_hash,
            created_at=created_at,
            expires_at=authorization_expires_at,
        )
        authorized = self._repository.create_resume_authorization(
            authorization,
            expected_run_lock_version=2,
            expected_interrupt_version=1,
        )
        if _result_classification(authorized) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "authorization_created",
                _result_classification(authorized),
                graph_invocation_id=graph_invocation_id,
            )
        consumption_row = store.prepare_resume_consumption_row(
            authorization,
            consumer_instance_id=consumer_instance_id,
            claimed_at=created_at,
            expected_authorization_version=0,
        )
        consumed = self._repository.consume_resume_authorization(
            consumption_row,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=authorization_token_hash,
        )
        if _result_classification(consumed) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "authorization_consumed",
                _result_classification(consumed),
                graph_invocation_id=graph_invocation_id,
            )
        authorization_read = self._repository.read_resume_authorization(
            owner_user_id=owner_user_id,
            decision_id=decision["decision_id"],
        )
        consumption_read = self._repository.read_resume_consumption(
            owner_user_id=owner_user_id,
            authorization_id=authorization["authorization_id"],
        )
        if (
            _result_classification(authorization_read) != "applied"
            or _result_record(authorization_read).get("authorization_status")
            != "consumed"
            or _result_classification(consumption_read) != "applied"
        ):
            return _bounded_failure(
                "authorization_consumed",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        consumption = dict(_result_record(consumption_read))
        if (
            consumption.get("checkpoint_id") != repository_checkpoint_id
            or consumption.get("interrupt_request_id") != interrupt_request_id
        ):
            return _bounded_failure(
                "authorization_consumed",
                "stale_state",
                graph_invocation_id=graph_invocation_id,
            )

        consumed_graph = deepcopy(graph_run)
        consumed_graph.update(
            {
                "run_status": "resume_consumed",
                "current_checkpoint_id": repository_checkpoint_id,
                "lock_version": 4,
                "updated_at": created_at,
            }
        )
        attempt = store.prepare_node_attempt_row(
            consumed_graph,
            input_checkpoint_id=repository_checkpoint_id,
            node_key="finalize",
            attempt_number=1,
            input_digest=checkpoint["checkpoint_envelope_digest"],
            created_at=created_at,
            resume_invocation_id=consumption["resume_invocation_id"],
        )
        pending_event = store.prepare_lifecycle_event_row(
            consumed_graph,
            event_type="recovery_claim_recorded",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=0,
            event_payload={"status": "pending"},
            event_timestamp=created_at,
            references={
                "node_attempt_id": attempt["node_attempt_id"],
                "checkpoint_id": repository_checkpoint_id,
                "consumption_id": consumption["consumption_id"],
            },
        )
        pending = self._repository.create_pending_finalize_attempt(
            consumption,
            consumed_graph,
            attempt,
            pending_event,
            expected_run_lock_version=4,
        )
        if _result_classification(pending) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "resume_attempted",
                _result_classification(pending),
                graph_invocation_id=graph_invocation_id,
            )
        resumed_graph = deepcopy(consumed_graph)
        resumed_graph.update({"run_status": "resumed", "lock_version": 5})
        claim_event = store.prepare_lifecycle_event_row(
            resumed_graph,
            event_type="node_attempt_claimed",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=1,
            event_payload={"status": "claimed"},
            event_timestamp=lease_acquired_at,
            references={
                "node_attempt_id": attempt["node_attempt_id"],
                "checkpoint_id": repository_checkpoint_id,
            },
        )
        claimed = self._repository.claim_attempt(
            attempt,
            claim_event,
            lease_owner_id=consumer_instance_id,
            lease_acquired_at=lease_acquired_at,
            lease_expires_at=lease_expires_at,
            expected_lock_version=0,
            expected_run_lock_version=5,
        )
        if _result_classification(claimed) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "resume_attempted",
                _result_classification(claimed),
                graph_invocation_id=graph_invocation_id,
            )
        claimed_read = self._repository.read_attempt(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            attempt_id=attempt["node_attempt_id"],
        )
        claimed_record = _result_record(claimed_read)
        graph_read = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        if (
            _result_classification(claimed_read) != "applied"
            or claimed_record.get("attempt_status") != "claimed"
            or claimed_record.get("lease_owner_id") != consumer_instance_id
            or claimed_record.get("node_key") != "finalize"
            or _result_classification(graph_read) != "applied"
            or _result_record(graph_read).get("run_status") != "resumed"
        ):
            return _bounded_failure(
                "resume_attempted",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        binding = self._repository.read_checkpoint_binding(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=repository_checkpoint_id,
        )
        if _result_classification(binding) != "applied":
            return _bounded_failure(
                "resume_attempted",
                _result_classification(binding),
                graph_invocation_id=graph_invocation_id,
            )
        payload = dict(_result_record(binding).get("event_payload_json") or {})
        if payload != {
            "binding_schema_version": store.LANGGRAPH_CHECKPOINT_BINDING_SCHEMA_VERSION,
            "graph_invocation_id": graph_invocation_id,
            "repository_checkpoint_id": repository_checkpoint_id,
            "langgraph_thread_id": reopened.langgraph_thread_id,
            "langgraph_checkpoint_namespace": reopened.langgraph_checkpoint_namespace,
            "langgraph_checkpoint_id": reopened.langgraph_checkpoint_id,
        }:
            return _bounded_failure(
                "resume_attempted",
                "stale_state",
                graph_invocation_id=graph_invocation_id,
            )

        final_values = self._graph.invoke(None, deepcopy(saved_config))
        final_snapshot = self._graph.get_state(
            {
                "configurable": {
                    "thread_id": payload.get("langgraph_thread_id"),
                    "checkpoint_ns": payload.get(
                        "langgraph_checkpoint_namespace"
                    ),
                }
            }
        )
        try:
            snapshot_values = self._validate_snapshot(
                final_snapshot, expect_paused=False
            )
            if harness._checkpoint_digest(final_values) != harness._checkpoint_digest(
                snapshot_values
            ):
                raise ValueError("final_saved_graph_state_changed")
            artifacts = snapshot_values.get("artifacts")
            if not isinstance(artifacts, Mapping) or not isinstance(
                artifacts.get("agent_evidence_chain_bundle"), Mapping
            ):
                raise ValueError("final_bundle_missing")
            final_config = self._snapshot_config(final_snapshot)["configurable"]
        except (TypeError, ValueError):
            return _bounded_failure(
                "resume_attempted",
                "invalid_saved_graph_state",
                graph_invocation_id=graph_invocation_id,
            )

        artifacts = dict(snapshot_values["artifacts"])
        bundle_digest = harness._checkpoint_digest(
            artifacts["agent_evidence_chain_bundle"]
        )
        trace = artifacts.get("agent_evidence_chain_trace_payload")
        trace_digest = (
            harness._checkpoint_digest(trace) if trace is not None else None
        )
        output_digests = {"agent_evidence_chain_bundle": bundle_digest}
        if trace_digest is not None:
            output_digests["agent_evidence_chain_trace_payload"] = trace_digest
        final_checkpoint = store.prepare_final_checkpoint_row(
            resumed_graph,
            checkpoint,
            final_bundle_digest=bundle_digest,
            final_trace_digest=trace_digest,
            output_artifact_digests=output_digests,
            committed_at=completed_at,
        )
        final_committed = self._repository.commit_final_checkpoint(
            final_checkpoint,
            parent_checkpoint_id=repository_checkpoint_id,
            expected_run_lock_version=5,
        )
        if _result_classification(final_committed) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "resume_attempted",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        final_binding = store.prepare_langgraph_checkpoint_binding_row(
            resumed_graph,
            repository_checkpoint_id=final_checkpoint["checkpoint_id"],
            langgraph_thread_id=str(final_config["thread_id"]),
            langgraph_checkpoint_namespace=str(final_config["checkpoint_ns"]),
            langgraph_checkpoint_id=str(final_config["checkpoint_id"]),
            event_timestamp=completed_at,
        )
        final_bound = self._repository.commit_checkpoint_binding(final_binding)
        if _result_classification(final_bound) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "resume_attempted",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        success_event = store.prepare_lifecycle_event_row(
            resumed_graph,
            event_type="node_attempt_succeeded",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=2,
            event_payload={"status": "succeeded"},
            event_timestamp=completed_at,
            references={
                "node_attempt_id": attempt["node_attempt_id"],
                "checkpoint_id": final_checkpoint["checkpoint_id"],
            },
        )
        succeeded = self._repository.record_attempt_success(
            dict(claimed_record),
            success_event,
            output_checkpoint_id=final_checkpoint["checkpoint_id"],
            output_digest=final_checkpoint["checkpoint_envelope_digest"],
            completed_at=completed_at,
            duration_ms=duration_ms,
            lease_owner_id=consumer_instance_id,
            expected_lock_version=1,
            expected_run_lock_version=5,
        )
        if _result_classification(succeeded) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "resume_attempted",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        preterminal = deepcopy(resumed_graph)
        preterminal.update(
            {
                "current_checkpoint_id": final_checkpoint["checkpoint_id"],
                "lock_version": 6,
                "updated_at": completed_at,
            }
        )
        terminal = store.prepare_terminal_result_row(
            preterminal,
            terminal_checkpoint_id=final_checkpoint["checkpoint_id"],
            checkpoint_schema_version=harness.CHECKPOINT_SCHEMA_VERSION,
            terminal_status="completed",
            result_metadata={
                "final_bundle_digest": bundle_digest,
                "final_trace_digest": trace_digest,
                "resume_invocation_id": consumption["resume_invocation_id"],
            },
            completed_at=completed_at,
        )
        terminal_event = store.prepare_lifecycle_event_row(
            preterminal,
            event_type="terminal_result_recorded",
            aggregate_type="terminal_result",
            aggregate_id=terminal["terminal_result_id"],
            event_sequence=0,
            event_payload={"status": "completed"},
            event_timestamp=completed_at,
            references={
                "terminal_result_id": terminal["terminal_result_id"],
                "checkpoint_id": final_checkpoint["checkpoint_id"],
            },
        )
        terminalized = self._repository.terminalize_completed_run(
            preterminal,
            terminal,
            terminal_event,
            dict(_result_record(succeeded)),
            final_binding,
            expected_run_lock_version=6,
        )
        if _result_classification(terminalized) not in _ACCEPTED_WRITES:
            return _bounded_failure(
                "resume_attempted",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        terminal_read = self._repository.read_terminal_result(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        completed_graph = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        if (
            _result_classification(terminal_read) != "applied"
            or _result_record(terminal_read).get("terminal_result_id")
            != terminal["terminal_result_id"]
            or _result_classification(completed_graph) != "applied"
            or _result_record(completed_graph).get("run_status") != "completed"
        ):
            return _bounded_failure(
                "resume_attempted",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        return DurableResumeResult(
            status="resume_completed",
            classification="applied",
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=final_checkpoint["checkpoint_id"],
            interrupt_request_id=interrupt_request_id,
            attempt_id=attempt["node_attempt_id"],
            terminal_result_id=terminal["terminal_result_id"],
            langgraph_thread_id=str(final_config["thread_id"]),
            langgraph_checkpoint_namespace=str(final_config["checkpoint_ns"]),
            langgraph_checkpoint_id=str(final_config["checkpoint_id"]),
        )

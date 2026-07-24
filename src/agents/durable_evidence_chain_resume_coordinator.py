"""Explicit, default-off coordination for durable evidence-chain resume.

This module deliberately owns no connections.  A caller supplies an already
constructed durable repository, saver, and compiled graph.  The repository
remains the authority for authorization and attempt ownership; the LangGraph
saver remains the authority for executable graph state.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping

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

    def resume_claimed_attempt(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
        repository_checkpoint_id: str,
        authorization_id: str,
        attempt_id: str,
        lease_owner_id: str,
        persist_final_state: Callable[
            [Mapping[str, Any], Mapping[str, Any]], DurableResumeResult
        ],
    ) -> DurableResumeResult:
        """Invoke only after consumed authorization and claimed attempt are proven.

        ``persist_final_state`` receives the validated actual final state and
        exact final saver identity synchronously.  It must commit the repository
        final checkpoint, binding, attempt success, and terminal result, and
        return a bounded result.  Raw state never leaves this call as a result.
        """
        graph_result = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        if _result_classification(graph_result) != "applied":
            return _bounded_failure(
                    "resume_attempted",
                    _result_classification(graph_result),
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
            graph_record.get("run_status") != "resumed"
            or graph_record.get("current_checkpoint_id")
            != repository_checkpoint_id
        ):
            return _bounded_failure(
                    "resume_attempted",
                    "stale_state",
                    graph_invocation_id=graph_invocation_id,
                )
        consumption = self._repository.read_resume_consumption(
            owner_user_id=owner_user_id,
            authorization_id=authorization_id,
        )
        attempt = self._repository.read_attempt(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            attempt_id=attempt_id,
        )
        if _result_classification(consumption) != "applied":
            return _bounded_failure(
                    "resume_attempted",
                    "stale_state",
                    graph_invocation_id=graph_invocation_id,
                )
        attempt_record = _result_record(attempt)
        if (
            _result_classification(attempt) != "applied"
            or attempt_record.get("attempt_status") != "claimed"
            or attempt_record.get("lease_owner_id") != lease_owner_id
            or attempt_record.get("node_key") != "finalize"
        ):
            return _bounded_failure(
                    "resume_attempted",
                    "stale_state",
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
        saved_config = {
            "configurable": {
                "thread_id": payload.get("langgraph_thread_id"),
                "checkpoint_ns": payload.get("langgraph_checkpoint_namespace"),
                "checkpoint_id": payload.get("langgraph_checkpoint_id"),
            }
        }
        try:
            paused = self._graph.get_state(
                harness._experimental_state_lookup_config(saved_config, self._saver)
            )
            self._validate_snapshot(paused, expect_paused=True)
        except (TypeError, ValueError):
            return _bounded_failure(
                    "resume_attempted",
                    "invalid_saved_graph_state",
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
        persisted = persist_final_state(
            deepcopy(dict(snapshot_values)), deepcopy(dict(final_config))
        )
        if not isinstance(persisted, DurableResumeResult):
            return _bounded_failure(
                "resume_attempted",
                "non_retryable_failure",
                graph_invocation_id=graph_invocation_id,
            )
        return persisted

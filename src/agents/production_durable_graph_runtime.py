"""Shared durable runtime for explicitly enabled production LangGraphs.

The runtime coordinates an injected durable repository and LangGraph saver. It
contains no production business logic and does not construct connections.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time
from typing import Any, Callable, Mapping

from src.storage.durable_orchestration import production


PRODUCTION_DURABLE_GRAPH_RUNTIME_FLAG = (
    "APPLYLENS_PRODUCTION_DURABLE_GRAPH_RUNTIME_ENABLED"
)
PRODUCTION_DURABLE_RUNTIME_VERSION = "production-durable-runtime-v1"
DEFAULT_LEASE_SECONDS = 300
MAX_FAILURE_CODE_LENGTH = 128
_ACCEPTED_WRITES = frozenset({"applied", "idempotent_existing"})


@dataclass(frozen=True, slots=True)
class ProductionExecutionIdentity:
    graph_run_row: Mapping[str, Any]
    graph_version: str
    state_version: str
    node_key: str
    input_digest: str
    checkpoint_namespace: str

    @property
    def graph_invocation_id(self) -> str:
        return str(self.graph_run_row["graph_invocation_id"])

    @property
    def owner_user_id(self) -> str:
        return str(self.graph_run_row["owner_user_id"])


class ProductionDurableRuntimeError(RuntimeError):
    def __init__(self, classification: str, reason_code: str) -> None:
        self.classification = str(classification or "non_retryable_failure")
        self.reason_code = str(reason_code or "durable_runtime_failed")[
            :MAX_FAILURE_CODE_LENGTH
        ]
        super().__init__(
            f"production_durable_runtime:{self.classification}:"
            f"{self.reason_code}"
        )


def _classification(result: Any) -> str:
    return str(getattr(result, "classification", "") or "")


def _thaw_repository_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _thaw_repository_value(nested)
            for key, nested in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_thaw_repository_value(nested) for nested in value]
    if isinstance(value, (set, frozenset)):
        return [
            _thaw_repository_value(nested)
            for nested in sorted(value, key=repr)
        ]
    return deepcopy(value)


def _record(result: Any) -> dict[str, Any]:
    value = getattr(result, "record", None)
    return _thaw_repository_value(value) if isinstance(value, Mapping) else {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProductionDurableRuntimeError(
            "identity_mismatch", f"{field}_required"
        )
    return text


def _job_identity(
    packet: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> tuple[str, str]:
    job = packet.get("job")
    payload_job = payload.get("job")
    snapshot = packet.get("job_snapshot")
    selection = payload.get("selection")
    job_id = str(
        packet.get("job_doc_id")
        or packet.get("job_id")
        or (job.get("job_doc_id") if isinstance(job, Mapping) else "")
        or (
            snapshot.get("job_doc_id")
            if isinstance(snapshot, Mapping)
            else ""
        )
        or (
            payload_job.get("job_doc_id")
            if isinstance(payload_job, Mapping)
            else ""
        )
        or ""
    ).strip()
    selected_resume = str(
        packet.get("selected_resume")
        or packet.get("selected_resume_name")
        or packet.get("resume_name")
        or (
            selection.get("selected_resume")
            if isinstance(selection, Mapping)
            else ""
        )
        or ""
    ).strip()
    return (
        _required_text(job_id, "job_id"),
        _required_text(selected_resume, "selected_resume_id"),
    )


def compute_tailoring_input_digest(
    *,
    packet: Mapping[str, Any],
    payload: Mapping[str, Any],
    refresh_llm_cache: bool,
    enable_safe_app_ready_rewrite_promotion: bool,
) -> str:
    return production.canonical_digest(
        {
            "packet": deepcopy(dict(packet)),
            "payload": deepcopy(dict(payload)),
            "refresh_llm_cache": bool(refresh_llm_cache),
            "safe_rewrite_promotion": bool(
                enable_safe_app_ready_rewrite_promotion
            ),
        },
        field="tailoring_generation_input",
    )


def build_tailoring_execution_identity(
    *,
    packet: Mapping[str, Any],
    payload: Mapping[str, Any],
    graph_version: str,
    state_version: str,
    node_key: str,
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
    job_index: int,
    refresh_llm_cache: bool,
    enable_safe_app_ready_rewrite_promotion: bool,
    created_at: str,
) -> ProductionExecutionIdentity:
    if isinstance(job_index, bool) or not isinstance(job_index, int):
        raise ProductionDurableRuntimeError(
            "identity_mismatch", "job_index_required"
        )
    job_id, selected_resume = _job_identity(packet, payload)
    input_digest = compute_tailoring_input_digest(
        packet=packet,
        payload=payload,
        refresh_llm_cache=refresh_llm_cache,
        enable_safe_app_ready_rewrite_promotion=(
            enable_safe_app_ready_rewrite_promotion
        ),
    )
    try:
        graph_run = production.prepare_graph_run_row(
            graph_version=graph_version,
            state_version=state_version,
            owner_user_id=owner_user_id,
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            job_id=job_id,
            job_index=job_index,
            selected_resume_id=selected_resume,
            production_node_key=node_key,
            input_digest=input_digest,
            created_at=created_at,
        )
    except ValueError as exc:
        raise ProductionDurableRuntimeError(
            "identity_mismatch", str(exc)
        ) from None
    namespace = (
        f"production/{node_key}/{graph_version}/{state_version}"
    )
    return ProductionExecutionIdentity(
        graph_run_row=graph_run,
        graph_version=graph_version,
        state_version=state_version,
        node_key=node_key,
        input_digest=input_digest,
        checkpoint_namespace=namespace,
    )


def _bounded_tailoring_result(result: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ProductionDurableRuntimeError(
            "non_retryable_failure", "tailoring_result_invalid"
        )
    bounded = deepcopy(dict(result))
    for key in (
        "raw_response",
        "retry_raw_response",
        "provider_response",
        "transport_response",
    ):
        if key in bounded:
            bounded[key] = ""
    try:
        serialized = production._bounded_mapping(
            bounded,
            field="bounded_tailoring_result",
            maximum=production.MAX_PRODUCTION_RESULT_BYTES // 2,
        )
    except ValueError as exc:
        raise ProductionDurableRuntimeError(
            "non_retryable_failure", str(exc)
        ) from None
    return serialized


def _saver_checkpoint_config(
    saver: Any,
    base_config: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        saved = saver.get_tuple(deepcopy(dict(base_config)))
    except Exception:
        raise ProductionDurableRuntimeError(
            "reconciliation_required", "saver_checkpoint_read_failed"
        ) from None
    config = getattr(saved, "config", None)
    configurable = (
        dict(config.get("configurable") or {})
        if isinstance(config, Mapping)
        else {}
    )
    thread_id = _required_text(
        configurable.get("thread_id"), "langgraph_thread_id"
    )
    checkpoint_id = _required_text(
        configurable.get("checkpoint_id"), "langgraph_checkpoint_id"
    )
    return {
        "thread_id": thread_id,
        "checkpoint_ns": str(configurable.get("checkpoint_ns") or ""),
        "checkpoint_id": checkpoint_id,
    }


def _validated_terminal_replay(
    terminal: Mapping[str, Any],
    identity: ProductionExecutionIdentity,
) -> dict[str, Any]:
    metadata = terminal.get("result_metadata_json")
    if not isinstance(metadata, Mapping):
        raise ProductionDurableRuntimeError(
            "reconciliation_required", "terminal_metadata_missing"
        )
    expected = {
        "contract_type": production.PRODUCTION_DURABLE_CONTRACT_TYPE,
        "contract_version": production.PRODUCTION_DURABLE_CONTRACT_VERSION,
        "production_graph_version": identity.graph_version,
        "production_state_version": identity.state_version,
        "production_node_key": identity.node_key,
        "input_digest": identity.input_digest,
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ProductionDurableRuntimeError(
            "identity_mismatch", "terminal_identity_mismatch"
        )
    result = metadata.get("bounded_result")
    if not isinstance(result, Mapping):
        raise ProductionDurableRuntimeError(
            "reconciliation_required", "terminal_result_missing"
        )
    return deepcopy(dict(result))


class ProductionDurableGraphRuntime:
    """Coordinate repository ownership, saver state, and one graph attempt."""

    def __init__(
        self,
        *,
        repository: Any,
        saver: Any,
        consumer_instance_id: str,
        enabled: bool = False,
        now_func: Callable[[], datetime] = _utc_now,
    ) -> None:
        if enabled is not True:
            raise ProductionDurableRuntimeError(
                "unavailable", "production_durable_runtime_disabled"
            )
        if repository is None:
            raise ProductionDurableRuntimeError(
                "unavailable", "durable_repository_required"
            )
        if saver is None:
            raise ProductionDurableRuntimeError(
                "unavailable", "langgraph_saver_required"
            )
        if not callable(now_func):
            raise TypeError("now_func_must_be_callable")
        self._repository = repository
        self._saver = saver
        self._consumer_instance_id = _required_text(
            consumer_instance_id, "consumer_instance_id"
        )
        self._now = now_func

    def _read_completed(
        self,
        identity: ProductionExecutionIdentity,
    ) -> dict[str, Any] | None:
        result = self._repository.read_terminal_result(
            owner_user_id=identity.owner_user_id,
            graph_invocation_id=identity.graph_invocation_id,
        )
        classification = _classification(result)
        if classification == "not_found":
            return None
        if classification != "applied":
            raise ProductionDurableRuntimeError(
                classification or "reconciliation_required",
                "terminal_read_failed",
            )
        terminal = _record(result)
        if terminal.get("terminal_status") != "completed":
            raise ProductionDurableRuntimeError(
                "already_terminal", "terminal_not_completed"
            )
        replay = _validated_terminal_replay(terminal, identity)
        checkpoint_id = _required_text(
            terminal.get("terminal_checkpoint_id"),
            "terminal_checkpoint_id",
        )
        binding = self._repository.read_checkpoint_binding(
            owner_user_id=identity.owner_user_id,
            graph_invocation_id=identity.graph_invocation_id,
            repository_checkpoint_id=checkpoint_id,
        )
        if _classification(binding) != "applied":
            raise ProductionDurableRuntimeError(
                "reconciliation_required", "checkpoint_binding_missing"
            )
        binding_payload = _record(binding).get("event_payload_json")
        if not isinstance(binding_payload, Mapping):
            raise ProductionDurableRuntimeError(
                "reconciliation_required", "checkpoint_binding_invalid"
            )
        saved = _saver_checkpoint_config(
            self._saver,
            {
                "configurable": {
                    "thread_id": binding_payload.get(
                        "langgraph_thread_id"
                    ),
                    "checkpoint_ns": binding_payload.get(
                        "langgraph_checkpoint_namespace"
                    ),
                    "checkpoint_id": binding_payload.get(
                        "langgraph_checkpoint_id"
                    ),
                }
            },
        )
        if (
            saved["thread_id"]
            != binding_payload.get("langgraph_thread_id")
            or saved["checkpoint_id"]
            != binding_payload.get("langgraph_checkpoint_id")
        ):
            raise ProductionDurableRuntimeError(
                "reconciliation_required", "saver_binding_mismatch"
            )
        return replay

    def execute(
        self,
        *,
        identity: ProductionExecutionIdentity,
        invoke_graph: Callable[[Any, Mapping[str, Any]], Mapping[str, Any]],
    ) -> dict[str, Any]:
        replay = self._read_completed(identity)
        if replay is not None:
            return {
                "tailoring_result": replay,
                "execution_metadata": {
                    "execution_mode": "langgraph",
                    "production_node_count": 1,
                    "node_invocation_count": 0,
                    "tailoring_owner_invocation_count": 0,
                    "critic_invocation_count": 0,
                    "status": "completed",
                    "durable_runtime_version": (
                        PRODUCTION_DURABLE_RUNTIME_VERSION
                    ),
                    "durable_status": "completed_replay",
                    "graph_invocation_count": 0,
                    "tailoring_owner_invocation_count": 0,
                    "provider_call_count": 0,
                    "cache_write_count": 0,
                    "graph_invocation_id": identity.graph_invocation_id,
                    "input_digest": identity.input_digest,
                    "mutation_authority": False,
                    "application_authority": False,
                    "ats_authority": False,
                },
            }

        created = self._repository.create_production_graph_run(
            identity.graph_run_row
        )
        if _classification(created) not in _ACCEPTED_WRITES:
            raise ProductionDurableRuntimeError(
                _classification(created) or "duplicate_conflict",
                "production_graph_run_create_failed",
            )
        if _classification(created) == "idempotent_existing":
            replay = self._read_completed(identity)
            if replay is not None:
                return {
                    "tailoring_result": replay,
                    "execution_metadata": {
                        "execution_mode": "langgraph",
                        "production_node_count": 1,
                        "node_invocation_count": 0,
                        "tailoring_owner_invocation_count": 0,
                        "critic_invocation_count": 0,
                        "status": "completed",
                        "durable_runtime_version": (
                            PRODUCTION_DURABLE_RUNTIME_VERSION
                        ),
                        "durable_status": "completed_replay",
                        "graph_invocation_count": 0,
                        "tailoring_owner_invocation_count": 0,
                        "provider_call_count": 0,
                        "cache_write_count": 0,
                        "graph_invocation_id": identity.graph_invocation_id,
                        "input_digest": identity.input_digest,
                        "mutation_authority": False,
                        "application_authority": False,
                        "ats_authority": False,
                    },
                }

        started_at = self._now()
        started_text = _timestamp(started_at)
        initial_checkpoint = production.prepare_checkpoint_row(
            identity.graph_run_row,
            production_node_key=identity.node_key,
            input_digest=identity.input_digest,
            checkpoint_sequence=0,
            bounded_execution_state={
                "status": "pending",
                "completed_node_keys": [],
                "next_node_key": identity.node_key,
            },
            completed_node_keys=[],
            next_node_key=identity.node_key,
            committed_at=started_text,
        )
        attempt = production.prepare_node_attempt_row(
            identity.graph_run_row,
            input_checkpoint_id=initial_checkpoint["checkpoint_id"],
            production_node_key=identity.node_key,
            input_digest=identity.input_digest,
            created_at=started_text,
        )
        started = self._repository.start_production_attempt(
            identity.graph_run_row,
            initial_checkpoint,
            attempt,
        )
        if _classification(started) not in _ACCEPTED_WRITES:
            raise ProductionDurableRuntimeError(
                _classification(started) or "duplicate_conflict",
                "production_attempt_in_progress",
            )
        active_run = {
            **dict(identity.graph_run_row),
            "run_status": "resumed",
            "current_checkpoint_id": initial_checkpoint["checkpoint_id"],
            "lock_version": 1,
            "updated_at": started_text,
        }
        claim_event = production.prepare_lifecycle_event_row(
            active_run,
            event_type="node_attempt_claimed",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=0,
            event_payload={
                "production_node_key": identity.node_key,
                "input_digest": identity.input_digest,
                "attempt_status": "claimed",
            },
            event_timestamp=started_text,
            references={"node_attempt_id": attempt["node_attempt_id"]},
        )
        claimed = self._repository.claim_attempt(
            attempt,
            claim_event,
            lease_owner_id=self._consumer_instance_id,
            lease_acquired_at=started_text,
            lease_expires_at=_timestamp(
                started_at + timedelta(seconds=DEFAULT_LEASE_SECONDS)
            ),
            expected_lock_version=0,
            expected_run_lock_version=1,
        )
        if _classification(claimed) != "applied":
            raise ProductionDurableRuntimeError(
                _classification(claimed) or "stale_state",
                "production_attempt_claim_conflict",
            )
        claimed_attempt = _record(claimed)
        config = {
            "configurable": {
                "thread_id": identity.graph_invocation_id,
                "checkpoint_ns": "",
                "applylens_production_checkpoint_namespace": (
                    identity.checkpoint_namespace
                ),
            }
        }
        try:
            graph_result = invoke_graph(self._saver, deepcopy(config))
            if not isinstance(graph_result, Mapping):
                raise ValueError("graph_result_invalid")
            tailoring_result = graph_result.get("tailoring_result")
            execution_metadata = graph_result.get("execution_metadata")
            if (
                not isinstance(tailoring_result, Mapping)
                or not isinstance(execution_metadata, Mapping)
            ):
                raise ValueError("graph_result_contract_invalid")
            bounded_result = _bounded_tailoring_result(tailoring_result)
            saved_config = _saver_checkpoint_config(self._saver, config)
        except Exception as exc:
            if isinstance(exc, ProductionDurableRuntimeError):
                reason = exc.reason_code
            else:
                reason = "authoritative_graph_failed"
            failed_at = _timestamp(self._now())
            failure_event = production.prepare_lifecycle_event_row(
                active_run,
                event_type="node_attempt_failed",
                aggregate_type="node_attempt",
                aggregate_id=attempt["node_attempt_id"],
                event_sequence=1,
                event_payload={
                    "production_node_key": identity.node_key,
                    "failure_code": reason,
                },
                event_timestamp=failed_at,
                references={"node_attempt_id": attempt["node_attempt_id"]},
            )
            self._repository.record_attempt_failure(
                claimed_attempt,
                failure_event,
                error_code=reason,
                error_detail="",
                completed_at=failed_at,
                lease_owner_id=self._consumer_instance_id,
                expected_lock_version=1,
                expected_run_lock_version=1,
            )
            raise ProductionDurableRuntimeError(
                "retryable_failure", reason
            ) from None

        completed_at = self._now()
        completed_text = _timestamp(completed_at)
        final_checkpoint = production.prepare_checkpoint_row(
            active_run,
            production_node_key=identity.node_key,
            input_digest=identity.input_digest,
            checkpoint_sequence=1,
            bounded_execution_state={
                "status": "completed",
                "completed_node_keys": [identity.node_key],
                "next_node_key": production.PRODUCTION_END_NODE,
                "execution_metadata": deepcopy(dict(execution_metadata)),
            },
            completed_node_keys=[identity.node_key],
            next_node_key=production.PRODUCTION_END_NODE,
            committed_at=completed_text,
        )
        committed = self._repository.commit_production_checkpoint(
            final_checkpoint,
            parent_checkpoint_id=initial_checkpoint["checkpoint_id"],
            expected_run_lock_version=1,
        )
        if _classification(committed) not in _ACCEPTED_WRITES:
            raise ProductionDurableRuntimeError(
                "reconciliation_required", "repository_checkpoint_failed"
            )
        binding = production.prepare_checkpoint_binding_row(
            active_run,
            repository_checkpoint_id=final_checkpoint["checkpoint_id"],
            langgraph_thread_id=saved_config["thread_id"],
            langgraph_checkpoint_namespace=saved_config["checkpoint_ns"],
            langgraph_checkpoint_id=saved_config["checkpoint_id"],
            event_timestamp=completed_text,
        )
        bound = self._repository.commit_checkpoint_binding(binding)
        if _classification(bound) not in _ACCEPTED_WRITES:
            raise ProductionDurableRuntimeError(
                "reconciliation_required", "checkpoint_binding_failed"
            )
        success_event = production.prepare_lifecycle_event_row(
            active_run,
            event_type="node_attempt_succeeded",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=2,
            event_payload={
                "production_node_key": identity.node_key,
                "input_digest": identity.input_digest,
                "output_digest": final_checkpoint[
                    "checkpoint_envelope_digest"
                ],
            },
            event_timestamp=completed_text,
            references={
                "checkpoint_id": final_checkpoint["checkpoint_id"],
                "node_attempt_id": attempt["node_attempt_id"],
            },
        )
        succeeded = self._repository.record_attempt_success(
            claimed_attempt,
            success_event,
            output_checkpoint_id=final_checkpoint["checkpoint_id"],
            output_digest=final_checkpoint["checkpoint_envelope_digest"],
            completed_at=completed_text,
            duration_ms=max(
                0,
                int((completed_at - started_at).total_seconds() * 1000),
            ),
            lease_owner_id=self._consumer_instance_id,
            expected_lock_version=1,
            expected_run_lock_version=1,
        )
        if _classification(succeeded) not in _ACCEPTED_WRITES:
            raise ProductionDurableRuntimeError(
                "reconciliation_required", "attempt_success_failed"
            )
        successful_attempt = _record(succeeded)
        completed_run = {
            **active_run,
            "current_checkpoint_id": final_checkpoint["checkpoint_id"],
            "lock_version": 2,
            "updated_at": completed_text,
        }
        terminal = production.prepare_terminal_result_row(
            completed_run,
            terminal_checkpoint_id=final_checkpoint["checkpoint_id"],
            production_node_key=identity.node_key,
            input_digest=identity.input_digest,
            bounded_result=bounded_result,
            completed_at=completed_text,
        )
        terminal_event = production.prepare_lifecycle_event_row(
            completed_run,
            event_type="terminal_result_recorded",
            aggregate_type="graph_run",
            aggregate_id=identity.graph_invocation_id,
            event_sequence=3,
            event_payload={
                "production_node_key": identity.node_key,
                "input_digest": identity.input_digest,
                "terminal_status": "completed",
            },
            event_timestamp=completed_text,
            references={
                "checkpoint_id": final_checkpoint["checkpoint_id"],
                "node_attempt_id": attempt["node_attempt_id"],
                "terminal_result_id": terminal["terminal_result_id"],
            },
        )
        terminalized = self._repository.terminalize_production_run(
            completed_run,
            terminal,
            terminal_event,
            successful_attempt_row=successful_attempt,
            final_binding_row=binding,
            expected_run_lock_version=2,
        )
        if _classification(terminalized) not in _ACCEPTED_WRITES:
            raise ProductionDurableRuntimeError(
                "reconciliation_required", "terminalization_failed"
            )
        return {
            "tailoring_result": bounded_result,
            "execution_metadata": {
                **deepcopy(dict(execution_metadata)),
                "durable_runtime_version": PRODUCTION_DURABLE_RUNTIME_VERSION,
                "durable_status": "completed",
                "graph_invocation_count": 1,
                "graph_invocation_id": identity.graph_invocation_id,
                "input_digest": identity.input_digest,
                "repository_checkpoint_id": final_checkpoint["checkpoint_id"],
                "langgraph_thread_id": saved_config["thread_id"],
                "langgraph_checkpoint_namespace": saved_config[
                    "checkpoint_ns"
                ],
                "langgraph_checkpoint_id": saved_config["checkpoint_id"],
                "mutation_authority": False,
                "application_authority": False,
                "ats_authority": False,
            },
        }


__all__ = [
    "DEFAULT_LEASE_SECONDS",
    "PRODUCTION_DURABLE_GRAPH_RUNTIME_FLAG",
    "PRODUCTION_DURABLE_RUNTIME_VERSION",
    "ProductionDurableGraphRuntime",
    "ProductionDurableRuntimeError",
    "ProductionExecutionIdentity",
    "build_tailoring_execution_identity",
    "compute_tailoring_input_digest",
]

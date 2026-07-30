"""Generic production-graph rows and SQL for durable orchestration.

This module is deliberately separate from the evidence-chain checkpoint
contract.  It reuses only the storage package's generic canonical JSON,
secret-rejection, digest, transaction-command, and bounded-row primitives.
It opens no connection and executes no SQL.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any, Mapping

from src.storage.durable_orchestration import store


PRODUCTION_DURABLE_CONTRACT_TYPE = "production_graph_execution"
PRODUCTION_DURABLE_CONTRACT_VERSION = "production-durable-contract-v1"
PRODUCTION_CHECKPOINT_SCHEMA_VERSION = "production-graph-checkpoint-v1"
PRODUCTION_CHECKPOINT_STATUS = "production_execution"
PRODUCTION_GRAPH_ENGINE_PREFIX = "langgraph-production:"
PRODUCTION_END_NODE = "__end__"
MAX_PRODUCTION_STATE_BYTES = 262_144
MAX_PRODUCTION_RESULT_BYTES = 262_144
PRODUCTION_HUMAN_REVIEW_CONTRACT_VERSION = (
    "production-human-review-contract-v1"
)
PRODUCTION_HUMAN_REVIEW_CHECKPOINT_VERSION = (
    "production-human-review-checkpoint-v1"
)
PRODUCTION_HUMAN_REVIEW_INTERRUPT_VERSION = (
    "production-human-review-interrupt-v1"
)
PRODUCTION_HUMAN_REVIEW_NODE = "operator_review"
PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE = "finalize"
PRODUCTION_HUMAN_REVIEW_DECISIONS = (
    "continue_read_only",
    "needs_revision",
    "cancel",
)
PRODUCTION_TAILORING_REVIEW_ARTIFACT_TYPE = (
    "bounded_tailoring_result_digest"
)
PRODUCTION_TAILORING_REVIEW_ARTIFACT_VERSION = (
    "bounded-tailoring-result-digest-v1"
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _required(value: Any, field: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        raise ValueError(f"{field}_required")
    return cleaned


def _version(value: Any, field: str) -> str:
    cleaned = _required(value, field)
    if re.fullmatch(r"[a-z0-9][a-z0-9._:-]{0,127}", cleaned) is None:
        raise ValueError(f"{field}_invalid")
    return cleaned


def _node(value: Any) -> str:
    cleaned = _required(value, "production_node_key")
    if re.fullmatch(r"[a-z][a-z0-9_]{0,127}", cleaned) is None:
        raise ValueError("production_node_key_invalid")
    return cleaned


def _nonnegative(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field}_invalid")
    return value


def _digest(value: Any, field: str) -> str:
    cleaned = _clean(value)
    if re.fullmatch(r"[0-9a-f]{64}", cleaned) is None:
        raise ValueError(f"{field}_invalid")
    return cleaned


def _canonical(value: Any, field: str) -> str:
    store._reject_prohibited_payload(value, field_path=field)
    return store._canonical_json(value, field_path=field)


def canonical_digest(value: Any, *, field: str = "production_value") -> str:
    return hashlib.sha256(_canonical(value, field).encode("utf-8")).hexdigest()


def _bounded_mapping(
    value: Mapping[str, Any],
    *,
    field: str,
    maximum: int,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field}_must_be_mapping")
    serialized = _canonical(value, field)
    if len(serialized.encode("utf-8")) > maximum:
        raise ValueError(f"{field}_too_large")
    normalized = json.loads(serialized)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field}_must_be_object")
    return normalized


def _graph_engine(graph_version: str) -> str:
    return f"{PRODUCTION_GRAPH_ENGINE_PREFIX}{graph_version}"


def _validate_graph_run(row: Mapping[str, Any]) -> dict[str, Any]:
    store._require_exact_fields(row, store._GRAPH_RUN_COLUMNS, "production_graph_run")
    graph_engine = _clean(row.get("graph_engine"))
    if not graph_engine.startswith(PRODUCTION_GRAPH_ENGINE_PREFIX):
        raise ValueError("production_graph_engine_invalid")
    _version(
        graph_engine[len(PRODUCTION_GRAPH_ENGINE_PREFIX) :],
        "production_graph_version",
    )
    _version(row.get("graph_state_schema_version"), "production_state_version")
    for field in (
        "graph_invocation_id",
        "owner_user_id",
        "pipeline_run_id",
        "context_id",
        "job_id",
        "selected_resume_id",
        "created_at",
        "updated_at",
    ):
        _required(row.get(field), field)
    _nonnegative(row.get("job_index"), "job_index")
    _nonnegative(row.get("lock_version"), "lock_version")
    if row.get("run_status") not in store.GRAPH_RUN_STATUS_VALUES:
        raise ValueError("graph_run_status_unsupported")
    store._reject_prohibited_payload(row, field_path="production_graph_run")
    return deepcopy(dict(row))


def prepare_graph_run_row(
    *,
    graph_version: str,
    state_version: str,
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
    job_id: str,
    job_index: int,
    selected_resume_id: str,
    production_node_key: str,
    input_digest: str,
    created_at: str,
) -> dict[str, Any]:
    graph = _version(graph_version, "production_graph_version")
    state = _version(state_version, "production_state_version")
    node = _node(production_node_key)
    identity = {
        "contract_type": PRODUCTION_DURABLE_CONTRACT_TYPE,
        "contract_version": PRODUCTION_DURABLE_CONTRACT_VERSION,
        "graph_engine": _graph_engine(graph),
        "production_graph_version": graph,
        "production_state_version": state,
        "owner_user_id": _required(owner_user_id, "owner_user_id"),
        "pipeline_run_id": _required(pipeline_run_id, "pipeline_run_id"),
        "context_id": _required(context_id, "context_id"),
        "job_id": _required(job_id, "job_id"),
        "job_index": _nonnegative(job_index, "job_index"),
        "selected_resume_id": _required(
            selected_resume_id, "selected_resume_id"
        ),
        "production_node_key": node,
        "input_digest": _digest(input_digest, "input_digest"),
    }
    graph_invocation_id = (
        "production-graph:"
        + canonical_digest(identity, field="production_graph_identity")
    )
    timestamp = _required(created_at, "created_at")
    row = {
        "graph_invocation_id": graph_invocation_id,
        "graph_engine": identity["graph_engine"],
        "graph_state_schema_version": state,
        "owner_user_id": identity["owner_user_id"],
        "pipeline_run_id": identity["pipeline_run_id"],
        "context_id": identity["context_id"],
        "job_id": identity["job_id"],
        "job_index": identity["job_index"],
        "selected_resume_id": identity["selected_resume_id"],
        "run_status": "running",
        "current_checkpoint_id": None,
        "lock_version": 0,
        "created_at": timestamp,
        "updated_at": timestamp,
        "terminal_at": None,
        "purge_after": None,
    }
    return _validate_graph_run(row)


def production_identity_from_graph_run(
    graph_run_row: Mapping[str, Any],
    *,
    production_node_key: str,
    input_digest: str,
) -> dict[str, Any]:
    row = _validate_graph_run(graph_run_row)
    graph_version = row["graph_engine"][len(PRODUCTION_GRAPH_ENGINE_PREFIX) :]
    return {
        "contract_type": PRODUCTION_DURABLE_CONTRACT_TYPE,
        "contract_version": PRODUCTION_DURABLE_CONTRACT_VERSION,
        "graph_engine": row["graph_engine"],
        "production_graph_version": graph_version,
        "production_state_version": row["graph_state_schema_version"],
        "owner_user_id": row["owner_user_id"],
        "pipeline_run_id": row["pipeline_run_id"],
        "context_id": row["context_id"],
        "job_id": row["job_id"],
        "job_index": row["job_index"],
        "selected_resume_id": row["selected_resume_id"],
        "production_node_key": _node(production_node_key),
        "input_digest": _digest(input_digest, "input_digest"),
        "graph_invocation_id": row["graph_invocation_id"],
    }


def prepare_checkpoint_row(
    graph_run_row: Mapping[str, Any],
    *,
    production_node_key: str,
    input_digest: str,
    checkpoint_sequence: int,
    bounded_execution_state: Mapping[str, Any],
    completed_node_keys: list[str],
    next_node_key: str,
    committed_at: str,
) -> dict[str, Any]:
    row = _validate_graph_run(graph_run_row)
    identity = production_identity_from_graph_run(
        row,
        production_node_key=production_node_key,
        input_digest=input_digest,
    )
    sequence = _nonnegative(checkpoint_sequence, "checkpoint_sequence")
    node = identity["production_node_key"]
    completed = [_node(item) for item in completed_node_keys]
    if len(completed) != len(set(completed)) or any(
        item != node for item in completed
    ):
        raise ValueError("completed_node_keys_invalid")
    next_node = _clean(next_node_key)
    if next_node not in {node, PRODUCTION_END_NODE}:
        raise ValueError("next_node_key_invalid")
    if sequence == 0 and (completed or next_node != node):
        raise ValueError("initial_checkpoint_position_invalid")
    if sequence > 0 and (
        completed != [node] or next_node != PRODUCTION_END_NODE
    ):
        raise ValueError("terminal_checkpoint_position_invalid")
    state = _bounded_mapping(
        bounded_execution_state,
        field="bounded_execution_state",
        maximum=MAX_PRODUCTION_STATE_BYTES,
    )
    envelope_base = {
        **identity,
        "checkpoint_schema_version": PRODUCTION_CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_status": PRODUCTION_CHECKPOINT_STATUS,
        "checkpoint_sequence": sequence,
        "input_digest": identity["input_digest"],
        "completed_node_keys": completed,
        "next_node_key": next_node,
        "bounded_execution_state": state,
        "production_execution": True,
        "diagnostic_only": False,
        "read_only": True,
        "durable": True,
        "application_authorization": False,
        "mutation_authorization": False,
        "ats_authorization": False,
    }
    checkpoint_id = (
        "production-checkpoint:"
        + canonical_digest(
            envelope_base, field="production_checkpoint_identity"
        )
    )
    envelope = {**envelope_base, "checkpoint_id": checkpoint_id}
    return {
        "checkpoint_id": checkpoint_id,
        "graph_invocation_id": row["graph_invocation_id"],
        "checkpoint_sequence": sequence,
        "checkpoint_schema_version": PRODUCTION_CHECKPOINT_SCHEMA_VERSION,
        "graph_state_schema_version": row["graph_state_schema_version"],
        "checkpoint_status": PRODUCTION_CHECKPOINT_STATUS,
        **{
            field: deepcopy(row[field])
            for field in store._IDENTITY_COLUMNS
        },
        "checkpoint_envelope_json": envelope,
        "checkpoint_envelope_digest": canonical_digest(
            envelope, field="production_checkpoint_envelope"
        ),
        "completed_node_keys_json": completed,
        "next_node_key": next_node,
        "committed_at": _required(committed_at, "committed_at"),
        "purge_after": None,
    }


def _validate_checkpoint(row: Mapping[str, Any]) -> dict[str, Any]:
    store._require_exact_fields(
        row, store._CHECKPOINT_COLUMNS, "production_checkpoint"
    )
    if (
        row.get("checkpoint_schema_version")
        != PRODUCTION_CHECKPOINT_SCHEMA_VERSION
        or row.get("checkpoint_status") != PRODUCTION_CHECKPOINT_STATUS
    ):
        raise ValueError("production_checkpoint_contract_invalid")
    envelope = row.get("checkpoint_envelope_json")
    if not isinstance(envelope, Mapping):
        raise ValueError("production_checkpoint_envelope_invalid")
    required = {
        "contract_type": PRODUCTION_DURABLE_CONTRACT_TYPE,
        "contract_version": PRODUCTION_DURABLE_CONTRACT_VERSION,
        "checkpoint_schema_version": PRODUCTION_CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_status": PRODUCTION_CHECKPOINT_STATUS,
        "checkpoint_id": row.get("checkpoint_id"),
        "graph_invocation_id": row.get("graph_invocation_id"),
        "production_state_version": row.get("graph_state_schema_version"),
        "checkpoint_sequence": row.get("checkpoint_sequence"),
        "completed_node_keys": row.get("completed_node_keys_json"),
        "next_node_key": row.get("next_node_key"),
        "production_execution": True,
        "diagnostic_only": False,
        "read_only": True,
        "application_authorization": False,
        "mutation_authorization": False,
        "ats_authorization": False,
    }
    if any(envelope.get(key) != value for key, value in required.items()):
        raise ValueError("production_checkpoint_envelope_mismatch")
    if row.get("checkpoint_envelope_digest") != canonical_digest(
        envelope, field="production_checkpoint_envelope"
    ):
        raise ValueError("production_checkpoint_digest_mismatch")
    _bounded_mapping(
        envelope,
        field="production_checkpoint_envelope",
        maximum=store.MAX_CHECKPOINT_ENVELOPE_BYTES,
    )
    return deepcopy(dict(row))


def prepare_node_attempt_row(
    graph_run_row: Mapping[str, Any],
    *,
    input_checkpoint_id: str,
    production_node_key: str,
    input_digest: str,
    created_at: str,
) -> dict[str, Any]:
    graph = _validate_graph_run(graph_run_row)
    node = _node(production_node_key)
    checkpoint_id = _required(input_checkpoint_id, "input_checkpoint_id")
    seed = {
        "graph_invocation_id": graph["graph_invocation_id"],
        "input_checkpoint_id": checkpoint_id,
        "production_node_key": node,
        "input_digest": _digest(input_digest, "input_digest"),
        "attempt_number": 1,
    }
    return {
        "node_attempt_id": (
            "production-attempt:"
            + canonical_digest(seed, field="production_attempt_identity")
        ),
        "graph_invocation_id": graph["graph_invocation_id"],
        "input_checkpoint_id": checkpoint_id,
        "output_checkpoint_id": None,
        **{
            field: deepcopy(graph[field])
            for field in store._IDENTITY_COLUMNS
        },
        "node_key": node,
        "attempt_number": 1,
        "resume_invocation_id": None,
        "attempt_status": "pending",
        "lease_owner_id": None,
        "lease_acquired_at": None,
        "lease_expires_at": None,
        "started_at": None,
        "completed_at": None,
        "duration_ms": None,
        "input_digest": seed["input_digest"],
        "output_digest": None,
        "error_code": "",
        "error_detail": "",
        "lock_version": 0,
        "application_authorization": False,
        "mutation_authorization": False,
        "created_at": _required(created_at, "created_at"),
        "updated_at": _required(created_at, "created_at"),
    }


def prepare_lifecycle_event_row(
    graph_run_row: Mapping[str, Any],
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    event_sequence: int,
    event_payload: Mapping[str, Any],
    event_timestamp: str,
    references: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    graph = _validate_graph_run(graph_run_row)
    event = _required(event_type, "event_type")
    if event not in store.LIFECYCLE_EVENT_TYPE_VALUES:
        raise ValueError("event_type_unsupported")
    aggregate = _required(aggregate_type, "aggregate_type")
    aggregate_key = _required(aggregate_id, "aggregate_id")
    refs = dict(references or {})
    allowed = {
        "checkpoint_id",
        "interrupt_request_id",
        "decision_id",
        "authorization_id",
        "consumption_id",
        "node_attempt_id",
        "terminal_result_id",
    }
    if set(refs) - allowed:
        raise ValueError("lifecycle_event_reference_fields_invalid")
    normalized_refs = {
        key: (_clean(refs.get(key)) or None) for key in allowed
    }
    payload = _bounded_mapping(
        event_payload,
        field="production_lifecycle_event",
        maximum=MAX_PRODUCTION_STATE_BYTES,
    )
    seed = {
        "graph_invocation_id": graph["graph_invocation_id"],
        "event_type": event,
        "aggregate_type": aggregate,
        "aggregate_id": aggregate_key,
        "event_sequence": _nonnegative(event_sequence, "event_sequence"),
        "references": normalized_refs,
        "payload_digest": canonical_digest(
            payload, field="production_lifecycle_payload"
        ),
    }
    return {
        "event_id": (
            "production-event:"
            + canonical_digest(seed, field="production_lifecycle_identity")
        ),
        "graph_invocation_id": graph["graph_invocation_id"],
        **normalized_refs,
        "owner_user_id": graph["owner_user_id"],
        "event_type": event,
        "aggregate_type": aggregate,
        "aggregate_id": aggregate_key,
        "event_sequence": seed["event_sequence"],
        "event_payload_json": payload,
        "event_timestamp": _required(event_timestamp, "event_timestamp"),
        "projection_status": "pending",
        "projected_at": None,
        "projection_retry_count": 0,
    }


def prepare_checkpoint_binding_row(
    graph_run_row: Mapping[str, Any],
    *,
    repository_checkpoint_id: str,
    langgraph_thread_id: str,
    langgraph_checkpoint_namespace: str,
    langgraph_checkpoint_id: str,
    event_timestamp: str,
) -> dict[str, Any]:
    repository_id = _required(
        repository_checkpoint_id, "repository_checkpoint_id"
    )
    thread_id = _required(langgraph_thread_id, "langgraph_thread_id")
    saver_checkpoint = _required(
        langgraph_checkpoint_id, "langgraph_checkpoint_id"
    )
    payload = {
        "binding_schema_version": store.LANGGRAPH_CHECKPOINT_BINDING_SCHEMA_VERSION,
        "graph_invocation_id": graph_run_row.get("graph_invocation_id"),
        "repository_checkpoint_id": repository_id,
        "langgraph_thread_id": thread_id,
        "langgraph_checkpoint_namespace": _clean(
            langgraph_checkpoint_namespace
        ),
        "langgraph_checkpoint_id": saver_checkpoint,
    }
    row = prepare_lifecycle_event_row(
        graph_run_row,
        event_type="checkpoint_committed",
        aggregate_type=store.LANGGRAPH_CHECKPOINT_BINDING_AGGREGATE_TYPE,
        aggregate_id=repository_id,
        event_sequence=0,
        event_payload=payload,
        event_timestamp=event_timestamp,
        references={"checkpoint_id": repository_id},
    )
    normalized_refs = {
        key: row[key]
        for key in (
            "checkpoint_id",
            "interrupt_request_id",
            "decision_id",
            "authorization_id",
            "consumption_id",
            "node_attempt_id",
            "terminal_result_id",
        )
    }
    row["event_id"] = store._deterministic_id(
        "lifecycle-event",
        {
            "graph_invocation_id": row["graph_invocation_id"],
            "event_type": row["event_type"],
            "aggregate_type": row["aggregate_type"],
            "aggregate_id": row["aggregate_id"],
            "event_sequence": row["event_sequence"],
            "references": normalized_refs,
            "payload_digest": canonical_digest(
                payload,
                field="checkpoint_binding_payload",
            ),
        },
    )
    return row


def prepare_terminal_result_row(
    graph_run_row: Mapping[str, Any],
    *,
    terminal_checkpoint_id: str,
    production_node_key: str,
    input_digest: str,
    bounded_result: Mapping[str, Any],
    completed_at: str,
    terminal_status: str = "completed",
    failure_code: str = "",
) -> dict[str, Any]:
    graph = _validate_graph_run(graph_run_row)
    node = _node(production_node_key)
    status = _clean(terminal_status)
    if status not in store.TERMINAL_STATUS_VALUES:
        raise ValueError("terminal_status_unsupported")
    failure = _clean(failure_code)
    if (status == "failed") != bool(failure):
        raise ValueError("terminal_failure_code_invalid")
    result = _bounded_mapping(
        bounded_result,
        field="production_terminal_result",
        maximum=MAX_PRODUCTION_RESULT_BYTES,
    )
    metadata = {
        "contract_type": PRODUCTION_DURABLE_CONTRACT_TYPE,
        "contract_version": PRODUCTION_DURABLE_CONTRACT_VERSION,
        "production_graph_version": graph["graph_engine"][
            len(PRODUCTION_GRAPH_ENGINE_PREFIX) :
        ],
        "production_state_version": graph["graph_state_schema_version"],
        "production_node_key": node,
        "input_digest": _digest(input_digest, "input_digest"),
        "bounded_result": result,
        "application_authorization": False,
        "mutation_authorization": False,
        "ats_authorization": False,
    }
    result_digest = canonical_digest(
        metadata, field="production_terminal_metadata"
    )
    checkpoint_id = _required(
        terminal_checkpoint_id, "terminal_checkpoint_id"
    )
    seed = {
        "graph_invocation_id": graph["graph_invocation_id"],
        "terminal_checkpoint_id": checkpoint_id,
        "terminal_status": status,
        "result_digest": result_digest,
    }
    return {
        "terminal_result_id": (
            "production-terminal:"
            + canonical_digest(seed, field="production_terminal_identity")
        ),
        "graph_invocation_id": graph["graph_invocation_id"],
        "terminal_checkpoint_id": checkpoint_id,
        **{
            field: deepcopy(graph[field])
            for field in store._IDENTITY_COLUMNS
        },
        "graph_state_schema_version": graph["graph_state_schema_version"],
        "checkpoint_schema_version": PRODUCTION_CHECKPOINT_SCHEMA_VERSION,
        "terminal_status": status,
        "result_digest": result_digest,
        "result_metadata_json": metadata,
        "final_node_order_json": [node],
        "failure_code": failure,
        "application_authorization": False,
        "completed_at": _required(completed_at, "completed_at"),
    }


def prepare_human_review_checkpoint_row(
    graph_run_row: Mapping[str, Any],
    *,
    artifact_digest: str,
    saved_state_digest: str,
    committed_at: str,
    checkpoint_sequence: int = 1,
    human_review_status: str = "awaiting_review",
) -> dict[str, Any]:
    """Build a production checkpoint that retains only review-safe digests."""
    graph = _validate_graph_run(graph_run_row)
    if graph["run_status"] != "running":
        raise ValueError("production_human_review_run_not_running")
    artifact = _digest(artifact_digest, "artifact_digest")
    saved_state = _digest(saved_state_digest, "saved_state_digest")
    sequence = _nonnegative(checkpoint_sequence, "checkpoint_sequence")
    if sequence != 1:
        raise ValueError("production_human_review_sequence_invalid")
    if _clean(human_review_status) != "awaiting_review":
        raise ValueError("production_human_review_status_invalid")
    envelope_base = {
        "contract_type": PRODUCTION_DURABLE_CONTRACT_TYPE,
        "contract_version": PRODUCTION_DURABLE_CONTRACT_VERSION,
        "human_review_contract_version": (
            PRODUCTION_HUMAN_REVIEW_CONTRACT_VERSION
        ),
        "checkpoint_schema_version": (
            PRODUCTION_HUMAN_REVIEW_CHECKPOINT_VERSION
        ),
        "checkpoint_status": PRODUCTION_CHECKPOINT_STATUS,
        "graph_invocation_id": graph["graph_invocation_id"],
        "graph_engine": graph["graph_engine"],
        "production_state_version": graph["graph_state_schema_version"],
        **{
            field: deepcopy(graph[field])
            for field in store._IDENTITY_COLUMNS
        },
        "checkpoint_sequence": sequence,
        "completed_node_keys": [PRODUCTION_HUMAN_REVIEW_NODE],
        "next_node_key": PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
        "review_artifact_type": PRODUCTION_TAILORING_REVIEW_ARTIFACT_TYPE,
        "review_artifact_version": (
            PRODUCTION_TAILORING_REVIEW_ARTIFACT_VERSION
        ),
        "review_artifact_digest": artifact,
        "saved_state_digest": saved_state,
        "human_review_status": "awaiting_review",
        "production_execution": True,
        "diagnostic_only": False,
        "read_only": True,
        "application_authorization": False,
        "mutation_authorization": False,
        "ats_authorization": False,
    }
    checkpoint_id = (
        "production-review-checkpoint:"
        + canonical_digest(
            envelope_base, field="production_human_review_checkpoint"
        )
    )
    envelope = {**envelope_base, "checkpoint_id": checkpoint_id}
    return {
        "checkpoint_id": checkpoint_id,
        "graph_invocation_id": graph["graph_invocation_id"],
        "checkpoint_sequence": sequence,
        "checkpoint_schema_version": (
            PRODUCTION_HUMAN_REVIEW_CHECKPOINT_VERSION
        ),
        "graph_state_schema_version": graph["graph_state_schema_version"],
        "checkpoint_status": PRODUCTION_CHECKPOINT_STATUS,
        **{
            field: deepcopy(graph[field])
            for field in store._IDENTITY_COLUMNS
        },
        "checkpoint_envelope_json": envelope,
        "checkpoint_envelope_digest": canonical_digest(
            envelope, field="production_human_review_checkpoint_envelope"
        ),
        "completed_node_keys_json": [PRODUCTION_HUMAN_REVIEW_NODE],
        "next_node_key": PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
        "committed_at": _required(committed_at, "committed_at"),
        "purge_after": None,
    }


def prepare_human_review_interrupt_row(
    checkpoint_row: Mapping[str, Any],
    *,
    created_at: str,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """Build the bounded production review request for an exact checkpoint."""
    store._require_exact_fields(
        checkpoint_row, store._CHECKPOINT_COLUMNS, "checkpoint_row"
    )
    envelope = checkpoint_row.get("checkpoint_envelope_json")
    if (
        not isinstance(envelope, Mapping)
        or envelope.get("human_review_contract_version")
        != PRODUCTION_HUMAN_REVIEW_CONTRACT_VERSION
        or checkpoint_row.get("checkpoint_envelope_digest")
        != canonical_digest(
            envelope, field="production_human_review_checkpoint_envelope"
        )
    ):
        raise ValueError("production_human_review_checkpoint_invalid")
    payload_base = {
        "interrupt_request_schema_version": (
            PRODUCTION_HUMAN_REVIEW_INTERRUPT_VERSION
        ),
        "human_review_contract_version": (
            PRODUCTION_HUMAN_REVIEW_CONTRACT_VERSION
        ),
        "checkpoint_schema_version": checkpoint_row[
            "checkpoint_schema_version"
        ],
        "graph_state_schema_version": checkpoint_row[
            "graph_state_schema_version"
        ],
        "graph_invocation_id": checkpoint_row["graph_invocation_id"],
        "checkpoint_id": checkpoint_row["checkpoint_id"],
        **{
            field: deepcopy(checkpoint_row[field])
            for field in store._IDENTITY_COLUMNS
        },
        "node_key": PRODUCTION_HUMAN_REVIEW_NODE,
        "safe_next_node_key": PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
        "operator_review_artifact_type": envelope["review_artifact_type"],
        "operator_review_artifact_version": envelope[
            "review_artifact_version"
        ],
        "operator_review_artifact_digest": envelope[
            "review_artifact_digest"
        ],
        "allowed_decision_values": list(
            PRODUCTION_HUMAN_REVIEW_DECISIONS
        ),
        "read_only": True,
        "diagnostic_only": False,
        "application_authorization": False,
        "resume_authorization": False,
    }
    request_id = (
        "production-review-interrupt:"
        + canonical_digest(
            payload_base, field="production_human_review_interrupt"
        )
    )
    payload = {**payload_base, "interrupt_request_id": request_id}
    _bounded_mapping(
        payload,
        field="production_human_review_interrupt",
        maximum=store.MAX_INTERRUPT_REQUEST_BYTES,
    )
    return {
        "interrupt_request_id": request_id,
        "graph_invocation_id": checkpoint_row["graph_invocation_id"],
        "checkpoint_id": checkpoint_row["checkpoint_id"],
        "interrupt_request_schema_version": (
            PRODUCTION_HUMAN_REVIEW_INTERRUPT_VERSION
        ),
        "checkpoint_schema_version": checkpoint_row[
            "checkpoint_schema_version"
        ],
        "graph_state_schema_version": checkpoint_row[
            "graph_state_schema_version"
        ],
        **{
            field: deepcopy(checkpoint_row[field])
            for field in store._IDENTITY_COLUMNS
        },
        "node_key": PRODUCTION_HUMAN_REVIEW_NODE,
        "safe_next_node_key": PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
        "operator_review_artifact_type": envelope["review_artifact_type"],
        "operator_review_artifact_version": envelope[
            "review_artifact_version"
        ],
        "operator_review_artifact_digest": envelope[
            "review_artifact_digest"
        ],
        "allowed_decision_values_json": list(
            PRODUCTION_HUMAN_REVIEW_DECISIONS
        ),
        "interrupt_request_json": payload,
        "interrupt_status": "awaiting_decision",
        "lock_version": 0,
        "read_only": True,
        "diagnostic_only": False,
        "application_authorization": False,
        "resume_authorization": False,
        "created_at": _required(created_at, "created_at"),
        "expires_at": _clean(expires_at) or None,
        "resolved_at": None,
    }


def prepare_human_review_decision_row(
    interrupt_row: Mapping[str, Any],
    *,
    decision_value: str,
    actor_id: str,
    client_idempotency_key: str,
    expected_interrupt_version: int,
    expected_run_lock_version: int,
    created_at: str,
    reason: str = "",
) -> dict[str, Any]:
    store._require_exact_fields(
        interrupt_row, store._INTERRUPT_COLUMNS, "interrupt_row"
    )
    if (
        interrupt_row.get("interrupt_request_schema_version")
        != PRODUCTION_HUMAN_REVIEW_INTERRUPT_VERSION
        or interrupt_row.get("diagnostic_only") is not False
    ):
        raise ValueError("production_human_review_interrupt_invalid")
    decision = _clean(decision_value)
    if decision not in PRODUCTION_HUMAN_REVIEW_DECISIONS:
        raise ValueError("decision_value_unsupported")
    actor = _required(actor_id, "actor_id")
    idempotency = _required(
        client_idempotency_key, "client_idempotency_key"
    )
    note = _clean(reason)
    if len(note.encode("utf-8")) > 4096:
        raise ValueError("decision_reason_too_large")
    seed = {
        "interrupt_request_id": interrupt_row["interrupt_request_id"],
        "client_idempotency_key": idempotency,
        "decision_value": decision,
        "actor_id": actor,
        "graph_invocation_id": interrupt_row["graph_invocation_id"],
        "checkpoint_id": interrupt_row["checkpoint_id"],
        "operator_review_artifact_digest": interrupt_row[
            "operator_review_artifact_digest"
        ],
    }
    return {
        "decision_id": (
            "production-human-decision:"
            + canonical_digest(seed, field="production_human_decision")
        ),
        "graph_invocation_id": interrupt_row["graph_invocation_id"],
        "checkpoint_id": interrupt_row["checkpoint_id"],
        "interrupt_request_id": interrupt_row["interrupt_request_id"],
        **{
            field: deepcopy(interrupt_row[field])
            for field in store._IDENTITY_COLUMNS
        },
        "operator_review_artifact_digest": interrupt_row[
            "operator_review_artifact_digest"
        ],
        "decision_value": decision,
        "actor_id": actor,
        "client_idempotency_key": idempotency,
        "expected_interrupt_status": "awaiting_decision",
        "expected_interrupt_version": _nonnegative(
            expected_interrupt_version, "expected_interrupt_version"
        ),
        "expected_run_lock_version": _nonnegative(
            expected_run_lock_version, "expected_run_lock_version"
        ),
        "decision_record_status": "recorded",
        "reason": note,
        "rejection_code": "",
        "application_authorization": False,
        "created_at": _required(created_at, "created_at"),
    }


def prepare_human_review_authorization_row(
    decision_row: Mapping[str, Any],
    *,
    authorization_token_hash: str,
    created_at: str,
    expires_at: str,
) -> dict[str, Any]:
    store._require_exact_fields(
        decision_row, store._DECISION_COLUMNS, "decision_row"
    )
    if decision_row.get("decision_value") != "continue_read_only":
        raise ValueError("decision_not_resume_authorizable")
    token_hash = _digest(
        authorization_token_hash, "authorization_token_hash"
    )
    seed = {
        "decision_id": decision_row["decision_id"],
        "interrupt_request_id": decision_row["interrupt_request_id"],
        "authorization_token_hash": token_hash,
        "safe_next_node_key": PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
    }
    return {
        "authorization_id": (
            "production-resume-authorization:"
            + canonical_digest(
                seed, field="production_resume_authorization"
            )
        ),
        "decision_id": decision_row["decision_id"],
        "graph_invocation_id": decision_row["graph_invocation_id"],
        "checkpoint_id": decision_row["checkpoint_id"],
        "interrupt_request_id": decision_row["interrupt_request_id"],
        **{
            field: deepcopy(decision_row[field])
            for field in store._IDENTITY_COLUMNS
        },
        "operator_review_artifact_digest": decision_row[
            "operator_review_artifact_digest"
        ],
        "decision_value": "continue_read_only",
        "safe_next_node_key": PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
        "authorization_token_hash": token_hash,
        "authorization_status": "authorized",
        "lock_version": 0,
        "read_only": True,
        "application_authorization": False,
        "resume_text_mutation_authorization": False,
        "queue_mutation_authorization": False,
        "operator_state_mutation_authorization": False,
        "created_at": _required(created_at, "created_at"),
        "expires_at": _required(expires_at, "expires_at"),
        "consumed_at": None,
    }


def prepare_human_review_consumption_row(
    authorization_row: Mapping[str, Any],
    *,
    consumer_instance_id: str,
    claimed_at: str,
    expected_authorization_version: int = 0,
) -> dict[str, Any]:
    store._require_exact_fields(
        authorization_row, store._AUTHORIZATION_COLUMNS, "authorization_row"
    )
    if authorization_row.get("authorization_status") != "authorized":
        raise ValueError("authorization_not_consumable")
    consumer = _required(consumer_instance_id, "consumer_instance_id")
    seed = {
        "authorization_id": authorization_row["authorization_id"],
        "consumer_instance_id": consumer,
    }
    resume_invocation_id = (
        "production-resume-invocation:"
        + canonical_digest(seed, field="production_resume_invocation")
    )
    return {
        "consumption_id": (
            "production-resume-consumption:"
            + canonical_digest(
                {"authorization_id": authorization_row["authorization_id"]},
                field="production_resume_consumption",
            )
        ),
        "authorization_id": authorization_row["authorization_id"],
        "decision_id": authorization_row["decision_id"],
        "graph_invocation_id": authorization_row["graph_invocation_id"],
        "checkpoint_id": authorization_row["checkpoint_id"],
        "interrupt_request_id": authorization_row["interrupt_request_id"],
        **{
            field: deepcopy(authorization_row[field])
            for field in store._IDENTITY_COLUMNS
        },
        "resume_invocation_id": resume_invocation_id,
        "consumer_instance_id": consumer,
        "claimed_at": _required(claimed_at, "claimed_at"),
        "claim_status": "claimed",
        "expected_authorization_version": _nonnegative(
            expected_authorization_version,
            "expected_authorization_version",
        ),
        "authorization_token_hash_proof": authorization_row[
            "authorization_token_hash"
        ],
        "application_authorization": False,
    }


def prepare_human_review_terminal_checkpoint_row(
    graph_run_row: Mapping[str, Any],
    *,
    parent_checkpoint_row: Mapping[str, Any],
    saved_state_digest: str,
    committed_at: str,
) -> dict[str, Any]:
    graph = _validate_graph_run(graph_run_row)
    store._require_exact_fields(
        parent_checkpoint_row, store._CHECKPOINT_COLUMNS, "checkpoint_row"
    )
    parent_envelope = parent_checkpoint_row["checkpoint_envelope_json"]
    if not isinstance(parent_envelope, Mapping):
        raise ValueError("production_human_review_parent_invalid")
    envelope_base = {
        **{
            key: deepcopy(value)
            for key, value in parent_envelope.items()
            if key != "checkpoint_id"
        },
        "checkpoint_sequence": 2,
        "completed_node_keys": [
            PRODUCTION_HUMAN_REVIEW_NODE,
            PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
        ],
        "next_node_key": PRODUCTION_END_NODE,
        "saved_state_digest": _digest(
            saved_state_digest, "saved_state_digest"
        ),
        "human_review_status": "human_reviewed",
    }
    checkpoint_id = (
        "production-review-checkpoint:"
        + canonical_digest(
            envelope_base, field="production_human_review_checkpoint"
        )
    )
    envelope = {**envelope_base, "checkpoint_id": checkpoint_id}
    return {
        "checkpoint_id": checkpoint_id,
        "graph_invocation_id": graph["graph_invocation_id"],
        "checkpoint_sequence": 2,
        "checkpoint_schema_version": (
            PRODUCTION_HUMAN_REVIEW_CHECKPOINT_VERSION
        ),
        "graph_state_schema_version": graph["graph_state_schema_version"],
        "checkpoint_status": PRODUCTION_CHECKPOINT_STATUS,
        **{
            field: deepcopy(graph[field])
            for field in store._IDENTITY_COLUMNS
        },
        "checkpoint_envelope_json": envelope,
        "checkpoint_envelope_digest": canonical_digest(
            envelope, field="production_human_review_checkpoint_envelope"
        ),
        "completed_node_keys_json": [
            PRODUCTION_HUMAN_REVIEW_NODE,
            PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
        ],
        "next_node_key": PRODUCTION_END_NODE,
        "committed_at": _required(committed_at, "committed_at"),
        "purge_after": None,
    }


def _graph_run_insert_sql(params: Mapping[str, Any]) -> dict[str, Any]:
    sql = """
WITH inserted AS (
 INSERT INTO orchestration_graph_runs (
   graph_invocation_id, graph_engine, graph_state_schema_version,
   owner_user_id, pipeline_run_id, context_id, job_id, job_index,
   selected_resume_id, run_status, current_checkpoint_id, lock_version,
   created_at, updated_at, terminal_at, purge_after
 ) VALUES (
   %(graph_invocation_id)s, %(graph_engine)s,
   %(graph_state_schema_version)s, %(owner_user_id)s,
   %(pipeline_run_id)s, %(context_id)s, %(job_id)s, %(job_index)s,
   %(selected_resume_id)s, %(run_status)s, %(current_checkpoint_id)s,
   %(lock_version)s, %(created_at)s, %(updated_at)s, %(terminal_at)s,
   %(purge_after)s
 )
 ON CONFLICT (graph_invocation_id) DO NOTHING
 RETURNING *, FALSE AS idempotent_duplicate
), accepted AS (
 SELECT * FROM inserted
 UNION ALL
 SELECT existing.*, TRUE AS idempotent_duplicate
 FROM orchestration_graph_runs AS existing
 WHERE existing.graph_invocation_id = %(graph_invocation_id)s
   AND existing.graph_engine = %(graph_engine)s
   AND existing.graph_state_schema_version = %(graph_state_schema_version)s
   AND existing.owner_user_id = %(owner_user_id)s
   AND existing.pipeline_run_id = %(pipeline_run_id)s
   AND existing.context_id = %(context_id)s
   AND existing.job_id = %(job_id)s
   AND existing.job_index = %(job_index)s
   AND existing.selected_resume_id = %(selected_resume_id)s
   AND NOT EXISTS (SELECT 1 FROM inserted)
)
SELECT * FROM accepted LIMIT 1
"""
    return store._command(
        operation="prepare_production_graph_run_insert",
        tables=("orchestration_graph_runs",),
        sql=sql,
        params=params,
        read_only=False,
    )


def prepare_graph_run_insert(graph_run_row: Mapping[str, Any]) -> dict[str, Any]:
    return _graph_run_insert_sql(_validate_graph_run(graph_run_row))


def prepare_checkpoint_attempt_start(
    graph_run_row: Mapping[str, Any],
    checkpoint_row: Mapping[str, Any],
    attempt_row: Mapping[str, Any],
) -> dict[str, Any]:
    graph = _validate_graph_run(graph_run_row)
    checkpoint = _validate_checkpoint(checkpoint_row)
    store._require_exact_fields(
        attempt_row, store._NODE_ATTEMPT_COLUMNS, "production_node_attempt"
    )
    attempt = deepcopy(dict(attempt_row))
    node = _node(attempt.get("node_key"))
    if (
        graph["run_status"] != "running"
        or checkpoint["graph_invocation_id"] != graph["graph_invocation_id"]
        or checkpoint["checkpoint_sequence"] != 0
        or checkpoint["next_node_key"] != node
        or checkpoint["completed_node_keys_json"] != []
        or attempt["graph_invocation_id"] != graph["graph_invocation_id"]
        or attempt["input_checkpoint_id"] != checkpoint["checkpoint_id"]
        or attempt["attempt_status"] != "pending"
        or attempt["input_digest"]
        != checkpoint["checkpoint_envelope_json"]["input_digest"]
    ):
        raise ValueError("production_attempt_start_contract_invalid")
    checkpoint_params = deepcopy(checkpoint)
    checkpoint_params["checkpoint_envelope_json"] = _canonical(
        checkpoint["checkpoint_envelope_json"], "production_checkpoint"
    )
    checkpoint_params["completed_node_keys_json"] = _canonical(
        checkpoint["completed_node_keys_json"], "production_completed_nodes"
    )
    params = {
        **{
            f"run_{key}": value
            for key, value in graph.items()
        },
        **{
            f"checkpoint_{key}": value
            for key, value in checkpoint_params.items()
        },
        **{
            f"attempt_{key}": value
            for key, value in attempt.items()
        },
    }
    checkpoint_columns = ", ".join(store._CHECKPOINT_COLUMNS)
    checkpoint_values = ", ".join(
        f"%(checkpoint_{column})s" for column in store._CHECKPOINT_COLUMNS
    )
    attempt_columns = ", ".join(store._NODE_ATTEMPT_COLUMNS)
    attempt_values = ", ".join(
        f"%(attempt_{column})s" for column in store._NODE_ATTEMPT_COLUMNS
    )
    sql = f"""
WITH locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND owner_user_id = %(run_owner_user_id)s
   AND run_status = 'running'
   AND current_checkpoint_id IS NULL
   AND lock_version = 0
 FOR UPDATE
), inserted_checkpoint AS (
 INSERT INTO orchestration_checkpoints ({checkpoint_columns})
 SELECT {checkpoint_values} FROM locked_run
 ON CONFLICT DO NOTHING RETURNING *
), accepted_checkpoint AS (
 SELECT * FROM inserted_checkpoint
 UNION ALL
 SELECT existing.*
 FROM orchestration_checkpoints AS existing
 WHERE existing.checkpoint_id = %(checkpoint_checkpoint_id)s
   AND existing.graph_invocation_id = %(checkpoint_graph_invocation_id)s
   AND existing.owner_user_id = %(checkpoint_owner_user_id)s
   AND existing.checkpoint_envelope_digest
       = %(checkpoint_checkpoint_envelope_digest)s
   AND NOT EXISTS (SELECT 1 FROM inserted_checkpoint)
), advanced_run AS (
 UPDATE orchestration_graph_runs
 SET run_status = 'resumed',
     current_checkpoint_id = %(checkpoint_checkpoint_id)s,
     lock_version = 1,
     updated_at = %(checkpoint_committed_at)s
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND owner_user_id = %(run_owner_user_id)s
   AND run_status = 'running'
   AND lock_version = 0
   AND EXISTS (SELECT 1 FROM accepted_checkpoint)
 RETURNING *
), inserted_attempt AS (
 INSERT INTO orchestration_node_attempts ({attempt_columns})
 SELECT {attempt_values} FROM advanced_run
 ON CONFLICT (
   graph_invocation_id, input_checkpoint_id, node_key, attempt_number
 ) DO NOTHING
 RETURNING *, FALSE AS idempotent_duplicate
), accepted_attempt AS (
 SELECT * FROM inserted_attempt
 UNION ALL
 SELECT existing.*, TRUE AS idempotent_duplicate
 FROM orchestration_node_attempts AS existing
 JOIN orchestration_graph_runs AS current_run
   ON current_run.graph_invocation_id = existing.graph_invocation_id
 WHERE existing.node_attempt_id = %(attempt_node_attempt_id)s
   AND existing.owner_user_id = %(attempt_owner_user_id)s
   AND existing.input_checkpoint_id = %(attempt_input_checkpoint_id)s
   AND existing.node_key = %(attempt_node_key)s
   AND existing.input_digest = %(attempt_input_digest)s
   AND existing.attempt_status = 'pending'
   AND current_run.run_status = 'resumed'
   AND current_run.current_checkpoint_id = %(attempt_input_checkpoint_id)s
   AND NOT EXISTS (SELECT 1 FROM inserted_attempt)
)
SELECT * FROM accepted_attempt LIMIT 1
"""
    return store._command(
        operation="prepare_production_checkpoint_attempt_start",
        tables=(
            "orchestration_graph_runs",
            "orchestration_checkpoints",
            "orchestration_node_attempts",
        ),
        sql=sql,
        params=params,
        read_only=False,
    )


def prepare_checkpoint_commit(
    checkpoint_row: Mapping[str, Any],
    *,
    parent_checkpoint_id: str,
    expected_run_lock_version: int,
) -> dict[str, Any]:
    checkpoint = _validate_checkpoint(checkpoint_row)
    parent = _required(parent_checkpoint_id, "parent_checkpoint_id")
    if (
        checkpoint["checkpoint_sequence"] < 1
        or checkpoint["next_node_key"] != PRODUCTION_END_NODE
        or checkpoint["checkpoint_id"] == parent
    ):
        raise ValueError("production_final_checkpoint_invalid")
    params = {
        **{
            f"checkpoint_{key}": value
            for key, value in checkpoint.items()
        },
        "parent_checkpoint_id": parent,
        "expected_run_lock_version": _nonnegative(
            expected_run_lock_version, "expected_run_lock_version"
        ),
    }
    params["checkpoint_checkpoint_envelope_json"] = _canonical(
        checkpoint["checkpoint_envelope_json"], "production_checkpoint"
    )
    params["checkpoint_completed_node_keys_json"] = _canonical(
        checkpoint["completed_node_keys_json"], "production_completed_nodes"
    )
    columns = ", ".join(store._CHECKPOINT_COLUMNS)
    values = ", ".join(
        f"%(checkpoint_{column})s" for column in store._CHECKPOINT_COLUMNS
    )
    sql = f"""
WITH locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(checkpoint_graph_invocation_id)s
   AND owner_user_id = %(checkpoint_owner_user_id)s
   AND current_checkpoint_id = %(parent_checkpoint_id)s
   AND run_status = 'resumed'
   AND lock_version = %(expected_run_lock_version)s
 FOR UPDATE
), inserted_checkpoint AS (
 INSERT INTO orchestration_checkpoints ({columns})
 SELECT {values} FROM locked_run
 ON CONFLICT DO NOTHING RETURNING *
), accepted_checkpoint AS (
 SELECT inserted_checkpoint.*, FALSE AS idempotent_duplicate
 FROM inserted_checkpoint
 UNION ALL
 SELECT existing.*, TRUE AS idempotent_duplicate
 FROM orchestration_checkpoints AS existing
 WHERE existing.checkpoint_id = %(checkpoint_checkpoint_id)s
   AND existing.graph_invocation_id = %(checkpoint_graph_invocation_id)s
   AND existing.owner_user_id = %(checkpoint_owner_user_id)s
   AND existing.checkpoint_envelope_digest
       = %(checkpoint_checkpoint_envelope_digest)s
   AND existing.checkpoint_envelope_json
       = %(checkpoint_checkpoint_envelope_json)s::jsonb
   AND NOT EXISTS (SELECT 1 FROM inserted_checkpoint)
)
SELECT * FROM accepted_checkpoint
"""
    return store._command(
        operation="prepare_production_checkpoint_commit",
        tables=("orchestration_graph_runs", "orchestration_checkpoints"),
        sql=sql,
        params=params,
        read_only=False,
    )


def prepare_terminalization(
    graph_run_row: Mapping[str, Any],
    terminal_result_row: Mapping[str, Any],
    lifecycle_event_row: Mapping[str, Any],
    *,
    successful_attempt_row: Mapping[str, Any] | None,
    final_binding_row: Mapping[str, Any] | None,
    expected_run_lock_version: int,
) -> dict[str, Any]:
    graph = _validate_graph_run(graph_run_row)
    store._require_exact_fields(
        terminal_result_row,
        store._TERMINAL_RESULT_COLUMNS,
        "production_terminal_result",
    )
    terminal = deepcopy(dict(terminal_result_row))
    store._require_exact_fields(
        lifecycle_event_row,
        store._LIFECYCLE_EVENT_COLUMNS,
        "production_terminal_event",
    )
    event = deepcopy(dict(lifecycle_event_row))
    status = terminal["terminal_status"]
    if (
        terminal["graph_invocation_id"] != graph["graph_invocation_id"]
        or terminal["owner_user_id"] != graph["owner_user_id"]
        or terminal["terminal_checkpoint_id"]
        != graph["current_checkpoint_id"]
        or terminal["final_node_order_json"]
        != [terminal["result_metadata_json"]["production_node_key"]]
        or event["event_type"] != "terminal_result_recorded"
        or event["terminal_result_id"] != terminal["terminal_result_id"]
    ):
        raise ValueError("production_terminalization_identity_invalid")
    strict = successful_attempt_row is not None or final_binding_row is not None
    if strict and (
        successful_attempt_row is None or final_binding_row is None
    ):
        raise ValueError("production_terminalization_evidence_incomplete")
    params = {
        **{f"run_{key}": value for key, value in graph.items()},
        **{f"terminal_{key}": value for key, value in terminal.items()},
        **{f"event_{key}": value for key, value in event.items()},
        "expected_run_lock_version": _nonnegative(
            expected_run_lock_version, "expected_run_lock_version"
        ),
    }
    params["terminal_result_metadata_json"] = _canonical(
        terminal["result_metadata_json"], "production_terminal_result"
    )
    params["terminal_final_node_order_json"] = _canonical(
        terminal["final_node_order_json"], "production_terminal_nodes"
    )
    params["event_event_payload_json"] = _canonical(
        event["event_payload_json"], "production_terminal_event"
    )
    strict_sql = ""
    if strict:
        attempt = deepcopy(dict(successful_attempt_row or {}))
        binding = deepcopy(dict(final_binding_row or {}))
        node = terminal["result_metadata_json"]["production_node_key"]
        if (
            attempt.get("attempt_status") != "succeeded"
            or attempt.get("node_key") != node
            or attempt.get("output_checkpoint_id")
            != terminal["terminal_checkpoint_id"]
            or binding.get("checkpoint_id")
            != terminal["terminal_checkpoint_id"]
            or binding.get("aggregate_type")
            != store.LANGGRAPH_CHECKPOINT_BINDING_AGGREGATE_TYPE
        ):
            raise ValueError("production_terminalization_evidence_invalid")
        params.update(
            {
                "successful_attempt_id": attempt["node_attempt_id"],
                "final_binding_event_id": binding["event_id"],
                "production_node_key": node,
            }
        )
        strict_sql = """
   AND EXISTS (
       SELECT 1 FROM orchestration_node_attempts
       WHERE node_attempt_id = %(successful_attempt_id)s
         AND graph_invocation_id = %(run_graph_invocation_id)s
         AND owner_user_id = %(run_owner_user_id)s
         AND output_checkpoint_id = %(terminal_terminal_checkpoint_id)s
         AND node_key = %(production_node_key)s
         AND attempt_status = 'succeeded'
   )
   AND EXISTS (
       SELECT 1 FROM orchestration_lifecycle_events
       WHERE event_id = %(final_binding_event_id)s
         AND graph_invocation_id = %(run_graph_invocation_id)s
         AND owner_user_id = %(run_owner_user_id)s
         AND checkpoint_id = %(terminal_terminal_checkpoint_id)s
         AND aggregate_type = 'langgraph_checkpoint_binding'
         AND event_sequence = 0
   )"""
    sql = f"""
WITH locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND owner_user_id = %(run_owner_user_id)s
   AND current_checkpoint_id = %(terminal_terminal_checkpoint_id)s
   AND run_status = 'resumed'
   AND lock_version = %(expected_run_lock_version)s
   {strict_sql}
 FOR UPDATE
), inserted_terminal AS (
 INSERT INTO orchestration_terminal_results
 SELECT %(terminal_terminal_result_id)s,
        %(terminal_graph_invocation_id)s,
        %(terminal_terminal_checkpoint_id)s,
        %(terminal_owner_user_id)s, %(terminal_pipeline_run_id)s,
        %(terminal_context_id)s, %(terminal_job_id)s,
        %(terminal_job_index)s, %(terminal_selected_resume_id)s,
        %(terminal_graph_state_schema_version)s,
        %(terminal_checkpoint_schema_version)s,
        %(terminal_terminal_status)s, %(terminal_result_digest)s,
        %(terminal_result_metadata_json)s::jsonb,
        %(terminal_final_node_order_json)s::jsonb,
        %(terminal_failure_code)s,
        %(terminal_application_authorization)s,
        %(terminal_completed_at)s
 FROM locked_run
 ON CONFLICT (graph_invocation_id) DO NOTHING RETURNING *
), accepted_terminal AS (
 SELECT inserted_terminal.*, FALSE AS idempotent_duplicate
 FROM inserted_terminal
 UNION ALL
 SELECT existing.*, TRUE AS idempotent_duplicate
 FROM orchestration_terminal_results AS existing
 WHERE existing.graph_invocation_id = %(terminal_graph_invocation_id)s
   AND existing.terminal_result_id = %(terminal_terminal_result_id)s
   AND existing.terminal_checkpoint_id
       = %(terminal_terminal_checkpoint_id)s
   AND existing.result_digest = %(terminal_result_digest)s
   AND existing.result_metadata_json
       = %(terminal_result_metadata_json)s::jsonb
   AND NOT EXISTS (SELECT 1 FROM inserted_terminal)
), terminalized_run AS (
 UPDATE orchestration_graph_runs
 SET run_status = %(terminal_terminal_status)s,
     terminal_at = %(terminal_completed_at)s,
     updated_at = %(terminal_completed_at)s,
     lock_version = lock_version + 1
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND run_status = 'resumed'
   AND lock_version = %(expected_run_lock_version)s
   AND EXISTS (SELECT 1 FROM accepted_terminal)
 RETURNING *
), inserted_event AS (
 INSERT INTO orchestration_lifecycle_events
 SELECT %(event_event_id)s, %(event_graph_invocation_id)s,
        %(event_checkpoint_id)s, %(event_interrupt_request_id)s,
        %(event_decision_id)s, %(event_authorization_id)s,
        %(event_consumption_id)s, %(event_node_attempt_id)s,
        %(event_terminal_result_id)s, %(event_owner_user_id)s,
        %(event_event_type)s, %(event_aggregate_type)s,
        %(event_aggregate_id)s, %(event_event_sequence)s,
        %(event_event_payload_json)s::jsonb, %(event_event_timestamp)s,
        %(event_projection_status)s, %(event_projected_at)s,
        %(event_projection_retry_count)s
 FROM terminalized_run
 ON CONFLICT (event_id) DO NOTHING RETURNING *
)
SELECT * FROM accepted_terminal
"""
    return store._command(
        operation="prepare_production_terminalization",
        tables=(
            "orchestration_graph_runs",
            "orchestration_terminal_results",
            "orchestration_lifecycle_events",
        ),
        sql=sql,
        params=params,
        read_only=False,
    )


__all__ = [
    "MAX_PRODUCTION_RESULT_BYTES",
    "MAX_PRODUCTION_STATE_BYTES",
    "PRODUCTION_CHECKPOINT_SCHEMA_VERSION",
    "PRODUCTION_CHECKPOINT_STATUS",
    "PRODUCTION_DURABLE_CONTRACT_TYPE",
    "PRODUCTION_DURABLE_CONTRACT_VERSION",
    "PRODUCTION_END_NODE",
    "PRODUCTION_GRAPH_ENGINE_PREFIX",
    "PRODUCTION_HUMAN_REVIEW_CHECKPOINT_VERSION",
    "PRODUCTION_HUMAN_REVIEW_CONTRACT_VERSION",
    "PRODUCTION_HUMAN_REVIEW_DECISIONS",
    "PRODUCTION_HUMAN_REVIEW_INTERRUPT_VERSION",
    "PRODUCTION_HUMAN_REVIEW_NODE",
    "PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE",
    "PRODUCTION_TAILORING_REVIEW_ARTIFACT_TYPE",
    "PRODUCTION_TAILORING_REVIEW_ARTIFACT_VERSION",
    "canonical_digest",
    "prepare_checkpoint_attempt_start",
    "prepare_checkpoint_binding_row",
    "prepare_checkpoint_commit",
    "prepare_checkpoint_row",
    "prepare_graph_run_insert",
    "prepare_graph_run_row",
    "prepare_human_review_authorization_row",
    "prepare_human_review_checkpoint_row",
    "prepare_human_review_consumption_row",
    "prepare_human_review_decision_row",
    "prepare_human_review_interrupt_row",
    "prepare_human_review_terminal_checkpoint_row",
    "prepare_lifecycle_event_row",
    "prepare_node_attempt_row",
    "prepare_terminal_result_row",
    "prepare_terminalization",
    "production_identity_from_graph_run",
]

"""Default-off durable production review coordination.

The coordinator accepts an already-produced bounded tailoring result, retains
only its digest, and owns no connection, saver, provider, cache, or application
action.  Injected repository and saver owners remain authoritative.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Any, Mapping, TypedDict

from src.storage.durable_orchestration import production


PRODUCTION_HUMAN_CHECKPOINT_FLAG = (
    "APPLYLENS_PRODUCTION_HUMAN_CHECKPOINT_ENABLED"
)
PRODUCTION_HUMAN_CHECKPOINT_COORDINATOR_VERSION = (
    "production-human-checkpoint-coordinator-v1"
)
PRODUCTION_HUMAN_REVIEW_GRAPH_VERSION = (
    "production-human-review-graph-v1"
)
PRODUCTION_HUMAN_REVIEW_STATE_VERSION = (
    "production-human-review-state-v1"
)
_ACCEPTED = frozenset({"applied", "idempotent_existing"})


class ProductionHumanReviewState(TypedDict, total=False):
    graph_version: str
    state_version: str
    graph_invocation_id: str
    owner_user_id: str
    pipeline_run_id: str
    context_id: str
    job_id: str
    job_index: int
    selected_resume_id: str
    review_artifact_type: str
    review_artifact_version: str
    review_artifact_digest: str
    current_node: str
    completed_nodes: list[str]
    pending_node: str
    human_review_status: str
    read_only: bool
    mutation_authority: bool
    application_authority: bool
    ats_authority: bool


@dataclass(frozen=True, slots=True)
class ProductionHumanCheckpointResult:
    status: str
    classification: str
    graph_invocation_id: str = ""
    repository_checkpoint_id: str = ""
    interrupt_request_id: str = ""
    decision_id: str = ""
    authorization_id: str = ""
    consumption_id: str = ""
    terminal_result_id: str = ""
    review_artifact_digest: str = ""
    human_review_status: str = ""


def hash_resume_authorization_token(token: str) -> str:
    value = str(token or "")
    if not value:
        raise ValueError("authorization_token_required")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _classification(result: Any) -> str:
    return str(getattr(result, "classification", "") or "")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw(item) for item in value]
    return deepcopy(value)


def _record(result: Any) -> dict[str, Any]:
    value = getattr(result, "record", None)
    return _thaw(value) if isinstance(value, Mapping) else {}


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field}_required")
    return text


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_result(
    status: str,
    classification: str,
    **values: Any,
) -> ProductionHumanCheckpointResult:
    allowed = {
        "applied",
        "idempotent_existing",
        "not_found",
        "stale_state",
        "identity_mismatch",
        "already_terminal",
        "duplicate_conflict",
        "unavailable",
        "transaction_failed",
        "expired",
        "invalid_saved_graph_state",
        "reconciliation_required",
    }
    safe = (
        classification
        if classification in allowed
        else "reconciliation_required"
    )
    return ProductionHumanCheckpointResult(
        status=status,
        classification=safe,
        **values,
    )


def build_production_human_review_graph(*, checkpointer: Any) -> Any:
    from langgraph.graph import END, START, StateGraph

    def operator_review(
        state: ProductionHumanReviewState,
    ) -> ProductionHumanReviewState:
        next_state = deepcopy(state)
        next_state.update(
            {
                "current_node": production.PRODUCTION_HUMAN_REVIEW_NODE,
                "completed_nodes": [
                    production.PRODUCTION_HUMAN_REVIEW_NODE
                ],
                "pending_node": (
                    production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE
                ),
                "human_review_status": "awaiting_review",
            }
        )
        return next_state

    def finalize(
        state: ProductionHumanReviewState,
    ) -> ProductionHumanReviewState:
        next_state = deepcopy(state)
        next_state.update(
            {
                "current_node": (
                    production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE
                ),
                "completed_nodes": [
                    production.PRODUCTION_HUMAN_REVIEW_NODE,
                    production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
                ],
                "pending_node": "",
                "human_review_status": "human_reviewed",
            }
        )
        return next_state

    graph = StateGraph(ProductionHumanReviewState)
    graph.add_node(production.PRODUCTION_HUMAN_REVIEW_NODE, operator_review)
    graph.add_node(
        production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE, finalize
    )
    graph.add_edge(START, production.PRODUCTION_HUMAN_REVIEW_NODE)
    graph.add_edge(
        production.PRODUCTION_HUMAN_REVIEW_NODE,
        production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,
    )
    graph.add_edge(
        production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE, END
    )
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE
        ],
    )


class ProductionHumanCheckpointCoordinator:
    """Coordinate one bounded production review pause and continuation."""

    def __init__(
        self,
        *,
        repository: Any,
        saver: Any,
        consumer_instance_id: str,
        enabled: bool = False,
    ) -> None:
        if enabled is not True:
            raise ValueError("production_human_checkpoint_not_enabled")
        if repository is None:
            raise ValueError("durable_repository_required")
        if saver is None:
            raise ValueError("langgraph_saver_required")
        self._repository = repository
        self._saver = saver
        self._consumer_instance_id = _required(
            consumer_instance_id, "consumer_instance_id"
        )
        self._graph = build_production_human_review_graph(
            checkpointer=saver
        )

    @staticmethod
    def _snapshot_config(snapshot: Any) -> dict[str, Any]:
        config = getattr(snapshot, "config", None)
        configurable = (
            dict(config.get("configurable") or {})
            if isinstance(config, Mapping)
            else {}
        )
        return {
            "thread_id": _required(
                configurable.get("thread_id"), "langgraph_thread_id"
            ),
            "checkpoint_ns": str(
                configurable.get("checkpoint_ns") or ""
            ),
            "checkpoint_id": _required(
                configurable.get("checkpoint_id"),
                "langgraph_checkpoint_id",
            ),
        }

    @staticmethod
    def _validate_snapshot(
        snapshot: Any, *, expect_paused: bool
    ) -> Mapping[str, Any]:
        values = getattr(snapshot, "values", None)
        if not isinstance(values, Mapping):
            raise ValueError("saved_graph_state_missing")
        expected_next = (
            (production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE,)
            if expect_paused
            else ()
        )
        if tuple(getattr(snapshot, "next", ())) != expected_next:
            raise ValueError("saved_graph_pending_node_invalid")
        expected_status = (
            "awaiting_review" if expect_paused else "human_reviewed"
        )
        if (
            values.get("human_review_status") != expected_status
            or values.get("read_only") is not True
            or values.get("mutation_authority") is not False
            or values.get("application_authority") is not False
            or values.get("ats_authority") is not False
        ):
            raise ValueError("saved_graph_safety_contract_invalid")
        prohibited = {
            "tailoring_result",
            "resume_content",
            "job_description",
            "provider_response",
            "prompt",
        }
        if prohibited.intersection(values):
            raise ValueError("saved_graph_raw_content_prohibited")
        return values

    @staticmethod
    def _graph_row_from_checkpoint(
        checkpoint: Mapping[str, Any],
        *,
        run_status: str,
        lock_version: int,
        updated_at: str,
    ) -> dict[str, Any]:
        envelope = checkpoint.get("checkpoint_envelope_json")
        if not isinstance(envelope, Mapping):
            raise ValueError("checkpoint_envelope_missing")
        return {
            "graph_invocation_id": checkpoint["graph_invocation_id"],
            "graph_engine": envelope["graph_engine"],
            "graph_state_schema_version": checkpoint[
                "graph_state_schema_version"
            ],
            **{
                field: checkpoint[field]
                for field in (
                    "owner_user_id",
                    "pipeline_run_id",
                    "context_id",
                    "job_id",
                    "job_index",
                    "selected_resume_id",
                )
            },
            "run_status": run_status,
            "current_checkpoint_id": checkpoint["checkpoint_id"],
            "lock_version": lock_version,
            "created_at": checkpoint["committed_at"],
            "updated_at": updated_at,
            "terminal_at": None,
            "purge_after": checkpoint.get("purge_after"),
        }

    def create_or_reopen_pause(
        self,
        *,
        bounded_tailoring_result: Mapping[str, Any],
        owner_user_id: str,
        pipeline_run_id: str,
        context_id: str,
        job_id: str,
        job_index: int,
        selected_resume_id: str,
        created_at: str,
        expires_at: str | None = None,
    ) -> ProductionHumanCheckpointResult:
        artifact_digest = production.canonical_digest(
            deepcopy(dict(bounded_tailoring_result)),
            field="bounded_tailoring_review_artifact",
        )
        graph_run = production.prepare_graph_run_row(
            graph_version=PRODUCTION_HUMAN_REVIEW_GRAPH_VERSION,
            state_version=PRODUCTION_HUMAN_REVIEW_STATE_VERSION,
            owner_user_id=owner_user_id,
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            job_id=job_id,
            job_index=job_index,
            selected_resume_id=selected_resume_id,
            production_node_key=production.PRODUCTION_HUMAN_REVIEW_NODE,
            input_digest=artifact_digest,
            created_at=created_at,
        )
        existing = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_run["graph_invocation_id"],
        )
        if _classification(existing) == "applied":
            return self.reopen_pause(
                owner_user_id=owner_user_id,
                graph_invocation_id=graph_run["graph_invocation_id"],
                expected_artifact_digest=artifact_digest,
            )
        if _classification(existing) not in {"not_found", ""}:
            return _safe_result(
                "pause_not_created",
                _classification(existing),
                graph_invocation_id=graph_run["graph_invocation_id"],
                review_artifact_digest=artifact_digest,
            )
        created = self._repository.create_production_graph_run(graph_run)
        if _classification(created) not in _ACCEPTED:
            return _safe_result(
                "pause_not_created",
                _classification(created),
                graph_invocation_id=graph_run["graph_invocation_id"],
                review_artifact_digest=artifact_digest,
            )
        initial_state: ProductionHumanReviewState = {
            "graph_version": PRODUCTION_HUMAN_REVIEW_GRAPH_VERSION,
            "state_version": PRODUCTION_HUMAN_REVIEW_STATE_VERSION,
            "graph_invocation_id": graph_run["graph_invocation_id"],
            "owner_user_id": graph_run["owner_user_id"],
            "pipeline_run_id": graph_run["pipeline_run_id"],
            "context_id": graph_run["context_id"],
            "job_id": graph_run["job_id"],
            "job_index": graph_run["job_index"],
            "selected_resume_id": graph_run["selected_resume_id"],
            "review_artifact_type": (
                production.PRODUCTION_TAILORING_REVIEW_ARTIFACT_TYPE
            ),
            "review_artifact_version": (
                production.PRODUCTION_TAILORING_REVIEW_ARTIFACT_VERSION
            ),
            "review_artifact_digest": artifact_digest,
            "current_node": "",
            "completed_nodes": [],
            "pending_node": production.PRODUCTION_HUMAN_REVIEW_NODE,
            "human_review_status": "generated",
            "read_only": True,
            "mutation_authority": False,
            "application_authority": False,
            "ats_authority": False,
        }
        config = {
            "configurable": {
                "thread_id": graph_run["graph_invocation_id"],
                "checkpoint_ns": "",
                "applylens_production_checkpoint_namespace": (
                    "production/human_review/v1"
                ),
            }
        }
        self._graph.invoke(initial_state, deepcopy(config))
        snapshot = self._graph.get_state(deepcopy(config))
        try:
            values = self._validate_snapshot(snapshot, expect_paused=True)
            saved = self._snapshot_config(snapshot)
        except ValueError:
            return _safe_result(
                "pause_not_created",
                "invalid_saved_graph_state",
                graph_invocation_id=graph_run["graph_invocation_id"],
                review_artifact_digest=artifact_digest,
            )
        saved_digest = production.canonical_digest(
            values, field="production_human_review_saved_state"
        )
        checkpoint = production.prepare_human_review_checkpoint_row(
            graph_run,
            artifact_digest=artifact_digest,
            saved_state_digest=saved_digest,
            committed_at=created_at,
        )
        interrupt = production.prepare_human_review_interrupt_row(
            checkpoint,
            created_at=created_at,
            expires_at=expires_at,
        )
        committed = self._repository.commit_checkpoint_interrupt(
            graph_invocation_id=graph_run["graph_invocation_id"],
            owner_user_id=owner_user_id,
            expected_run_status="running",
            expected_lock_version=0,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        )
        if _classification(committed) not in _ACCEPTED:
            return _safe_result(
                "pause_not_created",
                _classification(committed),
                graph_invocation_id=graph_run["graph_invocation_id"],
                review_artifact_digest=artifact_digest,
            )
        binding = production.prepare_checkpoint_binding_row(
            graph_run,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            langgraph_thread_id=saved["thread_id"],
            langgraph_checkpoint_namespace=saved["checkpoint_ns"],
            langgraph_checkpoint_id=saved["checkpoint_id"],
            event_timestamp=created_at,
        )
        bound = self._repository.commit_checkpoint_binding(binding)
        if _classification(bound) not in _ACCEPTED:
            return _safe_result(
                "pause_not_created",
                "reconciliation_required",
                graph_invocation_id=graph_run["graph_invocation_id"],
                review_artifact_digest=artifact_digest,
            )
        return ProductionHumanCheckpointResult(
            status="awaiting_review",
            classification="applied",
            graph_invocation_id=graph_run["graph_invocation_id"],
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            interrupt_request_id=interrupt["interrupt_request_id"],
            review_artifact_digest=artifact_digest,
            human_review_status="awaiting_review",
        )

    def reopen_pause(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
        expected_artifact_digest: str = "",
    ) -> ProductionHumanCheckpointResult:
        run = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        if _classification(run) != "applied":
            return _safe_result(
                "pause_not_reopened",
                _classification(run),
                graph_invocation_id=graph_invocation_id,
            )
        run_row = _record(run)
        if run_row.get("run_status") == "completed":
            terminal = self._repository.read_terminal_result(
                owner_user_id=owner_user_id,
                graph_invocation_id=graph_invocation_id,
            )
            terminal_row = _record(terminal)
            metadata = terminal_row.get("result_metadata_json")
            bounded = (
                metadata.get("bounded_result")
                if isinstance(metadata, Mapping)
                else {}
            )
            return _safe_result(
                "completed_replay",
                "already_terminal",
                graph_invocation_id=graph_invocation_id,
                repository_checkpoint_id=str(
                    terminal_row.get("terminal_checkpoint_id") or ""
                ),
                terminal_result_id=str(
                    terminal_row.get("terminal_result_id") or ""
                ),
                review_artifact_digest=str(
                    (
                        bounded.get("review_artifact_digest")
                        if isinstance(bounded, Mapping)
                        else ""
                    )
                    or ""
                ),
                human_review_status="human_reviewed",
            )
        if run_row.get("run_status") != "awaiting_decision":
            return _safe_result(
                "pause_not_reopened",
                "stale_state",
                graph_invocation_id=graph_invocation_id,
            )
        checkpoint_result = self._repository.read_checkpoint_by_id(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            checkpoint_id=str(run_row.get("current_checkpoint_id") or ""),
        )
        interrupt_result = self._repository.read_pending_interrupt(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        if (
            _classification(checkpoint_result) != "applied"
            or _classification(interrupt_result) != "applied"
        ):
            return _safe_result(
                "pause_not_reopened",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        checkpoint = _record(checkpoint_result)
        interrupt = _record(interrupt_result)
        envelope = checkpoint.get("checkpoint_envelope_json")
        artifact_digest = str(
            (
                envelope.get("review_artifact_digest")
                if isinstance(envelope, Mapping)
                else ""
            )
            or ""
        )
        if (
            expected_artifact_digest
            and artifact_digest != expected_artifact_digest
        ):
            return _safe_result(
                "pause_not_reopened",
                "identity_mismatch",
                graph_invocation_id=graph_invocation_id,
            )
        binding = self._repository.read_checkpoint_binding(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
        )
        payload = _record(binding).get("event_payload_json")
        if (
            _classification(binding) != "applied"
            or not isinstance(payload, Mapping)
        ):
            return _safe_result(
                "pause_not_reopened",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        config = {
            "configurable": {
                "thread_id": payload.get("langgraph_thread_id"),
                "checkpoint_ns": payload.get(
                    "langgraph_checkpoint_namespace"
                ),
                "checkpoint_id": payload.get("langgraph_checkpoint_id"),
            }
        }
        try:
            snapshot = self._graph.get_state(config)
            values = self._validate_snapshot(snapshot, expect_paused=True)
            if production.canonical_digest(
                values, field="production_human_review_saved_state"
            ) != checkpoint["checkpoint_envelope_json"].get(
                "saved_state_digest"
            ):
                raise ValueError("saved_state_digest_mismatch")
        except ValueError:
            return _safe_result(
                "pause_not_reopened",
                "invalid_saved_graph_state",
                graph_invocation_id=graph_invocation_id,
            )
        return ProductionHumanCheckpointResult(
            status="awaiting_review",
            classification="applied",
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            interrupt_request_id=interrupt["interrupt_request_id"],
            review_artifact_digest=artifact_digest,
            human_review_status="awaiting_review",
        )

    def record_decision(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
        repository_checkpoint_id: str,
        interrupt_request_id: str,
        decision_value: str,
        actor_id: str,
        client_idempotency_key: str,
        decision_reason: str,
        created_at: str,
        authorization_token: str = "",
        authorization_expires_at: str = "",
    ) -> ProductionHumanCheckpointResult:
        run_result = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        run_status = str(_record(run_result).get("run_status") or "")
        if run_status == "completed":
            existing_result = (
                self._repository.read_current_human_decision(
                    owner_user_id=owner_user_id,
                    interrupt_request_id=interrupt_request_id,
                )
            )
            existing = _record(existing_result)
            if (
                _classification(existing_result) != "applied"
                or existing.get("graph_invocation_id")
                != graph_invocation_id
                or existing.get("checkpoint_id")
                != repository_checkpoint_id
                or existing.get("decision_value") != decision_value
                or existing.get("actor_id") != actor_id
                or existing.get("client_idempotency_key")
                != client_idempotency_key
            ):
                return _safe_result(
                    "decision_not_recorded",
                    "duplicate_conflict",
                    graph_invocation_id=graph_invocation_id,
                )
            if decision_value != "continue_read_only":
                return _safe_result(
                    "decision_not_recorded",
                    "duplicate_conflict",
                    graph_invocation_id=graph_invocation_id,
                )
            replay = self.reopen_pause(
                owner_user_id=owner_user_id,
                graph_invocation_id=graph_invocation_id,
            )
            if replay.status != "completed_replay":
                return _safe_result(
                    "decision_not_recorded",
                    "reconciliation_required",
                    graph_invocation_id=graph_invocation_id,
                )
            return ProductionHumanCheckpointResult(
                status="completed_replay",
                classification="idempotent_existing",
                graph_invocation_id=graph_invocation_id,
                repository_checkpoint_id=(
                    replay.repository_checkpoint_id
                ),
                interrupt_request_id=interrupt_request_id,
                decision_id=str(existing.get("decision_id") or ""),
                terminal_result_id=replay.terminal_result_id,
                review_artifact_digest=replay.review_artifact_digest,
                human_review_status="human_reviewed",
            )
        if run_status in {
            "decision_recorded",
            "resume_authorized",
            "decision_rejected",
            "cancelled",
        }:
            existing_result = (
                self._repository.read_current_human_decision(
                    owner_user_id=owner_user_id,
                    interrupt_request_id=interrupt_request_id,
                )
            )
            existing = _record(existing_result)
            if (
                _classification(existing_result) != "applied"
                or existing.get("checkpoint_id")
                != repository_checkpoint_id
                or existing.get("decision_value") != decision_value
                or existing.get("actor_id") != actor_id
                or existing.get("client_idempotency_key")
                != client_idempotency_key
            ):
                return _safe_result(
                    "decision_not_recorded",
                    "duplicate_conflict",
                    graph_invocation_id=graph_invocation_id,
                )
            if decision_value != "continue_read_only":
                return ProductionHumanCheckpointResult(
                    status=(
                        "revision_required"
                        if decision_value == "needs_revision"
                        else "cancelled"
                    ),
                    classification="idempotent_existing",
                    graph_invocation_id=graph_invocation_id,
                    repository_checkpoint_id=repository_checkpoint_id,
                    interrupt_request_id=interrupt_request_id,
                    decision_id=str(existing["decision_id"]),
                    human_review_status=(
                        "revision_required"
                        if decision_value == "needs_revision"
                        else "cancelled"
                    ),
                )
            if run_status == "resume_authorized":
                authorization_result = (
                    self._repository.read_resume_authorization(
                        owner_user_id=owner_user_id,
                        decision_id=str(existing["decision_id"]),
                    )
                )
                authorization = _record(authorization_result)
                if _classification(authorization_result) != "applied":
                    return _safe_result(
                        "decision_recorded",
                        "reconciliation_required",
                        graph_invocation_id=graph_invocation_id,
                    )
                return ProductionHumanCheckpointResult(
                    status="resume_authorized",
                    classification="idempotent_existing",
                    graph_invocation_id=graph_invocation_id,
                    repository_checkpoint_id=repository_checkpoint_id,
                    interrupt_request_id=interrupt_request_id,
                    decision_id=str(existing["decision_id"]),
                    authorization_id=str(
                        authorization.get("authorization_id") or ""
                    ),
                    human_review_status="decision_recorded",
                )
            token_hash = hash_resume_authorization_token(
                authorization_token
            )
            authorization = (
                production.prepare_human_review_authorization_row(
                    existing,
                    authorization_token_hash=token_hash,
                    created_at=created_at,
                    expires_at=authorization_expires_at,
                )
            )
            authorized = self._repository.create_resume_authorization(
                authorization,
                expected_run_lock_version=2,
                expected_interrupt_version=1,
            )
            return ProductionHumanCheckpointResult(
                status=(
                    "resume_authorized"
                    if _classification(authorized) in _ACCEPTED
                    else "decision_recorded"
                ),
                classification=_classification(authorized),
                graph_invocation_id=graph_invocation_id,
                repository_checkpoint_id=repository_checkpoint_id,
                interrupt_request_id=interrupt_request_id,
                decision_id=str(existing["decision_id"]),
                authorization_id=(
                    authorization["authorization_id"]
                    if _classification(authorized) in _ACCEPTED
                    else ""
                ),
                human_review_status="decision_recorded",
            )
        reopened = self.reopen_pause(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        if reopened.classification != "applied":
            return reopened
        if (
            reopened.repository_checkpoint_id != repository_checkpoint_id
            or reopened.interrupt_request_id != interrupt_request_id
        ):
            return _safe_result(
                "decision_not_recorded",
                "stale_state",
                graph_invocation_id=graph_invocation_id,
            )
        interrupt_result = self._repository.read_pending_interrupt_full(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        interrupt = _record(interrupt_result)
        decision = production.prepare_human_review_decision_row(
            interrupt,
            decision_value=decision_value,
            actor_id=actor_id,
            client_idempotency_key=client_idempotency_key,
            expected_interrupt_version=0,
            expected_run_lock_version=1,
            created_at=created_at,
            reason=decision_reason,
        )
        recorded = self._repository.record_human_decision(decision)
        if _classification(recorded) not in _ACCEPTED:
            return _safe_result(
                "decision_not_recorded",
                _classification(recorded),
                graph_invocation_id=graph_invocation_id,
            )
        if decision_value != "continue_read_only":
            return ProductionHumanCheckpointResult(
                status=(
                    "revision_required"
                    if decision_value == "needs_revision"
                    else "cancelled"
                ),
                classification=_classification(recorded),
                graph_invocation_id=graph_invocation_id,
                repository_checkpoint_id=repository_checkpoint_id,
                interrupt_request_id=interrupt_request_id,
                decision_id=decision["decision_id"],
                review_artifact_digest=reopened.review_artifact_digest,
                human_review_status=(
                    "revision_required"
                    if decision_value == "needs_revision"
                    else "cancelled"
                ),
            )
        token_hash = hash_resume_authorization_token(
            authorization_token
        )
        authorization = (
            production.prepare_human_review_authorization_row(
                decision,
                authorization_token_hash=token_hash,
                created_at=created_at,
                expires_at=authorization_expires_at,
            )
        )
        authorized = self._repository.create_resume_authorization(
            authorization,
            expected_run_lock_version=2,
            expected_interrupt_version=1,
        )
        if _classification(authorized) not in _ACCEPTED:
            return _safe_result(
                "decision_recorded",
                _classification(authorized),
                graph_invocation_id=graph_invocation_id,
                decision_id=decision["decision_id"],
            )
        return ProductionHumanCheckpointResult(
            status="resume_authorized",
            classification=_classification(authorized),
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=repository_checkpoint_id,
            interrupt_request_id=interrupt_request_id,
            decision_id=decision["decision_id"],
            authorization_id=authorization["authorization_id"],
            review_artifact_digest=reopened.review_artifact_digest,
            human_review_status="decision_recorded",
        )

    def resume(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
        repository_checkpoint_id: str,
        interrupt_request_id: str,
        decision_id: str,
        authorization_token: str,
        claimed_at: str,
        lease_expires_at: str,
        completed_at: str,
        duration_ms: int,
    ) -> ProductionHumanCheckpointResult:
        run = self._repository.read_graph_run(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        run_record = _record(run)
        if (
            _classification(run) != "applied"
            or run_record.get("run_status") != "resume_authorized"
            or run_record.get("current_checkpoint_id")
            != repository_checkpoint_id
        ):
            return _safe_result(
                "resume_not_consumed",
                (
                    _classification(run)
                    if _classification(run) != "applied"
                    else "stale_state"
                ),
                graph_invocation_id=graph_invocation_id,
            )
        checkpoint_result = self._repository.read_checkpoint_by_id(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            checkpoint_id=repository_checkpoint_id,
        )
        decision_result = self._repository.read_current_human_decision(
            owner_user_id=owner_user_id,
            interrupt_request_id=interrupt_request_id,
        )
        authorization_result = self._repository.read_resume_authorization(
            owner_user_id=owner_user_id,
            decision_id=decision_id,
        )
        if any(
            _classification(item) != "applied"
            for item in (
                checkpoint_result,
                decision_result,
                authorization_result,
            )
        ):
            return _safe_result(
                "resume_not_consumed",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        checkpoint = _record(checkpoint_result)
        decision = _record(decision_result)
        authorization = _record(authorization_result)
        if (
            decision.get("decision_id") != decision_id
            or authorization.get("interrupt_request_id")
            != interrupt_request_id
            or authorization.get("checkpoint_id")
            != repository_checkpoint_id
        ):
            return _safe_result(
                "resume_not_consumed",
                "identity_mismatch",
                graph_invocation_id=graph_invocation_id,
            )
        token_hash = hash_resume_authorization_token(
            authorization_token
        )
        authorization_with_hash = {
            **authorization,
            "authorization_token_hash": token_hash,
        }
        consumption = production.prepare_human_review_consumption_row(
            authorization_with_hash,
            consumer_instance_id=self._consumer_instance_id,
            claimed_at=claimed_at,
        )
        consumed = self._repository.consume_resume_authorization(
            consumption,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=token_hash,
        )
        if _classification(consumed) not in _ACCEPTED:
            return _safe_result(
                "resume_not_consumed",
                _classification(consumed),
                graph_invocation_id=graph_invocation_id,
            )
        consumed_record = _record(consumed) or {
            key: value
            for key, value in consumption.items()
            if key != "authorization_token_hash_proof"
        }
        consumed_graph = self._graph_row_from_checkpoint(
            checkpoint,
            run_status="resume_consumed",
            lock_version=4,
            updated_at=claimed_at,
        )
        attempt = production.prepare_node_attempt_row(
            consumed_graph,
            input_checkpoint_id=repository_checkpoint_id,
            production_node_key=(
                production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE
            ),
            input_digest=checkpoint["checkpoint_envelope_digest"],
            created_at=claimed_at,
        )
        attempt["resume_invocation_id"] = consumed_record[
            "resume_invocation_id"
        ]
        pending_event = production.prepare_lifecycle_event_row(
            consumed_graph,
            event_type="recovery_claim_recorded",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=0,
            event_payload={"status": "pending", "read_only": True},
            event_timestamp=claimed_at,
            references={
                "checkpoint_id": repository_checkpoint_id,
                "interrupt_request_id": interrupt_request_id,
                "decision_id": decision_id,
                "authorization_id": authorization["authorization_id"],
                "consumption_id": consumed_record["consumption_id"],
                "node_attempt_id": attempt["node_attempt_id"],
            },
        )
        pending = self._repository.create_pending_finalize_attempt(
            consumed_record,
            consumed_graph,
            attempt,
            pending_event,
            expected_run_lock_version=4,
        )
        if _classification(pending) not in _ACCEPTED:
            return _safe_result(
                "resume_not_started",
                _classification(pending),
                graph_invocation_id=graph_invocation_id,
            )
        resumed_graph = {
            **consumed_graph,
            "run_status": "resumed",
            "lock_version": 5,
        }
        claim_event = production.prepare_lifecycle_event_row(
            resumed_graph,
            event_type="node_attempt_claimed",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=1,
            event_payload={"status": "claimed", "read_only": True},
            event_timestamp=claimed_at,
            references={
                "checkpoint_id": repository_checkpoint_id,
                "node_attempt_id": attempt["node_attempt_id"],
            },
        )
        claimed = self._repository.claim_attempt(
            attempt,
            claim_event,
            lease_owner_id=self._consumer_instance_id,
            lease_acquired_at=claimed_at,
            lease_expires_at=lease_expires_at,
            expected_lock_version=0,
            expected_run_lock_version=5,
        )
        if _classification(claimed) not in _ACCEPTED:
            return _safe_result(
                "resume_not_started",
                _classification(claimed),
                graph_invocation_id=graph_invocation_id,
            )
        claimed_attempt = _record(claimed)
        binding_result = self._repository.read_checkpoint_binding(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=repository_checkpoint_id,
        )
        payload = _record(binding_result).get("event_payload_json")
        if not isinstance(payload, Mapping):
            return _safe_result(
                "resume_not_started",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        saved_config = {
            "configurable": {
                "thread_id": payload.get("langgraph_thread_id"),
                "checkpoint_ns": payload.get(
                    "langgraph_checkpoint_namespace"
                ),
                "checkpoint_id": payload.get("langgraph_checkpoint_id"),
            }
        }
        self._graph.invoke(None, deepcopy(saved_config))
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
            final_values = self._validate_snapshot(
                final_snapshot, expect_paused=False
            )
            final_saved = self._snapshot_config(final_snapshot)
        except ValueError:
            return _safe_result(
                "resume_failed",
                "invalid_saved_graph_state",
                graph_invocation_id=graph_invocation_id,
            )
        final_checkpoint = (
            production.prepare_human_review_terminal_checkpoint_row(
                resumed_graph,
                parent_checkpoint_row=checkpoint,
                saved_state_digest=production.canonical_digest(
                    final_values,
                    field="production_human_review_saved_state",
                ),
                committed_at=completed_at,
            )
        )
        committed = self._repository.commit_final_checkpoint(
            final_checkpoint,
            parent_checkpoint_id=repository_checkpoint_id,
            expected_run_lock_version=5,
        )
        if _classification(committed) not in _ACCEPTED:
            return _safe_result(
                "resume_failed",
                _classification(committed),
                graph_invocation_id=graph_invocation_id,
            )
        final_binding = production.prepare_checkpoint_binding_row(
            resumed_graph,
            repository_checkpoint_id=final_checkpoint["checkpoint_id"],
            langgraph_thread_id=final_saved["thread_id"],
            langgraph_checkpoint_namespace=final_saved["checkpoint_ns"],
            langgraph_checkpoint_id=final_saved["checkpoint_id"],
            event_timestamp=completed_at,
        )
        bound = self._repository.commit_checkpoint_binding(final_binding)
        if _classification(bound) not in _ACCEPTED:
            return _safe_result(
                "resume_failed",
                "reconciliation_required",
                graph_invocation_id=graph_invocation_id,
            )
        success_event = production.prepare_lifecycle_event_row(
            resumed_graph,
            event_type="node_attempt_succeeded",
            aggregate_type="node_attempt",
            aggregate_id=attempt["node_attempt_id"],
            event_sequence=2,
            event_payload={"status": "succeeded", "read_only": True},
            event_timestamp=completed_at,
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
            completed_at=completed_at,
            duration_ms=duration_ms,
            lease_owner_id=self._consumer_instance_id,
            expected_lock_version=1,
            expected_run_lock_version=5,
        )
        if _classification(succeeded) not in _ACCEPTED:
            return _safe_result(
                "resume_failed",
                _classification(succeeded),
                graph_invocation_id=graph_invocation_id,
            )
        successful_attempt = _record(succeeded)
        completed_graph = {
            **resumed_graph,
            "current_checkpoint_id": final_checkpoint["checkpoint_id"],
            "lock_version": 6,
            "updated_at": completed_at,
        }
        terminal_payload = {
            "review_artifact_type": (
                checkpoint["checkpoint_envelope_json"][
                    "review_artifact_type"
                ]
            ),
            "review_artifact_version": (
                checkpoint["checkpoint_envelope_json"][
                    "review_artifact_version"
                ]
            ),
            "review_artifact_digest": (
                checkpoint["checkpoint_envelope_json"][
                    "review_artifact_digest"
                ]
            ),
            "decision_value": "continue_read_only",
            "human_review_status": "human_reviewed",
            "read_only": True,
            "mutation_authority": False,
            "application_authority": False,
            "ats_authority": False,
        }
        terminal = production.prepare_terminal_result_row(
            completed_graph,
            terminal_checkpoint_id=final_checkpoint["checkpoint_id"],
            production_node_key=(
                production.PRODUCTION_HUMAN_REVIEW_SAFE_NEXT_NODE
            ),
            input_digest=checkpoint["checkpoint_envelope_digest"],
            bounded_result=terminal_payload,
            completed_at=completed_at,
        )
        terminal_event = production.prepare_lifecycle_event_row(
            completed_graph,
            event_type="terminal_result_recorded",
            aggregate_type="graph_run",
            aggregate_id=graph_invocation_id,
            event_sequence=3,
            event_payload={
                "terminal_status": "completed",
                "human_review_status": "human_reviewed",
                "read_only": True,
            },
            event_timestamp=completed_at,
            references={
                "checkpoint_id": final_checkpoint["checkpoint_id"],
                "node_attempt_id": attempt["node_attempt_id"],
                "terminal_result_id": terminal["terminal_result_id"],
            },
        )
        terminalized = self._repository.terminalize_production_run(
            completed_graph,
            terminal,
            terminal_event,
            successful_attempt_row=successful_attempt,
            final_binding_row=final_binding,
            expected_run_lock_version=6,
        )
        if _classification(terminalized) not in _ACCEPTED:
            return _safe_result(
                "resume_failed",
                _classification(terminalized),
                graph_invocation_id=graph_invocation_id,
            )
        return ProductionHumanCheckpointResult(
            status="completed",
            classification=_classification(terminalized),
            graph_invocation_id=graph_invocation_id,
            repository_checkpoint_id=final_checkpoint["checkpoint_id"],
            interrupt_request_id=interrupt_request_id,
            decision_id=decision_id,
            authorization_id=authorization["authorization_id"],
            consumption_id=consumed_record["consumption_id"],
            terminal_result_id=terminal["terminal_result_id"],
            review_artifact_digest=terminal_payload[
                "review_artifact_digest"
            ],
            human_review_status="human_reviewed",
        )


__all__ = [
    "PRODUCTION_HUMAN_CHECKPOINT_COORDINATOR_VERSION",
    "PRODUCTION_HUMAN_CHECKPOINT_FLAG",
    "PRODUCTION_HUMAN_REVIEW_GRAPH_VERSION",
    "PRODUCTION_HUMAN_REVIEW_STATE_VERSION",
    "ProductionHumanCheckpointCoordinator",
    "ProductionHumanCheckpointResult",
    "build_production_human_review_graph",
    "hash_resume_authorization_token",
]

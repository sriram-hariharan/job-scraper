from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Dict, List, Mapping, TypedDict

from src.agents.critic_agent import build_critic_resume_match_jd_evidence_artifact
from src.agents.evidence_chain_composition import (
    ORDERED_AGENT_KEYS,
    build_agent_evidence_chain_bundle,
    build_agent_evidence_chain_trace_payload,
)
from src.agents.evidence_chain_execution import (
    DEFAULT_SAMPLE_LIMIT,
    FALSE_SAFETY_FLAGS,
)
from src.agents.jd_intelligence import describe_existing_job_intelligence_result
from src.agents.job_prioritization_agent import (
    build_job_prioritization_critic_evidence_artifact,
)
from src.agents.operator_review_agent import (
    OPERATOR_REVIEW_LANES,
    OPERATOR_REVIEW_TAILORING_EVIDENCE_ARTIFACT_VERSION,
    build_operator_review_tailoring_evidence_artifact,
)
from src.agents.resume_match_agent import build_resume_match_jd_evidence_artifact
from src.agents.tailoring_decision_agent import (
    build_tailoring_decision_priority_evidence_artifact,
)


LANGGRAPH_EVIDENCE_CHAIN_GATE_NAME = (
    "APPLYLENS_AGENTIC_LANGGRAPH_EVIDENCE_CHAIN_ENABLED"
)
LANGGRAPH_EVIDENCE_CHAIN_VERSION = "langgraph-evidence-chain-harness-v1"
CHECKPOINT_SCHEMA_VERSION = "evidence-chain-checkpoint-envelope-v1"
GRAPH_STATE_SCHEMA_VERSION = "evidence-chain-graph-state-v1"
CHECKPOINT_GRAPH_ENGINE = "langgraph-evidence-chain"
CHECKPOINT_STATUS = "diagnostic_snapshot"
OPERATOR_REVIEW_INTERRUPT_REQUEST_SCHEMA_VERSION = (
    "operator-review-interrupt-request-v1"
)
OPERATOR_REVIEW_INTERRUPT_NODE_KEY = "operator_review"
OPERATOR_REVIEW_INTERRUPT_SAFE_NEXT_NODE_KEY = "finalize"
OPERATOR_REVIEW_INTERRUPT_ALLOWED_DECISIONS = (
    "continue_read_only",
    "needs_revision",
    "cancel",
)
ARTIFACT_KEYS_BY_AGENT = {
    "jd_intelligence": "jd_intelligence",
    "resume_match": "resume_match_jd_evidence",
    "critic": "critic_resume_match_jd_evidence",
    "job_prioritization": "job_prioritization_critic_evidence",
    "tailoring_decision": "tailoring_decision_priority_evidence",
    "operator_review": "operator_review_tailoring_evidence",
}


EvidenceChainArtifact = Dict[str, Any]
EvidenceChainArtifacts = Dict[str, EvidenceChainArtifact]
EvidenceChainGraphWarnings = List[str]


class EvidenceChainNodeSummary(TypedDict):
    agent_key: str
    node_key: str
    status: str
    artifact_key: str
    artifact_type: str
    reason_codes: List[str]


class EvidenceChainInitialState(TypedDict):
    job: Dict[str, Any]
    job_index: int
    job_identity: Dict[str, str]
    resume_rows: List[Dict[str, Any]]
    selected_resume_id: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    include_trace_payload: bool
    artifacts: EvidenceChainArtifacts
    ordered_node_keys: List[str]
    node_statuses: List[EvidenceChainNodeSummary]
    warnings: EvidenceChainGraphWarnings


class EvidenceChainGraphState(EvidenceChainInitialState, total=False):
    evidence_chain_bundle: Dict[str, Any]
    trace_payload: Dict[str, Any]


class EvidenceChainCheckpointIdentityPayload(TypedDict):
    graph_engine: str
    checkpoint_schema_version: str
    graph_state_schema_version: str
    owner_user_id: str
    pipeline_run_id: str
    context_id: str
    job_id: str
    job_index: int
    selected_resume_id: str
    graph_invocation_id: str
    checkpoint_id: str


class EvidenceChainCheckpointEnvelope(TypedDict):
    checkpoint_schema_version: str
    graph_state_schema_version: str
    checkpoint_identity: EvidenceChainCheckpointIdentityPayload
    checkpoint_status: str
    diagnostic_only: bool
    read_only: bool
    durable: bool
    resumable: bool
    persistence_performed: bool
    completed_node_keys: List[str]
    next_node_key: str
    state: Dict[str, Any]


class OperatorReviewInterruptRequest(TypedDict):
    interrupt_request_schema_version: str
    interrupt_request_id: str
    graph_engine: str
    graph_invocation_id: str
    checkpoint_id: str
    checkpoint_schema_version: str
    graph_state_schema_version: str
    owner_user_id: str
    pipeline_run_id: str
    context_id: str
    job_id: str
    job_index: int
    selected_resume_id: str
    node_key: str
    completed_node_keys: List[str]
    safe_next_node_key: str
    operator_review_artifact_type: str
    operator_review_artifact_version: str
    operator_review_artifact_digest: str
    operator_review_lane: str
    operator_review_readiness: str
    human_review_required: bool
    recommended_next_step: str
    reason_codes: List[str]
    validation_status: str
    allowed_decision_values: List[str]
    read_only: bool
    diagnostic_only: bool
    persistent: bool
    resumable: bool
    application_authorization: bool
    resume_authorization: bool


@dataclass(frozen=True, slots=True)
class EvidenceChainCheckpointIdentity:
    graph_engine: str
    checkpoint_schema_version: str
    graph_state_schema_version: str
    owner_user_id: str
    pipeline_run_id: str
    context_id: str
    job_id: str
    job_index: int
    selected_resume_id: str
    graph_invocation_id: str
    checkpoint_id: str

    def to_payload(self) -> EvidenceChainCheckpointIdentityPayload:
        return {
            "graph_engine": self.graph_engine,
            "checkpoint_schema_version": self.checkpoint_schema_version,
            "graph_state_schema_version": self.graph_state_schema_version,
            "owner_user_id": self.owner_user_id,
            "pipeline_run_id": self.pipeline_run_id,
            "context_id": self.context_id,
            "job_id": self.job_id,
            "job_index": self.job_index,
            "selected_resume_id": self.selected_resume_id,
            "graph_invocation_id": self.graph_invocation_id,
            "checkpoint_id": self.checkpoint_id,
        }


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_sample_limit(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_SAMPLE_LIMIT
    if parsed < 0:
        return 0
    return min(parsed, DEFAULT_SAMPLE_LIMIT)


def _jobs_list(jobs: Any) -> List[Dict[str, Any]]:
    if jobs is None:
        return []
    if isinstance(jobs, Mapping):
        return [deepcopy(dict(jobs))]
    if isinstance(jobs, (list, tuple)):
        return [
            deepcopy(dict(job))
            for job in jobs
            if isinstance(job, Mapping)
        ]
    return []


def _resume_rows_and_selection(
    resume_context: Any,
) -> tuple[List[Dict[str, Any]], str]:
    if resume_context is None:
        return [], ""
    if isinstance(resume_context, list):
        return [
            deepcopy(dict(row))
            for row in resume_context
            if isinstance(row, Mapping)
        ], ""
    if not isinstance(resume_context, Mapping):
        return [], ""

    context = dict(resume_context)
    raw_rows = (
        context.get("resume_variants")
        if context.get("resume_variants") is not None
        else context.get("resume_evidence_rows")
    )
    if raw_rows is None and any(
        key in context
        for key in ("resume_id", "skills", "raw_text", "bullets", "tools")
    ):
        raw_rows = [context]
    rows = [
        deepcopy(dict(row))
        for row in list(raw_rows or [])
        if isinstance(row, Mapping)
    ]
    return rows, _clean_text(context.get("selected_resume_id"))


def _job_identity(job: Mapping[str, Any], index: int) -> Dict[str, str]:
    return {
        "job_id": _clean_text(
            job.get("job_id")
            or job.get("id")
            or job.get("job_key")
            or f"sampled-job-{index + 1}"
        ),
        "title": _clean_text(job.get("title") or job.get("job_title")),
        "company": _clean_text(job.get("company")),
    }


def _safety_metadata(*, automatic_internal_decisioning_performed: bool) -> Dict[str, bool]:
    return {
        **{flag: False for flag in FALSE_SAFETY_FLAGS},
        "automatic_internal_decisioning_performed": bool(
            automatic_internal_decisioning_performed
        ),
    }


def _reason_codes_from_artifacts(artifacts: Mapping[str, Any]) -> List[str]:
    reason_codes: List[str] = []
    for artifact in artifacts.values():
        if isinstance(artifact, Mapping):
            reason_codes.extend(
                _clean_text(code)
                for code in list(artifact.get("reason_codes") or [])
                if _clean_text(code)
            )
            reason_codes.extend(
                _clean_text(code)
                for code in list(artifact.get("chain_reason_codes") or [])
                if _clean_text(code)
            )
    return list(dict.fromkeys(reason_codes))


def _node_summary(agent_key: str, artifact: Any) -> EvidenceChainNodeSummary:
    artifact_type = artifact.get("artifact_type", "") if isinstance(artifact, Mapping) else ""
    reason_codes = artifact.get("reason_codes", []) if isinstance(artifact, Mapping) else []
    return {
        "agent_key": agent_key,
        "node_key": agent_key,
        "status": "completed",
        "artifact_key": ARTIFACT_KEYS_BY_AGENT[agent_key],
        "artifact_type": _clean_text(artifact_type),
        "reason_codes": [
            _clean_text(code)
            for code in list(reason_codes or [])
            if _clean_text(code)
        ],
    }


def _build_initial_graph_state(
    *,
    job: Mapping[str, Any],
    job_index: int,
    job_identity: Mapping[str, Any],
    resume_rows: List[Dict[str, Any]],
    selected_resume_id: str,
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    include_trace_payload: bool,
) -> EvidenceChainInitialState:
    return {
        "job": deepcopy(dict(job)),
        "job_index": int(job_index),
        "job_identity": {
            "job_id": _clean_text(job_identity.get("job_id")),
            "title": _clean_text(job_identity.get("title")),
            "company": _clean_text(job_identity.get("company")),
        },
        "resume_rows": deepcopy(list(resume_rows)),
        "selected_resume_id": _clean_text(selected_resume_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "context_id": _clean_text(context_id),
        "include_trace_payload": bool(include_trace_payload),
        "artifacts": {},
        "ordered_node_keys": [],
        "node_statuses": [],
        "warnings": [],
    }


def _copy_state_for_transition(
    state: EvidenceChainGraphState,
) -> EvidenceChainGraphState:
    next_state: EvidenceChainGraphState = dict(state)
    next_state["artifacts"] = deepcopy(dict(state.get("artifacts") or {}))
    next_state["ordered_node_keys"] = list(state.get("ordered_node_keys") or [])
    next_state["node_statuses"] = deepcopy(list(state.get("node_statuses") or []))
    next_state["warnings"] = list(state.get("warnings") or [])
    return next_state


def _checkpoint_json_value(value: Any, *, field_path: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(
                f"checkpoint_value_not_json_compatible:{field_path}"
            )
        return value
    if isinstance(value, Mapping):
        normalized: Dict[str, Any] = {}
        keys = list(value)
        if not all(isinstance(key, str) for key in keys):
            raise ValueError(
                f"checkpoint_mapping_key_not_text:{field_path}"
            )
        for key in sorted(keys):
            child_path = f"{field_path}.{key}" if field_path else key
            normalized[key] = _checkpoint_json_value(
                value[key],
                field_path=child_path,
            )
        return normalized
    if isinstance(value, list):
        return [
            _checkpoint_json_value(
                item,
                field_path=f"{field_path}[{index}]",
            )
            for index, item in enumerate(value)
        ]
    raise ValueError(f"checkpoint_value_not_json_compatible:{field_path}")


def _canonical_checkpoint_json(value: Any) -> str:
    normalized = _checkpoint_json_value(value, field_path="checkpoint")
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _checkpoint_digest(value: Any) -> str:
    encoded = _canonical_checkpoint_json(value).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _checkpoint_completed_node_keys(
    state: Mapping[str, Any],
) -> List[str]:
    completed = [
        _clean_text(node_key)
        for node_key in list(state.get("ordered_node_keys") or [])
    ]
    expected_prefix = list(ORDERED_AGENT_KEYS)[: len(completed)]
    if completed != expected_prefix:
        raise ValueError("checkpoint_completed_node_keys_invalid")
    return completed


def _checkpoint_next_node_key(
    state: Mapping[str, Any],
    completed_node_keys: List[str],
) -> str:
    if isinstance(state.get("evidence_chain_bundle"), Mapping):
        return ""
    if len(completed_node_keys) < len(ORDERED_AGENT_KEYS):
        return ORDERED_AGENT_KEYS[len(completed_node_keys)]
    return "finalize"


def _build_checkpoint_identity(
    state: Mapping[str, Any],
) -> EvidenceChainCheckpointIdentity:
    identity = state.get("job_identity")
    if not isinstance(identity, Mapping):
        raise ValueError("checkpoint_identity_missing_required_field:job_identity")
    required_text = {
        "owner_user_id": _clean_text(state.get("owner_user_id")),
        "pipeline_run_id": _clean_text(state.get("pipeline_run_id")),
        "context_id": _clean_text(state.get("context_id")),
        "job_id": _clean_text(identity.get("job_id")),
    }
    for field_name, field_value in required_text.items():
        if not field_value:
            raise ValueError(
                f"checkpoint_identity_missing_required_field:{field_name}"
            )
    job_index = state.get("job_index")
    if isinstance(job_index, bool) or not isinstance(job_index, int) or job_index < 0:
        raise ValueError("checkpoint_identity_invalid_job_index")

    completed_node_keys = _checkpoint_completed_node_keys(state)
    invocation_seed = {
        "graph_engine": CHECKPOINT_GRAPH_ENGINE,
        "graph_state_schema_version": GRAPH_STATE_SCHEMA_VERSION,
        **required_text,
        "job_index": job_index,
        "selected_resume_id": _clean_text(state.get("selected_resume_id")),
        "include_trace_payload": bool(state.get("include_trace_payload")),
        "job": state.get("job"),
        "job_identity": identity,
        "resume_rows": state.get("resume_rows"),
    }
    graph_invocation_id = (
        "langgraph-evidence-chain-invocation:"
        + _checkpoint_digest(invocation_seed)
    )
    state_snapshot = _checkpoint_json_value(state, field_path="state")
    checkpoint_id = (
        "langgraph-evidence-chain-checkpoint:"
        + _checkpoint_digest(
            {
                "graph_invocation_id": graph_invocation_id,
                "completed_node_keys": completed_node_keys,
                "state": state_snapshot,
            }
        )
    )
    return EvidenceChainCheckpointIdentity(
        graph_engine=CHECKPOINT_GRAPH_ENGINE,
        checkpoint_schema_version=CHECKPOINT_SCHEMA_VERSION,
        graph_state_schema_version=GRAPH_STATE_SCHEMA_VERSION,
        owner_user_id=required_text["owner_user_id"],
        pipeline_run_id=required_text["pipeline_run_id"],
        context_id=required_text["context_id"],
        job_id=required_text["job_id"],
        job_index=job_index,
        selected_resume_id=_clean_text(state.get("selected_resume_id")),
        graph_invocation_id=graph_invocation_id,
        checkpoint_id=checkpoint_id,
    )


def _build_checkpoint_envelope(
    state: Mapping[str, Any],
) -> EvidenceChainCheckpointEnvelope:
    state_snapshot = _checkpoint_json_value(state, field_path="state")
    completed_node_keys = _checkpoint_completed_node_keys(state_snapshot)
    identity = _build_checkpoint_identity(state_snapshot)
    return {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "graph_state_schema_version": GRAPH_STATE_SCHEMA_VERSION,
        "checkpoint_identity": identity.to_payload(),
        "checkpoint_status": CHECKPOINT_STATUS,
        "diagnostic_only": True,
        "read_only": True,
        "durable": False,
        "resumable": False,
        "persistence_performed": False,
        "completed_node_keys": completed_node_keys,
        "next_node_key": _checkpoint_next_node_key(
            state_snapshot,
            completed_node_keys,
        ),
        "state": state_snapshot,
    }


def _serialize_checkpoint_envelope(
    envelope: Mapping[str, Any],
) -> str:
    return _canonical_checkpoint_json(envelope)


def _deserialize_checkpoint_envelope(
    serialized_envelope: str,
) -> EvidenceChainCheckpointEnvelope:
    if not isinstance(serialized_envelope, str) or not serialized_envelope.strip():
        raise ValueError("checkpoint_payload_malformed")
    try:
        decoded = json.loads(serialized_envelope)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("checkpoint_payload_malformed") from exc
    if not isinstance(decoded, Mapping):
        raise ValueError("checkpoint_payload_malformed")

    expected_fields = {
        "checkpoint_schema_version",
        "graph_state_schema_version",
        "checkpoint_identity",
        "checkpoint_status",
        "diagnostic_only",
        "read_only",
        "durable",
        "resumable",
        "persistence_performed",
        "completed_node_keys",
        "next_node_key",
        "state",
    }
    if set(decoded) != expected_fields:
        raise ValueError("checkpoint_envelope_fields_invalid")
    if decoded.get("checkpoint_schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("checkpoint_schema_version_unsupported")
    if decoded.get("graph_state_schema_version") != GRAPH_STATE_SCHEMA_VERSION:
        raise ValueError("checkpoint_graph_state_schema_version_unsupported")
    if (
        decoded.get("checkpoint_status") != CHECKPOINT_STATUS
        or decoded.get("diagnostic_only") is not True
        or decoded.get("read_only") is not True
        or decoded.get("durable") is not False
        or decoded.get("resumable") is not False
        or decoded.get("persistence_performed") is not False
    ):
        raise ValueError("checkpoint_safety_metadata_invalid")

    state = decoded.get("state")
    identity_payload = decoded.get("checkpoint_identity")
    completed_node_keys = decoded.get("completed_node_keys")
    if not isinstance(state, Mapping):
        raise ValueError("checkpoint_state_malformed")
    if not isinstance(identity_payload, Mapping):
        raise ValueError("checkpoint_identity_malformed")
    expected_identity_fields = set(
        EvidenceChainCheckpointIdentityPayload.__required_keys__
    )
    if set(identity_payload) != expected_identity_fields:
        raise ValueError("checkpoint_identity_fields_invalid")
    if not isinstance(completed_node_keys, list):
        raise ValueError("checkpoint_completed_node_keys_invalid")

    normalized_state = _checkpoint_json_value(state, field_path="state")
    normalized_completed = _checkpoint_completed_node_keys(normalized_state)
    if completed_node_keys != normalized_completed:
        raise ValueError("checkpoint_completed_node_keys_mismatch")
    expected_next_node = _checkpoint_next_node_key(
        normalized_state,
        normalized_completed,
    )
    if decoded.get("next_node_key") != expected_next_node:
        raise ValueError("checkpoint_next_node_mismatch")
    expected_identity = _build_checkpoint_identity(normalized_state).to_payload()
    normalized_identity = _checkpoint_json_value(
        identity_payload,
        field_path="checkpoint_identity",
    )
    if normalized_identity != expected_identity:
        raise ValueError("checkpoint_identity_mismatch")

    return {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "graph_state_schema_version": GRAPH_STATE_SCHEMA_VERSION,
        "checkpoint_identity": expected_identity,
        "checkpoint_status": CHECKPOINT_STATUS,
        "diagnostic_only": True,
        "read_only": True,
        "durable": False,
        "resumable": False,
        "persistence_performed": False,
        "completed_node_keys": list(normalized_completed),
        "next_node_key": expected_next_node,
        "state": deepcopy(normalized_state),
    }


def _operator_review_artifact_digest(
    artifact: Mapping[str, Any],
) -> str:
    if not isinstance(artifact, Mapping):
        raise ValueError("operator_review_artifact_malformed")
    return _checkpoint_digest(artifact)


def _operator_review_interrupt_evidence(
    artifact: Mapping[str, Any],
    *,
    job_id: str,
    selected_resume_id: str,
) -> Dict[str, Any]:
    if not isinstance(artifact, Mapping):
        raise ValueError("operator_review_artifact_malformed")
    if artifact.get("artifact_type") != "operator_review_tailoring_evidence":
        raise ValueError("operator_review_artifact_malformed")
    if (
        artifact.get("artifact_version")
        != OPERATOR_REVIEW_TAILORING_EVIDENCE_ARTIFACT_VERSION
    ):
        raise ValueError("operator_review_artifact_malformed")
    if (
        artifact.get("read_only") is not True
        or artifact.get("diagnostic_only") is not True
    ):
        raise ValueError("operator_review_artifact_malformed")
    if _clean_text(artifact.get("job_id")) != job_id:
        raise ValueError("operator_review_artifact_job_identity_mismatch")
    if _clean_text(artifact.get("selected_resume_id")) != selected_resume_id:
        raise ValueError("operator_review_artifact_resume_identity_mismatch")

    lane = _clean_text(artifact.get("operator_review_lane"))
    readiness = _clean_text(artifact.get("operator_review_readiness"))
    recommended_next_step = _clean_text(artifact.get("recommended_next_step"))
    human_review_required = artifact.get("human_review_required")
    raw_reason_codes = artifact.get("reason_codes")
    validation_summary = artifact.get("validation_summary")
    if (
        lane not in OPERATOR_REVIEW_LANES
        or not readiness
        or not recommended_next_step
        or not isinstance(human_review_required, bool)
        or not isinstance(raw_reason_codes, list)
        or not isinstance(validation_summary, Mapping)
    ):
        raise ValueError("operator_review_artifact_malformed")
    if not all(
        isinstance(reason_code, str) and bool(reason_code.strip())
        for reason_code in raw_reason_codes
    ):
        raise ValueError("operator_review_artifact_malformed")
    validation_status = _clean_text(
        validation_summary.get("validation_status")
    ).lower()
    if validation_status not in {"passed", "degraded", "failed"}:
        raise ValueError("operator_review_artifact_malformed")

    return {
        "operator_review_artifact_type": "operator_review_tailoring_evidence",
        "operator_review_artifact_version": (
            OPERATOR_REVIEW_TAILORING_EVIDENCE_ARTIFACT_VERSION
        ),
        "operator_review_lane": lane,
        "operator_review_readiness": readiness,
        "human_review_required": human_review_required,
        "recommended_next_step": recommended_next_step,
        "reason_codes": list(raw_reason_codes),
        "validation_status": validation_status,
    }


def _checkpoint_identity_payload_for_interrupt(
    state: Mapping[str, Any],
    checkpoint_identity: (
        EvidenceChainCheckpointIdentity | Mapping[str, Any] | None
    ),
) -> EvidenceChainCheckpointIdentityPayload:
    expected = _build_checkpoint_identity(state).to_payload()
    if checkpoint_identity is None:
        return expected
    if isinstance(checkpoint_identity, EvidenceChainCheckpointIdentity):
        supplied: Any = checkpoint_identity.to_payload()
    else:
        supplied = checkpoint_identity
    if not isinstance(supplied, Mapping):
        raise ValueError("interrupt_request_checkpoint_identity_malformed")
    if set(supplied) != set(EvidenceChainCheckpointIdentityPayload.__required_keys__):
        raise ValueError("interrupt_request_checkpoint_identity_fields_invalid")
    if supplied.get("checkpoint_schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("interrupt_request_checkpoint_schema_version_unsupported")
    if supplied.get("graph_state_schema_version") != GRAPH_STATE_SCHEMA_VERSION:
        raise ValueError("interrupt_request_graph_state_schema_version_unsupported")
    normalized = _checkpoint_json_value(
        supplied,
        field_path="checkpoint_identity",
    )
    if normalized != expected:
        raise ValueError("interrupt_request_checkpoint_identity_mismatch")
    return expected


def _build_operator_review_interrupt_request(
    state: Mapping[str, Any],
    *,
    checkpoint_identity: (
        EvidenceChainCheckpointIdentity | Mapping[str, Any] | None
    ) = None,
    requested_node_key: str = OPERATOR_REVIEW_INTERRUPT_NODE_KEY,
    safe_next_node_key: str = OPERATOR_REVIEW_INTERRUPT_SAFE_NEXT_NODE_KEY,
) -> OperatorReviewInterruptRequest:
    if not isinstance(state, Mapping):
        raise ValueError("interrupt_request_state_malformed")
    state_snapshot = _checkpoint_json_value(state, field_path="state")
    completed_node_keys = _checkpoint_completed_node_keys(state_snapshot)
    if completed_node_keys != list(ORDERED_AGENT_KEYS):
        raise ValueError("interrupt_request_completed_node_keys_invalid")
    if _clean_text(requested_node_key) != OPERATOR_REVIEW_INTERRUPT_NODE_KEY:
        raise ValueError("interrupt_request_node_key_invalid")
    if _clean_text(safe_next_node_key) != OPERATOR_REVIEW_INTERRUPT_SAFE_NEXT_NODE_KEY:
        raise ValueError("interrupt_request_safe_next_node_key_invalid")
    if "evidence_chain_bundle" in state_snapshot:
        raise ValueError("interrupt_request_state_already_finalized")
    if (
        _checkpoint_next_node_key(state_snapshot, completed_node_keys)
        != OPERATOR_REVIEW_INTERRUPT_SAFE_NEXT_NODE_KEY
    ):
        raise ValueError("interrupt_request_safe_next_node_key_invalid")

    identity = _checkpoint_identity_payload_for_interrupt(
        state_snapshot,
        checkpoint_identity,
    )
    selected_resume_id = _clean_text(identity.get("selected_resume_id"))
    if not selected_resume_id:
        raise ValueError(
            "interrupt_request_identity_missing_required_field:selected_resume_id"
        )
    artifacts = state_snapshot.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError("operator_review_artifact_missing")
    artifact = artifacts.get("operator_review_tailoring_evidence")
    if artifact is None:
        raise ValueError("operator_review_artifact_missing")
    if not isinstance(artifact, Mapping):
        raise ValueError("operator_review_artifact_malformed")
    evidence = _operator_review_interrupt_evidence(
        artifact,
        job_id=identity["job_id"],
        selected_resume_id=selected_resume_id,
    )
    artifact_digest = _operator_review_artifact_digest(artifact)
    request_seed = {
        "interrupt_request_schema_version": (
            OPERATOR_REVIEW_INTERRUPT_REQUEST_SCHEMA_VERSION
        ),
        "checkpoint_identity": identity,
        "node_key": OPERATOR_REVIEW_INTERRUPT_NODE_KEY,
        "completed_node_keys": completed_node_keys,
        "safe_next_node_key": OPERATOR_REVIEW_INTERRUPT_SAFE_NEXT_NODE_KEY,
        "operator_review_artifact_digest": artifact_digest,
    }
    interrupt_request_id = (
        "operator-review-interrupt-request:"
        + _checkpoint_digest(request_seed)
    )
    return {
        "interrupt_request_schema_version": (
            OPERATOR_REVIEW_INTERRUPT_REQUEST_SCHEMA_VERSION
        ),
        "interrupt_request_id": interrupt_request_id,
        "graph_engine": identity["graph_engine"],
        "graph_invocation_id": identity["graph_invocation_id"],
        "checkpoint_id": identity["checkpoint_id"],
        "checkpoint_schema_version": identity["checkpoint_schema_version"],
        "graph_state_schema_version": identity["graph_state_schema_version"],
        "owner_user_id": identity["owner_user_id"],
        "pipeline_run_id": identity["pipeline_run_id"],
        "context_id": identity["context_id"],
        "job_id": identity["job_id"],
        "job_index": identity["job_index"],
        "selected_resume_id": selected_resume_id,
        "node_key": OPERATOR_REVIEW_INTERRUPT_NODE_KEY,
        "completed_node_keys": list(completed_node_keys),
        "safe_next_node_key": OPERATOR_REVIEW_INTERRUPT_SAFE_NEXT_NODE_KEY,
        **evidence,
        "operator_review_artifact_digest": artifact_digest,
        "allowed_decision_values": list(
            OPERATOR_REVIEW_INTERRUPT_ALLOWED_DECISIONS
        ),
        "read_only": True,
        "diagnostic_only": True,
        "persistent": False,
        "resumable": False,
        "application_authorization": False,
        "resume_authorization": False,
    }


def _validate_operator_review_interrupt_request(
    interrupt_request: Mapping[str, Any],
    state: Mapping[str, Any],
) -> OperatorReviewInterruptRequest:
    if not isinstance(interrupt_request, Mapping):
        raise ValueError("interrupt_request_malformed")
    expected_fields = set(OperatorReviewInterruptRequest.__required_keys__)
    if set(interrupt_request) != expected_fields:
        raise ValueError("interrupt_request_fields_invalid")
    if (
        interrupt_request.get("interrupt_request_schema_version")
        != OPERATOR_REVIEW_INTERRUPT_REQUEST_SCHEMA_VERSION
    ):
        raise ValueError("interrupt_request_schema_version_unsupported")
    if interrupt_request.get("checkpoint_schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("interrupt_request_checkpoint_schema_version_unsupported")
    if (
        interrupt_request.get("graph_state_schema_version")
        != GRAPH_STATE_SCHEMA_VERSION
    ):
        raise ValueError("interrupt_request_graph_state_schema_version_unsupported")
    if (
        interrupt_request.get("allowed_decision_values")
        != list(OPERATOR_REVIEW_INTERRUPT_ALLOWED_DECISIONS)
    ):
        raise ValueError("interrupt_request_allowed_decision_values_invalid")
    if (
        interrupt_request.get("read_only") is not True
        or interrupt_request.get("diagnostic_only") is not True
        or interrupt_request.get("persistent") is not False
        or interrupt_request.get("resumable") is not False
        or interrupt_request.get("application_authorization") is not False
        or interrupt_request.get("resume_authorization") is not False
    ):
        raise ValueError("interrupt_request_safety_declarations_invalid")
    job_index = interrupt_request.get("job_index")
    if isinstance(job_index, bool) or not isinstance(job_index, int):
        raise ValueError("interrupt_request_job_index_invalid")
    if not isinstance(interrupt_request.get("human_review_required"), bool):
        raise ValueError("interrupt_request_operator_review_evidence_invalid")

    normalized = _checkpoint_json_value(
        interrupt_request,
        field_path="interrupt_request",
    )
    expected = _build_operator_review_interrupt_request(state)
    if normalized != expected:
        raise ValueError("interrupt_request_mismatch")
    return deepcopy(expected)


def _state_with_artifact(
    state: EvidenceChainGraphState,
    *,
    agent_key: str,
    artifact_key: str,
    artifact: Dict[str, Any],
) -> EvidenceChainGraphState:
    next_state = _copy_state_for_transition(state)
    artifacts = next_state["artifacts"]
    artifacts[artifact_key] = artifact
    next_state["ordered_node_keys"] = [
        *next_state["ordered_node_keys"],
        agent_key,
    ]
    next_state["node_statuses"] = [
        *next_state["node_statuses"],
        _node_summary(agent_key, artifact),
    ]
    return next_state


def _jd_intelligence_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifact = describe_existing_job_intelligence_result(dict(state.get("job") or {}))
    return _state_with_artifact(
        state,
        agent_key="jd_intelligence",
        artifact_key="jd_intelligence",
        artifact=artifact,
    )


def _resume_match_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    identity = dict(state.get("job_identity") or {})
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_resume_match_jd_evidence_artifact(
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        resume_variants=list(state.get("resume_rows") or []),
        selected_resume_id=_clean_text(state.get("selected_resume_id")),
        job_id=_clean_text(identity.get("job_id")),
        title=_clean_text(identity.get("title")),
        company=_clean_text(identity.get("company")),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="resume_match",
        artifact_key="resume_match_jd_evidence",
        artifact=artifact,
    )


def _critic_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="critic",
        artifact_key="critic_resume_match_jd_evidence",
        artifact=artifact,
    )


def _job_prioritization_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="job_prioritization",
        artifact_key="job_prioritization_critic_evidence",
        artifact=artifact,
    )


def _tailoring_decision_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=dict(
            artifacts.get("job_prioritization_critic_evidence") or {}
        ),
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="tailoring_decision",
        artifact_key="tailoring_decision_priority_evidence",
        artifact=artifact,
    )


def _operator_review_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_operator_review_tailoring_evidence_artifact(
        tailoring_decision_priority_evidence=dict(
            artifacts.get("tailoring_decision_priority_evidence") or {}
        ),
        job_prioritization_critic_evidence=dict(
            artifacts.get("job_prioritization_critic_evidence") or {}
        ),
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="operator_review",
        artifact_key="operator_review_tailoring_evidence",
        artifact=artifact,
    )


def _finalize_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    identity = dict(state.get("job_identity") or {})
    chain_id = ":".join(
        part
        for part in (
            _clean_text(state.get("pipeline_run_id")),
            _clean_text(identity.get("job_id")),
            "langgraph-evidence-chain",
        )
        if part
    )
    bundle = build_agent_evidence_chain_bundle(
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        job_prioritization_critic_evidence=dict(
            artifacts.get("job_prioritization_critic_evidence") or {}
        ),
        tailoring_decision_priority_evidence=dict(
            artifacts.get("tailoring_decision_priority_evidence") or {}
        ),
        operator_review_tailoring_evidence=dict(
            artifacts.get("operator_review_tailoring_evidence") or {}
        ),
        enabled=True,
        chain_id=chain_id,
        pipeline_run_id=_clean_text(state.get("pipeline_run_id")),
        owner_user_id=_clean_text(state.get("owner_user_id")),
        context_id=_clean_text(state.get("context_id")),
    )
    next_state = _copy_state_for_transition(state)
    artifacts = next_state["artifacts"]
    artifacts["agent_evidence_chain_bundle"] = bundle
    next_state["evidence_chain_bundle"] = bundle
    if bool(state.get("include_trace_payload")):
        trace_payload = build_agent_evidence_chain_trace_payload(bundle, enabled=True)
        artifacts["agent_evidence_chain_trace_payload"] = trace_payload
        next_state["trace_payload"] = trace_payload
    next_state["artifacts"] = artifacts
    return next_state


def _compile_graph() -> Any:
    from langgraph.graph import END, StateGraph

    graph = StateGraph(EvidenceChainGraphState)
    graph.add_node("jd_intelligence", _jd_intelligence_node)
    graph.add_node("resume_match", _resume_match_node)
    graph.add_node("critic", _critic_node)
    graph.add_node("job_prioritization", _job_prioritization_node)
    graph.add_node("tailoring_decision", _tailoring_decision_node)
    graph.add_node("operator_review", _operator_review_node)
    graph.add_node("finalize", _finalize_node)
    graph.set_entry_point("jd_intelligence")
    graph.add_edge("jd_intelligence", "resume_match")
    graph.add_edge("resume_match", "critic")
    graph.add_edge("critic", "job_prioritization")
    graph.add_edge("job_prioritization", "tailoring_decision")
    graph.add_edge("tailoring_decision", "operator_review")
    graph.add_edge("operator_review", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def _execute_graph_state(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    compiled_graph = _compile_graph()
    return compiled_graph.invoke(state)


def _per_job_result_from_state(state: EvidenceChainGraphState) -> Dict[str, Any]:
    identity = dict(state.get("job_identity") or {})
    artifacts = dict(state.get("artifacts") or {})
    reason_codes = _reason_codes_from_artifacts(artifacts)
    ordered_node_keys = list(state.get("ordered_node_keys") or [])
    node_statuses = list(state.get("node_statuses") or [])
    return {
        **identity,
        "status": "degraded" if reason_codes else "succeeded",
        "reason_codes": reason_codes,
        "graph_runtime": "langgraph",
        "ordered_node_keys": ordered_node_keys,
        "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
        "node_statuses": node_statuses,
        "artifacts": artifacts,
        "evidence_chain_bundle": artifacts.get("agent_evidence_chain_bundle", {}),
        "trace_payload": artifacts.get("agent_evidence_chain_trace_payload", {}),
        "safety_metadata": _safety_metadata(
            automatic_internal_decisioning_performed=True
        ),
    }


def _base_result(
    *,
    enabled: bool,
    jobs_received_count: int,
    jobs_sampled_count: int,
    sample_limit: int,
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    include_trace_payload: bool,
    attempted: bool,
    executed: bool,
    reason: str,
    per_job_results: List[Dict[str, Any]] | None = None,
    warnings: List[str] | None = None,
) -> Dict[str, Any]:
    per_job_results = list(per_job_results or [])
    succeeded_count = sum(
        1 for result in per_job_results if result.get("status") in {"succeeded", "degraded"}
    )
    failed_count = sum(1 for result in per_job_results if result.get("status") == "failed")
    safety_metadata = _safety_metadata(
        automatic_internal_decisioning_performed=succeeded_count > 0
    )
    return {
        "artifact_type": "langgraph_evidence_chain_execution",
        "artifact_version": LANGGRAPH_EVIDENCE_CHAIN_VERSION,
        "gate_name": LANGGRAPH_EVIDENCE_CHAIN_GATE_NAME,
        "enabled": bool(enabled),
        "execution_gate_enabled": bool(enabled),
        "graph_runtime": "langgraph",
        "default_off": True,
        "explicit_call_only": True,
        "read_only": True,
        "diagnostic_only": True,
        "attempted": bool(attempted),
        "executed": bool(executed),
        "reason": reason,
        "job_count": jobs_received_count,
        "jobs_received_count": jobs_received_count,
        "jobs_sampled_count": jobs_sampled_count,
        "processed_count": len(per_job_results),
        "jobs_executed_count": len(per_job_results),
        "jobs_succeeded_count": succeeded_count,
        "jobs_failed_count": failed_count,
        "sample_limit": sample_limit,
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
        "include_trace_payload": bool(include_trace_payload),
        "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
        "per_job_results": per_job_results,
        "warnings": list(warnings or []),
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }


def execute_langgraph_evidence_chain(
    jobs: Any,
    *,
    pipeline_run_id: str | None = None,
    owner_user_id: str | None = None,
    context_id: str | None = None,
    resume_context: Any = None,
    sample_limit: Any = DEFAULT_SAMPLE_LIMIT,
    include_trace_payload: bool = True,
    enabled: bool = False,
    strict: bool = False,
) -> Dict[str, Any]:
    """Run the existing evidence chain through an explicit default-off LangGraph harness."""

    normalized_jobs = _jobs_list(jobs)
    safe_sample_limit = _safe_sample_limit(sample_limit)
    sampled_jobs = normalized_jobs[:safe_sample_limit]
    pipeline_run = _clean_text(pipeline_run_id)
    owner_user = _clean_text(owner_user_id)
    context = _clean_text(context_id)

    if not enabled:
        return _base_result(
            enabled=False,
            jobs_received_count=len(normalized_jobs),
            jobs_sampled_count=0,
            sample_limit=safe_sample_limit,
            pipeline_run_id=pipeline_run,
            owner_user_id=owner_user,
            context_id=context,
            include_trace_payload=include_trace_payload,
            attempted=False,
            executed=False,
            reason="langgraph_evidence_chain_disabled",
        )

    if not sampled_jobs:
        return _base_result(
            enabled=True,
            jobs_received_count=len(normalized_jobs),
            jobs_sampled_count=0,
            sample_limit=safe_sample_limit,
            pipeline_run_id=pipeline_run,
            owner_user_id=owner_user,
            context_id=context,
            include_trace_payload=include_trace_payload,
            attempted=True,
            executed=False,
            reason="no_jobs_sampled",
        )

    resume_rows, selected_resume_id = _resume_rows_and_selection(resume_context)
    per_job_results: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for index, job in enumerate(sampled_jobs):
        identity = _job_identity(job, index)
        initial_state = _build_initial_graph_state(
            job=job,
            job_index=index,
            job_identity=identity,
            resume_rows=resume_rows,
            selected_resume_id=selected_resume_id,
            pipeline_run_id=pipeline_run,
            owner_user_id=owner_user,
            context_id=context,
            include_trace_payload=include_trace_payload,
        )
        try:
            final_state = _execute_graph_state(initial_state)
            per_job_results.append(_per_job_result_from_state(final_state))
        except Exception as exc:
            if strict:
                raise
            warnings.append("langgraph_evidence_chain_job_failed")
            per_job_results.append(
                {
                    **identity,
                    "status": "failed",
                    "reason_codes": ["langgraph_evidence_chain_job_failed"],
                    "graph_runtime": "langgraph",
                    "ordered_node_keys": [],
                    "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
                    "node_statuses": [],
                    "artifacts": {},
                    "error_message": str(exc),
                    "safety_metadata": _safety_metadata(
                        automatic_internal_decisioning_performed=False
                    ),
                }
            )

    failed_count = sum(1 for result in per_job_results if result.get("status") == "failed")
    reason = (
        "langgraph_evidence_chain_completed_with_failures"
        if failed_count
        else "langgraph_evidence_chain_completed"
    )
    return _base_result(
        enabled=True,
        jobs_received_count=len(normalized_jobs),
        jobs_sampled_count=len(sampled_jobs),
        sample_limit=safe_sample_limit,
        pipeline_run_id=pipeline_run,
        owner_user_id=owner_user,
        context_id=context,
        include_trace_payload=include_trace_payload,
        attempted=True,
        executed=True,
        reason=reason,
        per_job_results=per_job_results,
        warnings=warnings,
    )

"""Read-only projection of completed planning artifacts for production shadow."""

from __future__ import annotations

import csv
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import stat
from typing import Any, Dict, Mapping, Sequence


PRODUCTION_SHADOW_ADAPTER_VERSION = "production-shadow-artifact-adapter-v1"
MAX_ARTIFACT_BYTES = 4_000_000
ARTIFACT_FILENAMES = {
    "job_corpus": "",
    "best_resume": "best_resume_variant_by_job.csv",
    "execution_queue": "application_execution_queue.csv",
    "packet_manifest": "job_packet_manifest.csv",
    "advisory_priority": "job_prioritization_recommendations.csv",
    "tailoring_decision": "tailoring_decision_recommendations.csv",
    "operator_review": "operator_review_recommendations.csv",
}
_IDENTITY = re.compile(r"[A-Za-z0-9_.:@/-]{1,200}")
_PROVIDER_FIELDS = (
    "llm_provider",
    "llm_model",
    "llm_adjudication_provider",
    "llm_adjudication_model",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cost_usd",
)


class ProductionShadowAdapterError(ValueError):
    """Bounded fail-closed artifact projection error."""


def _fail(code: str) -> None:
    raise ProductionShadowAdapterError(code)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _identity(value: Any, code: str) -> str:
    text = _text(value)
    if not _IDENTITY.fullmatch(text):
        _fail(code)
    return text


def _safe_regular_path(value: str | Path, label: str) -> Path:
    raw = Path(value)
    if ".." in raw.parts:
        _fail("artifact_path_traversal")
    absolute = raw.absolute()
    try:
        resolved = raw.resolve(strict=True)
        details = resolved.stat()
    except (OSError, RuntimeError):
        _fail("artifact_missing")
    if absolute != resolved or raw.is_symlink() or not stat.S_ISREG(details.st_mode):
        _fail("artifact_path_unsafe")
    if details.st_size <= 0 or details.st_size > MAX_ARTIFACT_BYTES:
        _fail("artifact_size_invalid")
    return resolved


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                value.update(chunk)
    except OSError:
        _fail("artifact_read_failed")
    return value.hexdigest()


def artifact_digests(
    artifact_paths: Mapping[str, str | Path],
) -> Dict[str, str]:
    return {
        name: _digest(_safe_regular_path(path, name))
        for name, path in sorted(artifact_paths.items())
    }


def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    _fail("artifact_malformed")
                rows.append(dict(value))
    except ProductionShadowAdapterError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError):
        _fail("artifact_malformed")
    if not rows:
        _fail("artifact_malformed")
    return rows


def _read_csv(path: Path) -> list[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                _fail("artifact_malformed")
            rows = [dict(row) for row in reader]
    except ProductionShadowAdapterError:
        raise
    except (OSError, UnicodeError, csv.Error):
        _fail("artifact_malformed")
    if not rows:
        _fail("artifact_malformed")
    return rows


def _job_id(row: Mapping[str, Any]) -> str:
    return _text(row.get("doc_id") or row.get("job_doc_id") or row.get("job_id"))


def _unique_rows(
    rows: Sequence[Mapping[str, Any]], label: str
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    versions: set[str] = set()
    for row in rows:
        identity = _job_id(row)
        if not identity or not _IDENTITY.fullmatch(identity):
            _fail("artifact_required_field_missing")
        if identity in result:
            _fail("duplicate_job_identity")
        result[identity] = deepcopy(dict(row))
        version = _text(row.get("schema_version"))
        if version:
            versions.add(version)
    if len(versions) > 1:
        _fail("artifact_schema_conflict")
    return result


def _required(row: Mapping[str, Any], field: str) -> str:
    value = _text(row.get(field))
    if not value:
        _fail("artifact_required_field_missing")
    return value


def _reason_codes(value: Any) -> list[str]:
    if isinstance(value, list):
        candidates = value
    else:
        candidates = re.split(r"[,|;]", _text(value))
    result: list[str] = []
    for candidate in candidates:
        code = _text(candidate).lower().replace(" ", "_")
        if code and re.fullmatch(r"[a-z0-9_.-]{1,120}", code):
            if code not in result:
                result.append(code)
    return result[:25]


def _provider_metadata(*rows: Mapping[str, Any]) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    for field in _PROVIDER_FIELDS:
        values = [_text(row.get(field)) for row in rows if _text(row.get(field))]
        if not values:
            continue
        if len(set(values)) != 1:
            _fail("provider_metadata_conflict")
        value: Any = values[0][:200]
        if field.endswith("_tokens"):
            try:
                value = max(0, min(int(values[0]), 10_000_000))
            except ValueError:
                _fail("provider_metadata_invalid")
        elif field == "cost_usd":
            try:
                value = max(0.0, min(float(values[0]), 1_000_000.0))
            except ValueError:
                _fail("provider_metadata_invalid")
        metadata[field] = value
    return metadata


def _optional_bool(row: Mapping[str, Any], field: str) -> bool | None:
    raw = _text(row.get(field)).lower()
    if not raw:
        return None
    if raw in {"1", "true", "yes", "y"}:
        return True
    if raw in {"0", "false", "no", "n"}:
        return False
    _fail("authoritative_boolean_invalid")


def _project_one_job(
    *,
    job_id: str,
    indexed: Mapping[str, Mapping[str, Mapping[str, Any]]],
    corpus_order: Sequence[str],
    owner: str,
    run: str,
    context: str,
    digests: Mapping[str, str],
    artifact_identities: Mapping[str, Mapping[str, str]],
) -> Dict[str, Any]:
    if any(job_id not in rows for rows in indexed.values()):
        _fail("partial_artifact_set")
    best = indexed["best_resume"][job_id]
    queue = indexed["execution_queue"][job_id]
    packet = indexed["packet_manifest"][job_id]
    priority = indexed["advisory_priority"][job_id]
    tailoring = indexed["tailoring_decision"][job_id]
    operator = indexed["operator_review"][job_id]

    best_resume = _identity(
        _required(best, "winner_resume"), "selected_resume_identity_invalid"
    )
    packet_resume = _identity(
        _required(packet, "packet_resume"), "selected_resume_identity_invalid"
    )
    queue_winner = _identity(
        _text(queue.get("resolved_resume") or queue.get("winner_resume")),
        "selected_resume_identity_invalid",
    )
    if best_resume != _text(queue.get("winner_resume") or best_resume):
        _fail("selected_resume_conflict")
    if packet_resume != queue_winner:
        _fail("selected_resume_conflict")
    for row in (tailoring, operator):
        row_resume = _text(row.get("resolved_resume") or row.get("winner_resume"))
        if row_resume and row_resume != packet_resume:
            _fail("selected_resume_conflict")

    queue_rank: int | None = None
    if _text(queue.get("queue_rank")):
        try:
            queue_rank = int(_text(queue.get("queue_rank")))
        except ValueError:
            _fail("queue_rank_invalid")
        if queue_rank < 0:
            _fail("queue_rank_invalid")
    queue_action = _text(queue.get("action"))
    advisory_priority = _text(priority.get("advisory_priority"))
    advisory_reasons = _reason_codes(priority.get("advisory_reason_codes"))
    tailoring_decision = _text(tailoring.get("tailoring_decision"))
    tailoring_reasons = _reason_codes(
        tailoring.get("tailoring_reason_codes")
    )
    operator_lane = _text(operator.get("operator_review_lane"))
    packet_allowed = _optional_bool(operator, "packet_generation_allowed")
    manual_review = _optional_bool(queue, "requires_manual_review")

    authoritative_facts: Dict[str, Any] = {
        "job_id": job_id,
        "selected_resume_id": queue_winner,
        "packet_resume": packet_resume,
    }
    for field, value in (
        ("queue_rank", queue_rank),
        ("action", queue_action),
        ("advisory_priority", advisory_priority),
        ("tailoring_decision", tailoring_decision),
        ("operator_review_lane", operator_lane),
        ("packet_generation_allowed", packet_allowed),
        ("requires_manual_review", manual_review),
    ):
        if value is not None and value != "":
            authoritative_facts[field] = value
    if advisory_reasons:
        authoritative_facts["advisory_reason_codes"] = advisory_reasons
    if tailoring_reasons:
        authoritative_facts["tailoring_reason_codes"] = tailoring_reasons

    seed = {
        "version": PRODUCTION_SHADOW_ADAPTER_VERSION,
        "owner_user_id": owner,
        "pipeline_run_id": run,
        "context_id": context,
        "job_id": job_id,
        "job_index": corpus_order.index(job_id),
        "selected_resume_id": packet_resume,
        "artifact_digests": dict(digests),
    }
    invocation = hashlib.sha256(
        json.dumps(seed, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    queue_facts: Dict[str, Any] = {}
    if queue_rank is not None:
        queue_facts["queue_rank"] = queue_rank
    if queue_action:
        queue_facts["queue_action"] = queue_action[:80]
    if advisory_priority:
        queue_facts["advisory_priority"] = advisory_priority[:80]
    if advisory_reasons:
        queue_facts["advisory_reason_codes"] = advisory_reasons
    if manual_review is not None:
        queue_facts["requires_manual_review"] = manual_review
    tailoring_facts: Dict[str, Any] = {}
    if tailoring_decision:
        tailoring_facts["tailoring_decision"] = tailoring_decision[:80]
    if tailoring_reasons:
        tailoring_facts["tailoring_reason_codes"] = tailoring_reasons
    operator_facts: Dict[str, Any] = {
        "operator_decision_consumed": False
    }
    if operator_lane:
        operator_facts["operator_review_lane"] = operator_lane[:80]
    if packet_allowed is not None:
        operator_facts["packet_generation_allowed"] = packet_allowed
    operator_reasons = _reason_codes(
        operator.get("operator_review_reason_codes")
    )
    if operator_reasons:
        operator_facts["operator_review_reason_codes"] = operator_reasons
    owner_input_facts = {
        "job_id": job_id,
        "company": _text(queue.get("job_company") or queue.get("company")),
        "title": _text(queue.get("job_title") or queue.get("title")),
        "action": queue_action,
        "deterministic_winner_score": _text(
            queue.get("deterministic_winner_score")
            or queue.get("selector_winner_score")
            or queue.get("winner_score")
            or queue.get("resolved_score")
        ),
        "deterministic_winner_available": _text(
            queue.get("deterministic_winner_available")
        ),
        "fallback_only_no_deterministic_match": _text(
            queue.get("fallback_only_no_deterministic_match")
        ),
        "packet_generation_allowed": _text(
            queue.get("packet_generation_allowed")
        ),
        "packet_generation_block_reason": _text(
            queue.get("packet_generation_block_reason")
        ),
    }
    for field in ("source_recommendation", "critic_decision"):
        value = _text(queue.get(field))
        if value:
            owner_input_facts[field] = value
    owner_authoritative_facts: Dict[str, Any] = {
        "job_id": job_id,
    }
    for field in ("advisory_priority", "existing_action"):
        value = _text(priority.get(field))
        if value:
            owner_authoritative_facts[field] = value
    if advisory_reasons:
        owner_authoritative_facts[
            "advisory_reason_codes"
        ] = advisory_reasons
    priority_packet_allowed = _optional_bool(
        priority, "packet_generation_allowed"
    )
    if priority_packet_allowed is not None:
        owner_authoritative_facts[
            "packet_generation_allowed"
        ] = priority_packet_allowed
    return {
        **seed,
        "graph_invocation_id": f"production-shadow:{invocation}",
        "authoritative_artifacts": deepcopy(dict(artifact_identities)),
        "authoritative_parity_facts": deepcopy(authoritative_facts),
        "deterministic_owner_input_facts": owner_input_facts,
        "deterministic_owner_authoritative_facts": (
            owner_authoritative_facts
        ),
        "identity_facts": {"job_id": job_id},
        "resume_selection_facts": {
            "selected_resume_id": packet_resume,
            "packet_resume": packet_resume,
        },
        "queue_priority_facts": queue_facts,
        "tailoring_decision_facts": tailoring_facts,
        "operator_review_facts": operator_facts,
        "provider_metadata": _provider_metadata(
            queue, packet, priority, tailoring, operator
        ),
    }


def project_completed_authoritative_artifacts(
    *,
    job_ids: Sequence[str],
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
    artifact_paths: Mapping[str, str | Path],
) -> Dict[str, Any]:
    """Project bounded, detached facts without invoking a production owner."""

    owner = _identity(owner_user_id, "owner_identity_invalid")
    run = _identity(pipeline_run_id, "pipeline_identity_invalid")
    context = _identity(context_id, "context_identity_invalid")
    requested = [_identity(item, "job_identity_invalid") for item in job_ids]
    if not requested:
        _fail("job_identity_missing")
    if len(requested) != len(set(requested)):
        _fail("duplicate_job_identity")
    if set(artifact_paths) != set(ARTIFACT_FILENAMES):
        _fail("artifact_set_incomplete")

    safe_paths = {
        name: _safe_regular_path(path, name)
        for name, path in artifact_paths.items()
    }
    digests = {name: _digest(path) for name, path in sorted(safe_paths.items())}
    rows_by_name: Dict[str, list[Dict[str, Any]]] = {}
    for name, path in safe_paths.items():
        rows_by_name[name] = (
            _read_jsonl(path) if name == "job_corpus" else _read_csv(path)
        )
    indexed = {
        name: _unique_rows(rows, name) for name, rows in rows_by_name.items()
    }
    corpus_order = [_job_id(row) for row in rows_by_name["job_corpus"]]
    artifact_identities = {
        name: {"artifact_name": name, "sha256": digest}
        for name, digest in digests.items()
    }
    projections: list[Dict[str, Any]] = []
    rejections: list[Dict[str, Any]] = []
    for request_index, job_id in enumerate(requested):
        try:
            projection = _project_one_job(
                job_id=job_id,
                indexed=indexed,
                corpus_order=corpus_order,
                owner=owner,
                run=run,
                context=context,
                digests=digests,
                artifact_identities=artifact_identities,
            )
        except ProductionShadowAdapterError as exc:
            rejections.append(
                {
                    "request_index": request_index,
                    "job_id": job_id,
                    "status": "input_rejected",
                    "failure_classification": str(exc)[:120],
                }
            )
            continue
        projection["request_index"] = request_index
        projections.append(projection)
    if not projections and rejections:
        _fail(rejections[0]["failure_classification"])
    return {
        "adapter_version": PRODUCTION_SHADOW_ADAPTER_VERSION,
        "artifact_digests": digests,
        "projections": deepcopy(projections),
        "rejections": deepcopy(rejections),
    }

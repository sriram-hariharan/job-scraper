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
    for job_id in requested:
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
        queue_winner = _text(queue.get("resolved_resume") or queue.get("winner_resume"))
        queue_winner = _identity(
            queue_winner, "selected_resume_identity_invalid"
        )
        if best_resume != _text(queue.get("winner_resume") or best_resume):
            _fail("selected_resume_conflict")
        if packet_resume != queue_winner:
            _fail("selected_resume_conflict")
        for row in (tailoring, operator):
            row_resume = _text(row.get("resolved_resume") or row.get("winner_resume"))
            if row_resume and row_resume != packet_resume:
                _fail("selected_resume_conflict")

        try:
            queue_rank = int(_required(queue, "queue_rank"))
        except ValueError:
            _fail("queue_rank_invalid")
        if queue_rank < 0:
            _fail("queue_rank_invalid")
        queue_action = _required(queue, "action")
        advisory_priority = _required(priority, "advisory_priority")
        tailoring_decision = _required(tailoring, "tailoring_decision")
        operator_lane = _required(operator, "operator_review_lane")
        seed = {
            "version": PRODUCTION_SHADOW_ADAPTER_VERSION,
            "owner_user_id": owner,
            "pipeline_run_id": run,
            "context_id": context,
            "job_id": job_id,
            "job_index": corpus_order.index(job_id),
            "selected_resume_id": packet_resume,
            "artifact_digests": digests,
        }
        invocation = hashlib.sha256(
            json.dumps(seed, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        projections.append(
            {
                **seed,
                "graph_invocation_id": f"production-shadow:{invocation}",
                "authoritative_artifacts": deepcopy(artifact_identities),
                "identity_facts": {"job_id": job_id},
                "resume_selection_facts": {
                    "selected_resume_id": packet_resume,
                },
                "queue_priority_facts": {
                    "queue_rank": queue_rank,
                    "queue_action": queue_action[:80],
                    "advisory_priority": advisory_priority[:80],
                    "advisory_reason_codes": _reason_codes(
                        priority.get("advisory_reason_codes")
                    ),
                },
                "tailoring_decision_facts": {
                    "tailoring_decision": tailoring_decision[:80],
                    "tailoring_reason_codes": _reason_codes(
                        tailoring.get("tailoring_reason_codes")
                    ),
                },
                "operator_review_facts": {
                    "operator_review_lane": operator_lane[:80],
                    "operator_review_reason_codes": _reason_codes(
                        operator.get("operator_review_reason_codes")
                    ),
                    "operator_decision_consumed": False,
                },
                "provider_metadata": _provider_metadata(
                    queue, packet, priority, tailoring, operator
                ),
            }
        )
    return {
        "adapter_version": PRODUCTION_SHADOW_ADAPTER_VERSION,
        "artifact_digests": digests,
        "projections": deepcopy(projections),
    }

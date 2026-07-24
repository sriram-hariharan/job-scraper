"""Bounded, sanitized resume-evidence projection for explicit shadow handoff."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence


PROJECTION_CONTRACT_VERSION = "applylens-shadow-resume-evidence-v1"
MAX_SELECTED_RESUMES = 50
MAX_EVIDENCE_ROWS_PER_RESUME = 20
MAX_SERIALIZED_BYTES = 1_000_000
MAX_IDENTITY_LENGTH = 200
MAX_STRING_LENGTH = 500
MAX_LIST_ITEMS = 50
MAX_NESTED_DEPTH = 5

_IDENTITY_PATTERN = re.compile(r"[A-Za-z0-9_.:@/-]{1,200}")
_TOP_LEVEL_FIELDS = {"contract_version", "resumes"}
_RESUME_ENTRY_FIELDS = {"resume_id", "evidence_rows"}
_EVIDENCE_FIELDS = {
    "resume_id",
    "resume_name",
    "titles",
    "skills",
    "tools",
    "methods",
    "workflows",
    "business_contexts",
    "stakeholder_contexts",
    "ownership_signals",
    "domain_signals",
    "analytics_ml_signals",
    "tooling_signals",
    "quantified_bullets",
    "bullets",
    "source_bullet_ids",
}
_SENSITIVE_FIELDS = {
    "raw_text",
    "normalized_text",
    "name",
    "owner_name",
    "email",
    "phone",
    "postal_address",
    "address",
    "contact",
    "contact_header",
    "metadata",
    "path",
    "file_path",
    "embedding",
    "embeddings",
    "prompt",
    "response",
    "database_url",
    "credential",
    "credentials",
}


class ProjectionError(ValueError):
    """Bounded projection failure whose message is a stable non-sensitive code."""


def _fail(code: str) -> None:
    raise ProjectionError(code)


def _identity(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        _fail("blank_resume_identity")
    if len(text) > MAX_IDENTITY_LENGTH or not _IDENTITY_PATTERN.fullmatch(text):
        _fail("projection_malformed")
    return text


def _bounded_text(value: Any) -> str:
    if not isinstance(value, str):
        _fail("projection_malformed")
    return " ".join(value.split()).strip()[:MAX_STRING_LENGTH]


def _bounded_list(values: Any) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, (list, tuple)):
        _fail("projection_malformed")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _bounded_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if len(result) >= MAX_LIST_ITEMS:
            break
    return result


def _resume_bullet_evidence(resume_evidence: Any) -> tuple[list[str], list[str]]:
    bullets: list[str] = []
    bullet_ids: list[str] = []
    seen_bullets: set[str] = set()
    for collection_name in ("experience_entries", "project_entries"):
        entries = getattr(resume_evidence, collection_name, None)
        if entries is None:
            continue
        if not isinstance(entries, (list, tuple)):
            _fail("projection_malformed")
        for entry in entries:
            entry_bullets = getattr(entry, "bullets", None)
            entry_bullet_ids = getattr(entry, "bullet_ids", None)
            if not isinstance(entry_bullets, (list, tuple)):
                _fail("projection_malformed")
            if entry_bullet_ids is None:
                entry_bullet_ids = []
            if not isinstance(entry_bullet_ids, (list, tuple)):
                _fail("projection_malformed")
            for index, raw_bullet in enumerate(entry_bullets):
                bullet = _bounded_text(raw_bullet)
                if not bullet or bullet in seen_bullets:
                    continue
                seen_bullets.add(bullet)
                bullets.append(bullet)
                if index < len(entry_bullet_ids):
                    bullet_id = _bounded_text(entry_bullet_ids[index])
                    if bullet_id:
                        bullet_ids.append(bullet_id)
                if len(bullets) >= MAX_LIST_ITEMS:
                    return bullets, bullet_ids
    return bullets, bullet_ids


def _candidate_row(resume_evidence: Any, resume_identity: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "resume_id": resume_identity,
        "resume_name": resume_identity,
    }
    for field_name in (
        "titles",
        "skills",
        "tools",
        "methods",
        "workflows",
        "business_contexts",
        "stakeholder_contexts",
        "ownership_signals",
        "domain_signals",
        "analytics_ml_signals",
        "tooling_signals",
        "quantified_bullets",
    ):
        values = _bounded_list(getattr(resume_evidence, field_name, []))
        if values:
            row[field_name] = values
    bullets, bullet_ids = _resume_bullet_evidence(resume_evidence)
    if bullets:
        row["bullets"] = bullets
    if bullet_ids:
        row["source_bullet_ids"] = bullet_ids
    return row


def _serialized_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        encoded = (
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        _fail("projection_malformed")
    if len(encoded) > MAX_SERIALIZED_BYTES:
        _fail("projection_limit_exceeded")
    return encoded


def _reject_sensitive_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).strip().lower() in _SENSITIVE_FIELDS:
                _fail("projection_sensitive_field_rejected")
            _reject_sensitive_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_sensitive_fields(nested)


def _validate_depth(value: Any, depth: int = 0) -> None:
    if isinstance(value, Mapping):
        if depth > MAX_NESTED_DEPTH:
            _fail("projection_malformed")
        for nested in value.values():
            _validate_depth(nested, depth + 1)
    elif isinstance(value, list):
        if depth > MAX_NESTED_DEPTH:
            _fail("projection_malformed")
        for nested in value:
            _validate_depth(nested, depth + 1)


def validate_projection(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != _TOP_LEVEL_FIELDS:
        _fail("projection_malformed")
    if payload.get("contract_version") != PROJECTION_CONTRACT_VERSION:
        _fail("projection_malformed")
    resumes = payload.get("resumes")
    if not isinstance(resumes, list) or not resumes:
        _fail("selected_resume_evidence_missing")
    if len(resumes) > MAX_SELECTED_RESUMES:
        _fail("projection_limit_exceeded")

    _reject_sensitive_fields(payload)
    _validate_depth(payload)
    normalized_entries: list[dict[str, Any]] = []
    identities: set[str] = set()
    for entry in resumes:
        if not isinstance(entry, Mapping) or set(entry) != _RESUME_ENTRY_FIELDS:
            _fail("projection_malformed")
        resume_id = _identity(entry.get("resume_id"))
        if resume_id in identities:
            _fail("duplicate_resume_identity")
        identities.add(resume_id)
        evidence_rows = entry.get("evidence_rows")
        if (
            not isinstance(evidence_rows, list)
            or not evidence_rows
            or len(evidence_rows) > MAX_EVIDENCE_ROWS_PER_RESUME
        ):
            _fail("projection_limit_exceeded")
        normalized_rows: list[dict[str, Any]] = []
        for row in evidence_rows:
            if not isinstance(row, Mapping) or not set(row).issubset(_EVIDENCE_FIELDS):
                _fail("projection_malformed")
            if set(row).intersection(_SENSITIVE_FIELDS):
                _fail("projection_sensitive_field_rejected")
            if _identity(row.get("resume_id") or row.get("resume_name")) != resume_id:
                _fail("projection_malformed")
            normalized_row: dict[str, Any] = {}
            for key, raw_value in row.items():
                if key in {"resume_id", "resume_name"}:
                    value = _identity(raw_value)
                    if value != resume_id:
                        _fail("projection_malformed")
                    normalized_row[key] = value
                else:
                    normalized_row[key] = _bounded_list(raw_value)
            normalized_rows.append(normalized_row)
        normalized_entries.append(
            {"resume_id": resume_id, "evidence_rows": normalized_rows}
        )

    normalized = {
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "resumes": sorted(normalized_entries, key=lambda item: item["resume_id"]),
    }
    _serialized_bytes(normalized)
    return normalized


def build_candidate_projection(
    resume_evidence_objects: Sequence[Any],
) -> dict[str, Any]:
    if not isinstance(resume_evidence_objects, (list, tuple)):
        _fail("projection_malformed")
    if not resume_evidence_objects:
        _fail("selected_resume_evidence_missing")
    if len(resume_evidence_objects) > MAX_SELECTED_RESUMES:
        _fail("projection_limit_exceeded")

    entries: list[dict[str, Any]] = []
    identities: set[str] = set()
    for resume_evidence in resume_evidence_objects:
        document = getattr(resume_evidence, "document", None)
        resume_id = _identity(getattr(document, "resume_name", ""))
        if resume_id in identities:
            _fail("duplicate_resume_identity")
        identities.add(resume_id)
        entries.append(
            {
                "resume_id": resume_id,
                "evidence_rows": [_candidate_row(resume_evidence, resume_id)],
            }
        )
    return validate_projection(
        {
            "contract_version": PROJECTION_CONTRACT_VERSION,
            "resumes": entries,
        }
    )


def filter_projection_by_packet_manifest(
    candidate_projection: Mapping[str, Any],
    manifest_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    candidate = validate_projection(candidate_projection)
    if not isinstance(manifest_rows, (list, tuple)):
        _fail("projection_malformed")

    selected_ids: set[str] = set()
    seen_jobs: set[str] = set()
    for row in manifest_rows:
        if not isinstance(row, Mapping):
            _fail("projection_malformed")
        raw_resume_id = str(row.get("packet_resume") or "").strip()
        if not raw_resume_id:
            continue
        job_id = str(
            row.get("job_doc_id") or row.get("job_id") or row.get("doc_id") or ""
        ).strip()
        if not job_id or job_id in seen_jobs:
            _fail("projection_malformed")
        seen_jobs.add(job_id)
        selected_ids.add(_identity(raw_resume_id))

    if not selected_ids:
        _fail("selected_resume_evidence_missing")
    if len(selected_ids) > MAX_SELECTED_RESUMES:
        _fail("projection_limit_exceeded")

    candidates_by_id = {
        entry["resume_id"]: entry for entry in candidate["resumes"]
    }
    missing = selected_ids.difference(candidates_by_id)
    if missing:
        _fail("selected_resume_evidence_missing")
    return validate_projection(
        {
            "contract_version": PROJECTION_CONTRACT_VERSION,
            "resumes": [
                deepcopy(candidates_by_id[resume_id])
                for resume_id in sorted(selected_ids)
            ],
        }
    )


def _reject_unsafe_path(path: Path, *, require_file: bool = False) -> None:
    absolute = path.expanduser().absolute()
    if require_file:
        if not absolute.is_file() or absolute.is_symlink():
            _fail("projection_malformed")
        return
    parent = absolute.parent
    if not parent.is_dir() or parent.is_symlink():
        _fail("projection_malformed")
    if absolute.exists() and (absolute.is_dir() or absolute.is_symlink()):
        _fail("projection_malformed")


def write_projection_atomic(path: str | Path, payload: Mapping[str, Any]) -> Path:
    normalized = validate_projection(payload)
    output_path = Path(path).expanduser().absolute()
    _reject_unsafe_path(output_path)
    encoded = _serialized_bytes(normalized)
    descriptor = -1
    temporary_name = ""
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=str(output_path.parent),
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        _reject_unsafe_path(output_path)
        os.replace(temporary_name, output_path)
        temporary_name = ""
        os.chmod(output_path, 0o600)
        return output_path
    except ProjectionError:
        raise
    except OSError:
        _fail("projection_malformed")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def load_projection(path: str | Path) -> dict[str, Any]:
    input_path = Path(path).expanduser().absolute()
    _reject_unsafe_path(input_path, require_file=True)
    try:
        if input_path.stat().st_size > MAX_SERIALIZED_BYTES:
            _fail("projection_limit_exceeded")
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except ProjectionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError):
        _fail("projection_malformed")
    return validate_projection(payload)


def remove_projection_output(path: str | Path) -> None:
    output_path = Path(path).expanduser().absolute()
    if not output_path.exists():
        return
    _reject_unsafe_path(output_path, require_file=True)
    try:
        output_path.unlink()
    except OSError:
        _fail("projection_malformed")


def temporary_candidate_projection_path() -> Any:
    """Return a restrictive context manager yielding an internal candidate path."""

    class _CandidateWorkspace:
        def __init__(self) -> None:
            self._temporary_directory: tempfile.TemporaryDirectory[str] | None = None

        def __enter__(self) -> Path:
            self._temporary_directory = tempfile.TemporaryDirectory(
                prefix="applylens_shadow_resume_evidence_"
            )
            directory = Path(self._temporary_directory.name)
            os.chmod(directory, 0o700)
            return directory / "candidate_projection.json"

        def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
            if self._temporary_directory is not None:
                self._temporary_directory.cleanup()

    return _CandidateWorkspace()

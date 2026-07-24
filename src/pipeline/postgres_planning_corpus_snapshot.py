"""Bounded temporary JSONL snapshot for explicit Postgres planning reads."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Callable, Mapping, Sequence

from src.matching.job_adapter import build_job_evidence


MAX_POSTGRES_SNAPSHOT_JOBS = 50
MAX_POSTGRES_SNAPSHOT_BYTES = 8 * 1024 * 1024
_DIRECTORY_PREFIX = "applylens_postgres_planning_corpus_"
_CORPUS_FILENAME = "planning_corpus.jsonl"


class PostgresPlanningCorpusSnapshotError(ValueError):
    """A bounded Postgres planning snapshot operation failed."""


def _fail(code: str) -> None:
    raise PostgresPlanningCorpusSnapshotError(code)


def _bounded_limit(requested_limit: Any) -> int:
    if isinstance(requested_limit, bool):
        _fail("postgres_snapshot_limit_invalid")
    try:
        parsed = int(requested_limit)
    except (TypeError, ValueError):
        _fail("postgres_snapshot_limit_invalid")
    if parsed < 0:
        _fail("postgres_snapshot_limit_invalid")
    if parsed == 0:
        return MAX_POSTGRES_SNAPSHOT_JOBS
    return min(parsed, MAX_POSTGRES_SNAPSHOT_JOBS)


def _serialize_record(record: Mapping[str, Any]) -> bytes:
    try:
        return (
            json.dumps(
                dict(record),
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        _fail("postgres_snapshot_record_invalid")


@dataclass(frozen=True, slots=True)
class PostgresPlanningCorpusSnapshotCounts:
    requested: int
    fetched: int
    emitted: int
    invalid_rejected: int
    duplicate_rejected: int

    def runtime_counts(self) -> dict[str, int]:
        return {
            "postgres_snapshot_requested_count": self.requested,
            "postgres_snapshot_fetched_count": self.fetched,
            "postgres_snapshot_emitted_count": self.emitted,
            "postgres_snapshot_invalid_count": self.invalid_rejected,
            "postgres_snapshot_duplicate_count": self.duplicate_rejected,
        }


@dataclass(slots=True)
class PostgresPlanningCorpusSnapshot:
    directory: Path
    corpus_path: Path
    counts: PostgresPlanningCorpusSnapshotCounts
    cleanup_complete: bool = False

    def cleanup(self) -> bool:
        if self.cleanup_complete:
            return True
        try:
            directory = self.directory.absolute()
            if (
                not directory.name.startswith(_DIRECTORY_PREFIX)
                or directory.is_symlink()
                or not directory.is_dir()
            ):
                _fail("postgres_snapshot_cleanup_failed")
            for child in list(directory.iterdir()):
                if child.parent != directory:
                    _fail("postgres_snapshot_cleanup_failed")
                if child.is_symlink() or child.is_file():
                    child.unlink()
                else:
                    _fail("postgres_snapshot_cleanup_failed")
            directory.rmdir()
        except PostgresPlanningCorpusSnapshotError:
            raise
        except (OSError, ValueError):
            _fail("postgres_snapshot_cleanup_failed")
        self.cleanup_complete = True
        return True


def _private_directory() -> Path:
    directory: Path | None = None
    try:
        directory = Path(tempfile.mkdtemp(prefix=_DIRECTORY_PREFIX)).absolute()
        if directory.is_symlink() or not directory.is_dir():
            _fail("postgres_snapshot_unsafe_storage")
        os.chmod(directory, 0o700)
        if stat.S_IMODE(directory.stat().st_mode) != 0o700:
            _fail("postgres_snapshot_unsafe_storage")
        return directory
    except PostgresPlanningCorpusSnapshotError:
        if (
            directory is not None
            and directory.name.startswith(_DIRECTORY_PREFIX)
            and directory.is_dir()
            and not directory.is_symlink()
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    except OSError:
        if (
            directory is not None
            and directory.name.startswith(_DIRECTORY_PREFIX)
            and directory.is_dir()
            and not directory.is_symlink()
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        _fail("postgres_snapshot_unsafe_storage")


def _write_snapshot(directory: Path, encoded: bytes) -> Path:
    if len(encoded) > MAX_POSTGRES_SNAPSHOT_BYTES:
        _fail("postgres_snapshot_serialization_limit_exceeded")
    path = directory / _CORPUS_FILENAME
    descriptor = -1
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        if directory.is_symlink() or not directory.is_dir() or path.exists():
            _fail("postgres_snapshot_unsafe_storage")
        descriptor = os.open(path, flags, 0o600)
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            _fail("postgres_snapshot_unsafe_storage")
        written = os.write(descriptor, encoded)
        if written != len(encoded):
            _fail("postgres_snapshot_unsafe_storage")
        os.fsync(descriptor)
        os.fchmod(descriptor, 0o600)
        os.close(descriptor)
        descriptor = -1
        if (
            path.is_symlink()
            or not path.is_file()
            or stat.S_IMODE(path.stat().st_mode) != 0o600
        ):
            _fail("postgres_snapshot_unsafe_storage")
        return path
    except PostgresPlanningCorpusSnapshotError:
        raise
    except OSError:
        _fail("postgres_snapshot_unsafe_storage")
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def create_postgres_planning_corpus_snapshot(
    requested_limit: Any,
    *,
    reader: Callable[[int], Sequence[Mapping[str, Any]]] | None = None,
) -> PostgresPlanningCorpusSnapshot:
    """Read canonical Postgres rows and create one bounded private JSONL file."""

    bounded_limit = _bounded_limit(requested_limit)
    if reader is None:
        from src.storage.rag_store import get_rag_job_documents

        reader = get_rag_job_documents

    try:
        fetched_rows = reader(limit=bounded_limit)
    except Exception as exc:
        raise PostgresPlanningCorpusSnapshotError(
            "postgres_snapshot_read_failed"
        ) from exc
    if not isinstance(fetched_rows, Sequence) or isinstance(
        fetched_rows, (str, bytes, bytearray)
    ):
        _fail("postgres_snapshot_read_failed")
    fetched = min(len(fetched_rows), bounded_limit)
    if fetched == 0:
        _fail("postgres_snapshot_empty")

    invalid_rejected = 0
    duplicate_rejected = 0
    emitted_rows: list[dict[str, Any]] = []
    seen_job_ids: set[str] = set()
    for raw_row in list(fetched_rows)[:bounded_limit]:
        if not isinstance(raw_row, Mapping):
            invalid_rejected += 1
            continue
        row = dict(raw_row)
        try:
            evidence = build_job_evidence(row)
            job_doc_id = str(evidence.job_doc_id or "").strip()
        except Exception:
            invalid_rejected += 1
            continue
        if not job_doc_id:
            invalid_rejected += 1
            continue
        if job_doc_id in seen_job_ids:
            duplicate_rejected += 1
            continue
        row["job_doc_id"] = job_doc_id
        try:
            _serialize_record(row)
        except PostgresPlanningCorpusSnapshotError:
            invalid_rejected += 1
            continue
        seen_job_ids.add(job_doc_id)
        emitted_rows.append(row)

    if not emitted_rows:
        _fail("postgres_snapshot_no_usable_documents")

    encoded = b"".join(_serialize_record(row) for row in emitted_rows)
    if len(encoded) > MAX_POSTGRES_SNAPSHOT_BYTES:
        _fail("postgres_snapshot_serialization_limit_exceeded")

    directory: Path | None = None
    try:
        directory = _private_directory()
        corpus_path = _write_snapshot(directory, encoded)
        return PostgresPlanningCorpusSnapshot(
            directory=directory,
            corpus_path=corpus_path,
            counts=PostgresPlanningCorpusSnapshotCounts(
                requested=bounded_limit,
                fetched=fetched,
                emitted=len(emitted_rows),
                invalid_rejected=invalid_rejected,
                duplicate_rejected=duplicate_rejected,
            ),
        )
    except Exception:
        if directory is not None and directory.is_dir() and not directory.is_symlink():
            lifecycle = PostgresPlanningCorpusSnapshot(
                directory=directory,
                corpus_path=directory / _CORPUS_FILENAME,
                counts=PostgresPlanningCorpusSnapshotCounts(
                    requested=bounded_limit,
                    fetched=fetched,
                    emitted=0,
                    invalid_rejected=invalid_rejected,
                    duplicate_rejected=duplicate_rejected,
                ),
            )
            lifecycle.cleanup()
        raise

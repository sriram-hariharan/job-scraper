"""Bounded local JSONL owner for controlled shadow observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import stat
import struct
from typing import Iterator

from src.pipeline.shadow_observation_contract import (
    OBSERVATION_CONTRACT_VERSION,
    ShadowObservationRecord,
    parse_observation_json,
)
from src.utils.file_lock import exclusive_file_lock


DEFAULT_OBSERVATION_ROOT = Path("outputs/shadow_observations")
MAX_SEGMENT_BYTES = 10 * 1024 * 1024
RETENTION_DAYS = 30
_SEGMENT_PATTERN = re.compile(
    r"shadow-observations-(\d{4}-\d{2}-\d{2})-(\d{4})\.jsonl"
)
_LOCK_NAME = ".observation.lock"
_SECRET_NAME = ".observation-key"


@dataclass(frozen=True, slots=True)
class ObservationStoreResult:
    status: str


class ObservationStoreError(ValueError):
    """An observation store operation failed with a bounded code."""


def _regular_file(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return False
    return stat.S_ISREG(mode) and not path.is_symlink()


def _canonical_identity(
    *, owner_id: str, pipeline_run_id: str, context_id: str
) -> bytes:
    chunks = (
        OBSERVATION_CONTRACT_VERSION.encode("utf-8"),
        owner_id.encode("utf-8"),
        pipeline_run_id.encode("utf-8"),
        context_id.encode("utf-8"),
    )
    return b"".join(struct.pack(">I", len(chunk)) + chunk for chunk in chunks)


class ShadowObservationStore:
    def __init__(
        self,
        root: str | Path = DEFAULT_OBSERVATION_ROOT,
        *,
        today: date | None = None,
    ) -> None:
        self.root = Path(root)
        self._today = today

    def _utc_date(self) -> date:
        return self._today or datetime.now(timezone.utc).date()

    def _ensure_root(self) -> None:
        if self.root.exists():
            if self.root.is_symlink() or not self.root.is_dir():
                raise ObservationStoreError("unsafe_root")
        else:
            self.root.mkdir(parents=True, mode=0o700)
        os.chmod(self.root, 0o700)

    def _ensure_lock(self) -> Path:
        path = self.root / _LOCK_NAME
        flags = os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags, 0o600)
            os.close(descriptor)
        except OSError as exc:
            raise ObservationStoreError("unsafe_lock") from exc
        if not _regular_file(path):
            raise ObservationStoreError("unsafe_lock")
        os.chmod(path, 0o600)
        return path

    def _secret(self) -> bytes:
        path = self.root / _SECRET_NAME
        if path.exists():
            if not _regular_file(path):
                raise ObservationStoreError("unsafe_secret")
            try:
                secret = path.read_bytes()
            except OSError as exc:
                raise ObservationStoreError("secret_read_failed") from exc
            if len(secret) != 32:
                raise ObservationStoreError("secret_invalid")
            os.chmod(path, 0o600)
            return secret
        secret = secrets.token_bytes(32)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = -1
        try:
            descriptor = os.open(path, flags, 0o600)
            written = os.write(descriptor, secret)
            if written != len(secret):
                raise OSError("short secret write")
            os.fsync(descriptor)
        except OSError as exc:
            raise ObservationStoreError("secret_write_failed") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        os.chmod(path, 0o600)
        return secret

    def observation_key(
        self, *, owner_id: str, pipeline_run_id: str, context_id: str
    ) -> str:
        self._ensure_root()
        lock_path = self._ensure_lock()
        try:
            with exclusive_file_lock(lock_path):
                os.chmod(lock_path, 0o600)
                secret = self._secret()
        except ObservationStoreError:
            raise
        except Exception as exc:
            raise ObservationStoreError("store_lock_failed") from exc
        digest = hmac.new(
            secret,
            _canonical_identity(
                owner_id=owner_id,
                pipeline_run_id=pipeline_run_id,
                context_id=context_id,
            ),
            hashlib.sha256,
        ).hexdigest()
        return digest[:32]

    def _owned_segments(self) -> Iterator[tuple[Path, date, int]]:
        try:
            children = list(self.root.iterdir())
        except OSError as exc:
            raise ObservationStoreError("store_scan_failed") from exc
        for child in children:
            match = _SEGMENT_PATTERN.fullmatch(child.name)
            if match is None:
                continue
            if child.is_symlink() or not _regular_file(child):
                raise ObservationStoreError("unsafe_segment")
            try:
                segment_date = date.fromisoformat(match.group(1))
            except ValueError as exc:
                raise ObservationStoreError("segment_name_invalid") from exc
            yield child, segment_date, int(match.group(2))

    def _apply_retention(self, today: date) -> None:
        cutoff = today - timedelta(days=RETENTION_DAYS)
        for path, segment_date, _index in list(self._owned_segments()):
            if segment_date < cutoff:
                try:
                    path.unlink()
                except OSError as exc:
                    raise ObservationStoreError("retention_failed") from exc

    def _read_records(
        self, path: Path
    ) -> list[ShadowObservationRecord]:
        try:
            if path.stat().st_size > MAX_SEGMENT_BYTES:
                raise ObservationStoreError("segment_oversized")
            rendered = path.read_bytes()
        except ObservationStoreError:
            raise
        except OSError as exc:
            raise ObservationStoreError("segment_read_failed") from exc
        if rendered and not rendered.endswith(b"\n"):
            raise ObservationStoreError("malformed_segment")
        records: list[ShadowObservationRecord] = []
        for line in rendered.splitlines():
            if not line:
                raise ObservationStoreError("malformed_segment")
            try:
                records.append(parse_observation_json(line))
            except ValueError as exc:
                raise ObservationStoreError("malformed_segment") from exc
        return records

    def _select_segment(self, today: date, record_size: int) -> Path:
        same_day = sorted(
            (
                (index, path)
                for path, segment_date, index in self._owned_segments()
                if segment_date == today
            ),
            key=lambda item: item[0],
        )
        if same_day:
            index, current = same_day[-1]
            size = current.stat().st_size
            if size + record_size <= MAX_SEGMENT_BYTES:
                return current
            index += 1
        else:
            index = 1
        if index > 9999:
            raise ObservationStoreError("segment_limit_reached")
        return self.root / (
            f"shadow-observations-{today.isoformat()}-{index:04d}.jsonl"
        )

    def _append_bytes(self, path: Path, encoded: bytes) -> None:
        if path.exists() and (path.is_symlink() or not _regular_file(path)):
            raise ObservationStoreError("unsafe_segment")
        flags = os.O_CREAT | os.O_WRONLY | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = -1
        initial_size = 0
        try:
            descriptor = os.open(path, flags, 0o600)
            details = os.fstat(descriptor)
            if not stat.S_ISREG(details.st_mode):
                raise ObservationStoreError("unsafe_segment")
            initial_size = details.st_size
            written = os.write(descriptor, encoded)
            if written != len(encoded):
                raise OSError("short observation write")
            os.fsync(descriptor)
            os.fchmod(descriptor, 0o600)
        except ObservationStoreError:
            raise
        except OSError as exc:
            if descriptor >= 0:
                try:
                    os.ftruncate(descriptor, initial_size)
                    os.fsync(descriptor)
                except OSError:
                    pass
            raise ObservationStoreError("append_failed") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def append(self, record: ShadowObservationRecord) -> ObservationStoreResult:
        encoded = record.serialize()
        try:
            self._ensure_root()
            lock_path = self._ensure_lock()
            with exclusive_file_lock(lock_path):
                os.chmod(lock_path, 0o600)
                today = self._utc_date()
                self._apply_retention(today)
                identical = False
                for path, _segment_date, _index in self._owned_segments():
                    for existing in self._read_records(path):
                        if existing.observation_key != record.observation_key:
                            continue
                        if existing == record:
                            identical = True
                            continue
                        return ObservationStoreResult("duplicate_conflict")
                if identical:
                    return ObservationStoreResult("already_recorded")
                segment = self._select_segment(today, len(encoded))
                if segment.exists():
                    self._read_records(segment)
                self._append_bytes(segment, encoded)
            return ObservationStoreResult("stored")
        except ObservationStoreError as exc:
            return ObservationStoreResult(str(exc))
        except Exception:
            return ObservationStoreResult("store_failed")

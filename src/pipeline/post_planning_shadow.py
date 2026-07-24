"""Default-off, non-authoritative post-planning shadow lifecycle."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
import errno
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Mapping, Sequence

from src.utils.logging import get_logger


SHADOW_FLAG = "APPLYLENS_DURABLE_EVIDENCE_CHAIN_SHADOW_ENABLED"
SHADOW_HOOK_VERSION = "applylens-post-planning-shadow-v1"
AUTHORITATIVE_FACTS_VERSION = "applylens-shadow-authoritative-facts-v1"
SHADOW_EXECUTION_VERSION = "evidence-chain-shadow-execution-v1"
SHADOW_PARITY_VERSION = "evidence-chain-shadow-parity-v1"
MAX_SHADOW_JOBS = 25
MAX_FACTS_BYTES = 256_000
MAX_OUTPUT_BYTES = 64 * 1024
SHADOW_TIMEOUT_SECONDS = 30
PROCESS_STOP_WAIT_SECONDS = 2
_IDENTITY = re.compile(r"[A-Za-z0-9_.:@/-]{1,200}")
_EXPECTED_NODES = [
    "jd_intelligence",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]
_logger = get_logger(__name__)
_CLEANUP_CATEGORIES = {
    "process_terminate_failed",
    "process_kill_failed",
    "process_wait_or_drain_failed",
    "temporary_cleanup_failed",
    "cleanup_target_rejected",
    "process_liveness_unconfirmed",
}


@dataclass
class CleanupResult:
    categories: dict[str, int] = field(default_factory=dict)
    process_liveness_confirmed: bool | None = None

    def add(self, category: str) -> None:
        if category in _CLEANUP_CATEGORIES:
            self.categories[category] = min(
                1_000_000, self.categories.get(category, 0) + 1
            )

    def merge(self, other: "CleanupResult") -> "CleanupResult":
        for category, count in other.categories.items():
            self.categories[category] = min(
                1_000_000, self.categories.get(category, 0) + count
            )
        if other.process_liveness_confirmed is not None:
            self.process_liveness_confirmed = (
                other.process_liveness_confirmed
            )
        return self

    @property
    def failure_count(self) -> int:
        return sum(self.categories.values())

    @property
    def complete(self) -> bool:
        return self.failure_count == 0


def shadow_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    return str(source.get(SHADOW_FLAG, "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _identity(value: Any) -> str:
    text = str(value or "").strip()
    return text if _IDENTITY.fullmatch(text) else ""


def _bounded_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(parsed, 1_000_000))


def _optional_bounded_int(
    value: Any, *, maximum: int = 1_000_000
) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(parsed, maximum))


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    try:
        encoded = (
            json.dumps(
                payload,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("authoritative_facts_malformed") from exc
    if len(encoded) > MAX_FACTS_BYTES:
        raise ValueError("authoritative_facts_too_large")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise ValueError("authoritative_facts_path_unsafe")
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise ValueError("authoritative_facts_path_unsafe")
    descriptor = -1
    temporary = ""
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = ""
        os.chmod(path, 0o600)
    except OSError as exc:
        raise ValueError("authoritative_facts_write_failed") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary:
            try:
                Path(temporary).unlink()
            except FileNotFoundError:
                pass


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("authoritative_artifact_missing")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_authoritative_facts(
    *,
    execution_queue_path: str | Path,
    packet_manifest_path: str | Path,
    pipeline_run_id: str,
) -> tuple[dict[str, Any], int]:
    queue_rows = _csv_rows(Path(execution_queue_path))
    manifest_rows = _csv_rows(Path(packet_manifest_path))
    selected_by_job: dict[str, str] = {}
    for row in manifest_rows:
        job_id = _identity(row.get("job_doc_id"))
        resume_id = _identity(row.get("packet_resume"))
        if not job_id or not resume_id or job_id in selected_by_job:
            if job_id in selected_by_job:
                raise ValueError("authoritative_job_identity_duplicate")
            continue
        selected_by_job[job_id] = resume_id

    ordered: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for row in queue_rows:
        job_id = _identity(row.get("job_doc_id"))
        if not job_id or job_id not in selected_by_job:
            continue
        if job_id in seen:
            raise ValueError("authoritative_job_identity_duplicate")
        seen.add(job_id)
        ordered.append(
            (
                _bounded_int(row.get("queue_rank"), 1_000_000),
                job_id,
                selected_by_job[job_id],
            )
        )
    ordered.sort(key=lambda item: (item[0], item[1]))
    skipped_by_limit = max(0, len(ordered) - MAX_SHADOW_JOBS)
    jobs = []
    for queue_rank, job_id, resume_id in ordered[:MAX_SHADOW_JOBS]:
        jobs.append(
            {
                "job_id": job_id,
                "selected_resume_id": resume_id,
                "queue_rank": queue_rank,
                "comparisons": [
                    {
                        "field": "completed_node_order",
                        "mode": "ordered",
                        "authoritative_value": _EXPECTED_NODES,
                    },
                    {
                        "field": "job_id",
                        "mode": "exact",
                        "authoritative_value": job_id,
                    },
                    {
                        "field": "pending_node",
                        "mode": "exact",
                        "authoritative_value": "finalize",
                    },
                    {
                        "field": "pipeline_run_id",
                        "mode": "exact",
                        "authoritative_value": pipeline_run_id,
                    },
                    {
                        "field": "selected_resume_id",
                        "mode": "exact",
                        "authoritative_value": resume_id,
                    },
                ],
            }
        )
    if not jobs:
        raise ValueError("authoritative_jobs_missing")
    return (
        {
            "contract_version": AUTHORITATIVE_FACTS_VERSION,
            "pipeline_run_id": pipeline_run_id,
            "jobs": jobs,
        },
        skipped_by_limit,
    )


def _bounded_reader(stream: Any, retained: bytearray, state: dict[str, bool]) -> None:
    try:
        while True:
            chunk = stream.read(8192)
            if not chunk:
                return
            remaining = MAX_OUTPUT_BYTES - len(retained)
            if remaining > 0:
                retained.extend(chunk[:remaining])
            if len(chunk) > remaining:
                state["overflow"] = True
    finally:
        stream.close()


def _process_group_live(process_group_id: int) -> bool | None:
    if os.name != "posix" or process_group_id <= 0:
        return None
    try:
        os.killpg(process_group_id, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return None
    except OSError as exc:
        return False if exc.errno == errno.ESRCH else None


def _wait_for_process_group_exit(
    process_group_id: int, timeout_seconds: float
) -> bool | None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        live = _process_group_live(process_group_id)
        if live is not True:
            return None if live is None else True
        if time.monotonic() >= deadline:
            return False
        time.sleep(min(0.02, max(0.0, deadline - time.monotonic())))


def _stop_process_group(
    process: subprocess.Popen[bytes],
    *,
    owned_process_group_id: int | None,
) -> CleanupResult:
    result = CleanupResult()
    if os.name != "posix" or owned_process_group_id is None:
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=PROCESS_STOP_WAIT_SECONDS)
            else:
                process.wait(timeout=0)
        except OSError:
            result.add("process_terminate_failed")
        except subprocess.TimeoutExpired:
            try:
                process.kill()
                process.wait(timeout=PROCESS_STOP_WAIT_SECONDS)
            except OSError:
                result.add("process_kill_failed")
            except subprocess.TimeoutExpired:
                result.add("process_wait_or_drain_failed")
        result.process_liveness_confirmed = None
        result.add("process_liveness_unconfirmed")
        return result

    group_live = _process_group_live(owned_process_group_id)
    if process.poll() is None or group_live is True:
        try:
            os.killpg(owned_process_group_id, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except OSError:
            result.add("process_terminate_failed")

    try:
        if process.poll() is None:
            process.wait(timeout=PROCESS_STOP_WAIT_SECONDS)
        else:
            process.wait(timeout=0)
    except OSError:
        result.add("process_wait_or_drain_failed")
    except subprocess.TimeoutExpired:
        pass

    group_stopped = _wait_for_process_group_exit(
        owned_process_group_id, PROCESS_STOP_WAIT_SECONDS
    )
    if group_stopped is False:
        try:
            os.killpg(owned_process_group_id, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            result.add("process_kill_failed")
        try:
            if process.poll() is None:
                process.wait(timeout=PROCESS_STOP_WAIT_SECONDS)
        except (OSError, subprocess.TimeoutExpired):
            result.add("process_wait_or_drain_failed")
        group_stopped = _wait_for_process_group_exit(
            owned_process_group_id, PROCESS_STOP_WAIT_SECONDS
        )

    try:
        process.wait(timeout=0)
        direct_reaped = process.returncode is not None
    except (OSError, subprocess.TimeoutExpired):
        direct_reaped = False
        result.add("process_wait_or_drain_failed")
    result.process_liveness_confirmed = bool(
        direct_reaped and group_stopped is True
    )
    if not result.process_liveness_confirmed:
        result.add("process_liveness_unconfirmed")
    return result


def _shadow_subprocess_environment() -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for key, value in os.environ.items():
        normalized = key.upper()
        if (
            normalized == SHADOW_FLAG
            or normalized == "DATABASE_URL"
            or "DURABLE" in normalized
            or "LLM" in normalized
            or normalized.endswith("_API_KEY")
        ):
            continue
        sanitized[key] = value
    return sanitized


def _run_shadow_command(command: Sequence[str]) -> dict[str, Any]:
    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=(os.name == "posix"),
        env=_shadow_subprocess_environment(),
    )
    owned_process_group_id = process.pid if os.name == "posix" else None
    if process.stdout is None or process.stderr is None:
        cleanup = _stop_process_group(
            process, owned_process_group_id=owned_process_group_id
        )
        return {
            "classification": "shadow_execution_failure",
            "cleanup_categories": cleanup.categories,
            "process_liveness_confirmed": cleanup.process_liveness_confirmed,
            "subprocess_wall_clock_ms": max(
                0, int((time.monotonic() - started) * 1000)
            ),
        }
    stdout = bytearray()
    stderr = bytearray()
    stdout_state = {"overflow": False}
    stderr_state = {"overflow": False}
    readers = [
        threading.Thread(
            target=_bounded_reader,
            args=(process.stdout, stdout, stdout_state),
            daemon=True,
        ),
        threading.Thread(
            target=_bounded_reader,
            args=(process.stderr, stderr, stderr_state),
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=SHADOW_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True
    cleanup = _stop_process_group(
        process, owned_process_group_id=owned_process_group_id
    )
    for reader in readers:
        reader.join(timeout=PROCESS_STOP_WAIT_SECONDS)
        if reader.is_alive():
            cleanup.add("process_wait_or_drain_failed")
    if (
        cleanup.process_liveness_confirmed is not True
        and "process_liveness_unconfirmed" not in cleanup.categories
    ):
        cleanup.add("process_liveness_unconfirmed")

    base = {
        "cleanup_categories": cleanup.categories,
        "process_liveness_confirmed": cleanup.process_liveness_confirmed,
        "subprocess_wall_clock_ms": max(
            0, int((time.monotonic() - started) * 1000)
        ),
    }
    if cleanup.process_liveness_confirmed is not True:
        return {
            **base,
            "classification": "shadow_safety_violation",
            "safety_violation_count": 1,
        }
    if timed_out:
        return {**base, "classification": "shadow_timeout"}
    if (
        process.returncode != 0
        or stdout_state["overflow"]
        or stderr_state["overflow"]
    ):
        return {**base, "classification": "shadow_execution_failure"}
    try:
        rendered = stdout.decode("utf-8")
    except UnicodeError:
        return {**base, "classification": "shadow_execution_failure"}
    lines = rendered.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        return {**base, "classification": "shadow_execution_failure"}
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError:
        return {**base, "classification": "shadow_execution_failure"}
    classified = _classify_command_payload(payload)
    return {**classified, **base}


def _classify_command_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"classification": "shadow_execution_failure"}
    results = payload.get("results")
    if (
        payload.get("execution_version") != SHADOW_EXECUTION_VERSION
        or payload.get("status")
        not in {"completed", "write_suppression_violation"}
        or not isinstance(results, list)
        or not results
        or len(results) > MAX_SHADOW_JOBS
        or payload.get("job_count") != len(results)
    ):
        return {"classification": "shadow_execution_failure"}
    statuses = [
        str(row.get("status") or "")
        for row in results
        if isinstance(row, Mapping)
    ]
    aggregates: dict[str, Any] = {
        "jobs_attempted": len(results),
        "shadow_completed": statuses.count("parity_completed"),
        "adapter_rejection_count": statuses.count("input_rejected"),
        "graph_failure_count": sum(
            status
            in {
                "graph_construction_failed",
                "graph_execution_failed",
                "graph_output_malformed",
            }
            for status in statuses
        ),
        "parity_processing_failure_count": statuses.count("parity_failed"),
    }
    if (
        payload.get("status") == "write_suppression_violation"
        or payload.get("artifacts_unchanged") is not True
        or any(
            isinstance(row, Mapping)
            and row.get("status") == "write_suppression_violation"
            for row in results
        )
    ):
        return {
            **aggregates,
            "classification": "shadow_safety_violation",
            "shadow_write_suppression_violations": 1,
            "safety_violation_count": 1,
        }

    matches = 0
    mismatches = 0
    exact_total = 0
    exact_matched = 0
    selected_total = 0
    selected_matched = 0
    ordered_total = 0
    ordered_matched = 0
    incomparable = 0
    max_graph_latency_ms = 0
    comparison_fields_seen = False
    graph_latency_seen = False
    for row in results:
        if not isinstance(row, Mapping) or row.get("status") != "parity_completed":
            return {**aggregates, "classification": "shadow_execution_failure"}
        facts = row.get("shadow_facts")
        if (
            not isinstance(facts, Mapping)
            or facts.get("pending_node") != "finalize"
        ):
            return {**aggregates, "classification": "shadow_execution_failure"}
        if (
            facts.get("finalization_executed") is not False
            or facts.get("final_bundle_present") is not False
            or facts.get("final_trace_present") is not False
        ):
            return {
                **aggregates,
                "classification": "shadow_safety_violation",
                "shadow_write_suppression_violations": 0,
                "safety_violation_count": 1,
            }
        if facts.get("completed_node_order") != _EXPECTED_NODES:
            return {**aggregates, "classification": "shadow_execution_failure"}
        if facts.get("graph_latency_ms") is not None:
            graph_latency_seen = True
            max_graph_latency_ms = max(
                max_graph_latency_ms,
                _bounded_int(facts.get("graph_latency_ms")),
            )
        parity = row.get("parity")
        if (
            not isinstance(parity, Mapping)
            or parity.get("contract_version") != SHADOW_PARITY_VERSION
        ):
            return {**aggregates, "classification": "shadow_execution_failure"}
        classification = parity.get("overall_classification")
        if classification == "match":
            matches += 1
        elif classification == "mismatch":
            mismatches += 1
        else:
            return {**aggregates, "classification": "shadow_execution_failure"}
        field_results = parity.get("field_results")
        if field_results is None:
            continue
        if not isinstance(field_results, list):
            return {**aggregates, "classification": "shadow_execution_failure"}
        comparison_fields_seen = True
        for field_result in field_results:
            if not isinstance(field_result, Mapping):
                return {
                    **aggregates,
                    "classification": "shadow_execution_failure",
                }
            field_name = str(field_result.get("field") or "")
            mode = field_result.get("mode")
            status = field_result.get("status")
            if status == "intentionally_incomparable":
                incomparable += 1
            if mode == "ordered":
                ordered_total += 1
                ordered_matched += int(status == "match")
            if mode == "exact" and field_name == "selected_resume_id":
                selected_total += 1
                selected_matched += int(status == "match")
            elif mode == "exact":
                exact_total += 1
                exact_matched += int(status == "match")
    return {
        **aggregates,
        "classification": (
            "parity_mismatch" if mismatches else "shadow_completed"
        ),
        "shadow_parity_matches": matches,
        "shadow_parity_mismatches": mismatches,
        "shadow_completed": len(results),
        "parity_mismatch_count": mismatches,
        "exact_identity_total": exact_total if comparison_fields_seen else None,
        "exact_identity_matched": (
            exact_matched if comparison_fields_seen else None
        ),
        "selected_resume_total": (
            selected_total if comparison_fields_seen else None
        ),
        "selected_resume_matched": (
            selected_matched if comparison_fields_seen else None
        ),
        "ordered_parity_total": (
            ordered_total if comparison_fields_seen else None
        ),
        "ordered_parity_matched": (
            ordered_matched if comparison_fields_seen else None
        ),
        "categorical_parity_total": None,
        "categorical_parity_matched": None,
        "intentionally_incomparable_count": (
            incomparable if comparison_fields_seen else None
        ),
        "max_job_graph_latency_ms": (
            max_graph_latency_ms if graph_latency_seen else None
        ),
    }


@dataclass
class PostPlanningShadowLifecycle:
    enabled: bool
    armed: bool
    owner_id: str = ""
    pipeline_run_id: str = ""
    context_id: str = ""
    directory: Path | None = None
    projection_path: Path | None = None
    status_path: Path | None = None
    facts_path: Path | None = None
    observation_root: Path = field(
        default_factory=lambda: Path("outputs/shadow_observations")
    )
    initial_classification: str = ""
    _cleaned: bool = field(default=False, init=False, repr=False)
    _cleanup_result: CleanupResult = field(
        default_factory=CleanupResult, init=False, repr=False
    )

    @property
    def planning_arguments(self) -> list[str]:
        if not self.armed:
            return []
        return [
            "--shadow-resume-evidence-output",
            str(self.projection_path),
            "--shadow-resume-evidence-status-output",
            str(self.status_path),
            "--shadow-resume-evidence-non-authoritative",
        ]

    def _command(
        self,
        *,
        job_corpus_path: str | Path,
        output_dir: str | Path,
    ) -> list[str]:
        output = Path(output_dir)
        return [
            sys.executable,
            "run_evidence_chain_shadow.py",
            "--execute-shadow",
            "--job-corpus",
            str(job_corpus_path),
            "--best-resume",
            str(output / "best_resume_variant_by_job.csv"),
            "--execution-queue",
            str(output / "application_execution_queue.csv"),
            "--packet-manifest",
            str(output / "job_packet_manifest.csv"),
            "--resume-evidence",
            str(self.projection_path),
            "--authoritative-facts",
            str(self.facts_path),
            "--owner-id",
            self.owner_id,
            "--pipeline-run-id",
            self.pipeline_run_id,
            "--context-id",
            self.context_id,
        ]

    def complete_after_authoritative_success(
        self,
        *,
        job_corpus_path: str | Path,
        output_dir: str | Path,
    ) -> dict[str, Any]:
        started = time.monotonic()
        outcome: dict[str, Any] = {
            "classification": self.initial_classification
            or "shadow_execution_failure"
        }
        try:
            if self.armed:
                from src.pipeline.shadow_resume_evidence_projection import (
                    ProjectionError,
                    load_handoff_status,
                    load_projection,
                )

                try:
                    status = load_handoff_status(self.status_path)
                except ProjectionError:
                    status = {"status": "failed"}
                if status["status"] == "failed":
                    outcome = {"classification": "shadow_projection_failed"}
                elif status["status"] == "skipped":
                    outcome = {"classification": "shadow_projection_skipped"}
                else:
                    try:
                        projection_mode = (
                            self.projection_path.stat().st_mode & 0o777
                            if self.projection_path is not None
                            else -1
                        )
                    except OSError:
                        projection_mode = -1
                    if (
                        status["status"] != "ready"
                        or status["projection_available"] is not True
                        or projection_mode != 0o600
                    ):
                        outcome = {
                            "classification": "shadow_projection_failed"
                        }
                    else:
                        try:
                            load_projection(self.projection_path)
                        except (ProjectionError, OSError):
                            outcome = {
                                "classification": "shadow_projection_failed"
                            }
                        else:
                            output = Path(output_dir)
                            facts, skipped_by_limit = (
                                build_authoritative_facts(
                                    execution_queue_path=output
                                    / "application_execution_queue.csv",
                                    packet_manifest_path=output
                                    / "job_packet_manifest.csv",
                                    pipeline_run_id=self.pipeline_run_id,
                                )
                            )
                            _atomic_json(self.facts_path, facts)
                            outcome = _run_shadow_command(
                                self._command(
                                    job_corpus_path=job_corpus_path,
                                    output_dir=output_dir,
                                )
                            )
                            outcome["shadow_skipped_by_limit"] = (
                                skipped_by_limit
                            )
                            facts = {}
                            status = {}
            else:
                outcome = {
                    "classification": self.initial_classification
                    or "shadow_execution_failure"
                }
        except Exception:
            outcome = {"classification": "shadow_execution_failure"}
        command_cleanup = CleanupResult(
            categories=dict(outcome.pop("cleanup_categories", {}) or {}),
            process_liveness_confirmed=outcome.get(
                "process_liveness_confirmed"
            ),
        )
        cleanup = command_cleanup.merge(self.cleanup())
        return self._observe(
            outcome,
            started,
            cleanup=cleanup,
            persist_observation=self.armed,
        )

    def _observe(
        self,
        outcome: dict[str, Any],
        started: float,
        *,
        cleanup: CleanupResult,
        persist_observation: bool,
    ) -> dict[str, Any]:
        classification = str(outcome.get("classification") or "")[:80]
        if cleanup.process_liveness_confirmed is False:
            classification = "shadow_safety_violation"
            outcome["classification"] = classification
            outcome["safety_violation_count"] = max(
                1, _bounded_int(outcome.get("safety_violation_count"))
            )
        latency_ms = max(0, int((time.monotonic() - started) * 1000))
        attempted = int(
            classification
            in {
                "shadow_completed",
                "parity_mismatch",
                "shadow_execution_failure",
                "shadow_timeout",
                "shadow_safety_violation",
            }
        )
        skipped = int(
            classification
            in {
                "shadow_skipped_missing_identity",
                "shadow_projection_failed",
                "shadow_projection_skipped",
            }
        )
        counts = {
            "shadow_enabled": 1,
            "shadow_attempted": attempted,
            "shadow_completed": _bounded_int(outcome.get("shadow_completed")),
            "shadow_skipped": skipped,
            "shadow_failed": int(
                classification
                in {
                    "shadow_projection_failed",
                    "shadow_execution_failure",
                    "shadow_timeout",
                    "shadow_safety_violation",
                }
            ),
            "shadow_parity_matches": _bounded_int(
                outcome.get("shadow_parity_matches")
            ),
            "shadow_parity_mismatches": _bounded_int(
                outcome.get("shadow_parity_mismatches")
            ),
            "shadow_skipped_by_limit": _bounded_int(
                outcome.get("shadow_skipped_by_limit")
            ),
            "shadow_timeout_count": int(classification == "shadow_timeout"),
            "shadow_write_suppression_violations": _bounded_int(
                outcome.get("shadow_write_suppression_violations")
            ),
            "shadow_latency_ms": latency_ms,
            "shadow_failure_classification": classification,
            "shadow_contract_version": SHADOW_HOOK_VERSION,
        }
        observation_status = "not_applicable"
        if persist_observation:
            observation_status = self._persist_observation(
                outcome=outcome,
                counts=counts,
                cleanup=cleanup,
                latency_ms=latency_ms,
            )
            if observation_status not in {"stored", "already_recorded"}:
                try:
                    _logger.warning(
                        "Post-planning shadow observation failed code=%s",
                        observation_status,
                    )
                except Exception:
                    pass
        status_update_succeeded = False
        try:
            from src.pipeline.runtime_status import update_counts

            update_counts(**counts)
            status_update_succeeded = True
        except Exception:
            try:
                _logger.warning(
                    "Post-planning shadow runtime-count update failed"
                )
            except Exception:
                pass
        aggregate_log_succeeded = False
        try:
            _logger.info(
                "Post-planning shadow terminal classification=%s attempted=%s "
                "completed=%s skipped=%s parity_matches=%s "
                "parity_mismatches=%s skipped_by_limit=%s timeout=%s "
                "safety_violations=%s cleanup_failures=%s "
                "liveness_confirmed=%s observation=%s latency_ms=%s "
                "contract=%s",
                classification,
                attempted,
                counts["shadow_completed"],
                skipped,
                counts["shadow_parity_matches"],
                counts["shadow_parity_mismatches"],
                counts["shadow_skipped_by_limit"],
                counts["shadow_timeout_count"],
                counts["shadow_write_suppression_violations"],
                cleanup.failure_count,
                cleanup.process_liveness_confirmed,
                observation_status,
                latency_ms,
                SHADOW_HOOK_VERSION,
            )
            aggregate_log_succeeded = True
        except Exception:
            pass
        return {
            **outcome,
            **counts,
            "cleanup_categories": dict(cleanup.categories),
            "cleanup_failure_count": cleanup.failure_count,
            "cleanup_complete": cleanup.complete,
            "process_liveness_failure_count": int(
                cleanup.process_liveness_confirmed is False
            ),
            "process_liveness_confirmed": (
                cleanup.process_liveness_confirmed
            ),
            "observation_store_status": observation_status,
            "status_update_succeeded": status_update_succeeded,
            "aggregate_log_succeeded": aggregate_log_succeeded,
        }

    def _persist_observation(
        self,
        *,
        outcome: Mapping[str, Any],
        counts: Mapping[str, Any],
        cleanup: CleanupResult,
        latency_ms: int,
    ) -> str:
        try:
            from src.pipeline.shadow_observation_contract import (
                OBSERVATION_CONTRACT_VERSION,
                OBSERVATION_MODE,
                ShadowObservationRecord,
            )
            from src.pipeline.shadow_observation_store import (
                ShadowObservationStore,
            )

            store = ShadowObservationStore(self.observation_root)
            observation_key = store.observation_key(
                owner_id=self.owner_id,
                pipeline_run_id=self.pipeline_run_id,
                context_id=self.context_id,
            )
            record = ShadowObservationRecord(
                contract_version=OBSERVATION_CONTRACT_VERSION,
                observation_key=observation_key,
                observation_date_utc=datetime.now(timezone.utc)
                .date()
                .isoformat(),
                shadow_mode=OBSERVATION_MODE,
                terminal_classification=str(
                    outcome.get("classification") or ""
                ),
                authoritative_run_succeeded=True,
                invocation_count=1,
                jobs_attempted=_optional_bounded_int(
                    outcome.get("jobs_attempted"), maximum=25
                ),
                jobs_completed=_optional_bounded_int(
                    outcome.get("shadow_completed"), maximum=25
                ),
                jobs_skipped=(
                    1
                    if outcome.get("classification")
                    in {
                        "shadow_projection_failed",
                        "shadow_projection_skipped",
                    }
                    else 0
                ),
                jobs_skipped_by_limit=_optional_bounded_int(
                    outcome.get("shadow_skipped_by_limit"), maximum=25
                ),
                adapter_rejection_count=_optional_bounded_int(
                    outcome.get("adapter_rejection_count"), maximum=25
                ),
                graph_failure_count=_optional_bounded_int(
                    outcome.get("graph_failure_count"), maximum=25
                ),
                parity_mismatch_count=_optional_bounded_int(
                    outcome.get("parity_mismatch_count")
                ),
                parity_processing_failure_count=_optional_bounded_int(
                    outcome.get("parity_processing_failure_count"),
                    maximum=25,
                ),
                timeout_count=int(
                    outcome.get("classification") == "shadow_timeout"
                ),
                safety_violation_count=_optional_bounded_int(
                    outcome.get("safety_violation_count")
                )
                or 0,
                cleanup_failure_count=cleanup.failure_count,
                process_liveness_failure_count=int(
                    cleanup.process_liveness_confirmed is False
                ),
                exact_identity_total=_optional_bounded_int(
                    outcome.get("exact_identity_total")
                ),
                exact_identity_matched=_optional_bounded_int(
                    outcome.get("exact_identity_matched")
                ),
                selected_resume_total=_optional_bounded_int(
                    outcome.get("selected_resume_total")
                ),
                selected_resume_matched=_optional_bounded_int(
                    outcome.get("selected_resume_matched")
                ),
                ordered_parity_total=_optional_bounded_int(
                    outcome.get("ordered_parity_total")
                ),
                ordered_parity_matched=_optional_bounded_int(
                    outcome.get("ordered_parity_matched")
                ),
                categorical_parity_total=_optional_bounded_int(
                    outcome.get("categorical_parity_total")
                ),
                categorical_parity_matched=_optional_bounded_int(
                    outcome.get("categorical_parity_matched")
                ),
                intentionally_incomparable_count=_optional_bounded_int(
                    outcome.get("intentionally_incomparable_count")
                ),
                shadow_latency_ms_total=min(latency_ms, 3_600_000),
                max_job_graph_latency_ms=_optional_bounded_int(
                    outcome.get("max_job_graph_latency_ms"),
                    maximum=3_600_000,
                ),
                subprocess_wall_clock_ms=_optional_bounded_int(
                    outcome.get("subprocess_wall_clock_ms"),
                    maximum=3_600_000,
                ),
                status_update_succeeded=None,
                aggregate_log_succeeded=None,
                flag_enabled_for_run=True,
                cleanup_complete=cleanup.complete,
                process_liveness_confirmed=(
                    cleanup.process_liveness_confirmed
                ),
            )
            return store.append(record).status
        except Exception as exc:
            code = str(exc)
            if not re.fullmatch(r"[a-z0-9_]{1,80}", code):
                code = "observation_failed"
            return code

    def cleanup(self) -> CleanupResult:
        if self._cleaned:
            return self._cleanup_result
        self._cleaned = True
        directory = self.directory
        if directory is None:
            return self._cleanup_result
        try:
            resolved = directory.absolute()
            safe_directory = (
                resolved.name.startswith("applylens_post_planning_shadow_")
                and not resolved.is_symlink()
                and resolved.is_dir()
            )
        except OSError:
            self._cleanup_result.add("temporary_cleanup_failed")
            return self._cleanup_result
        if not safe_directory:
            self._cleanup_result.add("cleanup_target_rejected")
            return self._cleanup_result
        try:
            children = list(resolved.iterdir())
        except OSError:
            self._cleanup_result.add("temporary_cleanup_failed")
            return self._cleanup_result
        for child in children:
            if child.parent != resolved:
                self._cleanup_result.add("cleanup_target_rejected")
                continue
            try:
                if child.is_symlink() or child.is_file():
                    child.unlink()
                else:
                    self._cleanup_result.add("cleanup_target_rejected")
            except FileNotFoundError:
                pass
            except OSError:
                self._cleanup_result.add("temporary_cleanup_failed")
        try:
            resolved.rmdir()
        except OSError:
            self._cleanup_result.add("temporary_cleanup_failed")
        return self._cleanup_result


def prepare_post_planning_shadow(
    env: Mapping[str, str] | None = None,
) -> PostPlanningShadowLifecycle:
    source = os.environ if env is None else env
    if not shadow_enabled(source):
        return PostPlanningShadowLifecycle(
            enabled=False,
            armed=False,
            initial_classification="shadow_disabled",
        )
    owner_id = _identity(source.get("JOB_STACK_OWNER_USER_ID"))
    pipeline_run_id = _identity(source.get("JOB_APP_PIPELINE_RUN_ID"))
    explicit_context = str(
        source.get("APPLYLENS_AGENT_CONTEXT_ID", "") or ""
    ).strip()
    context_id = _identity(
        explicit_context
        or (
            f"application_planning:{pipeline_run_id}"
            if pipeline_run_id
            else ""
        )
    )
    if not owner_id or not pipeline_run_id or not context_id:
        return PostPlanningShadowLifecycle(
            enabled=True,
            armed=False,
            initial_classification="shadow_skipped_missing_identity",
        )
    directory = Path(
        tempfile.mkdtemp(prefix="applylens_post_planning_shadow_")
    ).absolute()
    os.chmod(directory, 0o700)
    return PostPlanningShadowLifecycle(
        enabled=True,
        armed=True,
        owner_id=owner_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
        directory=directory,
        projection_path=directory / "resume_evidence.json",
        status_path=directory / "projection_status.json",
        facts_path=directory / "authoritative_facts.json",
        initial_classification="shadow_projection_ready",
    )

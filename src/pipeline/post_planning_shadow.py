"""Default-off, non-authoritative post-planning shadow lifecycle."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
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


def _stop_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=PROCESS_STOP_WAIT_SECONDS)
        return
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=PROCESS_STOP_WAIT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        pass


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
    process = subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=(os.name == "posix"),
        env=_shadow_subprocess_environment(),
    )
    if process.stdout is None or process.stderr is None:
        _stop_process_group(process)
        return {"classification": "shadow_execution_failure"}
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
        _stop_process_group(process)
    finally:
        for reader in readers:
            reader.join(timeout=PROCESS_STOP_WAIT_SECONDS)
        _stop_process_group(process)

    if timed_out:
        return {"classification": "shadow_timeout"}
    if process.returncode != 0 or stdout_state["overflow"] or stderr_state["overflow"]:
        return {"classification": "shadow_execution_failure"}
    try:
        rendered = stdout.decode("utf-8")
    except UnicodeError:
        return {"classification": "shadow_execution_failure"}
    lines = rendered.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        return {"classification": "shadow_execution_failure"}
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError:
        return {"classification": "shadow_execution_failure"}
    return _classify_command_payload(payload)


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
            "classification": "shadow_safety_violation",
            "shadow_write_suppression_violations": 1,
        }

    matches = 0
    mismatches = 0
    for row in results:
        if not isinstance(row, Mapping) or row.get("status") != "parity_completed":
            return {"classification": "shadow_execution_failure"}
        facts = row.get("shadow_facts")
        if (
            not isinstance(facts, Mapping)
            or facts.get("pending_node") != "finalize"
        ):
            return {"classification": "shadow_execution_failure"}
        if (
            facts.get("finalization_executed") is not False
            or facts.get("final_bundle_present") is not False
            or facts.get("final_trace_present") is not False
        ):
            return {
                "classification": "shadow_safety_violation",
                "shadow_write_suppression_violations": 0,
            }
        if facts.get("completed_node_order") != _EXPECTED_NODES:
            return {"classification": "shadow_execution_failure"}
        parity = row.get("parity")
        if (
            not isinstance(parity, Mapping)
            or parity.get("contract_version") != SHADOW_PARITY_VERSION
        ):
            return {"classification": "shadow_execution_failure"}
        classification = parity.get("overall_classification")
        if classification == "match":
            matches += 1
        elif classification == "mismatch":
            mismatches += 1
        else:
            return {"classification": "shadow_execution_failure"}
    return {
        "classification": (
            "parity_mismatch" if mismatches else "shadow_completed"
        ),
        "shadow_parity_matches": matches,
        "shadow_parity_mismatches": mismatches,
        "shadow_completed": len(results),
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
    initial_classification: str = ""
    _cleaned: bool = field(default=False, init=False, repr=False)

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
            if not self.armed:
                return self._observe(outcome, started)
            from src.pipeline.shadow_resume_evidence_projection import (
                ProjectionError,
                load_handoff_status,
                load_projection,
            )

            try:
                status = load_handoff_status(self.status_path)
            except ProjectionError:
                outcome = {"classification": "shadow_projection_failed"}
                return self._observe(outcome, started)
            if status["status"] == "failed":
                outcome = {"classification": "shadow_projection_failed"}
                return self._observe(outcome, started)
            if status["status"] == "skipped":
                outcome = {"classification": "shadow_projection_skipped"}
                return self._observe(outcome, started)
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
                outcome = {"classification": "shadow_projection_failed"}
                return self._observe(outcome, started)
            try:
                load_projection(self.projection_path)
            except (ProjectionError, OSError):
                outcome = {"classification": "shadow_projection_failed"}
                return self._observe(outcome, started)

            output = Path(output_dir)
            facts, skipped_by_limit = build_authoritative_facts(
                execution_queue_path=output
                / "application_execution_queue.csv",
                packet_manifest_path=output / "job_packet_manifest.csv",
                pipeline_run_id=self.pipeline_run_id,
            )
            _atomic_json(self.facts_path, facts)
            outcome = _run_shadow_command(
                self._command(
                    job_corpus_path=job_corpus_path,
                    output_dir=output_dir,
                )
            )
            outcome["shadow_skipped_by_limit"] = skipped_by_limit
            return self._observe(outcome, started)
        except Exception:
            outcome = {"classification": "shadow_execution_failure"}
            return self._observe(outcome, started)
        finally:
            self.cleanup()

    def _observe(
        self, outcome: dict[str, Any], started: float
    ) -> dict[str, Any]:
        classification = str(outcome.get("classification") or "")[:80]
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
        try:
            from src.pipeline.runtime_status import update_counts

            update_counts(**counts)
        except Exception:
            _logger.warning(
                "Post-planning shadow runtime-count update failed"
            )
        _logger.info(
            "Post-planning shadow terminal classification=%s attempted=%s "
            "completed=%s skipped=%s parity_matches=%s parity_mismatches=%s "
            "skipped_by_limit=%s timeout=%s safety_violations=%s "
            "latency_ms=%s contract=%s",
            classification,
            attempted,
            counts["shadow_completed"],
            skipped,
            counts["shadow_parity_matches"],
            counts["shadow_parity_mismatches"],
            counts["shadow_skipped_by_limit"],
            counts["shadow_timeout_count"],
            counts["shadow_write_suppression_violations"],
            latency_ms,
            SHADOW_HOOK_VERSION,
        )
        return {**outcome, **counts}

    def cleanup(self) -> None:
        if self._cleaned:
            return
        self._cleaned = True
        directory = self.directory
        if directory is None:
            return
        try:
            resolved = directory.absolute()
            safe_directory = (
                resolved.name.startswith("applylens_post_planning_shadow_")
                and not resolved.is_symlink()
                and resolved.is_dir()
            )
        except OSError:
            return
        if not safe_directory:
            return
        try:
            children = list(resolved.iterdir())
        except OSError:
            return
        for child in children:
            if child.parent != resolved:
                continue
            try:
                if child.is_symlink() or child.is_file():
                    child.unlink()
            except (FileNotFoundError, OSError):
                pass
        try:
            resolved.rmdir()
        except OSError:
            pass


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

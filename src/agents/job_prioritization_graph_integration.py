from __future__ import annotations

from copy import deepcopy
import signal
import threading
import time
from typing import Any, Dict, List, Mapping

from src.agents.job_prioritization_agent import trace_context_from_env


GRAPH_VERIFICATION_TIMEOUT_SECONDS = 5
MAX_GRAPH_VERIFICATION_ROWS = 10
VERIFICATION_CLASSIFICATIONS = frozenset(
    {
        "matched",
        "mismatch",
        "timeout",
        "exception",
        "skipped_disabled",
        "skipped_invalid_identity",
        "skipped_row_bound",
        "duplicate_suppressed",
    }
)

_SEEN_INVOCATION_IDENTITIES: set[str] = set()
_SEEN_INVOCATION_IDENTITIES_LOCK = threading.Lock()


class GraphVerificationTimeoutError(TimeoutError):
    pass


class GraphVerificationTimeoutBoundaryUnavailable(RuntimeError):
    pass


class GraphVerificationTimeoutCleanupError(RuntimeError):
    pass


def _bounded_elapsed_ms(started_at: float) -> int:
    return max(0, min(int(round((time.monotonic() - started_at) * 1000)), 300_000))


def _summary(
    *,
    classification: str,
    input_row_count: int,
    enabled: bool = True,
    attempted: bool = False,
    completed: bool = False,
    output_row_count: int = 0,
    parity_matched: bool = False,
    timeout_count: int = 0,
    exception_count: int = 0,
    duplicate_suppressed_count: int = 0,
    elapsed_ms: int = 0,
    safety_violation_count: int = 0,
    rollback_required: bool = False,
    graph_input_mutation_count: int = 0,
    caller_input_mutation_count: int = 0,
    authoritative_direct_mutation_count: int = 0,
    output_mismatch_count: int = 0,
) -> Dict[str, Any]:
    if classification not in VERIFICATION_CLASSIFICATIONS:
        raise ValueError("unsupported_graph_verification_classification")
    return {
        "enabled": enabled,
        "attempted": attempted,
        "completed": completed,
        "classification": classification,
        "input_row_count": max(0, min(input_row_count, 1_000_000)),
        "output_row_count": max(0, min(output_row_count, 1_000_000)),
        "parity_matched": parity_matched,
        "timeout_count": timeout_count,
        "exception_count": exception_count,
        "duplicate_suppressed_count": duplicate_suppressed_count,
        "elapsed_ms": elapsed_ms,
        "direct_output_authoritative": True,
        "graph_output_applied": False,
        "safety_violation_count": safety_violation_count,
        "rollback_required": rollback_required,
        "graph_input_mutation_count": graph_input_mutation_count,
        "caller_input_mutation_count": caller_input_mutation_count,
        "authoritative_direct_mutation_count": (
            authoritative_direct_mutation_count
        ),
        "output_mismatch_count": output_mismatch_count,
    }


def build_disabled_job_prioritization_graph_verification_summary(
    *,
    input_row_count: int,
) -> Dict[str, Any]:
    """Build the inert disabled status without importing or executing the graph."""

    return _summary(
        classification="skipped_disabled",
        input_row_count=input_row_count,
        enabled=False,
    )


def _run_with_signal_timeout(callback: Any) -> Any:
    if (
        threading.current_thread() is not threading.main_thread()
        or not hasattr(signal, "SIGALRM")
        or not hasattr(signal, "ITIMER_REAL")
    ):
        raise GraphVerificationTimeoutBoundaryUnavailable(
            "safe_timeout_boundary_unavailable"
        )

    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    if previous_timer != (0.0, 0.0):
        raise GraphVerificationTimeoutBoundaryUnavailable(
            "existing_interval_timer_active"
        )
    previous_handler = signal.getsignal(signal.SIGALRM)

    def _timeout_handler(signum: int, frame: Any) -> None:
        del signum, frame
        raise GraphVerificationTimeoutError("graph_verification_timeout")

    signal.signal(signal.SIGALRM, _timeout_handler)
    try:
        signal.setitimer(
            signal.ITIMER_REAL,
            GRAPH_VERIFICATION_TIMEOUT_SECONDS,
        )
        return callback()
    finally:
        cleanup_failed = False
        try:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        except BaseException:
            cleanup_failed = True
        try:
            signal.signal(signal.SIGALRM, previous_handler)
        except BaseException:
            cleanup_failed = True
        if cleanup_failed:
            raise GraphVerificationTimeoutCleanupError(
                "graph_verification_timeout_cleanup_failed"
            )


def verify_direct_job_prioritization_rows(
    *,
    rows: List[Mapping[str, Any]],
    direct_rendered_rows: List[Mapping[str, Any]],
    source_artifact_reference: str,
    env: Mapping[str, str],
) -> Dict[str, Any]:
    """Compare one bounded graph result while preserving direct authority."""

    started_at = time.monotonic()
    input_row_count = len(rows) if isinstance(rows, list) else 0
    if input_row_count < 1 or input_row_count > MAX_GRAPH_VERIFICATION_ROWS:
        return _summary(
            classification="skipped_row_bound",
            input_row_count=input_row_count,
            elapsed_ms=_bounded_elapsed_ms(started_at),
        )

    caller_rows_before = deepcopy(rows)
    authoritative_direct_rows = deepcopy(direct_rendered_rows)
    identity_rows = deepcopy(rows)
    identity_rows_before = deepcopy(identity_rows)

    context = trace_context_from_env(dict(env))
    if not all(
        str(context.get(key) or "").strip()
        for key in ("pipeline_run_id", "owner_user_id", "context_id")
    ):
        return _summary(
            classification="skipped_invalid_identity",
            input_row_count=input_row_count,
            elapsed_ms=_bounded_elapsed_ms(started_at),
        )

    try:
        from src.agents import job_prioritization_graph_verification as graph_contract

        identity = (
            graph_contract.build_job_prioritization_graph_verification_identity(
                rows=identity_rows,
                pipeline_run_id=context["pipeline_run_id"],
                owner_user_id=context["owner_user_id"],
                context_id=context["context_id"],
            )
        )
    except Exception:
        graph_input_mutation_count = int(identity_rows != identity_rows_before)
        caller_input_mutation_count = int(rows != caller_rows_before)
        authoritative_direct_mutation_count = int(
            direct_rendered_rows != authoritative_direct_rows
        )
        safety_violation_count = (
            graph_input_mutation_count
            + caller_input_mutation_count
            + authoritative_direct_mutation_count
        )
        return _summary(
            classification="exception",
            input_row_count=input_row_count,
            exception_count=1,
            elapsed_ms=_bounded_elapsed_ms(started_at),
            safety_violation_count=safety_violation_count,
            rollback_required=safety_violation_count > 0,
            graph_input_mutation_count=graph_input_mutation_count,
            caller_input_mutation_count=caller_input_mutation_count,
            authoritative_direct_mutation_count=(
                authoritative_direct_mutation_count
            ),
        )

    if identity_rows != identity_rows_before:
        return _summary(
            classification="mismatch",
            input_row_count=input_row_count,
            elapsed_ms=_bounded_elapsed_ms(started_at),
            safety_violation_count=1,
            rollback_required=True,
            graph_input_mutation_count=1,
        )

    invocation_identity = str(identity["invocation_identity"])
    with _SEEN_INVOCATION_IDENTITIES_LOCK:
        if invocation_identity in _SEEN_INVOCATION_IDENTITIES:
            return _summary(
                classification="duplicate_suppressed",
                input_row_count=input_row_count,
                duplicate_suppressed_count=1,
                elapsed_ms=_bounded_elapsed_ms(started_at),
            )
        _SEEN_INVOCATION_IDENTITIES.add(invocation_identity)

    graph_call_rows = deepcopy(rows)
    graph_call_rows_before = deepcopy(graph_call_rows)

    def _owned_mutation_counts() -> tuple[int, int, int]:
        return (
            int(graph_call_rows != graph_call_rows_before),
            int(rows != caller_rows_before),
            int(direct_rendered_rows != authoritative_direct_rows),
        )

    def _execute_graph() -> Dict[str, Any]:
        return graph_contract.execute_job_prioritization_graph_verification(
            rows=graph_call_rows,
            pipeline_run_id=context["pipeline_run_id"],
            owner_user_id=context["owner_user_id"],
            context_id=context["context_id"],
            source_artifact_reference=source_artifact_reference,
        )

    try:
        result = _run_with_signal_timeout(_execute_graph)
    except GraphVerificationTimeoutError:
        (
            graph_input_mutation_count,
            caller_input_mutation_count,
            authoritative_direct_mutation_count,
        ) = _owned_mutation_counts()
        safety_violation_count = (
            graph_input_mutation_count
            + caller_input_mutation_count
            + authoritative_direct_mutation_count
        )
        return _summary(
            classification="timeout",
            input_row_count=input_row_count,
            attempted=True,
            timeout_count=1,
            elapsed_ms=_bounded_elapsed_ms(started_at),
            safety_violation_count=safety_violation_count,
            rollback_required=safety_violation_count > 0,
            graph_input_mutation_count=graph_input_mutation_count,
            caller_input_mutation_count=caller_input_mutation_count,
            authoritative_direct_mutation_count=(
                authoritative_direct_mutation_count
            ),
        )
    except GraphVerificationTimeoutCleanupError:
        (
            graph_input_mutation_count,
            caller_input_mutation_count,
            authoritative_direct_mutation_count,
        ) = _owned_mutation_counts()
        return _summary(
            classification="exception",
            input_row_count=input_row_count,
            attempted=True,
            exception_count=1,
            elapsed_ms=_bounded_elapsed_ms(started_at),
            safety_violation_count=(
                1
                + graph_input_mutation_count
                + caller_input_mutation_count
                + authoritative_direct_mutation_count
            ),
            rollback_required=True,
            graph_input_mutation_count=graph_input_mutation_count,
            caller_input_mutation_count=caller_input_mutation_count,
            authoritative_direct_mutation_count=(
                authoritative_direct_mutation_count
            ),
        )
    except Exception:
        (
            graph_input_mutation_count,
            caller_input_mutation_count,
            authoritative_direct_mutation_count,
        ) = _owned_mutation_counts()
        safety_violation_count = (
            graph_input_mutation_count
            + caller_input_mutation_count
            + authoritative_direct_mutation_count
        )
        return _summary(
            classification="exception",
            input_row_count=input_row_count,
            attempted=True,
            exception_count=1,
            elapsed_ms=_bounded_elapsed_ms(started_at),
            safety_violation_count=safety_violation_count,
            rollback_required=safety_violation_count > 0,
            graph_input_mutation_count=graph_input_mutation_count,
            caller_input_mutation_count=caller_input_mutation_count,
            authoritative_direct_mutation_count=(
                authoritative_direct_mutation_count
            ),
        )

    graph_rows = result.get("rendered_recommendation_rows")
    safety_metadata = result.get("safety_metadata")
    safety_violation_count = 0
    (
        graph_input_mutation_count,
        caller_input_mutation_count,
        authoritative_direct_mutation_count,
    ) = _owned_mutation_counts()
    safety_violation_count += (
        graph_input_mutation_count
        + caller_input_mutation_count
        + authoritative_direct_mutation_count
    )
    if not isinstance(safety_metadata, Mapping):
        safety_violation_count += 1
    else:
        expected_safety_metadata = graph_contract.SAFETY_METADATA
        safety_violation_count += sum(
            1
            for key, expected_value in expected_safety_metadata.items()
            if safety_metadata.get(key) is not expected_value
        )
        safety_violation_count += sum(
            1
            for key in safety_metadata
            if key not in expected_safety_metadata
        )
    if result.get("input_unchanged") is not True:
        safety_violation_count += 1
    output_mismatch_count = int(graph_rows != authoritative_direct_rows)
    parity_matched = output_mismatch_count == 0
    classification = (
        "matched"
        if parity_matched and safety_violation_count == 0
        else "mismatch"
    )
    return _summary(
        classification=classification,
        input_row_count=input_row_count,
        attempted=True,
        completed=bool(result.get("completed")),
        output_row_count=len(graph_rows) if isinstance(graph_rows, list) else 0,
        parity_matched=parity_matched and safety_violation_count == 0,
        elapsed_ms=_bounded_elapsed_ms(started_at),
        safety_violation_count=safety_violation_count,
        rollback_required=classification == "mismatch",
        graph_input_mutation_count=graph_input_mutation_count,
        caller_input_mutation_count=caller_input_mutation_count,
        authoritative_direct_mutation_count=(
            authoritative_direct_mutation_count
        ),
        output_mismatch_count=output_mismatch_count,
    )


def _reset_process_local_duplicate_suppression_for_tests() -> None:
    with _SEEN_INVOCATION_IDENTITIES_LOCK:
        _SEEN_INVOCATION_IDENTITIES.clear()

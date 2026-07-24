"""Test-only process worker for the Phase 9 durable restart proof."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents import evidence_chain_langgraph_harness as harness
from src.agents.durable_evidence_chain_resume_coordinator import (
    DurableEvidenceChainResumeCoordinator,
)
from src.storage.durable_orchestration import (
    langgraph_postgres,
    postgres_connection,
    repository,
)


REPOSITORY_TARGET = "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
SAVER_TARGET = "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_TEST_DATABASE_URL"
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9:._-]{0,255}")
MODES = frozenset({"pause", "resume", "replay", "wrong-owner", "inspect", "cleanup"})
TOKEN_HASH = "7" * 64
NOW = "2026-07-25T12:00:00Z"
CLAIMED_AT = "2026-07-25T12:05:00Z"
COMPLETED_AT = "2026-07-25T12:10:00Z"
LEASE_EXPIRES_AT = "2026-07-25T12:15:00Z"
AUTHORIZATION_EXPIRES_AT = "2026-07-25T13:00:00Z"
TABLES = (
    "orchestration_lifecycle_events",
    "orchestration_terminal_results",
    "orchestration_node_attempts",
    "orchestration_resume_consumptions",
    "orchestration_resume_authorizations",
    "orchestration_human_decisions",
    "orchestration_interrupt_requests",
    "orchestration_checkpoints",
    "orchestration_graph_runs",
)


def _safe(value: str, name: str, *, required: bool = True) -> str:
    normalized = str(value or "").strip()
    if required and not normalized:
        raise ValueError(f"{name}_required")
    if normalized and SAFE_ID.fullmatch(normalized) is None:
        raise ValueError(f"{name}_invalid")
    return normalized


def _targets() -> tuple[str, str]:
    repository_target = str(os.environ.get(REPOSITORY_TARGET, "") or "").strip()
    saver_target = str(os.environ.get(SAVER_TARGET, "") or "").strip()
    if not repository_target or not saver_target:
        raise ValueError("dedicated_test_targets_required")
    return repository_target, saver_target


def _factory(target: str):
    return postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase9-step18b-process-worker",
    )


def _initial_state(owner: str):
    job = {
        "job_id": "job-phase9-step18b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "url": "https://example.test/jobs/phase9-step18b",
        "intelligence": {
            "skills": {
                "required": ["Python", "SQL"],
                "preferred": ["RAG"],
                "all": ["Python", "SQL", "RAG"],
            },
            "visa_sponsorship": "unknown",
        },
        "ai_fit_score": 8,
        "priority_score": 12.5,
    }
    return harness._build_initial_graph_state(
        job=job,
        job_index=0,
        job_identity=harness._job_identity(job, 0),
        resume_rows=[
            {
                "resume_id": "resume-phase9-step18b",
                "skills": ["Python", "SQL", "RAG"],
                "raw_text": "Built Python, SQL, and RAG systems.",
            }
        ],
        selected_resume_id="resume-phase9-step18b",
        pipeline_run_id="run-phase9-step18b",
        owner_user_id=owner,
        context_id="context-phase9-step18b",
        include_trace_payload=True,
    )


def _counts(factory: Any, owner: str, graph_id: str) -> dict[str, int]:
    connection = factory()
    cursor = connection.cursor()
    try:
        result = {}
        for table in TABLES:
            cursor.execute(
                f"SELECT count(*) AS record_count FROM {table} "
                "WHERE owner_user_id = %(owner_user_id)s "
                "AND graph_invocation_id = %(graph_invocation_id)s",
                {"owner_user_id": owner, "graph_invocation_id": graph_id},
            )
            result[table] = int(cursor.fetchall()[0]["record_count"])
        connection.rollback()
        return result
    finally:
        cursor.close()
        connection.close()


def _delete_exact(factory: Any, owner: str, graph_id: str) -> int:
    connection = factory()
    cursor = connection.cursor()
    removed = 0
    try:
        for table in TABLES:
            cursor.execute(
                f"DELETE FROM {table} "
                "WHERE owner_user_id = %(owner_user_id)s "
                "AND graph_invocation_id = %(graph_invocation_id)s",
                {"owner_user_id": owner, "graph_invocation_id": graph_id},
            )
            removed += max(cursor.rowcount, 0)
        connection.commit()
        return removed
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def _count_nodes():
    names = (
        "_jd_intelligence_node",
        "_resume_match_node",
        "_critic_node",
        "_job_prioritization_node",
        "_tailoring_decision_node",
        "_operator_review_node",
        "_finalize_node",
    )
    calls = {name: 0 for name in names}
    originals = {}
    for name in names:
        original = getattr(harness, name)
        originals[name] = original

        def counted(state, *, _name=name, _original=original):
            calls[_name] += 1
            return _original(state)

        setattr(harness, name, counted)
    return names, calls, originals


def _restore_nodes(originals):
    for name, original in originals.items():
        setattr(harness, name, original)


def _pause(owner: str, repository_target: str, saver_target: str) -> dict[str, Any]:
    state = _initial_state(owner)
    identity = harness._build_checkpoint_envelope(state)["checkpoint_identity"]
    graph_id = identity["graph_invocation_id"]
    base_config = {
        "configurable": {
            "thread_id": graph_id,
            "checkpoint_ns": "",
            "applylens_checkpoint_namespace": (
                harness.LANGGRAPH_OPERATOR_REVIEW_PAUSE_RESUME_CHECKPOINT_NAMESPACE
            ),
        }
    }
    factory = _factory(repository_target)
    names, calls, originals = _count_nodes()
    try:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase9-step18b-pause",
        ) as saver:
            graph = harness._compile_operator_review_pause_resume_graph(saver)
            coordinator = DurableEvidenceChainResumeCoordinator(
                repository=repository.DurableOrchestrationRepository(
                    factory, enabled=True
                ),
                saver=saver,
                graph=graph,
                enabled=True,
            )
            result = coordinator.create_durable_pause(
                initial_state=state,
                base_config=base_config,
                created_at=NOW,
                committed_at=NOW,
            )
            snapshot = graph.get_state(base_config)
            harness._validate_paused_operator_review_state(snapshot.values)
        counts = _counts(factory, owner, graph_id)
        if any(calls[name] != 1 for name in names[:-1]) or calls[names[-1]] != 0:
            raise ValueError("pause_node_execution_invalid")
        if any(
            counts[table] != 0
            for table in (
                "orchestration_human_decisions",
                "orchestration_resume_authorizations",
                "orchestration_resume_consumptions",
                "orchestration_node_attempts",
                "orchestration_terminal_results",
            )
        ):
            raise ValueError("pause_repository_state_invalid")
        return {
            "mode": "pause",
            "pid": os.getpid(),
            "status": result.status,
            "classification": result.classification,
            "owner_user_id": owner,
            "graph_invocation_id": result.graph_invocation_id,
            "repository_checkpoint_id": result.repository_checkpoint_id,
            "interrupt_request_id": result.interrupt_request_id,
            "evidence_nodes_executed": sum(calls[name] for name in names[:-1]),
            "finalize_nodes_executed": calls[names[-1]],
        }
    finally:
        _restore_nodes(originals)


def _coordinator_mode(
    mode: str,
    owner: str,
    graph_id: str,
    checkpoint_id: str,
    interrupt_id: str,
    repository_target: str,
    saver_target: str,
) -> dict[str, Any]:
    factory = _factory(repository_target)
    names, calls, originals = _count_nodes()
    try:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name=f"applylens-phase9-step18b-{mode}",
        ) as saver:
            graph = harness._compile_operator_review_pause_resume_graph(saver)
            coordinator = DurableEvidenceChainResumeCoordinator(
                repository=repository.DurableOrchestrationRepository(
                    factory, enabled=True
                ),
                saver=saver,
                graph=graph,
                enabled=True,
            )
            if mode == "wrong-owner":
                result = coordinator.reopen_durable_pause(
                    owner_user_id=owner,
                    graph_invocation_id=graph_id,
                    repository_checkpoint_id=checkpoint_id,
                )
            else:
                result = coordinator.resume_paused_workflow(
                    owner_user_id=owner,
                    graph_invocation_id=graph_id,
                    repository_checkpoint_id=checkpoint_id,
                    interrupt_request_id=interrupt_id,
                    actor_id="actor-phase9-step18b",
                    client_idempotency_key="client-phase9-step18b",
                    decision_reason="approved read-only continuation",
                    authorization_token_hash=TOKEN_HASH,
                    consumer_instance_id="worker-phase9-step18b",
                    created_at=NOW,
                    authorization_expires_at=AUTHORIZATION_EXPIRES_AT,
                    lease_acquired_at=CLAIMED_AT,
                    lease_expires_at=LEASE_EXPIRES_AT,
                    completed_at=COMPLETED_AT,
                    duration_ms=300_000,
                )
        return {
            "mode": mode,
            "pid": os.getpid(),
            "status": result.status,
            "classification": result.classification,
            "graph_invocation_id": result.graph_invocation_id,
            "repository_checkpoint_id": result.repository_checkpoint_id,
            "attempt_id": result.attempt_id,
            "terminal_result_id": result.terminal_result_id,
            "evidence_nodes_executed": sum(calls[name] for name in names[:-1]),
            "finalize_nodes_executed": calls[names[-1]],
        }
    finally:
        _restore_nodes(originals)


def _inspect(
    owner: str,
    graph_id: str,
    checkpoint_id: str,
    repository_target: str,
    saver_target: str,
) -> dict[str, Any]:
    factory = _factory(repository_target)
    executor = repository.DurableOrchestrationRepository(factory, enabled=True)
    graph_result = executor.read_graph_run(
        owner_user_id=owner, graph_invocation_id=graph_id
    )
    binding_result = executor.read_checkpoint_binding(
        owner_user_id=owner,
        graph_invocation_id=graph_id,
        repository_checkpoint_id=checkpoint_id,
    )
    counts = _counts(factory, owner, graph_id)
    with langgraph_postgres.open_langgraph_postgres_saver(
        enabled=True,
        database_url=saver_target,
        application_name="applylens-phase9-step18b-inspect",
    ) as saver:
        graph = harness._compile_operator_review_pause_resume_graph(saver)
        snapshot = graph.get_state(
            {"configurable": {"thread_id": graph_id, "checkpoint_ns": ""}}
        )
        artifacts = dict(snapshot.values.get("artifacts") or {})
        next_nodes = list(snapshot.next)
        completed_evidence = list(snapshot.values.get("ordered_node_keys") or [])
    return {
        "mode": "inspect",
        "pid": os.getpid(),
        "classification": graph_result.classification,
        "run_status": (
            graph_result.record.get("run_status") if graph_result.record else ""
        ),
        "current_checkpoint_id": (
            graph_result.record.get("current_checkpoint_id")
            if graph_result.record
            else ""
        ),
        "binding_status": binding_result.classification,
        "pending_finalize": next_nodes == ["finalize"],
        "pending_node_count": len(next_nodes),
        "completed_evidence_count": len(completed_evidence),
        "final_bundle_present": "agent_evidence_chain_bundle" in artifacts,
        "final_trace_present": "agent_evidence_chain_trace_payload" in artifacts,
        "graph_run_count": counts["orchestration_graph_runs"],
        "checkpoint_count": counts["orchestration_checkpoints"],
        "decision_count": counts["orchestration_human_decisions"],
        "authorization_count": counts["orchestration_resume_authorizations"],
        "consumption_count": counts["orchestration_resume_consumptions"],
        "attempt_count": counts["orchestration_node_attempts"],
        "terminal_count": counts["orchestration_terminal_results"],
    }


def _cleanup(
    owner: str,
    graph_id: str,
    repository_target: str,
    saver_target: str,
) -> dict[str, Any]:
    factory = _factory(repository_target)
    removed = _delete_exact(factory, owner, graph_id)
    with langgraph_postgres.open_langgraph_postgres_saver(
        enabled=True,
        database_url=saver_target,
        application_name="applylens-phase9-step18b-cleanup",
    ) as saver:
        saver.delete_thread(graph_id)
    remaining = sum(_counts(factory, owner, graph_id).values())
    if remaining:
        raise ValueError("cleanup_incomplete")
    return {
        "mode": "cleanup",
        "pid": os.getpid(),
        "status": "cleaned",
        "removed_repository_rows": removed,
        "remaining_repository_rows": remaining,
    }


def _run(arguments: list[str]) -> dict[str, Any]:
    if len(arguments) < 2:
        raise ValueError("mode_and_owner_required")
    mode = _safe(arguments[0], "mode")
    if mode not in MODES:
        raise ValueError("mode_unsupported")
    owner = _safe(arguments[1], "owner_user_id")
    graph_id = _safe(arguments[2] if len(arguments) > 2 else "", "graph_invocation_id", required=False)
    checkpoint_id = _safe(arguments[3] if len(arguments) > 3 else "", "repository_checkpoint_id", required=False)
    interrupt_id = _safe(arguments[4] if len(arguments) > 4 else "", "interrupt_request_id", required=False)
    if mode == "pause":
        if len(arguments) != 2:
            raise ValueError("pause_arguments_invalid")
        repository_target, saver_target = _targets()
        return _pause(owner, repository_target, saver_target)
    if not graph_id:
        raise ValueError("graph_invocation_id_required")
    if mode == "cleanup":
        if len(arguments) != 3:
            raise ValueError("cleanup_arguments_invalid")
        repository_target, saver_target = _targets()
        return _cleanup(owner, graph_id, repository_target, saver_target)
    if mode == "inspect":
        if len(arguments) != 4 or not checkpoint_id:
            raise ValueError("inspect_arguments_invalid")
        repository_target, saver_target = _targets()
        return _inspect(
            owner, graph_id, checkpoint_id, repository_target, saver_target
        )
    if len(arguments) != 5 or not checkpoint_id or not interrupt_id:
        raise ValueError("resume_arguments_invalid")
    repository_target, saver_target = _targets()
    return _coordinator_mode(
        mode,
        owner,
        graph_id,
        checkpoint_id,
        interrupt_id,
        repository_target,
        saver_target,
    )


def main() -> int:
    try:
        output = _run(sys.argv[1:])
    except Exception as exc:
        reason = str(exc)
        if SAFE_ID.fullmatch(reason) is None:
            reason = "worker_failure"
        print(
            json.dumps(
                {
                    "mode": "error",
                    "status": "failed",
                    "classification": "non_retryable_failure",
                    "reason_code": reason,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

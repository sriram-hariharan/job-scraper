from __future__ import annotations

import ast
from copy import deepcopy
import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.agents.durable_evidence_chain_resume_coordinator import (
    DurableEvidenceChainResumeCoordinator,
    DurableResumeResult,
)
from src.agents import evidence_chain_langgraph_harness as harness
from src.storage.durable_orchestration import (
    langgraph_postgres,
    postgres_connection,
    repository,
    store,
)
from tests.test_phase9_step16a_durable_decision_authorization_runtime_contract import (
    _cleanup,
    _counts,
)


SOURCE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "agents"
    / "durable_evidence_chain_resume_coordinator.py"
)
LIVE_GATE = "APPLYLENS_DURABLE_ORCHESTRATION_RESTART_RESUME_TEST_ENABLED"
REPOSITORY_TARGET = "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
SAVER_TARGET = "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_TEST_DATABASE_URL"


@dataclass
class _RepositoryResult:
    classification: str
    record: dict | None = None


class _Repository:
    def __init__(self, *, run_status="resumed", attempt_status="claimed"):
        self.run_status = run_status
        self.attempt_status = attempt_status

    def read_graph_run(self, **_):
        return _RepositoryResult(
            "applied",
            {
                "run_status": self.run_status,
                "current_checkpoint_id": "repository-pause",
            },
        )

    def read_resume_consumption(self, **_):
        return _RepositoryResult(
            "applied", {"resume_invocation_id": "resume-invocation"}
        )

    def read_attempt(self, **_):
        return _RepositoryResult(
            "applied",
            {
                "attempt_status": self.attempt_status,
                "lease_owner_id": "worker-a",
                "node_key": "finalize",
            },
        )

    def read_checkpoint_binding(self, **_):
        return _RepositoryResult(
            "applied",
            {
                "event_payload_json": {
                    "langgraph_thread_id": "thread-a",
                    "langgraph_checkpoint_namespace": "",
                    "langgraph_checkpoint_id": "package-pause",
                }
            },
        )


class _NeverInvokedGraph:
    def __init__(self):
        self.invoke_count = 0
        self.get_state_count = 0

    def invoke(self, *_args, **_kwargs):
        self.invoke_count += 1
        raise AssertionError("graph invocation must be rejected")

    def get_state(self, *_args, **_kwargs):
        self.get_state_count += 1
        raise AssertionError("saver lookup must be rejected")


def _coordinator(repository, graph):
    return DurableEvidenceChainResumeCoordinator(
        repository=repository,
        saver=object(),
        graph=graph,
        enabled=True,
    )


def _resume(coordinator):
    return coordinator.resume_claimed_attempt(
        owner_user_id="owner-a",
        graph_invocation_id="graph-a",
        repository_checkpoint_id="repository-pause",
        authorization_id="authorization-a",
        attempt_id="attempt-a",
        lease_owner_id="worker-a",
        persist_final_state=lambda *_: DurableResumeResult(
            status="resume_completed", classification="applied"
        ),
    )


def test_coordinator_is_explicit_and_defaults_off():
    with pytest.raises(ValueError, match="not_enabled"):
        DurableEvidenceChainResumeCoordinator(
            repository=object(), saver=object(), graph=object()
        )
    for missing in ("repository", "saver", "graph"):
        dependencies = {
            "repository": object(),
            "saver": object(),
            "graph": object(),
        }
        dependencies[missing] = None
        with pytest.raises(ValueError, match="required"):
            DurableEvidenceChainResumeCoordinator(
                **dependencies, enabled=True
            )


def test_module_has_no_environment_or_import_time_resource_ownership():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "os.environ" not in source
    assert "getenv(" not in source
    assert "load_dotenv" not in source
    assert "DATABASE_URL" not in source
    assert "application_action" not in source
    assert "pipeline" not in source.lower()
    assert "llm" not in source.lower()
    assert "retry(" not in source.lower()
    assignments = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    assert all(
        not any(
            marker in ast.unparse(node).lower()
            for marker in ("repository =", "saver =", "graph =", "pool =")
        )
        for node in assignments
    )


def test_wrong_owner_fails_closed_before_saver_or_graph_use():
    class MissingRepository(_Repository):
        def read_graph_run(self, **_):
            return _RepositoryResult("not_found")

    graph = _NeverInvokedGraph()
    result = _resume(_coordinator(MissingRepository(), graph))
    assert result.status == "resume_attempted"
    assert result.classification == "not_found"
    assert graph.get_state_count == graph.invoke_count == 0


def test_stale_checkpoint_fails_before_saver_or_graph_use():
    repository = _Repository()
    repository.read_graph_run = lambda **_: _RepositoryResult(
        "applied",
        {
            "run_status": "resumed",
            "current_checkpoint_id": "different-checkpoint",
        },
    )
    graph = _NeverInvokedGraph()
    result = _resume(_coordinator(repository, graph))
    assert result.classification == "stale_state"
    assert graph.get_state_count == graph.invoke_count == 0


def test_resume_requires_consumption_before_saver_or_graph_use():
    class UnconsumedRepository(_Repository):
        def read_resume_consumption(self, **_):
            return _RepositoryResult("not_found")

    graph = _NeverInvokedGraph()
    result = _resume(_coordinator(UnconsumedRepository(), graph))
    assert result.classification == "stale_state"
    assert graph.get_state_count == graph.invoke_count == 0


def test_resume_requires_exact_claimed_attempt_before_saver_or_graph_use():
    graph = _NeverInvokedGraph()
    result = _resume(
        _coordinator(_Repository(attempt_status="pending"), graph)
    )
    assert result.classification == "stale_state"
    assert graph.get_state_count == graph.invoke_count == 0


def test_completed_run_rejects_replay_before_saver_or_graph_use():
    graph = _NeverInvokedGraph()
    result = _resume(_coordinator(_Repository(run_status="completed"), graph))
    assert result.status == "already_completed"
    assert result.classification == "already_completed"
    assert graph.get_state_count == graph.invoke_count == 0


def test_live_postgres_restart_resume_requires_all_three_explicit_targets(
    monkeypatch,
):
    if os.environ.get(LIVE_GATE) != "1":
        pytest.skip("explicit Step 17 restart-resume gate is disabled")
    if not os.environ.get(REPOSITORY_TARGET) or not os.environ.get(SAVER_TARGET):
        pytest.skip("both dedicated Step 17 PostgreSQL targets are required")
    repository_target = os.environ[REPOSITORY_TARGET]
    saver_target = os.environ[SAVER_TARGET]
    for prohibited in (
        os.environ.get("DATABASE_URL"),
        os.environ.get("APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL"),
        os.environ.get(
            "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_DATABASE_URL"
        ),
    ):
        if prohibited and prohibited in {repository_target, saver_target}:
            pytest.fail("dedicated Step 17 database target aliases application target")

    owner = "owner-phase9-step17"
    wrong_owner = "owner-phase9-step17-wrong"
    now = "2026-07-25T12:00:00Z"
    claimed_at = "2026-07-25T12:05:00Z"
    lease_expires = "2026-07-25T12:15:00Z"
    completed_at = "2026-07-25T12:10:00Z"
    token_hash = "7" * 64
    worker = "worker-phase9-step17"
    job = {
        "job_id": "job-phase9-step17",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "url": "https://example.test/jobs/phase9-step17",
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
    initial_state = harness._build_initial_graph_state(
        job=job,
        job_index=0,
        job_identity=harness._job_identity(job, 0),
        resume_rows=[
            {
                "resume_id": "resume-phase9-step17",
                "skills": ["Python", "SQL", "RAG"],
                "raw_text": "Built Python, SQL, and RAG systems.",
            }
        ],
        selected_resume_id="resume-phase9-step17",
        pipeline_run_id="run-phase9-step17",
        owner_user_id=owner,
        context_id="context-phase9-step17",
        include_trace_payload=True,
    )
    initial_envelope = harness._build_checkpoint_envelope(initial_state)
    identity = dict(initial_envelope["checkpoint_identity"])
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
    node_names = (
        "_jd_intelligence_node",
        "_resume_match_node",
        "_critic_node",
        "_job_prioritization_node",
        "_tailoring_decision_node",
        "_operator_review_node",
        "_finalize_node",
    )
    calls = {name: 0 for name in node_names}
    for node_name in node_names:
        original = getattr(harness, node_name)

        def counted(state, *, _name=node_name, _original=original):
            calls[_name] += 1
            return _original(state)

        monkeypatch.setattr(harness, node_name, counted)
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=repository_target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase9-step17-repository",
    )
    unrelated_before = _counts(
        factory, owner=wrong_owner, graph_id="unrelated-step17"
    )
    _cleanup(factory, owner=owner, graph_id=graph_id)
    pause = None
    try:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase9-step17-pause",
        ) as first_saver:
            first_saver.delete_thread(graph_id)
            first_repository = repository.DurableOrchestrationRepository(
                factory, enabled=True
            )
            first_graph = harness._compile_operator_review_pause_resume_graph(
                first_saver
            )
            first_coordinator = DurableEvidenceChainResumeCoordinator(
                repository=first_repository,
                saver=first_saver,
                graph=first_graph,
                enabled=True,
            )
            pause = first_coordinator.create_durable_pause(
                initial_state=initial_state,
                base_config=base_config,
                created_at=now,
                committed_at=now,
            )
            assert pause.status == "durable_pause_created"
            assert pause.classification == "applied"
            first_connection = first_saver.conn
        assert first_connection.closed
        del first_coordinator, first_graph, first_repository, first_saver

        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase9-step17-resume",
        ) as second_saver:
            second_factory = postgres_connection.build_postgres_connection_factory(
                enabled=True,
                database_url=repository_target,
                connect_timeout_seconds=5,
                statement_timeout_ms=10_000,
                application_name="applylens-phase9-step17-reopened-repository",
            )
            second_repository = repository.DurableOrchestrationRepository(
                second_factory, enabled=True
            )
            second_graph = harness._compile_operator_review_pause_resume_graph(
                second_saver
            )
            coordinator = DurableEvidenceChainResumeCoordinator(
                repository=second_repository,
                saver=second_saver,
                graph=second_graph,
                enabled=True,
            )
            reopened = coordinator.reopen_durable_pause(
                owner_user_id=owner,
                graph_invocation_id=graph_id,
                repository_checkpoint_id=pause.repository_checkpoint_id,
            )
            assert reopened.status == "durable_pause_reopened"
            assert coordinator.reopen_durable_pause(
                owner_user_id=wrong_owner,
                graph_invocation_id=graph_id,
                repository_checkpoint_id=pause.repository_checkpoint_id,
            ).classification == "not_found"

            paused_config = {
                "configurable": {
                    "thread_id": reopened.langgraph_thread_id,
                    "checkpoint_ns": reopened.langgraph_checkpoint_namespace,
                    "checkpoint_id": reopened.langgraph_checkpoint_id,
                }
            }
            paused_snapshot = second_graph.get_state(paused_config)
            paused_state = dict(paused_snapshot.values)
            paused_envelope = harness._build_checkpoint_envelope(paused_state)
            graph_run = store.prepare_graph_run_row(
                initial_envelope, created_at=now
            )
            checkpoint = store.prepare_checkpoint_row(
                paused_envelope, committed_at=now
            )
            interrupt = store.prepare_interrupt_request_row(
                harness._build_operator_review_interrupt_request(
                    paused_state,
                    checkpoint_identity=paused_envelope["checkpoint_identity"],
                ),
                checkpoint_envelope=paused_envelope,
                created_at=now,
            )
            decision = store.prepare_human_decision_row(
                interrupt,
                decision_value="continue_read_only",
                actor_id="actor-phase9-step17",
                client_idempotency_key="client-phase9-step17",
                expected_interrupt_version=0,
                expected_run_lock_version=1,
                created_at=now,
                reason="approved read-only continuation",
            )
            assert second_repository.record_human_decision(
                decision
            ).classification == "applied"
            authorization = store.prepare_resume_authorization_row(
                decision,
                authorization_token_hash=token_hash,
                created_at=now,
                expires_at="2026-07-25T13:00:00Z",
            )
            assert second_repository.create_resume_authorization(
                authorization,
                expected_run_lock_version=2,
                expected_interrupt_version=1,
            ).classification == "applied"
            consumption_row = store.prepare_resume_consumption_row(
                authorization,
                consumer_instance_id=worker,
                claimed_at=now,
                expected_authorization_version=0,
            )
            assert second_repository.consume_resume_authorization(
                consumption_row,
                expected_run_lock_version=3,
                expected_interrupt_version=2,
                authorization_token_hash=token_hash,
            ).classification == "applied"
            consumption = dict(
                second_repository.read_resume_consumption(
                    owner_user_id=owner,
                    authorization_id=authorization["authorization_id"],
                ).record
            )
            consumed_graph = deepcopy(graph_run)
            consumed_graph.update(
                {
                    "run_status": "resume_consumed",
                    "current_checkpoint_id": checkpoint["checkpoint_id"],
                    "lock_version": 4,
                    "updated_at": now,
                }
            )
            attempt = store.prepare_node_attempt_row(
                consumed_graph,
                input_checkpoint_id=checkpoint["checkpoint_id"],
                node_key="finalize",
                attempt_number=1,
                input_digest=checkpoint["checkpoint_envelope_digest"],
                created_at=now,
                resume_invocation_id=consumption["resume_invocation_id"],
            )
            recovery_event = store.prepare_lifecycle_event_row(
                consumed_graph,
                event_type="recovery_claim_recorded",
                aggregate_type="node_attempt",
                aggregate_id=attempt["node_attempt_id"],
                event_sequence=0,
                event_payload={"status": "pending"},
                event_timestamp=now,
                references={
                    "node_attempt_id": attempt["node_attempt_id"],
                    "checkpoint_id": checkpoint["checkpoint_id"],
                    "consumption_id": consumption["consumption_id"],
                },
            )
            assert second_repository.create_pending_finalize_attempt(
                consumption,
                consumed_graph,
                attempt,
                recovery_event,
                expected_run_lock_version=4,
            ).classification == "applied"
            resumed_graph = deepcopy(consumed_graph)
            resumed_graph.update({"run_status": "resumed", "lock_version": 5})
            claim_event = store.prepare_lifecycle_event_row(
                resumed_graph,
                event_type="node_attempt_claimed",
                aggregate_type="node_attempt",
                aggregate_id=attempt["node_attempt_id"],
                event_sequence=1,
                event_payload={"status": "running"},
                event_timestamp=claimed_at,
                references={
                    "node_attempt_id": attempt["node_attempt_id"],
                    "checkpoint_id": checkpoint["checkpoint_id"],
                },
            )
            claimed = second_repository.claim_attempt(
                attempt,
                claim_event,
                lease_owner_id=worker,
                lease_acquired_at=claimed_at,
                lease_expires_at=lease_expires,
                expected_lock_version=0,
                expected_run_lock_version=5,
            )
            assert claimed.classification == "applied"
            assert second_repository.read_graph_run(
                owner_user_id=owner, graph_invocation_id=graph_id
            ).record["run_status"] == "resumed"
            assert dict(
                second_repository.read_attempt(
                    owner_user_id=owner,
                    graph_invocation_id=graph_id,
                    attempt_id=attempt["node_attempt_id"],
                ).record
            )["attempt_status"] == "claimed"

            def persist_final_state(final_state, final_config):
                artifacts = dict(final_state["artifacts"])
                bundle_digest = harness._checkpoint_digest(
                    artifacts["agent_evidence_chain_bundle"]
                )
                trace = artifacts.get("agent_evidence_chain_trace_payload")
                trace_digest = (
                    harness._checkpoint_digest(trace) if trace is not None else None
                )
                output_digests = {
                    "agent_evidence_chain_bundle": bundle_digest,
                }
                if trace_digest:
                    output_digests["agent_evidence_chain_trace_payload"] = (
                        trace_digest
                    )
                final_checkpoint = store.prepare_final_checkpoint_row(
                    resumed_graph,
                    checkpoint,
                    final_bundle_digest=bundle_digest,
                    final_trace_digest=trace_digest,
                    output_artifact_digests=output_digests,
                    committed_at=completed_at,
                )
                assert second_repository.commit_final_checkpoint(
                    final_checkpoint,
                    parent_checkpoint_id=checkpoint["checkpoint_id"],
                    expected_run_lock_version=5,
                ).classification == "applied"
                success_event = store.prepare_lifecycle_event_row(
                    resumed_graph,
                    event_type="node_attempt_succeeded",
                    aggregate_type="node_attempt",
                    aggregate_id=attempt["node_attempt_id"],
                    event_sequence=2,
                    event_payload={"status": "succeeded"},
                    event_timestamp=completed_at,
                    references={
                        "node_attempt_id": attempt["node_attempt_id"],
                        "checkpoint_id": final_checkpoint["checkpoint_id"],
                    },
                )
                succeeded = second_repository.record_attempt_success(
                    dict(claimed.record),
                    success_event,
                    output_checkpoint_id=final_checkpoint["checkpoint_id"],
                    output_digest=final_checkpoint[
                        "checkpoint_envelope_digest"
                    ],
                    completed_at=completed_at,
                    duration_ms=300_000,
                    lease_owner_id=worker,
                    expected_lock_version=1,
                    expected_run_lock_version=5,
                )
                assert succeeded.classification == "applied"
                final_binding = store.prepare_langgraph_checkpoint_binding_row(
                    resumed_graph,
                    repository_checkpoint_id=final_checkpoint["checkpoint_id"],
                    langgraph_thread_id=final_config["thread_id"],
                    langgraph_checkpoint_namespace=final_config["checkpoint_ns"],
                    langgraph_checkpoint_id=final_config["checkpoint_id"],
                    event_timestamp=completed_at,
                )
                assert second_repository.commit_checkpoint_binding(
                    final_binding
                ).classification == "applied"
                preterminal = deepcopy(resumed_graph)
                preterminal.update(
                    {
                        "current_checkpoint_id": final_checkpoint[
                            "checkpoint_id"
                        ],
                        "lock_version": 6,
                        "updated_at": completed_at,
                    }
                )
                terminal = store.prepare_terminal_result_row(
                    preterminal,
                    terminal_checkpoint_id=final_checkpoint["checkpoint_id"],
                    checkpoint_schema_version=(
                        harness.CHECKPOINT_SCHEMA_VERSION
                    ),
                    terminal_status="completed",
                    result_metadata={
                        "final_bundle_digest": bundle_digest,
                        "final_trace_digest": trace_digest,
                        "resume_invocation_id": consumption[
                            "resume_invocation_id"
                        ],
                    },
                    completed_at=completed_at,
                )
                terminal_event = store.prepare_lifecycle_event_row(
                    preterminal,
                    event_type="terminal_result_recorded",
                    aggregate_type="terminal_result",
                    aggregate_id=terminal["terminal_result_id"],
                    event_sequence=0,
                    event_payload={"status": "completed"},
                    event_timestamp=completed_at,
                    references={
                        "terminal_result_id": terminal["terminal_result_id"],
                        "checkpoint_id": final_checkpoint["checkpoint_id"],
                    },
                )
                assert second_repository.terminalize_completed_run(
                    preterminal,
                    terminal,
                    terminal_event,
                    dict(succeeded.record),
                    final_binding,
                    expected_run_lock_version=6,
                ).classification == "applied"
                return DurableResumeResult(
                    status="resume_completed",
                    classification="applied",
                    graph_invocation_id=graph_id,
                    repository_checkpoint_id=final_checkpoint["checkpoint_id"],
                    attempt_id=attempt["node_attempt_id"],
                    terminal_result_id=terminal["terminal_result_id"],
                    langgraph_thread_id=final_config["thread_id"],
                    langgraph_checkpoint_namespace=final_config["checkpoint_ns"],
                    langgraph_checkpoint_id=final_config["checkpoint_id"],
                )

            completed = coordinator.resume_claimed_attempt(
                owner_user_id=owner,
                graph_invocation_id=graph_id,
                repository_checkpoint_id=checkpoint["checkpoint_id"],
                authorization_id=authorization["authorization_id"],
                attempt_id=attempt["node_attempt_id"],
                lease_owner_id=worker,
                persist_final_state=persist_final_state,
            )
            assert completed.status == "resume_completed", completed
            assert all(calls[name] == 1 for name in node_names)
            assert second_repository.read_graph_run(
                owner_user_id=owner, graph_invocation_id=graph_id
            ).record["run_status"] == "completed"
            assert second_repository.read_terminal_result(
                owner_user_id=owner, graph_invocation_id=graph_id
            ).classification == "applied"
            assert coordinator.resume_claimed_attempt(
                owner_user_id=owner,
                graph_invocation_id=graph_id,
                repository_checkpoint_id=checkpoint["checkpoint_id"],
                authorization_id=authorization["authorization_id"],
                attempt_id=attempt["node_attempt_id"],
                lease_owner_id=worker,
                persist_final_state=lambda *_: pytest.fail(
                    "replay reached persistence"
                ),
            ).status == "already_completed"
            assert _counts(factory, owner=owner, graph_id=graph_id)[
                "orchestration_terminal_results"
            ] == 1
    finally:
        _cleanup(factory, owner=owner, graph_id=graph_id)
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase9-step17-cleanup",
        ) as cleanup_saver:
            cleanup_saver.delete_thread(graph_id)
        assert _counts(
            factory, owner=wrong_owner, graph_id="unrelated-step17"
        ) == unrelated_before

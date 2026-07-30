from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import inspect
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from langgraph.checkpoint.memory import MemorySaver

import generate_tailoring_suggestions as caller
from src.agents import production_durable_graph_runtime as runtime_owner
from src.agents import tailoring_generation_authoritative_graph as graph_owner
from src.storage.durable_orchestration import production
from src.storage.durable_orchestration import repository as repository_owner
from src.storage.durable_orchestration import store


NOW = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)
GATE = runtime_owner.PRODUCTION_DURABLE_GRAPH_RUNTIME_FLAG
GRAPH_GATE = caller.AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_FLAG
SCHEMA = Path("src/storage/durable_orchestration/schema.sql")


def _packet() -> dict:
    return {
        "job": {
            "job_doc_id": "job-phase18r",
            "company": "ExampleCo",
            "title": "Analytics Engineer",
        },
        "selection": {"selected_resume": "resume-phase18r.pdf"},
        "summary": {"matched_required": ["Python"]},
    }


def _payload() -> dict:
    return {
        "job": {
            "job_doc_id": "job-phase18r",
            "company": "ExampleCo",
            "title": "Analytics Engineer",
        },
        "selection": {"selected_resume": "resume-phase18r.pdf"},
        "live_rewrite_prompt": "synthetic prompt",
        "evidence_layers": {"anchors": [], "supports": [], "context": []},
    }


def _owner_result() -> dict:
    return {
        "parse_ok": True,
        "parse_error": "",
        "retry_used": False,
        "cache_hit": False,
        "requested_provider": "groq",
        "requested_model": "synthetic-model",
        "resolved_provider": "groq",
        "resolved_model": "synthetic-model",
        "fallback_used": False,
        "raw_response": "raw provider transport must not persist",
        "retry_raw_response": "",
        "parsed": {
            "recruiter_summary": "Grounded synthetic summary.",
            "keep_emphasize": ["Python"],
            "tailoring_actions": ["Emphasize Python"],
            "do_not_claim": [],
            "rewrite_directions": [],
            "invalid_concrete_replacement_candidates": [],
        },
        "concrete_replacement_candidates_requested": False,
    }


def _result(classification: str, record=None):
    return SimpleNamespace(
        classification=classification,
        record=deepcopy(record or {}),
        metadata={},
    )


class _Repository:
    def __init__(self):
        self.runs = {}
        self.checkpoints = {}
        self.attempts = {}
        self.bindings = {}
        self.terminals = {}
        self.interrupts = 0
        self.human_decisions = 0
        self.authorizations = 0
        self.fail_terminalization = False

    def read_terminal_result(self, *, owner_user_id, graph_invocation_id):
        row = self.terminals.get(graph_invocation_id)
        if row is None or row["owner_user_id"] != owner_user_id:
            return _result("not_found")
        return _result("applied", row)

    def create_production_graph_run(self, row):
        graph_id = row["graph_invocation_id"]
        existing = self.runs.get(graph_id)
        if existing is not None:
            if existing["owner_user_id"] != row["owner_user_id"]:
                return _result("duplicate_conflict")
            return _result("idempotent_existing", existing)
        self.runs[graph_id] = deepcopy(row)
        return _result("applied", row)

    def start_production_attempt(self, graph, checkpoint, attempt):
        attempt_id = attempt["node_attempt_id"]
        existing = self.attempts.get(attempt_id)
        if existing is not None:
            classification = (
                "idempotent_existing"
                if existing["attempt_status"] == "pending"
                else "duplicate_conflict"
            )
            return _result(classification, existing)
        self.checkpoints[checkpoint["checkpoint_id"]] = deepcopy(checkpoint)
        self.attempts[attempt_id] = deepcopy(attempt)
        run = self.runs[graph["graph_invocation_id"]]
        run.update(
            {
                "run_status": "resumed",
                "current_checkpoint_id": checkpoint["checkpoint_id"],
                "lock_version": 1,
            }
        )
        return _result("applied", attempt)

    def claim_attempt(self, attempt, _event, **kwargs):
        row = self.attempts[attempt["node_attempt_id"]]
        if row["attempt_status"] != "pending":
            return _result("stale_state", row)
        row.update(
            {
                "attempt_status": "claimed",
                "lease_owner_id": kwargs["lease_owner_id"],
                "lease_acquired_at": kwargs["lease_acquired_at"],
                "lease_expires_at": kwargs["lease_expires_at"],
                "started_at": kwargs["lease_acquired_at"],
                "lock_version": 1,
                "updated_at": kwargs["lease_acquired_at"],
            }
        )
        return _result("applied", row)

    def record_attempt_failure(self, attempt, _event, **kwargs):
        row = self.attempts[attempt["node_attempt_id"]]
        row.update(
            {
                "attempt_status": "failed",
                "error_code": kwargs["error_code"],
                "error_detail": kwargs["error_detail"],
                "completed_at": kwargs["completed_at"],
                "lock_version": 2,
            }
        )
        return _result("applied", row)

    def commit_production_checkpoint(
        self, checkpoint, **_kwargs
    ):
        self.checkpoints[checkpoint["checkpoint_id"]] = deepcopy(checkpoint)
        return _result("applied", checkpoint)

    def commit_checkpoint_binding(self, binding):
        self.bindings[binding["checkpoint_id"]] = deepcopy(binding)
        return _result("applied", binding)

    def read_checkpoint_binding(
        self,
        *,
        owner_user_id,
        graph_invocation_id,
        repository_checkpoint_id,
    ):
        row = self.bindings.get(repository_checkpoint_id)
        if (
            row is None
            or row["owner_user_id"] != owner_user_id
            or row["graph_invocation_id"] != graph_invocation_id
        ):
            return _result("not_found")
        return _result("applied", row)

    def record_attempt_success(self, attempt, _event, **kwargs):
        row = self.attempts[attempt["node_attempt_id"]]
        if row["attempt_status"] != "claimed":
            return _result("stale_state", row)
        row.update(
            {
                "attempt_status": "succeeded",
                "output_checkpoint_id": kwargs["output_checkpoint_id"],
                "output_digest": kwargs["output_digest"],
                "completed_at": kwargs["completed_at"],
                "duration_ms": kwargs["duration_ms"],
                "lock_version": 2,
            }
        )
        run = self.runs[row["graph_invocation_id"]]
        run.update(
            {
                "current_checkpoint_id": kwargs["output_checkpoint_id"],
                "lock_version": 2,
            }
        )
        return _result("applied", row)

    def terminalize_production_run(
        self, graph, terminal, _event, **_kwargs
    ):
        if self.fail_terminalization:
            return _result("transaction_failed")
        self.terminals[graph["graph_invocation_id"]] = deepcopy(terminal)
        self.runs[graph["graph_invocation_id"]].update(
            {
                "run_status": terminal["terminal_status"],
                "terminal_at": terminal["completed_at"],
                "lock_version": 3,
            }
        )
        return _result("applied", terminal)


def _identity(**overrides):
    values = {
        "packet": _packet(),
        "payload": _payload(),
        "graph_version": (
            graph_owner.AUTHORITATIVE_TAILORING_GENERATION_GRAPH_VERSION
        ),
        "state_version": (
            graph_owner.AUTHORITATIVE_TAILORING_GENERATION_STATE_VERSION
        ),
        "node_key": graph_owner.AUTHORITATIVE_TAILORING_GENERATION_NODE,
        "owner_user_id": "owner-phase18r",
        "pipeline_run_id": "run-phase18r",
        "context_id": "context-phase18r",
        "job_index": 7,
        "refresh_llm_cache": False,
        "enable_safe_app_ready_rewrite_promotion": False,
        "created_at": "2026-07-29T12:00:00Z",
    }
    values.update(overrides)
    return runtime_owner.build_tailoring_execution_identity(**values)


def _runtime(repository, saver):
    return runtime_owner.ProductionDurableGraphRuntime(
        repository=repository,
        saver=saver,
        consumer_instance_id="worker-phase18r",
        enabled=True,
        now_func=lambda: NOW,
    )


def _invoke(owner_calls):
    def owner(**_kwargs):
        owner_calls.append("owner")
        return deepcopy(_owner_result())

    def invoke(saver, config):
        return graph_owner.execute_authoritative_tailoring_generation_graph(
            packet=_packet(),
            payload=_payload(),
            run_tailoring_func=owner,
            pipeline_run_id="run-phase18r",
            owner_user_id="owner-phase18r",
            context_id="context-phase18r",
            checkpointer=saver,
            configurable=config,
        )

    return invoke


def test_exact_generic_contract_versions():
    assert (
        production.PRODUCTION_DURABLE_CONTRACT_VERSION
        == "production-durable-contract-v1"
    )
    assert (
        production.PRODUCTION_CHECKPOINT_SCHEMA_VERSION
        == "production-graph-checkpoint-v1"
    )
    assert (
        runtime_owner.PRODUCTION_DURABLE_RUNTIME_VERSION
        == "production-durable-runtime-v1"
    )


def test_graph_identity_is_deterministic_and_inputs_are_unchanged():
    packet, payload = _packet(), _payload()
    before = deepcopy((packet, payload))
    first = _identity(packet=packet, payload=payload)
    second = _identity(packet=packet, payload=payload)
    assert first == second
    assert first.graph_invocation_id.startswith("production-graph:")
    assert (packet, payload) == before


def test_production_identity_retains_real_job_resume_and_index():
    identity = _identity()
    row = identity.graph_run_row
    assert row["job_id"] == "job-phase18r"
    assert row["job_index"] == 7
    assert row["selected_resume_id"] == "resume-phase18r.pdf"
    assert "authoritative-tailoring-generation-graph-v1" in row["graph_engine"]


def test_missing_real_identity_fails_closed():
    with pytest.raises(
        runtime_owner.ProductionDurableRuntimeError,
        match="job_id_required",
    ):
        _identity(packet={}, payload={"selection": {"selected_resume": "r"}})
    with pytest.raises(
        runtime_owner.ProductionDurableRuntimeError,
        match="job_index_required",
    ):
        _identity(job_index=None)


def test_production_checkpoint_is_not_evidence_or_diagnostic():
    identity = _identity()
    checkpoint = production.prepare_checkpoint_row(
        identity.graph_run_row,
        production_node_key=identity.node_key,
        input_digest=identity.input_digest,
        checkpoint_sequence=0,
        bounded_execution_state={
            "status": "pending",
            "completed_node_keys": [],
            "next_node_key": identity.node_key,
        },
        completed_node_keys=[],
        next_node_key=identity.node_key,
        committed_at="2026-07-29T12:00:00Z",
    )
    envelope = checkpoint["checkpoint_envelope_json"]
    assert checkpoint["checkpoint_status"] == "production_execution"
    assert envelope["production_execution"] is True
    assert envelope["diagnostic_only"] is False
    assert "checkpoint_identity" not in envelope


def test_generic_contract_rejects_secrets_and_authority():
    identity = _identity()
    with pytest.raises(ValueError, match="secret"):
        production.prepare_checkpoint_row(
            identity.graph_run_row,
            production_node_key=identity.node_key,
            input_digest=identity.input_digest,
            checkpoint_sequence=0,
            bounded_execution_state={"api_key": "forbidden"},
            completed_node_keys=[],
            next_node_key=identity.node_key,
            committed_at="2026-07-29T12:00:00Z",
        )


def test_evidence_chain_public_contract_remains_exact():
    source = inspect.getsource(store.prepare_graph_run_row)
    assert "harness.EvidenceChainCheckpointIdentityPayload" not in source
    assert "checkpoint_graph_engine_unsupported" in inspect.getsource(
        store._validated_identity
    )
    assert store.prepare_graph_run_row.__module__.endswith(".store")
    assert production.prepare_graph_run_row.__module__.endswith(".production")


def test_schema_preserves_legacy_and_adds_only_production_checkpoint_status():
    schema = SCHEMA.read_text(encoding="utf-8")
    assert "'diagnostic_snapshot'" in schema
    assert "'production_execution'" in schema
    assert schema.count(
        "DROP CONSTRAINT IF EXISTS ck_orchestration_checkpoints_status"
    ) == 1
    assert schema.count(
        "ADD CONSTRAINT ck_orchestration_checkpoints_status"
    ) == 1
    assert schema.count("CREATE TABLE IF NOT EXISTS") == 9


def test_repository_exposes_explicit_production_operations():
    repository = object.__new__(
        repository_owner.DurableOrchestrationRepository
    )
    for name in (
        "create_production_graph_run",
        "start_production_attempt",
        "commit_production_checkpoint",
        "terminalize_production_run",
    ):
        assert callable(getattr(repository, name))


def test_production_sql_uses_existing_cas_attempt_and_terminal_tables():
    identity = _identity()
    checkpoint = production.prepare_checkpoint_row(
        identity.graph_run_row,
        production_node_key=identity.node_key,
        input_digest=identity.input_digest,
        checkpoint_sequence=0,
        bounded_execution_state={"status": "pending"},
        completed_node_keys=[],
        next_node_key=identity.node_key,
        committed_at="2026-07-29T12:00:00Z",
    )
    attempt = production.prepare_node_attempt_row(
        identity.graph_run_row,
        input_checkpoint_id=checkpoint["checkpoint_id"],
        production_node_key=identity.node_key,
        input_digest=identity.input_digest,
        created_at="2026-07-29T12:00:00Z",
    )
    command = production.prepare_checkpoint_attempt_start(
        identity.graph_run_row, checkpoint, attempt
    )
    assert "orchestration_node_attempts" in command["tables"]
    assert "lock_version = 0" in command["sql"]
    assert "ON CONFLICT" in command["sql"]


def test_durable_gate_is_default_off_and_uses_truthy_convention():
    for value, expected in (
        (None, False),
        ("", False),
        ("false", False),
        ("0", False),
        ("true", True),
        ("1", True),
    ):
        env = {} if value is None else {GATE: value}
        assert (
            caller._production_durable_graph_runtime_enabled(env)
            is expected
        )


def test_durability_gate_does_not_enable_authoritative_graph():
    calls = []
    result = caller._maybe_execute_authoritative_tailoring_generation_graph(
        packet=_packet(),
        payload=_payload(),
        run_tailoring_func=lambda **kwargs: calls.append(kwargs),
        env={GATE: "1"},
        job_index=7,
    )
    assert result is None
    assert calls == []


def test_first_execution_claims_and_invokes_graph_and_owner_once():
    repository, saver, calls = _Repository(), MemorySaver(), []
    result = _runtime(repository, saver).execute(
        identity=_identity(),
        invoke_graph=_invoke(calls),
    )
    assert calls == ["owner"]
    assert result["execution_metadata"]["graph_invocation_count"] == 1
    assert result["execution_metadata"]["durable_status"] == "completed"
    assert len(repository.attempts) == 1
    assert next(iter(repository.attempts.values()))["attempt_status"] == (
        "succeeded"
    )
    assert len(repository.terminals) == 1


def test_tailoring_output_parity_preserves_bounded_business_result():
    result = _runtime(_Repository(), MemorySaver()).execute(
        identity=_identity(),
        invoke_graph=_invoke([]),
    )["tailoring_result"]
    expected = _owner_result()
    assert result["parsed"] == expected["parsed"]
    assert result["requested_provider"] == expected["requested_provider"]
    assert result["resolved_model"] == expected["resolved_model"]
    assert result["raw_response"] == ""


def test_completed_replay_invokes_no_graph_owner_provider_or_cache_write():
    repository, saver, calls = _Repository(), MemorySaver(), []
    runtime = _runtime(repository, saver)
    identity = _identity()
    first = runtime.execute(identity=identity, invoke_graph=_invoke(calls))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("completed replay invoked graph")

    replay = runtime.execute(identity=identity, invoke_graph=forbidden)
    assert calls == ["owner"]
    assert replay["tailoring_result"] == first["tailoring_result"]
    metadata = replay["execution_metadata"]
    assert metadata["graph_invocation_count"] == 0
    assert metadata["tailoring_owner_invocation_count"] == 0
    assert metadata["provider_call_count"] == 0
    assert metadata["cache_write_count"] == 0


def test_restart_with_new_runtime_and_repository_object_replays_terminal():
    repository, saver = _Repository(), MemorySaver()
    identity = _identity()
    _runtime(repository, saver).execute(
        identity=identity, invoke_graph=_invoke([])
    )
    reopened_repository = deepcopy(repository)
    reopened_runtime = _runtime(reopened_repository, saver)
    replay = reopened_runtime.execute(
        identity=identity,
        invoke_graph=lambda *_args: pytest.fail("owner rerun"),
    )
    assert replay["execution_metadata"]["durable_status"] == (
        "completed_replay"
    )


def test_changed_input_has_distinct_digest_and_invocation_identity():
    changed = _payload()
    changed["live_rewrite_prompt"] = "changed input"
    original, different = _identity(), _identity(payload=changed)
    assert original.input_digest != different.input_digest
    assert original.graph_invocation_id != different.graph_invocation_id


def test_wrong_owner_cannot_read_existing_terminal():
    repository, saver = _Repository(), MemorySaver()
    identity = _identity()
    _runtime(repository, saver).execute(
        identity=identity, invoke_graph=_invoke([])
    )
    result = repository.read_terminal_result(
        owner_user_id="wrong-owner",
        graph_invocation_id=identity.graph_invocation_id,
    )
    assert result.classification == "not_found"
    assert result.record == {}


def test_concurrent_claim_conflict_prevents_duplicate_owner_execution():
    repository, saver = _Repository(), MemorySaver()
    identity = _identity()
    created = repository.create_production_graph_run(
        identity.graph_run_row
    )
    assert created.classification == "applied"
    checkpoint = production.prepare_checkpoint_row(
        identity.graph_run_row,
        production_node_key=identity.node_key,
        input_digest=identity.input_digest,
        checkpoint_sequence=0,
        bounded_execution_state={
            "status": "pending",
            "completed_node_keys": [],
            "next_node_key": identity.node_key,
        },
        completed_node_keys=[],
        next_node_key=identity.node_key,
        committed_at="2026-07-29T12:00:00Z",
    )
    attempt = production.prepare_node_attempt_row(
        identity.graph_run_row,
        input_checkpoint_id=checkpoint["checkpoint_id"],
        production_node_key=identity.node_key,
        input_digest=identity.input_digest,
        created_at="2026-07-29T12:00:00Z",
    )
    repository.start_production_attempt(
        identity.graph_run_row, checkpoint, attempt
    )
    repository.attempts[attempt["node_attempt_id"]][
        "attempt_status"
    ] = "claimed"
    calls = []
    with pytest.raises(
        runtime_owner.ProductionDurableRuntimeError,
        match="production_attempt_in_progress",
    ):
        _runtime(repository, saver).execute(
            identity=identity, invoke_graph=_invoke(calls)
        )
    assert calls == []


def test_graph_failure_is_bounded_retryable_and_records_no_authority():
    repository, saver = _Repository(), MemorySaver()

    def failed(*_args):
        raise RuntimeError("secret provider exception detail")

    with pytest.raises(
        runtime_owner.ProductionDurableRuntimeError,
        match="retryable_failure",
    ):
        _runtime(repository, saver).execute(
            identity=_identity(), invoke_graph=failed
        )
    attempt = next(iter(repository.attempts.values()))
    assert attempt["attempt_status"] == "failed"
    assert attempt["error_code"] == "authoritative_graph_failed"
    assert attempt["application_authorization"] is False
    assert attempt["mutation_authorization"] is False


def test_terminal_failure_reports_ambiguous_reconciliation_without_replay():
    repository, saver = _Repository(), MemorySaver()
    repository.fail_terminalization = True
    with pytest.raises(
        runtime_owner.ProductionDurableRuntimeError,
        match="reconciliation_required",
    ):
        _runtime(repository, saver).execute(
            identity=_identity(), invoke_graph=_invoke([])
        )
    assert repository.terminals == {}


def test_checkpoint_binding_is_exact_and_owner_scoped():
    repository, saver = _Repository(), MemorySaver()
    identity = _identity()
    result = _runtime(repository, saver).execute(
        identity=identity, invoke_graph=_invoke([])
    )
    checkpoint_id = result["execution_metadata"][
        "repository_checkpoint_id"
    ]
    binding = repository.bindings[checkpoint_id][
        "event_payload_json"
    ]
    assert binding["langgraph_thread_id"] == identity.graph_invocation_id
    assert binding["langgraph_checkpoint_id"]
    assert binding["langgraph_checkpoint_namespace"] == ""


def test_human_and_application_authority_remain_zero():
    repository = _Repository()
    result = _runtime(repository, MemorySaver()).execute(
        identity=_identity(), invoke_graph=_invoke([])
    )
    assert repository.interrupts == 0
    assert repository.human_decisions == 0
    assert repository.authorizations == 0
    metadata = result["execution_metadata"]
    assert metadata["mutation_authority"] is False
    assert metadata["application_authority"] is False
    assert metadata["ats_authority"] is False


def test_planning_caller_passes_the_real_job_index():
    source = Path("run_application_planning.py").read_text(encoding="utf-8")
    assert '"--job-index",\n                    str(job_index),' in source


def test_dedicated_database_targets_never_fall_back_to_normal_database():
    source = inspect.getsource(caller._execute_durable_tailoring_graph)
    assert "DATABASE_URL" in source
    assert "repository_target == ordinary_target" in source
    assert "saver_target == ordinary_target" in source


def test_real_provider_network_human_and_application_owners_are_absent():
    source = inspect.getsource(
        runtime_owner.ProductionDurableGraphRuntime
    )
    for prohibited in (
        "run_chat_completion",
        "continue_read_only",
        "create_resume_authorization",
        "consume_resume_authorization",
        "mark_applied",
        "submit_application",
    ):
        assert prohibited not in source


def test_real_postgres_target_is_dedicated_phase9_database_or_skips():
    repository_target = str(
        os.environ.get(
            "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
        )
        or ""
    ).strip()
    saver_target = str(
        os.environ.get(
            "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_TEST_DATABASE_URL"
        )
        or ""
    ).strip()
    if not repository_target or not saver_target:
        pytest.skip("dedicated Phase 9 PostgreSQL targets are not configured")
    from urllib.parse import urlsplit

    assert urlsplit(repository_target).path.strip("/") == (
        "job_scraper_phase9_test"
    )
    assert urlsplit(saver_target).path.strip("/") == (
        "job_scraper_phase9_test"
    )
    assert repository_target != str(os.environ.get("DATABASE_URL") or "")
    assert saver_target != str(os.environ.get("DATABASE_URL") or "")

    from psycopg.errors import CheckViolation
    from src.storage.admin_tools.durable_orchestration import apply_schema
    from src.storage.durable_orchestration import langgraph_postgres
    from src.storage.durable_orchestration import postgres_connection
    from tests.test_phase9_step16a_durable_decision_authorization_runtime_contract import (
        _cleanup,
        _counts,
    )

    schema_application = (
        apply_schema.DurableOrchestrationSchemaExecutor(enabled=True).apply(
            database_url=repository_target
        )
    )
    assert schema_application.outcome == "applied"
    assert schema_application.compatibility == "compatible"

    identity = _identity(
        owner_user_id="owner-phase18r-postgres",
        pipeline_run_id="run-phase18r-postgres",
        context_id="context-phase18r-postgres",
    )
    graph_id = identity.graph_invocation_id
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=repository_target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase18r-repository",
    )
    owner_calls: list[str] = []
    _cleanup(
        factory,
        owner=identity.owner_user_id,
        graph_id=graph_id,
    )
    try:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase18r-first",
        ) as first_saver:
            first_saver.delete_thread(graph_id)
            first_repository = (
                repository_owner.DurableOrchestrationRepository(
                    factory,
                    enabled=True,
                )
            )
            first = _runtime(first_repository, first_saver).execute(
                identity=identity,
                invoke_graph=_invoke(owner_calls),
            )
            assert owner_calls == ["owner"]
            assert first["tailoring_result"]["parsed"] == (
                _owner_result()["parsed"]
            )
            assert first["tailoring_result"]["raw_response"] == ""

        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase18r-restart",
        ) as restarted_saver:
            restarted_repository = (
                repository_owner.DurableOrchestrationRepository(
                    postgres_connection.build_postgres_connection_factory(
                        enabled=True,
                        database_url=repository_target,
                        connect_timeout_seconds=5,
                        statement_timeout_ms=10_000,
                        application_name=(
                            "applylens-phase18r-restarted-repository"
                        ),
                    ),
                    enabled=True,
                )
            )
            replay = _runtime(
                restarted_repository,
                restarted_saver,
            ).execute(
                identity=identity,
                invoke_graph=_invoke(owner_calls),
            )
            assert replay["tailoring_result"] == first["tailoring_result"]
            assert owner_calls == ["owner"]
            assert replay["execution_metadata"][
                "graph_invocation_count"
            ] == 0
            assert replay["execution_metadata"][
                "tailoring_owner_invocation_count"
            ] == 0
            assert replay["execution_metadata"]["provider_call_count"] == 0
        assert _counts(
            factory,
            owner=identity.owner_user_id,
            graph_id=graph_id,
        )["orchestration_terminal_results"] == 1
        connection = factory()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT pg_get_constraintdef(oid, true) "
                "AS constraint_definition "
                "FROM pg_constraint "
                "WHERE conname = "
                "'ck_orchestration_checkpoints_status' "
                "AND conrelid = "
                "'orchestration_checkpoints'::regclass"
            )
            definition = cursor.fetchall()[0]["constraint_definition"]
            assert "diagnostic_snapshot" in definition
            assert "production_execution" in definition

            cursor.execute("SAVEPOINT phase18r_status_compatibility")
            cursor.execute(
                "UPDATE orchestration_checkpoints "
                "SET checkpoint_status = 'diagnostic_snapshot' "
                "WHERE graph_invocation_id = %(graph_invocation_id)s",
                {"graph_invocation_id": graph_id},
            )
            assert cursor.rowcount == 2
            cursor.execute(
                "ROLLBACK TO SAVEPOINT phase18r_status_compatibility"
            )

            cursor.execute("SAVEPOINT phase18r_status_rejection")
            with pytest.raises(CheckViolation):
                cursor.execute(
                    "UPDATE orchestration_checkpoints "
                    "SET checkpoint_status = 'unsupported_status' "
                    "WHERE graph_invocation_id = %(graph_invocation_id)s",
                    {"graph_invocation_id": graph_id},
                )
            cursor.execute(
                "ROLLBACK TO SAVEPOINT phase18r_status_rejection"
            )
        finally:
            connection.rollback()
            cursor.close()
            connection.close()
    finally:
        _cleanup(
            factory,
            owner=identity.owner_user_id,
            graph_id=graph_id,
        )
        assert all(
            count == 0
            for count in _counts(
                factory,
                owner=identity.owner_user_id,
                graph_id=graph_id,
            ).values()
        )
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase18r-cleanup",
        ) as cleanup_saver:
            cleanup_saver.delete_thread(graph_id)

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.agents import evidence_chain_langgraph_harness as harness
from src.storage.durable_orchestration import store


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src/storage/durable_orchestration/schema.sql"
STORE_PATH = ROOT / "src/storage/durable_orchestration/store.py"
PACKAGE_PATH = ROOT / "src/storage/durable_orchestration/__init__.py"
NOW = "2026-07-23T12:00:00Z"
COMMITTED = "2026-07-23T12:01:00Z"


def _pause_state(**overrides):
    job_id = overrides.pop("job_id", "job-phase9-step2")
    selected_resume_id = overrides.pop("selected_resume_id", "resume-main")
    job = {
        "job_id": job_id,
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "url": "https://example.test/jobs/phase9-step2",
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
    resume_rows = [
        {
            "resume_id": selected_resume_id,
            "skills": ["Python", "SQL", "RAG"],
            "raw_text": "Built Python, SQL, and RAG systems.",
        }
    ]
    state = harness._build_initial_graph_state(
        job=job,
        job_index=overrides.pop("job_index", 0),
        job_identity={
            "job_id": job_id,
            "title": job["title"],
            "company": job["company"],
        },
        resume_rows=resume_rows,
        selected_resume_id=selected_resume_id,
        pipeline_run_id=overrides.pop("pipeline_run_id", "run-phase9-step2"),
        owner_user_id=overrides.pop("owner_user_id", "owner-phase9-step2"),
        context_id=overrides.pop("context_id", "ctx-phase9-step2"),
        include_trace_payload=True,
    )
    assert not overrides
    for node in (
        harness._jd_intelligence_node,
        harness._resume_match_node,
        harness._critic_node,
        harness._job_prioritization_node,
        harness._tailoring_decision_node,
        harness._operator_review_node,
    ):
        state = node(state)
    return state


def _contracts(**overrides):
    state = _pause_state(**overrides)
    envelope = harness._build_checkpoint_envelope(state)
    request = harness._build_operator_review_interrupt_request(state)
    graph_run = store.prepare_graph_run_row(envelope, created_at=NOW)
    checkpoint = store.prepare_checkpoint_row(
        envelope,
        committed_at=COMMITTED,
    )
    interrupt = store.prepare_interrupt_request_row(
        request,
        checkpoint_envelope=envelope,
        created_at=COMMITTED,
        expires_at="2026-07-24T12:01:00Z",
    )
    return state, envelope, request, graph_run, checkpoint, interrupt


def test_schema_has_exact_non_colliding_objects_and_static_only_scope():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    assert schema.count("CREATE TABLE IF NOT EXISTS") == 3
    assert "CREATE TABLE IF NOT EXISTS orchestration_graph_runs" in schema
    assert "CREATE TABLE IF NOT EXISTS orchestration_checkpoints" in schema
    assert (
        "CREATE TABLE IF NOT EXISTS orchestration_interrupt_requests"
        in schema
    )
    assert "CREATE TABLE IF NOT EXISTS agent_runs" not in schema
    assert "CREATE TABLE IF NOT EXISTS agent_steps" not in schema
    assert "\nINSERT INTO " not in schema
    assert "\nUPDATE " not in schema
    assert "\nDELETE FROM " not in schema


def test_schema_defines_keys_cas_constraints_and_immutable_checkpoint_shape():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    for primary_key in (
        "graph_invocation_id TEXT PRIMARY KEY",
        "checkpoint_id TEXT PRIMARY KEY",
        "interrupt_request_id TEXT PRIMARY KEY",
    ):
        assert primary_key in schema
    assert "fk_orchestration_checkpoints_graph_run" in schema
    assert "fk_orchestration_interrupt_requests_graph_run" in schema
    assert "fk_orchestration_interrupt_requests_checkpoint" in schema
    assert "uq_orchestration_checkpoints_run_sequence" in schema
    assert "uq_orchestration_interrupt_requests_checkpoint_node" in schema
    assert schema.count("lock_version INTEGER NOT NULL DEFAULT 0") == 2
    assert "CHECK (lock_version >= 0)" in schema
    assert "ON CONFLICT" not in schema
    assert "updated_at" not in schema.split(
        "CREATE TABLE IF NOT EXISTS orchestration_checkpoints",
        1,
    )[1].split(
        "CREATE TABLE IF NOT EXISTS orchestration_interrupt_requests",
        1,
    )[0]


def test_schema_status_safety_payload_bounds_and_targeted_indexes_are_exact():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    assert "run_status IN ('running', 'awaiting_decision')" in schema
    assert "CHECK (interrupt_status = 'pending')" in schema
    assert "node_key = 'operator_review'" in schema
    assert "safe_next_node_key = 'finalize'" in schema
    assert (
        """'["continue_read_only","needs_revision","cancel"]'::jsonb"""
        in schema
    )
    assert "application_authorization = FALSE" in schema
    assert "resume_authorization = FALSE" in schema
    assert "octet_length(checkpoint_envelope_json::text) <= 1048576" in schema
    assert "octet_length(interrupt_request_json::text) <= 262144" in schema
    for index_name in (
        "idx_orchestration_graph_runs_owner_updated",
        "idx_orchestration_graph_runs_pipeline_context",
        "idx_orchestration_graph_runs_current_checkpoint",
        "idx_orchestration_checkpoints_owner_run_sequence",
        "idx_orchestration_interrupt_requests_pending_owner",
        "idx_orchestration_interrupt_requests_expiry",
    ):
        assert index_name in schema


def test_table_specs_capture_relationships_immutability_and_status_vocabularies():
    specs = store.durable_orchestration_table_specs()

    assert set(specs) == {
        "orchestration_graph_runs",
        "orchestration_checkpoints",
        "orchestration_interrupt_requests",
    }
    assert specs["orchestration_graph_runs"]["status_values"] == [
        "running",
        "awaiting_decision",
    ]
    assert specs["orchestration_graph_runs"]["cas_column"] == "lock_version"
    assert specs["orchestration_checkpoints"]["immutable"] is True
    assert specs["orchestration_checkpoints"]["foreign_keys"] == {
        "graph_invocation_id": (
            "orchestration_graph_runs.graph_invocation_id"
        )
    }
    assert specs["orchestration_interrupt_requests"]["foreign_keys"] == {
        "graph_invocation_id": "orchestration_graph_runs.graph_invocation_id",
        "checkpoint_id": "orchestration_checkpoints.checkpoint_id",
    }
    assert specs["orchestration_interrupt_requests"]["status_values"] == [
        "pending"
    ]


def test_rows_preserve_exact_harness_identities_schemas_boundary_and_safety():
    state, envelope, request, graph_run, checkpoint, interrupt = _contracts()
    identity = harness._build_checkpoint_identity(state).to_payload()

    assert graph_run["graph_invocation_id"] == identity["graph_invocation_id"]
    assert checkpoint["checkpoint_id"] == identity["checkpoint_id"]
    assert interrupt["interrupt_request_id"] == request["interrupt_request_id"]
    for row in (graph_run, checkpoint, interrupt):
        for key in (
            "owner_user_id",
            "pipeline_run_id",
            "context_id",
            "job_id",
            "job_index",
            "selected_resume_id",
        ):
            assert row[key] == identity[key]
    assert checkpoint["checkpoint_schema_version"] == (
        harness.CHECKPOINT_SCHEMA_VERSION
    )
    assert checkpoint["graph_state_schema_version"] == (
        harness.GRAPH_STATE_SCHEMA_VERSION
    )
    assert checkpoint["completed_node_keys_json"] == list(
        harness.ORDERED_AGENT_KEYS
    )
    assert checkpoint["next_node_key"] == "finalize"
    assert interrupt["node_key"] == "operator_review"
    assert interrupt["safe_next_node_key"] == "finalize"
    assert interrupt["allowed_decision_values_json"] == [
        "continue_read_only",
        "needs_revision",
        "cancel",
    ]
    assert interrupt["read_only"] is True
    assert interrupt["diagnostic_only"] is True
    assert interrupt["application_authorization"] is False
    assert interrupt["resume_authorization"] is False
    assert checkpoint["checkpoint_envelope_json"] == envelope


def test_row_preparation_is_deterministic_deep_copied_and_input_preserving():
    state = _pause_state()
    envelope = harness._build_checkpoint_envelope(state)
    request = harness._build_operator_review_interrupt_request(state)
    before_envelope = deepcopy(envelope)
    before_request = deepcopy(request)

    first_graph = store.prepare_graph_run_row(envelope, created_at=NOW)
    second_graph = store.prepare_graph_run_row(envelope, created_at=NOW)
    first_checkpoint = store.prepare_checkpoint_row(
        envelope,
        committed_at=COMMITTED,
    )
    second_checkpoint = store.prepare_checkpoint_row(
        envelope,
        committed_at=COMMITTED,
    )
    first_interrupt = store.prepare_interrupt_request_row(
        request,
        checkpoint_envelope=envelope,
        created_at=COMMITTED,
    )
    second_interrupt = store.prepare_interrupt_request_row(
        request,
        checkpoint_envelope=envelope,
        created_at=COMMITTED,
    )

    assert first_graph == second_graph
    assert first_checkpoint == second_checkpoint
    assert first_interrupt == second_interrupt
    first_checkpoint["checkpoint_envelope_json"]["state"]["job"][
        "title"
    ] = "mutated"
    first_interrupt["allowed_decision_values_json"].append("apply")
    assert second_checkpoint["checkpoint_envelope_json"] == envelope
    assert second_interrupt["allowed_decision_values_json"] == (
        request["allowed_decision_values"]
    )
    assert envelope == before_envelope
    assert request == before_request


def test_unsupported_schemas_missing_identity_and_unknown_fields_fail_closed():
    _, envelope, _, _, _, _ = _contracts()
    unsupported = deepcopy(envelope)
    unsupported["checkpoint_schema_version"] = "unsupported"
    missing = deepcopy(envelope)
    del missing["checkpoint_identity"]["owner_user_id"]
    unknown = deepcopy(envelope)
    unknown["unapproved"] = True

    with pytest.raises(ValueError, match="checkpoint_schema_version"):
        store.prepare_checkpoint_row(unsupported, committed_at=COMMITTED)
    with pytest.raises(ValueError, match="checkpoint_identity_fields"):
        store.prepare_checkpoint_row(missing, committed_at=COMMITTED)
    with pytest.raises(ValueError, match="checkpoint_envelope_fields"):
        store.prepare_checkpoint_row(unknown, committed_at=COMMITTED)


def test_completed_order_next_node_and_interrupt_boundary_fail_closed():
    _, envelope, request, _, _, _ = _contracts()
    bad_order = deepcopy(envelope)
    bad_order["completed_node_keys"] = list(
        reversed(bad_order["completed_node_keys"])
    )
    bad_next = deepcopy(envelope)
    bad_next["next_node_key"] = "apply"
    bad_node = deepcopy(request)
    bad_node["node_key"] = "finalize"

    with pytest.raises(ValueError, match="completed_node_keys"):
        store.prepare_checkpoint_row(bad_order, committed_at=COMMITTED)
    with pytest.raises(ValueError, match="next_node"):
        store.prepare_checkpoint_row(bad_next, committed_at=COMMITTED)
    with pytest.raises(ValueError):
        store.prepare_interrupt_request_row(
            bad_node,
            checkpoint_envelope=envelope,
            created_at=COMMITTED,
        )


def test_owner_job_resume_checkpoint_and_allowed_decision_mismatches_fail_closed():
    _, envelope, request, _, checkpoint, interrupt = _contracts()
    for key, value in (
        ("owner_user_id", "wrong-owner"),
        ("job_id", "wrong-job"),
        ("selected_resume_id", "wrong-resume"),
        ("checkpoint_id", "wrong-checkpoint"),
    ):
        mismatch = deepcopy(request)
        mismatch[key] = value
        with pytest.raises(ValueError):
            store.prepare_interrupt_request_row(
                mismatch,
                checkpoint_envelope=envelope,
                created_at=COMMITTED,
            )
    decisions = deepcopy(request)
    decisions["allowed_decision_values"] = ["continue_read_only", "apply"]
    with pytest.raises(ValueError, match="allowed_decision_values"):
        store.prepare_interrupt_request_row(
            decisions,
            checkpoint_envelope=envelope,
            created_at=COMMITTED,
        )
    wrong_owner_interrupt = deepcopy(interrupt)
    wrong_owner_interrupt["owner_user_id"] = "wrong-owner"
    with pytest.raises(ValueError, match="checkpoint_interrupt_identity_mismatch"):
        store.prepare_checkpoint_interrupt_commit(
            checkpoint_row=checkpoint,
            interrupt_row=wrong_owner_interrupt,
            expected_owner_user_id=checkpoint["owner_user_id"],
            expected_run_status="running",
            expected_lock_version=0,
        )


def test_secret_non_json_nonfinite_and_oversized_payloads_fail_closed():
    _, envelope, request, _, _, _ = _contracts()
    prohibited_cases = []
    for key, value in (
        ("provider_api_key", "key-value"),
        ("authorization_header", "Bearer token-value"),
        ("resume_token", "raw-token"),
        ("database_password", "password-value"),
    ):
        candidate = deepcopy(envelope)
        candidate["state"]["job"][key] = value
        prohibited_cases.append(candidate)
    non_string_key = deepcopy(envelope)
    non_string_key["state"]["job"][1] = "invalid"
    non_finite = deepcopy(envelope)
    non_finite["state"]["job"]["score"] = float("inf")
    oversized = deepcopy(envelope)
    oversized["state"]["job"]["description"] = "x" * (
        store.MAX_CHECKPOINT_ENVELOPE_BYTES + 1
    )

    for candidate in prohibited_cases:
        with pytest.raises(ValueError, match="secret_field"):
            store.prepare_checkpoint_row(candidate, committed_at=COMMITTED)
    for candidate in (non_string_key, non_finite):
        with pytest.raises(ValueError):
            store.prepare_checkpoint_row(candidate, committed_at=COMMITTED)
    with pytest.raises(ValueError, match="too_large"):
        store.prepare_checkpoint_row(oversized, committed_at=COMMITTED)
    bearer = deepcopy(request)
    bearer["reason_codes"] = ["Bearer raw-token"]
    with pytest.raises(ValueError, match="bearer"):
        store.prepare_interrupt_request_row(
            bearer,
            checkpoint_envelope=envelope,
            created_at=COMMITTED,
        )


def test_immutable_duplicate_classification_is_exact_and_conflicts_fail_closed():
    _, _, _, _, checkpoint, interrupt = _contracts()
    checkpoint_copy = deepcopy(checkpoint)
    interrupt_copy = deepcopy(interrupt)

    assert store.checkpoint_rows_are_identical(checkpoint, checkpoint_copy)
    assert store.interrupt_rows_are_identical(interrupt, interrupt_copy)
    returned_checkpoint = store.require_idempotent_checkpoint_duplicate(
        checkpoint,
        checkpoint_copy,
    )
    returned_interrupt = store.require_idempotent_interrupt_duplicate(
        interrupt,
        interrupt_copy,
    )
    assert returned_checkpoint == checkpoint
    assert returned_checkpoint is not checkpoint
    assert returned_interrupt == interrupt
    mismatch = deepcopy(checkpoint)
    mismatch["checkpoint_envelope_digest"] = "0" * 64
    with pytest.raises(ValueError, match="checkpoint_duplicate_content_conflict"):
        store.require_idempotent_checkpoint_duplicate(checkpoint, mismatch)


def test_graph_insert_is_deterministic_idempotent_only_for_exact_content():
    _, _, _, graph_run, _, _ = _contracts()

    first = store.prepare_graph_run_insert(graph_run)
    second = store.prepare_graph_run_insert(graph_run)

    assert first == second
    assert first["operation"] == "prepare_graph_run_insert"
    assert first["tables"] == ["orchestration_graph_runs"]
    assert "ON CONFLICT (graph_invocation_id) DO NOTHING" in first["sql"]
    assert "DO UPDATE" not in first["sql"]
    assert "idempotent_duplicate" in first["sql"]
    assert "existing.owner_user_id = %(owner_user_id)s" in first["sql"]
    assert first["params"] == graph_run


def test_owner_scoped_reads_bind_owner_and_current_checkpoint():
    _, _, _, graph_run, _, _ = _contracts()
    kwargs = {
        "owner_user_id": graph_run["owner_user_id"],
        "graph_invocation_id": graph_run["graph_invocation_id"],
    }
    graph_read = store.prepare_current_graph_run_read(**kwargs)
    checkpoint_read = store.prepare_current_checkpoint_read(**kwargs)
    interrupt_read = store.prepare_pending_interrupt_read(**kwargs)

    for command in (graph_read, checkpoint_read, interrupt_read):
        assert command["read_only"] is True
        assert "owner_user_id = %(owner_user_id)s" in command["sql"]
        assert command["params"]["owner_user_id"] == graph_run["owner_user_id"]
        assert command["params"]["graph_invocation_id"] == (
            graph_run["graph_invocation_id"]
        )
    assert "graph_run.current_checkpoint_id" in checkpoint_read["sql"]
    assert "graph_run.current_checkpoint_id" in interrupt_read["sql"]
    assert interrupt_read["params"]["interrupt_status"] == "pending"
    with pytest.raises(ValueError, match="owner_user_id"):
        store.prepare_current_graph_run_read(
            owner_user_id="",
            graph_invocation_id=graph_run["graph_invocation_id"],
        )


def test_atomic_commit_is_one_owner_scoped_cas_statement_for_both_records():
    _, _, _, _, checkpoint, interrupt = _contracts()
    command = store.prepare_checkpoint_interrupt_commit(
        checkpoint_row=checkpoint,
        interrupt_row=interrupt,
        expected_owner_user_id=checkpoint["owner_user_id"],
        expected_run_status="running",
        expected_lock_version=7,
    )
    sql = command["sql"]

    assert command["operation"] == "prepare_checkpoint_interrupt_commit"
    assert command["tables"] == [
        "orchestration_graph_runs",
        "orchestration_checkpoints",
        "orchestration_interrupt_requests",
    ]
    assert sql.lstrip().startswith("WITH locked_run AS")
    assert "INSERT INTO orchestration_checkpoints" in sql
    assert "INSERT INTO orchestration_interrupt_requests" in sql
    assert "UPDATE orchestration_graph_runs" in sql
    assert "FOR UPDATE" in sql
    assert "owner_user_id = %(expected_owner_user_id)s" in sql
    assert "run_status = %(expected_run_status)s" in sql
    assert "lock_version = %(expected_lock_version)s" in sql
    assert "current_checkpoint_id" in sql
    assert "lock_version = lock_version + 1" in sql
    assert "EXISTS (SELECT 1 FROM accepted_checkpoint)" in sql
    assert "EXISTS (SELECT 1 FROM accepted_interrupt)" in sql
    assert "COMMIT" not in sql
    assert "ROLLBACK" not in sql
    assert command["params"]["expected_lock_version"] == 7
    assert command["params"]["next_run_status"] == "awaiting_decision"


def test_atomic_commit_rejects_wrong_owner_status_version_and_graph_identity():
    _, _, _, _, checkpoint, interrupt = _contracts()

    with pytest.raises(ValueError, match="checkpoint_owner_mismatch"):
        store.prepare_checkpoint_interrupt_commit(
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
            expected_owner_user_id="wrong-owner",
            expected_run_status="running",
            expected_lock_version=0,
        )
    with pytest.raises(ValueError, match="expected_run_status"):
        store.prepare_checkpoint_interrupt_commit(
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
            expected_owner_user_id=checkpoint["owner_user_id"],
            expected_run_status="awaiting_decision",
            expected_lock_version=0,
        )
    with pytest.raises(ValueError, match="expected_lock_version"):
        store.prepare_checkpoint_interrupt_commit(
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
            expected_owner_user_id=checkpoint["owner_user_id"],
            expected_run_status="running",
            expected_lock_version=-1,
        )
    wrong_graph = deepcopy(interrupt)
    wrong_graph["graph_invocation_id"] = "wrong-graph"
    with pytest.raises(ValueError, match="checkpoint_interrupt_identity_mismatch"):
        store.prepare_checkpoint_interrupt_commit(
            checkpoint_row=checkpoint,
            interrupt_row=wrong_graph,
            expected_owner_user_id=checkpoint["owner_user_id"],
            expected_run_status="running",
            expected_lock_version=0,
        )


def test_atomic_sql_recognizes_only_identical_duplicates_and_unique_interrupt():
    _, _, _, _, checkpoint, interrupt = _contracts()
    command = store.prepare_checkpoint_interrupt_commit(
        checkpoint_row=checkpoint,
        interrupt_row=interrupt,
        expected_owner_user_id=checkpoint["owner_user_id"],
        expected_run_status="running",
        expected_lock_version=0,
    )
    sql = command["sql"]
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    assert "existing.checkpoint_envelope_digest" in sql
    assert "existing.checkpoint_envelope_json" in sql
    assert "existing.completed_node_keys_json" in sql
    assert "existing.interrupt_request_json" in sql
    assert sql.count("DO NOTHING") == 2
    assert "DO UPDATE" not in sql
    assert "UNIQUE (checkpoint_id, node_key)" in schema


def test_store_and_package_imports_are_inert_and_execution_dependencies_absent():
    store_source = STORE_PATH.read_text(encoding="utf-8")
    package_source = PACKAGE_PATH.read_text(encoding="utf-8")
    store_tree = ast.parse(store_source)
    package_tree = ast.parse(package_source)
    imported_modules = {
        node.module
        for node in ast.walk(store_tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(store_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert not list(package_tree.body)[1:]
    assert "langgraph" not in imported_modules
    assert "psycopg" not in imported_modules
    assert "sqlalchemy" not in imported_modules
    assert "subprocess" not in imported_modules
    assert not any(
        module and module.startswith(
            (
                "src.app",
                "src.collector",
                "src.storage.application_actions",
            )
        )
        for module in imported_modules
    )
    for token in (
        ".execute(",
        ".cursor(",
        ".commit(",
        ".rollback(",
        "connect(",
        "os.environ",
        "schema.sql",
    ):
        assert token not in store_source
    assert store.safety_declarations() == {
        "schema_executed": False,
        "database_connection_opened": False,
        "sql_executed": False,
        "transaction_committed": False,
        "checkpointer_configured": False,
        "graph_paused": False,
        "graph_resumed": False,
        "decision_accepted": False,
        "authorization_created": False,
        "production_activated": False,
    }


def test_phase8_checkpoint_and_interrupt_contracts_remain_unchanged():
    _, envelope, request, _, _, _ = _contracts()

    assert harness.CHECKPOINT_GRAPH_ENGINE == "langgraph-evidence-chain"
    assert (
        harness.GRAPH_STATE_SCHEMA_VERSION
        == "evidence-chain-graph-state-v1"
    )
    assert (
        harness.CHECKPOINT_SCHEMA_VERSION
        == "evidence-chain-checkpoint-envelope-v1"
    )
    assert (
        harness.OPERATOR_REVIEW_INTERRUPT_REQUEST_SCHEMA_VERSION
        == "operator-review-interrupt-request-v1"
    )
    assert envelope["durable"] is False
    assert envelope["resumable"] is False
    assert envelope["persistence_performed"] is False
    assert request["persistent"] is False
    assert request["resumable"] is False
    assert request["application_authorization"] is False
    assert request["resume_authorization"] is False

import ast
from copy import deepcopy
from pathlib import Path

import pytest
from langgraph.checkpoint import memory as checkpoint_memory
from langgraph.checkpoint.memory import InMemorySaver

from src.agents import evidence_chain_langgraph_harness as harness


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "src/agents/evidence_chain_langgraph_harness.py"
EXPECTED_AGENT_KEYS = [
    "jd_intelligence",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]
EXPECTED_ARTIFACT_KEYS = [
    harness.ARTIFACT_KEYS_BY_AGENT[key] for key in EXPECTED_AGENT_KEYS
]


def _job(job_id="job-phase9-step6", **overrides):
    row = {
        "job_id": job_id,
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "url": "https://example.test/jobs/phase9-step6",
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
    row.update(overrides)
    return row


def _resume_context(selected_resume_id="resume-main"):
    return {
        "selected_resume_id": selected_resume_id,
        "resume_variants": [
            {
                "resume_id": selected_resume_id,
                "skills": ["Python", "SQL", "RAG"],
                "raw_text": "Built Python, SQL, and RAG systems.",
            }
        ],
    }


def _start(**overrides):
    values = {
        "job": _job(),
        "resume_context": _resume_context(),
        "pipeline_run_id": "run-phase9-step6",
        "owner_user_id": "owner-phase9-step6",
        "context_id": "context-phase9-step6",
        "enabled": True,
    }
    values.update(overrides)
    job = values.pop("job")
    return harness._start_operator_review_pause_resume_session(job, **values)


def _decision_kwargs(session, result, **overrides):
    values = {
        "interrupt_request": deepcopy(result["interrupt_request"]),
        "expected_owner_user_id": session.owner_user_id,
        "expected_pipeline_run_id": session.pipeline_run_id,
        "expected_context_id": session.context_id,
        "expected_job_id": session.job_id,
        "expected_job_index": session.job_index,
        "expected_selected_resume_id": session.selected_resume_id,
        "expected_graph_invocation_id": session.graph_invocation_id,
        "expected_repository_checkpoint_id": session.repository_checkpoint_id,
        "expected_langgraph_checkpoint_id": session.langgraph_checkpoint_id,
    }
    values.update(overrides)
    return values


def _decide(session, result, decision, **overrides):
    return harness._apply_operator_review_pause_resume_decision(
        session,
        decision_value=decision,
        **_decision_kwargs(session, result, **overrides),
    )


def _snapshot(session):
    return session._compiled_graph.get_state(
        harness._experimental_state_lookup_config(
            session.paused_config,
            session._checkpointer,
        )
    )


def test_experimental_gate_defaults_off_without_compile_or_checkpointer(monkeypatch):
    assert harness.LANGGRAPH_OPERATOR_REVIEW_PAUSE_RESUME_GATE_NAME == (
        "APPLYLENS_AGENTIC_LANGGRAPH_OPERATOR_REVIEW_PAUSE_RESUME_ENABLED"
    )

    def fail(*_args, **_kwargs):
        raise AssertionError("disabled start must remain inert")

    monkeypatch.setattr(
        harness,
        "_compile_operator_review_pause_resume_graph",
        fail,
    )
    monkeypatch.setattr(checkpoint_memory, "InMemorySaver", fail)
    session, result = harness._start_operator_review_pause_resume_session(
        _job()
    )

    assert session is None
    assert result["status"] == "disabled"
    assert result["enabled"] is False
    assert result["default_off"] is True
    assert result["process_restart_supported"] is False


def test_real_start_uses_memory_saver_and_static_pause_after_six_nodes():
    session, result = _start()
    snapshot = _snapshot(session)

    assert isinstance(session._checkpointer, InMemorySaver)
    assert session.session_status == "awaiting_decision"
    assert snapshot.next == ("finalize",)
    assert snapshot.interrupts == ()
    assert snapshot.values["ordered_node_keys"] == EXPECTED_AGENT_KEYS
    assert result["completed_node_keys"] == EXPECTED_AGENT_KEYS
    assert result["artifact_keys"] == EXPECTED_ARTIFACT_KEYS
    assert result["safe_next_node"] == "finalize"
    artifacts = snapshot.values["artifacts"]
    assert all(key in artifacts for key in EXPECTED_ARTIFACT_KEYS)
    assert "evidence_chain_bundle" not in snapshot.values
    assert "trace_payload" not in snapshot.values
    assert "agent_evidence_chain_bundle" not in artifacts
    assert "agent_evidence_chain_trace_payload" not in artifacts


def test_pause_identities_envelope_and_interrupt_request_are_exact_and_separate():
    session, result = _start()
    snapshot = _snapshot(session)
    restored = harness._deserialize_checkpoint_envelope(
        harness._serialize_checkpoint_envelope(
            result["checkpoint_envelope"]
        )
    )
    validated = harness._validate_operator_review_interrupt_request(
        result["interrupt_request"],
        snapshot.values,
    )

    assert session.graph_invocation_id == session.langgraph_thread_id
    assert result["graph_invocation_id"] == result["langgraph_thread_id"]
    assert session.repository_checkpoint_id == (
        restored["checkpoint_identity"]["checkpoint_id"]
    )
    assert session.langgraph_checkpoint_id == (
        snapshot.config["configurable"]["checkpoint_id"]
    )
    assert session.repository_checkpoint_id != session.langgraph_checkpoint_id
    assert validated == result["interrupt_request"]
    assert session.checkpoint_namespace == (
        harness.LANGGRAPH_OPERATOR_REVIEW_PAUSE_RESUME_CHECKPOINT_NAMESPACE
    )


def test_start_result_is_serializable_read_only_and_never_exposes_runtime_objects():
    _, result = _start()
    harness._canonical_checkpoint_json(result)
    assert "checkpointer" not in result
    assert "compiled_graph" not in result
    assert result["status"] == "awaiting_decision"
    for field in (
        "read_only",
        "diagnostic_only",
    ):
        assert result[field] is True
    for field in (
        "durable",
        "persistent",
        "process_restart_supported",
        "application_authorization",
        "resume_text_mutation_authorization",
        "queue_mutation_authorization",
        "operator_state_mutation_authorization",
        "patch_application_authorization",
    ):
        assert result[field] is False


def test_continue_read_only_executes_only_finalize_and_matches_normal_result(monkeypatch):
    calls = []
    node_names = {
        "_jd_intelligence_node",
        "_resume_match_node",
        "_critic_node",
        "_job_prioritization_node",
        "_tailoring_decision_node",
        "_operator_review_node",
        "_finalize_node",
    }
    originals = {name: getattr(harness, name) for name in node_names}
    for name, original in originals.items():
        def wrapped(state, *, _name=name, _original=original):
            calls.append(_name)
            return _original(state)

        monkeypatch.setattr(harness, name, wrapped)

    session, paused = _start()
    assert calls == [
        "_jd_intelligence_node",
        "_resume_match_node",
        "_critic_node",
        "_job_prioritization_node",
        "_tailoring_decision_node",
        "_operator_review_node",
    ]
    resumed = _decide(session, paused, "continue_read_only")

    assert calls[-1] == "_finalize_node"
    assert calls.count("_finalize_node") == 1
    assert all(calls.count(name) == 1 for name in node_names)
    assert resumed["status"] == "completed"
    assert resumed["decision"] == "continue_read_only"
    assert resumed["resume_consumed"] is True
    assert resumed["resumed"] is True
    assert resumed["completed"] is True
    assert resumed["application_authorization"] is False
    assert session.session_status == "completed"
    assert session.finalization_completed is True
    assert _snapshot_after_completion(session).next == ()

    uninterrupted = harness.execute_langgraph_evidence_chain(
        [_job()],
        resume_context=_resume_context(),
        pipeline_run_id="run-phase9-step6",
        owner_user_id="owner-phase9-step6",
        context_id="context-phase9-step6",
        enabled=True,
        strict=True,
    )
    assert resumed["normal_result"] == uninterrupted["per_job_results"][0]


def _snapshot_after_completion(session):
    config = {
        "configurable": {
            "thread_id": session.langgraph_thread_id,
            "checkpoint_ns": "",
            "applylens_checkpoint_namespace": session.checkpoint_namespace,
        }
    }
    return session._compiled_graph.get_state(
        harness._experimental_state_lookup_config(
            config,
            session._checkpointer,
        )
    )


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    (("needs_revision", "needs_revision"), ("cancel", "cancelled")),
)
def test_non_continue_decisions_close_without_finalization(
    monkeypatch,
    decision,
    expected_status,
):
    calls = []
    original = harness._finalize_node

    def finalize(state):
        calls.append("finalize")
        return original(state)

    monkeypatch.setattr(harness, "_finalize_node", finalize)
    session, paused = _start()
    result = _decide(session, paused, decision)

    assert calls == []
    assert session.session_status == expected_status
    assert session.decision_consumed is True
    assert session.finalization_completed is False
    assert result["status"] == expected_status
    assert result["resume_consumed"] is True
    assert result["resumed"] is False
    assert result["completed"] is False
    assert result["final_evidence_bundle"] == {}
    assert _snapshot(session).next == ("finalize",)
    if decision == "needs_revision":
        assert result["durable_terminal_result_policy"] == (
            "product_decision_pending"
        )


@pytest.mark.parametrize(
    ("override_key", "override_value", "error"),
    (
        ("expected_owner_user_id", "other-owner", "owner_user_id"),
        ("expected_pipeline_run_id", "other-run", "pipeline_run_id"),
        ("expected_context_id", "other-context", "context_id"),
        ("expected_job_id", "other-job", "job_id"),
        ("expected_job_index", 4, "job_index"),
        ("expected_selected_resume_id", "other-resume", "selected_resume_id"),
        ("expected_graph_invocation_id", "other-graph", "graph_invocation_id"),
        (
            "expected_repository_checkpoint_id",
            "other-repository-checkpoint",
            "repository_checkpoint_id",
        ),
        (
            "expected_langgraph_checkpoint_id",
            "other-langgraph-checkpoint",
            "langgraph_checkpoint_id",
        ),
    ),
)
def test_decision_rejects_every_mismatched_identity_before_resume(
    override_key,
    override_value,
    error,
):
    session, paused = _start()
    with pytest.raises(ValueError, match=error):
        _decide(
            session,
            paused,
            "continue_read_only",
            **{override_key: override_value},
        )
    assert session.decision_consumed is False
    assert session.session_status == "awaiting_decision"
    assert _snapshot(session).next == ("finalize",)


def test_altered_interrupt_request_and_artifact_digest_fail_closed():
    session, paused = _start()
    altered = deepcopy(paused["interrupt_request"])
    altered["operator_review_artifact_digest"] = "0" * 64
    with pytest.raises(ValueError, match="interrupt_request"):
        _decide(
            session,
            paused,
            "continue_read_only",
            interrupt_request=altered,
        )
    assert session.decision_consumed is False

    session.operator_review_artifact_digest = "0" * 64
    with pytest.raises(ValueError, match="interrupt"):
        _decide(session, paused, "continue_read_only")
    assert session.decision_consumed is False


def test_duplicate_decision_closed_session_and_unsupported_schema_fail_closed():
    session, paused = _start()
    _decide(session, paused, "continue_read_only")
    for decision in ("continue_read_only", "needs_revision", "cancel"):
        with pytest.raises(ValueError, match="not_awaiting"):
            _decide(session, paused, decision)

    session2, paused2 = _start()
    session2.session_schema_version = "unsupported"
    with pytest.raises(ValueError, match="schema_unsupported"):
        _decide(session2, paused2, "continue_read_only")


def test_live_session_reuse_and_different_initial_input_are_rejected():
    session, _ = _start()
    with pytest.raises(ValueError, match="session_already_exists"):
        _start(
            job=_job("different-job"),
            existing_session=session,
        )
    assert session.session_status == "awaiting_decision"


def test_historical_or_mutated_pause_configuration_is_not_accepted():
    session, paused = _start()
    session.paused_config["configurable"]["checkpoint_id"] = "historical"
    with pytest.raises(ValueError, match="pause_boundary|checkpoint"):
        _decide(session, paused, "continue_read_only")
    assert session.decision_consumed is False


def test_normal_harness_remains_uninterrupted_and_exposes_no_pause_fields():
    result = harness.execute_langgraph_evidence_chain(
        [_job()],
        resume_context=_resume_context(),
        pipeline_run_id="run-normal",
        owner_user_id="owner-normal",
        context_id="context-normal",
        enabled=True,
        strict=True,
    )
    assert result["reason"] == "langgraph_evidence_chain_completed"
    assert result["per_job_results"][0]["ordered_node_keys"] == (
        EXPECTED_AGENT_KEYS
    )
    for key in (
        "interrupt_request",
        "repository_checkpoint_id",
        "langgraph_checkpoint_id",
        "resume_consumed",
        "process_restart_supported",
    ):
        assert key not in result


def test_source_uses_only_static_private_inmemory_pause_and_validated_resume():
    source = HARNESS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "from langgraph.checkpoint.memory import InMemorySaver" in source
    assert 'interrupt_after=["operator_review"]' in source
    assert "Command(" not in source
    assert "add_conditional_edges" not in source
    assert "global_session" not in source

    forbidden_imports = {
        "psycopg",
        "sqlalchemy",
        "pickle",
        "src.storage",
        "src.pipeline",
        "src.app",
    }
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for imported in imports
        for forbidden in forbidden_imports
    )
    forbidden_calls = {
        "execute",
        "cursor",
        "commit",
        "connect",
        "write_text",
        "open",
        "run_chat_completion",
        "execute_application",
        "submit_application",
        "mark_applied",
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    }
    assert forbidden_calls.isdisjoint(called_attributes)
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    }
    assert {"interrupt", "Command"}.isdisjoint(called_names)

    none_invokes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "invoke"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value is None
    ]
    assert len(none_invokes) == 1
    enclosing = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_apply_operator_review_pause_resume_decision"
    )
    assert none_invokes[0] in set(ast.walk(enclosing))


def test_no_caller_input_mutation_or_restart_durability_claim():
    job = _job()
    resume = _resume_context()
    before_job, before_resume = deepcopy(job), deepcopy(resume)
    session, paused = _start(job=job, resume_context=resume)
    result = _decide(session, paused, "continue_read_only")

    assert job == before_job
    assert resume == before_resume
    assert paused["durable"] is False
    assert paused["persistent"] is False
    assert paused["process_restart_supported"] is False
    assert result["durable"] is False
    assert result["process_restart_supported"] is False

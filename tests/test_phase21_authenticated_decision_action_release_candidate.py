from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import inspect

from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver
import pytest

from src.agents import production_human_checkpoint_coordinator as coordinator_owner
from src.app import api, services
from tests.test_phase20_production_human_review_checkpoint import (
    EXPIRES,
    NOW,
    OWNER,
    TOKEN,
    _Repository,
    _authorize,
    _coordinator,
    _pause,
    _resume,
)


ENABLED_ENV = {
    "APPLYLENS_PRODUCTION_DURABLE_GRAPH_RUNTIME_ENABLED": "1",
    "APPLYLENS_PRODUCTION_HUMAN_CHECKPOINT_ENABLED": "1",
}
ENDPOINT = "/api/production-human-reviews/review-phase21/decision"


def _action(instance, pause, **overrides):
    values = {
        "owner_user_id": OWNER,
        "actor_id": OWNER,
        "graph_invocation_id": pause.graph_invocation_id,
        "repository_checkpoint_id": pause.repository_checkpoint_id,
        "interrupt_request_id": pause.interrupt_request_id,
        "decision_value": "continue_read_only",
        "client_idempotency_key": "phase21-action",
        "decision_reason": "bounded read-only continuation",
        "continuation_token": TOKEN,
        "env": ENABLED_ENV,
        "coordinator": instance,
        "time_source": lambda: datetime(
            2026, 7, 30, 12, 0, tzinfo=timezone.utc
        ),
    }
    values.update(overrides)
    return services.production_human_review_decision_action_payload(
        **values
    )


@dataclass
class _Result:
    status: str
    classification: str
    graph_invocation_id: str = "graph-phase21"
    interrupt_request_id: str = "review-phase21"
    repository_checkpoint_id: str = "checkpoint-phase21"
    decision_id: str = "decision-phase21"
    terminal_result_id: str = ""
    review_artifact_digest: str = ""
    human_review_status: str = ""


class _CountingCoordinator:
    def __init__(self, decision=None, resumed=None):
        self.decision = decision or _Result(
            "resume_authorized", "applied"
        )
        self.resumed = resumed or _Result(
            "completed",
            "applied",
            terminal_result_id="terminal-phase21",
            review_artifact_digest="a" * 64,
            human_review_status="human_reviewed",
        )
        self.record_calls = []
        self.resume_calls = []

    def record_decision(self, **kwargs):
        self.record_calls.append(deepcopy(kwargs))
        return self.decision

    def resume(self, **kwargs):
        self.resume_calls.append(deepcopy(kwargs))
        return self.resumed


def _request_payload(**overrides):
    payload = {
        "graph_invocation_id": "graph-phase21",
        "repository_checkpoint_id": "checkpoint-phase21",
        "decision_value": "continue_read_only",
        "client_idempotency_key": "idempotency-phase21",
        "decision_reason": "continue read only",
        "continuation_token": "phase21-continuation-token",
    }
    payload.update(overrides)
    return payload


def _authenticated_client(monkeypatch, owner=OWNER):
    def guard(request):
        request.state.auth_user = {
            "user_id": owner,
            "email": "operator@example.invalid",
        }
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def test_01_exact_action_version_and_decision_vocabulary():
    assert services.PRODUCTION_HUMAN_REVIEW_ACTION_VERSION == (
        "production-human-review-authenticated-action-v1"
    )
    assert services.PRODUCTION_HUMAN_REVIEW_DECISIONS == (
        "continue_read_only",
        "needs_revision",
        "cancel",
    )


def test_02_action_gates_default_off_without_coordinator_work():
    fake = _CountingCoordinator()
    result = services.production_human_review_decision_action_payload(
        owner_user_id=OWNER,
        actor_id=OWNER,
        graph_invocation_id="graph",
        repository_checkpoint_id="checkpoint",
        interrupt_request_id="review",
        decision_value="continue_read_only",
        client_idempotency_key="key",
        continuation_token="long-enough-secret-token",
        env={},
        coordinator=fake,
    )
    assert result["failure_classification"] == "unavailable"
    assert fake.record_calls == fake.resume_calls == []


def test_03_request_contract_fails_closed():
    cases = [
        ("owner_user_id", "", "authenticated_owner_required"),
        ("actor_id", "other-owner", "authenticated_actor_owner_mismatch"),
        ("graph_invocation_id", "", "graph_invocation_id_required"),
        ("repository_checkpoint_id", "", "repository_checkpoint_id_required"),
        ("interrupt_request_id", "", "interrupt_request_id_required"),
        ("client_idempotency_key", "", "client_idempotency_key_required"),
        ("decision_value", "apply", "unsupported"),
    ]
    for field, value, reason in cases:
        fake = _CountingCoordinator()
        values = {
            "owner_user_id": OWNER,
            "actor_id": OWNER,
            "graph_invocation_id": "graph",
            "repository_checkpoint_id": "checkpoint",
            "interrupt_request_id": "review",
            "decision_value": "continue_read_only",
            "client_idempotency_key": "key",
            "continuation_token": "long-enough-secret-token",
            "env": ENABLED_ENV,
            "coordinator": fake,
        }
        values[field] = value
        with pytest.raises(ValueError, match=reason):
            services.production_human_review_decision_action_payload(**values)
        assert fake.record_calls == fake.resume_calls == []


def test_04_continue_requires_bounded_continuation_token():
    fake = _CountingCoordinator()
    with pytest.raises(ValueError, match="continuation_token_invalid"):
        services.production_human_review_decision_action_payload(
            owner_user_id=OWNER,
            actor_id=OWNER,
            graph_invocation_id="graph",
            repository_checkpoint_id="checkpoint",
            interrupt_request_id="review",
            decision_value="continue_read_only",
            client_idempotency_key="key",
            continuation_token="short",
            env=ENABLED_ENV,
            coordinator=fake,
        )


@pytest.mark.parametrize("decision", ["needs_revision", "cancel"])
def test_05_non_continue_rejects_continuation_token(decision):
    with pytest.raises(ValueError, match="continuation_token_not_allowed"):
        services.production_human_review_decision_action_payload(
            owner_user_id=OWNER,
            actor_id=OWNER,
            graph_invocation_id="graph",
            repository_checkpoint_id="checkpoint",
            interrupt_request_id="review",
            decision_value=decision,
            client_idempotency_key="key",
            continuation_token="long-enough-secret-token",
            env=ENABLED_ENV,
            coordinator=_CountingCoordinator(),
        )


def test_06_action_to_real_coordinator_completes_read_only():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    result = _action(instance, _pause(instance))
    assert result["ok"] is True
    assert result["continuation_status"] == "completed"
    assert result["human_review_status"] == "human_reviewed"
    assert len(repository.decisions) == 1
    assert len(repository.authorizations) == 1
    assert len(repository.consumptions) == 1
    assert len(repository.terminals) == 1


def test_07_plaintext_token_and_hash_are_absent_from_response_and_rows():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    result = _action(instance, _pause(instance))
    serialized_result = repr(result)
    serialized_rows = repr(
        (
            repository.decisions,
            repository.consumptions,
            repository.terminals,
        )
    )
    assert TOKEN not in serialized_result
    assert TOKEN not in serialized_rows
    assert "authorization_token_hash" not in serialized_result
    stored = next(iter(repository.authorizations.values()))
    assert stored["authorization_token_hash"] == (
        coordinator_owner.hash_resume_authorization_token(TOKEN)
    )


def test_08_duplicate_identical_completed_action_is_bounded_replay():
    repository, saver = _Repository(), MemorySaver()
    first = _coordinator(repository, saver)
    pause = _pause(first)
    completed = _action(first, pause)
    replay = _action(_coordinator(repository, saver), pause)
    assert completed["terminal_status"] == "terminal"
    assert replay["ok"] is True
    assert replay["continuation_status"] == "replayed"
    assert replay["idempotency_status"] == "replayed"
    assert len(repository.decisions) == len(repository.consumptions) == 1
    assert len(repository.terminals) == 1


def test_09_conflicting_completed_action_fails_closed():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    _action(instance, pause)
    conflict = _action(
        _coordinator(repository, saver),
        pause,
        client_idempotency_key="different-key",
    )
    assert conflict["ok"] is False
    assert conflict["failure_classification"] == "duplicate_conflict"
    assert len(repository.decisions) == len(repository.consumptions) == 1


def test_10_authenticated_wrong_owner_exposes_no_state():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    result = _action(
        instance,
        pause,
        owner_user_id="wrong-owner",
        actor_id="wrong-owner",
    )
    assert result["ok"] is False
    assert result["failure_classification"] == "not_found"
    assert result["read_only_artifact"] == {
        "digest": "",
        "terminal_result_id": "",
    }


@pytest.mark.parametrize(
    ("decision", "status"),
    [
        ("needs_revision", "revision_required"),
        ("cancel", "cancelled"),
    ],
)
def test_11_non_continue_records_once_and_never_resumes(decision, status):
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    result = _action(
        instance,
        pause,
        decision_value=decision,
        continuation_token="",
    )
    assert result["ok"] is True
    assert result["decision_status"] == status
    assert result["continuation_status"] == "not_requested"
    assert repository.authorizations == {}
    assert repository.consumptions == {}
    assert repository.terminals == {}


def test_12_expired_same_action_token_fails_closed():
    times = iter(
        [
            datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc),
            datetime(2026, 7, 30, 12, 10, tzinfo=timezone.utc),
        ]
    )
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    result = _action(instance, _pause(instance), time_source=lambda: next(times))
    assert result["ok"] is False
    assert result["failure_classification"] == "stale_state"
    assert repository.consumptions == {}
    assert repository.terminals == {}


def test_13_reused_token_cannot_resume_coordinator_twice():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    decision = _authorize(instance, pause)
    first = _resume(instance, pause, decision)
    second = _resume(instance, pause, decision)
    assert first.status == "completed"
    assert second.status == "resume_not_consumed"
    assert second.classification == "stale_state"
    assert len(repository.consumptions) == 1


def test_14_concurrent_consumers_cannot_both_claim_authorization():
    repository, saver = _Repository(), MemorySaver()
    instance = _coordinator(repository, saver)
    pause = _pause(instance)
    decision = _authorize(instance, pause)
    authorization = repository.authorizations[decision.decision_id]
    first = coordinator_owner.production.prepare_human_review_consumption_row(
        authorization,
        consumer_instance_id="consumer-a",
        claimed_at="2026-07-30T12:05:00Z",
    )
    second = coordinator_owner.production.prepare_human_review_consumption_row(
        authorization,
        consumer_instance_id="consumer-b",
        claimed_at="2026-07-30T12:05:00Z",
    )
    token_hash = coordinator_owner.hash_resume_authorization_token(TOKEN)
    assert repository.consume_resume_authorization(
        first, authorization_token_hash=token_hash
    ).classification == "applied"
    assert repository.consume_resume_authorization(
        second, authorization_token_hash=token_hash
    ).classification == "duplicate_conflict"


def test_15_response_never_grants_application_or_ats_authority():
    result = _action(_CountingCoordinator(), _Result("pause", "applied"))
    assert result["mutation_authority"] is False
    assert result["application_authority"] is False
    assert result["ats_authority"] is False
    assert result["human_review_is_application_approval"] is False
    for field in (
        "automatic_application_count",
        "mark_applied_count",
        "resume_replacement_count",
        "recruiter_communication_count",
        "ats_submission_count",
    ):
        assert result[field] == 0


def test_16_action_invokes_no_tailoring_provider_or_cache_owner(monkeypatch):
    prohibited = []
    for name in (
        "run_tailoring",
        "provider_call",
        "cache_read",
        "cache_write",
        "mark_applied",
        "submit_application",
    ):
        monkeypatch.setattr(
            services,
            name,
            lambda *args, _name=name, **kwargs: prohibited.append(_name),
            raising=False,
        )
    result = _action(_CountingCoordinator(), _Result("pause", "applied"))
    assert result["ok"] is True
    assert prohibited == []


def test_17_api_uses_authenticated_owner_and_actor(monkeypatch):
    captured = {}

    def action(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "decision_status": "completed",
            "failure_classification": "",
        }

    monkeypatch.setattr(
        services,
        "production_human_review_decision_action_payload",
        action,
    )
    response = _authenticated_client(monkeypatch).post(
        ENDPOINT, json=_request_payload()
    )
    assert response.status_code == 200
    assert captured["owner_user_id"] == OWNER
    assert captured["actor_id"] == OWNER
    assert captured["interrupt_request_id"] == "review-phase21"


def test_18_unauthenticated_api_request_is_rejected(monkeypatch):
    monkeypatch.setattr(
        api,
        "auth_guard_response",
        lambda request: JSONResponse(
            {"detail": "Not authenticated."}, status_code=401
        ),
    )
    response = TestClient(api.app).post(
        ENDPOINT, json=_request_payload()
    )
    assert response.status_code == 401


def test_19_client_owner_override_is_rejected(monkeypatch):
    called = []
    monkeypatch.setattr(
        services,
        "production_human_review_decision_action_payload",
        lambda **kwargs: called.append(kwargs),
    )
    response = _authenticated_client(monkeypatch).post(
        ENDPOINT,
        json=_request_payload(owner_user_id="attacker"),
    )
    assert response.status_code == 422
    assert called == []


def test_20_api_maps_wrong_owner_to_not_found_without_artifact(monkeypatch):
    monkeypatch.setattr(
        services,
        "production_human_review_decision_action_payload",
        lambda **kwargs: {
            "ok": False,
            "failure_classification": "not_found",
            "read_only_artifact": {"digest": "", "terminal_result_id": ""},
        },
    )
    response = _authenticated_client(
        monkeypatch, owner="wrong-owner"
    ).post(ENDPOINT, json=_request_payload())
    assert response.status_code == 404
    assert response.json()["detail"]["read_only_artifact"]["digest"] == ""


def test_21_secret_token_is_redacted_by_request_contract():
    request = api.ProductionHumanReviewDecisionRequest(
        **_request_payload()
    )
    assert "phase21-continuation-token" not in repr(request)
    assert request.continuation_token is not None
    assert request.continuation_token.get_secret_value() == (
        "phase21-continuation-token"
    )


def test_22_action_source_has_no_provider_cache_or_external_action_imports():
    source = inspect.getsource(
        services.production_human_review_decision_action_payload
    )
    for prohibited in (
        "llm_client",
        "run_tailoring",
        "application_execution_queue",
        "mark_applied",
        "submit_application",
        "recruiter",
        "dotenv",
    ):
        assert prohibited not in source


def test_23_dedicated_postgres_authenticated_action_and_restart_replay():
    import os
    from urllib.parse import urlsplit

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
    assert urlsplit(repository_target).path.strip("/") == (
        "job_scraper_phase9_test"
    )
    assert urlsplit(saver_target).path.strip("/") == (
        "job_scraper_phase9_test"
    )

    from src.storage.admin_tools.durable_orchestration import apply_schema
    from src.storage.durable_orchestration import (
        langgraph_postgres,
        postgres_connection,
        repository as repository_owner,
    )
    from tests.test_phase9_step16a_durable_decision_authorization_runtime_contract import (
        _cleanup,
        _counts,
    )

    assert apply_schema.DurableOrchestrationSchemaExecutor(
        enabled=True
    ).apply(database_url=repository_target).outcome == "applied"
    owner = "owner-phase21-postgres"
    artifact = {
        "parse_ok": True,
        "parsed": {"tailoring_actions": ["injected bounded fixture"]},
        "raw_response": "",
        "provider_call_count": 1,
    }
    artifact_digest = coordinator_owner.production.canonical_digest(
        artifact, field="bounded_tailoring_review_artifact"
    )
    graph_row = coordinator_owner.production.prepare_graph_run_row(
        graph_version=(
            coordinator_owner.PRODUCTION_HUMAN_REVIEW_GRAPH_VERSION
        ),
        state_version=(
            coordinator_owner.PRODUCTION_HUMAN_REVIEW_STATE_VERSION
        ),
        owner_user_id=owner,
        pipeline_run_id="run-phase21-postgres",
        context_id="context-phase21-postgres",
        job_id="job-phase21-postgres",
        job_index=0,
        selected_resume_id="resume-phase21-postgres.pdf",
        production_node_key=(
            coordinator_owner.production.PRODUCTION_HUMAN_REVIEW_NODE
        ),
        input_digest=artifact_digest,
        created_at=NOW,
    )
    graph_id = graph_row["graph_invocation_id"]
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=repository_target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase21-test-repository",
    )
    _cleanup(factory, owner=owner, graph_id=graph_id)
    action_env = {
        **ENABLED_ENV,
        "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL": (
            repository_target
        ),
        "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_DATABASE_URL": (
            saver_target
        ),
    }
    try:
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase21-test-pause",
        ) as saver:
            saver.delete_thread(graph_id)
            pause = (
                coordinator_owner.ProductionHumanCheckpointCoordinator(
                    repository=(
                        repository_owner.DurableOrchestrationRepository(
                            factory, enabled=True
                        )
                    ),
                    saver=saver,
                    consumer_instance_id="phase21-pause",
                    enabled=True,
                ).create_or_reopen_pause(
                    bounded_tailoring_result=artifact,
                    owner_user_id=owner,
                    pipeline_run_id="run-phase21-postgres",
                    context_id="context-phase21-postgres",
                    job_id="job-phase21-postgres",
                    job_index=0,
                    selected_resume_id="resume-phase21-postgres.pdf",
                    created_at=NOW,
                )
            )
        arguments = {
            "owner_user_id": owner,
            "actor_id": owner,
            "graph_invocation_id": graph_id,
            "repository_checkpoint_id": pause.repository_checkpoint_id,
            "interrupt_request_id": pause.interrupt_request_id,
            "decision_value": "continue_read_only",
            "client_idempotency_key": "phase21-postgres-action",
            "decision_reason": "bounded read-only continuation",
            "continuation_token": "phase21-postgres-continuation-token",
            "env": action_env,
            "time_source": lambda: datetime(
                2026, 7, 30, 12, 0, tzinfo=timezone.utc
            ),
            "consumer_instance_id": "phase21-action",
        }
        completed = (
            services.production_human_review_decision_action_payload(
                **arguments
            )
        )
        replay = services.production_human_review_decision_action_payload(
            **arguments
        )
        assert completed["continuation_status"] == "completed"
        assert replay["continuation_status"] == "replayed"
        counts = _counts(factory, owner=owner, graph_id=graph_id)
        assert counts["orchestration_human_decisions"] == 1
        assert counts["orchestration_resume_authorizations"] == 1
        assert counts["orchestration_resume_consumptions"] == 1
        assert counts["orchestration_terminal_results"] == 1
    finally:
        _cleanup(factory, owner=owner, graph_id=graph_id)
        with langgraph_postgres.open_langgraph_postgres_saver(
            enabled=True,
            database_url=saver_target,
            application_name="applylens-phase21-test-cleanup",
        ) as saver:
            saver.delete_thread(graph_id)

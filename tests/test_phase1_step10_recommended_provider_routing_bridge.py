from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.app import provider_model_routing_service as routing


ROOT = Path(__file__).resolve().parents[1]

OWNER = (
    ROOT
    / "src/app/provider_model_routing_service.py"
)


def _recommendation(
    *,
    status="recommended",
    provider="groq",
    model="openai/gpt-oss-20b",
):
    return {
        "workload_id": "skill_extraction",
        "recommendation_status": status,
        "provider": provider,
        "model": model,
        "selection_basis": (
            "durable_quality_tie_latency_tiebreak"
        ),
        "task_contract_sha256": "a" * 64,
        "qualification_binding_sha256": "b" * 64,
        "evidence_sha256": "c" * 64,
        "review_sha256": None,
    }


def test_aggregate_routing_statuses_are_safe_and_preserve_policy_order(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    monkeypatch.setattr(
        routing,
        "build_provider_model_recommendation_policy",
        lambda payload: {
            "workloads": [
                {
                    "workload_id": "skill_extraction",
                    "recommendation_status": "recommended",
                    "provider": "groq",
                    "model": "openai/gpt-oss-20b",
                    "selection_basis": "quality",
                    "task_contract_sha256": "secret-task",
                    "qualification_binding_sha256": "secret-binding",
                    "evidence_sha256": "secret-evidence",
                    "review_sha256": None,
                },
                {
                    "workload_id": "job_fit_evaluation",
                    "recommendation_status": (
                        "fail_closed_zero_qualified"
                    ),
                    "provider": None,
                    "model": None,
                    "selection_basis": None,
                    "task_contract_sha256": "secret-task-2",
                },
                {
                    "workload_id": "manual_provider_preview",
                    "recommendation_status": "blocked_non_live",
                    "provider": None,
                    "model": None,
                    "selection_basis": None,
                },
            ]
        },
    )

    payload = routing.list_provider_model_routing_statuses()

    assert payload == {
        "workloads": [
            {
                "workload_id": "skill_extraction",
                "recommendation_status": "recommended",
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "selection_basis": "quality",
            },
            {
                "workload_id": "job_fit_evaluation",
                "recommendation_status": (
                    "fail_closed_zero_qualified"
                ),
                "provider": None,
                "model": None,
                "selection_basis": None,
            },
            {
                "workload_id": "manual_provider_preview",
                "recommendation_status": "blocked_non_live",
                "provider": None,
                "model": None,
                "selection_basis": None,
            },
        ]
    }

    rendered = repr(payload)

    assert "secret-task" not in rendered
    assert "secret-binding" not in rendered
    assert "secret-evidence" not in rendered


def test_resolve_uses_authoritative_registry_and_exact_workload(
    monkeypatch,
):
    registry_payload = {"registry": "sentinel"}
    observed = {}

    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: registry_payload,
    )

    def fake_read(payload, workload_id):
        observed["payload"] = payload
        observed["workload_id"] = workload_id
        return _recommendation()

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        fake_read,
    )

    result = routing.resolve_recommended_user_provider_route(
        "skill_extraction"
    )

    assert observed == {
        "payload": registry_payload,
        "workload_id": "skill_extraction",
    }

    assert result == {
        "workload_id": "skill_extraction",
        "recommendation_status": "recommended",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "selection_basis": (
            "durable_quality_tie_latency_tiebreak"
        ),
        "task_contract_sha256": "a" * 64,
        "qualification_binding_sha256": "b" * 64,
        "evidence_sha256": "c" * 64,
        "review_sha256": None,
    }


@pytest.mark.parametrize(
    "status",
    [
        "fail_closed_zero_qualified",
        "blocked_non_live",
    ],
)
def test_non_recommended_workload_fails_before_runtime(
    monkeypatch,
    status,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        lambda payload, workload_id: _recommendation(
            status=status,
            provider=None,
            model=None,
        ),
    )

    runtime_called = False

    def forbidden_runtime(**kwargs):
        nonlocal runtime_called
        runtime_called = True
        raise AssertionError("runtime must not be called")

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        forbidden_runtime,
    )

    with pytest.raises(
        routing.RecommendedProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_recommended_user_chat_completion_with_metadata(
            owner_user_id="owner-1",
            workload_id="skill_extraction",
            messages=[{"role": "user", "content": "hello"}],
        )

    assert exc_info.value.recommendation_status == status
    assert runtime_called is False


def test_recommended_execution_forwards_exact_frozen_identity(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        lambda payload, workload_id: _recommendation(
            provider="groq",
            model="openai/gpt-oss-120b",
        ),
    )

    observed = {}

    def fake_runtime(**kwargs):
        observed.update(kwargs)
        return {
            "content": "ok",
            "provider": kwargs["provider"],
            "model": kwargs["model"],
        }

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        fake_runtime,
    )

    result = routing.run_recommended_user_chat_completion_with_metadata(
        owner_user_id="owner-1",
        workload_id="ambiguous_resume_adjudication",
        messages=[{"role": "user", "content": "review"}],
        temperature=0.2,
        max_tokens=321,
        response_mime_type="application/json",
        response_schema={"type": "object"},
        return_parsed=True,
        thinking_budget=123,
        database_url="postgresql://sentinel",
        database_url_env="SENTINEL_DATABASE_URL",
        psql_bin="/sentinel/psql",
        ensure_schema=False,
    )

    assert observed == {
        "owner_user_id": "owner-1",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "user",
                "content": "review",
            }
        ],
        "temperature": 0.2,
        "max_tokens": 321,
        "response_mime_type": "application/json",
        "response_schema": {"type": "object"},
        "return_parsed": True,
        "thinking_budget": 123,
        "database_url": "postgresql://sentinel",
        "database_url_env": "SENTINEL_DATABASE_URL",
        "psql_bin": "/sentinel/psql",
        "ensure_schema": False,
    }

    assert result == {
        "content": "ok",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }


def test_invalid_recommended_identity_fails_before_runtime(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        lambda payload, workload_id: _recommendation(
            status="recommended",
            provider="",
            model="",
        ),
    )

    runtime_called = False

    def forbidden_runtime(**kwargs):
        nonlocal runtime_called
        runtime_called = True
        raise AssertionError("runtime must not be called")

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        forbidden_runtime,
    )

    with pytest.raises(
        routing.RecommendedProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_recommended_user_chat_completion_with_metadata(
            owner_user_id="owner-1",
            workload_id="skill_extraction",
            messages=[],
        )

    assert (
        exc_info.value.recommendation_status
        == "invalid_recommended_identity"
    )
    assert runtime_called is False


def test_policy_error_propagates_before_runtime(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    def fail_policy(payload, workload_id):
        raise ValueError("policy unavailable")

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        fail_policy,
    )

    runtime_called = False

    def forbidden_runtime(**kwargs):
        nonlocal runtime_called
        runtime_called = True
        raise AssertionError("runtime must not be called")

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        forbidden_runtime,
    )

    with pytest.raises(
        ValueError,
        match="policy unavailable",
    ):
        routing.run_recommended_user_chat_completion_with_metadata(
            owner_user_id="owner-1",
            workload_id="unknown",
            messages=[],
        )

    assert runtime_called is False


def test_public_execution_bridge_exposes_no_provider_model_or_fallback_override():
    parameters = inspect.signature(
        routing.run_recommended_user_chat_completion_with_metadata
    ).parameters

    assert "provider" not in parameters
    assert "model" not in parameters
    assert "fallback_enabled" not in parameters
    assert "preferred_provider" not in parameters


def test_bridge_does_not_own_model_ranking_or_preferred_provider_logic():
    source = OWNER.read_text(encoding="utf-8")

    assert "resolve_user_preferred_provider" not in source
    assert "preferred_provider" not in source
    assert "fallback_enabled" not in source
    assert "COST_SELECTION_WEIGHT" not in source


def test_bridge_import_boundary_has_no_provider_sdk_or_direct_transport():
    source = OWNER.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)

    assert not any(
        module == prohibited
        or module.startswith(prohibited + ".")
        for module in imported_modules
        for prohibited in (
            "groq",
            "openai",
            "google",
            "requests",
            "httpx",
            "src.ai.llm_client",
        )
    )


def test_only_approved_api_consumes_bridge():
    references = []

    for path in (ROOT / "src").rglob("*.py"):
        if path.resolve() == OWNER.resolve():
            continue

        if (
            "provider_model_routing_service"
            in path.read_text(encoding="utf-8")
        ):
            references.append(
                path.relative_to(ROOT).as_posix()
            )

    assert sorted(references) == [
        "src/app/api.py"
    ]

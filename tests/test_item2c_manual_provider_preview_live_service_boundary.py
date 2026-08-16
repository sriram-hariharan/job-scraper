from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.ai.user_provider_runtime import UserProviderRuntimeConfigurationError
from src.app import api, provider_model_routing_service, services
from src.evaluation.production_task_contract_fingerprints import (
    production_task_contract_sha256,
)


EXPECTED_ITEM2B_FINGERPRINT = (
    "817998a72669796e26c2e99a6ac28af4613cb99a671125dbac71e4d550498222"
)


def _request(owner_user_id: str = "owner-a") -> SimpleNamespace:
    return SimpleNamespace(
        state=SimpleNamespace(auth_user={"user_id": owner_user_id})
    )


def _body(**overrides):
    values = {
        "pipeline_run_id": "run-a",
        "job_id": "job-a",
        "manual_triggered": True,
        "operator_confirmed": True,
    }
    values.update(overrides)
    return api.ManualProviderPreviewLiveRequest(**values)


def _artifacts(job_id: str = "job-a") -> list[dict]:
    return [
        {
            "artifact_kind": "job_packet_json",
            "artifact_name": "job_packets/job-a.json",
            "content_json": {
                "job_snapshot": {
                    "job_id": job_id,
                    "company": "Example Co",
                    "title": "Data Engineer",
                    "location": "Remote",
                    "source": "greenhouse",
                    "description": "Build reliable Python and SQL pipelines.",
                    "required_skills": ["python", "sql"],
                    "preferred_skills": ["airflow"],
                },
                "selection": {"selected_resume": "resume-a.pdf"},
                "summary": {
                    "missing_required": ["airflow"],
                    "matched_terms": ["python", "sql"],
                },
                "top_relevant_evidence_units": [
                    {
                        "bullet_id": "evidence-1",
                        "clause_text": "Built Python and SQL data pipelines.",
                    }
                ],
            },
        },
        {
            "artifact_kind": "tailoring_decision_recommendations",
            "artifact_name": "tailoring_decision_recommendations.csv",
            "content_text": (
                "job_id,tailoring_decision,tailoring_reason_codes\n"
                f"{job_id},tailor_before_apply,missing_requirement\n"
            ),
        },
    ]


def _eligible(monkeypatch) -> None:
    monkeypatch.setenv(
        services.MANUAL_PROVIDER_PREVIEW_LIVE_ENABLED_ENV,
        "true",
    )
    monkeypatch.setattr(
        services,
        "_user_pipeline_run_and_artifacts",
        lambda owner, run_id: (
            {"owner_user_id": owner, "run_id": run_id},
            _artifacts(),
        ),
    )


def _runtime_success() -> dict:
    return {
        "content": {
            "preview_status": "advisory",
            "manual_only": True,
            "suggestions": [],
        },
        "provider": "synthetic",
        "model": "qualified-model",
        "fallback_used": False,
    }


def test_api_requires_auth_and_browser_cannot_supply_or_override_owner(monkeypatch):
    monkeypatch.setattr(
        api.services,
        "manual_provider_preview_live_candidate_payload",
        lambda **_kwargs: pytest.fail("service must not run without auth"),
    )
    with pytest.raises(api.HTTPException) as exc_info:
        api.manual_generate_ai_tailoring_preview_live_api(_body(), _request(""))
    assert exc_info.value.status_code == 401

    with pytest.raises(ValidationError):
        api.ManualProviderPreviewLiveRequest(
            **_body().model_dump(),
            owner_user_id="attacker",
        )

    calls = []
    monkeypatch.setattr(
        api.services,
        "manual_provider_preview_live_candidate_payload",
        lambda **kwargs: calls.append(kwargs) or {"ok": True},
    )
    assert api.manual_generate_ai_tailoring_preview_live_api(
        _body(), _request("canonical-owner")
    ) == {"ok": True}
    assert calls == [
        {
            "owner_user_id": "canonical-owner",
            "pipeline_run_id": "run-a",
            "job_id": "job-a",
            "manual_triggered": True,
            "operator_confirmed": True,
        }
    ]


@pytest.mark.parametrize(
    ("overrides", "expected_category"),
    (
        ({"manual_triggered": False}, "manual_trigger_required"),
        ({"operator_confirmed": False}, "operator_confirmation_required"),
    ),
)
def test_manual_consent_gates_fail_before_context_or_runtime(
    monkeypatch,
    overrides,
    expected_category,
):
    monkeypatch.setenv(
        services.MANUAL_PROVIDER_PREVIEW_LIVE_ENABLED_ENV,
        "true",
    )
    monkeypatch.setattr(
        services,
        "_user_pipeline_run_and_artifacts",
        lambda *_args: pytest.fail("context must not load"),
    )
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("runtime must not run"),
    )
    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services.manual_provider_preview_live_candidate_payload(
            owner_user_id="owner-a",
            pipeline_run_id="run-a",
            job_id="job-a",
            manual_triggered=overrides.get("manual_triggered", True),
            operator_confirmed=overrides.get("operator_confirmed", True),
        )
    assert exc_info.value.category == expected_category


def test_activation_disabled_fails_before_context_route_or_provider(monkeypatch):
    monkeypatch.delenv(
        services.MANUAL_PROVIDER_PREVIEW_LIVE_ENABLED_ENV,
        raising=False,
    )
    monkeypatch.setattr(
        services,
        "_user_pipeline_run_and_artifacts",
        lambda *_args: pytest.fail("context must not load"),
    )
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("route/runtime must not run"),
    )
    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services.manual_provider_preview_live_candidate_payload(
            owner_user_id="owner-a",
            pipeline_run_id="run-a",
            job_id="job-a",
            manual_triggered=True,
            operator_confirmed=True,
        )
    assert exc_info.value.category == "activation_disabled"


@pytest.mark.parametrize(
    ("loader", "expected_category"),
    (
        (
            lambda _owner, _run: (_ for _ in ()).throw(
                ValueError("not owned")
            ),
            "authorized_context_not_found",
        ),
        (
            lambda owner, run: (
                {"owner_user_id": owner, "run_id": run},
                _artifacts("another-job"),
            ),
            "authorized_context_unavailable",
        ),
    ),
)
def test_run_and_job_must_belong_to_authenticated_owner(
    monkeypatch,
    loader,
    expected_category,
):
    monkeypatch.setenv(
        services.MANUAL_PROVIDER_PREVIEW_LIVE_ENABLED_ENV,
        "true",
    )
    monkeypatch.setattr(services, "_user_pipeline_run_and_artifacts", loader)
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("runtime must not run"),
    )
    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services.manual_provider_preview_live_candidate_payload(
            owner_user_id="owner-a",
            pipeline_run_id="run-a",
            job_id="job-a",
            manual_triggered=True,
            operator_confirmed=True,
        )
    assert exc_info.value.category == expected_category


@pytest.mark.parametrize("routing_status", ("blocked_non_live", "routing_status_unavailable"))
def test_unqualified_or_stale_route_fails_closed_with_one_boundary_call(
    monkeypatch,
    routing_status,
):
    _eligible(monkeypatch)
    boundary_calls = []
    runtime_calls = []
    def routing_status_read(workload_id, *, owner_user_id=None):
        if routing_status == "routing_status_unavailable":
            raise ValueError("stale qualification")
        return {
            "workload_id": workload_id,
            "execution_mode": routing_status,
            "effective_selection": None,
            "effective_selection_source": routing_status,
            "qualified_options": [],
        }

    monkeypatch.setattr(
        provider_model_routing_service,
        "read_provider_model_routing_status",
        routing_status_read,
    )
    monkeypatch.setattr(
        provider_model_routing_service,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: runtime_calls.append(kwargs)
        or pytest.fail("credential/provider runtime must not run"),
    )

    def unavailable(*args, **kwargs):
        boundary_calls.append((args, kwargs))
        return provider_model_routing_service.run_effective_user_chat_completion_with_metadata(
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        unavailable,
    )
    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services.manual_provider_preview_live_candidate_payload(
            owner_user_id="owner-a",
            pipeline_run_id="run-a",
            job_id="job-a",
            manual_triggered=True,
            operator_confirmed=True,
        )
    assert exc_info.value.category == "route_unavailable"
    assert exc_info.value.state == routing_status
    assert len(boundary_calls) == 1
    assert runtime_calls == []


def test_missing_owner_credential_is_bounded_without_retry(monkeypatch):
    _eligible(monkeypatch)
    calls = []

    def missing(*args, **kwargs):
        calls.append((args, kwargs))
        raise UserProviderRuntimeConfigurationError(
            "credential_not_configured",
            "synthetic",
        )

    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        missing,
    )
    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services.manual_provider_preview_live_candidate_payload(
            owner_user_id="owner-a",
            pipeline_run_id="run-a",
            job_id="job-a",
            manual_triggered=True,
            operator_confirmed=True,
        )
    assert exc_info.value.category == "credential_not_configured"
    assert len(calls) == 1


def test_eligible_request_uses_canonical_contract_and_runtime_exactly_once(monkeypatch):
    _eligible(monkeypatch)
    calls = []

    def runtime(*args, **kwargs):
        calls.append((args, kwargs))
        return _runtime_success()

    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        runtime,
    )
    result = services.manual_provider_preview_live_candidate_payload(
        owner_user_id=" owner-a ",
        pipeline_run_id="run-a",
        job_id="job-a",
        manual_triggered=True,
        operator_confirmed=True,
    )

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[:2] == ("owner-a", "manual_provider_preview")
    assert kwargs["temperature"] == 0
    assert kwargs["max_tokens"] == 700
    assert kwargs["return_parsed"] is True
    assert kwargs["thinking_budget"] == 0
    serialized_messages = str(args[2])
    assert "Example Co" in serialized_messages
    assert "evidence-1" in serialized_messages
    assert "tailor_before_apply" in serialized_messages
    assert result["provider_metadata"] == {
        "provider": "synthetic",
        "model": "qualified-model",
        "fallback_used": False,
    }
    assert result["provider_response_candidate"] == _runtime_success()["content"]
    assert result["normalized_preview"] is False
    assert result["persisted"] is False
    assert result["resume_mutation_authorized"] is False
    assert result["application_mutation_authorized"] is False


@pytest.mark.parametrize(
    ("runtime_result", "expected_category"),
    (
        (RuntimeError("private provider failure"), "provider_failure"),
        ({"content": "not parsed", "provider": "x", "model": "y", "fallback_used": False}, "malformed_provider_response"),
        ({"content": {"reasoning": "hidden"}, "provider": "x", "model": "y", "fallback_used": False}, "unsafe_provider_response"),
        ({"content": {"text": "x" * 33_000}, "provider": "x", "model": "y", "fallback_used": False}, "provider_response_too_large"),
        ({"content": {"preview_status": "advisory"}, "provider": "x", "model": "y", "fallback_used": True}, "unsafe_provider_metadata"),
    ),
)
def test_provider_failure_or_malformed_unsafe_unbounded_response_never_retries(
    monkeypatch,
    runtime_result,
    expected_category,
):
    _eligible(monkeypatch)
    calls = []

    def runtime(*args, **kwargs):
        calls.append((args, kwargs))
        if isinstance(runtime_result, Exception):
            raise runtime_result
        return runtime_result

    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        runtime,
    )
    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services.manual_provider_preview_live_candidate_payload(
            owner_user_id="owner-a",
            pipeline_run_id="run-a",
            job_id="job-a",
            manual_triggered=True,
            operator_confirmed=True,
        )
    assert exc_info.value.category == expected_category
    assert len(calls) == 1
    assert "private provider failure" not in str(exc_info.value)


def test_api_maps_service_failures_to_bounded_browser_safe_detail(monkeypatch):
    monkeypatch.setattr(
        api.services,
        "manual_provider_preview_live_candidate_payload",
        lambda **_kwargs: (_ for _ in ()).throw(
            services.ManualProviderPreviewLiveError(
                "route_unavailable",
                "blocked_non_live",
            )
        ),
    )
    with pytest.raises(api.HTTPException) as exc_info:
        api.manual_generate_ai_tailoring_preview_live_api(
            _body(),
            _request("owner-a"),
        )
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "ok": False,
        "error_category": "route_unavailable",
        "state": "blocked_non_live",
    }


def test_historical_manual_preview_get_contracts_remain_default_off():
    phase24 = api.manual_generate_ai_tailoring_preview_contract_api()
    phase32 = (
        api.manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract_api()
    )
    assert phase24["can_prepare_preview"] is False
    assert phase24["provider_call_performed"] is False
    assert phase32["provider_call_performed"] is False
    assert phase32["network_call_performed"] is False


def test_item2b_fingerprint_and_static_separation_are_preserved():
    assert (
        production_task_contract_sha256("manual_provider_preview")
        == EXPECTED_ITEM2B_FINGERPRINT
    )

    api_source = inspect.getsource(api.manual_generate_ai_tailoring_preview_live_api)
    service_source = inspect.getsource(
        services.manual_provider_preview_live_candidate_payload
    )
    assert "run_effective_user_chat_completion_with_metadata" in service_source
    for forbidden in (
        "OpenAI(",
        "Groq(",
        "requests.",
        "httpx.",
        "aiohttp.",
        "insert_",
        "upsert_",
        "update_",
        "delete_",
        "score_resume_job_match",
        "run_prefilter",
        "application_action",
    ):
        assert forbidden not in api_source
        assert forbidden not in service_source

    changed_production_sources = (
        Path("src/app/api.py").read_text(encoding="utf-8"),
        Path("src/app/services.py").read_text(encoding="utf-8"),
    )
    newly_owned_source = "\n".join(changed_production_sources)
    assert "from openai import" not in newly_owned_source
    assert "from groq import" not in newly_owned_source

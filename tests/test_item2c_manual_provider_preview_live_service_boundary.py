from __future__ import annotations

from copy import deepcopy
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
    "6d8867803fcd95e137ab774e3a3be153abb39e8d354798b1918a96db59de9b8b"
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


def _schema_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _schema_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _schema_keys(nested)


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


def test_provider_schema_adaptation_is_recursive_nonmutating_and_fail_closed():
    contract = services.build_manual_provider_preview_production_task_contract_material()
    canonical_schema = contract["output_contract"]["schema"]
    canonical_before = deepcopy(canonical_schema)

    adapted = services._manual_provider_preview_provider_compatible_schema(
        canonical_schema
    )

    assert canonical_schema == canonical_before
    assert adapted is not canonical_schema
    assert production_task_contract_sha256("manual_provider_preview") == (
        EXPECTED_ITEM2B_FINGERPRINT
    )
    canonical_keys = list(_schema_keys(canonical_schema))
    adapted_keys = list(_schema_keys(adapted))
    assert canonical_keys.count("const") == 6
    assert canonical_keys.count("minItems") == 2
    assert canonical_keys.count("maxItems") == 4
    assert canonical_keys.count("minLength") == 4
    assert canonical_keys.count("maxLength") == 6
    for removed_keyword in (
        "const",
        "minItems",
        "maxItems",
        "minLength",
        "maxLength",
    ):
        assert removed_keyword not in adapted_keys

    canonical_properties = canonical_schema["properties"]
    adapted_properties = adapted["properties"]
    assert adapted["type"] == canonical_schema["type"]
    assert adapted["required"] == canonical_schema["required"]
    assert adapted["additionalProperties"] is False
    assert set(adapted_properties) == set(canonical_properties)
    assert adapted_properties["preview_status"]["enum"] == ["advisory"]
    assert adapted_properties["manual_only"]["enum"] == [True]
    for field_name in (
        "resume_mutation_authorized",
        "automatic_acceptance_authorized",
        "application_mutation_authorized",
        "auto_apply_authorized",
        "auto_submit_authorized",
    ):
        assert adapted_properties[field_name]["enum"] == [False]

    canonical_suggestions = canonical_properties["suggestions"]
    adapted_suggestions = adapted_properties["suggestions"]
    assert adapted_suggestions["type"] == canonical_suggestions["type"]
    assert "items" in adapted_suggestions
    assert adapted_suggestions["items"]["required"] == (
        canonical_suggestions["items"]["required"]
    )
    assert adapted_suggestions["items"]["additionalProperties"] is False
    assert set(adapted_suggestions["items"]["properties"]) == set(
        canonical_suggestions["items"]["properties"]
    )

    nested_source = {
        "anyOf": [
            {"type": "string", "minLength": 1, "enum": ["kept"]},
            {"type": "boolean", "const": False},
        ]
    }
    nested_before = deepcopy(nested_source)
    assert services._manual_provider_preview_provider_compatible_schema(
        nested_source
    ) == {
        "anyOf": [
            {"type": "string", "enum": ["kept"]},
            {"type": "boolean", "enum": [False]},
        ]
    }
    assert nested_source == nested_before

    conflicting = {"type": "boolean", "const": True, "enum": [False]}
    conflicting_before = deepcopy(conflicting)
    with pytest.raises(ValueError, match="const conflicts with enum"):
        services._manual_provider_preview_provider_compatible_schema(conflicting)
    assert conflicting == conflicting_before


def _forbid_context_lookup_side_effects(monkeypatch) -> tuple[list, list]:
    provider_calls = []
    persistence_calls = []
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *args, **kwargs: provider_calls.append((args, kwargs))
        or pytest.fail("context lookup must not call a provider"),
    )
    monkeypatch.setattr(
        services,
        "upsert_user_pipeline_artifact_postgres_payload",
        lambda *args, **kwargs: persistence_calls.append((args, kwargs))
        or pytest.fail("context lookup must not persist or mutate artifacts"),
    )
    return provider_calls, persistence_calls


def test_packet_lookup_resolves_requested_url_from_authoritative_snapshot_aliases(
    monkeypatch,
):
    requested_url = "https://job-boards.greenhouse.io/reddit/jobs/8072076"
    artifacts = _artifacts(requested_url)
    job_snapshot = artifacts[0]["content_json"]["job_snapshot"]
    job_snapshot.update(
        {
            "job_id": "gh_8072076",
            "job_doc_id": requested_url,
            "doc_id": requested_url,
            "url": requested_url,
            "job_url": requested_url,
        }
    )
    before = deepcopy(artifacts)
    provider_calls, persistence_calls = _forbid_context_lookup_side_effects(
        monkeypatch
    )

    contexts = services._manual_provider_preview_contexts(
        artifacts=artifacts,
        pipeline_run_id="20260817T101016247794Z",
        job_id=requested_url,
    )

    assert contexts["authorized_job_context"]["job_id"] == requested_url
    assert contexts["authorized_job_context"]["company"] == "Example Co"
    assert contexts["selected_tailoring_request"]["job_id"] == requested_url
    assert artifacts == before
    assert provider_calls == []
    assert persistence_calls == []


def test_packet_lookup_preserves_exact_existing_job_id_match(monkeypatch):
    artifacts = _artifacts("gh_8072076")
    before = deepcopy(artifacts)
    provider_calls, persistence_calls = _forbid_context_lookup_side_effects(
        monkeypatch
    )

    packet = services._manual_provider_preview_job_packet(
        artifacts,
        "gh_8072076",
    )

    assert packet["job_snapshot"]["job_id"] == "gh_8072076"
    assert artifacts == before
    assert provider_calls == []
    assert persistence_calls == []


def test_packet_lookup_unrelated_identifier_still_fails_closed(monkeypatch):
    artifacts = _artifacts("gh_8072076")
    before = deepcopy(artifacts)
    provider_calls, persistence_calls = _forbid_context_lookup_side_effects(
        monkeypatch
    )

    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services._manual_provider_preview_job_packet(
            artifacts,
            "https://example.test/jobs/unrelated",
        )

    assert exc_info.value.category == "authorized_context_unavailable"
    assert exc_info.value.state == "job_packet_not_found"
    assert artifacts == before
    assert provider_calls == []
    assert persistence_calls == []


def test_packet_lookup_ambiguous_authoritative_alias_still_fails_closed(
    monkeypatch,
):
    requested_url = "https://job-boards.greenhouse.io/reddit/jobs/8072076"
    first = _artifacts("gh_8072076")[0]
    second = deepcopy(first)
    first["content_json"]["job_snapshot"]["url"] = requested_url
    second["content_json"]["job_snapshot"].update(
        {"job_id": "gh_duplicate_8072076", "doc_id": requested_url}
    )
    artifacts = [first, second]
    before = deepcopy(artifacts)
    provider_calls, persistence_calls = _forbid_context_lookup_side_effects(
        monkeypatch
    )

    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services._manual_provider_preview_job_packet(artifacts, requested_url)

    assert exc_info.value.category == "authorized_context_unavailable"
    assert exc_info.value.state == "ambiguous_job_packet"
    assert artifacts == before
    assert provider_calls == []
    assert persistence_calls == []


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


def _valid_content() -> dict:
    return {
        "preview_status": "advisory",
        "manual_only": True,
        "suggestions": [
            {
                "suggestion_id": "suggestion-1",
                "source_evidence_ids": ["evidence-1"],
                "preview_text": "Built Python and SQL data pipelines.",
                "claims": ["Built Python and SQL data pipelines."],
                "rationale": "Uses the authorized pipeline evidence.",
                "risk_flags": [],
            }
        ],
        "resume_mutation_authorized": False,
        "automatic_acceptance_authorized": False,
        "application_mutation_authorized": False,
        "auto_apply_authorized": False,
        "auto_submit_authorized": False,
    }


def _runtime_success() -> dict:
    return {
        "content": _valid_content(),
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


def test_eligible_request_uses_json_object_mode_and_runtime_exactly_once(
    monkeypatch,
):
    _eligible(monkeypatch)
    calls = []
    canonical_contract = (
        services.build_manual_provider_preview_production_task_contract_material()
    )
    canonical_schema = canonical_contract["output_contract"]["schema"]
    canonical_before = deepcopy(canonical_schema)

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
    assert kwargs["max_tokens"] == 1024
    assert kwargs["response_mime_type"] == "application/json"
    assert kwargs["return_parsed"] is True
    assert kwargs["thinking_budget"] == 0
    assert kwargs["response_schema"] is None
    assert kwargs["response_mime_type"] == "application/json"
    assert canonical_schema == canonical_before
    canonical_keys = list(_schema_keys(canonical_schema))
    assert canonical_keys.count("const") == 6
    assert canonical_keys.count("minItems") == 2
    assert canonical_keys.count("maxItems") == 4
    assert canonical_keys.count("minLength") == 4
    assert canonical_keys.count("maxLength") == 6
    assert canonical_schema["properties"]["manual_only"]["const"] is True
    assert canonical_schema["properties"]["auto_submit_authorized"]["const"] is (
        False
    )
    assert canonical_schema["properties"]["preview_status"]["enum"] == ["advisory"]
    assert canonical_schema["properties"]["suggestions"]["minItems"] == 1
    assert canonical_schema["properties"]["suggestions"]["maxItems"] == 3
    assert production_task_contract_sha256("manual_provider_preview") == (
        EXPECTED_ITEM2B_FINGERPRINT
    )
    serialized_messages = str(args[2])
    assert "Example Co" in serialized_messages
    assert "evidence-1" in serialized_messages
    assert "tailor_before_apply" in serialized_messages
    assert result["provider_metadata"] == {
        "provider": "synthetic",
        "model": "qualified-model",
        "fallback_used": False,
    }
    assert result["suggestions"] == _valid_content()["suggestions"]
    assert "provider_response_candidate" not in result
    assert result["normalized_preview"] is True
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
        ({**_runtime_success(), "fallback_used": True}, "unsafe_provider_metadata"),
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


@pytest.mark.parametrize(
    "provider_category",
    (
        "authentication",
        "authorization",
        "configuration",
        "connection",
        "invalid_request",
        "provider_5xx",
        "provider_model_mismatch",
        "rate_limit",
        "refusal_or_empty_content",
        "safety",
        "schema_or_parse",
        "timeout",
        "unknown",
        "unsupported_provider",
    ),
)
def test_bounded_primary_provider_diagnostic_survives_service_and_api_boundaries(
    monkeypatch,
    caplog,
    provider_category,
):
    _eligible(monkeypatch)
    provider_error = RuntimeError(
        "LLM provider invocation failed "
        f"(stage=primary, category={provider_category}, provider=groq, "
        "model=openai/gpt-oss-120b)"
    )
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(provider_error),
    )

    with caplog.at_level("ERROR", logger=services.__name__):
        with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
            services.manual_provider_preview_live_candidate_payload(
                owner_user_id="owner-a",
                pipeline_run_id="run-a",
                job_id="job-a",
                manual_triggered=True,
                operator_confirmed=True,
            )

    expected_state = (
        "stage=primary;"
        f"category={provider_category};"
        "provider=groq;"
        "model=openai/gpt-oss-120b"
    )
    assert exc_info.value.category == "provider_failure"
    assert exc_info.value.state == expected_state
    assert expected_state in caplog.text

    monkeypatch.setattr(
        api.services,
        "manual_provider_preview_live_candidate_payload",
        lambda **_kwargs: (_ for _ in ()).throw(exc_info.value),
    )
    with pytest.raises(api.HTTPException) as http_exc_info:
        api.manual_generate_ai_tailoring_preview_live_api(
            _body(),
            _request("owner-a"),
        )
    assert http_exc_info.value.status_code == 502
    assert http_exc_info.value.detail == {
        "ok": False,
        "error_category": "provider_failure",
        "state": expected_state,
    }


def test_bounded_invalid_request_reason_survives_with_http_502_and_no_retry(
    monkeypatch,
    caplog,
):
    _eligible(monkeypatch)
    calls = []
    bounded_error = RuntimeError(
        "LLM provider invocation failed "
        "(stage=primary, category=invalid_request, provider=groq, "
        "model=openai/gpt-oss-120b, "
        "invalid_request_reason=unsupported_schema_keyword, "
        "error_type=invalid_request_error, error_code=json_validate_failed, "
        "error_param=response_format, schema_keyword=anyOf)"
    )

    def runtime(*args, **kwargs):
        calls.append((args, kwargs))
        raise bounded_error

    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        runtime,
    )
    with caplog.at_level("ERROR", logger=services.__name__):
        with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
            services.manual_provider_preview_live_candidate_payload(
                owner_user_id="owner-a",
                pipeline_run_id="run-a",
                job_id="job-a",
                manual_triggered=True,
                operator_confirmed=True,
            )

    expected_state = (
        "stage=primary;category=invalid_request;provider=groq;"
        "model=openai/gpt-oss-120b;"
        "invalid_request_reason=unsupported_schema_keyword;"
        "error_type=invalid_request_error;error_code=json_validate_failed;"
        "error_param=response_format;schema_keyword=anyOf"
    )
    assert len(calls) == 1
    assert exc_info.value.category == "provider_failure"
    assert exc_info.value.state == expected_state
    assert expected_state in caplog.text

    monkeypatch.setattr(
        api.services,
        "manual_provider_preview_live_candidate_payload",
        lambda **_kwargs: (_ for _ in ()).throw(exc_info.value),
    )
    with pytest.raises(api.HTTPException) as http_exc_info:
        api.manual_generate_ai_tailoring_preview_live_api(
            _body(),
            _request("owner-a"),
        )
    assert http_exc_info.value.status_code == 502
    assert http_exc_info.value.detail == {
        "ok": False,
        "error_category": "provider_failure",
        "state": expected_state,
    }


def test_bounded_fallback_provider_diagnostic_preserves_both_stages(monkeypatch):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError(
                "LLM provider invocation failed "
                "(stage=fallback, primary_category=timeout, "
                "primary_provider=groq, primary_model=openai/gpt-oss-120b, "
                "fallback_category=provider_5xx, fallback_provider=openai, "
                "fallback_model=gpt-5-mini)"
            )
        ),
    )

    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        services.manual_provider_preview_live_candidate_payload(
            owner_user_id="owner-a",
            pipeline_run_id="run-a",
            job_id="job-a",
            manual_triggered=True,
            operator_confirmed=True,
        )

    assert exc_info.value.category == "provider_failure"
    assert exc_info.value.state == (
        "stage=fallback;primary_category=timeout;primary_provider=groq;"
        "primary_model=openai/gpt-oss-120b;fallback_category=provider_5xx;"
        "fallback_provider=openai;fallback_model=gpt-5-mini"
    )


def test_unrecognized_provider_exception_text_is_not_logged_or_exposed(
    monkeypatch,
    caplog,
):
    _eligible(monkeypatch)
    raw_secret = "sk-test-private-provider-detail"
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError(f"third-party provider rejected {raw_secret}")
        ),
    )

    with caplog.at_level("ERROR", logger=services.__name__):
        with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
            services.manual_provider_preview_live_candidate_payload(
                owner_user_id="owner-a",
                pipeline_run_id="run-a",
                job_id="job-a",
                manual_triggered=True,
                operator_confirmed=True,
            )

    assert exc_info.value.category == "provider_failure"
    assert exc_info.value.state == ""
    assert raw_secret not in str(exc_info.value)
    assert raw_secret not in caplog.text
    assert "stage=unknown;category=unknown" in caplog.text

    monkeypatch.setattr(
        api.services,
        "manual_provider_preview_live_candidate_payload",
        lambda **_kwargs: (_ for _ in ()).throw(exc_info.value),
    )
    with pytest.raises(api.HTTPException) as http_exc_info:
        api.manual_generate_ai_tailoring_preview_live_api(
            _body(),
            _request("owner-a"),
        )
    assert http_exc_info.value.status_code == 502
    assert http_exc_info.value.detail == {
        "ok": False,
        "error_category": "provider_failure",
    }
    assert raw_secret not in str(http_exc_info.value.detail)


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


@pytest.mark.parametrize(
    ("bypass_content", "expected_category"),
    (
        ({"preview_status": "advisory"}, "schema_invalid"),
        (
            {**_valid_content(), "unexpected_field": "x"},
            "unsupported_provider_response_field",
        ),
        ({**_valid_content(), "manual_only": "true"}, "schema_invalid"),
        (
            {**_valid_content(), "auto_apply_authorized": True},
            "mutation_authority_requested",
        ),
        (
            {**_valid_content(), "auto_submit_authorized": True},
            "mutation_authority_requested",
        ),
    ),
)
def test_json_object_mode_output_cannot_bypass_local_validation(
    monkeypatch,
    bypass_content,
    expected_category,
):
    """JSON Object Mode transmits no schema, so local validation is the only gate."""

    _eligible(monkeypatch)
    calls = []
    persistence_calls = []

    def runtime(*args, **kwargs):
        calls.append((args, kwargs))
        return {
            "content": deepcopy(bypass_content),
            "provider": "synthetic",
            "model": "qualified-model",
            "fallback_used": False,
        }

    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        runtime,
    )
    monkeypatch.setattr(
        services,
        "upsert_user_pipeline_artifact_postgres_payload",
        lambda *args, **kwargs: persistence_calls.append((args, kwargs))
        or pytest.fail("rejected preview must never persist or mutate"),
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
    assert calls[0][1]["response_schema"] is None
    assert persistence_calls == []

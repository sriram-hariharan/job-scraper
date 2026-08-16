from __future__ import annotations

from copy import deepcopy
import inspect
from types import SimpleNamespace

import pytest

from src.agents import manual_provider_preview_production_task_contract as contract
from src.app import api, services
from src.evaluation.production_task_contract_fingerprints import (
    production_task_contract_sha256,
)


EXPECTED_ITEM2B_FINGERPRINT = (
    "817998a72669796e26c2e99a6ac28af4613cb99a671125dbac71e4d550498222"
)


def _evidence_context() -> dict:
    return {
        "selected_resume_id": "resume-a.pdf",
        "evidence": [
            {
                "source_evidence_id": "evidence-1",
                "text": "Built Python and SQL data pipelines for analytics.",
            },
            {
                "source_evidence_id": "evidence-2",
                "text": "Improved reporting reliability by 20 percent.",
            },
        ],
    }


def _valid_response() -> dict:
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


def _validate(value):
    return contract.validate_manual_provider_preview_production_response(
        value,
        bounded_resume_evidence_context=_evidence_context(),
    )


def _expect_error(value, category: str) -> None:
    with pytest.raises(contract.ManualProviderPreviewResponseError) as exc_info:
        _validate(value)
    assert exc_info.value.category == category


def test_valid_structured_result_uses_exact_item2b_schema():
    response = _valid_response()
    validated = _validate(response)
    schema = contract.build_manual_provider_preview_production_task_contract_material()[
        "output_contract"
    ]["schema"]

    assert validated == response
    assert validated is not response
    assert set(validated) == set(schema["properties"])
    assert set(validated) == set(schema["required"])
    assert schema is not contract.RESPONSE_SCHEMA


@pytest.mark.parametrize(
    ("mutation", "category"),
    (
        (lambda value: value.update({"unexpected": "field"}), "unsupported_provider_response_field"),
        (lambda value: value.pop("manual_only"), "schema_invalid"),
        (lambda value: value.update(preview_status="final"), "schema_invalid"),
        (lambda value: value.update(manual_only=False), "schema_invalid"),
        (lambda value: value.update(suggestions=[]), "schema_invalid"),
        (lambda value: value.update(suggestions=value["suggestions"] * 4), "provider_response_contract_bound_exceeded"),
        (lambda value: value["suggestions"].__setitem__(0, "bad"), "schema_invalid"),
        (lambda value: value["suggestions"][0].update(extra="bad"), "unsupported_provider_response_field"),
        (lambda value: value["suggestions"][0].pop("claims"), "schema_invalid"),
        (lambda value: value["suggestions"][0].update(suggestion_id=""), "schema_invalid"),
        (lambda value: value["suggestions"][0].update(suggestion_id="x" * 129), "provider_response_contract_bound_exceeded"),
        (lambda value: value["suggestions"][0].update(source_evidence_ids=[]), "schema_invalid"),
        (lambda value: value["suggestions"][0].update(source_evidence_ids=["unknown"]), "ungrounded_evidence_reference"),
        (lambda value: value["suggestions"][0].update(source_evidence_ids=["owner-b-evidence"]), "ungrounded_evidence_reference"),
        (lambda value: value["suggestions"][0].update(preview_text="x" * 1201), "provider_response_contract_bound_exceeded"),
        (lambda value: value["suggestions"][0].update(rationale="x" * 601), "provider_response_contract_bound_exceeded"),
        (lambda value: value["suggestions"][0].update(claims=["Python"] * 13), "provider_response_contract_bound_exceeded"),
        (lambda value: value["suggestions"][0].update(risk_flags=["review"] * 9), "provider_response_contract_bound_exceeded"),
        (lambda value: value["suggestions"][0].update(claims=["Led quantum cryptography research with Python."]), "ungrounded_claim"),
    ),
)
def test_schema_grounding_and_bounds_fail_closed(mutation, category):
    response = _valid_response()
    mutation(response)
    _expect_error(response, category)


@pytest.mark.parametrize(
    "field_name",
    (
        "resume_mutation_authorized",
        "automatic_acceptance_authorized",
        "application_mutation_authorized",
        "auto_apply_authorized",
        "auto_submit_authorized",
    ),
)
def test_any_mutation_authority_is_rejected_not_repaired(field_name):
    response = _valid_response()
    response[field_name] = True
    _expect_error(response, "mutation_authority_requested")


@pytest.mark.parametrize("malformed", (None, "{}", [], 1))
def test_malformed_provider_result_is_rejected(malformed):
    _expect_error(malformed, "malformed_provider_response")


def test_normalization_is_deterministic_bounded_and_grounded():
    response = _valid_response()
    suggestion = response["suggestions"][0]
    suggestion["suggestion_id"] = "  suggestion-1\n"
    suggestion["source_evidence_ids"] = [
        "evidence-1",
        "evidence-1",
        "evidence-2",
    ]
    suggestion["preview_text"] = "Built   Python\n and SQL pipelines."
    suggestion["claims"] = [
        "Built Python pipelines.",
        "Built  Python pipelines.",
    ]
    suggestion["rationale"] = "Uses  authorized\n evidence."
    suggestion["risk_flags"] = ["Manual review", "Manual  review"]

    first = contract.normalize_manual_provider_preview_production_response(
        response,
        bounded_resume_evidence_context=_evidence_context(),
    )
    second = contract.normalize_manual_provider_preview_production_response(
        response,
        bounded_resume_evidence_context=_evidence_context(),
    )

    assert first == second
    assert first["suggestions"] == [
        {
            "suggestion_id": "suggestion-1",
            "source_evidence_ids": ["evidence-1", "evidence-2"],
            "preview_text": "Built Python and SQL pipelines.",
            "claims": ["Built Python pipelines."],
            "rationale": "Uses authorized evidence.",
            "risk_flags": ["Manual review"],
        }
    ]
    assert _validate(first) == first


def test_normalization_does_not_invent_fields_or_repair_safety_violations():
    missing = _valid_response()
    missing["suggestions"][0].pop("rationale")
    with pytest.raises(contract.ManualProviderPreviewResponseError) as missing_error:
        contract.normalize_manual_provider_preview_production_response(
            missing,
            bounded_resume_evidence_context=_evidence_context(),
        )
    assert missing_error.value.category == "schema_invalid"

    unsafe = _valid_response()
    unsafe["auto_submit_authorized"] = True
    with pytest.raises(contract.ManualProviderPreviewResponseError) as unsafe_error:
        contract.normalize_manual_provider_preview_production_response(
            unsafe,
            bounded_resume_evidence_context=_evidence_context(),
        )
    assert unsafe_error.value.category == "mutation_authority_requested"


def _eligible_service(monkeypatch, runtime_result: dict) -> list:
    runtime_calls = []
    monkeypatch.setenv(
        services.MANUAL_PROVIDER_PREVIEW_LIVE_ENABLED_ENV,
        "true",
    )
    monkeypatch.setattr(
        services,
        "_user_pipeline_run_and_artifacts",
        lambda owner, run_id: ({"owner_user_id": owner, "run_id": run_id}, []),
    )
    monkeypatch.setattr(
        services,
        "_manual_provider_preview_contexts",
        lambda **_kwargs: {
            "authorized_job_context": {"job_id": "job-a"},
            "bounded_resume_evidence_context": _evidence_context(),
            "selected_tailoring_request": {
                "job_id": "job-a",
                "tailoring_decision": "tailor_before_apply",
            },
            "manual_trigger_context": {
                "manual_triggered": True,
                "operator_confirmed": True,
            },
        },
    )
    monkeypatch.setattr(
        services,
        "run_effective_user_chat_completion_with_metadata",
        lambda *args, **kwargs: runtime_calls.append((args, kwargs))
        or deepcopy(runtime_result),
    )
    return runtime_calls


def _runtime_result(content: dict) -> dict:
    return {
        "content": content,
        "provider": "synthetic",
        "model": "qualified-model",
        "fallback_used": False,
        "headers": {"authorization": "must-not-return"},
        "reasoning": "must-not-return",
        "sdk_object": object(),
    }


def _call_service() -> dict:
    return services.manual_provider_preview_live_candidate_payload(
        owner_user_id="owner-a",
        pipeline_run_id="run-a",
        job_id="job-a",
        manual_triggered=True,
        operator_confirmed=True,
    )


def test_valid_service_result_is_normalized_safe_and_exactly_one_call(monkeypatch):
    response = _valid_response()
    response["suggestions"][0]["source_evidence_ids"] *= 2
    runtime_calls = _eligible_service(monkeypatch, _runtime_result(response))

    result = _call_service()

    assert len(runtime_calls) == 1
    assert result["status"] == "manual_provider_preview_ready"
    assert result["preview_status"] == "advisory"
    assert result["manual_only"] is True
    assert result["normalized_preview"] is True
    assert result["suggestions"][0]["source_evidence_ids"] == ["evidence-1"]
    assert result["provider_metadata"] == {
        "provider": "synthetic",
        "model": "qualified-model",
        "fallback_used": False,
    }
    serialized = repr(result).lower()
    for forbidden in (
        "authorization",
        "must-not-return",
        "reasoning",
        "sdk_object",
        "system_prompt",
        "request_body",
        "api_key",
        "credential",
    ):
        assert forbidden not in serialized
    for field_name in (
        "resume_mutation_authorized",
        "automatic_acceptance_authorized",
        "application_mutation_authorized",
        "auto_apply_authorized",
        "auto_submit_authorized",
    ):
        assert result[field_name] is False


@pytest.mark.parametrize(
    ("mutation", "category"),
    (
        (lambda value: value.update(unexpected="field"), "unsupported_provider_response_field"),
        (lambda value: value["suggestions"][0].update(source_evidence_ids=["unknown"]), "ungrounded_evidence_reference"),
        (lambda value: value.update(resume_mutation_authorized=True), "mutation_authority_requested"),
    ),
)
def test_validation_failure_causes_no_second_provider_call(
    monkeypatch,
    mutation,
    category,
):
    response = _valid_response()
    mutation(response)
    runtime_calls = _eligible_service(monkeypatch, _runtime_result(response))

    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        _call_service()

    assert exc_info.value.category == category
    assert len(runtime_calls) == 1


def test_normalization_failure_causes_no_second_provider_call(monkeypatch):
    runtime_calls = _eligible_service(
        monkeypatch,
        _runtime_result(_valid_response()),
    )
    monkeypatch.setattr(
        services,
        "normalize_manual_provider_preview_production_response",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            contract.ManualProviderPreviewResponseError(
                "normalization_failure"
            )
        ),
    )

    with pytest.raises(services.ManualProviderPreviewLiveError) as exc_info:
        _call_service()

    assert exc_info.value.category == "normalization_failure"
    assert len(runtime_calls) == 1


@pytest.mark.parametrize(
    ("category", "status_code"),
    (
        ("schema_invalid", 502),
        ("unsupported_provider_response_field", 502),
        ("mutation_authority_requested", 502),
        ("ungrounded_evidence_reference", 502),
        ("ungrounded_claim", 502),
        ("provider_response_contract_bound_exceeded", 502),
        ("normalization_failure", 502),
        ("authorized_evidence_unavailable", 409),
    ),
)
def test_live_api_maps_validation_errors_without_raw_detail(
    monkeypatch,
    category,
    status_code,
):
    monkeypatch.setattr(
        api.services,
        "manual_provider_preview_live_candidate_payload",
        lambda **_kwargs: (_ for _ in ()).throw(
            services.ManualProviderPreviewLiveError(category)
        ),
    )
    request = api.ManualProviderPreviewLiveRequest(
        pipeline_run_id="run-a",
        job_id="job-a",
        manual_triggered=True,
        operator_confirmed=True,
    )
    http_request = SimpleNamespace(
        state=SimpleNamespace(auth_user={"user_id": "owner-a"})
    )

    with pytest.raises(api.HTTPException) as exc_info:
        api.manual_generate_ai_tailoring_preview_live_api(
            request,
            http_request,
        )

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == {
        "ok": False,
        "error_category": category,
    }


def test_item2b_fingerprint_and_static_nonmutation_invariants_remain_exact():
    assert (
        production_task_contract_sha256("manual_provider_preview")
        == EXPECTED_ITEM2B_FINGERPRINT
    )
    service_source = inspect.getsource(
        services.manual_provider_preview_live_candidate_payload
    )
    assert service_source.count(
        "run_effective_user_chat_completion_with_metadata("
    ) == 1
    for forbidden in (
        "insert_",
        "upsert_",
        "update_",
        "delete_",
        "score_resume_job_match",
        "run_prefilter",
        "OpenAI(",
        "Groq(",
    ):
        assert forbidden not in service_source

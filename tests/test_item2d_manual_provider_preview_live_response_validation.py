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
    "6d8867803fcd95e137ab774e3a3be153abb39e8d354798b1918a96db59de9b8b"
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


def test_source_fact_preservation_rule_is_in_the_fingerprinted_prompt_contract():
    """Human review rejected scope-widening; the rule must be contract-bound."""

    material = (
        contract.build_manual_provider_preview_production_task_contract_material()
    )
    prompt_contract = material["prompt_contract"]
    user_template = prompt_contract["user_template"]

    assert "must preserve the exact factual scope" in user_template
    assert user_template.count("must preserve the exact factual scope") == 1
    for prohibited_addition in (
        "factual entity",
        "ownership concept",
        "deliverable",
        "metric",
        "technology",
        "project or initiative characterization",
        "outcome",
    ):
        assert prohibited_addition in user_template
    assert "Rephrasing supported facts is allowed" in user_template
    assert "widening" in user_template

    # the preservation duty is scoped to candidate facts and defines them
    assert "Every candidate fact must preserve the exact factual scope" in (
        user_template
    )
    assert "A candidate fact is any assertion about what the candidate" in (
        user_template
    )
    # and it still binds every free-text field
    assert "In preview_text, claims, and rationale, do not introduce" in (
        user_template
    )

    # the rule is fingerprinted, and the canonical schema is untouched by it
    assert material["output_contract"]["schema"] == contract.RESPONSE_SCHEMA
    assert material["output_contract"]["response_mode"] == "json_object"
    assert material["output_contract"]["strict"] is False
    assert material["task_parameters"]["max_tokens"] == 1024
    assert production_task_contract_sha256("manual_provider_preview") == (
        EXPECTED_ITEM2B_FINGERPRINT
    )


def test_source_fact_preservation_rule_does_not_hardcode_fixture_wording():
    """The rule must be general, not tuned to the synthetic qualification case."""

    user_template = (
        contract.build_manual_provider_preview_production_task_contract_material()
    )["prompt_contract"]["user_template"]

    for fixture_specific in (
        "evidence_alpha",
        "Delivered python",
        "Python projects",
        "synthetic",
    ):
        assert fixture_specific not in user_template


def test_rejected_history_remains_immutable_and_never_binds_the_registry():
    """Rejected artifacts stay immutable and are never the registry binding."""

    import json
    from pathlib import Path

    from src.evaluation import controlled_provider_qualification_registry as registry

    root = Path(__file__).resolve().parents[1]
    stem = (
        "manual-provider-preview-groq-openai-gpt-oss-120b-"
        "schedule_10712423fd687c623e99c3d69405eed1-jsonobject-e015724f"
    )
    evidence_path = root / "outputs/provider_qualification" / f"{stem}.json"
    context_path = (
        root / "outputs/provider_qualification" / f"{stem}.validation-context.json"
    )
    review_path = root / "outputs/provider_benchmark" / f"human-review-{stem}.json"
    if not evidence_path.exists():
        pytest.skip("rejected qualification history is not present locally")

    evidence = json.loads(evidence_path.read_text())
    context = json.loads(context_path.read_text())
    record = json.loads(review_path.read_text())
    authorization = context["live_authorization"]

    # The rejected pair stays bound to the superseded contract. Contract-bound
    # validators intentionally cannot re-validate it now that the fingerprint
    # moved, so immutability is asserted on stored content instead.
    assert record["decision"] == "rejected"
    assert record["reviewer_id"] == "sriram"
    assert record["evidence_sha256"] == (
        "0303f061b985140bf7ea4d1b5ac3381894d6b4389a1403d4d163eb21e081c244"
    )
    assert evidence["grading_summaries"][0][
        "production_task_contract_sha256"
    ] == "e015724f26e30c57c6796ba382979a142bc6ca6a13d20762383b8811ac25c288"
    assert authorization["production_task_contract_fingerprints"][
        "manual_provider_preview"
    ] == "e015724f26e30c57c6796ba382979a142bc6ca6a13d20762383b8811ac25c288"
    assert record["evidence_sha256"] != EXPECTED_ITEM2B_FINGERPRINT

    # the registry was never bound to the rejected attempt
    stored = registry.load_provider_qualification_registry(
        root / registry.REGISTRY_ARTIFACT_PATH, repository_root=root
    )
    cell = next(
        item
        for item in stored["cells"]
        if item["schedule_key"] == "schedule_10712423fd687c623e99c3d69405eed1"
    )
    # neither rejected review may ever become the registry binding
    assert cell["review_sha256"] not in {
        "474438aad03dc50a0e48822431ef1cdac191f03c082e78ab2f1789fcd471aa49",
        "7e7343b79f414771a928e8be7d2aa8de56e457a7752ce096c077ec4d97d7a344",
    }
    # the bound evidence is the approved attempt, not either rejected one
    assert cell["evidence_sha256"] not in {
        "0303f061b985140bf7ea4d1b5ac3381894d6b4389a1403d4d163eb21e081c244",
        "5d6c160cfa6b902d5a9b4ea51a6726a8a95ff26a31f70867867fd38b31bcd509",
    }


def test_routing_binds_the_current_claims_anchor_contract():
    """The claims-anchor contract is qualified, reviewed, and bound."""

    from src.app import provider_model_routing_service as routing

    entry = next(
        item
        for item in routing.list_provider_model_routing_statuses()["workloads"]
        if item["workload_id"] == "manual_provider_preview"
    )

    assert entry["recommendation_status"] == "recommended"
    assert entry["execution_mode"] == "qualified_provider_model"
    assert entry["provider"] == "groq"
    assert entry["model"] == "openai/gpt-oss-120b"
    assert entry["qualified_options"] == [
        {"provider": "groq", "model": "openai/gpt-oss-120b"}
    ]
    assert entry["effective_selection_source"] == "applylens_recommended"


def test_job_linkage_is_permitted_only_for_preview_text_and_rationale():
    """Bare restatement was rejected; relevance language is now sanctioned."""

    user_template = (
        contract.build_manual_provider_preview_production_task_contract_material()
    )["prompt_contract"]["user_template"]

    # preview_text and rationale may relate a preserved fact to the job context
    assert (
        "preview_text and rationale may additionally explain how a preserved "
        "candidate fact matches, supports, addresses, or is relevant to a "
        "requirement stated explicitly in the authorized job context."
    ) in user_template

    # linkage may never become a new candidate fact
    assert "must never introduce or imply a new fact about the candidate" in (
        user_template
    )

    # bare restatement is explicitly discouraged when a relationship exists
    assert "Do not restate the evidence alone" in user_template


def test_claims_are_candidate_fact_only_and_exclude_linkage_language():
    """_claim_is_grounded is evidence-text based, so claims must stay strict."""

    user_template = (
        contract.build_manual_provider_preview_production_task_contract_material()
    )["prompt_contract"]["user_template"]

    assert (
        "claims must contain only candidate facts supported by the cited "
        "evidence and must not contain relevance or job-linkage language."
    ) in user_template


def test_claim_grounding_validator_behaviour_is_unchanged():
    """The deterministic overlap validator must not have been altered."""

    evidence = "Delivered python."

    # a preserved candidate fact stays grounded
    assert contract._claim_is_grounded("Delivered Python", evidence) is True
    # candidate-fact widening is still rejected
    assert contract._claim_is_grounded("Delivered Python projects", evidence) is (
        False
    )
    # linkage wording in claims would still fail the overlap check, which is
    # exactly why the prompt forbids putting linkage language in claims
    assert contract._claim_is_grounded(
        "Delivered Python, matching the role's Python requirement", evidence
    ) is False


# Obviously synthetic résumé-shaped evidence (~25 unique tokens), sized to the
# real production evidence geometry (24-31 unique tokens per authorized row).
# No real résumé or job-description content.
_REALISTIC_SYNTHETIC_EVIDENCE = (
    "Built and maintained batch ingestion services that consolidated vendor "
    "telemetry into a governed warehouse, documented rollout checks for "
    "downstream reporting teams, and reviewed weekly schedule adherence."
)


def test_realistic_evidence_close_lexical_anchor_is_grounded():
    """CASE A: a concise claim reusing the evidence's own factual words."""

    claim = (
        "Built and maintained batch ingestion services consolidating vendor "
        "telemetry"
    )

    assert contract._claim_is_grounded(claim, _REALISTIC_SYNTHETIC_EVIDENCE) is (
        True
    )


def test_realistic_evidence_synonym_paraphrase_is_not_grounded():
    """CASE B: semantically faithful but synonym-heavy paraphrase fails.

    This documents the actual lexical contract the validator enforces, and is
    exactly why the prompt asks for evidence anchors rather than paraphrase.
    """

    claim = "Engineered recurring data-transfer pipelines unifying supplier signals"

    assert contract._claim_is_grounded(claim, _REALISTIC_SYNTHETIC_EVIDENCE) is (
        False
    )


@pytest.mark.parametrize(
    "widened_claim",
    (
        "Built batch ingestion services that reduced latency by forty percent",
        "Owned the flagship migration initiative for enterprise customers",
    ),
)
def test_realistic_evidence_unsupported_widening_is_not_grounded(widened_claim):
    """CASE C: invented metrics/ownership remain rejected."""

    assert contract._claim_is_grounded(
        widened_claim, _REALISTIC_SYNTHETIC_EVIDENCE
    ) is False


def test_realistic_widening_is_also_rejected_by_the_response_validator():
    """CASE C end-to-end: widening fails the authoritative validator."""

    evidence_context = {
        "selected_resume_id": "synthetic-resume.pdf",
        "evidence": [
            {
                "source_evidence_id": "synthetic-evidence-1",
                "text": _REALISTIC_SYNTHETIC_EVIDENCE,
            }
        ],
    }
    response = _valid_response()
    suggestion = response["suggestions"][0]
    suggestion["source_evidence_ids"] = ["synthetic-evidence-1"]
    suggestion["claims"] = [
        "Owned the flagship migration initiative for enterprise customers"
    ]

    with pytest.raises(contract.ManualProviderPreviewResponseError) as exc_info:
        contract.validate_manual_provider_preview_production_response(
            response,
            bounded_resume_evidence_context=evidence_context,
        )
    assert exc_info.value.category == "ungrounded_claim"


def test_claims_prompt_defines_claims_as_lexical_evidence_anchors():
    """Prompt must align with the lexical validator, without leaking it."""

    user_template = (
        contract.build_manual_provider_preview_production_task_contract_material()
    )["prompt_contract"]["user_template"]

    assert "concise evidence anchor" in user_template
    assert "reuses the cited evidence's key factual words" in user_template
    assert "lexically traceable" in user_template
    assert "Prefer the evidence's own factual terms over synonyms" in (
        user_template
    )
    assert "Do not copy an entire evidence entry" in user_template
    # claims stay candidate-fact-only and linkage-free
    assert "must not contain relevance or job-linkage language" in user_template
    # the implementation threshold must never leak into the prompt
    for leaked in ("0.5", "fifty percent", "token overlap", "50%", "threshold"):
        assert leaked not in user_template

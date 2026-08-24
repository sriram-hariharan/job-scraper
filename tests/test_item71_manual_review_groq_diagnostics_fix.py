from __future__ import annotations

import json
import re
from copy import deepcopy
from types import SimpleNamespace

import pytest

from src.agents.controlled_exact_resume_change_set_llm_request_packet_default_off import (
    build_controlled_exact_resume_change_set_llm_request_packet_default_off,
)
from src.agents.exact_resume_change_set_proposal_builder_default_off import (
    build_exact_resume_change_set_proposal_builder_default_off,
)
from src.ai import llm_client
from src.app import services
from src.resume.evidence_builder import build_resume_evidence
from src.resume.models import ResumeDocument
from tests.test_item71b_safe_diagnostics_runtime_foundation import _stateful_storage
from tests.test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off import (
    _valid_exact_provider_payload,
)
from tests.test_score_first_scan import _resume_evidence


GROQ_PREMIUM_MODEL = "openai/gpt-oss-120b"

STRUCTURED_RESUME_TEXT = """\
SUMMARY
Machine learning engineer focused on production analytics.
EXPERIENCE
Senior ML Engineer at ExampleCo
January 2021 - Present
- Built Python feature pipelines and SQL quality checks for production models.
- Deployed forecasting services with Python for analytics teams.
PROJECTS
Forecasting Lab
- Built a Python forecasting project with SQL reporting.
SKILLS
Python, SQL, Machine Learning
"""


def _structured_resume_evidence():
    return build_resume_evidence(
        ResumeDocument(
            resume_id="item71-fix6-resume",
            resume_name="item71-fix6-resume",
            path="",
            raw_text=STRUCTURED_RESUME_TEXT,
            normalized_text=re.sub(r"\s+", " ", STRUCTURED_RESUME_TEXT).strip(),
        )
    )


def _fresh_structured_scan(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return services.create_saved_scan_payload(
        scan_id="item71-fix6-scan",
        company="ExampleCo",
        role="Senior ML Engineer",
        job_description_text=(
            "Build production machine learning systems using Python and SQL."
        ),
        job_url="https://example.test/item71-fix6",
        job_doc_id="job-item71-fix6",
        resume_text=STRUCTURED_RESUME_TEXT,
    )


def _exact_request_packet() -> dict:
    return build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=[
            {
                "proposal_id": "proposal-1",
                "change_type": "bullet",
                "target_section": "experience",
                "resume_evidence_used": ["Built deterministic pipelines."],
            }
        ],
        resume_context={"skills": ["Python", "SQL"]},
        jd_context={"required_skills": ["Python"]},
        tailoring_context={"matched_required_skills": ["Python"]},
    )["request_packet"]


def _strict_tailoring_suggestion(*, patch_ready: bool = True) -> dict:
    return {
        "suggestion_id": "live_tailoring_001",
        "source_bullet_id": "bullet-1" if patch_ready else "",
        "original_text": "Built deterministic pipelines." if patch_ready else "",
        "suggested_text": (
            "Built deterministic Python pipelines."
            if patch_ready
            else "Gather direct evidence before adding the JD signal."
        ),
        "reason": "The supplied evidence supports this bounded guidance.",
        "evidence_spans": ["Built deterministic pipelines."] if patch_ready else [],
        "jd_signal_links": [{"field": "required_skills", "signal": "Python"}],
        "patch_ready": patch_ready,
        "projected_score_delta": 0.03 if patch_ready else 0.0,
        "risk_flags": [] if patch_ready else ["unsupported_claim"],
    }


def _strict_tailoring_provider_content() -> dict:
    return {
        "patch_ready_suggestions": [_strict_tailoring_suggestion()],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.03,
        "rationale": "Provider returned evidence-backed tailoring suggestions.",
    }


def _strict_schema_object_nodes(schema: dict) -> list[tuple[str, dict]]:
    rows = []

    def visit(value, path):
        if not isinstance(value, dict):
            return
        if value.get("type") == "object":
            rows.append((path, value))
        properties = value.get("properties")
        if isinstance(properties, dict):
            for key, child in properties.items():
                visit(child, f"{path}.properties.{key}")
        if isinstance(value.get("items"), dict):
            visit(value["items"], f"{path}.items")

    visit(schema, "$")
    return rows


def _schema_contract_errors(value, schema: dict, path: str = "$") -> list[str]:
    errors = []
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected object"]
        properties = schema.get("properties") or {}
        for key in schema.get("required") or []:
            if key not in value:
                errors.append(f"{path}: missing required property {key}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key}")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(
                    _schema_contract_errors(value[key], child_schema, f"{path}.{key}")
                )
    elif schema_type == "array":
        if not isinstance(value, list):
            return [f"{path}: expected array"]
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(
                    _schema_contract_errors(item, item_schema, f"{path}[{index}]")
                )
    return errors


def test_new_scan_persists_source_backed_structured_resume_targets(monkeypatch):
    evidence = _structured_resume_evidence()
    reparsed_evidence = _structured_resume_evidence()
    payload = _fresh_structured_scan(monkeypatch)
    review = payload["scan_review_payload"]
    targets = review["structured_resume_targets"]

    expected_bullets = [
        {
            "source_entry_id": entry.entry_id,
            "source_bullet_id": entry.bullet_ids[index],
            "text": bullet,
        }
        for entry in evidence.experience_entries
        for index, bullet in enumerate(entry.bullets)
    ]
    assert targets == {
        "version": "structured_resume_targets_v1",
        "source": "resume_evidence",
        "experience_bullets": expected_bullets,
        "skills": evidence.skills,
    }
    assert len(targets["experience_bullets"]) == 2
    assert len(targets["skills"]) == 5
    assert [
        bullet_id
        for entry in evidence.experience_entries
        for bullet_id in entry.bullet_ids
    ] == [
        bullet_id
        for entry in reparsed_evidence.experience_entries
        for bullet_id in entry.bullet_ids
    ]
    assert evidence.project_entries
    assert "projects" not in targets
    assert "profile_summary" not in targets
    assert "resume_sections" not in targets
    assert "profile_summary" not in review
    assert "resume_summary" not in review
    assert review["scan_issue_contract"]["version"] == "scan_issue_contract_v2"
    assert review["scan_score"]["source"] == "new_scan_match_score"
    serialized_review = json.dumps(review, sort_keys=True)
    assert "applylens_profile_resume_previews" not in serialized_review


def test_structured_target_projection_does_not_change_scan_scoring_or_issues(
    monkeypatch,
):
    with_targets = _fresh_structured_scan(monkeypatch)["scan_review_payload"]
    monkeypatch.setattr(
        services,
        "_new_scan_structured_resume_targets",
        lambda _resume_evidence: {
            "version": "structured_resume_targets_v1",
            "source": "resume_evidence",
            "experience_bullets": [],
            "skills": [],
        },
    )
    without_target_records = _fresh_structured_scan(monkeypatch)[
        "scan_review_payload"
    ]

    assert with_targets["scan_score"] == without_target_records["scan_score"]
    assert with_targets["score_preview"] == without_target_records["score_preview"]
    assert with_targets["scan_issue_contract"] == without_target_records[
        "scan_issue_contract"
    ]
    assert with_targets["new_scan"]["match_bucket"] == without_target_records[
        "new_scan"
    ]["match_bucket"]
    assert with_targets["new_scan"]["dimension_scores"] == without_target_records[
        "new_scan"
    ]["dimension_scores"]


def test_structured_resume_targets_survive_saved_scan_payload_round_trip(monkeypatch):
    payload = _fresh_structured_scan(monkeypatch)
    original = payload["scan_review_payload"]["structured_resume_targets"]
    serialized_row = json.loads(json.dumps(payload["scan"], sort_keys=True))

    restored = services._scan_review_payload_from_saved_scan_row(serialized_row)

    assert restored["structured_resume_targets"] == original
    assert restored["structured_resume_targets"] is not original


def test_exact_change_reader_prefers_canonical_targets_and_keeps_history_safe(
    monkeypatch,
):
    payload = _fresh_structured_scan(monkeypatch)
    review = payload["scan_review_payload"]
    targets = review["structured_resume_targets"]

    context = services._planning_workspace_exact_change_resume_context(
        row=payload["scan"],
        review_payload=review,
        draft=review.get("draft"),
    )

    assert context["resume_bullets"] == [
        {"id": target["source_bullet_id"], "text": target["text"]}
        for target in targets["experience_bullets"]
    ]
    assert context["skills"] == targets["skills"]
    assert context["profile_summary"] == ""
    assert all(not row["id"].startswith("evidence-") for row in context["resume_bullets"])

    historical_review = deepcopy(review)
    historical_review.pop("structured_resume_targets")
    historical_review["scan_issue_contract"] = {
        "version": "scan_issue_contract_v2",
        "issues": [{"text": "Historical text without a source identifier."}],
    }
    historical = services._planning_workspace_exact_change_resume_context(
        row=payload["scan"],
        review_payload=historical_review,
        draft=historical_review.get("draft"),
    )
    assert historical["resume_bullets"] == []
    assert historical["skills"] == []
    assert historical["profile_summary"] == (
        "Manual planning workspace resume context."
    )


def test_fresh_persisted_targets_reach_phase42_and_phase43_without_provider(
    monkeypatch,
):
    payload = _fresh_structured_scan(monkeypatch)
    review = payload["scan_review_payload"]
    review["jd_llm_extraction_readback"] = {
        "fallback_used": False,
        "validation_status": "valid",
        "structured_jd_signals": {
            "required_skills": ["Python", "SQL"],
            "preferred_skills": [],
            "tools": [],
        },
    }
    resume_context = services._planning_workspace_exact_change_resume_context(
        row=payload["scan"],
        review_payload=review,
        draft=review.get("draft"),
    )
    jd_context = services._planning_workspace_exact_change_jd_context(review)
    tailoring_context = services._planning_workspace_exact_change_tailoring_context(
        review_payload=review,
        draft=review.get("draft"),
    )
    proposal_result = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=services._planning_workspace_exact_change_review_queue(
            scan_id=payload["scan"]["scan_id"],
            row=payload["scan"],
            review_payload=review,
        ),
        resume_context=resume_context,
        jd_context=jd_context,
        tailoring_context=tailoring_context,
        proposal_policy={"allow_skill_changes": False},
    )
    request_result = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        proposal_result=proposal_result,
        resume_context=resume_context,
        jd_context=jd_context,
        tailoring_context=tailoring_context,
    )

    matched_jd_terms = [
        term
        for term in jd_context["required_skills"]
        if any(
            term.lower() in target["text"].lower()
            for target in resume_context["resume_bullets"]
        )
    ]
    assert jd_context["required_skills"] == ["Python", "SQL"]
    assert len(matched_jd_terms) == 2
    assert len(resume_context["resume_bullets"]) + len(resume_context["skills"]) == 7
    assert proposal_result["change_set_summary"]["change_proposal_count"] == 2
    assert {
        proposal["target_identifier"]
        for proposal in proposal_result["change_proposals"]
    } <= {target["id"] for target in resume_context["resume_bullets"]}
    request_summary = request_result["request_packet_summary"]
    assert request_summary["included_change_proposal_count"] == 2
    assert request_summary["request_blocked"] is False
    assert request_summary["provider_dispatch_ready"] is True
    assert request_summary["provider_call_performed"] is False
    assert request_summary["network_call_performed"] is False


def test_structured_resume_target_projection_is_bounded_source_evidence_only(
    monkeypatch,
):
    targets = _fresh_structured_scan(monkeypatch)["scan_review_payload"][
        "structured_resume_targets"
    ]
    serialized = json.dumps(
        targets,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    assert len(targets["experience_bullets"]) + len(targets["skills"]) == 7
    assert len(serialized) < 2048
    assert STRUCTURED_RESUME_TEXT.encode("utf-8") not in serialized


def test_exact_change_user_message_is_deterministic_json_text():
    first = _exact_request_packet()["request_messages"][1]["content"]
    second = _exact_request_packet()["request_messages"][1]["content"]

    assert isinstance(first, str)
    assert first == second
    payload = json.loads(first)
    assert payload["change_proposals"][0]["proposal_id"] == "proposal-1"
    assert payload["change_proposals"][0]["resume_evidence_used"] == [
        "Built deterministic pipelines."
    ]
    assert payload["resume_context"] == {"skills": ["Python", "SQL"]}
    assert payload["jd_context"] == {"required_skills": ["Python"]}
    assert payload["tailoring_context"] == {
        "matched_required_skills": ["Python"]
    }
    assert payload["safety_constraints"]
    assert payload["evidence_constraints"]
    assert payload["output_constraints"]


def test_exact_change_schema_is_groq_strict_object_compatible():
    schema = _exact_request_packet()["request_schema"]
    object_schemas = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("type") == "object":
                object_schemas.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)

    assert len(object_schemas) == 2
    for object_schema in object_schemas:
        assert object_schema["additionalProperties"] is False
        assert set(object_schema["properties"]) == set(object_schema["required"])
    refined_change_proposals = schema["properties"]["refined_change_proposals"]
    assert refined_change_proposals["type"] == "array"
    assert "minItems" not in refined_change_proposals
    assert refined_change_proposals["items"]["type"] == "object"
    assert schema["properties"]["resume_overwrite_performed"] == {"const": False}
    assert schema["properties"]["resume_mutation_performed"] == {"const": False}
    assert schema["properties"]["application_submission_performed"] == {
        "const": False
    }


def test_live_tailoring_schema_is_recursively_groq_strict_object_compatible():
    schema = services.LIVE_TAILORING_SUGGESTION_DRY_RUN_RESPONSE_SCHEMA
    object_nodes = _strict_schema_object_nodes(schema)

    assert {path for path, _node in object_nodes} == {
        "$",
        "$.properties.patch_ready_suggestions.items",
        "$.properties.patch_ready_suggestions.items.properties.jd_signal_links.items",
        "$.properties.guidance_only_suggestions.items",
        "$.properties.guidance_only_suggestions.items.properties.jd_signal_links.items",
        "$.properties.rejected_suggestions.items",
        "$.properties.rejected_suggestions.items.properties.jd_signal_links.items",
        "$.properties.unsupported_claim_risks.items",
    }
    for _path, object_schema in object_nodes:
        assert object_schema["additionalProperties"] is False
        assert set(object_schema["properties"]) == set(object_schema["required"])

    exact_object_nodes = _strict_schema_object_nodes(
        _exact_request_packet()["request_schema"]
    )
    assert exact_object_nodes
    for _path, object_schema in exact_object_nodes:
        assert object_schema["additionalProperties"] is False
        assert set(object_schema["properties"]) == set(object_schema["required"])


def test_live_tailoring_strict_schema_rejects_extra_and_missing_nested_fields():
    schema = services.LIVE_TAILORING_SUGGESTION_DRY_RUN_RESPONSE_SCHEMA
    extra = _strict_tailoring_provider_content()
    extra["patch_ready_suggestions"][0]["target_section"] = "experience"
    missing = _strict_tailoring_provider_content()
    del missing["patch_ready_suggestions"][0]["reason"]

    assert _schema_contract_errors(extra, schema) == [
        "$.patch_ready_suggestions[0]: unexpected property target_section"
    ]
    assert _schema_contract_errors(missing, schema) == [
        "$.patch_ready_suggestions[0]: missing required property reason"
    ]


def test_live_tailoring_strict_schema_preserves_empty_optional_semantics():
    schema = services.LIVE_TAILORING_SUGGESTION_DRY_RUN_RESPONSE_SCHEMA
    content = _strict_tailoring_provider_content()
    content["patch_ready_suggestions"] = []
    content["guidance_only_suggestions"] = [
        _strict_tailoring_suggestion(patch_ready=False)
    ]
    content["missing_evidence"] = ["required_skills:Python:resume_evidence_missing"]
    content["unsupported_claim_risks"] = [
        {
            "field": "required_skills",
            "signal": "Python",
            "risk": "unsupported_claim",
        }
    ]
    content["projected_score_delta"] = 0.0

    assert _schema_contract_errors(content, schema) == []
    normalized, errors = services._normalise_live_tailoring_provider_payload(content)
    assert errors == []
    assert normalized is not None
    assert normalized["guidance_only_suggestions"][0]["source_bullet_id"] == ""
    assert normalized["guidance_only_suggestions"][0]["evidence_spans"] == []
    assert normalized["guidance_only_suggestions"][0]["patch_ready"] is False


def test_live_tailoring_strict_provider_response_reaches_phase56_readback(
    monkeypatch,
):
    _stateful_storage(monkeypatch)
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return {
            "content": _strict_tailoring_provider_content(),
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "fallback_used": False,
        }

    monkeypatch.setattr(llm_client, "run_chat_completion_with_metadata", fake_completion)

    result = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_tailoring_suggestion"],
    )

    assert len(calls) == 1
    call = calls[0]
    assert call["provider"] == "groq"
    assert call["model"] == GROQ_PREMIUM_MODEL
    assert call["temperature"] == 0
    assert call["max_tokens"] == 900
    assert call["response_mime_type"] == "application/json"
    assert call["response_schema"] == (
        services.LIVE_TAILORING_SUGGESTION_DRY_RUN_RESPONSE_SCHEMA
    )
    assert services._live_tailoring_suggestion_structured_output_contract()[
        "strict"
    ] is True
    assert call["return_parsed"] is True
    assert call["thinking_budget"] == 0
    assert call["fallback_enabled"] is False
    assert all(isinstance(message["content"], str) for message in call["messages"])
    readback = result["live_tailoring_suggestion_readback"]
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["provider"] == "groq"
    assert readback["model"] == GROQ_PREMIUM_MODEL
    assert readback["suggestion_count"] == 1
    expected_preview = {
        "suggestion_id": "live_tailoring_001",
        "suggestion_type": "patch_ready",
        "source_bullet_id": "bullet-1",
        "target_section": "",
        "patch_ready": True,
    }
    assert all(
        readback["suggestions_preview"][0][key] == value
        for key, value in expected_preview.items()
    )
    assert result["diagnostic_state"]["last_execution"][
        "provider_retry_performed"
    ] is False
    assert not {
        "failure_category",
        "exception_class",
        "safe_error_summary",
        "retry_performed",
        "provider_fallback_performed",
    }.intersection(readback)


def test_live_tailoring_failed_readback_preserves_only_safe_structured_metadata(
    monkeypatch,
):
    class StructuredGroqError(RuntimeError):
        status_code = 400
        error_category = "invalid_request"
        body = {
            "error": {
                "message": "response_format is unsupported",
                "type": "invalid_request_error",
                "code": "unsupported_value",
                "param": "response_format",
            }
        }

    stored, original, calls = _stateful_storage(monkeypatch)

    def failing_adapter(_request):
        raise StructuredGroqError("provider rejected the structured request")

    result = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_tailoring_suggestion"],
        live_tailoring_suggestion_adapter=failing_adapter,
    )

    readback = result["live_tailoring_suggestion_readback"]
    assert readback["provider"] == "groq"
    assert readback["model"] == GROQ_PREMIUM_MODEL
    assert readback["failure_category"] == "invalid_request"
    assert readback["exception_class"] == "StructuredGroqError"
    assert readback["http_status"] == 400
    assert readback["provider_error_type"] == "invalid_request_error"
    assert readback["provider_error_code"] == "unsupported_value"
    assert readback["provider_error_param"] == "response_format"
    assert readback["invalid_request_reason"] == "response_format"
    assert readback["provider_call_attempted"] is True
    assert readback["retry_performed"] is False
    assert readback["provider_fallback_performed"] is False
    assert len(readback["safe_error_summary"]) <= 240
    persisted = stored["scan"]["payload_json"]["scan_review_payload"][
        "diagnostic_state"
    ]["readbacks"]["live_tailoring_suggestion_readback"]
    assert persisted == readback
    assert calls["get"]
    assert all(
        call == {"scan_id": "phase56a-scan", "owner_user_id": "owner-71b"}
        for call in calls["get"]
    )
    assert calls["diagnostic_save"][0]["owner_user_id"] == "owner-71b"
    assert stored["scan"]["payload_json"]["scan_review_payload"]["draft"] == (
        original["scan"]["payload_json"]["scan_review_payload"]["draft"]
    )


def test_live_tailoring_failure_never_persists_unsafe_exception_content(monkeypatch):
    stored, _original, _calls = _stateful_storage(monkeypatch)
    unsafe_markers = (
        "Authorization: Bearer sk-test-secret",
        '"prompt":"private resume and JD"',
        "/Users/private/resume.pdf",
    )
    unsafe_message = "\n".join(unsafe_markers) + (" request-body" * 2_000)

    def failing_adapter(_request):
        raise RuntimeError(unsafe_message)

    result = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_tailoring_suggestion"],
        live_tailoring_suggestion_adapter=failing_adapter,
    )

    readback = result["live_tailoring_suggestion_readback"]
    assert readback["provider"] == "groq"
    assert readback["model"] == GROQ_PREMIUM_MODEL
    assert readback["failure_category"] == "provider_adapter_error"
    assert readback["exception_class"] == "RuntimeError"
    assert readback["provider_call_attempted"] is True
    assert readback["retry_performed"] is False
    assert readback["provider_fallback_performed"] is False
    assert len(readback["safe_error_summary"]) <= 240
    for absent in (
        "http_status",
        "provider_error_type",
        "provider_error_code",
        "provider_error_param",
        "invalid_request_reason",
        "schema_keyword",
    ):
        assert absent not in readback
    persisted_text = json.dumps(
        stored["scan"]["payload_json"]["scan_review_payload"]["diagnostic_state"],
        sort_keys=True,
    )
    for marker in unsafe_markers:
        assert marker not in persisted_text
    assert "request-body" not in persisted_text


def test_live_tailoring_bounded_client_failure_contract_survives_readback():
    error = RuntimeError(
        "LLM provider invocation failed (stage=primary, category=invalid_request, "
        "provider=groq, model=openai/gpt-oss-120b, "
        "invalid_request_reason=response_schema, "
        "error_type=invalid_request_error, "
        "error_code=json_schema_validation_failed, "
        "error_param=response_schema, schema_keyword=additionalProperties)"
    )

    metadata = services._live_tailoring_provider_failure_metadata(
        error,
        provider="groq",
        model=GROQ_PREMIUM_MODEL,
    )

    assert metadata["failure_category"] == "invalid_request"
    assert metadata["provider_error_type"] == "invalid_request_error"
    assert metadata["provider_error_code"] == "json_schema_validation_failed"
    assert metadata["provider_error_param"] == "response_schema"
    assert metadata["invalid_request_reason"] == "response_schema"
    assert metadata["schema_keyword"] == "additionalProperties"
    assert metadata["retry_performed"] is False
    assert metadata["provider_fallback_performed"] is False


def test_scan_diagnostics_provider_adapters_use_groq_premium_structured_output(
    monkeypatch,
):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return {
            "content": {},
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "fallback_used": False,
        }

    monkeypatch.setattr(llm_client, "run_chat_completion_with_metadata", fake_completion)

    services._live_tailoring_suggestion_provider_adapter({})
    exact_packet = _exact_request_packet()
    services._live_exact_resume_change_proposal_provider_adapter(exact_packet)

    assert len(calls) == 2
    for call in calls:
        assert call["provider"] == "groq"
        assert call["model"] == GROQ_PREMIUM_MODEL
        assert call["response_mime_type"] == "application/json"
        assert call["response_schema"]
        assert call["return_parsed"] is True
        assert call["thinking_budget"] == 0
        assert call["fallback_enabled"] is False
        assert all(isinstance(message["content"], str) for message in call["messages"])
    assert calls[1]["response_schema"] == exact_packet["request_schema"]
    assert (
        "minItems"
        not in calls[1]["response_schema"]["properties"][
            "refined_change_proposals"
        ]
    )


def test_empty_exact_provider_response_reaches_domain_validation(monkeypatch):
    _stateful_storage(monkeypatch)

    result = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_exact_resume_change_proposal"],
        live_exact_resume_change_proposal_adapter=lambda _request: {
            "refined_change_proposals": [],
            "resume_overwrite_performed": False,
            "resume_mutation_performed": False,
            "application_submission_performed": False,
            "model_provider": "groq",
            "model_name": GROQ_PREMIUM_MODEL,
        },
    )

    readback = result["live_exact_resume_change_proposal_readback"]
    assert readback["validation_status"] == "fallback"
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"] == "provider_response_invalid"
    assert readback["fallback_error_class"] == "ValueError"
    assert readback["validation_errors"] == [
        "refined_change_proposals must not be empty"
    ]
    assert result["diagnostic_state"]["last_execution"][
        "provider_retry_performed"
    ] is False


def test_exact_change_readback_preserves_human_review_fields():
    provider_payload = _valid_exact_provider_payload()
    proposal = provider_payload["refined_change_proposals"][0]
    readback = services.build_planning_workspace_live_exact_resume_change_proposal_readback(
        {
            "runtime_result": {"provider_response": provider_payload},
            "validation_result": {"validation_status": "valid"},
            "normalization_result": {
                "normalized_refined_change_proposals": [proposal],
            },
        },
        enabled=True,
    )

    assert readback["proposed_changes_preview"] == [
        {
            "proposal_id": proposal["proposal_id"],
            "change_type": proposal["change_type"],
            "target_section": proposal["target_section"],
            "target_identifier": proposal["target_identifier"],
            "current_text": proposal["current_text"],
            "proposed_text": proposal["proposed_text"],
            "change_reason": proposal["change_reason"],
            "jd_terms_supported": proposal["jd_terms_supported"],
            "resume_evidence_used": proposal["resume_evidence_used"],
            "risk_flags": proposal["risk_flags"],
            "manual_review_required": True,
            "requires_user_acceptance": True,
        }
    ]


def test_saved_scan_contract_supplies_exact_change_jd_context_when_llm_jd_is_unavailable(
    monkeypatch,
):
    stored, _original, _calls = _stateful_storage(monkeypatch)
    review = stored["scan"]["payload_json"]["scan_review_payload"]
    review["jd_llm_extraction_readback"] = {
        "llm_enabled": False,
        "fallback_used": True,
        "validation_status": "disabled",
        "structured_jd_signals": {"required_skills": [], "tools": []},
    }
    review["scan_issue_contract"] = services._build_tailoring_scan_issue_contract(
        trusted_ready=[],
        trusted_optional=[],
        ai_optimize_optional=[],
        directional_guidance=[],
        resume_evidence=_resume_evidence(
            skills=["Python"],
            bullets=["Built Python pipelines."],
        ),
        tailoring_summary={"matched_required": ["Python"]},
    )
    resolved_jd_context = services._planning_workspace_exact_change_jd_context(review)
    assert resolved_jd_context == {
        "required_skills": ["Python"],
        "tools": [],
        "domain": [],
    }
    provider_calls = []

    result = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_exact_resume_change_proposal"],
        live_exact_resume_change_proposal_adapter=lambda request: provider_calls.append(
            deepcopy(request)
        )
        or _valid_exact_provider_payload(),
    )

    assert len(provider_calls) == 1
    assert provider_calls[0]["included_change_proposals"]
    request_payload = json.loads(provider_calls[0]["request_messages"][1]["content"])
    assert request_payload["jd_context"]["required_skills"] == ["Python"]
    assert request_payload["jd_context"]["tools"] == []
    readback = result["live_exact_resume_change_proposal_readback"]
    assert readback["validation_status"] == "valid"
    assert readback["exact_change_llm_call_performed"] is True


def test_blocked_exact_change_packet_never_dispatches_provider(monkeypatch):
    stored, _original, _calls = _stateful_storage(monkeypatch)
    review = stored["scan"]["payload_json"]["scan_review_payload"]
    review["jd_llm_extraction_readback"] = {
        "llm_enabled": False,
        "fallback_used": True,
        "validation_status": "disabled",
        "structured_jd_signals": {"required_skills": [], "tools": []},
    }
    review["scan_issue_contract"] = {
        "version": "scan_issue_contract_v2",
        "source": "tailoring_keyword_scan",
        "issues": [],
    }
    review.pop("required_skills", None)
    review.pop("tools", None)
    provider_calls = []

    raw_readback = services._planning_workspace_live_exact_resume_change_proposal_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        enabled=True,
        adapter=lambda request: provider_calls.append(request),
        draft=review.get("draft"),
    )

    proposal_result = raw_readback["stage_results"]["proposal_builder"]
    request_result = raw_readback["stage_results"]["request_packet"]
    request_summary = request_result["request_packet_summary"]
    assert proposal_result["change_set_summary"]["change_proposal_count"] == 0
    assert request_summary["request_blocked"] is True
    assert request_summary["included_change_proposal_count"] == 0
    assert request_summary["provider_dispatch_ready"] is False
    assert raw_readback["exact_change_llm_call_attempted"] is False
    assert raw_readback["exact_change_llm_call_performed"] is False

    result = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["live_exact_resume_change_proposal"],
        live_exact_resume_change_proposal_adapter=lambda request: provider_calls.append(
            request
        ),
    )

    assert provider_calls == []
    readback = result["live_exact_resume_change_proposal_readback"]
    assert readback["validation_status"] == "blocked"
    assert readback["fallback_used"] is False
    assert readback["fallback_reason"] == ""
    assert readback["fallback_error_class"] == ""
    assert readback.get("exact_change_llm_call_attempted", False) is False
    assert readback.get("exact_change_llm_call_performed", False) is False
    assert readback.get("provider", "") == ""
    assert readback.get("model", "") == ""
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["network_call_performed"] is False
    assert result["stage_results"] == [
        {
            "stage": "live_exact_resume_change_proposal",
            "readback_key": "live_exact_resume_change_proposal_readback",
            "status": "blocked",
            "valid": False,
            "validation_errors": ["exact_change_provider_dispatch_not_ready"],
        }
    ]
    assert result["diagnostic_state"]["last_execution"][
        "provider_retry_performed"
    ] is False


def test_groq_premium_transport_keeps_json_schema_and_lowest_reasoning_effort():
    calls = []

    class Completions:
        @staticmethod
        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(message=SimpleNamespace(content='{"status":"ok"}'))
                ]
            )

    schema = {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"],
        "additionalProperties": False,
    }
    messages = [{"role": "user", "content": "bounded text"}]

    result = llm_client._run_groq_chat_completion(
        messages=messages,
        model=GROQ_PREMIUM_MODEL,
        temperature=0,
        max_tokens=64,
        response_mime_type="application/json",
        response_schema=schema,
        return_parsed=True,
        thinking_budget=0,
        provider_client=SimpleNamespace(chat=SimpleNamespace(completions=Completions())),
    )

    assert result == {"status": "ok"}
    assert len(calls) == 1
    assert calls[0]["messages"] == messages
    assert calls[0]["model"] == GROQ_PREMIUM_MODEL
    assert calls[0]["max_completion_tokens"] == 64
    assert calls[0]["reasoning_effort"] == "low"
    assert calls[0]["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "structured_output",
            "strict": True,
            "schema": schema,
        },
    }
    assert "include_reasoning" not in calls[0]


@pytest.mark.parametrize(
    ("adapter", "provider_constant", "model_constant", "payload"),
    (
        (
            services._live_tailoring_suggestion_provider_adapter,
            "LIVE_TAILORING_SUGGESTION_DRY_RUN_PROVIDER",
            "LIVE_TAILORING_SUGGESTION_DRY_RUN_MODEL",
            {},
        ),
        (
            services._live_exact_resume_change_proposal_provider_adapter,
            "LIVE_EXACT_RESUME_CHANGE_PROPOSAL_PROVIDER",
            "LIVE_EXACT_RESUME_CHANGE_PROPOSAL_MODEL",
            None,
        ),
    ),
)
def test_scan_diagnostics_non_groq_configuration_fails_before_transport(
    monkeypatch,
    adapter,
    provider_constant,
    model_constant,
    payload,
):
    calls = []
    monkeypatch.setattr(services, provider_constant, "openai")
    monkeypatch.setattr(services, model_constant, "gpt-5-mini")
    monkeypatch.setattr(
        llm_client,
        "run_chat_completion_with_metadata",
        lambda **kwargs: calls.append(kwargs),
    )

    with pytest.raises(ValueError, match="provider must be groq"):
        adapter(_exact_request_packet() if payload is None else payload)

    assert calls == []


def test_scan_diagnostics_defaults_ignore_ambient_route_and_disable_fallback():
    assert services.LIVE_TAILORING_SUGGESTION_DRY_RUN_PROVIDER == "groq"
    assert services.LIVE_TAILORING_SUGGESTION_DRY_RUN_MODEL == GROQ_PREMIUM_MODEL
    assert services.LIVE_TAILORING_SUGGESTION_DRY_RUN_FALLBACK_ENABLED is False
    assert services.LIVE_EXACT_RESUME_CHANGE_PROPOSAL_PROVIDER == "groq"
    assert services.LIVE_EXACT_RESUME_CHANGE_PROPOSAL_MODEL == GROQ_PREMIUM_MODEL
    assert services.LIVE_EXACT_RESUME_CHANGE_PROPOSAL_FALLBACK_ENABLED is False


def test_deterministic_downstream_stage_invokes_no_provider(monkeypatch):
    _stateful_storage(monkeypatch)
    calls = []
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda payload: calls.append(("tailoring", payload)),
    )
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda payload: calls.append(("exact", payload)),
    )

    result = services.execute_saved_scan_diagnostics_payload(
        scan_id="phase56a-scan",
        owner_user_id="owner-71b",
        diagnostic_stages=["manual_exact_change_acceptance"],
    )

    assert calls == []
    assert result["diagnostic_state"]["last_execution"][
        "provider_retry_performed"
    ] is False
    assert result["diagnostic_state"]["last_execution"][
        "background_execution_performed"
    ] is False

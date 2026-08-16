"""Authoritative production semantics for manual provider preview."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any


TASK_CONTRACT_VERSION = "manual-provider-preview-v1"
SCHEMA_NAME = "manual_provider_preview_result_v1"
TEMPERATURE = 0
MAX_TOKENS = 700
SYSTEM_PROMPT = (
    "Generate a bounded, evidence-grounded resume tailoring preview for manual "
    "review. Use only the authorized job context and bounded resume evidence. "
    "Return only JSON. Never authorize, apply, or submit a change."
)
USER_TEMPLATE = (
    "Authorized job context:\n<authorized_job_context>\n\n"
    "Bounded resume evidence context:\n<bounded_resume_evidence_context>\n\n"
    "Selected tailoring opportunity/request:\n<selected_tailoring_request>\n\n"
    "Explicit manual-trigger context:\n<manual_trigger_context>\n\n"
    "Return one to three evidence-grounded preview suggestions. Each suggestion "
    "must retain its source evidence identifiers and must remain advisory."
)
RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "preview_status": {"type": "string", "enum": ["advisory"]},
        "manual_only": {"type": "boolean", "const": True},
        "suggestions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "suggestion_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 128,
                    },
                    "source_evidence_ids": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 8,
                        "items": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 128,
                        },
                    },
                    "preview_text": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1200,
                    },
                    "claims": {
                        "type": "array",
                        "maxItems": 12,
                        "items": {"type": "string", "maxLength": 160},
                    },
                    "rationale": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 600,
                    },
                    "risk_flags": {
                        "type": "array",
                        "maxItems": 8,
                        "items": {"type": "string", "maxLength": 160},
                    },
                },
                "required": [
                    "suggestion_id",
                    "source_evidence_ids",
                    "preview_text",
                    "claims",
                    "rationale",
                    "risk_flags",
                ],
            },
        },
        "resume_mutation_authorized": {"type": "boolean", "const": False},
        "automatic_acceptance_authorized": {
            "type": "boolean",
            "const": False,
        },
        "application_mutation_authorized": {
            "type": "boolean",
            "const": False,
        },
        "auto_apply_authorized": {"type": "boolean", "const": False},
        "auto_submit_authorized": {"type": "boolean", "const": False},
    },
    "required": [
        "preview_status",
        "manual_only",
        "suggestions",
        "resume_mutation_authorized",
        "automatic_acceptance_authorized",
        "application_mutation_authorized",
        "auto_apply_authorized",
        "auto_submit_authorized",
    ],
}


class ManualProviderPreviewResponseError(ValueError):
    """Bounded deterministic validation or normalization failure."""

    def __init__(self, category: str) -> None:
        self.category = str(category or "schema_invalid")
        super().__init__(self.category)


def _response_error(category: str) -> None:
    raise ManualProviderPreviewResponseError(category)


def _authorized_evidence(
    bounded_resume_evidence_context: dict[str, Any],
) -> dict[str, str]:
    rows = bounded_resume_evidence_context.get("evidence")
    if not isinstance(rows, list):
        _response_error("authorized_evidence_unavailable")
    evidence: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            _response_error("authorized_evidence_unavailable")
        evidence_id = row.get("source_evidence_id")
        evidence_text = row.get("text")
        if (
            not isinstance(evidence_id, str)
            or not evidence_id.strip()
            or not isinstance(evidence_text, str)
            or not evidence_text.strip()
        ):
            _response_error("authorized_evidence_unavailable")
        evidence.setdefault(evidence_id, evidence_text)
    if not evidence:
        _response_error("authorized_evidence_unavailable")
    return evidence


def _validate_string(value: Any, schema: dict[str, Any]) -> str:
    if not isinstance(value, str):
        _response_error("schema_invalid")
    minimum = schema.get("minLength")
    maximum = schema.get("maxLength")
    if minimum is not None and len(value) < int(minimum):
        _response_error("schema_invalid")
    if maximum is not None and len(value) > int(maximum):
        _response_error("provider_response_contract_bound_exceeded")
    if minimum and not value.strip():
        _response_error("schema_invalid")
    return value


_CLAIM_STOP_WORDS = {
    "and",
    "for",
    "from",
    "into",
    "that",
    "the",
    "their",
    "this",
    "through",
    "using",
    "with",
}


def _claim_is_grounded(claim: str, evidence_text: str) -> bool:
    claim_terms = {
        term
        for term in re.findall(r"[a-z0-9+#.-]+", claim.lower())
        if len(term) >= 2 and term not in _CLAIM_STOP_WORDS
    }
    evidence_terms = set(
        re.findall(r"[a-z0-9+#.-]+", evidence_text.lower())
    )
    if not claim_terms:
        return False
    supported_terms = claim_terms.intersection(evidence_terms)
    return len(supported_terms) / len(claim_terms) >= 0.5


def validate_manual_provider_preview_production_response(
    response: Any,
    *,
    bounded_resume_evidence_context: dict[str, Any],
) -> dict[str, Any]:
    """Validate one live response against the exact Item 2B schema and evidence."""

    if not isinstance(response, dict):
        _response_error("malformed_provider_response")
    schema = RESPONSE_SCHEMA
    properties = schema["properties"]
    response_keys = set(response)
    required_keys = set(schema["required"])
    if response_keys - set(properties):
        _response_error("unsupported_provider_response_field")
    if required_keys - response_keys:
        _response_error("schema_invalid")
    if response_keys != set(properties):
        _response_error("schema_invalid")

    if response["preview_status"] not in properties["preview_status"]["enum"]:
        _response_error("schema_invalid")
    if response["manual_only"] is not properties["manual_only"]["const"]:
        _response_error("schema_invalid")
    for field_name in (
        "resume_mutation_authorized",
        "automatic_acceptance_authorized",
        "application_mutation_authorized",
        "auto_apply_authorized",
        "auto_submit_authorized",
    ):
        if response[field_name] is not properties[field_name]["const"]:
            _response_error("mutation_authority_requested")

    suggestions_schema = properties["suggestions"]
    suggestions = response["suggestions"]
    if not isinstance(suggestions, list):
        _response_error("schema_invalid")
    if len(suggestions) < int(suggestions_schema["minItems"]):
        _response_error("schema_invalid")
    if len(suggestions) > int(suggestions_schema["maxItems"]):
        _response_error("provider_response_contract_bound_exceeded")

    evidence = _authorized_evidence(bounded_resume_evidence_context)
    item_schema = suggestions_schema["items"]
    item_properties = item_schema["properties"]
    item_keys = set(item_properties)
    required_item_keys = set(item_schema["required"])
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            _response_error("schema_invalid")
        suggestion_keys = set(suggestion)
        if suggestion_keys - item_keys:
            _response_error("unsupported_provider_response_field")
        if required_item_keys - suggestion_keys or suggestion_keys != item_keys:
            _response_error("schema_invalid")

        _validate_string(suggestion["suggestion_id"], item_properties["suggestion_id"])
        _validate_string(suggestion["preview_text"], item_properties["preview_text"])
        _validate_string(suggestion["rationale"], item_properties["rationale"])

        evidence_ids = suggestion["source_evidence_ids"]
        evidence_ids_schema = item_properties["source_evidence_ids"]
        if not isinstance(evidence_ids, list):
            _response_error("schema_invalid")
        if len(evidence_ids) < int(evidence_ids_schema["minItems"]):
            _response_error("schema_invalid")
        if len(evidence_ids) > int(evidence_ids_schema["maxItems"]):
            _response_error("provider_response_contract_bound_exceeded")
        for evidence_id in evidence_ids:
            _validate_string(evidence_id, evidence_ids_schema["items"])
            if evidence_id not in evidence:
                _response_error("ungrounded_evidence_reference")

        referenced_evidence = " ".join(
            evidence[evidence_id] for evidence_id in evidence_ids
        )
        for field_name in ("claims", "risk_flags"):
            values = suggestion[field_name]
            values_schema = item_properties[field_name]
            if not isinstance(values, list):
                _response_error("schema_invalid")
            if len(values) > int(values_schema["maxItems"]):
                _response_error("provider_response_contract_bound_exceeded")
            for value in values:
                _validate_string(value, values_schema["items"])
                if not value.strip():
                    _response_error("schema_invalid")
                if field_name == "claims" and not _claim_is_grounded(
                    value,
                    referenced_evidence,
                ):
                    _response_error("ungrounded_claim")

    return deepcopy(response)


def _normalize_response_text(value: str) -> str:
    return " ".join(value.split())


def _deduplicate_strings(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _normalize_response_text(value)
        if text not in seen:
            seen.add(text)
            normalized.append(text)
    return normalized


def normalize_manual_provider_preview_production_response(
    response: Any,
    *,
    bounded_resume_evidence_context: dict[str, Any],
) -> dict[str, Any]:
    """Normalize a valid live response without repairing or inventing content."""

    validated = validate_manual_provider_preview_production_response(
        response,
        bounded_resume_evidence_context=bounded_resume_evidence_context,
    )
    normalized = deepcopy(validated)
    normalized_ids: set[str] = set()
    for suggestion in normalized["suggestions"]:
        suggestion["suggestion_id"] = _normalize_response_text(
            suggestion["suggestion_id"]
        )
        if suggestion["suggestion_id"] in normalized_ids:
            _response_error("normalization_failure")
        normalized_ids.add(suggestion["suggestion_id"])
        suggestion["source_evidence_ids"] = _deduplicate_strings(
            suggestion["source_evidence_ids"]
        )
        suggestion["preview_text"] = _normalize_response_text(
            suggestion["preview_text"]
        )
        suggestion["claims"] = _deduplicate_strings(suggestion["claims"])
        suggestion["rationale"] = _normalize_response_text(
            suggestion["rationale"]
        )
        suggestion["risk_flags"] = _deduplicate_strings(
            suggestion["risk_flags"]
        )

    return validate_manual_provider_preview_production_response(
        normalized,
        bounded_resume_evidence_context=bounded_resume_evidence_context,
    )


def build_manual_provider_preview_production_task_contract_material(
) -> dict[str, Any]:
    """Return future live-task semantics without execution authority."""

    return {
        "task_contract_version": TASK_CONTRACT_VERSION,
        "prompt_contract": {
            "system": SYSTEM_PROMPT,
            "user_template": USER_TEMPLATE,
        },
        "input_contract": {
            "fields": [
                "authorized_job_context",
                "bounded_resume_evidence_context",
                "selected_tailoring_request",
                "manual_trigger_context",
            ],
            "authorized_job_context": "bounded_selected_job_fields_only",
            "bounded_resume_evidence_context": (
                "authorized_source_evidence_ids_and_text_only"
            ),
            "selected_tailoring_request": "one_explicit_selected_opportunity",
            "manual_trigger_context": (
                "explicit_user_trigger_and_operator_confirmation_required"
            ),
            "maximum_characters": {
                "authorized_job_context": 6000,
                "bounded_resume_evidence_context": 12000,
                "selected_tailoring_request": 4000,
                "manual_trigger_context": 1000,
            },
        },
        "output_contract": {
            "schema_name": SCHEMA_NAME,
            "strict": True,
            "schema": deepcopy(RESPONSE_SCHEMA),
        },
        "deterministic_transformation_contract": {
            "input_serialization": "canonical_bounded_json",
            "suggestion_limit": 3,
            "source_grounding": "exact_authorized_source_evidence_ids",
            "unsupported_claims": "reject",
            "preview_only": True,
            "manual_review_required": True,
            "resume_overwrite_allowed": False,
            "automatic_acceptance_allowed": False,
            "application_mutation_allowed": False,
            "auto_apply_allowed": False,
            "auto_submit_allowed": False,
            "scoring_or_ranking_authority": False,
        },
        "task_parameters": {
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "thinking_budget": 0,
            "response_mime_type": "application/json",
            "return_parsed": True,
            "fallback_enabled": False,
        },
    }


def build_manual_provider_preview_production_messages(
    *,
    authorized_job_context: dict[str, Any],
    bounded_resume_evidence_context: dict[str, Any],
    selected_tailoring_request: dict[str, Any],
    manual_trigger_context: dict[str, Any],
) -> list[dict[str, str]]:
    """Materialize the current contract prompts from bounded server context."""

    contract = build_manual_provider_preview_production_task_contract_material()
    values = {
        "authorized_job_context": authorized_job_context,
        "bounded_resume_evidence_context": bounded_resume_evidence_context,
        "selected_tailoring_request": selected_tailoring_request,
        "manual_trigger_context": manual_trigger_context,
    }
    limits = contract["input_contract"]["maximum_characters"]
    serialized: dict[str, str] = {}
    for field_name in contract["input_contract"]["fields"]:
        value = values[field_name]
        if not isinstance(value, dict) or not value:
            raise ValueError(f"{field_name} is required")
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if len(text) > int(limits[field_name]):
            raise ValueError(f"{field_name} exceeds its production bound")
        serialized[field_name] = text

    user_prompt = contract["prompt_contract"]["user_template"]
    for field_name, text in serialized.items():
        user_prompt = user_prompt.replace(f"<{field_name}>", text)

    return [
        {"role": "system", "content": contract["prompt_contract"]["system"]},
        {"role": "user", "content": user_prompt},
    ]

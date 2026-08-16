"""Authoritative production semantics for manual provider preview."""

from __future__ import annotations

from copy import deepcopy
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

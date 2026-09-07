"""Versioned, offline JD-intelligence contract for matching enrichment.

The live/manual and New Scan consumers in ``src.app.services`` continue to own
and use their v1 contract.  This v2 contract is deliberately not connected to
a provider or to ``build_job_evidence``; it prepares category-preserving,
source-groundable output for a later explicitly authorized integration step.
"""

from copy import deepcopy
from typing import Any, Dict, List, Tuple


JD_INTELLIGENCE_MATCHING_SCHEMA_NAME = "jd_intelligence_matching_enrichment_v2"
JD_INTELLIGENCE_MATCHING_PROMPT_VERSION = (
    "v2_verbatim_required_preferred_taxonomy"
)
JD_INTELLIGENCE_MATCHING_CONTRACT_VERSION = "v2"

JD_INTELLIGENCE_MATCHING_SIGNAL_MAX_LENGTH = 128
JD_INTELLIGENCE_MATCHING_EVIDENCE_SPAN_MAX_LENGTH = 160
JD_INTELLIGENCE_MATCHING_CATEGORY_MAX_ITEMS = 8
JD_INTELLIGENCE_MATCHING_RISK_FLAG_MAX_ITEMS = 8

JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS = (
    "required_skills",
    "preferred_skills",
    "required_tools",
    "preferred_tools",
    "required_workflows",
    "preferred_workflows",
    "required_methods",
    "preferred_methods",
    "business_contexts",
    "stakeholder_contexts",
    "ownership_signals",
)

JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS = (
    *JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS,
    "domain",
    "seniority",
)


def _signal_item_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "signal": {
                "type": "string",
                "minLength": 1,
                "maxLength": JD_INTELLIGENCE_MATCHING_SIGNAL_MAX_LENGTH,
            },
            "evidence_span": {
                "type": "string",
                "minLength": 1,
                "maxLength": JD_INTELLIGENCE_MATCHING_EVIDENCE_SPAN_MAX_LENGTH,
            },
        },
        "required": ["signal", "evidence_span"],
    }


def _signal_list_schema(*, max_items: int) -> Dict[str, Any]:
    return {
        "type": "array",
        "maxItems": max_items,
        "items": _signal_item_schema(),
    }


JD_INTELLIGENCE_MATCHING_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "contract_version": {
            "type": "string",
            "enum": [JD_INTELLIGENCE_MATCHING_CONTRACT_VERSION],
        },
        **{
            field: _signal_list_schema(
                max_items=(
                    1
                    if field in {"domain", "seniority"}
                    else JD_INTELLIGENCE_MATCHING_CATEGORY_MAX_ITEMS
                )
            )
            for field in JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS
        },
        "risk_flags": {
            "type": "array",
            "maxItems": JD_INTELLIGENCE_MATCHING_RISK_FLAG_MAX_ITEMS,
            "items": {
                "type": "string",
                "maxLength": JD_INTELLIGENCE_MATCHING_EVIDENCE_SPAN_MAX_LENGTH,
            },
        },
        "extraction_confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": [
        "contract_version",
        *JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS,
        "risk_flags",
        "extraction_confidence",
    ],
}

JD_INTELLIGENCE_MATCHING_SYSTEM_PROMPT = (
    "Extract structured matching evidence from only the full job description "
    "supplied by the user. Return only JSON matching the provided schema. "
    "Return only signals explicitly supported by that job description. For "
    "every signal, copy a short evidence_span verbatim from the job "
    "description; do not copy an entire paragraph. Keep each normalized signal "
    "lexically close to its evidence span by reusing the JD's key factual "
    "words instead of substituting synonyms. Classify each signal once in its "
    "most specific allowed category; never use skills as a catch-all. Skills "
    "are capabilities, competencies, or bodies of knowledge. Tools are named "
    "software, platforms, technologies, applications, systems, frameworks, or "
    "environments. Methods are named analytical, scientific, statistical, "
    "process-improvement, research, or problem-solving methodologies and "
    "techniques. Workflows are recurring responsibilities, processes, or work "
    "activities. Business contexts are functional or operating environments. "
    "Stakeholder contexts are people, groups, or functions collaborated with "
    "or supported. Domain is the one broader industry or subject-matter domain. "
    "Ownership signals require explicit ownership or accountability language. "
    "When categories overlap, prefer tool, then method, then workflow, then "
    "business context, then stakeholder context, then domain, before skill. "
    "A named system is a tool; operating-domain experience is not a tool. A "
    "named methodology or technique is a method; experience in an industry or "
    "operating context is not a skill. Do not "
    "duplicate semantic equivalents across categories. Omit degrees, education, "
    "certifications, and credentials because the schema has no credential "
    "category. Distinguish required from preferred skills, tools, workflows, "
    "and methods using the job description's own requirement language. Treat "
    "responsibilities, must-haves, required or minimum qualifications, and "
    "explicit expectations or equivalent mandatory language as required. Treat "
    "preferred, nice-to-have, bonus, strong-candidate, desired, plus, or "
    "equivalent optional language as preferred. Do not infer required from "
    "apparent importance or preferred from late placement alone. Never "
    "strengthen a preferred qualification "
    "into a required one, never duplicate a signal across required and "
    "preferred, and omit an ambiguous classification rather than guess. Omit "
    "boilerplate, equal-employment language, compensation, and benefits unless "
    "the text genuinely supports an allowed matching category. "
    "Do not provide reasoning, recommendations, Markdown, or fields outside "
    "the schema."
)


def jd_intelligence_matching_structured_output_contract() -> Dict[str, Any]:
    """Return the strict v2 response contract without exposing mutable globals."""

    return {
        "name": JD_INTELLIGENCE_MATCHING_SCHEMA_NAME,
        "strict": True,
        "schema": deepcopy(JD_INTELLIGENCE_MATCHING_RESPONSE_SCHEMA),
    }


def build_jd_intelligence_matching_prompt(*, full_job_description: str) -> str:
    """Build the v2 user prompt from the one authorized evidence source."""

    return "\n".join(
        [
            "Extract the schema fields from the complete job description below.",
            "Use this full job description as the only factual source.",
            "Use empty arrays when an allowed category has no supported value.",
            "Output one JSON object only.",
            "",
            "Full job description:",
            str(full_job_description or ""),
        ]
    )


def _validate_bounded_string(
    value: Any,
    *,
    field: str,
    maximum: int,
    errors: List[str],
) -> None:
    if not isinstance(value, str):
        errors.append(f"invalid_type:{field}:string_required")
        return
    if not value.strip():
        errors.append(f"invalid_value:{field}:nonempty_required")
    if len(value) > maximum:
        errors.append(f"bound_exceeded:{field}:max_length_{maximum}")


def validate_jd_intelligence_matching_payload(
    provider_payload: Any,
) -> Tuple[Dict[str, Any], List[str]]:
    """Validate strict v2 shape and bounds without contacting a provider."""

    if not isinstance(provider_payload, dict):
        return {}, ["provider_response_not_object"]

    source = deepcopy(provider_payload)
    schema = JD_INTELLIGENCE_MATCHING_RESPONSE_SCHEMA
    properties = schema["properties"]
    expected = set(properties)
    supplied = set(source)
    errors: List[str] = []

    missing = sorted(set(schema["required"]) - supplied)
    if missing:
        errors.append("missing_required_fields:" + ",".join(missing))
    unexpected = sorted(supplied - expected)
    if unexpected:
        errors.append("unexpected_fields:" + ",".join(unexpected))

    if source.get("contract_version") != JD_INTELLIGENCE_MATCHING_CONTRACT_VERSION:
        errors.append("invalid_value:contract_version:v2_required")

    for field in JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS:
        values = source.get(field)
        field_schema = properties[field]
        if not isinstance(values, list):
            errors.append(f"invalid_type:{field}:array_required")
            continue
        maximum_items = int(field_schema["maxItems"])
        if len(values) > maximum_items:
            errors.append(f"bound_exceeded:{field}:max_items_{maximum_items}")
        for index, item in enumerate(values):
            item_field = f"{field}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"invalid_type:{item_field}:object_required")
                continue
            item_keys = set(item)
            expected_item_keys = {"signal", "evidence_span"}
            missing_item_keys = sorted(expected_item_keys - item_keys)
            if missing_item_keys:
                errors.append(
                    f"missing_required_fields:{item_field}:"
                    + ",".join(missing_item_keys)
                )
            unexpected_item_keys = sorted(item_keys - expected_item_keys)
            if unexpected_item_keys:
                errors.append(
                    f"unexpected_fields:{item_field}:"
                    + ",".join(unexpected_item_keys)
                )
            if "signal" in item:
                _validate_bounded_string(
                    item["signal"],
                    field=f"{item_field}.signal",
                    maximum=JD_INTELLIGENCE_MATCHING_SIGNAL_MAX_LENGTH,
                    errors=errors,
                )
            if "evidence_span" in item:
                _validate_bounded_string(
                    item["evidence_span"],
                    field=f"{item_field}.evidence_span",
                    maximum=JD_INTELLIGENCE_MATCHING_EVIDENCE_SPAN_MAX_LENGTH,
                    errors=errors,
                )

    risk_flags = source.get("risk_flags")
    if not isinstance(risk_flags, list):
        errors.append("invalid_type:risk_flags:array_required")
    else:
        if len(risk_flags) > JD_INTELLIGENCE_MATCHING_RISK_FLAG_MAX_ITEMS:
            errors.append(
                "bound_exceeded:risk_flags:"
                f"max_items_{JD_INTELLIGENCE_MATCHING_RISK_FLAG_MAX_ITEMS}"
            )
        for index, value in enumerate(risk_flags):
            _validate_bounded_string(
                value,
                field=f"risk_flags[{index}]",
                maximum=JD_INTELLIGENCE_MATCHING_EVIDENCE_SPAN_MAX_LENGTH,
                errors=errors,
            )

    confidence = source.get("extraction_confidence")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= float(confidence) <= 1
    ):
        errors.append(
            "invalid_type:extraction_confidence:number_0_to_1_required"
        )

    return (source if not errors else {}), errors

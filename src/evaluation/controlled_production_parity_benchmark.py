"""Provider-neutral production-parity requests for synthetic qualification.

This owner composes existing transmission-safe fixtures with the semantic
contracts and pure parsers owned by production.  It does not import provider
SDKs, read credentials, select routes, call transports, or persist artifacts.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module
import json
import re
from types import SimpleNamespace
from typing import Any, Dict, Mapping

from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    validate_controlled_provider_benchmark_plan,
    validate_transmittable_request_packet,
)
from src.evaluation.production_task_contract_fingerprints import (
    FINGERPRINTED_PRODUCTION_WORKLOADS,
    UNRESOLVED_PRODUCTION_WORKLOADS,
    build_production_task_contract,
    production_task_contract_sha256,
)
from src.evaluation.provider_benchmark_contract import WORKLOAD_ORDER
from src.evaluation.provider_fixture_benchmark import (
    grade_normalized_candidate_result,
    load_fixture_case_corpus,
)


PARITY_ADAPTER_VERSION = "controlled-production-parity-benchmark-v1"
PARITY_RESULT_VERSION = "controlled-production-parity-result-v1"
PRODUCTION_PARITY_RUNNABLE_WORKLOADS = FINGERPRINTED_PRODUCTION_WORKLOADS
PRODUCTION_PARITY_BLOCKED_WORKLOADS = UNRESOLVED_PRODUCTION_WORKLOADS

_RESPONSE_MODES = {
    "skill_extraction": "json_text",
    "job_fit_evaluation": "json_text",
    "jd_intelligence": "structured_json",
    "grounded_rag_answer": "json_text",
    "resume_fallback_ranking": "json_text",
    "ambiguous_resume_adjudication": "json_text",
    "critic_evaluation": "structured_json",
    "tailoring_generation": "structured_json",
    "tailoring_refinement": "plain_text",
    "tailoring_judge": "plain_text",
    "manual_scan_phrase": "structured_json",
    "manual_provider_preview": "structured_json",
}
_PROMPT_KEYS = {
    "skill_extraction": ("system", "primary_user_template"),
    "job_fit_evaluation": ("system", "batch_user_template"),
    "jd_intelligence": ("system", "user_template"),
    "grounded_rag_answer": ("system", "user_template"),
    "resume_fallback_ranking": ("system", "user_template"),
    "critic_evaluation": ("system", "user_template"),
    "tailoring_generation": ("primary_system", "primary_user_template"),
    "tailoring_refinement": ("system", "user_template"),
    "tailoring_judge": ("system", "user_template"),
    "manual_scan_phrase": ("system", "user_template"),
    "manual_provider_preview": ("system", "user_template"),
}
_PARITY_REQUEST_FIELDS = {
    "parity_adapter_version",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "production_task_contract_sha256",
    "messages",
    "response_contract",
    "task_parameters",
    "local_validation_context",
    "fallback",
    "retry_limit",
    "timeout_seconds",
    "live_execution_requested",
    "synthetic_data_only",
}
_PARITY_RESULT_FIELDS = {
    "parity_result_version",
    "parity_adapter_version",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "production_task_contract_sha256",
    "production_contract_valid",
    "production_validation_errors",
    "production_normalized_output",
    "benchmark_projection",
    "benchmark_quality",
    "authority_invariants",
    "evidence_binding_sha256",
}


class ProductionParityBlocked(ValueError):
    """The workload has no resolved production semantic contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _strings(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen = set()
    for value in values:
        normalized = _clean(value)
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _first(values: Any, fallback: str) -> str:
    items = _strings(values)
    return items[0] if items else fallback


def _replace_text(value: str, replacements: Mapping[str, str]) -> str:
    result = value
    for placeholder, replacement in replacements.items():
        result = result.replace(placeholder, replacement)
    return result


def _replace_value(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, dict):
        return {
            _replace_text(str(key), replacements): _replace_value(item, replacements)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_value(item, replacements) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_value(item, replacements) for item in value)
    if isinstance(value, str):
        return _replace_text(value, replacements)
    return deepcopy(value)


def build_production_parity_runnability() -> Dict[str, Dict[str, Any]]:
    """Return deterministic parity readiness without routing authority."""

    mapping: Dict[str, Dict[str, Any]] = {}
    for workload_id in WORKLOAD_ORDER:
        digest = production_task_contract_sha256(workload_id)
        if digest is None:
            mapping[workload_id] = {
                "status": "blocked_pending_contract_resolution",
                "production_task_contract_sha256": None,
            }
        else:
            mapping[workload_id] = {
                "status": "production_parity_runnable",
                "production_task_contract_sha256": digest,
            }
    _require(tuple(mapping) == WORKLOAD_ORDER, "parity workload order changed")
    _require(
        tuple(
            workload_id
            for workload_id, value in mapping.items()
            if value["status"] == "production_parity_runnable"
        )
        == PRODUCTION_PARITY_RUNNABLE_WORKLOADS,
        "production-parity runnable coverage changed",
    )
    return deepcopy(mapping)


def _case_for_packet(
    packet: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> Dict[str, Any]:
    corpus = load_fixture_case_corpus()
    for case, review in zip(corpus["cases"], plan["transmission_review"]):
        if review["case_alias"] == packet["case_alias"]:
            _require(
                review["eligible_for_later_controlled_transmission"] is True,
                "parity fixture is not transmission-safe",
            )
            _require(
                case["workload_id"] == packet["workload_id"],
                "parity fixture workload mismatch",
            )
            return deepcopy(case)
    raise ValueError("parity fixture alias is unknown")


def _synthetic_material(
    workload_id: str,
    synthetic_input: Mapping[str, Any],
) -> tuple[Dict[str, str], Dict[str, Any]]:
    values = dict(synthetic_input)
    evidence = _strings(values.get("evidence_tokens"))
    supported = _strings(values.get("supported_terms")) or evidence
    required = (
        _strings(values.get("required_terms"))
        or _strings(values.get("required_skills"))
        or _strings(values.get("required_signals"))
    )
    preferred = (
        _strings(values.get("preferred_terms"))
        or _strings(values.get("preferred_skills"))
        or _strings(values.get("preferred_signals"))
    )
    matched = _strings(values.get("matched_skills")) or evidence
    missing = _strings(values.get("missing_skills")) or ["synthetic_requirement_gap"]
    source = (values.get("sources") or [{}])[0] if isinstance(values.get("sources"), list) else {}
    source_tokens = _strings(dict(source or {}).get("evidence_tokens")) or evidence
    candidate_ids = _strings(values.get("candidate_ids")) or ["candidate_alpha", "candidate_beta"]
    original_claims = _strings(values.get("original_claims")) or supported or evidence
    signal = _first(supported or matched or source_tokens, "synthetic_capability_alpha")
    core_term = _first(original_claims or evidence, "synthetic_core_term")

    if workload_id == "skill_extraction":
        description = (
            f"Required qualifications: {', '.join(required)}. "
            + "Synthetic role context. " * 14
            + f"Preferred qualifications: {', '.join(preferred)}."
        )
        replacements = {"<job_description>": description}
        context = {"job_description": description}
    elif workload_id == "job_fit_evaluation":
        replacements = {
            "<job_title>": _clean(values.get("role_category")) or "synthetic_workflow_role",
            "<company>": "synthetic_organization",
            "<required_skill>": ", ".join(required) or "synthetic_skill_alpha",
            "<preferred_skill>": ", ".join(preferred) or "synthetic_skill_delta",
            "<seniority>": "synthetic_seniority",
            "<ai_signal>": _first(evidence, "synthetic_workflow_signal"),
        }
        context = {"required_skills": required, "missing_skills": _strings(values.get("missing_skills"))}
    elif workload_id == "jd_intelligence":
        workflow = _strings(values.get("workflow_context"))
        description = (
            f"Required signals: {', '.join(required)}. Preferred signals: {', '.join(preferred)}. "
            f"Workflow context: {', '.join(workflow)}."
        )
        replacements = {
            "<job_title>": "synthetic_role",
            "<company>": "synthetic_organization",
            "<location>": "synthetic_location",
            "<job_description>": description,
            "<metadata_key>": "fixture_class",
            "<metadata_value>": "synthetic_only",
        }
        context = {"job_description": description}
    elif workload_id == "grounded_rag_answer":
        source_alias = _clean(source.get("source_alias") or source.get("source_id")) or "source_alpha"
        replacements = {
            "<question>": _clean(values.get("question")) or "Which synthetic capability is supported?",
            "<doc_id>": source_alias,
            "<company>": "synthetic_organization",
            "<job_title>": "synthetic_role",
            "<location>": "synthetic_location",
            "<source>": source_alias,
            "<job_url>": "https://example.invalid/synthetic-role",
            "<retrieval_text>": ", ".join(source_tokens) or "synthetic evidence",
        }
        context = {
            "source_alias": source_alias,
            "prompt_sources": [
                {
                    "source_id": "S1",
                    "doc_id": source_alias,
                    "company": "synthetic_organization",
                    "title": "synthetic_role",
                    "location": "synthetic_location",
                    "source": source_alias,
                    "job_url": "https://example.invalid/synthetic-role",
                    "posted_at": "",
                    "score": 1.0,
                    "preview": ", ".join(source_tokens),
                    "retrieval_text": ", ".join(source_tokens),
                }
            ],
            "evidence_tokens": source_tokens,
        }
    elif workload_id == "resume_fallback_ranking":
        replacements = {
            "<company>": "synthetic_organization",
            "<job_title>": "synthetic_role",
            "<role_family>": "synthetic_role_family",
            "<required_skill>": _first(required or evidence, "synthetic_skill_alpha"),
            "<preferred_skill>": _first(preferred, "synthetic_skill_delta"),
            "<all_skill>": ", ".join(evidence) or "synthetic_skill_alpha",
            "<job_description>": "Synthetic role requiring bounded evidence.",
            "<resume_name>": candidate_ids[0],
            "<resume_title>": "synthetic_candidate_role",
            "<matched_term>": _first(matched, candidate_ids[0]),
            "<missing_requirement>": _first(missing, "synthetic_requirement_gap"),
            "<resume_bullet>": f"Delivered {signal} using synthetic evidence.",
        }
        context = {
            "candidate_ids": candidate_ids,
            "deterministic_candidate_id": _clean(values.get("deterministic_candidate_id")) or candidate_ids[0],
            "missing_requirements": missing,
        }
    elif workload_id == "ambiguous_resume_adjudication":
        candidates = [
            deepcopy(candidate)
            for candidate in values.get("candidates", [])
            if isinstance(candidate, dict)
        ]
        _require(bool(candidates), "synthetic readback candidates are required")
        replacements = {}
        context = {"candidates": candidates}
    elif workload_id == "critic_evaluation":
        replacements = {
            "<suggestion_field>": "suggested_text",
            "<suggestion_value>": _clean(values.get("proposed_text")) or "Synthetic supported suggestion.",
            "<jd_field>": "supported_terms",
            "<jd_value>": ", ".join(evidence),
            "<evidence_field>": "evidence_tokens",
            "<evidence_value>": ", ".join(evidence),
        }
        context = {"evidence_tokens": evidence}
    elif workload_id == "tailoring_generation":
        bullet_id = _first(values.get("source_bullet_ids"), "bullet_alpha")
        replacements = {
            "<company>": "synthetic_organization",
            "<job_title>": "synthetic_role",
            "<selected_resume>": "synthetic_resume",
            "<selected_score>": "0.75",
            "<matched_required>": signal,
            "<missing_required>": "synthetic_requirement_gap",
            "<missing_preferred>": "synthetic_preference_gap",
            "<guardrail>": "synthetic_evidence_only",
            "<section>": "experience",
            "<source>": "synthetic_source",
            "<source_entry_id>": "entry_alpha",
            "<source_bullet_id>": bullet_id,
            "<evidence_text>": ", ".join(evidence),
            "<original_bullet>": f"Delivered {', '.join(evidence)}.",
            "<supported_signal>": signal,
        }
        context = {"source_bullet_id": bullet_id, "evidence_tokens": evidence}
    elif workload_id in {"tailoring_refinement", "tailoring_judge"}:
        replacements = {
            "<company>": "synthetic_organization",
            "<job_title>": "synthetic_role",
            "<matched_term>": signal,
            "<original_claim>": " ".join(original_claims),
            "<core_term>": core_term,
            "<supported_signal>": signal,
            "<writer_option_1>": f"Improved {' '.join(original_claims)} by 10% using {core_term} and {signal}.",
            "<writer_option_2>": f"Improved {' '.join(original_claims)} by 10% using {core_term}.",
            "<writer_reason_1>": "supported synthetic alignment",
            "<writer_reason_2>": "preserves deterministic wording",
        }
        context = {
            "patch_id": _clean(values.get("patch_id")) or _first(values.get("candidate_ids"), "patch_alpha"),
            "source_bullet_id": _clean(values.get("source_bullet_id")) or "bullet_alpha",
            "candidate_ids": _strings(values.get("candidate_ids")) or ["patch_alpha", "patch_beta"],
            "unsupported_candidate_ids": _strings(values.get("unsupported_candidate_ids")),
            "original_claims": original_claims,
            "evidence_tokens": evidence or original_claims,
        }
    elif workload_id == "manual_scan_phrase":
        current = f"Delivered {' and '.join(supported)} through bounded synthetic work."
        replacements = {
            "<current_bullet>": current,
            "<guidance>": f"Lead with {signal} while preserving scope.",
            "<supported_term>": ", ".join(supported),
        }
        context = {"current_bullet": current, "supported_terms": supported}
    elif workload_id == "manual_provider_preview":
        evidence_id = "evidence_alpha"
        replacements = {
            "<authorized_job_context>": (
                "Synthetic role requires " + ", ".join(evidence)
            ),
            "<bounded_resume_evidence_context>": (
                f"{evidence_id}: Delivered {', '.join(evidence)}."
            ),
            "<selected_tailoring_request>": (
                f"Clarify the supported {_first(evidence, 'python')} evidence."
            ),
            "<manual_trigger_context>": (
                "explicit_user_trigger=true; operator_confirmed=true"
            ),
        }
        context = {
            "authorized_evidence_ids": [evidence_id],
            "evidence_tokens": evidence,
        }
    else:
        raise ProductionParityBlocked("production parity contract is unresolved")

    context["synthetic_input"] = deepcopy(values)
    context["replacements"] = deepcopy(replacements)
    return replacements, context


def _response_contract(
    workload_id: str,
    production_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    mode = _RESPONSE_MODES[workload_id]
    output = production_contract["output_contract"]
    schema = None
    schema_name = None
    if mode == "structured_json":
        schema = output.get("schema") or output.get("default_schema")
        schema_name = output.get("schema_name") or f"{workload_id}_production_v1"
        _require(isinstance(schema, dict), "structured production schema is unavailable")
    return {
        "mode": mode,
        "schema_name": schema_name,
        "strict": True if mode == "structured_json" else False,
        "schema": deepcopy(schema),
        "production_output_contract": deepcopy(output),
    }


def build_production_parity_request(
    packet: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
    expected_task_contract_sha256: str | None = None,
) -> Dict[str, Any]:
    """Build one transport-ready request from an approved synthetic packet."""

    controlled_plan = build_controlled_provider_benchmark_plan() if plan is None else deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    validate_transmittable_request_packet(packet, plan=controlled_plan)
    workload_id = packet["workload_id"]
    current_digest = production_task_contract_sha256(workload_id)
    if current_digest is None:
        raise ProductionParityBlocked(
            f"{workload_id} is blocked pending production contract resolution"
        )
    if expected_task_contract_sha256 is not None:
        _require(
            expected_task_contract_sha256 == current_digest,
            "production task-contract fingerprint mismatch",
        )
    production_contract = build_production_task_contract(workload_id)
    _require(production_contract is not None, "production task contract is unavailable")
    replacements, local_context = _synthetic_material(
        workload_id,
        packet["synthetic_input"],
    )
    prompt_contract = production_contract["prompt_contract"]
    if workload_id == "ambiguous_resume_adjudication":
        owner = import_module("src.agents.llm_adjudicator_readback")
        messages = owner._provider_prompt(
            deepcopy(local_context["candidates"])
        )
    else:
        system_key, user_key = _PROMPT_KEYS[workload_id]
        messages = [
            {
                "role": "system",
                "content": _replace_text(prompt_contract[system_key], replacements),
            },
            {
                "role": "user",
                "content": _replace_text(prompt_contract[user_key], replacements),
            },
        ]
    task_parameters = deepcopy(production_contract["task_parameters"])
    maximum_tokens = task_parameters.get("max_tokens")
    _require(
        isinstance(maximum_tokens, int)
        and not isinstance(maximum_tokens, bool)
        and 0 < maximum_tokens <= 1024,
        "production task token bound is invalid",
    )
    request = {
        "parity_adapter_version": PARITY_ADAPTER_VERSION,
        "case_alias": packet["case_alias"],
        "workload_id": workload_id,
        "provider": packet["provider"],
        "model": packet["model"],
        "production_task_contract_sha256": current_digest,
        "messages": messages,
        "response_contract": _response_contract(workload_id, production_contract),
        "task_parameters": task_parameters,
        "local_validation_context": local_context,
        "fallback": False,
        "retry_limit": 0,
        "timeout_seconds": packet["timeout_seconds"],
        "live_execution_requested": False,
        "synthetic_data_only": True,
    }
    validate_production_parity_request(request, plan=controlled_plan)
    _case_for_packet(packet, controlled_plan)
    return deepcopy(request)


def validate_production_parity_request(
    request: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> bool:
    controlled_plan = build_controlled_provider_benchmark_plan() if plan is None else deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        isinstance(request, dict) and set(request) == _PARITY_REQUEST_FIELDS,
        "production-parity request fields are invalid",
    )
    _require(
        request.get("parity_adapter_version") == PARITY_ADAPTER_VERSION,
        "production-parity adapter version mismatch",
    )
    workload_id = request.get("workload_id")
    _require(
        workload_id in PRODUCTION_PARITY_RUNNABLE_WORKLOADS,
        "production-parity workload is blocked",
    )
    current_digest = production_task_contract_sha256(workload_id)
    _require(
        request.get("production_task_contract_sha256") == current_digest,
        "production task-contract fingerprint is stale or mismatched",
    )
    _require(
        any(
            row["case_alias"] == request.get("case_alias")
            and row["workload_id"] == workload_id
            and row["provider"] == request.get("provider")
            and row["model"] == request.get("model")
            for row in controlled_plan["staged_matrix"]
        ),
        "production-parity request is outside the 44-cell plan",
    )
    fixture = _case_for_packet(request, controlled_plan)
    expected_replacements, expected_context = _synthetic_material(
        workload_id,
        fixture["normalized_input_packet"],
    )
    _require(
        request.get("local_validation_context") == expected_context,
        "production-parity synthetic context mismatch",
    )
    production_contract = build_production_task_contract(workload_id)
    _require(
        production_contract is not None,
        "production task contract is unavailable",
    )
    prompt_contract = production_contract["prompt_contract"]
    if workload_id == "ambiguous_resume_adjudication":
        owner = import_module("src.agents.llm_adjudicator_readback")
        expected_messages = owner._provider_prompt(
            deepcopy(expected_context["candidates"])
        )
    else:
        system_key, user_key = _PROMPT_KEYS[workload_id]
        expected_messages = [
            {
                "role": "system",
                "content": _replace_text(
                    prompt_contract[system_key],
                    expected_replacements,
                ),
            },
            {
                "role": "user",
                "content": _replace_text(
                    prompt_contract[user_key],
                    expected_replacements,
                ),
            },
        ]
    messages = request.get("messages")
    _require(
        isinstance(messages, list)
        and len(messages) == 2
        and [item.get("role") for item in messages] == ["system", "user"]
        and all(
            isinstance(item, dict)
            and set(item) == {"role", "content"}
            and isinstance(item["content"], str)
            and bool(item["content"].strip())
            for item in messages
        ),
        "production-parity messages are invalid",
    )
    _require(
        messages == expected_messages,
        "production-parity prompt contract mismatch",
    )
    response = request.get("response_contract")
    expected_response = _response_contract(workload_id, production_contract)
    _require(
        isinstance(response, dict)
        and response == expected_response
        and response.get("mode") in {"structured_json", "json_text", "plain_text"},
        "production response mode mismatch",
    )
    if response["mode"] == "structured_json":
        _require(
            response.get("strict") is True
            and isinstance(response.get("schema"), dict),
            "structured production response contract is invalid",
        )
    else:
        _require(
            response.get("strict") is False and response.get("schema") is None,
            "non-structured production response contract is invalid",
        )
    _require(
        request.get("task_parameters") == production_contract["task_parameters"],
        "production task parameters mismatch",
    )
    _require(
        request.get("fallback") is False
        and request.get("retry_limit") == 0
        and request.get("timeout_seconds") == 30
        and request.get("live_execution_requested") is False
        and request.get("synthetic_data_only") is True,
        "production-parity authority or transport bounds changed",
    )
    return True


def _parse_json_object(raw_response: Any, parser) -> Dict[str, Any]:
    if isinstance(raw_response, dict):
        return deepcopy(raw_response)
    parsed = parser(str(raw_response or ""))
    _require(isinstance(parsed, dict), "production response is not an object")
    return parsed


def _tailoring_inputs(context: Mapping[str, Any]):
    owner = import_module("src.tailoring.llm")
    packet, payload, candidate = owner._production_task_contract_representative_tailoring_inputs()
    replacements = context["replacements"]
    return owner, _replace_value(packet, replacements), _replace_value(payload, replacements), _replace_value(candidate, replacements)


def _normalize_production_response(
    request: Mapping[str, Any],
    raw_response: Any,
) -> Dict[str, Any]:
    workload_id = request["workload_id"]
    context = request["local_validation_context"]
    if workload_id == "skill_extraction":
        owner = import_module("src.ai.skill_llm_enricher")
        if isinstance(raw_response, dict):
            parsed = deepcopy(raw_response)
        else:
            try:
                parsed = owner.extract_json_from_response(str(raw_response or ""))
            except Exception:
                parsed = owner._parse_sectioned_skill_response(str(raw_response or ""))
        _require(isinstance(parsed, dict), "skill response is invalid")
        required = owner._filter_skill_candidates(
            parsed.get("required_skills", []), context["job_description"]
        )
        preferred = owner._filter_skill_candidates(
            parsed.get("preferred_skills", []), context["job_description"]
        )
        preferred = [item for item in preferred if item not in required]
        required, preferred = owner._reassign_skills_by_context(
            required, preferred, context["job_description"]
        )
        required, preferred = owner._drop_shadowed_generic_skills(required, preferred)
        return {"required_skills": required, "preferred_skills": preferred}

    if workload_id == "job_fit_evaluation":
        owner = import_module("src.ai.job_fit_evaluator")
        parsed = _parse_json_object(raw_response, owner.extract_json_from_response)
        results = parsed.get("results")
        _require(isinstance(results, list) and bool(results), "job-fit results are missing")
        normalized = []
        for item in results:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "id": item.get("id"),
                    "ai_relevance": item.get("ai_relevance", 0),
                    "skill_match": item.get("skill_match", 0),
                    "seniority_match": item.get("seniority_match", 0),
                    "learning_opportunity": item.get("learning_opportunity", 0),
                    "overall_score": item.get("overall_score", 0),
                    "visa_sponsorship_signal": item.get("visa_sponsorship_signal", "unknown"),
                    "reason": item.get("reason", "No explanation"),
                }
            )
        _require(bool(normalized), "job-fit results are invalid")
        return {"results": normalized}

    if workload_id == "jd_intelligence":
        owner = import_module("src.agents.jd_intelligence")
        payload = owner.build_live_jd_intelligence_dry_run_payload(
            adapter=lambda _input: deepcopy(raw_response),
            feature_enabled=True,
            job_description=context["job_description"],
        )
        _require(payload.get("validation_status") == "valid", "JD response is invalid")
        return {
            field: deepcopy(payload[field])
            for field in owner.LIVE_DRY_RUN_LIST_FIELDS
        } | {"extraction_confidence": payload["extraction_confidence"]}

    if workload_id == "grounded_rag_answer":
        owner = import_module("src.rag.rag_answerer")
        parsed = _parse_json_object(raw_response, owner._extract_json_from_response)
        return owner.normalize_grounded_rag_model_response(
            parsed,
            deepcopy(context["prompt_sources"]),
        )

    if workload_id == "resume_fallback_ranking":
        owner = import_module("batch_select_best_resume_variant")
        parsed = owner._parse_llm_fallback_response(raw_response)
        normalized = owner._normalize_llm_fallback_parsed(
            parsed,
            context["candidate_ids"],
        )
        strict_results = [
            SimpleNamespace(
                pair=SimpleNamespace(resume_name=candidate_id),
                prefilter=SimpleNamespace(
                    missing_requirements=context["missing_requirements"]
                ),
            )
            for candidate_id in context["candidate_ids"]
        ]
        return owner._enforce_fallback_honesty(normalized, strict_results)

    if workload_id == "ambiguous_resume_adjudication":
        owner = import_module("src.agents.llm_adjudicator_readback")
        parsed = owner._parse_provider_response(raw_response)
        summary, label = owner._normalize_provider_response(parsed)
        return {
            "adjudicator_summary": summary,
            "adjudicator_recommendation_label": label,
        }

    if workload_id == "critic_evaluation":
        owner = import_module("src.app.services")
        parsed = raw_response if isinstance(raw_response, dict) else {"raw_response": raw_response}
        normalized, errors = owner._normalise_live_critic_provider_payload(parsed)
        _require(normalized is not None and not errors, "critic response is invalid")
        return normalized

    if workload_id == "tailoring_generation":
        owner, _packet, payload, _candidate = _tailoring_inputs(context)
        parsed = _parse_json_object(raw_response, owner._extract_json_from_llm_response)
        validated = owner._validate_live_llm_parsed_contract(parsed, payload)
        return owner._normalize_live_llm_parsed(validated)

    if workload_id == "tailoring_refinement":
        owner, _packet, _payload, candidate = _tailoring_inputs(context)
        parsed = owner._parse_patch_refinement_writer_text(str(raw_response or ""))
        if parsed.get("abstain"):
            return parsed
        valid, invalid = owner._partition_writer_options_by_validation(
            candidate,
            parsed.get("options", []),
        )
        deterministic = _clean(candidate.get("patch_text"))
        materially_valid = [
            option
            for option in valid
            if not owner._patch_refinement_style_only_delta(
                deterministic,
                _clean(option.get("patch_text")),
            )
        ]
        _require(bool(materially_valid), "writer response has no valid options")
        return {
            "abstain": False,
            "abstain_reason": "",
            "options": materially_valid,
            "invalid_options": invalid,
        }

    if workload_id == "tailoring_judge":
        owner = import_module("src.tailoring.llm")
        parsed = owner._parse_patch_refinement_judge_text(str(raw_response or ""))
        normalized = owner._normalize_patch_refinement_judge_parsed(parsed)
        _require(
            normalized["winner"]
            in {"deterministic", "writer_option_1", "writer_option_2", "abstain"},
            "judge winner is invalid",
        )
        return normalized

    if workload_id == "manual_scan_phrase":
        owner = import_module("src.app.services")
        raw_options = owner._scan_phrase_parse_options_payload(raw_response)
        normalized = owner._scan_phrase_validate_llm_options(
            raw_options,
            current=context["current_bullet"],
            terms=context["supported_terms"],
        )
        _require(bool(normalized), "scan phrase response has no valid options")
        return {"options": normalized}

    if workload_id == "manual_provider_preview":
        parsed = _parse_json_object(raw_response, json.loads)
        required = {
            "preview_status",
            "manual_only",
            "suggestions",
            "resume_mutation_authorized",
            "automatic_acceptance_authorized",
            "application_mutation_authorized",
            "auto_apply_authorized",
            "auto_submit_authorized",
        }
        _require(set(parsed) == required, "manual preview response fields are invalid")
        suggestions = parsed.get("suggestions")
        _require(
            parsed.get("preview_status") == "advisory"
            and parsed.get("manual_only") is True
            and isinstance(suggestions, list)
            and 1 <= len(suggestions) <= 3,
            "manual preview response is not bounded and advisory",
        )
        _require(
            all(parsed.get(field) is False for field in required if field.endswith("_authorized")),
            "manual preview response grants mutation or action authority",
        )
        allowed_ids = set(context["authorized_evidence_ids"])
        normalized = []
        suggestion_fields = {
            "suggestion_id",
            "source_evidence_ids",
            "preview_text",
            "claims",
            "rationale",
            "risk_flags",
        }
        for suggestion in suggestions:
            _require(
                isinstance(suggestion, dict) and set(suggestion) == suggestion_fields,
                "manual preview suggestion fields are invalid",
            )
            source_ids = _strings(suggestion.get("source_evidence_ids"))
            claims = _strings(suggestion.get("claims"))
            _require(
                bool(_clean(suggestion.get("suggestion_id")))
                and bool(source_ids)
                and set(source_ids).issubset(allowed_ids)
                and bool(_clean(suggestion.get("preview_text")))
                and bool(_clean(suggestion.get("rationale"))),
                "manual preview suggestion is ungrounded or incomplete",
            )
            normalized.append({**deepcopy(suggestion), "claims": claims})
        return {**deepcopy(parsed), "suggestions": normalized}

    raise ProductionParityBlocked("production parity contract is unresolved")


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _mentioned_tokens(text: str, candidates: list[str]) -> list[str]:
    normalized = text.casefold()
    return [item for item in candidates if item.casefold() in normalized]


def _claim_tokens(text: str) -> list[str]:
    return _unique(
        re.findall(
            r"\b(?:synthetic_[a-z0-9_]+|python|sql|airflow|dbt|analytics|"
            r"reporting|kubernetes|api)\b",
            text.casefold(),
        )
    )


def _benchmark_projection(
    request: Mapping[str, Any],
    normalized: Mapping[str, Any],
) -> Dict[str, Any]:
    workload_id = request["workload_id"]
    context = request["local_validation_context"]
    synthetic = context["synthetic_input"]
    if workload_id == "skill_extraction":
        return deepcopy(dict(normalized))
    if workload_id == "job_fit_evaluation":
        result = dict((normalized.get("results") or [{}])[0])
        fit_score = max(0.0, min(1.0, _number(result.get("overall_score")) / 10.0))
        required_match = max(0.0, min(1.0, _number(result.get("skill_match")) / 10.0))
        reason = _clean(result.get("reason"))
        evidence = _strings(synthetic.get("evidence_tokens"))
        missing = _strings(synthetic.get("missing_skills"))
        return {
            "classification": "strong_fit" if fit_score >= 0.8 else "partial_fit" if fit_score >= 0.5 else "weak_fit",
            "fit_score": fit_score,
            "required_match_score": required_match,
            "reason_tokens": _mentioned_tokens(reason, evidence),
            "missing_requirements": _mentioned_tokens(reason, missing),
        }
    if workload_id == "jd_intelligence":
        return {
            "required_signals": _strings(normalized.get("required_skills")),
            "preferred_signals": _strings(normalized.get("preferred_skills")),
            "workflow_context": _strings(normalized.get("workflows")),
            "missing_requirements": [],
        }
    if workload_id == "grounded_rag_answer":
        answer = _clean(normalized.get("answer"))
        return {
            "answer_status": "insufficient" if normalized.get("insufficient_evidence") else "supported",
            "claims": _claim_tokens(answer),
            "source_ids": [
                context["source_alias"]
                for source_id in _strings(normalized.get("used_source_ids"))
                if source_id == "S1"
            ],
        }
    if workload_id == "resume_fallback_ranking":
        best = _clean(normalized.get("best_resume"))
        backup = _clean(normalized.get("backup_resume"))
        return {
            "advisory_candidate_id": best,
            "ranking": [item for item in (best, backup) if item],
            "authoritative_candidate_id": context["deterministic_candidate_id"],
            "authority_mutated": False,
        }
    if workload_id == "ambiguous_resume_adjudication":
        return {
            "adjudicator_summary": _clean(normalized.get("adjudicator_summary")),
            "adjudicator_recommendation_label": _clean(
                normalized.get("adjudicator_recommendation_label")
            ),
        }
    if workload_id == "critic_evaluation":
        decisions = (
            list(normalized.get("approved_suggestions") or [])
            + list(normalized.get("downgraded_suggestions") or [])
            + list(normalized.get("rejected_suggestions") or [])
        )
        first_decision = dict(decisions[0] if decisions else {})
        decision = _clean(first_decision.get("decision"))
        return {
            "decision": decision,
            "reason_codes": _strings(first_decision.get("reason_codes")) or _strings(normalized.get("reason_codes")),
            "claims": _claim_tokens(
                " ".join(_strings(first_decision.get("evidence_spans")))
            ),
            "safe_suggestion": decision == "approve",
        }
    if workload_id == "tailoring_generation":
        directions = list(normalized.get("rewrite_directions_structured") or [])
        direction_text = " ".join(_clean(item.get("direction")) for item in directions if isinstance(item, dict))
        return {
            "suggestions": [
                {
                    "suggestion_id": "suggestion_alpha",
                    "source_bullet_id": context["source_bullet_id"],
                    "claims": _claim_tokens(direction_text),
                    "evidence_tokens": context["evidence_tokens"],
                }
            ],
            "human_review_required": True,
            "authority_mutated": False,
        }
    if workload_id == "tailoring_refinement":
        options = list(normalized.get("options") or [])
        patch_text = _clean(options[0].get("patch_text")) if options else ""
        return {
            "patch_id": context["patch_id"],
            "source_bullet_id": context["source_bullet_id"],
            "claims": _claim_tokens(patch_text),
            "structure_valid": bool(options) or bool(normalized.get("abstain")),
            "meaning_preserved": bool(options) or bool(normalized.get("abstain")),
            "authority_mutated": False,
        }
    if workload_id == "tailoring_judge":
        winner = _clean(normalized.get("winner"))
        candidate_ids = context["candidate_ids"]
        selected = (
            candidate_ids[0]
            if winner in {"writer_option_1", "deterministic"}
            else candidate_ids[1]
            if winner == "writer_option_2" and len(candidate_ids) > 1
            else ""
        )
        return {
            "advisory_candidate_id": selected,
            "rejected_candidate_ids": context["unsupported_candidate_ids"],
            "decision": "supported_candidate" if selected else "abstain",
            "authority_mutated": False,
        }
    if workload_id == "manual_scan_phrase":
        return {
            "options": [
                {
                    "option_id": "option_alpha" if index == 0 else f"option_{index + 1}",
                    "terms": _strings(option.get("supported_terms")),
                    "risk_flags": _strings(option.get("risk_flags")),
                }
                for index, option in enumerate(normalized.get("options") or [])
            ],
            "manual_only": True,
            "can_accept_directly": False,
        }
    if workload_id == "manual_provider_preview":
        claims = _unique(
            [
                claim
                for suggestion in normalized.get("suggestions") or []
                for claim in _strings(
                    suggestion.get("claims") if isinstance(suggestion, dict) else []
                )
            ]
        )
        claim_tokens = _claim_tokens(" ".join(claims))
        return {
            "preview_status": "advisory",
            "manual_only": True,
            "claims": claim_tokens,
            "mutation_authorized": False,
            "application_authorized": False,
            "ats_authorized": False,
        }
    return {}


def _grade_projection(
    request: Mapping[str, Any],
    benchmark_projection: Mapping[str, Any],
    *,
    production_contract_valid: bool,
    plan: Mapping[str, Any],
) -> Dict[str, Any]:
    case = _case_for_packet(
        {
            "case_alias": request["case_alias"],
            "workload_id": request["workload_id"],
        },
        plan,
    )
    required = case["required_fields"]
    schema_valid = production_contract_valid and all(
        field in benchmark_projection and benchmark_projection[field] is not None
        for field in required
    )
    candidate = {
        "case_id": case["case_id"],
        "workload_id": request["workload_id"],
        "provider": request["provider"],
        "model": request["model"],
        "normalized_output": deepcopy(dict(benchmark_projection)),
        "schema_valid": schema_valid,
        "normalization_succeeded": production_contract_valid,
        "fallback_used": False,
        "provider_call_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "raw_response_persisted": False,
        "live_execution": False,
        "latency_ms": 0,
        "input_token_count": 0,
        "output_token_count": 0,
        "estimated_cost": 0.0,
    }
    grade = grade_normalized_candidate_result(candidate)
    return deepcopy(grade)


def validate_and_grade_production_parity_response(
    request: Dict[str, Any],
    raw_response: Any,
    *,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate with production semantics, then grade the synthetic projection."""

    controlled_plan = build_controlled_provider_benchmark_plan() if plan is None else deepcopy(plan)
    validate_production_parity_request(request, plan=controlled_plan)
    current_digest = production_task_contract_sha256(request["workload_id"])
    _require(
        request["production_task_contract_sha256"] == current_digest,
        "production task-contract fingerprint is stale or mismatched",
    )
    errors: list[str] = []
    try:
        normalized = _normalize_production_response(request, raw_response)
        production_valid = True
    except Exception:
        normalized = {}
        production_valid = False
        errors = ["production_contract_invalid"]
    benchmark_projection = _benchmark_projection(request, normalized) if production_valid else {}
    benchmark_quality = _grade_projection(
        request,
        benchmark_projection,
        production_contract_valid=production_valid,
        plan=controlled_plan,
    )
    result_without_binding = {
        "parity_result_version": PARITY_RESULT_VERSION,
        "parity_adapter_version": PARITY_ADAPTER_VERSION,
        "case_alias": request["case_alias"],
        "workload_id": request["workload_id"],
        "provider": request["provider"],
        "model": request["model"],
        "production_task_contract_sha256": current_digest,
        "production_contract_valid": production_valid,
        "production_validation_errors": errors,
        "production_normalized_output": deepcopy(normalized),
        "benchmark_projection": deepcopy(benchmark_projection),
        "benchmark_quality": benchmark_quality,
        "authority_invariants": {
            "provider_call_count": 0,
            "fallback_used": False,
            "retry_count": 0,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "raw_response_persisted": False,
            "qualification_status_promoted": False,
            "recommendation_created": False,
            "routing_changed": False,
            "user_task_override_created": False,
        },
    }
    result = {
        **result_without_binding,
        "evidence_binding_sha256": sha256(
            _canonical_json(result_without_binding).encode("utf-8")
        ).hexdigest(),
    }
    validate_production_parity_result(result, request=request, plan=controlled_plan)
    return deepcopy(result)


def validate_production_parity_result(
    result: Dict[str, Any],
    *,
    request: Dict[str, Any],
    plan: Dict[str, Any] | None = None,
) -> bool:
    controlled_plan = build_controlled_provider_benchmark_plan() if plan is None else deepcopy(plan)
    validate_production_parity_request(request, plan=controlled_plan)
    _require(
        isinstance(result, dict) and set(result) == _PARITY_RESULT_FIELDS,
        "production-parity result fields are invalid",
    )
    _require(
        result.get("parity_result_version") == PARITY_RESULT_VERSION
        and result.get("parity_adapter_version") == PARITY_ADAPTER_VERSION,
        "production-parity result version mismatch",
    )
    for field in (
        "case_alias",
        "workload_id",
        "provider",
        "model",
        "production_task_contract_sha256",
    ):
        _require(result.get(field) == request.get(field), "parity result binding mismatch")
    _require(
        result["production_task_contract_sha256"]
        == production_task_contract_sha256(result["workload_id"]),
        "parity result task-contract fingerprint is stale",
    )
    quality = result.get("benchmark_quality")
    _require(
        isinstance(quality, dict)
        and isinstance(quality.get("quality_gate_passed"), bool)
        and isinstance(quality.get("hard_failures"), dict)
        and isinstance(quality.get("workload_metrics"), dict),
        "benchmark quality evidence is invalid",
    )
    _require(
        isinstance(result.get("production_contract_valid"), bool)
        and isinstance(result.get("production_validation_errors"), list),
        "production contract validity evidence is invalid",
    )
    authority = result.get("authority_invariants")
    _require(
        isinstance(authority, dict)
        and authority.get("provider_call_count") == 0
        and authority.get("fallback_used") is False
        and authority.get("retry_count") == 0
        and authority.get("mutation_count") == 0
        and authority.get("application_action_count") == 0
        and authority.get("ats_action_count") == 0
        and authority.get("raw_response_persisted") is False
        and authority.get("qualification_status_promoted") is False
        and authority.get("recommendation_created") is False
        and authority.get("routing_changed") is False
        and authority.get("user_task_override_created") is False,
        "production-parity authority changed",
    )
    material = deepcopy(result)
    supplied_binding = material.pop("evidence_binding_sha256")
    _require(
        supplied_binding == sha256(_canonical_json(material).encode("utf-8")).hexdigest(),
        "production-parity evidence binding mismatch",
    )
    return True

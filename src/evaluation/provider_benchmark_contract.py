"""Deterministic, offline-only provider benchmark contract.

This module defines benchmark inputs and safety constraints.  It intentionally
does not execute benchmarks, import provider clients, read credentials, or
persist artifacts.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List


CONTRACT_VERSION = "provider-benchmark-contract-v1"
FIXTURE_MANIFEST_VERSION = "provider-benchmark-fixture-manifest-v1"
DEFAULT_FIXTURE_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "provider_benchmark"
    / "manifest.json"
)

PROVIDER_ORDER = ("groq", "openai")
MODEL_ORDER = (
    ("groq", "openai/gpt-oss-20b"),
    ("groq", "openai/gpt-oss-120b"),
    ("openai", "gpt-5-mini"),
    ("openai", "gpt-5.1"),
)
MODEL_PROVIDER = {model: provider for provider, model in MODEL_ORDER}

WORKLOAD_ORDER = (
    "skill_extraction",
    "job_fit_evaluation",
    "jd_intelligence",
    "grounded_rag_answer",
    "resume_fallback_ranking",
    "ambiguous_resume_adjudication",
    "critic_evaluation",
    "tailoring_generation",
    "tailoring_refinement",
    "tailoring_judge",
    "manual_scan_phrase",
    "manual_provider_preview",
)

METRIC_ORDER = (
    "provider_call_success_rate",
    "schema_valid_response_rate",
    "normalization_success_rate",
    "grounded_evidence_precision",
    "unsupported_claim_count",
    "hallucination_count",
    "required_field_completeness",
    "deterministic_authority_preservation",
    "winner_agreement",
    "ranking_agreement",
    "skill_extraction_precision",
    "skill_extraction_recall",
    "missing_requirement_accuracy",
    "tailoring_evidence_support",
    "critic_agreement",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "estimated_cost",
    "cache_hit_count",
    "timeout_count",
    "retry_count",
    "rate_limit_count",
    "fallback_activation_count",
    "fallback_correctness",
    "duplicate_call_count",
    "persisted_raw_response_count",
    "mutation_count",
    "application_action_count",
    "ats_action_count",
)

HARD_FAILURE_ORDER = (
    "schema_invalid_result_accepted",
    "unsupported_claim",
    "hallucination",
    "sensitive_data_leakage",
    "deterministic_authority_mutation",
    "queue_mutation",
    "ranking_mutation",
    "selected_resume_mutation",
    "provider_called_while_disabled",
    "silent_cross_provider_fallback",
    "unbounded_retry",
    "missing_provider_observability",
    "missing_model_observability",
    "missing_latency_observability",
    "missing_token_observability",
    "persisted_raw_response",
    "application_action_reached",
    "ats_action_reached",
)

_WORKLOAD_DEFINITIONS = (
    {
        "workload_id": "skill_extraction",
        "tier": "A",
        "execution_responsibility": "skill extraction or enrichment",
        "input_classification": "sanitized_job_text",
        "output_classification": "required_and_preferred_skill_lists",
        "schema_strictness": "validated_json_object",
        "latency_sensitivity": "high",
        "quality_sensitivity": "high",
        "hallucination_risk": "high",
        "privacy_sensitivity": "medium",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory",
        "fallback_eligible": True,
        "failure_disposition": "use_cache_or_empty_result",
        "human_review_required": False,
    },
    {
        "workload_id": "job_fit_evaluation",
        "tier": "B",
        "execution_responsibility": "job fit evaluation and explanation",
        "input_classification": "sanitized_job_and_skill_evidence",
        "output_classification": "bounded_fit_scores_and_reason",
        "schema_strictness": "validated_json_object",
        "latency_sensitivity": "high",
        "quality_sensitivity": "high",
        "hallucination_risk": "high",
        "privacy_sensitivity": "medium",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory",
        "fallback_eligible": True,
        "failure_disposition": "skip_and_mark_evaluation_unavailable",
        "human_review_required": False,
    },
    {
        "workload_id": "jd_intelligence",
        "tier": "B",
        "execution_responsibility": "job description intelligence extraction",
        "input_classification": "sanitized_job_description",
        "output_classification": "structured_jd_signals",
        "schema_strictness": "strict_json_schema",
        "latency_sensitivity": "medium",
        "quality_sensitivity": "high",
        "hallucination_risk": "high",
        "privacy_sensitivity": "medium",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory",
        "fallback_eligible": True,
        "failure_disposition": "use_deterministic_fallback",
        "human_review_required": True,
    },
    {
        "workload_id": "grounded_rag_answer",
        "tier": "B",
        "execution_responsibility": "grounded job corpus question answering",
        "input_classification": "sanitized_question_and_bounded_sources",
        "output_classification": "grounded_answer_with_source_ids",
        "schema_strictness": "validated_json_object",
        "latency_sensitivity": "high",
        "quality_sensitivity": "high",
        "hallucination_risk": "critical",
        "privacy_sensitivity": "medium",
        "cacheability": False,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory",
        "fallback_eligible": True,
        "failure_disposition": "return_insufficient_evidence",
        "human_review_required": False,
    },
    {
        "workload_id": "resume_fallback_ranking",
        "tier": "B",
        "execution_responsibility": "resume fallback ranking",
        "input_classification": "sanitized_resume_evidence_and_job_signals",
        "output_classification": "advisory_resume_ranking",
        "schema_strictness": "strict_json_schema",
        "latency_sensitivity": "medium",
        "quality_sensitivity": "critical",
        "hallucination_risk": "critical",
        "privacy_sensitivity": "critical",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory_only",
        "fallback_eligible": False,
        "failure_disposition": "skip_and_require_human_review",
        "human_review_required": True,
    },
    {
        "workload_id": "ambiguous_resume_adjudication",
        "tier": "B",
        "execution_responsibility": "ambiguous resume adjudication",
        "input_classification": "sanitized_ranked_resume_evidence",
        "output_classification": "advisory_adjudication",
        "schema_strictness": "strict_json_schema",
        "latency_sensitivity": "medium",
        "quality_sensitivity": "critical",
        "hallucination_risk": "critical",
        "privacy_sensitivity": "critical",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory_only",
        "fallback_eligible": False,
        "failure_disposition": "preserve_deterministic_result",
        "human_review_required": True,
    },
    {
        "workload_id": "critic_evaluation",
        "tier": "B",
        "execution_responsibility": "critic evaluation of evidence support",
        "input_classification": "sanitized_suggestion_and_evidence",
        "output_classification": "advisory_critic_decision",
        "schema_strictness": "strict_json_schema",
        "latency_sensitivity": "medium",
        "quality_sensitivity": "critical",
        "hallucination_risk": "high",
        "privacy_sensitivity": "high",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory_only",
        "fallback_eligible": True,
        "failure_disposition": "reject_or_downgrade_to_guidance",
        "human_review_required": True,
    },
    {
        "workload_id": "tailoring_generation",
        "tier": "C",
        "execution_responsibility": "evidence-grounded tailoring generation",
        "input_classification": "sanitized_resume_and_job_evidence",
        "output_classification": "manual_review_tailoring_suggestions",
        "schema_strictness": "strict_json_schema",
        "latency_sensitivity": "low",
        "quality_sensitivity": "critical",
        "hallucination_risk": "critical",
        "privacy_sensitivity": "critical",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "manual_only",
        "fallback_eligible": True,
        "failure_disposition": "do_not_generate",
        "human_review_required": True,
    },
    {
        "workload_id": "tailoring_refinement",
        "tier": "C",
        "execution_responsibility": "tailoring refinement writer",
        "input_classification": "sanitized_patch_and_evidence",
        "output_classification": "manual_review_refined_patch",
        "schema_strictness": "validated_json_object",
        "latency_sensitivity": "low",
        "quality_sensitivity": "critical",
        "hallucination_risk": "critical",
        "privacy_sensitivity": "critical",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "manual_only",
        "fallback_eligible": True,
        "failure_disposition": "preserve_original_patch",
        "human_review_required": True,
    },
    {
        "workload_id": "tailoring_judge",
        "tier": "C",
        "execution_responsibility": "tailoring quality judge",
        "input_classification": "sanitized_candidate_patches_and_evidence",
        "output_classification": "advisory_patch_review",
        "schema_strictness": "validated_json_object",
        "latency_sensitivity": "low",
        "quality_sensitivity": "critical",
        "hallucination_risk": "high",
        "privacy_sensitivity": "critical",
        "cacheability": True,
        "deterministic_comparator_available": True,
        "current_authority_level": "advisory_only",
        "fallback_eligible": True,
        "failure_disposition": "keep_deterministic_candidate",
        "human_review_required": True,
    },
    {
        "workload_id": "manual_scan_phrase",
        "tier": "A",
        "execution_responsibility": "manual scan phrase generation",
        "input_classification": "sanitized_bullet_and_supported_terms",
        "output_classification": "manual_edit_phrase_options",
        "schema_strictness": "strict_json_schema",
        "latency_sensitivity": "high",
        "quality_sensitivity": "medium",
        "hallucination_risk": "high",
        "privacy_sensitivity": "high",
        "cacheability": False,
        "deterministic_comparator_available": True,
        "current_authority_level": "manual_only",
        "fallback_eligible": True,
        "failure_disposition": "return_no_live_options",
        "human_review_required": True,
    },
    {
        "workload_id": "manual_provider_preview",
        "tier": "C",
        "execution_responsibility": "manual provider preview generation",
        "input_classification": "sanitized_bounded_request_packet",
        "output_classification": "manual_review_preview",
        "schema_strictness": "strict_json_schema",
        "latency_sensitivity": "low",
        "quality_sensitivity": "critical",
        "hallucination_risk": "critical",
        "privacy_sensitivity": "critical",
        "cacheability": False,
        "deterministic_comparator_available": True,
        "current_authority_level": "manual_only",
        "fallback_eligible": False,
        "failure_disposition": "block_preview",
        "human_review_required": True,
    },
)

_CANDIDATE_DEFINITIONS = (
    {
        "candidate_id": "groq_openai_gpt_oss_20b",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "eligible_tiers": ["A", "B", "C"],
        "structured_output_required": True,
        "fallback_disabled": True,
        "explicit_provider_required": True,
        "explicit_model_required": True,
        "live_execution_default": False,
        "maximum_request_budget": 0,
        "raw_response_persistence_prohibited": True,
        "authority_transfer": False,
    },
    {
        "candidate_id": "groq_openai_gpt_oss_120b",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "eligible_tiers": ["B", "C"],
        "structured_output_required": True,
        "fallback_disabled": True,
        "explicit_provider_required": True,
        "explicit_model_required": True,
        "live_execution_default": False,
        "maximum_request_budget": 0,
        "raw_response_persistence_prohibited": True,
        "authority_transfer": False,
    },
    {
        "candidate_id": "openai_gpt_5_mini",
        "provider": "openai",
        "model": "gpt-5-mini",
        "eligible_tiers": ["A", "B", "C"],
        "structured_output_required": True,
        "fallback_disabled": True,
        "explicit_provider_required": True,
        "explicit_model_required": True,
        "live_execution_default": False,
        "maximum_request_budget": 0,
        "raw_response_persistence_prohibited": True,
        "authority_transfer": False,
    },
    {
        "candidate_id": "openai_gpt_5_1",
        "provider": "openai",
        "model": "gpt-5.1",
        "eligible_tiers": ["B", "C"],
        "structured_output_required": True,
        "fallback_disabled": True,
        "explicit_provider_required": True,
        "explicit_model_required": True,
        "live_execution_default": False,
        "maximum_request_budget": 0,
        "raw_response_persistence_prohibited": True,
        "authority_transfer": False,
    },
)

_TIER_CANDIDATES = {
    "A": ["groq_openai_gpt_oss_20b", "openai_gpt_5_mini"],
    "B": [
        "groq_openai_gpt_oss_20b",
        "groq_openai_gpt_oss_120b",
        "openai_gpt_5_mini",
        "openai_gpt_5_1",
    ],
    "C": [
        "groq_openai_gpt_oss_120b",
        "groq_openai_gpt_oss_20b",
        "openai_gpt_5_1",
        "openai_gpt_5_mini",
    ],
}

_METRIC_DEFINITIONS = tuple(
    {
        "metric_id": metric_id,
        "required": True,
        "offline_value": None,
    }
    for metric_id in METRIC_ORDER
)


def _hard_failure(
    failure_id: str,
    affected_responsibility: str,
    pass_condition: str,
    fail_condition: str,
    severity: str,
) -> Dict[str, Any]:
    return {
        "failure_id": failure_id,
        "affected_responsibility": affected_responsibility,
        "pass_condition": pass_condition,
        "fail_condition": fail_condition,
        "severity": severity,
        "execution_must_stop": True,
        "human_review_required": True,
    }


_HARD_FAILURE_DEFINITIONS = (
    _hard_failure(
        "schema_invalid_result_accepted",
        "response_validation",
        "schema-invalid results are rejected",
        "a schema-invalid result is accepted",
        "critical",
    ),
    _hard_failure(
        "unsupported_claim",
        "grounding",
        "all claims are supported by supplied evidence",
        "an unsupported claim is emitted",
        "critical",
    ),
    _hard_failure(
        "hallucination",
        "grounding",
        "no fabricated fact is emitted",
        "a fabricated fact is emitted",
        "critical",
    ),
    _hard_failure(
        "sensitive_data_leakage",
        "privacy",
        "no sensitive data leaves its authorized boundary",
        "sensitive data is exposed or transmitted",
        "critical",
    ),
    _hard_failure(
        "deterministic_authority_mutation",
        "deterministic_authority",
        "deterministic outputs remain unchanged",
        "an LLM result changes deterministic authority",
        "critical",
    ),
    _hard_failure(
        "queue_mutation",
        "queue",
        "queue state remains unchanged",
        "queue state changes",
        "critical",
    ),
    _hard_failure(
        "ranking_mutation",
        "ranking",
        "authoritative ranking remains unchanged",
        "authoritative ranking changes",
        "critical",
    ),
    _hard_failure(
        "selected_resume_mutation",
        "selected_resume",
        "authoritative selected resume remains unchanged",
        "authoritative selected resume changes",
        "critical",
    ),
    _hard_failure(
        "provider_called_while_disabled",
        "provider_activation",
        "disabled execution makes zero provider calls",
        "a provider is called while disabled",
        "critical",
    ),
    _hard_failure(
        "silent_cross_provider_fallback",
        "provider_routing",
        "benchmark fallback remains disabled",
        "another provider is contacted silently",
        "critical",
    ),
    _hard_failure(
        "unbounded_retry",
        "retry_control",
        "retry count remains within an explicit bound",
        "retry behavior is missing a bound",
        "critical",
    ),
    _hard_failure(
        "missing_provider_observability",
        "observability",
        "requested and used provider identifiers are recorded",
        "provider identity is missing",
        "high",
    ),
    _hard_failure(
        "missing_model_observability",
        "observability",
        "requested and used model identifiers are recorded",
        "model identity is missing",
        "high",
    ),
    _hard_failure(
        "missing_latency_observability",
        "observability",
        "bounded latency is recorded",
        "latency is missing",
        "high",
    ),
    _hard_failure(
        "missing_token_observability",
        "observability",
        "input and output token counts are recorded",
        "token observability is missing",
        "high",
    ),
    _hard_failure(
        "persisted_raw_response",
        "privacy",
        "raw provider responses are not persisted",
        "a raw provider response is persisted",
        "critical",
    ),
    _hard_failure(
        "application_action_reached",
        "application_actions",
        "application action count remains zero",
        "an application action is reached",
        "critical",
    ),
    _hard_failure(
        "ats_action_reached",
        "ats_actions",
        "ATS action count remains zero",
        "an ATS action is reached",
        "critical",
    ),
)

_SAFETY_INVARIANTS = {
    "prefilter_relevance_owner": "deterministic",
    "llm_evaluation_owner": "advisory_or_manual_only",
    "final_application_scoring_owner": "deterministic",
    "queue_owner": "deterministic",
    "ranking_owner": "deterministic",
    "selected_resume_owner": "deterministic",
    "graph_verification_mode": "comparison_only",
    "application_action_authority": False,
    "ats_authority": False,
    "automatic_mutation_authority": False,
    "credential_driven_activation": False,
    "automatic_fallback_during_benchmark": False,
    "live_execution_default": False,
}

_BENCHMARK_CONTROLS = {
    "execution_mode": "offline_contract_only",
    "live_execution_enabled": False,
    "maximum_request_budget": 0,
    "automatic_fallback_enabled": False,
    "provider_client_allowed": False,
    "network_allowed": False,
    "credential_read_allowed": False,
    "database_allowed": False,
    "subprocess_allowed": False,
    "thread_creation_allowed": False,
    "artifact_write_allowed": False,
    "raw_response_persistence_allowed": False,
    "model_winner_selection_allowed": False,
    "authority_transfer_allowed": False,
}

_REQUIRED_WORKLOAD_FIELDS = {
    "workload_id",
    "tier",
    "execution_responsibility",
    "input_classification",
    "output_classification",
    "schema_strictness",
    "latency_sensitivity",
    "quality_sensitivity",
    "hallucination_risk",
    "privacy_sensitivity",
    "cacheability",
    "deterministic_comparator_available",
    "current_authority_level",
    "fallback_eligible",
    "failure_disposition",
    "human_review_required",
}
_REQUIRED_FIXTURE_FIELDS = {
    "fixture_id",
    "workload_id",
    "source_path",
    "sanitized_classification",
    "live_transmission_eligible",
    "contains_personal_resume_content",
    "additional_redaction_required",
    "deterministic_invariant_available",
    "golden_output_available",
    "schema_expected",
    "offline_only",
}
_FORBIDDEN_FIXTURE_PATHS = {
    "skill_eval.txt",
}
_FORBIDDEN_FIXTURE_PREFIXES = (
    "outputs/",
    "data/",
)
_FORBIDDEN_WINNER_FIELDS = {
    "selected_winner",
    "selected_model",
    "winner_model",
    "winning_model",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _has_forbidden_winner_field(value: Any) -> bool:
    if isinstance(value, dict):
        if _FORBIDDEN_WINNER_FIELDS.intersection(value):
            return True
        return any(_has_forbidden_winner_field(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_forbidden_winner_field(item) for item in value)
    return False


def _validate_fixture_source_path(source_path: Any) -> None:
    text = str(source_path or "")
    path = PurePosixPath(text)
    _require(bool(text), "fixture source_path is required")
    _require(not path.is_absolute(), "absolute fixture paths are prohibited")
    _require(".." not in path.parts, "fixture paths outside the repository are prohibited")
    _require(text not in _FORBIDDEN_FIXTURE_PATHS, "unsafe fixture path is prohibited")
    _require(
        not any(text.startswith(prefix) for prefix in _FORBIDDEN_FIXTURE_PREFIXES),
        "runtime, archive, and production-data fixture paths are prohibited",
    )
    _require(text.startswith("tests/"), "fixture source_path must be test-owned")


def validate_fixture_manifest(manifest: Dict[str, Any]) -> bool:
    """Validate references only; fixture contents are never copied or transmitted."""

    _require(isinstance(manifest, dict), "fixture manifest must be an object")
    _require(
        manifest.get("manifest_version") == FIXTURE_MANIFEST_VERSION,
        "fixture manifest version mismatch",
    )
    entries = manifest.get("fixtures")
    _require(isinstance(entries, list) and bool(entries), "fixture manifest must be nonempty")

    fixture_ids: List[str] = []
    workload_ids: List[str] = []
    for entry in entries:
        _require(isinstance(entry, dict), "fixture entry must be an object")
        _require(
            _REQUIRED_FIXTURE_FIELDS.issubset(entry),
            "fixture entry is missing required fields",
        )
        fixture_id = str(entry.get("fixture_id") or "")
        workload_id = str(entry.get("workload_id") or "")
        _require(bool(fixture_id), "fixture_id is required")
        _require(workload_id in WORKLOAD_ORDER, "fixture workload is unsupported")
        _validate_fixture_source_path(entry.get("source_path"))
        _require(
            entry.get("sanitized_classification")
            in {"synthetic_sanitized", "repository_sanitized"},
            "fixture sanitized classification is invalid",
        )
        _require(
            entry.get("live_transmission_eligible") is False,
            "live fixture transmission is prohibited",
        )
        _require(
            entry.get("contains_personal_resume_content") is False,
            "personal resume content is prohibited",
        )
        _require(entry.get("offline_only") is True, "fixture must remain offline-only")
        for field in (
            "additional_redaction_required",
            "deterministic_invariant_available",
            "golden_output_available",
            "schema_expected",
        ):
            _require(isinstance(entry.get(field), bool), f"fixture {field} must be boolean")
        serialized_entry = json.dumps(entry, sort_keys=True).lower()
        _require("credential" not in serialized_entry, "credential fixture references are prohibited")
        _require("raw_provider_response" not in serialized_entry, "raw responses are prohibited")
        fixture_ids.append(fixture_id)
        workload_ids.append(workload_id)

    _require(len(fixture_ids) == len(set(fixture_ids)), "duplicate fixture definitions")
    _require(
        tuple(workload_ids) == WORKLOAD_ORDER,
        "fixture workload order or coverage mismatch",
    )
    return True


def load_provider_benchmark_fixture_manifest(
    path: str | Path | None = None,
) -> Dict[str, Any]:
    """Load one explicit local manifest without executing any referenced fixture."""

    manifest_path = Path(path) if path is not None else DEFAULT_FIXTURE_MANIFEST_PATH
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_fixture_manifest(payload)
    return deepcopy(payload)


def _candidate_matrix() -> List[Dict[str, Any]]:
    return [
        {
            "workload_id": workload["workload_id"],
            "tier": workload["tier"],
            "candidate_ids": list(_TIER_CANDIDATES[workload["tier"]]),
        }
        for workload in _WORKLOAD_DEFINITIONS
    ]


def build_provider_benchmark_contract(
    fixture_manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a fresh deterministic contract with zero execution authority."""

    manifest = (
        load_provider_benchmark_fixture_manifest()
        if fixture_manifest is None
        else deepcopy(fixture_manifest)
    )
    validate_fixture_manifest(manifest)
    contract = {
        "contract_version": CONTRACT_VERSION,
        "contract_kind": "offline_provider_benchmark_definition",
        "provider_order": list(PROVIDER_ORDER),
        "workload_order": list(WORKLOAD_ORDER),
        "workloads": deepcopy(list(_WORKLOAD_DEFINITIONS)),
        "candidate_definitions": deepcopy(list(_CANDIDATE_DEFINITIONS)),
        "candidate_matrix": _candidate_matrix(),
        "metric_order": list(METRIC_ORDER),
        "metric_definitions": deepcopy(list(_METRIC_DEFINITIONS)),
        "hard_failure_order": list(HARD_FAILURE_ORDER),
        "hard_failure_gates": deepcopy(list(_HARD_FAILURE_DEFINITIONS)),
        "fixture_manifest": manifest,
        "safety_invariants": deepcopy(_SAFETY_INVARIANTS),
        "benchmark_controls": deepcopy(_BENCHMARK_CONTROLS),
    }
    validate_provider_benchmark_contract(contract)
    return deepcopy(contract)


def validate_provider_benchmark_contract(contract: Dict[str, Any]) -> bool:
    """Fail closed on routing, authority, fixture, or determinism violations."""

    _require(isinstance(contract, dict), "benchmark contract must be an object")
    _require(contract.get("contract_version") == CONTRACT_VERSION, "contract version mismatch")
    _require(
        contract.get("provider_order") == list(PROVIDER_ORDER),
        "benchmark providers must be exactly groq and openai",
    )
    _require(not _has_forbidden_winner_field(contract), "model winner selection is prohibited")

    workloads = contract.get("workloads")
    _require(isinstance(workloads, list) and bool(workloads), "workloads must be nonempty")
    workload_ids = [str(row.get("workload_id") or "") for row in workloads if isinstance(row, dict)]
    _require(tuple(workload_ids) == WORKLOAD_ORDER, "workload order or coverage mismatch")
    _require(len(workload_ids) == len(set(workload_ids)), "duplicate workload definitions")
    for workload in workloads:
        _require(isinstance(workload, dict), "workload definition must be an object")
        _require(_REQUIRED_WORKLOAD_FIELDS.issubset(workload), "workload fields are incomplete")
        _require(workload.get("tier") in {"A", "B", "C"}, "unsupported workload tier")

    candidates = contract.get("candidate_definitions")
    _require(isinstance(candidates, list) and bool(candidates), "candidate definitions are required")
    candidate_ids: List[str] = []
    candidate_pairs: List[tuple[str, str]] = []
    candidate_by_id: Dict[str, Dict[str, Any]] = {}
    for candidate in candidates:
        _require(isinstance(candidate, dict), "candidate definition must be an object")
        candidate_id = str(candidate.get("candidate_id") or "")
        provider = str(candidate.get("provider") or "")
        model = str(candidate.get("model") or "")
        _require(provider in PROVIDER_ORDER, "unsupported benchmark provider")
        _require(model in MODEL_PROVIDER, "unsupported benchmark model")
        _require(MODEL_PROVIDER[model] == provider, "provider/model mismatch")
        _require(candidate.get("fallback_disabled") is True, "benchmark fallback must be disabled")
        _require(candidate.get("explicit_provider_required") is True, "explicit provider is required")
        _require(candidate.get("explicit_model_required") is True, "explicit model is required")
        _require(candidate.get("live_execution_default") is False, "live execution must default off")
        _require(candidate.get("maximum_request_budget") == 0, "offline request budget must be zero")
        _require(
            candidate.get("raw_response_persistence_prohibited") is True,
            "raw response persistence must be prohibited",
        )
        _require(candidate.get("authority_transfer") is False, "authority transfer is prohibited")
        candidate_ids.append(candidate_id)
        candidate_pairs.append((provider, model))
        candidate_by_id[candidate_id] = candidate

    _require(len(candidate_ids) == len(set(candidate_ids)), "duplicate candidate definitions")
    _require(len(candidate_pairs) == len(set(candidate_pairs)), "duplicate provider/model candidates")
    _require(tuple(candidate_pairs) == MODEL_ORDER, "benchmark model candidates are not exact")

    matrix = contract.get("candidate_matrix")
    _require(isinstance(matrix, list) and bool(matrix), "candidate matrix must be nonempty")
    matrix_ids = [str(row.get("workload_id") or "") for row in matrix if isinstance(row, dict)]
    _require(tuple(matrix_ids) == WORKLOAD_ORDER, "candidate matrix workload coverage mismatch")
    for row in matrix:
        _require(isinstance(row, dict), "candidate matrix row must be an object")
        row_candidates = row.get("candidate_ids")
        _require(
            isinstance(row_candidates, list) and bool(row_candidates),
            "every workload must have at least one candidate",
        )
        _require(
            len(row_candidates) == len(set(row_candidates)),
            "candidate matrix contains duplicates",
        )
        tier = str(row.get("tier") or "")
        _require(
            row_candidates == _TIER_CANDIDATES.get(tier),
            "candidate matrix tier definition mismatch",
        )
        for candidate_id in row_candidates:
            _require(candidate_id in candidate_by_id, "candidate matrix references an unknown candidate")
            _require(
                tier in candidate_by_id[candidate_id].get("eligible_tiers", []),
                "candidate is ineligible for workload tier",
            )

    _require(contract.get("metric_order") == list(METRIC_ORDER), "metric set or order mismatch")
    metric_definitions = contract.get("metric_definitions")
    _require(isinstance(metric_definitions, list), "metric definitions are required")
    _require(
        [row.get("metric_id") for row in metric_definitions] == list(METRIC_ORDER),
        "metric definitions are incomplete",
    )

    _require(
        contract.get("hard_failure_order") == list(HARD_FAILURE_ORDER),
        "hard-failure set or order mismatch",
    )
    hard_gates = contract.get("hard_failure_gates")
    _require(isinstance(hard_gates, list), "hard-failure gates are required")
    _require(
        [row.get("failure_id") for row in hard_gates] == list(HARD_FAILURE_ORDER),
        "hard-failure gates are incomplete",
    )
    for gate in hard_gates:
        _require(gate.get("execution_must_stop") is True, "hard failure must stop execution")
        _require(gate.get("human_review_required") is True, "hard failure requires human review")
        for field in (
            "affected_responsibility",
            "pass_condition",
            "fail_condition",
            "severity",
        ):
            _require(bool(str(gate.get(field) or "")), f"hard failure {field} is required")

    invariants = contract.get("safety_invariants")
    _require(invariants == _SAFETY_INVARIANTS, "authority or safety invariants changed")
    controls = contract.get("benchmark_controls")
    _require(controls == _BENCHMARK_CONTROLS, "offline benchmark controls changed")
    validate_fixture_manifest(contract.get("fixture_manifest"))
    return True


def serialize_provider_benchmark_contract(contract: Dict[str, Any] | None = None) -> str:
    """Return canonical UTF-8-compatible JSON without timestamps or host paths."""

    payload = build_provider_benchmark_contract() if contract is None else deepcopy(contract)
    validate_provider_benchmark_contract(payload)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def provider_benchmark_contract_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    """Return the SHA-256 digest of the canonical contract representation."""

    serialized = serialize_provider_benchmark_contract(contract)
    return sha256(serialized.encode("utf-8")).hexdigest()

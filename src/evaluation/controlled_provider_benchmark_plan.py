"""Default-off plan and transmission review for a future provider benchmark.

The owner is evaluation infrastructure only.  It performs no provider import,
credential read, network call, execution, persistence, or production mutation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from src.evaluation.provider_benchmark_contract import (
    CONTRACT_VERSION as STEP8L_CONTRACT_VERSION,
    MODEL_ORDER,
    WORKLOAD_ORDER,
    build_provider_benchmark_contract,
    provider_benchmark_contract_sha256,
)
from src.evaluation.provider_fixture_benchmark import (
    CASE_CORPUS_VERSION,
    FIXTURE_BENCHMARK_VERSION,
    build_provider_fixture_benchmark_contract,
    fixture_case_corpus_sha256,
    load_fixture_case_corpus,
    provider_fixture_benchmark_sha256,
)


CONTROLLED_PLAN_VERSION = "controlled-provider-benchmark-plan-v1"
RUN_PLAN_FIXTURE_VERSION = (
    "controlled-provider-benchmark-run-plan-fixture-v1"
)
AUTHORIZATION_VERSION = "controlled-provider-benchmark-authorization-v1"
DEFAULT_RUN_PLAN_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "provider_benchmark"
    / "run_plan.json"
)

STEP8L_CONTRACT_SOURCE = "src/evaluation/provider_benchmark_contract.py"
STEP8O_CASE_SOURCE = "tests/fixtures/provider_benchmark/cases.json"
STEP8O_ENGINE_SOURCE = "src/evaluation/provider_fixture_benchmark.py"
RUN_PLAN_FIXTURE_SOURCE = "tests/fixtures/provider_benchmark/run_plan.json"

_REQUEST_PACKET_FIELDS = {
    "benchmark_contract_version",
    "run_plan_version",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "synthetic_input",
    "output_schema",
    "temperature",
    "maximum_completion_tokens",
    "timeout_seconds",
    "fallback",
    "live_execution_requested",
}
_RESULT_PACKET_FIELDS = {
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "normalized_output",
    "schema_valid",
    "normalization_succeeded",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "observed_cost",
    "provider_outcome_category",
    "fallback_used",
    "retry_count",
    "redaction_status",
    "hard_failure_status",
}
_PROHIBITED_PACKET_KEY_PARTS = {
    "application_state",
    "ats",
    "credential",
    "database",
    "environment",
    "expected",
    "golden",
    "grader",
    "header",
    "owner_id",
    "prompt",
    "provenance",
    "raw_provider",
    "raw_response",
    "reasoning",
    "repository_path",
    "request_id",
    "request_payload",
    "resume_content",
    "run_id",
    "secret",
    "threshold",
    "tool_output",
    "transport_log",
    "user_name",
}
_PERSONAL_KEY_PARTS = {
    "person_name",
    "user_name",
    "email",
    "phone",
    "address",
}
_RUNTIME_KEY_PARTS = {
    "runtime_record",
    "production_run",
    "owner_id",
    "request_id",
    "database",
}
_EMPLOYER_KEY_PARTS = {"company", "employer"}
_RESUME_TEXT_KEY_PARTS = {
    "resume_text",
    "resume_content",
    "source_resume",
}
_PRIVATE_JOB_TEXT_KEY_PARTS = {
    "job_description",
    "private_job",
    "raw_jd",
}
_INTERNAL_PATH_KEY_PARTS = {
    "absolute_path",
    "artifact_path",
    "repository_path",
    "source_path",
}
_APPLICATION_STATE_KEY_PARTS = {
    "application_status",
    "queue_state",
    "ats_state",
    "approval_state",
}
_CREDENTIAL_KEY_PARTS = {
    "api_key",
    "credential",
    "database_url",
    "password",
    "secret",
    "token_value",
}

_STOP_CONDITIONS = (
    "provider_model_mismatch",
    "unapproved_case",
    "unapproved_model",
    "fallback_attempted",
    "retry_attempted",
    "request_budget_exceeded",
    "input_token_budget_exceeded",
    "output_token_budget_exceeded",
    "cost_ceiling_exceeded",
    "raw_response_persistence",
    "sensitive_information_detected",
    "schema_invalid_response_accepted",
    "unsupported_claim",
    "hallucination",
    "deterministic_authority_mutation",
    "application_or_ats_reach",
    "unknown_provider_error",
    "missing_usage_metadata",
    "duplicate_call_uncertainty",
    "ambiguous_timeout",
)


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


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_key(value: Any) -> str:
    return _clean_text(value).lower().replace("-", "_").replace(" ", "_")


def _iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield _normalized_key(key)
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, str):
        yield value


def _has_key_part(value: Any, parts: set[str]) -> bool:
    return any(
        any(part in key for part in parts)
        for key in _iter_keys(value)
    )


def _has_internal_path_value(value: Any) -> bool:
    for item in _iter_strings(value):
        normalized = item.replace("\\", "/").lower()
        if (
            normalized.startswith("/")
            or normalized.startswith("../")
            or "/../" in normalized
            or normalized.startswith("outputs/")
            or normalized.startswith("data/")
            or "/users/" in normalized
        ):
            return True
    return False


def _has_unsupported_free_text(value: Any) -> bool:
    return any(
        "\n" in item or len(item) > 160
        for item in _iter_strings(value)
    )


def _has_prohibited_packet_key(value: Any) -> bool:
    return _has_key_part(value, _PROHIBITED_PACKET_KEY_PARTS)


def _parse_utc(value: Any) -> datetime:
    text = _clean_text(value)
    _require(bool(text), "authorization validity timestamp is required")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("authorization validity timestamp is malformed") from exc
    _require(
        parsed.tzinfo is not None,
        "authorization validity timestamp must include timezone",
    )
    return parsed.astimezone(timezone.utc)


def _case_alias(case_id: str, corpus_sha256: str) -> str:
    material = (
        f"{CONTROLLED_PLAN_VERSION}:{corpus_sha256}:{case_id}"
    ).encode("utf-8")
    return f"case_{sha256(material).hexdigest()[:24]}"


def validate_run_plan_fixture(fixture: Dict[str, Any]) -> bool:
    _require(isinstance(fixture, dict), "run plan fixture must be an object")
    _require(
        fixture.get("fixture_version") == RUN_PLAN_FIXTURE_VERSION,
        "run plan fixture version mismatch",
    )
    request = fixture.get("request_limits")
    duration = fixture.get("duration_limits")
    token = fixture.get("token_budget_policy")
    cost = fixture.get("cost_budget_schema")
    retention = fixture.get("artifact_retention_policy")
    _require(isinstance(request, dict), "request limits are required")
    _require(isinstance(duration, dict), "duration limits are required")
    _require(isinstance(token, dict), "token budget policy is required")
    _require(isinstance(cost, dict), "cost budget schema is required")
    _require(
        isinstance(retention, dict),
        "artifact retention policy is required",
    )
    for field in (
        "timeout_seconds",
        "maximum_input_tokens_per_request",
        "maximum_completion_tokens_per_request",
        "maximum_requests_per_case",
    ):
        _require(
            isinstance(request.get(field), int)
            and not isinstance(request.get(field), bool)
            and request[field] > 0,
            f"{field} must be a positive integer",
        )
    _require(request.get("temperature") == 0, "temperature must be zero")
    _require(
        request.get("harness_retry_limit") == 0,
        "benchmark harness retries must be zero",
    )
    _require(
        request.get("serial_execution_required") is True
        and request.get("parallel_execution_allowed") is False
        and request.get("ambiguous_timeout_retry_allowed") is False
        and request.get("recursive_execution_allowed") is False,
        "request execution must be serial, nonrecursive, and no-retry",
    )
    _require(
        isinstance(duration.get("maximum_run_duration_seconds"), int)
        and duration["maximum_run_duration_seconds"] > 0,
        "maximum run duration is required",
    )
    provider_durations = duration.get("maximum_provider_duration_seconds")
    _require(
        isinstance(provider_durations, dict)
        and set(provider_durations) == {"groq", "openai"}
        and all(
            isinstance(value, int) and value > 0
            for value in provider_durations.values()
        ),
        "per-provider duration limits are required",
    )
    _require(
        all(value is True for value in token.values()),
        "token budget policy must fail closed",
    )
    for field in (
        "pricing_table_version_required",
        "operator_approved_pricing_table_required",
        "maximum_observed_cost_per_model_required",
        "maximum_total_observed_cost_required",
        "positive_dollar_ceiling_required",
        "missing_cost_blocks_comparison",
        "stop_on_cost_ceiling_exceeded",
    ):
        _require(cost.get(field) is True, f"{field} must be required")
    _require(cost.get("currency") == "USD", "cost currency must be explicit")
    _require(
        retention.get("automatic_persistence") is False
        and retention.get("ignored_artifact_only") is True
        and retention.get("normalized_output_only") is True
        and retention.get("raw_sdk_object_allowed") is False
        and retention.get("raw_response_envelope_allowed") is False
        and retention.get("provider_request_id_allowed") is False
        and retention.get("reasoning_trace_allowed") is False
        and retention.get("required_file_mode") == "0600"
        and isinstance(retention.get("maximum_retention_days"), int)
        and retention["maximum_retention_days"] > 0
        and retention.get("operator_review_required_before_deletion") is True
        and retention.get("delete_after_review") is True,
        "artifact retention policy is unsafe",
    )
    return True


def load_run_plan_fixture(
    path: str | Path | None = None,
) -> Dict[str, Any]:
    fixture_path = (
        Path(path) if path is not None else DEFAULT_RUN_PLAN_FIXTURE_PATH
    )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    validate_run_plan_fixture(payload)
    return deepcopy(payload)


def build_transmission_review(
    corpus: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Review every case without exposing its input, golden, or provenance."""

    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    corpus_digest = fixture_case_corpus_sha256(payload)
    reviews = []
    for case in payload["cases"]:
        input_packet = case["normalized_input_packet"]
        wholly_synthetic = (
            case.get("sanitized_classification") == "synthetic_sanitized"
        )
        flags = {
            "contains_personal_data": (
                case.get("contains_personal_resume_content") is not False
                or _has_key_part(input_packet, _PERSONAL_KEY_PARTS)
            ),
            "contains_runtime_derived_data": _has_key_part(
                input_packet, _RUNTIME_KEY_PARTS
            ),
            "contains_employer_or_company_identity": _has_key_part(
                input_packet, _EMPLOYER_KEY_PARTS
            ),
            "contains_person_name": _has_key_part(
                input_packet, {"person_name", "user_name"}
            ),
            "contains_resume_derived_text": _has_key_part(
                input_packet, _RESUME_TEXT_KEY_PARTS
            ),
            "contains_private_job_description_text": _has_key_part(
                input_packet, _PRIVATE_JOB_TEXT_KEY_PARTS
            ),
            "contains_credentials_or_secrets": _has_key_part(
                input_packet, _CREDENTIAL_KEY_PARTS
            ),
            "contains_internal_paths": (
                _has_key_part(input_packet, _INTERNAL_PATH_KEY_PARTS)
                or _has_internal_path_value(input_packet)
            ),
            "contains_request_identifiers": _has_key_part(
                input_packet, {"request_id", "run_id", "owner_id"}
            ),
            "contains_database_information": _has_key_part(
                input_packet, {"database", "sql", "connection_string"}
            ),
            "contains_proprietary_application_state": _has_key_part(
                input_packet, _APPLICATION_STATE_KEY_PARTS
            ),
            "contains_unsupported_free_form_text": _has_unsupported_free_text(
                input_packet
            ),
        }
        reasons = [
            name
            for name, present in flags.items()
            if present
        ]
        if _has_key_part(
            input_packet,
            {"expected", "golden", "grader", "threshold"},
        ):
            reasons.append("contains_local_only_expected_or_grader_material")
        if not wholly_synthetic:
            reasons.append("classification_not_wholly_synthetic")
        if case.get("additional_redaction_required") is True:
            reasons.append("case_requires_additional_redaction")
        eligible = not reasons
        reviews.append(
            {
                "case_alias": _case_alias(case["case_id"], corpus_digest),
                "workload_id": case["workload_id"],
                "wholly_synthetic": wholly_synthetic,
                **flags,
                "requires_additional_redaction": (
                    not wholly_synthetic
                    or case.get("additional_redaction_required") is True
                    or any(flags.values())
                ),
                "eligible_for_later_controlled_transmission": eligible,
                "human_approval_required": True,
                "eligibility_reasons": sorted(reasons),
            }
        )
    return deepcopy(reviews)


def _eligible_alias_to_case(
    corpus: Dict[str, Any] | None = None,
) -> Dict[str, Dict[str, Any]]:
    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    reviews = build_transmission_review(payload)
    corpus_digest = fixture_case_corpus_sha256(payload)
    by_alias = {}
    review_by_alias = {row["case_alias"]: row for row in reviews}
    for case in payload["cases"]:
        alias = _case_alias(case["case_id"], corpus_digest)
        if review_by_alias[alias][
            "eligible_for_later_controlled_transmission"
        ]:
            by_alias[alias] = case
    return by_alias


def _workload_definitions() -> Dict[str, Dict[str, Any]]:
    benchmark = build_provider_benchmark_contract()
    return {
        row["workload_id"]: row
        for row in benchmark["workloads"]
    }


def build_staged_benchmark_matrix(
    corpus: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Build a serial, bounded proposal without authorizing execution."""

    reviews = build_transmission_review(corpus)
    workloads = _workload_definitions()
    workload_index = {
        workload_id: index
        for index, workload_id in enumerate(WORKLOAD_ORDER)
    }
    entries = []
    for review in reviews:
        if not review["eligible_for_later_controlled_transmission"]:
            continue
        workload_id = review["workload_id"]
        workload = workloads[workload_id]
        tier = workload["tier"]
        alias = review["case_alias"]
        stage_a_pairs: List[tuple[str, str, str]] = []
        stage_b_pairs: List[tuple[str, str, str]] = []
        if tier == "A":
            stage_a_pairs.append(
                ("groq", "openai/gpt-oss-20b", "tier_a_quality_floor")
            )
            stage_b_pairs.append(
                ("openai", "gpt-5-mini", "tier_a_secondary_comparison")
            )
        elif tier == "B":
            stage_a_pairs.extend(
                [
                    (
                        "groq",
                        "openai/gpt-oss-20b",
                        "tier_b_quality_floor",
                    ),
                    (
                        "groq",
                        "openai/gpt-oss-120b",
                        "tier_b_quality_ceiling",
                    ),
                ]
            )
            if (
                workload["quality_sensitivity"] == "critical"
                or workload["hallucination_risk"] == "critical"
            ):
                stage_b_pairs.append(
                    (
                        "openai",
                        "gpt-5-mini",
                        "critical_tier_b_secondary_comparison",
                    )
                )
        else:
            stage_a_pairs.extend(
                [
                    (
                        "groq",
                        "openai/gpt-oss-120b",
                        "tier_c_quality_floor",
                    ),
                    (
                        "groq",
                        "openai/gpt-oss-20b",
                        "tier_c_explicit_cost_baseline",
                    ),
                ]
            )
        for stage, pairs in (("A", stage_a_pairs), ("B", stage_b_pairs)):
            for local_order, (provider, model, reason) in enumerate(pairs):
                entries.append(
                    {
                        "stage": stage,
                        "case_alias": alias,
                        "workload_id": workload_id,
                        "tier": tier,
                        "provider": provider,
                        "model": model,
                        "planning_reason": reason,
                        "fallback": False,
                        "harness_retry_limit": 0,
                        "live_execution_authorized": False,
                        "_sort": (
                            0 if stage == "A" else 1,
                            workload_index[workload_id],
                            local_order,
                        ),
                    }
                )
    entries.sort(key=lambda row: row["_sort"])
    for execution_order, row in enumerate(entries, start=1):
        row.pop("_sort")
        row["execution_order"] = execution_order
    return deepcopy(entries)


def _request_counts(
    matrix: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    by_provider = {
        provider: sum(
            1 for row in matrix if row["provider"] == provider
        )
        for provider in ("groq", "openai")
    }
    by_model = {
        f"{provider}/{model}": sum(
            1
            for row in matrix
            if row["provider"] == provider and row["model"] == model
        )
        for provider, model in MODEL_ORDER
    }
    by_workload = {
        workload_id: sum(
            1 for row in matrix if row["workload_id"] == workload_id
        )
        for workload_id in WORKLOAD_ORDER
    }
    by_case: Dict[str, int] = {}
    for row in matrix:
        by_case[row["case_alias"]] = by_case.get(row["case_alias"], 0) + 1
    return {
        "by_provider": by_provider,
        "by_model": by_model,
        "by_workload": by_workload,
        "maximum_total_requests": len(matrix),
        "maximum_requests_per_model": deepcopy(by_model),
        "maximum_requests_per_case": max(by_case.values(), default=0),
    }


def build_controlled_provider_benchmark_plan(
    *,
    corpus: Dict[str, Any] | None = None,
    run_plan_fixture: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a deterministic plan with no live execution authority."""

    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    fixture = (
        load_run_plan_fixture()
        if run_plan_fixture is None
        else deepcopy(run_plan_fixture)
    )
    validate_run_plan_fixture(fixture)
    benchmark = build_provider_benchmark_contract()
    reviews = build_transmission_review(payload)
    matrix = build_staged_benchmark_matrix(payload)
    counts = _request_counts(matrix)
    request_limits = fixture["request_limits"]
    maximum_total_requests = counts["maximum_total_requests"]
    token_budgets = {
        "maximum_input_tokens_per_request": request_limits[
            "maximum_input_tokens_per_request"
        ],
        "maximum_output_tokens_per_request": request_limits[
            "maximum_completion_tokens_per_request"
        ],
        "maximum_total_observed_input_tokens": (
            maximum_total_requests
            * request_limits["maximum_input_tokens_per_request"]
        ),
        "maximum_total_observed_output_tokens": (
            maximum_total_requests
            * request_limits["maximum_completion_tokens_per_request"]
        ),
        "observed_input_tokens_required": True,
        "observed_output_tokens_required": True,
        "missing_usage_blocks_cost_comparison": True,
    }
    candidate_pairs = [
        {
            "provider": row["provider"],
            "model": row["model"],
        }
        for row in benchmark["candidate_definitions"]
    ]
    plan = {
        "plan_version": CONTROLLED_PLAN_VERSION,
        "plan_kind": "default_off_controlled_live_benchmark_plan",
        "step8l_contract_source": STEP8L_CONTRACT_SOURCE,
        "step8l_contract_version": STEP8L_CONTRACT_VERSION,
        "step8l_contract_sha256": provider_benchmark_contract_sha256(
            benchmark
        ),
        "step8o_engine_source": STEP8O_ENGINE_SOURCE,
        "step8o_case_source": STEP8O_CASE_SOURCE,
        "step8o_contract_version": FIXTURE_BENCHMARK_VERSION,
        "step8o_case_corpus_version": CASE_CORPUS_VERSION,
        "step8o_case_corpus_sha256": fixture_case_corpus_sha256(payload),
        "step8o_engine_sha256": provider_fixture_benchmark_sha256(
            build_provider_fixture_benchmark_contract(payload)
        ),
        "run_plan_fixture_source": RUN_PLAN_FIXTURE_SOURCE,
        "run_plan_fixture_version": fixture["fixture_version"],
        "candidate_definitions": candidate_pairs,
        "workload_order": list(WORKLOAD_ORDER),
        "case_count": len(payload["cases"]),
        "transmission_review": reviews,
        "transmission_review_summary": {
            "reviewed_case_count": len(reviews),
            "eligible_case_count": sum(
                1
                for row in reviews
                if row["eligible_for_later_controlled_transmission"]
            ),
            "ineligible_case_count": sum(
                1
                for row in reviews
                if not row["eligible_for_later_controlled_transmission"]
            ),
        },
        "request_packet_schema": {
            "allowlisted_fields": sorted(_REQUEST_PACKET_FIELDS),
            "prohibited_field_parts": sorted(
                _PROHIBITED_PACKET_KEY_PARTS
            ),
            "local_alias_required": True,
            "goldens_local_only": True,
            "provenance_local_only": True,
            "live_execution_requested": False,
        },
        "staged_matrix": matrix,
        "conditional_future_comparisons": {
            "gpt_5_1_automatic_assignment": False,
            "gpt_5_1_requires_revised_plan_and_authorization": True,
            "allowed_conditions": [
                "groq_quality_below_threshold",
                "groq_models_disagree",
                "critical_workload",
                "explicit_quality_premium_comparison",
            ],
        },
        "request_counts": counts,
        "execution_policy": {
            "serial_ordering_required": True,
            "parallel_execution_allowed": False,
            "one_request_per_case_provider_model": True,
            "duplicate_request_after_ambiguous_timeout_allowed": False,
            "recursive_execution_allowed": False,
            "immediate_stop_on_hard_safety_failure": True,
            "maximum_run_duration_seconds": fixture[
                "duration_limits"
            ]["maximum_run_duration_seconds"],
            "maximum_provider_duration_seconds": deepcopy(
                fixture["duration_limits"][
                    "maximum_provider_duration_seconds"
                ]
            ),
        },
        "fallback_policy": {
            "fallback": False,
            "cross_provider_fallback_allowed": False,
            "recursive_fallback_allowed": False,
        },
        "retry_policy": {
            "harness_retry_limit": 0,
            "ambiguous_timeout_retry_allowed": False,
            "provider_sdk_automatic_retries_required": 0,
            "provider_sdk_retry_configuration_status": (
                "requires_pre_execution_verification"
            ),
        },
        "timeout_policy": {
            "timeout_seconds": request_limits["timeout_seconds"],
            "explicit_timeout_required": True,
            "timeout_is_stop_condition": True,
        },
        "token_budget_schema": token_budgets,
        "cost_ceiling_schema": deepcopy(
            fixture["cost_budget_schema"]
        ),
        "result_packet_schema": {
            "allowlisted_fields": sorted(_RESULT_PACKET_FIELDS),
            "prohibited_field_parts": sorted(
                _PROHIBITED_PACKET_KEY_PARTS
            ),
            "normalized_output_only": True,
            "raw_response_persistence_allowed": False,
            "usage_metadata_required_for_cost_comparison": True,
            "future_step8o_handoff_requires_controlled_adapter": True,
        },
        "artifact_retention_policy": deepcopy(
            fixture["artifact_retention_policy"]
        ),
        "authorization_schema": {
            "authorization_version": AUTHORIZATION_VERSION,
            "operator_created_only": True,
            "automatic_creation_allowed": False,
            "required_fields": [
                "authorization_version",
                "benchmark_plan_sha256",
                "case_corpus_sha256",
                "approved_candidate_pairs",
                "approved_case_aliases",
                "maximum_request_count",
                "token_budgets",
                "pricing_table_version",
                "maximum_observed_cost_per_model",
                "maximum_total_observed_cost",
                "valid_from_utc",
                "expires_at_utc",
                "fallback",
                "gemini_allowed",
                "production_activation_allowed",
                "operator_approved",
            ],
            "positive_dollar_ceiling_required": True,
            "bounded_validity_window_required": True,
        },
        "stop_conditions": list(_STOP_CONDITIONS),
        "rollback_contract": {
            "production_routing_change_allowed": False,
            "provider_default_change_allowed": False,
            "cache_promotion_allowed": False,
            "model_selection_publication_allowed": False,
            "application_planning_integration_allowed": False,
            "ignored_redacted_evidence_preserved_for_review": True,
            "return_to_default_off_required": True,
        },
        "model_selection_evidence_requirements": {
            "controlled_live_results_required": True,
            "minimum_case_coverage_required": True,
            "all_hard_failures_zero_required": True,
            "schema_valid_rate_threshold_required": True,
            "normalization_threshold_required": True,
            "unsupported_claims_zero_required": True,
            "hallucinations_zero_required": True,
            "deterministic_authority_required": True,
            "task_specific_quality_thresholds_required": True,
            "observed_latency_required": True,
            "observed_token_counts_required": True,
            "observed_cost_required": True,
            "repeatability_evidence_when_required": True,
            "human_review_for_critical_workloads": True,
            "quality_precedes_cost": True,
            "lower_cost_must_meet_same_quality_and_safety": True,
            "gpt_5_1_requires_observed_material_quality_improvement": True,
            "selection_execution_allowed": False,
        },
        "authority_invariants": {
            "live_execution_authorized": False,
            "provider_calls_allowed": False,
            "fallback_allowed": False,
            "production_activation_allowed": False,
            "routing_change_allowed": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "recovery_006_authorized": False,
        },
    }
    validate_controlled_provider_benchmark_plan(plan)
    return deepcopy(plan)


def validate_controlled_provider_benchmark_plan(
    plan: Dict[str, Any],
) -> bool:
    _require(isinstance(plan, dict), "controlled plan must be an object")
    _require(
        plan.get("plan_version") == CONTROLLED_PLAN_VERSION,
        "controlled plan version mismatch",
    )
    _require(
        [
            (row.get("provider"), row.get("model"))
            for row in plan.get("candidate_definitions", [])
        ]
        == list(MODEL_ORDER),
        "controlled plan candidates must come from Step 8L",
    )
    _require(
        all(
            row.get("provider") != "gemini"
            for row in plan["candidate_definitions"]
        ),
        "Gemini is prohibited",
    )
    _require(
        plan.get("workload_order") == list(WORKLOAD_ORDER),
        "controlled plan workloads must come from Step 8L",
    )
    fixture = load_run_plan_fixture()
    _require(
        plan.get("run_plan_fixture_version") == RUN_PLAN_FIXTURE_VERSION,
        "run plan fixture version mismatch",
    )
    review = plan.get("transmission_review")
    _require(
        isinstance(review, list)
        and len(review) == plan.get("case_count"),
        "every case requires transmission review",
    )
    aliases = [row.get("case_alias") for row in review]
    _require(
        len(aliases) == len(set(aliases))
        and all(
            isinstance(alias, str)
            and alias.startswith("case_")
            and len(alias) == 29
            for alias in aliases
        ),
        "case aliases must be unique and deterministic",
    )
    required_review_booleans = {
        "wholly_synthetic",
        "contains_personal_data",
        "contains_runtime_derived_data",
        "contains_employer_or_company_identity",
        "contains_person_name",
        "contains_resume_derived_text",
        "contains_private_job_description_text",
        "contains_credentials_or_secrets",
        "contains_internal_paths",
        "contains_request_identifiers",
        "contains_database_information",
        "contains_proprietary_application_state",
        "contains_unsupported_free_form_text",
        "requires_additional_redaction",
        "eligible_for_later_controlled_transmission",
        "human_approval_required",
    }
    _require(
        all(
            required_review_booleans.issubset(row)
            and all(
                isinstance(row[field], bool)
                for field in required_review_booleans
            )
            and row["human_approval_required"] is True
            and isinstance(row.get("eligibility_reasons"), list)
            and (
                row["eligible_for_later_controlled_transmission"]
                == (not row["eligibility_reasons"])
            )
            for row in review
        ),
        "transmission review is incomplete or unsafe",
    )
    expected_summary = {
        "reviewed_case_count": len(review),
        "eligible_case_count": sum(
            1
            for row in review
            if row["eligible_for_later_controlled_transmission"]
        ),
        "ineligible_case_count": sum(
            1
            for row in review
            if not row["eligible_for_later_controlled_transmission"]
        ),
    }
    _require(
        plan.get("transmission_review_summary") == expected_summary,
        "transmission review summary mismatch",
    )
    request_schema = plan.get("request_packet_schema")
    _require(
        isinstance(request_schema, dict)
        and request_schema.get("allowlisted_fields")
        == sorted(_REQUEST_PACKET_FIELDS)
        and request_schema.get("prohibited_field_parts")
        == sorted(_PROHIBITED_PACKET_KEY_PARTS)
        and request_schema.get("local_alias_required") is True
        and request_schema.get("goldens_local_only") is True
        and request_schema.get("provenance_local_only") is True
        and request_schema.get("live_execution_requested") is False,
        "request packet schema is unsafe",
    )
    matrix = plan.get("staged_matrix")
    _require(isinstance(matrix, list) and bool(matrix), "staged matrix required")
    _require(
        [row.get("execution_order") for row in matrix]
        == list(range(1, len(matrix) + 1)),
        "execution ordering must be stable and serial",
    )
    _require(
        all(
            row.get("fallback") is False
            and row.get("harness_retry_limit") == 0
            and row.get("live_execution_authorized") is False
            and (row.get("provider"), row.get("model")) in MODEL_ORDER
            for row in matrix
        ),
        "matrix routing or safety policy is invalid",
    )
    approved_aliases = {
        row["case_alias"]
        for row in review
        if row["eligible_for_later_controlled_transmission"]
    }
    _require(
        all(row.get("case_alias") in approved_aliases for row in matrix)
        and len(
            {
                (
                    row.get("case_alias"),
                    row.get("provider"),
                    row.get("model"),
                )
                for row in matrix
            }
        )
        == len(matrix),
        "matrix contains an unapproved or duplicate request",
    )
    counts = _request_counts(matrix)
    _require(
        plan.get("request_counts") == counts,
        "request count budget mismatch",
    )
    _require(
        counts["maximum_requests_per_case"]
        <= fixture["request_limits"][
            "maximum_requests_per_case"
        ],
        "per-case request bound exceeded",
    )
    _require(
        plan.get("conditional_future_comparisons", {}).get(
            "gpt_5_1_automatic_assignment"
        )
        is False
        and counts["by_model"]["openai/gpt-5.1"] == 0,
        "GPT-5.1 must not be automatically assigned",
    )
    _require(
        plan.get("fallback_policy", {}).get("fallback") is False,
        "fallback must remain false",
    )
    _require(
        plan.get("retry_policy", {}).get("harness_retry_limit") == 0,
        "harness retries must remain zero",
    )
    execution = plan.get("execution_policy")
    _require(
        isinstance(execution, dict)
        and execution.get("serial_ordering_required") is True
        and execution.get("parallel_execution_allowed") is False
        and execution.get("one_request_per_case_provider_model") is True
        and execution.get(
            "duplicate_request_after_ambiguous_timeout_allowed"
        )
        is False
        and execution.get("recursive_execution_allowed") is False
        and execution.get("immediate_stop_on_hard_safety_failure") is True
        and execution.get("maximum_run_duration_seconds")
        == fixture["duration_limits"]["maximum_run_duration_seconds"]
        and execution.get("maximum_provider_duration_seconds")
        == fixture["duration_limits"]["maximum_provider_duration_seconds"],
        "execution policy is unsafe",
    )
    _require(
        plan.get("retry_policy")
        == {
            "harness_retry_limit": 0,
            "ambiguous_timeout_retry_allowed": False,
            "provider_sdk_automatic_retries_required": 0,
            "provider_sdk_retry_configuration_status": (
                "requires_pre_execution_verification"
            ),
        },
        "retry policy is unsafe",
    )
    _require(
        plan.get("timeout_policy")
        == {
            "timeout_seconds": fixture["request_limits"]["timeout_seconds"],
            "explicit_timeout_required": True,
            "timeout_is_stop_condition": True,
        },
        "timeout policy is unsafe",
    )
    expected_tokens = {
        "maximum_input_tokens_per_request": fixture["request_limits"][
            "maximum_input_tokens_per_request"
        ],
        "maximum_output_tokens_per_request": fixture["request_limits"][
            "maximum_completion_tokens_per_request"
        ],
        "maximum_total_observed_input_tokens": (
            counts["maximum_total_requests"]
            * fixture["request_limits"]["maximum_input_tokens_per_request"]
        ),
        "maximum_total_observed_output_tokens": (
            counts["maximum_total_requests"]
            * fixture["request_limits"][
                "maximum_completion_tokens_per_request"
            ]
        ),
        "observed_input_tokens_required": True,
        "observed_output_tokens_required": True,
        "missing_usage_blocks_cost_comparison": True,
    }
    _require(
        plan.get("token_budget_schema") == expected_tokens,
        "token budget schema mismatch",
    )
    _require(
        plan.get("cost_ceiling_schema") == fixture["cost_budget_schema"],
        "cost ceiling schema mismatch",
    )
    result_schema = plan.get("result_packet_schema")
    _require(
        isinstance(result_schema, dict)
        and result_schema.get("allowlisted_fields")
        == sorted(_RESULT_PACKET_FIELDS)
        and result_schema.get("prohibited_field_parts")
        == sorted(_PROHIBITED_PACKET_KEY_PARTS)
        and result_schema.get("normalized_output_only") is True
        and result_schema.get("raw_response_persistence_allowed") is False
        and result_schema.get(
            "usage_metadata_required_for_cost_comparison"
        )
        is True
        and result_schema.get(
            "future_step8o_handoff_requires_controlled_adapter"
        )
        is True,
        "result packet schema is unsafe",
    )
    _require(
        plan.get("artifact_retention_policy")
        == fixture["artifact_retention_policy"],
        "artifact retention policy mismatch",
    )
    authorization = plan.get("authorization_schema")
    _require(
        isinstance(authorization, dict)
        and authorization.get("authorization_version")
        == AUTHORIZATION_VERSION
        and authorization.get("operator_created_only") is True
        and authorization.get("automatic_creation_allowed") is False
        and authorization.get("positive_dollar_ceiling_required") is True
        and authorization.get("bounded_validity_window_required") is True,
        "authorization schema is unsafe",
    )
    _require(
        set(plan.get("stop_conditions", [])) == set(_STOP_CONDITIONS),
        "stop conditions are incomplete",
    )
    rollback = plan.get("rollback_contract")
    _require(
        isinstance(rollback, dict)
        and all(
            rollback.get(field) is False
            for field in (
                "production_routing_change_allowed",
                "provider_default_change_allowed",
                "cache_promotion_allowed",
                "model_selection_publication_allowed",
                "application_planning_integration_allowed",
            )
        )
        and rollback.get("ignored_redacted_evidence_preserved_for_review")
        is True
        and rollback.get("return_to_default_off_required") is True,
        "rollback contract is unsafe",
    )
    evidence = plan.get("model_selection_evidence_requirements")
    _require(
        isinstance(evidence, dict)
        and evidence.get("quality_precedes_cost") is True
        and evidence.get("lower_cost_must_meet_same_quality_and_safety")
        is True
        and evidence.get("selection_execution_allowed") is False
        and all(
            value is True
            for field, value in evidence.items()
            if field != "selection_execution_allowed"
        ),
        "model-selection evidence contract is unsafe",
    )
    authority = plan.get("authority_invariants")
    _require(
        isinstance(authority, dict)
        and authority.get("live_execution_authorized") is False
        and authority.get("provider_calls_allowed") is False
        and authority.get("fallback_allowed") is False
        and authority.get("production_activation_allowed") is False
        and authority.get("routing_change_allowed") is False
        and authority.get("mutation_count") == 0
        and authority.get("application_action_count") == 0
        and authority.get("ats_action_count") == 0
        and authority.get("recovery_006_authorized") is False,
        "controlled plan authority changed",
    )
    serialized = _canonical_json(plan).lower()
    for forbidden in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
    ):
        _require(forbidden not in serialized, "model selection is prohibited")
    return True


def serialize_controlled_provider_benchmark_plan(
    plan: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(payload)
    return _canonical_json(payload)


def controlled_provider_benchmark_plan_sha256(
    plan: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_controlled_provider_benchmark_plan(plan).encode("utf-8")
    ).hexdigest()


def build_transmittable_request_packet(
    *,
    case_alias: str,
    provider: str,
    model: str,
    plan: Dict[str, Any] | None = None,
    corpus: Dict[str, Any] | None = None,
    live_execution_requested: bool = False,
) -> Dict[str, Any]:
    """Build a provider-neutral template; live execution is always false."""

    controlled_plan = (
        build_controlled_provider_benchmark_plan(corpus=corpus)
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        live_execution_requested is False,
        "live execution is not authorized by this plan",
    )
    cases = _eligible_alias_to_case(corpus)
    case = cases.get(case_alias)
    _require(case is not None, "case is not approved for transmission")
    _require(
        any(
            row["case_alias"] == case_alias
            and row["provider"] == provider
            and row["model"] == model
            for row in controlled_plan["staged_matrix"]
        ),
        "case provider/model combination is not in the staged matrix",
    )
    fixture = load_run_plan_fixture()
    packet = {
        "benchmark_contract_version": STEP8L_CONTRACT_VERSION,
        "run_plan_version": CONTROLLED_PLAN_VERSION,
        "case_alias": case_alias,
        "workload_id": case["workload_id"],
        "provider": provider,
        "model": model,
        "synthetic_input": deepcopy(case["normalized_input_packet"]),
        "output_schema": {
            "schema_id": case["schema_id"],
            "required_fields": deepcopy(case["required_fields"]),
        },
        "temperature": fixture["request_limits"]["temperature"],
        "maximum_completion_tokens": fixture["request_limits"][
            "maximum_completion_tokens_per_request"
        ],
        "timeout_seconds": fixture["request_limits"]["timeout_seconds"],
        "fallback": False,
        "live_execution_requested": False,
    }
    validate_transmittable_request_packet(packet, plan=controlled_plan)
    return deepcopy(packet)


def validate_transmittable_request_packet(
    packet: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> bool:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(isinstance(packet, dict), "request packet must be an object")
    _require(
        set(packet) == _REQUEST_PACKET_FIELDS,
        "request packet fields must match the allowlist",
    )
    _require(
        not _has_prohibited_packet_key(packet),
        "request packet contains a prohibited field",
    )
    _require(
        (packet.get("provider"), packet.get("model")) in MODEL_ORDER,
        "request provider/model pair is unsupported",
    )
    _require(packet.get("provider") != "gemini", "Gemini is prohibited")
    _require(packet.get("fallback") is False, "fallback is prohibited")
    _require(
        packet.get("live_execution_requested") is False,
        "live execution is not authorized",
    )
    _require(
        any(
            row["case_alias"] == packet.get("case_alias")
            and row["workload_id"] == packet.get("workload_id")
            and row["provider"] == packet.get("provider")
            and row["model"] == packet.get("model")
            for row in controlled_plan["staged_matrix"]
        ),
        "request packet is outside the staged matrix",
    )
    return True


def validate_redacted_result_packet(packet: Dict[str, Any]) -> bool:
    _require(isinstance(packet, dict), "result packet must be an object")
    _require(
        set(packet) == _RESULT_PACKET_FIELDS,
        "result packet fields must match the allowlist",
    )
    _require(
        not _has_prohibited_packet_key(packet),
        "result packet contains a prohibited field",
    )
    _require(
        (packet.get("provider"), packet.get("model")) in MODEL_ORDER,
        "result provider/model pair is unsupported",
    )
    _require(packet.get("fallback_used") is False, "fallback is prohibited")
    _require(packet.get("retry_count") == 0, "retries are prohibited")
    _require(
        isinstance(packet.get("normalized_output"), dict),
        "normalized output must be an object",
    )
    _require(
        packet.get("redaction_status") == "redacted_normalized_only",
        "result packet must be redacted",
    )
    for field in (
        "latency_ms",
        "input_token_count",
        "output_token_count",
        "observed_cost",
    ):
        value = packet.get(field)
        _require(
            value is None
            or (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and value >= 0
            ),
            f"{field} must be observed, absent, or nonnegative",
        )
    return True


def validate_operator_authorization(
    authorization: Dict[str, Any] | None,
    *,
    plan: Dict[str, Any] | None = None,
    execution_at_utc: str,
) -> bool:
    """Validate a separately operator-created authorization document."""

    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        isinstance(authorization, dict),
        "operator authorization is required",
    )
    required = set(
        controlled_plan["authorization_schema"]["required_fields"]
    )
    _require(
        required.issubset(authorization),
        "operator authorization is malformed",
    )
    _require(
        authorization.get("authorization_version")
        == AUTHORIZATION_VERSION,
        "authorization version mismatch",
    )
    _require(
        authorization.get("benchmark_plan_sha256")
        == controlled_provider_benchmark_plan_sha256(controlled_plan),
        "authorization plan hash mismatch",
    )
    _require(
        authorization.get("case_corpus_sha256")
        == controlled_plan["step8o_case_corpus_sha256"],
        "authorization corpus hash mismatch",
    )
    expected_pairs = deepcopy(controlled_plan["candidate_definitions"])
    _require(
        authorization.get("approved_candidate_pairs") == expected_pairs,
        "authorization provider/model scope mismatch",
    )
    expected_aliases = sorted(
        row["case_alias"]
        for row in controlled_plan["transmission_review"]
        if row["eligible_for_later_controlled_transmission"]
    )
    _require(
        authorization.get("approved_case_aliases") == expected_aliases,
        "authorization case scope is broader or mismatched",
    )
    _require(
        authorization.get("maximum_request_count")
        == controlled_plan["request_counts"]["maximum_total_requests"],
        "authorization request budget mismatch",
    )
    _require(
        authorization.get("token_budgets")
        == controlled_plan["token_budget_schema"],
        "authorization token budget mismatch",
    )
    _require(
        bool(_clean_text(authorization.get("pricing_table_version"))),
        "authorization pricing table version is required",
    )
    per_model_cost = authorization.get("maximum_observed_cost_per_model")
    expected_model_keys = set(
        controlled_plan["request_counts"]["maximum_requests_per_model"]
    )
    _require(
        isinstance(per_model_cost, dict)
        and set(per_model_cost) == expected_model_keys
        and all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > 0
            for value in per_model_cost.values()
        ),
        "authorization per-model dollar ceilings are required",
    )
    total_cost = authorization.get("maximum_total_observed_cost")
    _require(
        isinstance(total_cost, (int, float))
        and not isinstance(total_cost, bool)
        and total_cost > 0,
        "authorization total dollar ceiling is required",
    )
    _require(
        authorization.get("fallback") is False,
        "authorization fallback must be false",
    )
    _require(
        authorization.get("gemini_allowed") is False,
        "authorization Gemini scope must be false",
    )
    _require(
        authorization.get("production_activation_allowed") is False,
        "authorization production activation must be false",
    )
    _require(
        authorization.get("operator_approved") is True,
        "operator approval Boolean must be true",
    )
    valid_from = _parse_utc(authorization.get("valid_from_utc"))
    expires_at = _parse_utc(authorization.get("expires_at_utc"))
    execution_at = _parse_utc(execution_at_utc)
    _require(valid_from < expires_at, "authorization validity window is invalid")
    _require(
        valid_from <= execution_at <= expires_at,
        "authorization is expired or not yet valid",
    )
    return True

"""Deterministic, provider-free grading for normalized benchmark fixtures.

This module reads only repository-owned JSON definitions.  It does not import
provider clients, load environment configuration, execute workloads, or write
artifacts.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from src.evaluation.provider_benchmark_contract import (
    CONTRACT_VERSION as STEP8L_CONTRACT_VERSION,
    HARD_FAILURE_ORDER,
    METRIC_ORDER,
    MODEL_ORDER,
    WORKLOAD_ORDER,
    build_provider_benchmark_contract,
)


FIXTURE_BENCHMARK_VERSION = "provider-fixture-benchmark-v1"
CASE_CORPUS_VERSION = "provider-fixture-case-corpus-v1"
DEFAULT_CASE_CORPUS_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "provider_benchmark"
    / "cases.json"
)

STEP8L_CONTRACT_SOURCE = "src/evaluation/provider_benchmark_contract.py"
STEP8M_COMPATIBILITY_SOURCE = (
    "src/evaluation/provider_client_compatibility.py"
)
FIXTURE_MANIFEST_SOURCE = "tests/fixtures/provider_benchmark/manifest.json"
CASE_CORPUS_SOURCE = "tests/fixtures/provider_benchmark/cases.json"

_COMPARISON_TYPES = {
    "exact_golden",
    "invariant_only",
    "schema_only",
    "coverage_gap",
}
_REQUIRED_CASE_FIELDS = {
    "case_id",
    "workload_id",
    "tier",
    "provenance",
    "sanitized_classification",
    "contains_personal_resume_content",
    "live_transmission_eligible",
    "offline_only",
    "additional_redaction_required",
    "schema_id",
    "normalized_input_packet",
    "expected_output",
    "expected_invariant",
    "required_fields",
    "supported_evidence_tokens",
    "supported_evidence_ids",
    "prohibited_claims_or_terms",
    "comparison_type",
    "human_review_required",
    "deterministic_authority_required",
}
_REQUIRED_RESULT_FIELDS = {
    "case_id",
    "workload_id",
    "provider",
    "model",
    "normalized_output",
    "schema_valid",
    "normalization_succeeded",
    "fallback_used",
    "provider_call_count",
    "mutation_count",
    "application_action_count",
    "ats_action_count",
    "raw_response_persisted",
    "live_execution",
}
_OPTIONAL_EXECUTION_FIELDS = {
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "estimated_cost",
}
_ALLOWED_RESULT_FIELDS = _REQUIRED_RESULT_FIELDS | _OPTIONAL_EXECUTION_FIELDS
_FORBIDDEN_RESULT_KEY_PARTS = {
    "credential",
    "messages",
    "prompt",
    "provider_request",
    "raw_provider",
    "raw_response",
    "request_payload",
}
_SENSITIVE_MARKERS = {
    "api_key",
    "credential",
    "database_url",
    "personal_resume",
    "private_runtime",
}
_NOT_OBSERVED_OFFLINE = "not_observed_offline"
_NOT_APPLICABLE_FALLBACK = "not_applicable_fallback_disabled"

_WORKLOAD_GRADER_RESPONSIBILITIES = {
    "skill_extraction": [
        "required_skill_precision",
        "required_skill_recall",
        "preferred_skill_precision",
        "preferred_skill_recall",
        "unsupported_skill_count",
        "bucket_correctness",
    ],
    "job_fit_evaluation": [
        "schema_validity",
        "required_field_completeness",
        "bounded_score_ranges",
        "classification_agreement",
        "reason_grounding",
        "unsupported_claim_count",
    ],
    "jd_intelligence": [
        "required_signal_agreement",
        "preferred_signal_agreement",
        "workflow_context_agreement",
        "missing_requirement_accuracy",
        "unsupported_signal_count",
    ],
    "grounded_rag_answer": [
        "required_source_identifiers",
        "claim_grounding",
        "unsupported_citation_count",
        "unsupported_claim_count",
        "insufficient_evidence_behavior",
    ],
    "resume_fallback_ranking": [
        "candidate_identity_preservation",
        "advisory_candidate_agreement",
        "ranking_agreement",
        "unsupported_candidate_count",
        "deterministic_authority_preservation",
    ],
    "ambiguous_resume_adjudication": [
        "advisory_decision_agreement",
        "reason_code_agreement",
        "deterministic_result_preservation",
        "no_authoritative_selection_mutation",
    ],
    "critic_evaluation": [
        "decision_agreement",
        "reason_code_agreement",
        "unsupported_claim_rejection",
        "safe_suggestion_approval",
        "downgrade_agreement",
    ],
    "tailoring_generation": [
        "required_schema",
        "evidence_token_support",
        "unsupported_claim_count",
        "invented_content_count",
        "source_bullet_identity_preservation",
        "human_review_requirement",
    ],
    "tailoring_refinement": [
        "evidence_support",
        "meaning_preservation",
        "unsupported_additions",
        "required_structure",
        "patch_identity_preservation",
    ],
    "tailoring_judge": [
        "advisory_judgment_agreement",
        "supported_candidate_agreement",
        "unsupported_candidate_rejection",
        "no_authoritative_patch_mutation",
    ],
    "manual_scan_phrase": [
        "supported_term_containment",
        "prohibited_term_absence",
        "schema_validity",
        "manual_only_authority",
    ],
    "manual_provider_preview": [
        "schema_validity",
        "advisory_manual_only_status",
        "evidence_support",
        "no_mutation_or_action_authority",
    ],
}


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


def _normalized_term(value: Any) -> str:
    return " ".join(_clean_text(value).lower().split())


def _normalized_terms(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [
        term
        for term in (_normalized_term(item) for item in value)
        if term
    ]


def _normalized_set(value: Any) -> set[str]:
    return set(_normalized_terms(value))


def _rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 1.0
    return round(float(numerator) / float(denominator), 6)


def _precision_recall(
    actual: Iterable[str],
    expected: Iterable[str],
) -> tuple[float, float]:
    actual_set = set(actual)
    expected_set = set(expected)
    overlap = actual_set & expected_set
    return (
        _rate(len(overlap), len(actual_set)),
        _rate(len(overlap), len(expected_set)),
    )


def _agreement(actual: Any, expected: Any) -> float:
    return 1.0 if actual == expected else 0.0


def _average(values: Iterable[float]) -> float | None:
    rows = [float(value) for value in values]
    if not rows:
        return None
    return round(sum(rows) / len(rows), 6)


def _validate_repository_test_path(value: Any) -> None:
    text = _clean_text(value)
    path = PurePosixPath(text)
    _require(bool(text), "provenance source_path is required")
    _require(not path.is_absolute(), "absolute provenance paths are prohibited")
    _require(".." not in path.parts, "escaping provenance paths are prohibited")
    _require(text.startswith("tests/"), "provenance must be test-owned")


def _contains_machine_or_runtime_path(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_machine_or_runtime_path(key)
            or _contains_machine_or_runtime_path(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_machine_or_runtime_path(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.replace("\\", "/").lower()
    return (
        normalized.startswith("/")
        or normalized.startswith("../")
        or "/../" in normalized
        or normalized.startswith("outputs/")
        or normalized.startswith("data/")
        or normalized.startswith("file:")
        or "/users/" in normalized
    )


def _contains_forbidden_fixture_material(value: Any) -> bool:
    serialized = _canonical_json(value).lower()
    return any(
        marker in serialized
        for marker in (
            "database_url",
            "raw_provider_response",
            "request_id",
            "skill_eval.txt",
        )
    )


def _contains_forbidden_result_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = _normalized_term(key).replace(" ", "_")
            if (
                normalized != "raw_response_persisted"
                and any(
                    part in normalized
                    for part in _FORBIDDEN_RESULT_KEY_PARTS
                )
            ):
                return True
            if _contains_forbidden_result_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_result_key(item) for item in value)
    return False


def _case_by_id(corpus: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(case["case_id"]): case
        for case in corpus.get("cases", [])
        if isinstance(case, dict)
    }


def _workload_tiers() -> Dict[str, str]:
    benchmark = build_provider_benchmark_contract()
    return {
        row["workload_id"]: row["tier"]
        for row in benchmark["workloads"]
    }


def validate_fixture_case_corpus(corpus: Dict[str, Any]) -> bool:
    """Fail closed on unsafe fixture material, missing coverage, or ambiguity."""

    _require(isinstance(corpus, dict), "fixture corpus must be an object")
    _require(
        corpus.get("corpus_version") == CASE_CORPUS_VERSION,
        "fixture corpus version mismatch",
    )
    cases = corpus.get("cases")
    _require(isinstance(cases, list) and bool(cases), "fixture cases are required")
    _require(
        not _contains_machine_or_runtime_path(corpus),
        "machine-specific or runtime paths are prohibited",
    )
    _require(
        not _contains_forbidden_fixture_material(corpus),
        "forbidden fixture material is prohibited",
    )

    workload_tiers = _workload_tiers()
    case_ids: List[str] = []
    workloads_seen: set[str] = set()
    for case in cases:
        _require(isinstance(case, dict), "fixture case must be an object")
        _require(
            _REQUIRED_CASE_FIELDS.issubset(case),
            "fixture case is missing required fields",
        )
        case_id = _clean_text(case.get("case_id"))
        workload_id = _clean_text(case.get("workload_id"))
        _require(bool(case_id), "case_id is required")
        _require(workload_id in WORKLOAD_ORDER, "unknown fixture workload")
        _require(
            case.get("tier") == workload_tiers[workload_id],
            "fixture workload tier mismatch",
        )

        provenance = case.get("provenance")
        _require(isinstance(provenance, dict), "fixture provenance is required")
        _validate_repository_test_path(provenance.get("source_path"))
        _require(
            bool(_clean_text(provenance.get("source_identifier"))),
            "fixture provenance identifier is required",
        )
        _require(
            case.get("sanitized_classification")
            in {"synthetic_sanitized", "repository_sanitized"},
            "fixture sanitization classification is invalid",
        )
        _require(
            case.get("contains_personal_resume_content") is False,
            "personal resume content is prohibited",
        )
        _require(
            case.get("live_transmission_eligible") is False,
            "live fixture transmission is prohibited",
        )
        _require(case.get("offline_only") is True, "fixture must remain offline-only")
        _require(
            isinstance(case.get("additional_redaction_required"), bool),
            "redaction classification must be boolean",
        )
        _require(bool(_clean_text(case.get("schema_id"))), "schema_id is required")
        _require(
            isinstance(case.get("normalized_input_packet"), dict),
            "normalized input packet must be an object",
        )
        _require(
            isinstance(case.get("expected_output"), dict),
            "expected output must be an object",
        )
        _require(
            isinstance(case.get("expected_invariant"), dict),
            "expected invariant must be an object",
        )
        _require(
            isinstance(case.get("required_fields"), list)
            and all(_clean_text(item) for item in case["required_fields"]),
            "required fields must be a nonempty string list",
        )
        for field in (
            "supported_evidence_tokens",
            "supported_evidence_ids",
            "prohibited_claims_or_terms",
        ):
            _require(isinstance(case.get(field), list), f"{field} must be a list")
        comparison_type = case.get("comparison_type")
        _require(
            comparison_type in _COMPARISON_TYPES,
            "fixture comparison type is unsupported",
        )
        _require(
            isinstance(case.get("human_review_required"), bool),
            "human review classification must be boolean",
        )
        _require(
            case.get("deterministic_authority_required") is True,
            "deterministic authority is required",
        )
        has_expected = bool(case["expected_output"]) or bool(
            case["expected_invariant"]
        )
        _require(
            has_expected,
            "fixture requires an expected output or invariant",
        )
        if comparison_type == "coverage_gap":
            _require(
                bool(_clean_text(
                    case["expected_invariant"].get("coverage_gap_reason")
                )),
                "coverage gap reason is required",
            )
        else:
            _require(
                bool(case["expected_output"])
                or comparison_type in {"invariant_only", "schema_only"},
                "gradable fixture requires an expected output",
            )

        case_ids.append(case_id)
        workloads_seen.add(workload_id)

    _require(len(case_ids) == len(set(case_ids)), "duplicate fixture case ID")
    _require(
        workloads_seen == set(WORKLOAD_ORDER),
        "every workload requires a case or explicit coverage gap",
    )
    return True


def load_fixture_case_corpus(
    path: str | Path | None = None,
) -> Dict[str, Any]:
    """Load and validate the local sanitized case corpus without executing it."""

    corpus_path = Path(path) if path is not None else DEFAULT_CASE_CORPUS_PATH
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    validate_fixture_case_corpus(payload)
    return deepcopy(payload)


def fixture_case_coverage_summary(
    corpus: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    validate_fixture_case_corpus(payload)
    rows: List[Dict[str, Any]] = []
    for workload_id in WORKLOAD_ORDER:
        workload_cases = [
            case
            for case in payload["cases"]
            if case["workload_id"] == workload_id
        ]
        comparison_counts = {
            comparison_type: sum(
                1
                for case in workload_cases
                if case["comparison_type"] == comparison_type
            )
            for comparison_type in _COMPARISON_TYPES
        }
        rows.append(
            {
                "workload_id": workload_id,
                "machine_readable_case_count": len(workload_cases),
                "exact_golden_count": comparison_counts["exact_golden"],
                "invariant_only_count": comparison_counts["invariant_only"],
                "schema_only_count": comparison_counts["schema_only"],
                "coverage_gap_count": comparison_counts["coverage_gap"],
                "additional_redaction_required_count": sum(
                    1
                    for case in workload_cases
                    if case["additional_redaction_required"]
                ),
                "live_transmission_eligible_count": 0,
            }
        )
    return {
        "workload_count": len(WORKLOAD_ORDER),
        "total_case_count": len(payload["cases"]),
        "exact_golden_count": sum(row["exact_golden_count"] for row in rows),
        "invariant_only_count": sum(
            row["invariant_only_count"] for row in rows
        ),
        "schema_only_count": sum(row["schema_only_count"] for row in rows),
        "coverage_gap_count": sum(row["coverage_gap_count"] for row in rows),
        "additional_redaction_required_count": sum(
            row["additional_redaction_required_count"] for row in rows
        ),
        "live_transmission_eligible_count": 0,
        "workloads": rows,
    }


def serialize_fixture_case_corpus(
    corpus: Dict[str, Any] | None = None,
) -> str:
    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    validate_fixture_case_corpus(payload)
    ordered = {
        "corpus_version": payload["corpus_version"],
        "cases": sorted(payload["cases"], key=lambda case: case["case_id"]),
    }
    return _canonical_json(ordered)


def fixture_case_corpus_sha256(
    corpus: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_fixture_case_corpus(corpus).encode("utf-8")
    ).hexdigest()


def build_provider_fixture_benchmark_contract(
    corpus: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the versioned offline grading contract from Step 8L definitions."""

    benchmark = build_provider_benchmark_contract()
    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    validate_fixture_case_corpus(payload)
    contract = {
        "contract_version": FIXTURE_BENCHMARK_VERSION,
        "contract_kind": "offline_normalized_fixture_grading",
        "step8l_contract_source": STEP8L_CONTRACT_SOURCE,
        "step8l_contract_version": benchmark["contract_version"],
        "step8m_compatibility_source": STEP8M_COMPATIBILITY_SOURCE,
        "fixture_manifest_source": FIXTURE_MANIFEST_SOURCE,
        "case_corpus_source": CASE_CORPUS_SOURCE,
        "provider_order": deepcopy(benchmark["provider_order"]),
        "candidate_definitions": [
            {
                "candidate_id": row["candidate_id"],
                "provider": row["provider"],
                "model": row["model"],
            }
            for row in benchmark["candidate_definitions"]
        ],
        "workload_order": deepcopy(benchmark["workload_order"]),
        "metric_order": deepcopy(benchmark["metric_order"]),
        "hard_failure_order": deepcopy(benchmark["hard_failure_order"]),
        "grader_responsibilities": deepcopy(
            _WORKLOAD_GRADER_RESPONSIBILITIES
        ),
        "result_packet_schema": {
            "required_fields": sorted(_REQUIRED_RESULT_FIELDS),
            "optional_execution_fields": sorted(_OPTIONAL_EXECUTION_FIELDS),
            "fallback_used": False,
            "provider_call_count": 0,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "raw_response_persisted": False,
            "live_execution": False,
        },
        "quality_before_cost_policy": {
            "quality_evaluated_first": True,
            "hard_failures_must_equal_zero": True,
            "schema_and_normalization_required": True,
            "unsupported_claims_must_equal_zero": True,
            "hallucinations_must_equal_zero": True,
            "deterministic_authority_required": True,
            "observed_cost_required_for_cost_comparison": True,
            "observed_latency_required_for_latency_comparison": True,
            "pareto_frontier_future_only": True,
            "stable_tie_break_future_only": True,
            "live_evidence_required": True,
        },
        "controls": {
            "offline_only": True,
            "provider_clients_allowed": False,
            "provider_calls_allowed": False,
            "fallback_allowed": False,
            "network_allowed": False,
            "credential_reads_allowed": False,
            "database_allowed": False,
            "subprocess_allowed": False,
            "thread_creation_allowed": False,
            "artifact_writes_allowed": False,
            "authority_transfer_allowed": False,
            "application_actions_allowed": False,
            "ats_actions_allowed": False,
            "live_execution_allowed": False,
        },
        "fixture_corpus_sha256": fixture_case_corpus_sha256(payload),
        "coverage_summary": fixture_case_coverage_summary(payload),
    }
    validate_provider_fixture_benchmark_contract(contract)
    return deepcopy(contract)


def validate_provider_fixture_benchmark_contract(
    contract: Dict[str, Any],
) -> bool:
    _require(isinstance(contract, dict), "fixture benchmark must be an object")
    _require(
        contract.get("contract_version") == FIXTURE_BENCHMARK_VERSION,
        "fixture benchmark version mismatch",
    )
    _require(
        contract.get("step8l_contract_version") == STEP8L_CONTRACT_VERSION,
        "Step 8L contract version mismatch",
    )
    benchmark = build_provider_benchmark_contract()
    expected_candidates = [
        (row["provider"], row["model"])
        for row in benchmark["candidate_definitions"]
    ]
    actual_candidates = [
        (row.get("provider"), row.get("model"))
        for row in contract.get("candidate_definitions", [])
        if isinstance(row, dict)
    ]
    _require(
        actual_candidates == expected_candidates == list(MODEL_ORDER),
        "fixture benchmark candidates must come from Step 8L",
    )
    _require(
        all(provider != "gemini" for provider, _model in actual_candidates),
        "Gemini is not a fixture benchmark candidate",
    )
    _require(
        contract.get("workload_order") == list(WORKLOAD_ORDER),
        "fixture benchmark workloads must come from Step 8L",
    )
    _require(
        contract.get("metric_order") == list(METRIC_ORDER),
        "fixture benchmark metrics must come from Step 8L",
    )
    _require(
        contract.get("hard_failure_order") == list(HARD_FAILURE_ORDER),
        "fixture hard failures must come from Step 8L",
    )
    _require(
        contract.get("grader_responsibilities")
        == _WORKLOAD_GRADER_RESPONSIBILITIES,
        "workload grader responsibilities changed",
    )
    controls = contract.get("controls")
    _require(
        isinstance(controls, dict)
        and all(value is False for key, value in controls.items() if key != "offline_only")
        and controls.get("offline_only") is True,
        "fixture benchmark controls must remain offline and non-authoritative",
    )
    policy = contract.get("quality_before_cost_policy")
    _require(
        isinstance(policy, dict)
        and all(policy.values()),
        "quality-before-cost policy must remain fail closed",
    )
    schema = contract.get("result_packet_schema")
    _require(
        isinstance(schema, dict)
        and schema.get("required_fields") == sorted(_REQUIRED_RESULT_FIELDS),
        "normalized result schema changed",
    )
    _require(
        contract.get("coverage_summary", {}).get("workload_count")
        == len(WORKLOAD_ORDER),
        "fixture workload coverage is incomplete",
    )
    serialized = _canonical_json(contract).lower()
    for forbidden_field in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
        '"production_activation"',
    ):
        _require(
            forbidden_field not in serialized,
            "model selection or production activation fields are prohibited",
        )
    return True


def serialize_provider_fixture_benchmark_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_provider_fixture_benchmark_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_provider_fixture_benchmark_contract(payload)
    return _canonical_json(payload)


def provider_fixture_benchmark_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_provider_fixture_benchmark_contract(contract).encode("utf-8")
    ).hexdigest()


def validate_normalized_candidate_result(
    packet: Dict[str, Any],
    *,
    corpus: Dict[str, Any] | None = None,
) -> bool:
    """Validate a normalized, offline-only result before any grading."""

    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    validate_fixture_case_corpus(payload)
    _require(isinstance(packet, dict), "candidate result must be an object")
    _require(
        _REQUIRED_RESULT_FIELDS.issubset(packet),
        "candidate result is missing required fields",
    )
    _require(
        set(packet).issubset(_ALLOWED_RESULT_FIELDS),
        "candidate result contains unsupported fields",
    )
    _require(
        not _contains_forbidden_result_key(packet),
        "raw response, prompt, request, or credential fields are prohibited",
    )

    case_id = _clean_text(packet.get("case_id"))
    case = _case_by_id(payload).get(case_id)
    _require(case is not None, "candidate result references an unknown case")
    _require(
        packet.get("workload_id") == case["workload_id"],
        "candidate result workload mismatch",
    )
    provider_model = (
        _clean_text(packet.get("provider")).lower(),
        _clean_text(packet.get("model")),
    )
    _require(
        provider_model in MODEL_ORDER,
        "unsupported provider/model result pair",
    )
    _require(provider_model[0] != "gemini", "Gemini results are prohibited")
    _require(
        isinstance(packet.get("normalized_output"), dict),
        "normalized output must be an object",
    )
    _require(
        isinstance(packet.get("schema_valid"), bool),
        "schema_valid must be boolean",
    )
    _require(
        isinstance(packet.get("normalization_succeeded"), bool),
        "normalization_succeeded must be boolean",
    )
    _require(packet.get("fallback_used") is False, "fallback is prohibited")
    _require(
        packet.get("provider_call_count") == 0,
        "provider calls are prohibited offline",
    )
    _require(
        packet.get("mutation_count") == 0,
        "mutation is prohibited",
    )
    _require(
        packet.get("application_action_count") == 0,
        "application actions are prohibited",
    )
    _require(
        packet.get("ats_action_count") == 0,
        "ATS actions are prohibited",
    )
    _require(
        packet.get("raw_response_persisted") is False,
        "raw response persistence is prohibited",
    )
    _require(packet.get("live_execution") is False, "live execution is prohibited")
    for field in _OPTIONAL_EXECUTION_FIELDS:
        if field not in packet:
            continue
        value = packet[field]
        _require(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and float(value) >= 0,
            f"{field} must be a nonnegative observed value",
        )
    return True


def _required_field_completeness(
    output: Mapping[str, Any],
    required_fields: Sequence[str],
) -> float:
    present = sum(
        1
        for field in required_fields
        if field in output and output[field] is not None
    )
    return _rate(present, len(required_fields))


def _claim_terms(output: Mapping[str, Any]) -> List[str]:
    claims: List[str] = []
    for field in ("claims", "reason_tokens"):
        claims.extend(_normalized_terms(output.get(field)))
    for row in output.get("suggestions", []) if isinstance(
        output.get("suggestions"), list
    ) else []:
        if isinstance(row, dict):
            claims.extend(_normalized_terms(row.get("claims")))
    for row in output.get("options", []) if isinstance(
        output.get("options"), list
    ) else []:
        if isinstance(row, dict):
            claims.extend(_normalized_terms(row.get("terms")))
    return sorted(set(claims))


def _unsupported_claims(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> List[str]:
    claims = set(_claim_terms(output))
    supported = _normalized_set(case.get("supported_evidence_tokens"))
    prohibited = _normalized_set(case.get("prohibited_claims_or_terms"))
    return sorted((claims - supported) | (claims & prohibited))


def _sensitive_data_count(output: Mapping[str, Any]) -> int:
    serialized = _canonical_json(output).lower()
    return sum(1 for marker in _SENSITIVE_MARKERS if marker in serialized)


def _authority_preserved(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> bool:
    if output.get("authority_mutated") is True:
        return False
    input_packet = case.get("normalized_input_packet", {})
    deterministic_id = input_packet.get("deterministic_candidate_id")
    authoritative_id = output.get("authoritative_candidate_id")
    if deterministic_id is not None and authoritative_id != deterministic_id:
        return False
    for field in (
        "mutation_authorized",
        "application_authorized",
        "ats_authorized",
    ):
        if output.get(field) is True:
            return False
    return True


def _grade_skill_extraction(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    expected = case["expected_output"]
    actual_required = _normalized_set(output.get("required_skills"))
    actual_preferred = _normalized_set(output.get("preferred_skills"))
    expected_required = _normalized_set(expected.get("required_skills"))
    expected_preferred = _normalized_set(expected.get("preferred_skills"))
    required_precision, required_recall = _precision_recall(
        actual_required, expected_required
    )
    preferred_precision, preferred_recall = _precision_recall(
        actual_preferred, expected_preferred
    )
    unsupported = (
        actual_required
        | actual_preferred
    ) - (expected_required | expected_preferred)
    bucket_correct = (
        not (actual_required & expected_preferred)
        and not (actual_preferred & expected_required)
    )
    combined_precision, combined_recall = _precision_recall(
        actual_required | actual_preferred,
        expected_required | expected_preferred,
    )
    return {
        "required_skill_precision": required_precision,
        "required_skill_recall": required_recall,
        "preferred_skill_precision": preferred_precision,
        "preferred_skill_recall": preferred_recall,
        "unsupported_skill_count": len(unsupported),
        "bucket_correctness": 1.0 if bucket_correct else 0.0,
        "skill_extraction_precision": combined_precision,
        "skill_extraction_recall": combined_recall,
        "task_quality_passed": (
            required_precision
            == required_recall
            == preferred_precision
            == preferred_recall
            == 1.0
            and not unsupported
            and bucket_correct
        ),
    }


def _grade_job_fit(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    expected = case["expected_output"]
    fit_score = output.get("fit_score")
    required_score = output.get("required_match_score")
    bounded = all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0.0 <= float(value) <= 1.0
        for value in (fit_score, required_score)
    )
    unsupported = _unsupported_claims(case, output)
    missing_accuracy = _agreement(
        _normalized_set(output.get("missing_requirements")),
        _normalized_set(expected.get("missing_requirements")),
    )
    classification = _agreement(
        output.get("classification"),
        expected.get("classification"),
    )
    return {
        "bounded_score_ranges": 1.0 if bounded else 0.0,
        "classification_agreement": classification,
        "reason_grounding": 1.0 if not unsupported else 0.0,
        "unsupported_claim_count": len(unsupported),
        "missing_requirement_accuracy": missing_accuracy,
        "task_quality_passed": (
            bounded
            and classification == 1.0
            and not unsupported
            and missing_accuracy == 1.0
        ),
    }


def _grade_jd_intelligence(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    expected = case["expected_output"]
    fields = (
        "required_signals",
        "preferred_signals",
        "workflow_context",
    )
    agreements = {
        f"{field}_agreement": _agreement(
            _normalized_set(output.get(field)),
            _normalized_set(expected.get(field)),
        )
        for field in fields
    }
    actual_signals = set().union(
        *(_normalized_set(output.get(field)) for field in fields)
    )
    supported = _normalized_set(case.get("supported_evidence_tokens"))
    unsupported = actual_signals - supported
    missing_accuracy = _agreement(
        _normalized_set(output.get("missing_requirements")),
        _normalized_set(expected.get("missing_requirements")),
    )
    return {
        **agreements,
        "missing_requirement_accuracy": missing_accuracy,
        "unsupported_signal_count": len(unsupported),
        "task_quality_passed": (
            all(value == 1.0 for value in agreements.values())
            and missing_accuracy == 1.0
            and not unsupported
        ),
    }


def _grade_rag(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    claims = _normalized_set(output.get("claims"))
    supported_claims = _normalized_set(case.get("supported_evidence_tokens"))
    source_ids = set(_normalized_terms(output.get("source_ids")))
    supported_sources = set(_normalized_terms(case.get("supported_evidence_ids")))
    unsupported_claims = claims - supported_claims
    unsupported_sources = source_ids - supported_sources
    expected = case["expected_output"]
    status_agreement = _agreement(
        output.get("answer_status"),
        expected.get("answer_status"),
    )
    grounding = _rate(len(claims - unsupported_claims), len(claims))
    insufficient_correct = (
        status_agreement == 1.0
        if claims
        else output.get("answer_status")
        == case["expected_invariant"].get("insufficient_evidence_status")
    )
    return {
        "required_source_identifiers_present": 1.0
        if supported_sources.issubset(source_ids)
        else 0.0,
        "grounded_evidence_precision": grounding,
        "unsupported_citation_count": len(unsupported_sources),
        "unsupported_claim_count": len(unsupported_claims),
        "insufficient_evidence_behavior": 1.0 if insufficient_correct else 0.0,
        "task_quality_passed": (
            status_agreement == 1.0
            and not unsupported_claims
            and not unsupported_sources
            and supported_sources.issubset(source_ids)
            and insufficient_correct
        ),
    }


def _grade_resume_ranking(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    input_packet = case["normalized_input_packet"]
    expected = case["expected_output"]
    allowed = set(input_packet["candidate_ids"])
    ranking = list(output.get("ranking", [])) if isinstance(
        output.get("ranking"), list
    ) else []
    observed_ids = set(ranking)
    observed_ids.add(_clean_text(output.get("advisory_candidate_id")))
    observed_ids.discard("")
    unsupported = observed_ids - allowed
    advisory_agreement = _agreement(
        output.get("advisory_candidate_id"),
        expected.get("advisory_candidate_id"),
    )
    ranking_agreement = _agreement(ranking, expected.get("ranking"))
    identity = 1.0 if not unsupported and set(ranking) == allowed else 0.0
    authority = _authority_preserved(case, output)
    return {
        "candidate_identity_preservation": identity,
        "advisory_candidate_agreement": advisory_agreement,
        "winner_agreement": advisory_agreement,
        "ranking_agreement": ranking_agreement,
        "unsupported_candidate_count": len(unsupported),
        "deterministic_authority_preservation": 1.0 if authority else 0.0,
        "task_quality_passed": (
            identity == advisory_agreement == ranking_agreement == 1.0
            and authority
        ),
    }


def _grade_adjudication(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    expected = case["expected_output"]
    decision = _agreement(output.get("decision"), expected.get("decision"))
    reasons = _agreement(
        _normalized_set(output.get("reason_codes")),
        _normalized_set(expected.get("reason_codes")),
    )
    advisory = _agreement(
        output.get("advisory_candidate_id"),
        expected.get("advisory_candidate_id"),
    )
    authority = _authority_preserved(case, output)
    return {
        "advisory_decision_agreement": decision,
        "reason_code_agreement": reasons,
        "winner_agreement": advisory,
        "deterministic_result_preservation": 1.0 if authority else 0.0,
        "task_quality_passed": (
            decision == reasons == advisory == 1.0 and authority
        ),
    }


def _grade_critic(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    expected = case["expected_output"]
    decision = _agreement(output.get("decision"), expected.get("decision"))
    reasons = _agreement(
        _normalized_set(output.get("reason_codes")),
        _normalized_set(expected.get("reason_codes")),
    )
    unsupported = _unsupported_claims(case, output)
    safe_approval = (
        output.get("decision") == "approve"
        and output.get("safe_suggestion") is True
        and not unsupported
    )
    downgrade = (
        1.0
        if expected.get("decision") != "downgrade_to_guidance"
        else _agreement(output.get("decision"), "downgrade_to_guidance")
    )
    return {
        "decision_agreement": decision,
        "reason_code_agreement": reasons,
        "unsupported_claim_rejection": 1.0 if not unsupported else 0.0,
        "safe_suggestion_approval": 1.0 if safe_approval else 0.0,
        "downgrade_agreement": downgrade,
        "critic_agreement": decision,
        "unsupported_claim_count": len(unsupported),
        "task_quality_passed": (
            decision == reasons == downgrade == 1.0
            and not unsupported
            and safe_approval
        ),
    }


def _grade_tailoring_generation(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    suggestions = output.get("suggestions")
    suggestions = suggestions if isinstance(suggestions, list) else []
    supported_tokens = _normalized_set(case.get("supported_evidence_tokens"))
    supported_ids = set(case.get("supported_evidence_ids", []))
    claims: set[str] = set()
    source_ids: set[str] = set()
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            continue
        claims |= _normalized_set(suggestion.get("claims"))
        source_ids.add(_clean_text(suggestion.get("source_bullet_id")))
    unsupported = claims - supported_tokens
    unsupported_ids = source_ids - supported_ids
    evidence_support = _rate(len(claims - unsupported), len(claims))
    human_review = output.get("human_review_required") is True
    authority = _authority_preserved(case, output)
    return {
        "tailoring_evidence_support": evidence_support,
        "unsupported_claim_count": len(unsupported),
        "invented_content_count": len(unsupported),
        "source_bullet_identity_preservation": 1.0
        if not unsupported_ids and bool(source_ids)
        else 0.0,
        "human_review_requirement": 1.0 if human_review else 0.0,
        "task_quality_passed": (
            bool(suggestions)
            and not unsupported
            and not unsupported_ids
            and human_review
            and authority
        ),
    }


def _grade_tailoring_refinement(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    expected = case["expected_output"]
    claims = _normalized_set(output.get("claims"))
    supported = _normalized_set(case.get("supported_evidence_tokens"))
    unsupported = claims - supported
    evidence_support = _rate(len(claims - unsupported), len(claims))
    identity = (
        output.get("patch_id") == expected.get("patch_id")
        and output.get("source_bullet_id")
        == expected.get("source_bullet_id")
    )
    structure = output.get("structure_valid") is True
    meaning = output.get("meaning_preserved") is True
    authority = _authority_preserved(case, output)
    return {
        "tailoring_evidence_support": evidence_support,
        "meaning_preservation": 1.0 if meaning else 0.0,
        "unsupported_addition_count": len(unsupported),
        "required_structure": 1.0 if structure else 0.0,
        "patch_identity_preservation": 1.0 if identity else 0.0,
        "task_quality_passed": (
            not unsupported
            and identity
            and structure
            and meaning
            and authority
        ),
    }


def _grade_tailoring_judge(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    input_packet = case["normalized_input_packet"]
    expected = case["expected_output"]
    supported = set(input_packet["supported_candidate_ids"])
    unsupported = set(input_packet["unsupported_candidate_ids"])
    advisory = output.get("advisory_candidate_id")
    rejected = set(output.get("rejected_candidate_ids", [])) if isinstance(
        output.get("rejected_candidate_ids"), list
    ) else set()
    selection_agreement = _agreement(
        advisory, expected.get("advisory_candidate_id")
    )
    rejected_all = unsupported.issubset(rejected)
    selected_supported = advisory in supported
    authority = _authority_preserved(case, output)
    return {
        "advisory_judgment_agreement": _agreement(
            output.get("decision"),
            expected.get("decision"),
        ),
        "supported_candidate_agreement": 1.0
        if selected_supported and selection_agreement == 1.0
        else 0.0,
        "unsupported_candidate_rejection": 1.0 if rejected_all else 0.0,
        "winner_agreement": selection_agreement,
        "task_quality_passed": (
            selected_supported
            and selection_agreement == 1.0
            and rejected_all
            and authority
        ),
    }


def _grade_manual_scan(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    options = output.get("options")
    options = options if isinstance(options, list) else []
    supported = _normalized_set(case.get("supported_evidence_tokens"))
    prohibited = _normalized_set(case.get("prohibited_claims_or_terms"))
    observed: set[str] = set()
    for option in options:
        if isinstance(option, dict):
            observed |= _normalized_set(option.get("terms"))
    unsupported = observed - supported
    prohibited_present = observed & prohibited
    containment = supported.issubset(observed)
    manual = (
        output.get("manual_only") is True
        and output.get("can_accept_directly") is False
    )
    return {
        "supported_term_containment": 1.0 if containment else 0.0,
        "prohibited_term_absence": 1.0 if not prohibited_present else 0.0,
        "unsupported_claim_count": len(unsupported | prohibited_present),
        "manual_only_authority": 1.0 if manual else 0.0,
        "task_quality_passed": (
            bool(options)
            and containment
            and not unsupported
            and not prohibited_present
            and manual
        ),
    }


def _grade_manual_preview(
    case: Mapping[str, Any],
    output: Mapping[str, Any],
) -> Dict[str, Any]:
    unsupported = _unsupported_claims(case, output)
    advisory = (
        output.get("preview_status") == "advisory"
        and output.get("manual_only") is True
    )
    authority = _authority_preserved(case, output)
    return {
        "advisory_manual_only_status": 1.0 if advisory else 0.0,
        "evidence_support": 1.0 if not unsupported else 0.0,
        "unsupported_claim_count": len(unsupported),
        "no_mutation_or_action_authority": 1.0 if authority else 0.0,
        "task_quality_passed": advisory and not unsupported and authority,
    }


_GRADERS = {
    "skill_extraction": _grade_skill_extraction,
    "job_fit_evaluation": _grade_job_fit,
    "jd_intelligence": _grade_jd_intelligence,
    "grounded_rag_answer": _grade_rag,
    "resume_fallback_ranking": _grade_resume_ranking,
    "ambiguous_resume_adjudication": _grade_adjudication,
    "critic_evaluation": _grade_critic,
    "tailoring_generation": _grade_tailoring_generation,
    "tailoring_refinement": _grade_tailoring_refinement,
    "tailoring_judge": _grade_tailoring_judge,
    "manual_scan_phrase": _grade_manual_scan,
    "manual_provider_preview": _grade_manual_preview,
}


def grade_normalized_candidate_result(
    packet: Dict[str, Any],
    *,
    corpus: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Grade one normalized result using only deterministic case evidence."""

    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    validate_normalized_candidate_result(packet, corpus=payload)
    case = _case_by_id(payload)[packet["case_id"]]
    output = deepcopy(packet["normalized_output"])
    unsupported = _unsupported_claims(case, output)
    completeness = _required_field_completeness(
        output, case["required_fields"]
    )
    authority = _authority_preserved(case, output)
    workload_metrics = _GRADERS[case["workload_id"]](case, output)
    workload_unsupported_count = max(
        int(workload_metrics.get(metric_id, 0))
        for metric_id in (
            "unsupported_claim_count",
            "unsupported_skill_count",
            "unsupported_signal_count",
            "unsupported_addition_count",
            "invented_content_count",
        )
    )
    unsupported_count = max(
        len(unsupported),
        workload_unsupported_count,
    )
    sensitive_count = _sensitive_data_count(output)

    hard_failures = {failure_id: 0 for failure_id in HARD_FAILURE_ORDER}
    hard_failures["schema_invalid_result_accepted"] = int(
        not packet["schema_valid"]
    )
    hard_failures["unsupported_claim"] = unsupported_count
    hard_failures["hallucination"] = unsupported_count
    hard_failures["sensitive_data_leakage"] = sensitive_count
    hard_failures["deterministic_authority_mutation"] = int(not authority)
    hard_failures["ranking_mutation"] = int(
        case["workload_id"] == "resume_fallback_ranking" and not authority
    )
    hard_failures["selected_resume_mutation"] = int(
        case["workload_id"]
        in {
            "resume_fallback_ranking",
            "ambiguous_resume_adjudication",
        }
        and not authority
    )
    hard_failures["provider_called_while_disabled"] = packet[
        "provider_call_count"
    ]
    hard_failures["silent_cross_provider_fallback"] = int(
        packet["fallback_used"]
    )
    hard_failures["persisted_raw_response"] = int(
        packet["raw_response_persisted"]
    )
    hard_failures["application_action_reached"] = packet[
        "application_action_count"
    ]
    hard_failures["ats_action_reached"] = packet["ats_action_count"]

    grounded_precision = workload_metrics.get("grounded_evidence_precision")
    if grounded_precision is None:
        claim_count = len(_claim_terms(output))
        grounded_precision = _rate(
            claim_count - unsupported_count,
            claim_count,
        )
    quality_gate_passed = (
        all(value == 0 for value in hard_failures.values())
        and packet["schema_valid"]
        and packet["normalization_succeeded"]
        and completeness == 1.0
        and authority
        and bool(workload_metrics.get("task_quality_passed"))
    )
    return {
        "case_id": case["case_id"],
        "workload_id": case["workload_id"],
        "provider": packet["provider"],
        "model": packet["model"],
        "schema_valid_response": 1.0 if packet["schema_valid"] else 0.0,
        "normalization_success": 1.0
        if packet["normalization_succeeded"]
        else 0.0,
        "required_field_completeness": completeness,
        "grounded_evidence_precision": grounded_precision,
        "unsupported_claim_count": unsupported_count,
        "hallucination_count": unsupported_count,
        "deterministic_authority_preservation": 1.0
        if authority
        else 0.0,
        "winner_agreement": workload_metrics.get("winner_agreement"),
        "ranking_agreement": workload_metrics.get("ranking_agreement"),
        "skill_extraction_precision": workload_metrics.get(
            "skill_extraction_precision"
        ),
        "skill_extraction_recall": workload_metrics.get(
            "skill_extraction_recall"
        ),
        "missing_requirement_accuracy": workload_metrics.get(
            "missing_requirement_accuracy"
        ),
        "tailoring_evidence_support": workload_metrics.get(
            "tailoring_evidence_support"
        ),
        "critic_agreement": workload_metrics.get("critic_agreement"),
        "workload_metrics": deepcopy(workload_metrics),
        "hard_failures": hard_failures,
        "quality_gate_passed": quality_gate_passed,
        "cost_comparison_eligible": (
            quality_gate_passed
            and all(
                field in packet
                for field in (
                    "input_token_count",
                    "output_token_count",
                    "estimated_cost",
                )
            )
        ),
        "latency_comparison_eligible": (
            quality_gate_passed and "latency_ms" in packet
        ),
        "live_evidence_required": True,
    }


def build_synthetic_expected_result_packets(
    *,
    provider: str = "groq",
    model: str = "openai/gpt-oss-20b",
    corpus: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Create offline-only normalized packets from sanitized exact goldens."""

    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    validate_fixture_case_corpus(payload)
    _require(
        (provider, model) in MODEL_ORDER,
        "unsupported provider/model result pair",
    )
    packets = []
    for case in payload["cases"]:
        if case["comparison_type"] == "coverage_gap":
            continue
        _require(
            bool(case["expected_output"]),
            "synthetic packet construction requires an expected output",
        )
        packets.append(
            {
                "case_id": case["case_id"],
                "workload_id": case["workload_id"],
                "provider": provider,
                "model": model,
                "normalized_output": deepcopy(case["expected_output"]),
                "schema_valid": True,
                "normalization_succeeded": True,
                "fallback_used": False,
                "provider_call_count": 0,
                "mutation_count": 0,
                "application_action_count": 0,
                "ats_action_count": 0,
                "raw_response_persisted": False,
                "live_execution": False,
            }
        )
    return packets


def _aggregate_observable_metrics(
    grades: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {
        "provider_call_success_rate": _NOT_OBSERVED_OFFLINE,
        "schema_valid_response_rate": _average(
            grade["schema_valid_response"] for grade in grades
        ),
        "normalization_success_rate": _average(
            grade["normalization_success"] for grade in grades
        ),
        "grounded_evidence_precision": _average(
            grade["grounded_evidence_precision"] for grade in grades
        ),
        "unsupported_claim_count": sum(
            int(grade["unsupported_claim_count"]) for grade in grades
        ),
        "hallucination_count": sum(
            int(grade["hallucination_count"]) for grade in grades
        ),
        "required_field_completeness": _average(
            grade["required_field_completeness"] for grade in grades
        ),
        "deterministic_authority_preservation": _average(
            grade["deterministic_authority_preservation"] for grade in grades
        ),
        "winner_agreement": _average(
            grade["winner_agreement"]
            for grade in grades
            if grade["winner_agreement"] is not None
        ),
        "ranking_agreement": _average(
            grade["ranking_agreement"]
            for grade in grades
            if grade["ranking_agreement"] is not None
        ),
        "skill_extraction_precision": _average(
            grade["skill_extraction_precision"]
            for grade in grades
            if grade["skill_extraction_precision"] is not None
        ),
        "skill_extraction_recall": _average(
            grade["skill_extraction_recall"]
            for grade in grades
            if grade["skill_extraction_recall"] is not None
        ),
        "missing_requirement_accuracy": _average(
            grade["missing_requirement_accuracy"]
            for grade in grades
            if grade["missing_requirement_accuracy"] is not None
        ),
        "tailoring_evidence_support": _average(
            grade["tailoring_evidence_support"]
            for grade in grades
            if grade["tailoring_evidence_support"] is not None
        ),
        "critic_agreement": _average(
            grade["critic_agreement"]
            for grade in grades
            if grade["critic_agreement"] is not None
        ),
        "latency_ms": _NOT_OBSERVED_OFFLINE,
        "input_token_count": _NOT_OBSERVED_OFFLINE,
        "output_token_count": _NOT_OBSERVED_OFFLINE,
        "estimated_cost": _NOT_OBSERVED_OFFLINE,
        "cache_hit_count": _NOT_OBSERVED_OFFLINE,
        "timeout_count": _NOT_OBSERVED_OFFLINE,
        "retry_count": _NOT_OBSERVED_OFFLINE,
        "rate_limit_count": _NOT_OBSERVED_OFFLINE,
        "fallback_activation_count": 0,
        "fallback_correctness": _NOT_APPLICABLE_FALLBACK,
        "duplicate_call_count": 0,
        "persisted_raw_response_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
    }
    return {metric_id: metrics[metric_id] for metric_id in METRIC_ORDER}


def evaluate_offline_fixture_benchmark(
    result_packets: Sequence[Dict[str, Any]],
    *,
    corpus: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Grade normalized packets and return a deterministic in-memory summary."""

    payload = load_fixture_case_corpus() if corpus is None else deepcopy(corpus)
    validate_fixture_case_corpus(payload)
    _require(
        isinstance(result_packets, (list, tuple)) and bool(result_packets),
        "normalized candidate results are required",
    )
    packets = [deepcopy(packet) for packet in result_packets]
    identities = [
        (
            packet.get("case_id"),
            packet.get("provider"),
            packet.get("model"),
        )
        for packet in packets
        if isinstance(packet, dict)
    ]
    _require(
        len(identities) == len(set(identities)),
        "duplicate candidate result packet",
    )
    grades = [
        grade_normalized_candidate_result(packet, corpus=payload)
        for packet in packets
    ]
    coverage = fixture_case_coverage_summary(payload)
    per_workload = []
    for workload_id in WORKLOAD_ORDER:
        workload_grades = [
            grade for grade in grades if grade["workload_id"] == workload_id
        ]
        per_workload.append(
            {
                "workload_id": workload_id,
                "observed_result_count": len(workload_grades),
                "quality_gate_passed": bool(workload_grades)
                and all(
                    grade["quality_gate_passed"]
                    for grade in workload_grades
                ),
                "metrics": _aggregate_observable_metrics(workload_grades)
                if workload_grades
                else None,
            }
        )
    hard_failures = {
        failure_id: sum(
            int(grade["hard_failures"][failure_id]) for grade in grades
        )
        for failure_id in HARD_FAILURE_ORDER
    }
    coverage_sufficient = (
        coverage["coverage_gap_count"] == 0
        and all(
            row["machine_readable_case_count"] > 0
            for row in coverage["workloads"]
        )
    )
    quality_gate_passed = all(
        grade["quality_gate_passed"] for grade in grades
    ) and all(value == 0 for value in hard_failures.values())
    result = {
        "contract_version": FIXTURE_BENCHMARK_VERSION,
        "fixture_corpus_sha256": fixture_case_corpus_sha256(payload),
        "benchmark_engine_sha256": provider_fixture_benchmark_sha256(
            build_provider_fixture_benchmark_contract(payload)
        ),
        "candidate_result_count": len(grades),
        "case_grades": grades,
        "coverage_summary": coverage,
        "per_workload": per_workload,
        "metrics": _aggregate_observable_metrics(grades),
        "hard_failures": hard_failures,
        "hard_failures_all_zero": all(
            value == 0 for value in hard_failures.values()
        ),
        "quality_gate_passed": quality_gate_passed,
        "cost_comparison_eligible": (
            quality_gate_passed
            and all(grade["cost_comparison_eligible"] for grade in grades)
        ),
        "latency_comparison_eligible": (
            quality_gate_passed
            and all(
                grade["latency_comparison_eligible"] for grade in grades
            )
        ),
        "coverage_sufficient": coverage_sufficient,
        "live_evidence_required": True,
        "authority_invariants": {
            "deterministic_authority_preserved": all(
                grade["deterministic_authority_preservation"] == 1.0
                for grade in grades
            ),
            "provider_call_count": 0,
            "fallback_activation_count": 0,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "raw_response_persisted_count": 0,
            "live_execution": False,
        },
    }
    validate_offline_fixture_benchmark_result(result)
    return deepcopy(result)


def validate_offline_fixture_benchmark_result(
    result: Dict[str, Any],
) -> bool:
    _require(isinstance(result, dict), "benchmark result must be an object")
    _require(
        result.get("contract_version") == FIXTURE_BENCHMARK_VERSION,
        "benchmark result version mismatch",
    )
    _require(
        result.get("metrics", {}).get("provider_call_success_rate")
        == _NOT_OBSERVED_OFFLINE,
        "provider call success must remain unobserved offline",
    )
    for metric_id in (
        "latency_ms",
        "input_token_count",
        "output_token_count",
        "estimated_cost",
        "timeout_count",
        "retry_count",
        "rate_limit_count",
        "cache_hit_count",
    ):
        _require(
            result.get("metrics", {}).get(metric_id)
            == _NOT_OBSERVED_OFFLINE,
            f"{metric_id} must remain unobserved offline",
        )
    _require(
        result.get("metrics", {}).get("fallback_activation_count") == 0,
        "fallback activation must remain zero",
    )
    _require(
        result.get("metrics", {}).get("fallback_correctness")
        == _NOT_APPLICABLE_FALLBACK,
        "fallback correctness must remain not applicable",
    )
    authority = result.get("authority_invariants")
    _require(
        isinstance(authority, dict)
        and authority.get("provider_call_count") == 0
        and authority.get("fallback_activation_count") == 0
        and authority.get("mutation_count") == 0
        and authority.get("application_action_count") == 0
        and authority.get("ats_action_count") == 0
        and authority.get("raw_response_persisted_count") == 0
        and authority.get("live_execution") is False,
        "offline authority invariants changed",
    )
    serialized = _canonical_json(result).lower()
    for forbidden_field in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
    ):
        _require(
            forbidden_field not in serialized,
            "model selection fields are prohibited",
        )
    return True


def serialize_offline_fixture_benchmark_result(
    result: Dict[str, Any],
) -> str:
    payload = deepcopy(result)
    validate_offline_fixture_benchmark_result(payload)
    return _canonical_json(payload)


def offline_fixture_benchmark_result_sha256(
    result: Dict[str, Any],
) -> str:
    return sha256(
        serialize_offline_fixture_benchmark_result(result).encode("utf-8")
    ).hexdigest()

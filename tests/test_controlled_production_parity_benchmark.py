from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.evaluation import controlled_production_parity_benchmark as parity
from src.evaluation.controlled_groq_canary_transport import (
    build_groq_production_parity_chat_completion_arguments,
)
from src.evaluation.controlled_openai_canary_transport import (
    build_openai_production_parity_chat_completion_arguments,
)
from src.evaluation.controlled_provider_benchmark_human_review import (
    canonical_human_review_requirements,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)
from src.evaluation.production_task_contract_fingerprints import (
    build_production_task_contract,
    production_task_contract_sha256,
)
from src.evaluation.provider_benchmark_contract import WORKLOAD_ORDER


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / "src/evaluation/controlled_production_parity_benchmark.py"
RUNNABLE = (
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
BLOCKED = ()
EXPECTED_MODES = {
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


@pytest.fixture(scope="module")
def plan():
    return build_controlled_provider_benchmark_plan()


def _row(plan, workload_id, provider="groq"):
    return next(
        row
        for row in plan["staged_matrix"]
        if row["workload_id"] == workload_id and row["provider"] == provider
    )


def _request(plan, workload_id, provider="groq"):
    row = _row(plan, workload_id, provider)
    packet = build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=plan,
    )
    return parity.build_production_parity_request(packet, plan=plan)


def _scheduled(plan, workload_id, provider="groq"):
    row = _row(plan, workload_id, provider)
    return {
        **row,
        "fallback": False,
        "harness_retry_limit": 0,
        "provider_sdk_retry_limit": 0,
    }


def _valid_response(workload_id):
    return {
        "skill_extraction": {
            "required_skills": ["python", "sql"],
            "preferred_skills": ["airflow"],
        },
        "job_fit_evaluation": {
            "results": [
                {
                    "id": 0,
                    "ai_relevance": 7,
                    "skill_match": 5,
                    "seniority_match": 7,
                    "learning_opportunity": 9,
                    "overall_score": 7,
                    "visa_sponsorship_signal": "unknown",
                    "reason": (
                        "synthetic_skill_alpha and synthetic_workflow_signal "
                        "with missing synthetic_skill_beta"
                    ),
                }
            ]
        },
        "jd_intelligence": {
            "required_skills": ["python", "sql"],
            "preferred_skills": ["dbt"],
            "required_tools": [],
            "preferred_tools": [],
            "workflows": ["analytics"],
            "methods": [],
            "business_contexts": [],
            "stakeholder_contexts": [],
            "ownership_signals": [],
            "seniority_signals": [],
            "risk_flags": [],
            "extraction_confidence": 0.9,
        },
        "grounded_rag_answer": {
            "answer": (
                "synthetic_capability_alpha is supported by the evidence. [S1]"
            ),
            "insufficient_evidence": False,
            "used_source_ids": ["S1"],
            "job_evidence": [
                {
                    "source_id": "S1",
                    "evidence_points": ["synthetic_capability_alpha"],
                }
            ],
        },
        "resume_fallback_ranking": {
            "best_resume": "candidate_alpha",
            "best_score": 0.8,
            "backup_resume": "candidate_beta",
            "backup_score": 0.4,
            "confidence": "low",
            "reason": (
                "Best available imperfect match. Major remaining gaps: "
                "synthetic_requirement_gap."
            ),
        },
        "ambiguous_resume_adjudication": {
            "adjudicator_summary": (
                "Candidate alpha has stronger Python and SQL evidence; "
                "candidate beta has reporting evidence and a synthetic "
                "requirement gap."
            ),
            "adjudicator_recommendation_label": "Review candidate alpha first",
        },
        "critic_evaluation": {
            "critic_status": "approved",
            "approved_suggestions": [
                {
                    "suggestion_id": "suggestion_alpha",
                    "decision": "approve",
                    "confidence": 0.9,
                    "reason_codes": ["evidence_supported"],
                    "evidence_spans": ["synthetic_capability_alpha"],
                    "original_patch_ready": True,
                    "final_patch_ready": True,
                }
            ],
            "downgraded_suggestions": [],
            "rejected_suggestions": [],
            "reason_codes": ["evidence_supported"],
            "unsupported_claim_risks": [],
            "ats_risks": [],
            "readability_risks": [],
            "evidence_gaps": [],
            "confidence": 0.9,
            "rationale": "The synthetic evidence supports the suggestion.",
        },
        "tailoring_generation": {
            "rewrite_directions": [
                {
                    "prefix": "Lead with",
                    "source": "synthetic_source",
                    "direction": (
                        "Lead with python sql and airflow evidence for supported "
                        "delivery outcomes"
                    ),
                },
                {
                    "prefix": "Support with",
                    "source": "synthetic_source",
                    "direction": (
                        "Support with airflow workflow evidence while preserving "
                        "the original scope"
                    ),
                },
                {
                    "prefix": "Keep gap explicit",
                    "source": "",
                    "direction": (
                        "Keep the unsupported requirement gap explicit for manual review"
                    ),
                },
            ]
        },
        "tailoring_refinement": (
            "OPTION_1: Improved sql reporting by 10% using sql and reporting "
            "for supported delivery."
        ),
        "tailoring_judge": (
            "WINNER: writer_option_1\n"
            "REASON: supported by the synthetic evidence\n"
            "REJECTED: writer_option_2\n"
            "QUALITY_FLAGS: none\n"
            "SCORE_INTENT: improve alignment\n"
            "EXPECTED_DIMENSIONS: evidence\n"
            "RISK_FLAGS: none"
        ),
        "manual_scan_phrase": {
            "options": [
                {
                    "text": (
                        "Delivered SQL reporting through bounded synthetic work "
                        "with clearer impact."
                    ),
                    "reason": "Supported synthetic rewrite.",
                    "supported_terms": ["sql", "reporting"],
                    "risk_flags": [],
                }
            ]
        },
        "manual_provider_preview": {
            "preview_status": "advisory",
            "manual_only": True,
            "suggestions": [
                {
                    "suggestion_id": "suggestion_alpha",
                    "source_evidence_ids": ["evidence_alpha"],
                    "preview_text": (
                        "Delivered python evidence in the bounded synthetic context."
                    ),
                    "claims": ["python"],
                    "rationale": "Uses only the authorized synthetic evidence.",
                    "risk_flags": [],
                }
            ],
            "resume_mutation_authorized": False,
            "automatic_acceptance_authorized": False,
            "application_mutation_authorized": False,
            "auto_apply_authorized": False,
            "auto_submit_authorized": False,
        },
    }[workload_id]


def test_all_twelve_workloads_are_production_parity_runnable():
    runnability = parity.build_production_parity_runnability()

    assert len(WORKLOAD_ORDER) == len(runnability) == 12
    assert tuple(runnability) == WORKLOAD_ORDER
    assert parity.PRODUCTION_PARITY_RUNNABLE_WORKLOADS == RUNNABLE
    assert parity.PRODUCTION_PARITY_BLOCKED_WORKLOADS == BLOCKED
    assert tuple(
        key
        for key, value in runnability.items()
        if value["status"] == "production_parity_runnable"
    ) == RUNNABLE
    assert tuple(
        key
        for key, value in runnability.items()
        if value["status"] == "blocked_pending_contract_resolution"
    ) == BLOCKED


def test_manual_preview_parity_is_bounded_grounded_and_preview_only(plan):
    request = _request(plan, "manual_provider_preview")
    result = parity.validate_and_grade_production_parity_response(
        request,
        _valid_response("manual_provider_preview"),
        plan=plan,
    )

    assert request["response_contract"]["mode"] == "structured_json"
    assert request["fallback"] is False
    assert result["production_contract_valid"] is True
    assert result["benchmark_quality"]["quality_gate_passed"] is True
    assert result["benchmark_projection"] == {
        "preview_status": "advisory",
        "manual_only": True,
        "claims": ["python"],
        "mutation_authorized": False,
        "application_authorized": False,
        "ats_authorized": False,
    }
    assert result["authority_invariants"]["provider_call_count"] == 0
    assert result["authority_invariants"]["qualification_status_promoted"] is False


def test_manual_preview_parity_projects_grounded_natural_language_claims(
    plan,
):
    request = _request(plan, "manual_provider_preview")
    response = _valid_response("manual_provider_preview")
    response["suggestions"][0]["claims"] = [
        "Delivered python"
    ]

    result = parity.validate_and_grade_production_parity_response(
        request,
        response,
        plan=plan,
    )

    assert result["production_contract_valid"] is True
    assert result["benchmark_projection"]["claims"] == ["python"]
    assert result["benchmark_quality"]["unsupported_claim_count"] == 0
    assert result["benchmark_quality"]["quality_gate_passed"] is True


def test_manual_preview_parity_preserves_unsupported_benchmark_claim_tokens(
    plan,
):
    request = _request(plan, "manual_provider_preview")
    response = _valid_response("manual_provider_preview")
    response["suggestions"][0]["claims"] = [
        "Delivered python with kubernetes"
    ]

    result = parity.validate_and_grade_production_parity_response(
        request,
        response,
        plan=plan,
    )

    assert result["production_contract_valid"] is True
    assert result["benchmark_projection"]["claims"] == [
        "python",
        "kubernetes",
    ]
    assert result["benchmark_quality"]["quality_gate_passed"] is False
    assert (
        result["benchmark_quality"]["hard_failures"]["unsupported_claim"]
        == 1
    )
    assert (
        result["benchmark_quality"]["hard_failures"]["hallucination"]
        == 1
    )


def test_manual_preview_parity_rejects_stale_fingerprint_and_action_authority(
    plan,
):
    request = _request(plan, "manual_provider_preview")
    stale = deepcopy(request)
    stale["production_task_contract_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="stale or mismatched"):
        parity.validate_production_parity_request(stale, plan=plan)

    unsafe = _valid_response("manual_provider_preview")
    unsafe["auto_apply_authorized"] = True
    result = parity.validate_and_grade_production_parity_response(
        request,
        unsafe,
        plan=plan,
    )
    assert result["production_contract_valid"] is False
    assert result["benchmark_quality"]["quality_gate_passed"] is False


def test_ambiguous_parity_uses_exact_readback_prompt_and_candidate_payload(plan):
    from src.agents import llm_adjudicator_readback

    request = _request(plan, "ambiguous_resume_adjudication")
    contract = build_production_task_contract("ambiguous_resume_adjudication")
    candidates = request["local_validation_context"]["candidates"]

    assert request["messages"] == llm_adjudicator_readback._provider_prompt(
        candidates
    )
    assert request["messages"][0]["content"] == contract["prompt_contract"]["system"]
    assert request["response_contract"]["mode"] == "json_text"
    assert request["task_parameters"]["fallback_enabled"] is False


def test_ambiguous_production_validity_is_separate_from_readback_quality(plan):
    request = _request(plan, "ambiguous_resume_adjudication")
    result = parity.validate_and_grade_production_parity_response(
        request,
        {
            "adjudicator_summary": (
                "Candidate gamma adds Kubernetes production ownership."
            ),
            "adjudicator_recommendation_label": "Review candidate gamma first",
        },
        plan=plan,
    )

    assert result["production_contract_valid"] is True
    assert result["benchmark_quality"]["quality_gate_passed"] is False
    assert result["benchmark_quality"]["hard_failures"]["unsupported_claim"] >= 1
    assert result["benchmark_quality"]["hard_failures"]["hallucination"] >= 1


@pytest.mark.parametrize("raw_response", [{}, "not-json", "{}"])
def test_ambiguous_malformed_or_empty_readback_fails_production_contract(
    plan,
    raw_response,
):
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "ambiguous_resume_adjudication"),
        raw_response,
        plan=plan,
    )

    assert result["production_contract_valid"] is False
    assert result["benchmark_quality"]["quality_gate_passed"] is False


@pytest.mark.parametrize("workload_id", BLOCKED)
def test_unresolved_workload_cannot_build_a_parity_request(plan, workload_id):
    row = _row(plan, workload_id)
    packet = build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=plan,
    )
    with pytest.raises(parity.ProductionParityBlocked, match="blocked pending"):
        parity.build_production_parity_request(packet, plan=plan)


@pytest.mark.parametrize("workload_id", RUNNABLE)
def test_request_is_bound_to_current_production_contract_and_response_mode(
    plan,
    workload_id,
):
    request = _request(plan, workload_id)
    contract = build_production_task_contract(workload_id)

    assert request["production_task_contract_sha256"] == (
        production_task_contract_sha256(workload_id)
    )
    assert request["response_contract"]["mode"] == EXPECTED_MODES[workload_id]
    assert request["response_contract"]["production_output_contract"] == (
        contract["output_contract"]
    )
    assert request["task_parameters"] == contract["task_parameters"]
    assert request["fallback"] is False
    assert request["retry_limit"] == 0
    assert request["live_execution_requested"] is False
    assert request["synthetic_data_only"] is True


def test_request_uses_owner_prompt_material_without_a_copied_prompt_corpus(plan):
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assigned_strings = [
        node.value.value
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    assert not any("You generate evidence-anchored" in value for value in assigned_strings)
    assert not any("You evaluate data, machine learning" in value for value in assigned_strings)
    assert "build_production_task_contract(workload_id)" in source

    request = _request(plan, "skill_extraction")
    contract = build_production_task_contract("skill_extraction")
    replacements = request["local_validation_context"]["replacements"]
    assert request["messages"][0]["content"] == contract["prompt_contract"]["system"]
    assert request["messages"][1]["content"] == parity._replace_text(
        contract["prompt_contract"]["primary_user_template"],
        replacements,
    )


def test_arbitrary_or_stale_task_fingerprint_fails_closed(plan):
    row = _row(plan, "skill_extraction")
    packet = build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=plan,
    )
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        parity.build_production_parity_request(
            packet,
            plan=plan,
            expected_task_contract_sha256="0" * 64,
        )

    request = parity.build_production_parity_request(packet, plan=plan)
    request["production_task_contract_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="stale or mismatched"):
        parity.validate_production_parity_request(request, plan=plan)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        (
            lambda request: request["messages"][1].update(
                content="tampered synthetic prompt"
            ),
            "prompt contract mismatch",
        ),
        (
            lambda request: request["task_parameters"].update(max_tokens=1),
            "task parameters mismatch",
        ),
        (
            lambda request: request["response_contract"].update(schema={}),
            "response mode mismatch",
        ),
        (
            lambda request: request["local_validation_context"].update(
                synthetic_input={}
            ),
            "synthetic context mismatch",
        ),
    ],
)
def test_request_semantics_cannot_be_tampered_under_a_current_fingerprint(
    plan,
    mutation,
    expected_error,
):
    request = _request(plan, "jd_intelligence")
    mutation(request)

    with pytest.raises(ValueError, match=expected_error):
        parity.validate_production_parity_request(request, plan=plan)


@pytest.mark.parametrize("workload_id", RUNNABLE)
def test_production_parser_validator_and_benchmark_quality_both_pass(
    plan,
    workload_id,
):
    request = _request(plan, workload_id)
    result = parity.validate_and_grade_production_parity_response(
        request,
        _valid_response(workload_id),
        plan=plan,
    )

    assert result["production_contract_valid"] is True
    assert result["production_validation_errors"] == []
    assert result["benchmark_quality"]["quality_gate_passed"] is True
    assert not any(result["benchmark_quality"]["hard_failures"].values())
    assert result["production_task_contract_sha256"] == (
        request["production_task_contract_sha256"]
    )
    assert len(result["evidence_binding_sha256"]) == 64
    assert result["authority_invariants"]["qualification_status_promoted"] is False


def test_skill_parser_and_normalizer_use_production_bucket_semantics(plan):
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "skill_extraction"),
        _valid_response("skill_extraction"),
        plan=plan,
    )
    assert result["production_normalized_output"] == {
        "required_skills": ["python", "sql"],
        "preferred_skills": ["airflow"],
    }


def test_job_fit_production_result_structure_and_defaults_are_represented(plan):
    response = {"results": [{"id": 0, "overall_score": 7}]}
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "job_fit_evaluation"),
        response,
        plan=plan,
    )
    normalized = result["production_normalized_output"]["results"][0]
    assert normalized["ai_relevance"] == 0
    assert normalized["visa_sponsorship_signal"] == "unknown"
    assert normalized["reason"] == "No explanation"


def test_jd_and_critic_strict_schemas_are_the_production_schemas(plan):
    for workload_id in ("jd_intelligence", "critic_evaluation"):
        request = _request(plan, workload_id)
        contract = build_production_task_contract(workload_id)
        assert request["response_contract"] == {
            "mode": "structured_json",
            "schema_name": contract["output_contract"]["schema_name"],
            "strict": True,
            "schema": contract["output_contract"]["schema"],
            "production_output_contract": contract["output_contract"],
        }


def test_grounded_rag_reuses_production_citation_and_insufficient_rules(plan):
    response = deepcopy(_valid_response("grounded_rag_answer"))
    response["answer"] = "synthetic_capability_alpha without a valid citation"
    response["used_source_ids"] = []
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "grounded_rag_answer"),
        response,
        plan=plan,
    )
    assert result["production_contract_valid"] is True
    assert result["production_normalized_output"]["insufficient_evidence"] is True
    assert result["production_normalized_output"]["used_source_ids"] == []


def test_resume_candidate_allowlist_and_score_handling_are_production_owned(plan):
    response = deepcopy(_valid_response("resume_fallback_ranking"))
    response["best_resume"] = "candidate_not_allowed"
    response["best_score"] = 9
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "resume_fallback_ranking"),
        response,
        plan=plan,
    )
    assert result["production_contract_valid"] is False
    assert result["production_normalized_output"] == {}


def test_generation_rejects_unknown_production_source(plan):
    response = deepcopy(_valid_response("tailoring_generation"))
    response["rewrite_directions"][0]["source"] = "unknown_source"
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "tailoring_generation"),
        response,
        plan=plan,
    )
    assert result["production_contract_valid"] is False


def test_refinement_and_judge_remain_plain_text_not_generic_json(plan):
    for workload_id in ("tailoring_refinement", "tailoring_judge"):
        request = _request(plan, workload_id)
        assert request["response_contract"]["mode"] == "plain_text"
        assert request["response_contract"]["schema"] is None
        assert request["response_contract"]["strict"] is False
        result = parity.validate_and_grade_production_parity_response(
            request,
            _valid_response(workload_id),
            plan=plan,
        )
        assert result["production_contract_valid"] is True


def test_refinement_option_validation_rejects_unsupported_content(plan):
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "tailoring_refinement"),
        "OPTION_1: Invented kubernetes ownership without preserved evidence.",
        plan=plan,
    )
    assert result["production_contract_valid"] is False


def test_judge_parser_allowlists_decisions_and_preserves_abstain(plan):
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "tailoring_judge"),
        "WINNER: invented_winner\nREASON: invalid",
        plan=plan,
    )
    assert result["production_contract_valid"] is True
    assert result["production_normalized_output"]["winner"] == "abstain"


def test_scan_phrase_uses_production_option_validation(plan):
    response = deepcopy(_valid_response("manual_scan_phrase"))
    response["options"][0]["text"] = "Using SQL reporting for synthetic work."
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "manual_scan_phrase"),
        response,
        plan=plan,
    )
    assert result["production_contract_valid"] is False


def test_production_validity_is_separate_from_benchmark_quality(plan):
    response = deepcopy(_valid_response("grounded_rag_answer"))
    response["answer"] = "invented_capability is supported. [S1]"
    response["job_evidence"][0]["evidence_points"] = ["invented_capability"]
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "grounded_rag_answer"),
        response,
        plan=plan,
    )
    assert result["production_contract_valid"] is True
    assert result["benchmark_quality"]["quality_gate_passed"] is False
    assert result["production_validation_errors"] == []


def test_existing_hard_failure_grader_remains_effective(plan):
    response = deepcopy(_valid_response("grounded_rag_answer"))
    response["answer"] = "kubernetes is supported. [S1]"
    response["job_evidence"][0]["evidence_points"] = ["kubernetes"]
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "grounded_rag_answer"),
        response,
        plan=plan,
    )
    assert result["benchmark_quality"]["hard_failures"]["unsupported_claim"] == 1
    assert result["benchmark_quality"]["hard_failures"]["hallucination"] == 1


def test_evidence_binding_tampering_fails_closed(plan):
    request = _request(plan, "critic_evaluation")
    result = parity.validate_and_grade_production_parity_response(
        request,
        _valid_response("critic_evaluation"),
        plan=plan,
    )
    result["benchmark_projection"]["decision"] = "reject"
    with pytest.raises(ValueError, match="evidence binding mismatch"):
        parity.validate_production_parity_result(result, request=request, plan=plan)


@pytest.mark.parametrize(
    ("provider", "workload_id", "has_response_format"),
    [
        ("groq", "jd_intelligence", True),
        ("groq", "tailoring_refinement", False),
        ("openai", "critic_evaluation", True),
        ("openai", "tailoring_judge", False),
        ("groq", "ambiguous_resume_adjudication", False),
        ("openai", "ambiguous_resume_adjudication", False),
    ],
)
def test_transports_support_structured_and_plain_text_without_fallback_or_retry(
    plan,
    provider,
    workload_id,
    has_response_format,
):
    request = _request(plan, workload_id, provider)
    scheduled = _scheduled(plan, workload_id, provider)
    builder = (
        build_groq_production_parity_chat_completion_arguments
        if provider == "groq"
        else build_openai_production_parity_chat_completion_arguments
    )
    arguments = builder(
        parity_request=request,
        scheduled=scheduled,
        plan=plan,
    )
    assert ("response_format" in arguments) is has_response_format
    assert arguments["messages"] == request["messages"]
    assert arguments["max_completion_tokens"] == request["task_parameters"]["max_tokens"]
    assert request["fallback"] is False
    assert request["retry_limit"] == 0


def test_adapter_imports_no_sdk_environment_or_credential_owner():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(
        {"openai", "groq", "requests", "httpx", "os", "dotenv"}
    )
    for prohibited in (
        "OPENAI_API_KEY",
        "GROQ_API_KEY",
        "getenv(",
        "environ",
        "create_live_",
        "run_chat_completion",
        "database",
        "cache_set",
        "write_text",
        "write_bytes",
    ):
        assert prohibited not in source


def test_44_cell_plan_counts_default_off_and_human_review_are_unchanged(plan):
    counts = plan["request_counts"]["maximum_requests_per_model"]
    assert len(plan["staged_matrix"]) == 44
    assert counts == {
        "groq/openai/gpt-oss-20b": 12,
        "groq/openai/gpt-oss-120b": 10,
        "openai/gpt-5-mini": 12,
        "openai/gpt-5.1": 10,
    }
    assert plan["authority_invariants"]["live_execution_authorized"] is False
    assert plan["authority_invariants"]["provider_calls_allowed"] is False
    requirements = canonical_human_review_requirements()
    assert tuple(requirements) == WORKLOAD_ORDER
    assert {workload_id for workload_id, required in requirements.items() if required} == {
        "jd_intelligence",
        "resume_fallback_ranking",
        "critic_evaluation",
        "tailoring_generation",
        "tailoring_refinement",
        "tailoring_judge",
        "manual_scan_phrase",
        "ambiguous_resume_adjudication",
        "manual_provider_preview",
    }


def test_no_result_promotes_qualification_or_creates_routing_authority(plan):
    for workload_id in RUNNABLE:
        result = parity.validate_and_grade_production_parity_response(
            _request(plan, workload_id),
            _valid_response(workload_id),
            plan=plan,
        )
        authority = result["authority_invariants"]
        assert authority["qualification_status_promoted"] is False
        assert authority["recommendation_created"] is False
        assert authority["routing_changed"] is False
        assert authority["user_task_override_created"] is False
        assert authority["provider_call_count"] == 0

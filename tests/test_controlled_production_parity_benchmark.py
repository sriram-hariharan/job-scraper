from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.evaluation import controlled_production_parity_benchmark as parity
from src.evaluation.controlled_groq_canary_transport import (
    build_groq_production_parity_chat_completion_arguments,
    validate_groq_production_parity_chat_completion_arguments,
)
from src.evaluation.controlled_openai_canary_transport import (
    build_openai_production_parity_chat_completion_arguments,
    validate_openai_production_parity_chat_completion_arguments,
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
    "manual_provider_preview": "json_object",
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
                        "Lead with python sql and airflow terms in the opening clause"
                    ),
                },
                {
                    "prefix": "Support with",
                    "source": "synthetic_source",
                    "direction": (
                        "Support with python sql and airflow as supplied evidence"
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


def _job_fit_result(result_id=0, *, missing_field=None, **updates):
    result = deepcopy(
        _valid_response("job_fit_evaluation")["results"][0]
    )
    result["id"] = result_id
    result.update(updates)
    if missing_field is not None:
        result.pop(missing_field)
    return result


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

    assert request["response_contract"]["mode"] == "json_object"
    assert request["response_contract"]["schema"] is None
    assert request["response_contract"]["strict"] is False
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


def test_job_fit_production_result_requires_explicit_complete_fields(plan):
    response = {"results": [{"id": 0, "overall_score": 7}]}
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "job_fit_evaluation"),
        response,
        plan=plan,
    )
    assert result["production_contract_valid"] is False
    assert result["production_validation_errors"] == [
        "production_contract_invalid"
    ]


def test_job_fit_complete_controlled_batch_passes_without_rescoring(plan):
    response = _valid_response("job_fit_evaluation")
    response["results"][0].update(
        {
            "ai_relevance": 6.25,
            "skill_match": 4.5,
            "seniority_match": 7.75,
            "learning_opportunity": 8.125,
            "overall_score": 6.65625,
        }
    )
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "job_fit_evaluation"),
        response,
        plan=plan,
    )

    assert result["production_contract_valid"] is True
    assert result["production_normalized_output"] == response
    assert result["production_normalized_output"]["results"][0][
        "overall_score"
    ] == 6.65625


@pytest.mark.parametrize(
    ("results", "expected_batch_size", "error"),
    [
        ([_job_fit_result(0)], 2, "result count"),
        ([_job_fit_result(0), _job_fit_result(0)], 2, "duplicated"),
        ([_job_fit_result("0")], 1, "not an integer"),
        ([_job_fit_result(True)], 1, "not an integer"),
        ([_job_fit_result(1)], 1, "out of range"),
        ([_job_fit_result(0, missing_field="reason")], 1, "required fields"),
    ],
)
def test_job_fit_completeness_validator_rejects_invalid_batches(
    results,
    expected_batch_size,
    error,
):
    with pytest.raises(ValueError, match=error):
        parity._validate_job_fit_results(
            results,
            expected_batch_size=expected_batch_size,
        )


@pytest.mark.parametrize(
    "response",
    [
        [],
        {"results": "not-a-list"},
        {"results": []},
        {"results": [_job_fit_result(1)]},
    ],
)
def test_job_fit_invalid_controlled_payloads_fail_production_validation(
    plan,
    response,
):
    result = parity.validate_and_grade_production_parity_response(
        _request(plan, "job_fit_evaluation"),
        response,
        plan=plan,
    )
    assert result["production_contract_valid"] is False
    assert result["production_normalized_output"] == {}


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


def test_openai_structured_parity_still_emits_exact_json_schema(plan):
    request = _request(plan, "critic_evaluation", "openai")
    scheduled = _scheduled(plan, "critic_evaluation", "openai")
    arguments = build_openai_production_parity_chat_completion_arguments(
        parity_request=request,
        scheduled=scheduled,
        plan=plan,
    )

    assert arguments["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": request["response_contract"]["schema_name"],
            "strict": True,
            "schema": request["response_contract"]["schema"],
        },
    }
    assert validate_openai_production_parity_chat_completion_arguments(
        arguments,
        parity_request=request,
        scheduled=scheduled,
        plan=plan,
    )


def test_openai_json_object_parity_emits_no_schema_and_preserves_bounds(plan):
    request = _request(plan, "manual_provider_preview", "openai")
    scheduled = _scheduled(plan, "manual_provider_preview", "openai")
    arguments = build_openai_production_parity_chat_completion_arguments(
        parity_request=request,
        scheduled=scheduled,
        plan=plan,
    )

    assert request["response_contract"]["mode"] == "json_object"
    assert request["response_contract"]["schema_name"] is None
    assert request["response_contract"]["strict"] is False
    assert request["response_contract"]["schema"] is None
    assert arguments["response_format"] == {"type": "json_object"}
    assert set(arguments["response_format"]) == {"type"}
    assert request["fallback"] is False
    assert request["retry_limit"] == 0
    assert request["timeout_seconds"] == 30
    assert scheduled["fallback"] is False
    assert scheduled["harness_retry_limit"] == 0
    assert scheduled["provider_sdk_retry_limit"] == 0
    assert validate_openai_production_parity_chat_completion_arguments(
        arguments,
        parity_request=request,
        scheduled=scheduled,
        plan=plan,
    )


def test_groq_gpt_oss_120b_keeps_workload_scoped_response_modes(plan):
    requests = {}
    for workload_id in ("tailoring_generation", "jd_intelligence"):
        row = next(
            item
            for item in plan["staged_matrix"]
            if item["workload_id"] == workload_id
            and item["provider"] == "groq"
            and item["model"] == "openai/gpt-oss-120b"
        )
        packet = build_transmittable_request_packet(
            case_alias=row["case_alias"],
            provider=row["provider"],
            model=row["model"],
            plan=plan,
        )
        requests[workload_id] = parity.build_production_parity_request(
            packet,
            plan=plan,
        )

    tailoring = requests["tailoring_generation"]
    assert tailoring["response_contract"]["mode"] == "json_object"
    assert tailoring["response_contract"]["schema_name"] is None
    assert tailoring["response_contract"]["strict"] is False
    assert tailoring["response_contract"]["schema"] is None
    assert tailoring["task_parameters"]["max_tokens"] == 700

    jd_intelligence = requests["jd_intelligence"]
    assert jd_intelligence["response_contract"]["mode"] == "structured_json"
    assert jd_intelligence["response_contract"]["strict"] is True
    assert isinstance(jd_intelligence["response_contract"]["schema"], dict)


def test_groq_gpt_oss_120b_tailoring_prompt_operationalizes_bare_tool_safety(
    plan,
):
    row = next(
        item
        for item in plan["staged_matrix"]
        if item["workload_id"] == "tailoring_generation"
        and item["provider"] == "groq"
        and item["model"] == "openai/gpt-oss-120b"
    )
    packet = build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=plan,
    )
    request = parity.build_production_parity_request(packet, plan=plan)
    prompt = "\n".join(message["content"] for message in request["messages"])

    assert row["case_alias"] == "case_3dddc5f43be918e0932d3bb2"
    assert "emphasize Python as supported source evidence" in prompt
    assert "surface SQL prominently as supported evidence" in prompt
    assert "retain Airflow visibly as supporting evidence" in prompt
    assert "not evidenced" in prompt
    assert "candidate lacks" in prompt
    assert "supports=['python']" in prompt
    assert "Evidence unit: python, sql, airflow" in prompt
    assert "Parent bullet: Delivered python, sql, airflow." in prompt
    assert "Missing required: ['synthetic_requirement_gap']" in prompt
    assert "risk-reduction outcome" not in prompt
    assert "error-reduction context" not in prompt
    assert request["task_parameters"]["max_tokens"] == 700


def test_openai_parity_rejects_unsupported_mode_and_model_mismatch(plan):
    request = _request(plan, "manual_provider_preview", "openai")
    scheduled = _scheduled(plan, "manual_provider_preview", "openai")

    unsupported = deepcopy(request)
    unsupported["response_contract"]["mode"] = "unsupported"
    with pytest.raises(ValueError, match="production response mode mismatch"):
        build_openai_production_parity_chat_completion_arguments(
            parity_request=unsupported,
            scheduled=scheduled,
            plan=plan,
        )

    mismatched = deepcopy(scheduled)
    mismatched["model"] = "gpt-5.1"
    with pytest.raises(ValueError, match="schedule binding mismatch"):
        build_openai_production_parity_chat_completion_arguments(
            parity_request=request,
            scheduled=mismatched,
            plan=plan,
        )


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


def test_groq_gpt_oss_qualification_matches_production_reasoning_configuration(
    plan,
):
    """Qualification must exercise the same generation config production sends."""

    request = _request(plan, "manual_provider_preview", "groq")
    scheduled = _scheduled(plan, "manual_provider_preview", "groq")
    assert scheduled["model"].startswith("openai/gpt-oss-")
    assert request["response_contract"]["mode"] == "json_object"
    assert request["task_parameters"]["thinking_budget"] == 0

    arguments = build_groq_production_parity_chat_completion_arguments(
        parity_request=request,
        scheduled=scheduled,
        plan=plan,
    )

    # production parity: reasoning bounded and effort pinned low
    assert arguments["include_reasoning"] is False
    assert arguments["reasoning_effort"] == "low"
    # no provider-side schema in JSON Object Mode
    assert arguments["response_format"] == {"type": "json_object"}
    assert "reasoning_format" not in arguments
    assert request["response_contract"]["schema"] is None
    # controlled-transport conventions preserved
    assert arguments["stream"] is False
    assert arguments["n"] == 1
    assert arguments["temperature"] == 0
    assert arguments["max_completion_tokens"] == 1024


def test_groq_parity_validator_rejects_missing_reasoning_configuration(plan):
    """The exact field allowlist must require, not merely tolerate, parity."""

    request = _request(plan, "manual_provider_preview", "groq")
    scheduled = _scheduled(plan, "manual_provider_preview", "groq")
    arguments = build_groq_production_parity_chat_completion_arguments(
        parity_request=request,
        scheduled=scheduled,
        plan=plan,
    )

    missing_effort = deepcopy(arguments)
    missing_effort.pop("reasoning_effort")
    with pytest.raises(ValueError, match="allowlist"):
        validate_groq_production_parity_chat_completion_arguments(
            missing_effort, parity_request=request, scheduled=scheduled, plan=plan
        )

    wrong_effort = deepcopy(arguments)
    wrong_effort["reasoning_effort"] = "high"
    with pytest.raises(ValueError, match="reasoning effort mismatch"):
        validate_groq_production_parity_chat_completion_arguments(
            wrong_effort, parity_request=request, scheduled=scheduled, plan=plan
        )

    wrong_bounding = deepcopy(arguments)
    wrong_bounding["include_reasoning"] = True
    with pytest.raises(ValueError, match="reasoning bounding mismatch"):
        validate_groq_production_parity_chat_completion_arguments(
            wrong_bounding, parity_request=request, scheduled=scheduled, plan=plan
        )


# ---------------------------------------------------------------------------
# Stage 1: additive rendered-parity and workload-semantics primitives.
# ---------------------------------------------------------------------------


import json as _stage1_json  # noqa: E402

from src.evaluation import (  # noqa: E402
    controlled_provider_qualification_registry as _stage1_registry,
)
from src.evaluation import (  # noqa: E402
    provider_model_recommendation_policy as _stage1_policy,
)
from src.evaluation.provider_fixture_benchmark import (  # noqa: E402
    load_fixture_case_corpus as _stage1_load_corpus,
)

CURRENT_REGISTRY_SHA256 = (
    "6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"
)


def _stage1_skill_extraction_only_change(corpus):
    mutated = deepcopy(corpus)
    case = next(
        row
        for row in mutated["cases"]
        if row["workload_id"] == "skill_extraction"
    )
    case["normalized_input_packet"]["preferred_terms"].append("terraform")
    case["normalized_input_packet"]["evidence_tokens"].append("terraform")
    case["expected_output"]["preferred_skills"].append("terraform")
    case["supported_evidence_tokens"].append("terraform")
    return mutated


def test_stage1_rendered_parity_semantics_are_deterministic():
    corpus = _stage1_load_corpus()
    for workload_id in WORKLOAD_ORDER:
        first = parity.workload_rendered_parity_semantics_sha256(
            workload_id, corpus
        )
        second = parity.workload_rendered_parity_semantics_sha256(
            workload_id, deepcopy(corpus)
        )
        assert first == second

    rendered = parity.build_workload_rendered_parity_semantics(
        "skill_extraction", corpus
    )
    assert rendered["workload_id"] == "skill_extraction"
    assert rendered["rendered_semantics_version"] == (
        parity.RENDERED_PARITY_SEMANTICS_VERSION
    )
    assert rendered["rendered_cases"]
    for row in rendered["rendered_cases"]:
        assert set(row) == {
            "stable_case_alias",
            "replacements",
            "local_validation_context",
        }


def test_stage1_rendered_semantics_isolate_one_workload_branch():
    corpus = _stage1_load_corpus()
    baseline = {
        workload_id: parity.workload_rendered_parity_semantics_sha256(
            workload_id, corpus
        )
        for workload_id in WORKLOAD_ORDER
    }

    real_renderer = parity._synthetic_material

    def drifted_renderer(workload_id, packet):
        replacements, context = real_renderer(workload_id, packet)
        if workload_id == "skill_extraction":
            context = dict(context)
            context["job_description"] = (
                context["job_description"] + " EXTENDED SYNTHETIC SECTION."
            )
            replacements = dict(replacements)
            replacements["<job_description>"] = context["job_description"]
        return replacements, context

    parity._synthetic_material = drifted_renderer
    try:
        changed = [
            workload_id
            for workload_id in WORKLOAD_ORDER
            if parity.workload_rendered_parity_semantics_sha256(
                workload_id, corpus
            )
            != baseline[workload_id]
        ]
    finally:
        parity._synthetic_material = real_renderer

    assert changed == ["skill_extraction"]


def test_stage1_workload_qualification_semantics_isolate_one_workload():
    corpus = _stage1_load_corpus()
    mutated = _stage1_skill_extraction_only_change(corpus)

    changed = [
        workload_id
        for workload_id in WORKLOAD_ORDER
        if parity.workload_qualification_semantics_sha256(
            workload_id, corpus=corpus
        )
        != parity.workload_qualification_semantics_sha256(
            workload_id, corpus=mutated
        )
    ]

    assert changed == ["skill_extraction"]


def test_stage1_workload_qualification_semantics_bind_plan_projection():
    """The composed digest must be a function of the workload plan projection."""

    from src.evaluation.controlled_provider_benchmark_plan import (
        workload_plan_projection_sha256,
    )

    corpus = _stage1_load_corpus()
    plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    mutated = _stage1_skill_extraction_only_change(corpus)

    for workload_id in WORKLOAD_ORDER:
        composed = parity.workload_qualification_semantics_sha256(
            workload_id, plan=plan, corpus=corpus
        )
        assert composed == parity.workload_qualification_semantics_sha256(
            workload_id, plan=plan, corpus=corpus
        )

    # The plan projection component is what carries the shared safety envelope,
    # and it moves for exactly the changed workload.
    projection_changed = [
        workload_id
        for workload_id in WORKLOAD_ORDER
        if workload_plan_projection_sha256(workload_id, corpus=corpus)
        != workload_plan_projection_sha256(workload_id, corpus=mutated)
    ]
    assert projection_changed == ["skill_extraction"]


def test_stage1_registry_and_recommendation_authority_are_unchanged():
    registry = _stage1_json.load(
        open(
            Path(__file__).resolve().parents[1]
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json",
            encoding="utf-8",
        )
    )

    assert _stage1_registry.provider_qualification_registry_sha256(
        registry
    ) == CURRENT_REGISTRY_SHA256
    built = _stage1_policy.build_provider_model_recommendation_policy(registry)
    assert len(built["workloads"]) == 12


def test_stage1_plan_and_parity_owners_import_independently():
    import subprocess
    import sys

    root = str(Path(__file__).resolve().parents[1])
    for module_name in (
        "src.evaluation.controlled_provider_benchmark_plan",
        "src.evaluation.controlled_production_parity_benchmark",
    ):
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                f"import sys; sys.path.insert(0, {root!r}); "
                f"import {module_name} as m; print(m.__name__)",
            ],
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        assert module_name in completed.stdout


# ---------------------------------------------------------------------------
# Stage 4B: bounded recipe expansion + add-case workload isolation.
# cases.json is never written.
# ---------------------------------------------------------------------------


def _stage4b_cases():
    import test_provider_fixture_benchmark as fixture_suite

    return fixture_suite.stage4b_proposed_skill_cases()


def _stage4b_future_corpus():
    future = deepcopy(_stage1_load_corpus())
    future["cases"] = future["cases"] + _stage4b_cases()
    return future


def test_stage4b_legacy_skill_rendering_is_byte_identical():
    corpus = _stage1_load_corpus()
    case = next(
        row
        for row in corpus["cases"]
        if row["workload_id"] == "skill_extraction"
    )
    replacements, context = parity._synthetic_material(
        "skill_extraction", case["normalized_input_packet"]
    )
    expected = (
        "Required qualifications: python, sql. "
        + "Synthetic role context. " * 14
        + "Preferred qualifications: airflow."
    )
    assert context["job_description"] == expected
    assert replacements["<job_description>"] == expected
    assert len(expected) == 408


def test_stage4b_recipe_expansion_matches_production_shape_targets():
    from src.ai.skill_llm_enricher import (
        SKILL_EXTRACTION_FULL_TEXT_LIMIT,
        _build_skill_extraction_text,
    )
    from src.evaluation.provider_fixture_benchmark import (
        SYNTHETIC_ROLE_DOCUMENT_FIELD,
    )

    expectations = {
        "full_text_required_preferred": (5000, 5500, "FULL_TEXT"),
        "windowed_head_required_boilerplate": (8000, 8600, "WINDOWED"),
        "windowed_mid_required_tail_preferred": (7000, 7500, "WINDOWED"),
        "windowed_overlap_suppressed_preferred": (9800, 10300, "WINDOWED"),
    }
    for case in _stage4b_cases():
        packet = case["normalized_input_packet"]
        recipe = packet[SYNTHETIC_ROLE_DOCUMENT_FIELD]
        description = parity.expand_synthetic_role_document(recipe)
        replacements, context = parity._synthetic_material(
            "skill_extraction", packet
        )
        assert "Synthetic role context." not in description

        low, high, expected_path = expectations[recipe["profile"]]
        assert low <= len(description) <= high, recipe["profile"]
        path = (
            "FULL_TEXT"
            if len(description) <= SKILL_EXTRACTION_FULL_TEXT_LIMIT
            else "WINDOWED"
        )
        assert path == expected_path, recipe["profile"]

        extraction_text = _build_skill_extraction_text(description)
        assert context["job_description"] == extraction_text
        assert replacements["<job_description>"] == extraction_text
        extraction_text = extraction_text.lower()
        for skill in case["expected_output"]["required_skills"]:
            assert skill in extraction_text, (recipe["profile"], skill)
        for skill in case["expected_output"]["preferred_skills"]:
            assert skill in extraction_text, (recipe["profile"], skill)

        if recipe["profile"] == "windowed_overlap_suppressed_preferred":
            # Present in the expanded document, suppressed by the real
            # production window-overlap rule before the provider sees it.
            for skill in recipe["preferred_skills"]:
                assert skill in description.lower()
                assert skill not in extraction_text
            assert case["expected_output"]["preferred_skills"] == []


def test_stage4x_case5_final_parity_request_uses_production_windowing():
    from src.evaluation.controlled_provider_benchmark_plan import (
        _case_alias,
        build_controlled_provider_benchmark_plan,
        build_transmittable_request_packet,
    )
    from src.evaluation.provider_fixture_benchmark import (
        SYNTHETIC_ROLE_DOCUMENT_FIELD,
        fixture_case_corpus_sha256,
    )

    corpus = _stage4b_future_corpus()
    plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    case = next(
        row
        for row in corpus["cases"]
        if row["case_id"]
        == "skill_extraction_windowed_overlap_suppressed_preferred_v1"
    )
    recipe = case["normalized_input_packet"][SYNTHETIC_ROLE_DOCUMENT_FIELD]
    source = parity.expand_synthetic_role_document(recipe).lower()
    alias = _case_alias(case["case_id"], fixture_case_corpus_sha256(corpus))
    packet = build_transmittable_request_packet(
        case_alias=alias,
        provider="groq",
        model="openai/gpt-oss-20b",
        plan=plan,
        corpus=corpus,
    )
    request = parity.build_production_parity_request(
        packet,
        plan=plan,
        corpus=corpus,
    )
    provider_visible = request["messages"][1]["content"].lower()

    assert all(skill in source for skill in recipe["required_skills"])
    assert all(skill in source for skill in recipe["preferred_skills"])
    assert all(skill in provider_visible for skill in recipe["required_skills"])
    assert all(skill not in provider_visible for skill in recipe["preferred_skills"])
    assert request["local_validation_context"]["job_description"].lower() in (
        provider_visible
    )


def test_stage4b_expansion_is_deterministic_and_self_contained():
    from src.evaluation.provider_fixture_benchmark import (
        SYNTHETIC_ROLE_DOCUMENT_FIELD,
    )

    for case in _stage4b_cases():
        packet = case["normalized_input_packet"]
        first = parity._synthetic_material("skill_extraction", packet)
        second = parity._synthetic_material(
            "skill_extraction", deepcopy(packet)
        )
        assert first == second

    source = OWNER_PATH.read_text(encoding="utf-8")
    expander = source[
        source.index("def expand_synthetic_role_document") :
        source.index("RENDERED_PARITY_SEMANTICS_VERSION")
    ]
    # Compare executable lines only; prose may legitimately name what is
    # excluded.
    code = "\n".join(
        line
        for line in expander.splitlines()
        if not line.lstrip().startswith("#")
    )
    code = code.split('"""')[0] + "".join(code.split('"""')[2:])
    for forbidden in (
        "random",
        "datetime",
        "getenv",
        "open(",
        "requests",
        "urllib",
        "monotonic",
    ):
        assert forbidden not in code


def test_stage4b_adding_cases_moves_only_skill_extraction_semantics():
    from src.evaluation.controlled_provider_benchmark_plan import (
        build_controlled_provider_benchmark_plan,
        stable_case_alias,
    )

    corpus = _stage1_load_corpus()
    future = _stage4b_future_corpus()
    current_plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    future_plan = build_controlled_provider_benchmark_plan(corpus=future)

    before = {
        workload_id: parity.workload_qualification_semantics_sha256(
            workload_id, plan=current_plan, corpus=corpus
        )
        for workload_id in WORKLOAD_ORDER
    }
    after = {
        workload_id: parity.workload_qualification_semantics_sha256(
            workload_id, plan=future_plan, corpus=future
        )
        for workload_id in WORKLOAD_ORDER
    }
    changed = [
        workload_id
        for workload_id in WORKLOAD_ORDER
        if before[workload_id] != after[workload_id]
    ]
    assert changed == ["skill_extraction"]

    # Stable V2 aliases are unaffected for existing cases and deterministic
    # for the new ones.
    for case in corpus["cases"]:
        assert stable_case_alias(
            case["workload_id"], case["case_id"]
        ) == stable_case_alias(case["workload_id"], case["case_id"])
    new_aliases = {
        stable_case_alias(case["workload_id"], case["case_id"])
        for case in _stage4b_cases()
    }
    assert len(new_aliases) == 4
    existing_aliases = {
        stable_case_alias(case["workload_id"], case["case_id"])
        for case in corpus["cases"]
    }
    assert new_aliases.isdisjoint(existing_aliases)


def test_stage4b_rendered_semantics_bind_the_expanded_document():
    corpus = _stage4b_future_corpus()
    baseline = {
        workload_id: parity.workload_rendered_parity_semantics_sha256(
            workload_id, corpus
        )
        for workload_id in WORKLOAD_ORDER
    }

    real_expander = parity.expand_synthetic_role_document

    def drifted(recipe):
        return real_expander(recipe) + " EXTENDED SYNTHETIC SECTION."

    parity.expand_synthetic_role_document = drifted
    try:
        moved = [
            workload_id
            for workload_id in WORKLOAD_ORDER
            if parity.workload_rendered_parity_semantics_sha256(
                workload_id, corpus
            )
            != baseline[workload_id]
        ]
    finally:
        parity.expand_synthetic_role_document = real_expander

    # The compact recipes are unchanged; only the expansion moved.
    assert moved == ["skill_extraction"]
    assert parity.expand_synthetic_role_document is real_expander


def test_stage4b_current_authority_invariants_hold():
    from src.evaluation import (
        controlled_provider_qualification_registry as registry,
    )
    from src.evaluation import provider_model_recommendation_policy as policy
    from src.evaluation import (
        job_fit_provider_model_qualification_overlay as job_fit,
    )
    from src.evaluation.controlled_provider_benchmark_plan import (
        build_controlled_provider_benchmark_plan,
        controlled_provider_benchmark_plan_sha256,
        legacy_case_alias_map,
    )
    from src.evaluation.provider_fixture_benchmark import (
        fixture_case_corpus_sha256,
    )

    corpus = _stage1_load_corpus()
    source = _stage1_json.load(
        open(
            Path(__file__).resolve().parents[1]
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json",
            encoding="utf-8",
        )
    )

    assert fixture_case_corpus_sha256(corpus) == (
        "b4dea8bfccf39da87221755777d88f35427b1f4b772f3730fcd48cbdb5842b5f"
    )
    assert controlled_provider_benchmark_plan_sha256(
        build_controlled_provider_benchmark_plan(corpus=corpus)
    ) == "f2dcf5345442009915819432a9c1fc9342de40561eb6824c1518dcd31e99d3bf"
    assert len(legacy_case_alias_map(corpus)) == 15
    assert registry.provider_qualification_registry_sha256(source) == (
        "6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"
    )
    assert len(
        policy.build_provider_model_recommendation_policy(source)["workloads"]
    ) == 12
    overlay = job_fit.build_job_fit_provider_model_qualification_overlay(source)
    assert (overlay["recommendation_status"], overlay["provider"],
            overlay["model"]) == ("recommended", "groq", "openai/gpt-oss-20b")

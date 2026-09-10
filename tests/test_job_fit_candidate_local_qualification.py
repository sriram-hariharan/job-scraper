from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import stat

import pytest

from src.evaluation import controlled_live_provider_qualification as live
from src.evaluation import (
    controlled_provider_qualification_evidence_adapter as adapter,
)
from src.evaluation import (
    controlled_provider_qualification_registry as qualification_registry,
)
from src.evaluation import job_fit_candidate_local_qualification as candidate
from src.evaluation.controlled_groq_canary_transport import (
    build_groq_production_parity_chat_completion_arguments,
)
from src.evaluation.controlled_openai_canary_transport import (
    build_openai_production_parity_chat_completion_arguments,
)
from src.evaluation.controlled_production_parity_benchmark import (
    build_production_parity_request,
    validate_and_grade_production_parity_response,
    validate_production_parity_result,
)
from src.evaluation.controlled_provider_benchmark_human_review import (
    canonical_human_review_requirements,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)
from src.evaluation.job_fit_provider_model_qualification_overlay import (
    build_job_fit_provider_model_qualification_overlay,
)
from src.evaluation.production_task_contract_fingerprints import (
    production_task_contract_sha256,
)


EXECUTION_TIME = "2026-08-31T12:00:00Z"
TEST_CREDENTIAL = "in-memory-job-fit-candidate-test-only"
JOB_FIT_TASK_CONTRACT_SHA256 = (
    "e9568a48240886579814a557b414461510f86485e3bb7a50efc3e7ab8e319480"
)
JOB_FIT_QUALIFICATION_SEMANTICS_SHA256 = (
    "60e7fa48863d893aae0d29d29f01369324219253dcbcde3a1e9d5ba0925c553d"
)
OLD_JOB_FIT_QUALIFICATION_SEMANTICS_SHA256 = (
    "998f9ad1b93650ccdaca81dedd746ddcf0a041e6b6b17b7c80545da5e64c8672"
)
JOB_FIT_20B_CANDIDATE_SEMANTICS_SHA256 = (
    "5d7dc8f71de2799d8d2f448e91fd38ac21af87f628cf52f9bac825a1d1155334"
)
CANDIDATES = (
    ("groq", "openai/gpt-oss-20b"),
    ("groq", "openai/gpt-oss-120b"),
    ("openai", "gpt-5-mini"),
    ("openai", "gpt-5.1"),
)


@pytest.fixture(scope="module")
def plan():
    return build_controlled_provider_benchmark_plan()


def _scheduled(plan, provider, model):
    return next(
        row
        for row in live.build_live_qualification_universe(plan)
        if row["workload_id"] == candidate.JOB_FIT_WORKLOAD_ID
        and row["provider"] == provider
        and row["model"] == model
    )


def _request(plan, provider, model):
    scheduled = _scheduled(plan, provider, model)
    packet = build_transmittable_request_packet(
        case_alias=scheduled["case_alias"],
        provider=provider,
        model=model,
        plan=plan,
    )
    return scheduled, build_production_parity_request(packet, plan=plan)


def _valid_job_fit_response():
    return {
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
    }


def _dispatcher_for_response(response):
    def dispatcher(
        *, provider, api_key, parity_request, scheduled, plan, monotonic_clock
    ):
        assert api_key == TEST_CREDENTIAL
        return {
            "parity_result": validate_and_grade_production_parity_response(
                parity_request,
                deepcopy(response),
                plan=plan,
            ),
            "provider": provider,
            "model": scheduled["model"],
            "latency_ms": 25.0,
            "input_token_count": 40,
            "output_token_count": 20,
            "provider_outcome_category": "success",
        }

    return dispatcher


def _valid_live_inputs(plan, row):
    authorization = live.build_live_authorization_template(
        approved_schedule_keys=[row["schedule_key"]],
        plan=plan,
    )
    pricing = live.build_live_pricing_template(
        approved_provider_model_pairs=authorization[
            "approved_provider_model_pairs"
        ]
    )
    pricing.update(
        {
            "pricing_version": "job-fit-candidate-test-v1",
            "source_classification": live.LIVE_PRICING_SOURCE_CLASSIFICATION,
            "source_effective_at_utc": "2026-08-31T00:00:00Z",
            "valid_from_utc": "2026-08-31T00:00:00Z",
            "expires_at_utc": "2026-09-01T00:00:00Z",
            "operator_approved": True,
        }
    )
    pricing["prices"][0].update(
        {
            "input_price_per_million_tokens": "0.075",
            "output_price_per_million_tokens": "0.30",
        }
    )
    pricing["pricing_table_sha256"] = live.live_pricing_sha256(pricing)
    authorization.update(
        {
            "valid_from_utc": "2026-08-31T00:00:00Z",
            "expires_at_utc": "2026-09-01T00:00:00Z",
            "maximum_request_count": 1,
            "token_ceilings": {
                "maximum_input_tokens_per_request": 4096,
                "maximum_output_tokens_per_request": 600,
                "maximum_total_observed_input_tokens": 4096,
                "maximum_total_observed_output_tokens": 600,
            },
            "maximum_total_cost": "0.0004872",
            "pricing_table_sha256": live.live_pricing_sha256(pricing),
            "operator_approved": True,
        }
    )
    authorization["maximum_cost_per_provider_model"][
        "groq/openai/gpt-oss-20b"
    ] = "0.0004872"
    return authorization, pricing


def _candidate_execution_inputs(plan):
    row = _scheduled(plan, "groq", "openai/gpt-oss-20b")
    authorization, pricing = _valid_live_inputs(plan, row)
    candidate_authorization = (
        candidate.build_job_fit_candidate_live_authorization(
            schedule_key=row["schedule_key"],
            plan=plan,
            live_authorization=authorization,
        )
    )
    return row, authorization, pricing, candidate_authorization


def _execute_candidate(plan, dispatcher):
    row, authorization, pricing, candidate_authorization = (
        _candidate_execution_inputs(plan)
    )
    evidence = candidate.execute_job_fit_candidate_local_live_qualification(
        plan=plan,
        candidate_authorization=candidate_authorization,
        live_authorization=authorization,
        pricing=pricing,
        operator_credentials={"groq": TEST_CREDENTIAL},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers={"groq": dispatcher, "openai": dispatcher},
        monotonic_clock=lambda: 1.0,
    )
    assert candidate.validate_job_fit_candidate_live_evidence(
        evidence,
        candidate_authorization=candidate_authorization,
        live_authorization=authorization,
        plan=plan,
        pricing=pricing,
    )
    return row, evidence, authorization, pricing, candidate_authorization


def test_candidate_semantics_are_deterministic_and_isolated():
    current = {
        identity: candidate.build_job_fit_candidate_transport_semantics(
            *identity
        )
        for identity in CANDIDATES
    }
    historical = {
        identity: candidate.build_job_fit_candidate_transport_semantics(
            *identity,
            historical=True,
        )
        for identity in CANDIDATES
    }

    assert current[("groq", "openai/gpt-oss-20b")]["thinking_budget"] == 0
    assert historical[("groq", "openai/gpt-oss-20b")][
        "thinking_budget"
    ] is None
    assert candidate.job_fit_candidate_transport_semantics_sha256(
        "groq", "openai/gpt-oss-20b"
    ) != candidate.job_fit_candidate_transport_semantics_sha256(
        "groq", "openai/gpt-oss-20b", historical=True
    )
    for identity in CANDIDATES[1:]:
        assert current[identity] == historical[identity]
        assert candidate.job_fit_candidate_transport_semantics_sha256(
            *identity
        ) == candidate.job_fit_candidate_transport_semantics_sha256(
            *identity,
            historical=True,
        )
    assert {
        semantic["production_task_contract_sha256"]
        for semantic in current.values()
    } == {JOB_FIT_TASK_CONTRACT_SHA256}


def test_20b_fingerprint_moves_with_candidate_specific_budget(monkeypatch):
    from src.ai import job_fit_evaluator

    baseline = candidate.job_fit_candidate_transport_semantics_sha256(
        "groq", "openai/gpt-oss-20b"
    )
    monkeypatch.setattr(job_fit_evaluator, "JOB_FIT_THINKING_BUDGET", 1)

    assert candidate.job_fit_candidate_transport_semantics_sha256(
        "groq", "openai/gpt-oss-20b"
    ) != baseline
    for identity in CANDIDATES[1:]:
        assert candidate.job_fit_candidate_transport_semantics_sha256(
            *identity
        ) == candidate.job_fit_candidate_transport_semantics_sha256(
            *identity,
            historical=True,
        )


def test_historical_20b_binding_is_stale_but_unchanged_candidates_remain_valid():
    historical_20b = candidate.job_fit_candidate_transport_semantics_sha256(
        "groq", "openai/gpt-oss-20b", historical=True
    )
    with pytest.raises(
        ValueError,
        match="candidate transport semantics are stale",
    ):
        candidate.validate_current_job_fit_candidate_semantic_binding(
            provider="groq",
            model="openai/gpt-oss-20b",
            tested_candidate_transport_semantics_sha256=historical_20b,
        )

    for provider, model in CANDIDATES[1:]:
        assert candidate.validate_current_job_fit_candidate_semantic_binding(
            provider=provider,
            model=model,
            tested_candidate_transport_semantics_sha256=(
                candidate.job_fit_candidate_transport_semantics_sha256(
                    provider,
                    model,
                    historical=True,
                )
            ),
        )


def test_four_candidate_renderers_preserve_one_candidate_delta(plan):
    rendered = {}
    requests = {}
    for provider, model in CANDIDATES:
        scheduled, request = _request(plan, provider, model)
        requests[(provider, model)] = request
        if provider == "groq":
            rendered[(provider, model)] = (
                build_groq_production_parity_chat_completion_arguments(
                    parity_request=request,
                    scheduled=scheduled,
                    plan=plan,
                )
            )
        else:
            rendered[(provider, model)] = (
                build_openai_production_parity_chat_completion_arguments(
                    parity_request=request,
                    scheduled=scheduled,
                    plan=plan,
                )
            )

    groq_20b = rendered[("groq", "openai/gpt-oss-20b")]
    assert groq_20b["reasoning_effort"] == "low"
    assert groq_20b["include_reasoning"] is False
    assert groq_20b["temperature"] == 0
    assert groq_20b["max_completion_tokens"] == 600
    assert "response_format" not in groq_20b

    groq_120b = rendered[("groq", "openai/gpt-oss-120b")]
    assert groq_120b["include_reasoning"] is False
    assert "reasoning_effort" not in groq_120b
    assert groq_120b["temperature"] == 0
    assert groq_120b["max_completion_tokens"] == 600

    openai_mini = rendered[("openai", "gpt-5-mini")]
    assert openai_mini["reasoning_effort"] == "minimal"
    assert "temperature" not in openai_mini
    assert openai_mini["max_completion_tokens"] == 600

    openai_51 = rendered[("openai", "gpt-5.1")]
    assert "reasoning_effort" not in openai_51
    assert openai_51["temperature"] == 0
    assert openai_51["max_completion_tokens"] == 600

    base_fields = (
        "messages",
        "task_parameters",
        "response_contract",
        "retry_limit",
        "fallback",
    )
    baseline = {
        field: requests[("groq", "openai/gpt-oss-20b")][field]
        for field in base_fields
    }
    for request in requests.values():
        assert {field: request[field] for field in base_fields} == baseline
        assert request["task_parameters"] == {
            "temperature": 0,
            "max_tokens": 600,
        }
    assert all(request["fallback"] is False for request in requests.values())
    assert all(request["retry_limit"] == 0 for request in requests.values())


def test_parity_result_explicitly_binds_candidate_semantics(plan):
    _, request = _request(plan, "groq", "openai/gpt-oss-20b")
    result = validate_and_grade_production_parity_response(
        request,
        _valid_job_fit_response(),
        plan=plan,
    )
    field = candidate.CANDIDATE_TRANSPORT_SEMANTICS_FIELD
    assert result[field] == request[field]

    stale = deepcopy(result)
    stale[field] = candidate.job_fit_candidate_transport_semantics_sha256(
        "groq",
        "openai/gpt-oss-20b",
        historical=True,
    )
    with pytest.raises(ValueError, match="candidate semantic binding mismatch"):
        validate_production_parity_result(stale, request=request, plan=plan)


def test_candidate_authorization_and_fake_dispatch_evidence_bind_fresh_semantic(
    plan,
):
    row = _scheduled(plan, "groq", "openai/gpt-oss-20b")
    authorization, pricing = _valid_live_inputs(plan, row)
    candidate_authorization = (
        candidate.build_job_fit_candidate_live_authorization(
            schedule_key=row["schedule_key"],
            plan=plan,
            live_authorization=authorization,
        )
    )
    calls = []

    def dispatcher(
        *, provider, api_key, parity_request, scheduled, plan, monotonic_clock
    ):
        calls.append(deepcopy(parity_request))
        arguments = build_groq_production_parity_chat_completion_arguments(
            parity_request=parity_request,
            scheduled=scheduled,
            plan=plan,
        )
        assert arguments["reasoning_effort"] == "low"
        assert api_key == TEST_CREDENTIAL
        return {
            "parity_result": validate_and_grade_production_parity_response(
                parity_request,
                _valid_job_fit_response(),
                plan=plan,
            ),
            "provider": provider,
            "model": scheduled["model"],
            "latency_ms": 25.0,
            "input_token_count": 40,
            "output_token_count": 20,
            "provider_outcome_category": "success",
        }

    evidence = candidate.execute_job_fit_candidate_local_live_qualification(
        plan=plan,
        candidate_authorization=candidate_authorization,
        live_authorization=authorization,
        pricing=pricing,
        operator_credentials={"groq": TEST_CREDENTIAL},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers={"groq": dispatcher, "openai": dispatcher},
        monotonic_clock=lambda: 1.0,
    )

    assert len(calls) == 1
    assert evidence["schedule_key"] == row["schedule_key"]
    assert evidence["tested_candidate_transport_semantics_sha256"] == (
        JOB_FIT_20B_CANDIDATE_SEMANTICS_SHA256
    )
    assert evidence[
        "tested_workload_qualification_semantics_sha256"
    ] == JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
    observation = evidence["qualification_observation"]
    assert observation[
        "tested_workload_qualification_semantics_sha256"
    ] == JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
    assert evidence["qualification_observation_sha256"] == (
        adapter.renderer_bound_qualification_observation_sha256(observation)
    )
    assert evidence["live_evidence"]["evidence_version"] == (
        live.RENDERER_BOUND_LIVE_EVIDENCE_VERSION
    )
    assert evidence["live_evidence"]["grading_summaries"][0][
        live.TESTED_WORKLOAD_SEMANTICS_FIELD
    ] == JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
    assert evidence["live_evidence"]["attempted_schedule_keys"] == [
        row["schedule_key"]
    ]
    assert evidence["live_evidence"]["completed_schedule_keys"] == [
        row["schedule_key"]
    ]
    assert evidence["live_evidence"]["stop_reason"] is None
    assert evidence["candidate_qualification_valid"] is True
    assert evidence["ready_for_activation"] is True
    assert candidate.validate_job_fit_candidate_live_evidence(
        evidence,
        candidate_authorization=candidate_authorization,
        live_authorization=authorization,
        plan=plan,
        pricing=pricing,
    )


def test_old_semantics_and_v1_evidence_cannot_authorize_activation(plan):
    _, evidence, authorization, pricing, candidate_authorization = (
        _execute_candidate(
            plan,
            _dispatcher_for_response(_valid_job_fit_response()),
        )
    )

    old_semantics = deepcopy(evidence)
    old_semantics["qualification_observation"][
        "tested_workload_qualification_semantics_sha256"
    ] = OLD_JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
    old_semantics["tested_workload_qualification_semantics_sha256"] = (
        OLD_JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
    )
    old_semantics["qualification_observation_sha256"] = (
        adapter.renderer_bound_qualification_observation_sha256(
            old_semantics["qualification_observation"]
        )
    )
    old_semantics["candidate_qualification_valid"] = False
    old_semantics["ready_for_activation"] = False
    with pytest.raises(ValueError, match="observation binding mismatch"):
        candidate.validate_job_fit_candidate_live_evidence(
            old_semantics,
            candidate_authorization=candidate_authorization,
            live_authorization=authorization,
            plan=plan,
            pricing=pricing,
        )

    v1 = deepcopy(evidence)
    v1["live_evidence"] = live._v1_projection_of_renderer_bound_evidence(
        evidence["live_evidence"]
    )
    v1["base_live_evidence_sha256"] = live.live_qualification_evidence_sha256(
        v1["live_evidence"],
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    v1["qualification_observation"] = None
    v1["qualification_observation_sha256"] = None
    v1["tested_workload_qualification_semantics_sha256"] = None
    v1["candidate_qualification_valid"] = True
    v1["ready_for_activation"] = True
    with pytest.raises(ValueError, match="renderer-bound live evidence"):
        candidate.validate_job_fit_candidate_live_evidence(
            v1,
            candidate_authorization=candidate_authorization,
            live_authorization=authorization,
            plan=plan,
            pricing=pricing,
        )


def test_candidate_and_task_contract_mismatches_fail_closed(plan):
    _, evidence, authorization, pricing, candidate_authorization = (
        _execute_candidate(
            plan,
            _dispatcher_for_response(_valid_job_fit_response()),
        )
    )

    stale_candidate = deepcopy(evidence)
    stale_candidate["tested_candidate_transport_semantics_sha256"] = (
        candidate.job_fit_candidate_transport_semantics_sha256(
            "groq", "openai/gpt-oss-20b", historical=True
        )
    )
    with pytest.raises(ValueError, match="transport semantics are stale"):
        candidate.validate_job_fit_candidate_live_evidence(
            stale_candidate,
            candidate_authorization=candidate_authorization,
            live_authorization=authorization,
            plan=plan,
            pricing=pricing,
        )

    wrong_task = deepcopy(evidence)
    wrong_task["qualification_observation"][
        "tested_task_contract_sha256"
    ] = "0" * 64
    wrong_task["qualification_observation_sha256"] = (
        adapter.renderer_bound_qualification_observation_sha256(
            wrong_task["qualification_observation"]
        )
    )
    with pytest.raises(ValueError, match="observation binding mismatch"):
        candidate.validate_job_fit_candidate_live_evidence(
            wrong_task,
            candidate_authorization=candidate_authorization,
            live_authorization=authorization,
            plan=plan,
            pricing=pricing,
        )


def test_quality_and_authority_failures_cannot_qualify(plan):
    response = _valid_job_fit_response()
    response["results"][0]["reason"] = "   "
    _, evidence, authorization, pricing, candidate_authorization = (
        _execute_candidate(plan, _dispatcher_for_response(response))
    )
    observation = evidence["qualification_observation"]

    assert observation["contract_valid"] is True
    assert observation["quality_gate_passed"] is False
    assert observation["hard_failure_present"] is False
    assert evidence["candidate_qualification_valid"] is False
    assert evidence["ready_for_activation"] is False

    unsafe = deepcopy(evidence)
    unsafe["qualification_observation"]["authority_safety_valid"] = False
    with pytest.raises(ValueError, match="authority or safety invariants"):
        candidate.validate_job_fit_candidate_live_evidence(
            unsafe,
            candidate_authorization=candidate_authorization,
            live_authorization=authorization,
            plan=plan,
            pricing=pricing,
        )


def test_bounded_observation_persistence_is_exclusive_and_safe(plan, tmp_path):
    row, authorization, pricing, candidate_authorization = (
        _candidate_execution_inputs(plan)
    )
    repository_root = tmp_path / "repository"
    repository_root.mkdir()
    target = (
        repository_root
        / live.APPROVED_EVIDENCE_DIRECTORY
        / "job-fit-20b.qualification-observation.json"
    )
    evidence = candidate.execute_job_fit_candidate_local_live_qualification(
        plan=plan,
        candidate_authorization=candidate_authorization,
        live_authorization=authorization,
        pricing=pricing,
        operator_credentials={"groq": TEST_CREDENTIAL},
        execution_time_source=lambda: EXECUTION_TIME,
        transport_dispatchers={
            "groq": _dispatcher_for_response(_valid_job_fit_response()),
            "openai": _dispatcher_for_response(_valid_job_fit_response()),
        },
        monotonic_clock=lambda: 1.0,
        qualification_observation_target=target,
        repository_root=repository_root,
    )

    observation = evidence["qualification_observation"]
    assert target.read_text(encoding="utf-8") == (
        adapter.serialize_renderer_bound_qualification_observation(
            observation
        )
    )
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    persisted = json.loads(target.read_text(encoding="utf-8"))
    assert persisted == observation
    assert adapter.validate_renderer_bound_qualification_observation(
        persisted
    )
    for prohibited in (
        "api_key",
        "credential",
        "headers",
        "messages",
        "normalized_output",
        "prompt",
        "raw_response",
        "reason",
    ):
        assert prohibited not in persisted

    with pytest.raises(ValueError, match="overwrite is prohibited"):
        adapter.write_renderer_bound_qualification_observation_exclusive(
            target,
            observation,
            repository_root=repository_root,
        )

    symlink_root = tmp_path / "symlink-repository"
    symlink_root.mkdir()
    symlink_target = (
        symlink_root
        / live.APPROVED_EVIDENCE_DIRECTORY
        / "job-fit-20b.qualification-observation.json"
    )
    symlink_target.parent.mkdir(parents=True)
    symlink_target.symlink_to(tmp_path / "elsewhere.json")
    with pytest.raises(ValueError, match="overwrite is prohibited"):
        adapter.write_renderer_bound_qualification_observation_exclusive(
            symlink_target,
            observation,
            repository_root=symlink_root,
        )

    traversal_root = tmp_path / "traversal-repository"
    traversal_root.mkdir()
    traversal_target = (
        traversal_root
        / live.APPROVED_EVIDENCE_DIRECTORY
        / ".."
        / "escape.qualification-observation.json"
    )
    with pytest.raises(ValueError, match="traversal is prohibited"):
        adapter.write_renderer_bound_qualification_observation_exclusive(
            traversal_target,
            observation,
            repository_root=traversal_root,
        )
    assert row["schedule_key"] == evidence["schedule_key"]


def test_existing_registry_currentness_consumes_candidate_observation(plan):
    _, evidence, _, _, _ = _execute_candidate(
        plan,
        _dispatcher_for_response(_valid_job_fit_response()),
    )
    observation = evidence["qualification_observation"]
    current = qualification_registry.build_renderer_bound_candidate_qualification_cell(
        plan=plan,
        workload_id=candidate.JOB_FIT_WORKLOAD_ID,
        provider="groq",
        model="openai/gpt-oss-20b",
        observations=[observation],
        current_task_contract_sha256=JOB_FIT_TASK_CONTRACT_SHA256,
        current_workload_qualification_semantics_sha256=(
            JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
        ),
    )
    assert current["status"] == "qualified"
    assert current["status_reasons"] == [
        "qualification_requirements_satisfied"
    ]
    assert current[
        "current_workload_qualification_semantics_sha256"
    ] == JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
    assert current[
        "tested_workload_qualification_semantics_sha256"
    ] == JOB_FIT_QUALIFICATION_SEMANTICS_SHA256

    old_observation = deepcopy(observation)
    old_observation[
        "tested_workload_qualification_semantics_sha256"
    ] = OLD_JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
    stale = qualification_registry.build_renderer_bound_candidate_qualification_cell(
        plan=plan,
        workload_id=candidate.JOB_FIT_WORKLOAD_ID,
        provider="groq",
        model="openai/gpt-oss-20b",
        observations=[old_observation],
        current_task_contract_sha256=JOB_FIT_TASK_CONTRACT_SHA256,
        current_workload_qualification_semantics_sha256=(
            JOB_FIT_QUALIFICATION_SEMANTICS_SHA256
        ),
    )
    assert stale["status"] == "stale"
    assert "workload_semantics_binding_stale" in stale["status_reasons"]


def test_definitive_failure_returns_bounded_nonqualifying_evidence(plan):
    calls = []

    def dispatcher(**kwargs):
        calls.append(kwargs["scheduled"]["schedule_key"])
        raise live.LiveQualificationDefinitiveFailure(
            "definitive_invalid_request",
            status_code=400,
        )

    row, evidence, authorization, pricing, candidate_authorization = (
        _execute_candidate(plan, dispatcher)
    )
    base = evidence["live_evidence"]

    assert calls == [row["schedule_key"]]
    assert base["execution_status"] == "stopped"
    assert base["stop_reason"] == "definitive_invalid_request"
    assert base["attempted_schedule_keys"] == [row["schedule_key"]]
    assert base["completed_schedule_keys"] == []
    assert base["blocked_schedule_keys"] == [row["schedule_key"]]
    assert base["ambiguous_schedule_keys"] == []
    assert len(base["transport_diagnostics"]) == 1
    assert base["transport_diagnostics"][0]["http_status_code"] == 400
    assert evidence["candidate_qualification_valid"] is False
    assert evidence["ready_for_activation"] is False
    serialized = json.dumps(evidence, sort_keys=True).lower()
    for prohibited in (
        '"api_key"',
        '"credential"',
        '"headers"',
        '"messages"',
        '"prompt"',
        '"raw_request"',
        '"raw_response"',
        '"reasoning"',
        TEST_CREDENTIAL.lower(),
    ):
        assert prohibited not in serialized
    assert candidate.serialize_job_fit_candidate_live_evidence(
        evidence,
        candidate_authorization=candidate_authorization,
        live_authorization=authorization,
        plan=plan,
        pricing=pricing,
    )

    falsely_promoted = deepcopy(evidence)
    falsely_promoted["candidate_qualification_valid"] = True
    falsely_promoted["ready_for_activation"] = True
    with pytest.raises(
        ValueError,
        match="candidate qualification status is invalid",
    ):
        candidate.validate_job_fit_candidate_live_evidence(
            falsely_promoted,
            candidate_authorization=candidate_authorization,
            live_authorization=authorization,
            plan=plan,
            pricing=pricing,
        )


def test_ambiguous_outcome_returns_bounded_nonqualifying_evidence(plan):
    calls = []

    def dispatcher(**kwargs):
        calls.append(kwargs["scheduled"]["schedule_key"])
        raise live.LiveQualificationAmbiguousTimeout("ambiguous_timeout")

    row, evidence, _, _, _ = _execute_candidate(plan, dispatcher)
    base = evidence["live_evidence"]

    assert calls == [row["schedule_key"]]
    assert base["execution_status"] == "stopped"
    assert base["stop_reason"] == "ambiguous_timeout"
    assert base["attempted_schedule_keys"] == [row["schedule_key"]]
    assert base["completed_schedule_keys"] == []
    assert base["blocked_schedule_keys"] == []
    assert base["ambiguous_schedule_keys"] == [row["schedule_key"]]
    assert base["transport_diagnostics"] == []
    assert evidence["candidate_qualification_valid"] is False
    assert evidence["ready_for_activation"] is False


def test_contract_quality_failure_returns_grading_diagnostics(plan):
    calls = []

    def dispatcher(
        *, provider, api_key, parity_request, scheduled, plan, monotonic_clock
    ):
        calls.append(scheduled["schedule_key"])
        return {
            "parity_result": validate_and_grade_production_parity_response(
                parity_request,
                {"results": []},
                plan=plan,
            ),
            "provider": provider,
            "model": scheduled["model"],
            "latency_ms": 25.0,
            "input_token_count": 40,
            "output_token_count": 20,
            "provider_outcome_category": "success",
        }

    row, evidence, _, _, _ = _execute_candidate(plan, dispatcher)
    base = evidence["live_evidence"]

    assert calls == [row["schedule_key"]]
    assert base["execution_status"] == "stopped"
    assert base["stop_reason"] == "hard_safety_failure"
    assert base["blocked_schedule_keys"] == [row["schedule_key"]]
    assert len(base["grading_summaries"]) == 1
    assert base["grading_summaries"][0]["production_contract_valid"] is False
    assert base["grading_summaries"][0]["benchmark_quality_passed"] is False
    assert base["grading_summaries"][0]["hard_failure_present"] is True
    assert len(base["failure_diagnostics"]) == 1
    assert evidence["candidate_qualification_valid"] is False
    assert evidence["ready_for_activation"] is False


def test_malformed_base_evidence_still_fails_closed(plan, monkeypatch):
    _, authorization, pricing, candidate_authorization = (
        _candidate_execution_inputs(plan)
    )
    monkeypatch.setattr(
        live,
        "execute_controlled_live_qualification",
        lambda **_kwargs: {"execution_status": "stopped"},
    )

    with pytest.raises(ValueError, match="live evidence fields are invalid"):
        candidate.execute_job_fit_candidate_local_live_qualification(
            plan=plan,
            candidate_authorization=candidate_authorization,
            live_authorization=authorization,
            pricing=pricing,
            operator_credentials={"groq": TEST_CREDENTIAL},
            execution_time_source=lambda: EXECUTION_TIME,
            transport_dispatchers={"groq": lambda **_kwargs: None},
            monotonic_clock=lambda: 1.0,
        )


def test_task_contract_overlay_and_review_authority_remain_unchanged(plan):
    assert production_task_contract_sha256("job_fit_evaluation") == (
        JOB_FIT_TASK_CONTRACT_SHA256
    )
    registry = json.loads(
        Path(
            "outputs/provider_benchmark/provider-qualification-registry.json"
        ).read_text(encoding="utf-8")
    )
    overlay = build_job_fit_provider_model_qualification_overlay(registry)
    assert overlay["recommendation_status"] == "recommended"
    assert (overlay["provider"], overlay["model"]) == (
        "groq",
        "openai/gpt-oss-20b",
    )
    assert overlay["qualified_options"] == [
        {"provider": provider, "model": model}
        for provider, model in CANDIDATES
    ]
    assert canonical_human_review_requirements()["job_fit_evaluation"] is False

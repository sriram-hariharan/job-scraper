from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from src.app import provider_model_routing_service as routing
from src.evaluation import controlled_live_provider_qualification as live
from src.evaluation import controlled_provider_qualification_evidence_adapter as adapter
from src.evaluation import controlled_provider_qualification_registry as registry
from src.evaluation import job_fit_candidate_local_qualification as candidate
from src.evaluation import job_fit_provider_model_qualification_overlay as overlay
from src.evaluation import provider_model_recommendation_policy as policy
from src.evaluation.controlled_groq_canary_transport import (
    build_groq_production_parity_chat_completion_arguments,
)
from src.evaluation.controlled_production_parity_benchmark import (
    build_production_parity_request,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_PATH = (
    ROOT
    / "outputs/provider_qualification/"
    "job-fit-groq-gpt-oss-20b-"
    "schedule_81eb617b0805ecd61b0ca7e0ec7d2bf8-"
    "20260901T1720.qualification-observation.json"
)
OBSERVATION_SHA256 = (
    "34b75e1e52ccfd1577a1d52e814f327c07ccb3fd17509137bb8d9e829d50e7aa"
)
REGISTRY_SHA256 = (
    "2c75dd95de90553ce05dd2a20d9b9f478c9e65441305997adefd7c9f00787519"
)
TASK_SHA256 = (
    "e9568a48240886579814a557b414461510f86485e3bb7a50efc3e7ab8e319480"
)
SEMANTICS_SHA256 = (
    "60e7fa48863d893aae0d29d29f01369324219253dcbcde3a1e9d5ba0925c553d"
)
CANDIDATE_SHA256 = (
    "5d7dc8f71de2799d8d2f448e91fd38ac21af87f628cf52f9bac825a1d1155334"
)
WINNER = {"provider": "groq", "model": "openai/gpt-oss-20b"}
HISTORICAL_ALTERNATIVES = (
    {"provider": "groq", "model": "openai/gpt-oss-120b"},
    {"provider": "openai", "model": "gpt-5-mini"},
    {"provider": "openai", "model": "gpt-5.1"},
)


def _authority():
    return registry.load_renderer_bound_job_fit_qualification_registry(
        ROOT / registry.RENDERER_BOUND_JOB_FIT_REGISTRY_ARTIFACT_PATH,
        repository_root=ROOT,
    )


def _no_owner_selections(monkeypatch, selection=None):
    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        lambda owner_user_id: {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": (
                    []
                    if selection is None
                    else [
                        {
                            "owner_user_id": owner_user_id,
                            "workload_id": "job_fit_evaluation",
                            **selection,
                        }
                    ]
                ),
            }
        },
    )


def test_stage7a_durable_authority_pin_and_overlay_are_exact():
    observation = adapter.load_renderer_bound_qualification_observation(
        OBSERVATION_PATH,
        repository_root=ROOT,
    )
    assert adapter.renderer_bound_qualification_observation_sha256(
        observation
    ) == OBSERVATION_SHA256

    authority = _authority()
    assert registry.renderer_bound_qualification_registry_sha256(
        authority
    ) == REGISTRY_SHA256
    assert policy.validate_finalized_job_fit_renderer_bound_authority(
        authority
    )
    cells = authority["cells"]
    assert [
        (cell["provider"], cell["model"], cell["status"])
        for cell in cells
    ] == [
        ("groq", "openai/gpt-oss-20b", "qualified"),
        ("groq", "openai/gpt-oss-120b", "rejected"),
        ("openai", "gpt-5-mini", "rejected"),
        ("openai", "gpt-5.1", "rejected"),
    ]
    pin = policy.build_finalized_job_fit_renderer_bound_pin()
    result = overlay.build_renderer_bound_job_fit_overlay(
        authority,
        pin=pin,
    )
    assert result["recommendation_status"] == "recommended"
    assert result["selection_basis"] == "sole_qualified_candidate"
    assert result["qualified_options"] == [WINNER]
    assert (result["provider"], result["model"]) == (
        WINNER["provider"],
        WINNER["model"],
    )


def test_stage7a_job_fit_artifact_writer_and_loader_are_exclusive(
    monkeypatch,
    tmp_path,
):
    authority = _authority()
    relative = Path(
        "src/evaluation/renderer_bound_job_fit_qualification_registry.json"
    )
    monkeypatch.setattr(
        registry,
        "RENDERER_BOUND_JOB_FIT_REGISTRY_ARTIFACT_PATH",
        relative,
    )
    target = tmp_path / relative
    assert registry.write_initial_renderer_bound_job_fit_qualification_registry(
        target,
        authority,
        repository_root=tmp_path,
    ) == target
    assert registry.load_renderer_bound_job_fit_qualification_registry(
        target,
        repository_root=tmp_path,
    ) == authority
    with pytest.raises(ValueError, match="overwrite is prohibited"):
        registry.write_initial_renderer_bound_job_fit_qualification_registry(
            target,
            authority,
            repository_root=tmp_path,
        )


@pytest.mark.parametrize("selection", HISTORICAL_ALTERNATIVES)
def test_stage7a_historical_owner_options_are_no_longer_executable(
    monkeypatch,
    selection,
):
    _no_owner_selections(monkeypatch, selection)
    status = routing.read_provider_model_routing_status(
        "job_fit_evaluation",
        owner_user_id="controlled-stage7a-owner",
    )
    assert status["requested_selection"] == selection
    assert status["requested_selection_status"] == "no_longer_qualified"
    assert status["qualified_options"] == [WINNER]
    assert status["effective_selection"] == WINNER
    assert status["effective_selection_source"] == "applylens_recommended"


def test_stage7a_routing_uses_job_fit_authority_and_preserves_skill(
    monkeypatch,
):
    _no_owner_selections(monkeypatch)
    job_fit = routing.read_provider_model_routing_status(
        "job_fit_evaluation",
        owner_user_id="controlled-stage7a-owner",
    )
    assert job_fit["recommendation_status"] == "recommended"
    assert job_fit["execution_mode"] == "qualified_provider_model"
    assert job_fit["recommended_option"] == WINNER
    assert job_fit["effective_selection"] == WINNER
    assert job_fit["effective_selection_source"] == "applylens_recommended"

    skill = routing.read_provider_model_routing_status("skill_extraction")
    assert skill["recommended_option"] == WINNER
    assert skill["qualified_options"] == [
        WINNER,
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
    ]


def test_stage7a_legacy_and_transient_authority_fail_closed(monkeypatch):
    authority = _authority()
    pin = policy.build_finalized_job_fit_renderer_bound_pin()
    v1 = registry.load_provider_qualification_registry(
        ROOT / registry.REGISTRY_ARTIFACT_PATH,
        repository_root=ROOT,
    )
    with pytest.raises(ValueError):
        overlay.build_renderer_bound_job_fit_overlay(v1, pin=pin)

    stale = deepcopy(authority)
    winner = next(cell for cell in stale["cells"] if cell["status"] == "qualified")
    winner["tested_workload_qualification_semantics_sha256"] = (
        "998f9ad1b93650ccdaca81dedd746ddcf0a041e6b6b17b7c80545da5e64c8672"
    )
    winner["qualification_binding_sha256"] = (
        registry.renderer_bound_qualification_binding_sha256(winner)
    )
    with pytest.raises(ValueError):
        policy.validate_finalized_job_fit_renderer_bound_authority(stale)

    historical = overlay.build_job_fit_provider_model_qualification_overlay(v1)
    assert len(historical["qualified_options"]) == 4
    assert routing.read_provider_model_routing_status(
        "job_fit_evaluation"
    )["qualified_options"] == [WINNER]

    monkeypatch.setattr(
        routing.qualification_registry,
        "load_renderer_bound_job_fit_qualification_registry",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )
    blocked = routing.read_provider_model_routing_status("job_fit_evaluation")
    assert blocked["recommendation_status"] == "blocked_non_live"
    assert blocked["qualified_options"] == []


def test_stage7a_effective_route_reaches_qualified_candidate_semantics(
    monkeypatch,
):
    _no_owner_selections(monkeypatch)
    route = routing.resolve_effective_user_provider_route(
        "controlled-stage7a-owner",
        "job_fit_evaluation",
    )
    assert route == {
        "workload_id": "job_fit_evaluation",
        **WINNER,
        "effective_selection_source": "applylens_recommended",
    }
    assert candidate.job_fit_candidate_transport_semantics_sha256(
        route["provider"], route["model"]
    ) == CANDIDATE_SHA256

    corpus = load_fixture_case_corpus()
    plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    row = next(
        item
        for item in live.build_live_qualification_universe(plan)
        if item["schedule_key"]
        == "schedule_81eb617b0805ecd61b0ca7e0ec7d2bf8"
    )
    packet = build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=route["provider"],
        model=route["model"],
        plan=plan,
        corpus=corpus,
    )
    request = build_production_parity_request(
        packet,
        plan=plan,
        corpus=corpus,
    )
    arguments = build_groq_production_parity_chat_completion_arguments(
        parity_request=request,
        scheduled=row,
        plan=plan,
        corpus=corpus,
    )
    assert arguments["temperature"] == 0
    assert arguments["max_completion_tokens"] == 600
    assert candidate.job_fit_candidate_thinking_budget_for_request(request) == 0
    assert arguments["reasoning_effort"] == "low"
    assert arguments["include_reasoning"] is False
    assert request["response_contract"]["mode"] == "json_text"
    assert "response_format" not in arguments
    assert request["production_task_contract_sha256"] == TASK_SHA256
    assert live.build_workload_qualification_semantics_fingerprints(
        plan,
        corpus=corpus,
    )["job_fit_evaluation"] == SEMANTICS_SHA256

from __future__ import annotations

import ast
from copy import deepcopy
import inspect
from pathlib import Path

import pytest

from src.app import provider_model_routing_service as routing
from src.evaluation import (
    job_fit_provider_model_qualification_overlay as job_fit_overlay,
)
from src.evaluation.provider_model_recommendation_policy import (
    SOURCE_QUALIFICATION_REGISTRY_SHA256,
    build_provider_model_recommendation_policy,
)


ROOT = Path(__file__).resolve().parents[1]

OWNER = (
    ROOT
    / "src/app/provider_model_routing_service.py"
)

JOB_FIT_OPTIONS = [
    {"provider": "groq", "model": "openai/gpt-oss-20b"},
    {"provider": "groq", "model": "openai/gpt-oss-120b"},
    {"provider": "openai", "model": "gpt-5-mini"},
    {"provider": "openai", "model": "gpt-5.1"},
]
CURRENT_JOB_FIT_OPTIONS = [JOB_FIT_OPTIONS[0]]

MANUAL_PREVIEW_RECOMMENDED = {
    "provider": "groq",
    "model": "openai/gpt-oss-120b",
}


def _job_fit_overlay():
    return {
        "workload_id": "job_fit_evaluation",
        "recommendation_status": "recommended",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "selection_basis": (
            "reviewed_production_aligned_quality_tie_latency_tiebreak"
        ),
        "qualified_options": deepcopy(JOB_FIT_OPTIONS),
    }


def _recommendation(
    *,
    workload_id="skill_extraction",
    status="recommended",
    provider="groq",
    model="openai/gpt-oss-20b",
):
    return {
        "workload_id": workload_id,
        "recommendation_status": status,
        "provider": provider,
        "model": model,
        "selection_basis": (
            "durable_quality_tie_latency_tiebreak"
        ),
        "task_contract_sha256": "a" * 64,
        "qualification_binding_sha256": "b" * 64,
        "evidence_sha256": "c" * 64,
        "review_sha256": None,
    }


def _install_synthetic_routing_sources(monkeypatch):
    registry_payload = {
        "cells": [
            {
                "execution_order": 1,
                "workload_id": "skill_extraction",
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "status": "qualified",
                "cost": 99,
            },
            {
                "execution_order": 2,
                "workload_id": "skill_extraction",
                "provider": "openai",
                "model": "gpt-5-mini",
                "status": "qualified",
                "cost": 1,
            },
            {
                "execution_order": 3,
                "workload_id": "skill_extraction",
                "provider": "openai",
                "model": "rejected-model",
                "status": "rejected",
            },
            {
                "execution_order": 4,
                "workload_id": "job_fit_evaluation",
                "provider": "groq",
                "model": "pending-model",
                "status": "pending",
            },
            {
                "execution_order": 5,
                "workload_id": "job_fit_evaluation",
                "provider": "openai",
                "model": "stale-model",
                "status": "stale",
            },
            {
                "execution_order": 6,
                "workload_id": "manual_provider_preview",
                "provider": "openai",
                "model": "pending-preview-model",
                "status": "pending",
            },
        ],
        "preferred_provider": "openai",
    }
    policy = {
        "workloads": [
            {
                "workload_id": "skill_extraction",
                "recommendation_status": "recommended",
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "selection_basis": "quality",
            },
            {
                "workload_id": "job_fit_evaluation",
                "recommendation_status": "fail_closed_zero_qualified",
                "provider": None,
                "model": None,
                "selection_basis": None,
            },
            {
                "workload_id": "manual_provider_preview",
                "recommendation_status": "blocked_non_live",
                "provider": None,
                "model": None,
                "selection_basis": None,
            },
        ]
    }
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: registry_payload,
    )
    monkeypatch.setattr(
        routing,
        "build_provider_model_recommendation_policy",
        lambda _payload: policy,
    )
    monkeypatch.setattr(
        routing,
        "_build_authoritative_job_fit_renderer_bound_route",
        _job_fit_overlay,
    )
    monkeypatch.setattr(
        routing,
        "_build_authoritative_skill_renderer_bound_route",
        lambda: {
            **_recommendation(),
            "selection_basis": "quality",
            "qualified_options": [
                {
                    "provider": "groq",
                    "model": "openai/gpt-oss-20b",
                },
                {
                    "provider": "openai",
                    "model": "gpt-5-mini",
                },
            ],
        },
    )
    return registry_payload


def test_aggregate_routing_statuses_are_safe_and_preserve_policy_order(
    monkeypatch,
):
    registry_payload = {
        "cells": [
            {
                "execution_order": 1,
                "workload_id": "skill_extraction",
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "status": "qualified",
                "cost": 99,
            },
            {
                "execution_order": 2,
                "workload_id": "skill_extraction",
                "provider": "openai",
                "model": "gpt-5-mini",
                "status": "qualified",
                "cost": 1,
            },
            {
                "execution_order": 3,
                "workload_id": "skill_extraction",
                "provider": "openai",
                "model": "rejected-model",
                "status": "rejected",
            },
            {
                "execution_order": 4,
                "workload_id": "job_fit_evaluation",
                "provider": "groq",
                "model": "pending-model",
                "status": "pending",
            },
            {
                "execution_order": 5,
                "workload_id": "job_fit_evaluation",
                "provider": "openai",
                "model": "stale-model",
                "status": "stale",
            },
            {
                "execution_order": 6,
                "workload_id": "manual_provider_preview",
                "provider": "openai",
                "model": "pending-preview-model",
                "status": "pending",
            },
        ],
        "preferred_provider": "openai",
    }
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: registry_payload,
    )

    monkeypatch.setattr(
        routing,
        "build_provider_model_recommendation_policy",
        lambda payload: {
            "workloads": [
                {
                    "workload_id": "skill_extraction",
                    "recommendation_status": "recommended",
                    "provider": "groq",
                    "model": "openai/gpt-oss-20b",
                    "selection_basis": "quality",
                    "task_contract_sha256": "secret-task",
                    "qualification_binding_sha256": "secret-binding",
                    "evidence_sha256": "secret-evidence",
                    "review_sha256": None,
                },
                {
                    "workload_id": "job_fit_evaluation",
                    "recommendation_status": (
                        "fail_closed_zero_qualified"
                    ),
                    "provider": None,
                    "model": None,
                    "selection_basis": None,
                    "task_contract_sha256": "secret-task-2",
                },
                {
                    "workload_id": "manual_provider_preview",
                    "recommendation_status": "blocked_non_live",
                    "provider": None,
                    "model": None,
                    "selection_basis": None,
                },
            ]
        },
    )
    monkeypatch.setattr(
        routing,
        "_build_authoritative_job_fit_renderer_bound_route",
        _job_fit_overlay,
    )
    monkeypatch.setattr(
        routing,
        "_build_authoritative_skill_renderer_bound_route",
        lambda: {
            **_recommendation(),
            "selection_basis": "quality",
            "qualified_options": [
                {
                    "provider": "groq",
                    "model": "openai/gpt-oss-20b",
                },
                {
                    "provider": "openai",
                    "model": "gpt-5-mini",
                },
            ],
        },
    )

    payload = routing.list_provider_model_routing_statuses()

    assert payload == {
        "workloads": [
            {
                "workload_id": "skill_extraction",
                "recommendation_status": "recommended",
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "selection_basis": "quality",
                "execution_mode": "qualified_provider_model",
                "recommended_option": {
                    "provider": "groq",
                    "model": "openai/gpt-oss-20b",
                },
                "qualified_options": [
                    {
                        "provider": "groq",
                        "model": "openai/gpt-oss-20b",
                    },
                    {
                        "provider": "openai",
                        "model": "gpt-5-mini",
                    },
                ],
                "requested_selection": None,
                "requested_selection_status": "none",
                "effective_selection": {
                    "provider": "groq",
                    "model": "openai/gpt-oss-20b",
                },
                "effective_selection_source": "applylens_recommended",
            },
            {
                "workload_id": "job_fit_evaluation",
                "recommendation_status": "recommended",
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "selection_basis": (
                    "reviewed_production_aligned_quality_tie_latency_tiebreak"
                ),
                "execution_mode": "qualified_provider_model",
                "recommended_option": JOB_FIT_OPTIONS[0],
                "qualified_options": JOB_FIT_OPTIONS,
                "requested_selection": None,
                "requested_selection_status": "none",
                "effective_selection": JOB_FIT_OPTIONS[0],
                "effective_selection_source": "applylens_recommended",
            },
            {
                "workload_id": "manual_provider_preview",
                "recommendation_status": "blocked_non_live",
                "provider": None,
                "model": None,
                "selection_basis": None,
                "execution_mode": "blocked_non_live",
                "recommended_option": None,
                "qualified_options": [],
                "requested_selection": None,
                "requested_selection_status": "none",
                "effective_selection": None,
                "effective_selection_source": "blocked_non_live",
            },
        ]
    }

    rendered = repr(payload)

    assert "secret-task" not in rendered
    assert "secret-binding" not in rendered
    assert "secret-evidence" not in rendered
    assert "rejected-model" not in rendered
    assert "pending-model" not in rendered
    assert "stale-model" not in rendered
    assert "pending-preview-model" not in rendered
    assert "execution_order" not in rendered
    assert "cost" not in rendered
    assert "preferred_provider" not in rendered


def test_real_frozen_policy_remains_fail_closed_before_overlay_application():
    registry_payload = routing._load_authoritative_qualification_registry()
    policy = build_provider_model_recommendation_policy(registry_payload)
    job_fit = next(
        row
        for row in policy["workloads"]
        if row["workload_id"] == "job_fit_evaluation"
    )

    assert job_fit["recommendation_status"] == (
        "fail_closed_zero_qualified"
    )
    assert job_fit["provider"] is None
    assert job_fit["model"] is None


def test_real_job_fit_overlay_is_exact_and_returns_fresh_safe_payloads():
    registry_payload = routing._load_authoritative_qualification_registry()

    first = (
        job_fit_overlay.build_job_fit_provider_model_qualification_overlay(
            registry_payload
        )
    )
    first["qualified_options"].clear()
    second = (
        job_fit_overlay.build_job_fit_provider_model_qualification_overlay(
            registry_payload
        )
    )

    assert second == _job_fit_overlay()
    rendered = repr(second)
    for private_field in (
        "latency_ms",
        "estimated_cost",
        "input_tokens",
        "output_tokens",
        "historical_missing_requirement_accuracy",
        "registry_sha",
        "task_contract_sha",
        "raw_response",
        "credential",
    ):
        assert private_field not in rendered


def test_job_fit_overlay_fails_closed_when_registry_digest_changes(
    monkeypatch,
):
    registry_payload = routing._load_authoritative_qualification_registry()
    monkeypatch.setattr(
        job_fit_overlay.qualification_registry,
        "provider_qualification_registry_sha256",
        lambda _payload: "0" * 64,
    )

    with pytest.raises(ValueError, match="registry base changed"):
        job_fit_overlay.build_job_fit_provider_model_qualification_overlay(
            registry_payload
        )


def test_job_fit_overlay_fails_closed_when_base_universe_changes(
    monkeypatch,
):
    registry_payload = routing._load_authoritative_qualification_registry()
    changed = deepcopy(registry_payload)
    job_fit_cell = next(
        cell
        for cell in changed["cells"]
        if cell["workload_id"] == "job_fit_evaluation"
    )
    job_fit_cell["model"] = "unexpected-model"
    monkeypatch.setattr(
        job_fit_overlay.qualification_registry,
        "validate_provider_qualification_registry",
        lambda _payload: True,
    )
    monkeypatch.setattr(
        job_fit_overlay.qualification_registry,
        "provider_qualification_registry_sha256",
        lambda _payload: SOURCE_QUALIFICATION_REGISTRY_SHA256,
    )

    with pytest.raises(ValueError, match="base universe changed"):
        job_fit_overlay.build_job_fit_provider_model_qualification_overlay(
            changed
        )


def test_job_fit_overlay_fails_closed_when_base_cell_becomes_qualified(
    monkeypatch,
):
    registry_payload = routing._load_authoritative_qualification_registry()
    changed = deepcopy(registry_payload)
    job_fit_cell = next(
        cell
        for cell in changed["cells"]
        if cell["workload_id"] == "job_fit_evaluation"
    )
    job_fit_cell["status"] = "qualified"
    monkeypatch.setattr(
        job_fit_overlay.qualification_registry,
        "validate_provider_qualification_registry",
        lambda _payload: True,
    )
    monkeypatch.setattr(
        job_fit_overlay.qualification_registry,
        "provider_qualification_registry_sha256",
        lambda _payload: SOURCE_QUALIFICATION_REGISTRY_SHA256,
    )

    with pytest.raises(ValueError, match="unexpectedly contains"):
        job_fit_overlay.build_job_fit_provider_model_qualification_overlay(
            changed
        )


def test_job_fit_overlay_fails_closed_when_task_fingerprint_changes(
    monkeypatch,
):
    registry_payload = routing._load_authoritative_qualification_registry()
    monkeypatch.setattr(
        job_fit_overlay,
        "production_task_contract_sha256",
        lambda _workload_id: "0" * 64,
    )

    with pytest.raises(ValueError, match="production task contract changed"):
        job_fit_overlay.build_job_fit_provider_model_qualification_overlay(
            registry_payload
        )


def test_real_registry_routing_contract_matches_current_qualified_universe(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail(
            "read-only routing inventory must not execute provider runtime"
        ),
    )

    payload = routing.list_provider_model_routing_statuses()
    workloads = payload["workloads"]
    by_workload = {row["workload_id"]: row for row in workloads}

    expected_pairs = {
        "skill_extraction": [
            ("groq", "openai/gpt-oss-20b"),
            ("groq", "openai/gpt-oss-120b"),
        ],
        "job_fit_evaluation": [
            ("groq", "openai/gpt-oss-20b"),
        ],
        "jd_intelligence": [("openai", "gpt-5-mini")],
        "grounded_rag_answer": [
            ("groq", "openai/gpt-oss-20b"),
            ("groq", "openai/gpt-oss-120b"),
            ("openai", "gpt-5-mini"),
            ("openai", "gpt-5.1"),
        ],
        "resume_fallback_ranking": [],
        "ambiguous_resume_adjudication": [
            ("groq", "openai/gpt-oss-120b"),
            ("openai", "gpt-5-mini"),
        ],
        "critic_evaluation": [],
        "tailoring_generation": [
            ("groq", "openai/gpt-oss-120b"),
        ],
        "tailoring_refinement": [
            ("groq", "openai/gpt-oss-20b"),
            ("groq", "openai/gpt-oss-120b"),
        ],
        "tailoring_judge": [
            ("groq", "openai/gpt-oss-120b"),
            ("openai", "gpt-5-mini"),
            ("openai", "gpt-5.1"),
        ],
        "manual_scan_phrase": [],
        "manual_provider_preview": [
            ("groq", "openai/gpt-oss-120b"),
        ],
    }

    assert len(workloads) == 12
    assert set(by_workload) == set(expected_pairs)

    actual_total = 0
    for workload_id, expected in expected_pairs.items():
        row = by_workload[workload_id]
        actual = [
            (option["provider"], option["model"])
            for option in row["qualified_options"]
        ]
        assert actual == expected
        actual_total += len(actual)

        if row["recommendation_status"] == "recommended":
            assert row["recommended_option"] in row["qualified_options"]
        else:
            assert row["recommended_option"] is None
            assert row["qualified_options"] == []

    assert actual_total == 17
    assert {
        mode: sum(row["execution_mode"] == mode for row in workloads)
        for mode in (
            "qualified_provider_model",
            "deterministic",
            "blocked_non_live",
        )
    } == {
        "qualified_provider_model": 9,
        "deterministic": 3,
        "blocked_non_live": 0,
    }

    job_fit = by_workload["job_fit_evaluation"]
    assert job_fit["recommendation_status"] == "recommended"
    assert job_fit["execution_mode"] == "qualified_provider_model"
    assert job_fit["recommended_option"] == JOB_FIT_OPTIONS[0]
    assert job_fit["qualified_options"] == CURRENT_JOB_FIT_OPTIONS
    assert job_fit["effective_selection"] == JOB_FIT_OPTIONS[0]
    assert job_fit["effective_selection_source"] == (
        "applylens_recommended"
    )

    tailoring_generation = by_workload["tailoring_generation"]
    assert tailoring_generation["recommendation_status"] == "recommended"
    assert tailoring_generation["execution_mode"] == (
        "qualified_provider_model"
    )
    assert tailoring_generation["recommended_option"] == {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }
    assert tailoring_generation["qualified_options"] == [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
        }
    ]
    assert tailoring_generation["effective_selection"] == {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }
    assert tailoring_generation["effective_selection_source"] == (
        "applylens_recommended"
    )

    manual_preview = by_workload["manual_provider_preview"]
    assert manual_preview["recommendation_status"] == "recommended"
    assert manual_preview["execution_mode"] == "qualified_provider_model"
    assert manual_preview["recommended_option"] == MANUAL_PREVIEW_RECOMMENDED
    assert manual_preview["qualified_options"] == [MANUAL_PREVIEW_RECOMMENDED]
    assert manual_preview["effective_selection"] == MANUAL_PREVIEW_RECOMMENDED
    assert manual_preview["effective_selection_source"] == (
        "applylens_recommended"
    )
    assert {
        (option["provider"], option["model"])
        for option in manual_preview["qualified_options"]
    }.isdisjoint(
        {
            ("groq", "openai/gpt-oss-20b"),
            ("openai", "gpt-5-mini"),
            ("openai", "gpt-5.1"),
        }
    )

    rendered = repr(payload)
    for prohibited in (
        "execution_order",
        "task_contract_sha256",
        "qualification_binding_sha256",
        "evidence_sha256",
        "review_sha256",
        "registry_sha",
        "latency_ms",
        "estimated_cost",
        "input_tokens",
        "output_tokens",
        "historical_missing_requirement_accuracy",
        "credential",
        "raw_response",
    ):
        assert prohibited not in rendered


@pytest.mark.parametrize("selection", CURRENT_JOB_FIT_OPTIONS)
def test_job_fit_qualified_owner_overrides_become_effective(
    monkeypatch,
    selection,
):
    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        lambda owner_user_id: {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": [
                    {
                        "owner_user_id": owner_user_id,
                        "workload_id": "job_fit_evaluation",
                        **selection,
                    }
                ],
            }
        },
    )

    route = routing.read_provider_model_routing_status(
        "job_fit_evaluation",
        owner_user_id="owner-a",
    )

    assert route["requested_selection"] == selection
    assert route["requested_selection_status"] == "qualified"
    assert route["effective_selection"] == selection
    assert route["effective_selection_source"] == "user_override"


def test_stale_job_fit_owner_selection_is_retained_but_not_effective(
    monkeypatch,
):
    stale = {"provider": "openai", "model": "retired-job-fit-model"}
    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        lambda owner_user_id: {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": [
                    {
                        "owner_user_id": owner_user_id,
                        "workload_id": "job_fit_evaluation",
                        **stale,
                    }
                ],
            }
        },
    )

    route = routing.read_provider_model_routing_status(
        "job_fit_evaluation",
        owner_user_id="owner-a",
    )

    assert route["requested_selection"] == stale
    assert route["requested_selection_status"] == "no_longer_qualified"
    assert route["effective_selection"] == JOB_FIT_OPTIONS[0]
    assert route["effective_selection"] != stale
    assert route["effective_selection_source"] == (
        "applylens_recommended"
    )


def test_non_overlay_job_fit_model_is_not_currently_qualified():
    with pytest.raises(
        routing.ProviderModelSelectionNotQualifiedError
    ):
        routing.validate_current_qualified_provider_model_selection(
            "job_fit_evaluation",
            "openai",
            "gpt-4.1",
        )


def test_owner_selection_effective_state_is_scoped_validated_and_read_only(
    monkeypatch,
):
    _install_synthetic_routing_sources(monkeypatch)
    calls = []

    def list_selections(owner_user_id):
        calls.append(owner_user_id)
        selections = (
            [
                {
                    "owner_user_id": owner_user_id,
                    "workload_id": "skill_extraction",
                    "provider": "openai",
                    "model": "gpt-5-mini",
                }
            ]
            if owner_user_id == "owner-a"
            else []
        )
        return {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": selections,
            }
        }

    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        list_selections,
    )
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail(
            "routing read must not execute provider or read credentials"
        ),
    )

    owner_a = routing.read_provider_model_routing_status(
        "skill_extraction",
        owner_user_id="owner-a",
    )
    owner_b = routing.read_provider_model_routing_status(
        "skill_extraction",
        owner_user_id="owner-b",
    )

    assert owner_a["requested_selection"] == {
        "provider": "openai",
        "model": "gpt-5-mini",
    }
    assert owner_a["requested_selection_status"] == "qualified"
    assert owner_a["effective_selection"] == owner_a["requested_selection"]
    assert owner_a["effective_selection_source"] == "user_override"
    assert owner_b["requested_selection"] is None
    assert owner_b["requested_selection_status"] == "none"
    assert owner_b["effective_selection"] == owner_b["recommended_option"]
    assert owner_b["effective_selection_source"] == "applylens_recommended"
    assert calls == ["owner-a", "owner-b"]


def test_explicit_recommended_pair_remains_an_unambiguous_user_override(
    monkeypatch,
):
    _install_synthetic_routing_sources(monkeypatch)
    recommended = {
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
    }
    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        lambda owner_user_id: {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": [
                    {
                        "owner_user_id": owner_user_id,
                        "workload_id": "skill_extraction",
                        **recommended,
                    }
                ],
            }
        },
    )

    route = routing.read_provider_model_routing_status(
        "skill_extraction",
        owner_user_id="owner-a",
    )

    assert route["recommended_option"] == recommended
    assert route["requested_selection"] == recommended
    assert route["requested_selection_status"] == "qualified"
    assert route["effective_selection"] == recommended
    assert route["effective_selection_source"] == "user_override"


def test_stale_requested_selection_is_retained_but_never_effective(
    monkeypatch,
):
    _install_synthetic_routing_sources(monkeypatch)
    reads = []
    stale = {"provider": "openai", "model": "retired-model"}

    def list_selections(owner_user_id):
        reads.append(owner_user_id)
        return {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": [
                    {
                        "owner_user_id": owner_user_id,
                        "workload_id": "skill_extraction",
                        **stale,
                    }
                ],
            }
        }

    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        list_selections,
    )
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail(
            "stale routing read must not execute provider"
        ),
    )

    route = routing.read_provider_model_routing_status(
        "skill_extraction",
        owner_user_id="owner-a",
    )

    assert route["requested_selection"] == stale
    assert route["requested_selection_status"] == "no_longer_qualified"
    assert route["effective_selection"] == route["recommended_option"]
    assert route["effective_selection"] != stale
    assert route["effective_selection_source"] == "applylens_recommended"
    assert reads == ["owner-a"]


def test_blocked_non_live_mode_never_makes_persisted_selection_effective(
    monkeypatch,
):
    _install_synthetic_routing_sources(monkeypatch)
    workload_id = "manual_provider_preview"
    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        lambda owner_user_id: {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": [
                    {
                        "owner_user_id": owner_user_id,
                        "workload_id": workload_id,
                        "provider": "groq",
                        "model": "previous-model",
                    }
                ],
            }
        },
    )

    route = routing.read_provider_model_routing_status(
        workload_id,
        owner_user_id="owner-a",
    )

    assert route["requested_selection_status"] == "no_longer_qualified"
    assert route["effective_selection"] is None
    assert route["effective_selection_source"] == "blocked_non_live"


def test_current_selection_validation_uses_only_exact_qualified_pairs(
    monkeypatch,
):
    _install_synthetic_routing_sources(monkeypatch)
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail(
            "selection validation must not execute provider"
        ),
    )

    assert routing.validate_current_qualified_provider_model_selection(
        "skill_extraction",
        "openai",
        "gpt-5-mini",
    ) == {"provider": "openai", "model": "gpt-5-mini"}
    assert routing.validate_current_qualified_provider_model_selection(
        "skill_extraction",
        "groq",
        "openai/gpt-oss-20b",
    ) == {"provider": "groq", "model": "openai/gpt-oss-20b"}
    for option in JOB_FIT_OPTIONS:
        assert routing.validate_current_qualified_provider_model_selection(
            "job_fit_evaluation",
            option["provider"],
            option["model"],
        ) == option

    rejected = (
        ("skill_extraction", "openai", "rejected-model"),
        ("job_fit_evaluation", "groq", "pending-model"),
        ("job_fit_evaluation", "openai", "stale-model"),
        ("manual_provider_preview", "openai", "pending-preview-model"),
        ("unknown_workload", "openai", "gpt-5-mini"),
        ("skill_extraction", "groq", "gpt-5-mini"),
        ("skill_extraction", "openai", "catalog-only-model"),
    )
    for workload_id, provider, model in rejected:
        with pytest.raises(ValueError):
            routing.validate_current_qualified_provider_model_selection(
                workload_id,
                provider,
                model,
            )


def test_real_registry_validation_accepts_every_current_qualified_option():
    payload = routing.list_provider_model_routing_statuses()

    for route in payload["workloads"]:
        for option in route["qualified_options"]:
            assert routing.validate_current_qualified_provider_model_selection(
                route["workload_id"],
                option["provider"],
                option["model"],
            ) == option


def test_resolve_uses_authoritative_registry_and_exact_workload(
    monkeypatch,
):
    registry_payload = {"registry": "sentinel"}
    observed = {}

    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: registry_payload,
    )

    def fake_read(payload, workload_id):
        observed["payload"] = payload
        observed["workload_id"] = workload_id
        return _recommendation(workload_id=workload_id)

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        fake_read,
    )

    result = routing.resolve_recommended_user_provider_route(
        "grounded_rag_answer"
    )

    assert observed == {
        "payload": registry_payload,
        "workload_id": "grounded_rag_answer",
    }

    assert result == {
        "workload_id": "grounded_rag_answer",
        "recommendation_status": "recommended",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "selection_basis": (
            "durable_quality_tie_latency_tiebreak"
        ),
        "task_contract_sha256": "a" * 64,
        "qualification_binding_sha256": "b" * 64,
        "evidence_sha256": "c" * 64,
        "review_sha256": None,
    }


@pytest.mark.parametrize(
    "status",
    [
        "fail_closed_zero_qualified",
        "blocked_non_live",
    ],
)
def test_non_recommended_workload_fails_before_runtime(
    monkeypatch,
    status,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        lambda payload, workload_id: _recommendation(
            workload_id=workload_id,
            status=status,
            provider=None,
            model=None,
        ),
    )

    runtime_called = False

    def forbidden_runtime(**kwargs):
        nonlocal runtime_called
        runtime_called = True
        raise AssertionError("runtime must not be called")

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        forbidden_runtime,
    )

    with pytest.raises(
        routing.RecommendedProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_recommended_user_chat_completion_with_metadata(
            owner_user_id="owner-1",
            workload_id="grounded_rag_answer",
            messages=[{"role": "user", "content": "hello"}],
        )

    assert exc_info.value.recommendation_status == status
    assert runtime_called is False


def test_recommended_execution_forwards_exact_frozen_identity(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        lambda payload, workload_id: _recommendation(
            provider="groq",
            model="openai/gpt-oss-120b",
        ),
    )

    observed = {}

    def fake_runtime(**kwargs):
        observed.update(kwargs)
        return {
            "content": "ok",
            "provider": kwargs["provider"],
            "model": kwargs["model"],
        }

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        fake_runtime,
    )

    result = routing.run_recommended_user_chat_completion_with_metadata(
        owner_user_id="owner-1",
        workload_id="ambiguous_resume_adjudication",
        messages=[{"role": "user", "content": "review"}],
        temperature=0.2,
        max_tokens=321,
        response_mime_type="application/json",
        response_schema={"type": "object"},
        return_parsed=True,
        thinking_budget=123,
        database_url="postgresql://sentinel",
        database_url_env="SENTINEL_DATABASE_URL",
        psql_bin="/sentinel/psql",
        ensure_schema=False,
    )

    assert observed == {
        "owner_user_id": "owner-1",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "user",
                "content": "review",
            }
        ],
        "temperature": 0.2,
        "max_tokens": 321,
        "response_mime_type": "application/json",
        "response_schema": {"type": "object"},
        "return_parsed": True,
        "thinking_budget": 123,
        "database_url": "postgresql://sentinel",
        "database_url_env": "SENTINEL_DATABASE_URL",
        "psql_bin": "/sentinel/psql",
        "ensure_schema": False,
    }

    assert result == {
        "content": "ok",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }


def test_invalid_recommended_identity_fails_before_runtime(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        lambda payload, workload_id: _recommendation(
            workload_id=workload_id,
            status="recommended",
            provider="",
            model="",
        ),
    )

    runtime_called = False

    def forbidden_runtime(**kwargs):
        nonlocal runtime_called
        runtime_called = True
        raise AssertionError("runtime must not be called")

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        forbidden_runtime,
    )

    with pytest.raises(
        routing.RecommendedProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_recommended_user_chat_completion_with_metadata(
            owner_user_id="owner-1",
            workload_id="grounded_rag_answer",
            messages=[],
        )

    assert (
        exc_info.value.recommendation_status
        == "invalid_recommended_identity"
    )
    assert runtime_called is False


def test_policy_error_propagates_before_runtime(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "_load_authoritative_qualification_registry",
        lambda: {"registry": "sentinel"},
    )

    def fail_policy(payload, workload_id):
        raise ValueError("policy unavailable")

    monkeypatch.setattr(
        routing,
        "read_provider_model_recommendation",
        fail_policy,
    )

    runtime_called = False

    def forbidden_runtime(**kwargs):
        nonlocal runtime_called
        runtime_called = True
        raise AssertionError("runtime must not be called")

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        forbidden_runtime,
    )

    with pytest.raises(
        ValueError,
        match="policy unavailable",
    ):
        routing.run_recommended_user_chat_completion_with_metadata(
            owner_user_id="owner-1",
            workload_id="unknown",
            messages=[],
        )

    assert runtime_called is False


def _stage6b_owner_selections(monkeypatch, selection):
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
                            "workload_id": "skill_extraction",
                            **selection,
                        }
                    ]
                ),
            }
        },
    )


@pytest.mark.parametrize(
    (
        "selection",
        "expected_model",
        "expected_status",
        "expected_source",
    ),
    (
        (
            None,
            "openai/gpt-oss-20b",
            "none",
            "applylens_recommended",
        ),
        (
            {"provider": "groq", "model": "openai/gpt-oss-120b"},
            "openai/gpt-oss-120b",
            "qualified",
            "user_override",
        ),
        (
            {"provider": "openai", "model": "gpt-5-mini"},
            "openai/gpt-oss-20b",
            "no_longer_qualified",
            "applylens_recommended",
        ),
    ),
)
def test_stage6b_skill_effective_route_and_fake_runtime(
    monkeypatch,
    selection,
    expected_model,
    expected_status,
    expected_source,
):
    from src.ai import skill_llm_enricher

    _stage6b_owner_selections(monkeypatch, selection)
    executed = []

    def fake_runtime(**kwargs):
        executed.append((kwargs["provider"], kwargs["model"]))
        return {"content": "ok"}

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        fake_runtime,
    )
    status = routing.read_provider_model_routing_status(
        "skill_extraction",
        owner_user_id="owner-stage6b",
    )
    owner_route = skill_llm_enricher.resolve_effective_user_provider_route(
        "owner-stage6b",
        "skill_extraction",
    )
    result = routing.run_effective_user_chat_completion_with_metadata(
        "owner-stage6b",
        "skill_extraction",
        [],
    )

    assert status["requested_selection"] == selection
    assert status["requested_selection_status"] == expected_status
    assert status["effective_selection_source"] == expected_source
    assert owner_route == {
        "workload_id": "skill_extraction",
        "provider": "groq",
        "model": expected_model,
        "effective_selection_source": expected_source,
    }
    assert executed == [("groq", expected_model)]
    assert result == {"content": "ok"}


def test_stage6b_unrelated_grounded_rag_route_remains_v1(monkeypatch):
    _stage6b_owner_selections(monkeypatch, None)
    registry_payload = routing._load_authoritative_qualification_registry()
    v1_policy = build_provider_model_recommendation_policy(registry_payload)
    before = next(
        entry
        for entry in v1_policy["workloads"]
        if entry["workload_id"] == "grounded_rag_answer"
    )
    after = routing.read_provider_model_routing_status(
        "grounded_rag_answer",
        owner_user_id="owner-stage6b",
    )

    assert (before["provider"], before["model"]) == (
        "groq",
        "openai/gpt-oss-20b",
    )
    assert after["recommended_option"] == {
        "provider": before["provider"],
        "model": before["model"],
    }


@pytest.mark.parametrize(
    "failure_mode",
    (
        "missing",
        "malformed",
        "stale_semantics",
        "stale_task_contract",
        "20b_evidence",
        "20b_binding",
        "120b_evidence",
        "120b_binding",
        "candidate_universe",
        "pin_mismatch",
    ),
)
def test_stage6b_skill_authority_failures_never_fall_back_or_execute(
    monkeypatch,
    failure_mode,
):
    _stage6b_owner_selections(monkeypatch, None)
    artifact_path = (
        ROOT
        / routing.qualification_registry
        .RENDERER_BOUND_V2_SKILL_REGISTRY_ARTIFACT_PATH
    )
    baseline = (
        routing.qualification_registry
        .load_renderer_bound_v2_skill_qualification_registry(
            artifact_path,
            repository_root=ROOT,
        )
    )

    if failure_mode == "missing":
        def fail_load(*_args, **_kwargs):
            raise ValueError("renderer-bound Skill registry is missing")

        monkeypatch.setattr(
            routing.qualification_registry,
            "load_renderer_bound_v2_skill_qualification_registry",
            fail_load,
        )
    elif failure_mode == "pin_mismatch":
        original_pin = routing.build_finalized_skill_extraction_renderer_bound_v2_pin

        def mismatched_pin():
            pin = original_pin()
            pin["model"] = "openai/gpt-oss-120b"
            return pin

        monkeypatch.setattr(
            routing,
            "build_finalized_skill_extraction_renderer_bound_v2_pin",
            mismatched_pin,
        )
    else:
        altered = deepcopy(baseline)
        if failure_mode == "malformed":
            altered = {}
        elif failure_mode == "candidate_universe":
            altered["cells"] = altered["cells"][:-1]
        else:
            model = (
                "openai/gpt-oss-120b"
                if failure_mode.startswith("120b")
                else "openai/gpt-oss-20b"
            )
            cell = next(
                candidate
                for candidate in altered["cells"]
                if candidate["model"] == model
            )
            field = {
                "stale_semantics": (
                    "current_workload_qualification_semantics_sha256"
                ),
                "stale_task_contract": "current_task_contract_sha256",
                "20b_evidence": "evidence_sha256",
                "20b_binding": "qualification_binding_sha256",
                "120b_evidence": "evidence_sha256",
                "120b_binding": "qualification_binding_sha256",
            }[failure_mode]
            cell[field] = "0" * 64
        monkeypatch.setattr(
            routing.qualification_registry,
            "load_renderer_bound_v2_skill_qualification_registry",
            lambda *_args, **_kwargs: altered,
        )

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail(
            "invalid Skill authority must fail before provider runtime"
        ),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_effective_user_chat_completion_with_metadata(
            "owner-stage6b",
            "skill_extraction",
            [],
        )

    assert exc_info.value.routing_status == "blocked_non_live"

    unrelated = routing.resolve_effective_user_provider_route(
        "owner-stage6b",
        "grounded_rag_answer",
    )
    assert unrelated == {
        "workload_id": "grounded_rag_answer",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "effective_selection_source": "applylens_recommended",
    }


def _effective_status(
    *,
    selection=None,
    source="applylens_recommended",
    execution_mode="qualified_provider_model",
    qualified_options=None,
):
    selected = (
        {"provider": "groq", "model": "openai/gpt-oss-20b"}
        if selection is None
        else selection
    )
    options = [selected] if qualified_options is None else qualified_options
    return {
        "workload_id": "skill_extraction",
        "execution_mode": execution_mode,
        "effective_selection": selected,
        "effective_selection_source": source,
        "qualified_options": options,
    }


def test_effective_resolver_reads_exact_owner_route_and_returns_safe_metadata(
    monkeypatch,
):
    observed = []
    effective = {"provider": "openai", "model": "gpt-5-mini"}

    def fake_read(workload_id, *, owner_user_id=None):
        observed.append((workload_id, owner_user_id))
        return _effective_status(
            selection=effective,
            source="user_override",
        )

    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        fake_read,
    )

    route = routing.resolve_effective_user_provider_route(
        " owner-a ",
        " skill_extraction ",
    )

    assert observed == [("skill_extraction", "owner-a")]
    assert route == {
        "workload_id": "skill_extraction",
        "provider": "openai",
        "model": "gpt-5-mini",
        "effective_selection_source": "user_override",
    }


@pytest.mark.parametrize(
    ("source", "selection"),
    (
        (
            "applylens_recommended",
            {"provider": "groq", "model": "openai/gpt-oss-20b"},
        ),
        (
            "user_override",
            {"provider": "groq", "model": "openai/gpt-oss-20b"},
        ),
    ),
)
def test_effective_resolver_preserves_recommended_and_explicit_sources(
    monkeypatch,
    source,
    selection,
):
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda workload_id, *, owner_user_id=None: _effective_status(
            selection=selection,
            source=source,
        ),
    )

    route = routing.resolve_effective_user_provider_route(
        "owner-a",
        "skill_extraction",
    )

    assert (route["provider"], route["model"]) == (
        selection["provider"],
        selection["model"],
    )
    assert route["effective_selection_source"] == source


def test_stale_override_executes_current_effective_recommendation(
    monkeypatch,
):
    _install_synthetic_routing_sources(monkeypatch)
    stale = {"provider": "openai", "model": "retired-model"}
    monkeypatch.setattr(
        routing,
        "list_user_ai_task_model_selections_payload",
        lambda owner_user_id: {
            "data": {
                "owner_user_id": owner_user_id,
                "selections": [
                    {
                        "owner_user_id": owner_user_id,
                        "workload_id": "skill_extraction",
                        **stale,
                    }
                ],
            }
        },
    )
    executed = []

    def fake_runtime(**kwargs):
        executed.append((kwargs["provider"], kwargs["model"]))
        return {"content": "ok"}

    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        fake_runtime,
    )

    route = routing.resolve_effective_user_provider_route(
        "owner-a",
        "skill_extraction",
    )
    result = routing.run_effective_user_chat_completion_with_metadata(
        "owner-a",
        "skill_extraction",
        [],
    )

    assert route == {
        "workload_id": "skill_extraction",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "effective_selection_source": "applylens_recommended",
    }
    assert executed == [("groq", "openai/gpt-oss-20b")]
    assert stale not in [
        {"provider": provider, "model": model}
        for provider, model in executed
    ]
    assert result == {"content": "ok"}


@pytest.mark.parametrize("execution_mode", ("deterministic", "blocked_non_live"))
def test_non_llm_effective_routes_fail_before_runtime(
    monkeypatch,
    execution_mode,
):
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda workload_id, *, owner_user_id=None: _effective_status(
            selection=None,
            source=execution_mode,
            execution_mode=execution_mode,
            qualified_options=[],
        ),
    )
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: pytest.fail("runtime must not execute"),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_effective_user_chat_completion_with_metadata(
            "owner-a",
            "skill_extraction",
            [],
        )

    assert exc_info.value.routing_status == execution_mode


@pytest.mark.parametrize(
    "selection",
    (
        None,
        {},
        {"provider": "", "model": "gpt-5-mini"},
        {"provider": "openai", "model": ""},
        {"provider": "openai", "model": "gpt-5-mini", "extra": "x"},
    ),
)
def test_malformed_effective_selection_fails_before_runtime(
    monkeypatch,
    selection,
):
    status = _effective_status()
    status["effective_selection"] = selection
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda workload_id, *, owner_user_id=None: status,
    )
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: pytest.fail("runtime must not execute"),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_effective_user_chat_completion_with_metadata(
            "owner-a",
            "skill_extraction",
            [],
        )

    assert exc_info.value.routing_status == "invalid_effective_selection"


def test_blank_owner_fails_before_routing_read_or_runtime(monkeypatch):
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda *_args, **_kwargs: pytest.fail("route must not be read"),
    )
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: pytest.fail("runtime must not execute"),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_effective_user_chat_completion_with_metadata(
            " ",
            "skill_extraction",
            [],
        )

    assert exc_info.value.routing_status == "invalid_owner"


def test_blank_workload_fails_before_routing_read_or_runtime(monkeypatch):
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda *_args, **_kwargs: pytest.fail("route must not be read"),
    )
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: pytest.fail("runtime must not execute"),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.run_effective_user_chat_completion_with_metadata(
            "owner-a",
            " ",
            [],
        )

    assert exc_info.value.routing_status == "invalid_workload"


def test_unknown_workload_is_a_bounded_effective_route_failure(monkeypatch):
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda workload_id, *, owner_user_id=None: (_ for _ in ()).throw(
            ValueError("raw registry evidence must stay private")
        ),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.resolve_effective_user_provider_route(
            "owner-a",
            "unknown",
        )

    assert exc_info.value.routing_status == "routing_status_unavailable"
    assert "raw registry evidence" not in str(exc_info.value)


def test_effective_source_must_be_authorized(monkeypatch):
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda workload_id, *, owner_user_id=None: _effective_status(
            source="provider_preference",
        ),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.resolve_effective_user_provider_route(
            "owner-a",
            "skill_extraction",
        )

    assert (
        exc_info.value.routing_status
        == "invalid_effective_selection_source"
    )


def test_effective_pair_must_remain_currently_qualified(monkeypatch):
    monkeypatch.setattr(
        routing,
        "read_provider_model_routing_status",
        lambda workload_id, *, owner_user_id=None: _effective_status(
            qualified_options=[
                {"provider": "openai", "model": "gpt-5-mini"}
            ],
        ),
    )

    with pytest.raises(
        routing.EffectiveProviderRoutingUnavailableError
    ) as exc_info:
        routing.resolve_effective_user_provider_route(
            "owner-a",
            "skill_extraction",
        )

    assert (
        exc_info.value.routing_status
        == "effective_selection_not_qualified"
    )


def test_effective_execution_resolves_once_and_forwards_every_parameter(
    monkeypatch,
):
    resolve_calls = []
    runtime_calls = []

    def fake_resolve(owner_user_id, workload_id):
        resolve_calls.append((owner_user_id, workload_id))
        return {
            "workload_id": workload_id,
            "provider": "openai",
            "model": "gpt-5-mini",
            "effective_selection_source": "user_override",
        }

    def fake_runtime(**kwargs):
        runtime_calls.append(kwargs)
        return {"content": "ok"}

    monkeypatch.setattr(
        routing,
        "resolve_effective_user_provider_route",
        fake_resolve,
    )
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        fake_runtime,
    )
    messages = [{"role": "user", "content": "hello"}]
    schema = {"type": "object"}

    result = routing.run_effective_user_chat_completion_with_metadata(
        "owner-a",
        "skill_extraction",
        messages,
        temperature=0.3,
        max_tokens=321,
        response_mime_type="application/json",
        response_schema=schema,
        return_parsed=True,
        thinking_budget=123,
        database_url="postgresql://sentinel",
        database_url_env="SENTINEL_DATABASE_URL",
        psql_bin="/sentinel/psql",
        ensure_schema=False,
    )

    assert resolve_calls == [("owner-a", "skill_extraction")]
    assert runtime_calls == [
        {
            "owner_user_id": "owner-a",
            "provider": "openai",
            "model": "gpt-5-mini",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 321,
            "response_mime_type": "application/json",
            "response_schema": schema,
            "return_parsed": True,
            "thinking_budget": 123,
            "database_url": "postgresql://sentinel",
            "database_url_env": "SENTINEL_DATABASE_URL",
            "psql_bin": "/sentinel/psql",
            "ensure_schema": False,
        }
    ]
    assert result == {"content": "ok"}


def test_recommended_execution_does_not_consume_effective_resolver(
    monkeypatch,
):
    monkeypatch.setattr(
        routing,
        "resolve_effective_user_provider_route",
        lambda *_args, **_kwargs: pytest.fail(
            "recommended-only behavior must remain independent"
        ),
    )
    monkeypatch.setattr(
        routing,
        "resolve_recommended_user_provider_route",
        lambda workload_id: {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        },
    )
    observed = []
    monkeypatch.setattr(
        routing,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: observed.append(kwargs) or {"content": "ok"},
    )

    routing.run_recommended_user_chat_completion_with_metadata(
        "owner-a",
        "skill_extraction",
        [],
    )

    assert observed[0]["provider"] == "groq"
    assert observed[0]["model"] == "openai/gpt-oss-20b"


def test_public_execution_bridge_exposes_no_provider_model_or_fallback_override():
    for bridge in (
        routing.run_recommended_user_chat_completion_with_metadata,
        routing.run_effective_user_chat_completion_with_metadata,
    ):
        parameters = inspect.signature(bridge).parameters

        assert "provider" not in parameters
        assert "model" not in parameters
        assert "fallback_enabled" not in parameters
        assert "preferred_provider" not in parameters


def test_bridge_does_not_own_model_ranking_or_preferred_provider_logic():
    source = OWNER.read_text(encoding="utf-8")

    assert "resolve_user_preferred_provider" not in source
    assert "preferred_provider" not in source
    assert "fallback_enabled" not in source
    assert "COST_SELECTION_WEIGHT" not in source


def test_bridge_import_boundary_has_no_provider_sdk_or_direct_transport():
    source = OWNER.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)

    assert not any(
        module == prohibited
        or module.startswith(prohibited + ".")
        for module in imported_modules
        for prohibited in (
            "groq",
            "openai",
            "google",
            "requests",
            "httpx",
            "src.ai.llm_client",
        )
    )

    assert "get_user_provider_credential" not in source
    assert "decrypt_user_provider" not in source
    assert "os.environ" not in source


def test_effective_bridge_has_only_approved_production_task_owner_callsites():
    references = []
    symbol = "run_effective_user_chat_completion_with_metadata"

    for path in (ROOT / "src").rglob("*.py"):
        if path.resolve() == OWNER.resolve():
            continue
        if symbol in path.read_text(encoding="utf-8"):
            references.append(path.relative_to(ROOT).as_posix())

    assert sorted(references) == [
        "src/app/services.py",
    ]


def test_only_approved_api_consumes_bridge():
    references = []

    for path in (ROOT / "src").rglob("*.py"):
        if path.resolve() == OWNER.resolve():
            continue

        if (
            "provider_model_routing_service"
            in path.read_text(encoding="utf-8")
        ):
            references.append(
                path.relative_to(ROOT).as_posix()
            )

    assert sorted(references) == [
        "src/app/api.py",
        "src/app/user_ai_settings_service.py",
    ]


# ---------------------------------------------------------------------------
# Stage 3: registry-dependent workload-local authority tests.
# This suite has no autouse registry stub, so the real Stage 2A representation
# is exercised here.
# ---------------------------------------------------------------------------


from src.evaluation import (  # noqa: E402
    provider_model_recommendation_policy as _stage3_policy,
)


import json as _stage3_json  # noqa: E402

from src.evaluation import (  # noqa: E402
    controlled_production_parity_benchmark as _stage3_parity,
)
from src.evaluation import (  # noqa: E402
    controlled_provider_qualification_registry as _stage3_registry,
)
from src.evaluation.controlled_provider_benchmark_plan import (  # noqa: E402
    build_controlled_provider_benchmark_plan as _stage3_build_plan,
    controlled_provider_benchmark_plan_sha256 as _stage3_plan_sha,
    legacy_case_alias_map as _stage3_alias_map,
)
from src.evaluation.provider_fixture_benchmark import (  # noqa: E402
    fixture_case_corpus_sha256 as _stage3_corpus_sha,
    load_fixture_case_corpus as _stage3_load_corpus,
)

STAGE3_CORPUS_SHA256 = (
    "59180e4064dd74759c6ecd8630478225b191f942b68fb1880e172fe07ee80aec"
)
STAGE3_HISTORICAL_PLAN_SHA256 = (
    "f2dcf5345442009915819432a9c1fc9342de40561eb6824c1518dcd31e99d3bf"
)
STAGE3_PLAN_SHA256 = (
    "bacc7eaa4524199ba293e2d50232f5a8c6cf61014ad8dc89c3dd30d334654162"
)
STAGE3_REGISTRY_SHA256 = (
    "6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"
)
STAGE3_SYNTHETIC_SEMANTICS = "9" * 64
STAGE3_OTHER_SEMANTICS = "8" * 64


def _stage3_v1_registry():
    return _stage3_json.loads(
        (
            ROOT
            / "outputs"
            / "provider_benchmark"
            / "provider-qualification-registry.json"
        ).read_text(encoding="utf-8")
    )


def _stage3_legacy_projection(source=None):
    payload = _stage3_v1_registry() if source is None else deepcopy(source)
    corpus = _stage3_load_corpus()
    plan = _stage3_build_plan(corpus=corpus)
    semantics = {
        workload_id: _stage3_parity.workload_qualification_semantics_sha256(
            workload_id, plan=plan, corpus=corpus
        )
        for workload_id in sorted(
            {cell["workload_id"] for cell in payload["cells"]}
        )
    }
    return _stage3_registry.project_registry_to_renderer_bound_generation(
        payload,
        current_workload_qualification_semantics_sha256_by_workload=semantics,
    )


def _stage3_promote(workload_id, winner_index, *, semantics):
    """Build an in-memory renderer-bound registry with one synthetic winner.

    Test-only. The promoted identity is deliberately not the V1 winner.
    """

    source = _stage3_v1_registry()
    legacy = _stage3_legacy_projection(source)
    cells = [
        cell
        for cell in source["cells"]
        if cell["workload_id"] == workload_id
    ]
    promoted = []
    for index, cell in enumerate(cells):
        candidate = deepcopy(cell)
        if index == winner_index:
            candidate["status"] = "qualified"
            candidate["status_reasons"] = [
                "qualification_requirements_satisfied"
            ]
        promoted.append(
            _stage3_registry.build_renderer_bound_qualification_cell(
                base_cell=candidate,
                qualification_semantics_generation="renderer_bound_v1",
                current_workload_qualification_semantics_sha256=semantics,
                tested_workload_qualification_semantics_sha256=semantics,
            )
        )
    registry = deepcopy(legacy)
    registry["cells"] = [
        cell
        for cell in legacy["cells"]
        if cell["workload_id"] != workload_id
    ] + promoted
    _stage3_registry.validate_renderer_bound_qualification_registry(registry)
    return registry, promoted


def _stage3_pin(promoted, winner_index, *, semantics, basis="synthetic_basis"):
    winner = promoted[winner_index]
    return {
        "pin_version": _stage3_policy.RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
        "workload_id": winner["workload_id"],
        "provider": winner["provider"],
        "model": winner["model"],
        "selection_basis": basis,
        "expected_status": "qualified",
        "expected_status_reasons": list(winner["status_reasons"]),
        "expected_qualification_semantics_generation": "renderer_bound_v1",
        "expected_current_workload_qualification_semantics_sha256": semantics,
        "expected_tested_workload_qualification_semantics_sha256": semantics,
        "expected_current_task_contract_sha256": winner[
            "current_task_contract_sha256"
        ],
        "expected_tested_task_contract_sha256": winner[
            "tested_task_contract_sha256"
        ],
        "expected_qualification_binding_sha256": winner[
            "qualification_binding_sha256"
        ],
        "expected_evidence_sha256": winner["evidence_sha256"],
        "expected_review_sha256": winner["review_sha256"],
        "expected_candidate_universe": [
            {
                "provider": cell["provider"],
                "model": cell["model"],
                "status": cell["status"],
            }
            for cell in promoted
        ],
    }


def test_stage3_v1_authority_is_unchanged():
    source = _stage3_v1_registry()
    corpus = _stage3_load_corpus()

    assert _stage3_policy.RECOMMENDATION_POLICY_VERSION == (
        "provider-model-recommendation-policy-v1"
    )
    assert _stage3_policy.SOURCE_QUALIFICATION_REGISTRY_SHA256 == (
        STAGE3_REGISTRY_SHA256
    )
    assert len(
        _stage3_policy.build_provider_model_recommendation_policy(source)["workloads"]
    ) == 12
    assert _stage3_corpus_sha(corpus) == STAGE3_CORPUS_SHA256
    assert _stage3_plan_sha(_stage3_build_plan(corpus=corpus)) == (
        STAGE3_PLAN_SHA256
    )
    assert STAGE3_PLAN_SHA256 != STAGE3_HISTORICAL_PLAN_SHA256
    assert len(_stage3_alias_map(corpus)) == 15
    assert _stage3_registry.provider_qualification_registry_sha256(source) == (
        STAGE3_REGISTRY_SHA256
    )


def test_stage3_legacy_projection_promotes_no_workload():
    legacy = _stage3_legacy_projection()
    prospective = (
        _stage3_policy.build_prospective_renderer_bound_recommendation_policy(legacy)
    )

    assert prospective["policy_version"] == (
        _stage3_policy.RENDERER_BOUND_RECOMMENDATION_POLICY_VERSION
    )
    assert len(prospective["workloads"]) == 12
    for entry in prospective["workloads"]:
        assert entry["recommendation_status"] == "fail_closed_zero_qualified"
        assert entry["provider"] is None and entry["model"] is None
        assert entry["evidence_sha256"] is None
        assert entry["review_sha256"] is None


def test_stage3_v1_frozen_recommendations_are_not_valid_pins():
    legacy = _stage3_legacy_projection()

    for workload_id, frozen in _stage3_policy._FROZEN_RECOMMENDATIONS.items():
        # A V1 frozen entry is not even shaped like a renderer-bound pin.
        with pytest.raises(ValueError):
            _stage3_policy.validate_renderer_bound_recommendation_pin(
                {"workload_id": workload_id, **frozen}
            )
        # And its identity cannot be validated against legacy cells.
        legacy_cells = [
            cell
            for cell in legacy["cells"]
            if cell["workload_id"] == workload_id
        ]
        assert legacy_cells
        assert all(cell["status"] != "qualified" for cell in legacy_cells)
        assert all(
            cell["qualification_semantics_generation"]
            == "legacy_no_renderer_binding"
            for cell in legacy_cells
        )


def test_stage3_legacy_cell_cannot_produce_a_renderer_bound_recommendation():
    legacy = _stage3_legacy_projection()
    cell = next(
        row
        for row in legacy["cells"]
        if row["workload_id"] == "skill_extraction"
    )
    pin = {
        "pin_version": _stage3_policy.RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
        "workload_id": "skill_extraction",
        "provider": cell["provider"],
        "model": cell["model"],
        "selection_basis": "synthetic_basis",
        "expected_status": "qualified",
        "expected_status_reasons": ["qualification_requirements_satisfied"],
        "expected_qualification_semantics_generation": "renderer_bound_v1",
        "expected_current_workload_qualification_semantics_sha256": (
            cell["current_workload_qualification_semantics_sha256"]
        ),
        "expected_tested_workload_qualification_semantics_sha256": (
            cell["current_workload_qualification_semantics_sha256"]
        ),
        "expected_current_task_contract_sha256": cell[
            "current_task_contract_sha256"
        ],
        "expected_tested_task_contract_sha256": cell[
            "tested_task_contract_sha256"
        ],
        "expected_qualification_binding_sha256": cell[
            "qualification_binding_sha256"
        ],
        "expected_evidence_sha256": cell["evidence_sha256"],
        "expected_review_sha256": cell["review_sha256"],
        "expected_candidate_universe": [
            {
                "provider": row["provider"],
                "model": row["model"],
                "status": row["status"],
            }
            for row in legacy["cells"]
            if row["workload_id"] == "skill_extraction"
        ],
    }
    with pytest.raises(ValueError):
        _stage3_policy.validate_renderer_bound_workload_recommendation(
            legacy, pin=pin
        )


def test_stage3_workload_local_validation_and_isolation():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    pin = _stage3_pin(promoted, 1, semantics=STAGE3_SYNTHETIC_SEMANTICS)

    assert _stage3_policy.validate_renderer_bound_workload_recommendation(
        registry, pin=pin
    )
    entry = _stage3_policy.build_renderer_bound_workload_recommendation(
        registry, pin=pin
    )
    assert entry["recommendation_status"] == "recommended"
    assert entry["provider"] == promoted[1]["provider"]
    assert entry["model"] == promoted[1]["model"]

    # Mutating an unrelated workload must not affect this workload.
    unrelated = deepcopy(registry)
    for cell in unrelated["cells"]:
        if cell["workload_id"] == "tailoring_judge":
            cell["status_reasons"] = list(cell["status_reasons"]) + [
                "renderer_semantics_superseded"
            ]
            cell["qualification_binding_sha256"] = (
                _stage3_registry.renderer_bound_qualification_binding_sha256(
                    cell
                )
            )
    assert _stage3_policy.validate_renderer_bound_workload_recommendation(
        unrelated, pin=pin
    )


def test_stage3_candidate_universe_changes_fail_closed():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    pin = _stage3_pin(promoted, 1, semantics=STAGE3_SYNTHETIC_SEMANTICS)

    removed = deepcopy(registry)
    removed["cells"] = [
        cell
        for cell in removed["cells"]
        if not (
            cell["workload_id"] == "job_fit_evaluation"
            and cell["provider"] == "openai"
            and cell["model"] == "gpt-5.1"
        )
    ]
    with pytest.raises(ValueError):
        _stage3_policy.validate_renderer_bound_workload_recommendation(
            removed, pin=pin
        )

    shrunk_pin = deepcopy(pin)
    shrunk_pin["expected_candidate_universe"] = shrunk_pin[
        "expected_candidate_universe"
    ][:3]
    with pytest.raises(ValueError):
        _stage3_policy.validate_renderer_bound_workload_recommendation(
            registry, pin=shrunk_pin
        )

    changed_status = deepcopy(pin)
    for candidate in changed_status["expected_candidate_universe"]:
        if candidate["status"] == "rejected":
            candidate["status"] = "stale"
            break
    with pytest.raises(ValueError):
        _stage3_policy.validate_renderer_bound_workload_recommendation(
            registry, pin=changed_status
        )


def test_stage3_winner_authority_changes_fail_closed():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    pin = _stage3_pin(promoted, 1, semantics=STAGE3_SYNTHETIC_SEMANTICS)

    for field in (
        "expected_evidence_sha256",
        "expected_qualification_binding_sha256",
        "expected_current_workload_qualification_semantics_sha256",
        "expected_current_task_contract_sha256",
    ):
        altered = deepcopy(pin)
        altered[field] = "7" * 64
        with pytest.raises(ValueError):
            _stage3_policy.validate_renderer_bound_workload_recommendation(
                registry, pin=altered
            )

    # A stale workload-semantics binding on the winner fails closed.
    drifted_registry, drifted_promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    for cell in drifted_registry["cells"]:
        if (
            cell["workload_id"] == "job_fit_evaluation"
            and cell["provider"] == drifted_promoted[1]["provider"]
            and cell["model"] == drifted_promoted[1]["model"]
        ):
            cell["current_workload_qualification_semantics_sha256"] = (
                STAGE3_OTHER_SEMANTICS
            )
            cell["qualification_binding_sha256"] = (
                _stage3_registry.renderer_bound_qualification_binding_sha256(
                    cell
                )
            )
    with pytest.raises(ValueError):
        _stage3_policy.validate_renderer_bound_workload_recommendation(
            drifted_registry, pin=pin
        )


def test_stage3_unpinned_workload_never_inherits_a_v1_winner():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    pin = _stage3_pin(promoted, 1, semantics=STAGE3_SYNTHETIC_SEMANTICS)

    prospective = (
        _stage3_policy.build_prospective_renderer_bound_recommendation_policy(
            registry,
            pins_by_workload={"job_fit_evaluation": pin},
        )
    )
    by_workload = {
        entry["workload_id"]: entry for entry in prospective["workloads"]
    }
    assert by_workload["job_fit_evaluation"]["recommendation_status"] == (
        "recommended"
    )
    for workload_id, entry in by_workload.items():
        if workload_id == "job_fit_evaluation":
            continue
        assert entry["recommendation_status"] == "fail_closed_zero_qualified"
        assert entry["provider"] is None and entry["model"] is None

    # A workload holding renderer-bound qualified cells cannot be left unpinned.
    with pytest.raises(ValueError):
        _stage3_policy.build_prospective_renderer_bound_recommendation_policy(registry)


# ---------------------------------------------------------------------------
# Stage 3: renderer-bound Job Fit overlay authority (explicit pin only).
# ---------------------------------------------------------------------------


def test_stage3_v1_job_fit_overlay_route_is_unchanged():
    source = _stage3_v1_registry()
    overlay = job_fit_overlay.build_job_fit_provider_model_qualification_overlay(
        source
    )

    assert overlay["recommendation_status"] == "recommended"
    assert overlay["provider"] == "groq"
    assert overlay["model"] == "openai/gpt-oss-20b"
    assert overlay["selection_basis"] == (
        "reviewed_production_aligned_quality_tie_latency_tiebreak"
    )
    assert job_fit_overlay._SELECTION_BASIS == overlay["selection_basis"]
    assert job_fit_overlay._EXPECTED_IDENTITIES[0] == ("groq", "openai/gpt-oss-20b")


def test_stage3_renderer_bound_job_fit_requires_an_explicit_pin():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )

    # No pin at all, and no historical default is substituted.
    with pytest.raises(TypeError):
        job_fit_overlay.build_renderer_bound_job_fit_overlay(registry)

    # A V1-shaped selection is not a renderer-bound pin.
    with pytest.raises(ValueError):
        job_fit_overlay.build_renderer_bound_job_fit_overlay(
            registry,
            pin={
                "workload_id": "job_fit_evaluation",
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "selection_basis": job_fit_overlay._SELECTION_BASIS,
            },
        )


def test_stage3_renderer_bound_job_fit_uses_only_the_pinned_winner():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    pin = _stage3_pin(
        promoted,
        1,
        semantics=STAGE3_SYNTHETIC_SEMANTICS,
        basis="synthetic_future_basis_pending_review",
    )

    overlay = job_fit_overlay.build_renderer_bound_job_fit_overlay(
        registry, pin=pin
    )

    assert overlay["overlay_version"] == (
        job_fit_overlay.RENDERER_BOUND_JOB_FIT_OVERLAY_VERSION
    )
    assert overlay["recommendation_status"] == "recommended"
    # The synthetic pin deliberately selects a candidate that is NOT the
    # historical V1 winner, proving no historical promotion occurs.
    assert (overlay["provider"], overlay["model"]) == (
        promoted[1]["provider"],
        promoted[1]["model"],
    )
    assert (overlay["provider"], overlay["model"]) != (
        job_fit_overlay._EXPECTED_IDENTITIES[0]
    )
    assert overlay["selection_basis"] == "synthetic_future_basis_pending_review"
    assert overlay["selection_basis"] != job_fit_overlay._SELECTION_BASIS
    assert overlay["qualification_semantics_generation"] == "renderer_bound_v1"
    assert overlay["qualified_options"] == [
        {"provider": promoted[1]["provider"], "model": promoted[1]["model"]}
    ]


def test_stage3_renderer_bound_job_fit_fails_closed_on_authority_change():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    pin = _stage3_pin(promoted, 1, semantics=STAGE3_SYNTHETIC_SEMANTICS)

    # Candidate evidence change.
    evidence_changed = deepcopy(registry)
    for cell in evidence_changed["cells"]:
        if (
            cell["workload_id"] == "job_fit_evaluation"
            and cell["provider"] == promoted[1]["provider"]
            and cell["model"] == promoted[1]["model"]
        ):
            cell["evidence_sha256"] = "4" * 64
            cell["qualification_binding_sha256"] = (
                _stage3_registry.renderer_bound_qualification_binding_sha256(
                    cell
                )
            )
    with pytest.raises(ValueError):
        job_fit_overlay.build_renderer_bound_job_fit_overlay(
            evidence_changed, pin=pin
        )

    # Explicit winner identity change.
    other_winner = deepcopy(pin)
    other_winner["provider"] = promoted[0]["provider"]
    other_winner["model"] = promoted[0]["model"]
    with pytest.raises(ValueError):
        job_fit_overlay.build_renderer_bound_job_fit_overlay(
            registry, pin=other_winner
        )

    # Selection basis is pin-supplied, so a differing basis is a different pin.
    rebased = deepcopy(pin)
    rebased["selection_basis"] = "another_basis"
    rebuilt = job_fit_overlay.build_renderer_bound_job_fit_overlay(
        registry, pin=rebased
    )
    assert rebuilt["selection_basis"] == "another_basis"

    # Incomplete candidate set.
    partial = deepcopy(pin)
    partial["expected_candidate_universe"] = partial[
        "expected_candidate_universe"
    ][:3]
    with pytest.raises(ValueError):
        job_fit_overlay.build_renderer_bound_job_fit_overlay(
            registry, pin=partial
        )


def test_stage3_renderer_bound_job_fit_ignores_unrelated_workloads():
    registry, promoted = _stage3_promote(
        "job_fit_evaluation", 1, semantics=STAGE3_SYNTHETIC_SEMANTICS
    )
    pin = _stage3_pin(promoted, 1, semantics=STAGE3_SYNTHETIC_SEMANTICS)
    baseline = job_fit_overlay.build_renderer_bound_job_fit_overlay(
        registry, pin=pin
    )

    unrelated = deepcopy(registry)
    unrelated["cells"] = [
        cell
        for cell in unrelated["cells"]
        if cell["workload_id"] != "grounded_rag_answer"
    ]
    assert job_fit_overlay.build_renderer_bound_job_fit_overlay(
        unrelated, pin=pin
    ) == baseline

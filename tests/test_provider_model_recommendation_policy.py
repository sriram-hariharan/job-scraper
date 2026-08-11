from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.evaluation import provider_model_recommendation_policy as policy


ROOT = Path(__file__).resolve().parents[1]
OWNER = (
    ROOT
    / "src/evaluation/provider_model_recommendation_policy.py"
)


def _recommended_cell(workload_id, expected):
    return {
        "workload_id": workload_id,
        "provider": expected["provider"],
        "model": expected["model"],
        "status": "qualified",
        "status_reasons": [
            "qualification_requirements_satisfied"
        ],
        "current_task_contract_sha256": expected[
            "task_contract_sha256"
        ],
        "tested_task_contract_sha256": expected[
            "task_contract_sha256"
        ],
        "qualification_binding_sha256": expected[
            "qualification_binding_sha256"
        ],
        "evidence_sha256": expected["evidence_sha256"],
        "review_sha256": expected["review_sha256"],
    }


def _synthetic_registry():
    cells = []

    for workload_id in policy._WORKLOAD_ORDER:
        if workload_id in policy._FROZEN_RECOMMENDATIONS:
            cells.append(
                _recommended_cell(
                    workload_id,
                    policy._FROZEN_RECOMMENDATIONS[workload_id],
                )
            )
        elif workload_id in policy._FAIL_CLOSED_WORKLOADS:
            cells.append(
                {
                    "workload_id": workload_id,
                    "provider": "synthetic",
                    "model": "synthetic-rejected-model",
                    "status": "rejected",
                    "status_reasons": ["benchmark_failed"],
                    "current_task_contract_sha256": "a" * 64,
                    "tested_task_contract_sha256": "a" * 64,
                    "qualification_binding_sha256": "b" * 64,
                    "evidence_sha256": "c" * 64,
                    "review_sha256": None,
                }
            )
        elif workload_id in policy._BLOCKED_NON_LIVE_WORKLOADS:
            for index in range(4):
                cells.append(
                    {
                        "workload_id": workload_id,
                        "provider": "synthetic",
                        "model": f"blocked-{index}",
                        "status": "pending",
                        "status_reasons": [
                            "task_contract_missing"
                        ],
                        "current_task_contract_sha256": None,
                        "tested_task_contract_sha256": None,
                        "qualification_binding_sha256": "d" * 64,
                        "evidence_sha256": None,
                        "review_sha256": None,
                    }
                )

    return {"cells": cells}


@pytest.fixture(autouse=True)
def isolated_registry_validation(monkeypatch):
    monkeypatch.setattr(
        policy.qualification_registry,
        "validate_provider_qualification_registry",
        lambda payload: True,
    )
    monkeypatch.setattr(
        policy.qualification_registry,
        "provider_qualification_registry_sha256",
        lambda payload: policy.SOURCE_QUALIFICATION_REGISTRY_SHA256,
    )


def test_policy_has_exact_frozen_6_5_1_split():
    result = policy.build_provider_model_recommendation_policy(
        _synthetic_registry()
    )

    statuses = [
        entry["recommendation_status"]
        for entry in result["workloads"]
    ]

    assert len(result["workloads"]) == 12
    assert statuses.count("recommended") == 6
    assert statuses.count("fail_closed_zero_qualified") == 5
    assert statuses.count("blocked_non_live") == 1

    assert result["cost_selection_weight"] == 0
    assert result["source_registry_sha256"] == (
        policy.SOURCE_QUALIFICATION_REGISTRY_SHA256
    )

    assert all(
        value is False
        for value in result["authority_invariants"].values()
    )


def test_exact_six_recommendation_identities_and_bindings_are_frozen():
    result = policy.build_provider_model_recommendation_policy(
        _synthetic_registry()
    )

    recommended = {
        entry["workload_id"]: entry
        for entry in result["workloads"]
        if entry["recommendation_status"] == "recommended"
    }

    assert set(recommended) == set(
        policy._FROZEN_RECOMMENDATIONS
    )

    for workload_id, expected in (
        policy._FROZEN_RECOMMENDATIONS.items()
    ):
        entry = recommended[workload_id]

        assert entry["provider"] == expected["provider"]
        assert entry["model"] == expected["model"]
        assert (
            entry["selection_basis"]
            == expected["selection_basis"]
        )
        assert (
            entry["task_contract_sha256"]
            == expected["task_contract_sha256"]
        )
        assert (
            entry["qualification_binding_sha256"]
            == expected["qualification_binding_sha256"]
        )
        assert (
            entry["evidence_sha256"]
            == expected["evidence_sha256"]
        )
        assert (
            entry["review_sha256"]
            == expected["review_sha256"]
        )


def test_policy_is_deterministic_and_does_not_mutate_input():
    source = _synthetic_registry()
    snapshot = deepcopy(source)

    first = policy.build_provider_model_recommendation_policy(
        source
    )
    second = policy.build_provider_model_recommendation_policy(
        source
    )

    assert first == second
    assert source == snapshot


def test_registry_digest_change_requires_explicit_review(
    monkeypatch,
):
    monkeypatch.setattr(
        policy.qualification_registry,
        "provider_qualification_registry_sha256",
        lambda payload: "0" * 64,
    )

    with pytest.raises(
        ValueError,
        match="explicit recommendation review required",
    ):
        policy.build_provider_model_recommendation_policy(
            _synthetic_registry()
        )


def test_frozen_winner_cannot_silently_become_rejected():
    payload = _synthetic_registry()

    target = next(
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == "skill_extraction"
    )
    target["status"] = "rejected"

    with pytest.raises(
        ValueError,
        match="no longer qualified",
    ):
        policy.build_provider_model_recommendation_policy(payload)


def test_frozen_winner_binding_change_fails_closed():
    payload = _synthetic_registry()

    target = next(
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == "jd_intelligence"
    )
    target["qualification_binding_sha256"] = "0" * 64

    with pytest.raises(
        ValueError,
        match="qualification binding changed",
    ):
        policy.build_provider_model_recommendation_policy(payload)


def test_fail_closed_workload_cannot_auto_promote_new_model():
    payload = _synthetic_registry()

    target = next(
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == "tailoring_generation"
    )
    target["status"] = "qualified"

    with pytest.raises(
        ValueError,
        match="automatic replacement is prohibited",
    ):
        policy.build_provider_model_recommendation_policy(payload)


def test_blocked_non_live_workload_cannot_gain_evidence_silently():
    payload = _synthetic_registry()

    target = next(
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == "manual_provider_preview"
    )
    target["evidence_sha256"] = "1" * 64

    with pytest.raises(
        ValueError,
        match="unexpectedly contains qualification evidence",
    ):
        policy.build_provider_model_recommendation_policy(payload)


def test_read_one_workload_returns_recommendation_or_fail_closed_state():
    payload = _synthetic_registry()

    recommended = policy.read_provider_model_recommendation(
        payload,
        "tailoring_refinement",
    )
    fail_closed = policy.read_provider_model_recommendation(
        payload,
        "manual_scan_phrase",
    )

    assert recommended["recommendation_status"] == "recommended"
    assert recommended["provider"] == "groq"
    assert recommended["model"] == "openai/gpt-oss-120b"

    assert (
        fail_closed["recommendation_status"]
        == "fail_closed_zero_qualified"
    )
    assert fail_closed["provider"] is None
    assert fail_closed["model"] is None


def test_unknown_workload_fails_closed():
    with pytest.raises(
        ValueError,
        match="not part of the frozen recommendation policy",
    ):
        policy.read_provider_model_recommendation(
            _synthetic_registry(),
            "unknown_task",
        )


def test_owner_has_no_provider_sdk_network_environment_or_write_imports():
    source = OWNER.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_roots = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_roots.add(node.module.split(".")[0])

    assert not imported_roots.intersection(
        {
            "groq",
            "openai",
            "google",
            "requests",
            "httpx",
            "dotenv",
            "socket",
            "os",
            "pathlib",
            "subprocess",
        }
    )

    prohibited_attributes = {
        "getenv",
        "environ",
        "open",
        "write_text",
        "write_bytes",
        "unlink",
        "replace",
        "rename",
    }

    assert not any(
        isinstance(node, ast.Attribute)
        and node.attr in prohibited_attributes
        for node in ast.walk(tree)
    )


def test_only_approved_app_bridge_imports_recommendation_policy():
    references = []

    for path in (ROOT / "src").rglob("*.py"):
        relative = path.relative_to(ROOT / "src")

        if "evaluation" in relative.parts:
            continue

        if (
            "provider_model_recommendation_policy"
            in path.read_text(encoding="utf-8")
        ):
            references.append(relative.as_posix())

    assert references == [
        "app/provider_model_routing_service.py"
    ]

"""Frozen evaluation-only provider/model recommendation policy.

This module translates the reviewed provider qualification registry into a
deterministic recommendation view. It is intentionally read-only and has no
provider, credential, routing, user-settings, application, or ATS authority.

The policy is frozen to the reviewed qualification-registry snapshot and exact
winner bindings. Any registry mutation requires explicit policy review rather
than automatic model replacement.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

from src.evaluation import controlled_provider_qualification_registry as qualification_registry
from src.evaluation.production_task_contract_fingerprints import (
    production_task_contract_sha256,
)


RECOMMENDATION_POLICY_VERSION = "provider-model-recommendation-policy-v1"
RECOMMENDATION_POLICY_SCOPE = "evaluation_readonly_recommendation_only"

SOURCE_QUALIFICATION_REGISTRY_SHA256 = (
    "1d306df3beb42226d00e91f44260cbf9debc7f55132604b8849a4ccd5cc454a1"
)

RECOMMENDATION_STATUSES = (
    "recommended",
    "fail_closed_zero_qualified",
    "blocked_non_live",
)

COST_SELECTION_WEIGHT = 0

_AUTHORITY_INVARIANTS = {
    "production_routing_allowed": False,
    "provider_call_allowed": False,
    "credential_access_allowed": False,
    "user_settings_mutation_allowed": False,
    "application_mutation_allowed": False,
    "ats_mutation_allowed": False,
}

_WORKLOAD_ORDER = (
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

_FROZEN_RECOMMENDATIONS: Mapping[str, Mapping[str, Any]] = {
    "skill_extraction": {
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "selection_basis": "durable_quality_tie_latency_tiebreak",
        "task_contract_sha256": (
            "c7b9f541743b6967924583029036952b639c1f8117d00b68e152c24ac8405bb4"
        ),
        "qualification_binding_sha256": (
            "8c6961f54e3766892ba0d76157d84d6d7fd9a8a169cd55eb6f5659b51783d58d"
        ),
        "evidence_sha256": (
            "09019474b9f0ae6cf383ae0fb638d489eda1303d4b5185aa9f5a6e850b570432"
        ),
        "review_sha256": None,
    },
    "jd_intelligence": {
        "provider": "openai",
        "model": "gpt-5-mini",
        "selection_basis": "sole_qualified_candidate",
        "task_contract_sha256": (
            "846805264eb21a023e0d307869581f0f2702299703e9dbf76847dc73567feee9"
        ),
        "qualification_binding_sha256": (
            "0a2d4b5a509ff31a8b9fd51ee20ca4eeddb9b50c6f03eb2b50cd7d91693760f9"
        ),
        "evidence_sha256": (
            "12332a4d4e29968b499117bfd410cbddfc16dbf345987a39352b2c1619122c45"
        ),
        "review_sha256": (
            "cc4e5212fc1469fa8d468c33ee9adf37dc570b91cdd1a49340d7ace8b3e7893c"
        ),
    },
    "grounded_rag_answer": {
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "selection_basis": "durable_quality_tie_latency_tiebreak",
        "task_contract_sha256": (
            "941f7922b84dc3c150e63d5ad0557283cf657dbc18216ca6d96de2f0b7d8530b"
        ),
        "qualification_binding_sha256": (
            "e0ce8defd25d71f8a188e1c81a2a5a6ee902dcafd33a96d269016c1c4159eb6d"
        ),
        "evidence_sha256": (
            "bfd9bbd3d6e15d0f366e3970d425dc91d7c0f0e948b976f17918b7880491e26f"
        ),
        "review_sha256": None,
    },
    "ambiguous_resume_adjudication": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "selection_basis": "semantic_quality_leader",
        "task_contract_sha256": (
            "b924556c83f9a2650ab9724727385c61b3827cd1c1100b13fa15896302ad0ef3"
        ),
        "qualification_binding_sha256": (
            "7e500a7dde74349e6b78730611692bce5e8cad1252b5412b9781ec8e1e2a383e"
        ),
        "evidence_sha256": (
            "e9da3209291e81ab85ac9691f776951a60dc23262bfaa26011fa89f552b55470"
        ),
        "review_sha256": (
            "6e15835e144bdea42b67babed9a0a467c74893acadaf6b4994203bfbc49db396"
        ),
    },
    "tailoring_refinement": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "selection_basis": "semantic_quality_leader",
        "task_contract_sha256": (
            "ebd8aec3d2c6da08bd9e80e778b30fea8f1444d7a22bfbbba87e70baa547513d"
        ),
        "qualification_binding_sha256": (
            "473233ca7e01920bfcab43b4d57850ab3d25e74ad80720ca4f99a0df85505f8f"
        ),
        "evidence_sha256": (
            "49f286c1ec35611b5f9ddbc7cc841e6a6b3fde205076bc8b2af8ab207672eba3"
        ),
        "review_sha256": (
            "a7698a60f2408c280b820685c825dfe35b55b6feced2008bef0ebbf09823724d"
        ),
    },
    "tailoring_judge": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "selection_basis": "semantic_quality_leader",
        "task_contract_sha256": (
            "85c4ddc83495921c5c15ed07775e94f7b4810d9f9679e1c3520967c36935a133"
        ),
        "qualification_binding_sha256": (
            "d5766f0c0efe1233679403aea231390a11486b6fd227acc4cce87fbfbda1307d"
        ),
        "evidence_sha256": (
            "53ca6c03b89444dd1801cf045f8f3772021634b36d2b6a35df9cbea8debc3823"
        ),
        "review_sha256": (
            "a81ef71f03396711a7310b136fe177af35177ff7266005bfe76b8d39acd3b22c"
        ),
    },
}

_FAIL_CLOSED_WORKLOADS = frozenset(
    {
        "job_fit_evaluation",
        "resume_fallback_ranking",
        "critic_evaluation",
        "tailoring_generation",
        "manual_scan_phrase",
    }
)

_QUALIFICATION_GATED_WORKLOADS = frozenset({"manual_provider_preview"})
_BLOCKED_NON_LIVE_WORKLOADS: frozenset[str] = frozenset()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _cells_for_workload(
    registry_payload: Mapping[str, Any],
    workload_id: str,
) -> list[Mapping[str, Any]]:
    return [
        cell
        for cell in registry_payload["cells"]
        if cell["workload_id"] == workload_id
    ]


def _winner_cell(
    registry_payload: Mapping[str, Any],
    *,
    workload_id: str,
    provider: str,
    model: str,
) -> Mapping[str, Any]:
    matches = [
        cell
        for cell in _cells_for_workload(registry_payload, workload_id)
        if cell["provider"] == provider and cell["model"] == model
    ]
    _require(
        len(matches) == 1,
        f"{workload_id} frozen recommendation identity is missing or ambiguous",
    )
    return matches[0]


def validate_provider_model_recommendation_policy_source(
    registry_payload: Dict[str, Any],
) -> bool:
    """Validate that the registry still exactly supports the frozen policy."""

    payload = deepcopy(registry_payload)

    qualification_registry.validate_provider_qualification_registry(payload)

    registry_sha256 = (
        qualification_registry.provider_qualification_registry_sha256(payload)
    )
    _require(
        registry_sha256 == SOURCE_QUALIFICATION_REGISTRY_SHA256,
        "qualification registry changed; explicit recommendation review required",
    )

    actual_workloads = {
        cell["workload_id"]
        for cell in payload["cells"]
    }
    _require(
        actual_workloads == set(_WORKLOAD_ORDER),
        "qualification workload universe changed",
    )

    for workload_id, expected in _FROZEN_RECOMMENDATIONS.items():
        cell = _winner_cell(
            payload,
            workload_id=workload_id,
            provider=expected["provider"],
            model=expected["model"],
        )

        _require(
            cell["status"] == "qualified",
            f"{workload_id} frozen recommendation is no longer qualified",
        )
        _require(
            cell["status_reasons"]
            == ["qualification_requirements_satisfied"],
            f"{workload_id} qualification reasons changed",
        )
        _require(
            cell["current_task_contract_sha256"]
            == expected["task_contract_sha256"],
            f"{workload_id} current task contract changed",
        )
        _require(
            cell["tested_task_contract_sha256"]
            == expected["task_contract_sha256"],
            f"{workload_id} tested task contract changed",
        )
        _require(
            cell["qualification_binding_sha256"]
            == expected["qualification_binding_sha256"],
            f"{workload_id} qualification binding changed",
        )
        _require(
            cell["evidence_sha256"]
            == expected["evidence_sha256"],
            f"{workload_id} qualification evidence changed",
        )
        _require(
            cell["review_sha256"]
            == expected["review_sha256"],
            f"{workload_id} qualification review changed",
        )

    for workload_id in _FAIL_CLOSED_WORKLOADS:
        cells = _cells_for_workload(payload, workload_id)
        _require(
            bool(cells),
            f"{workload_id} qualification cells are missing",
        )
        _require(
            all(cell["status"] == "rejected" for cell in cells),
            (
                f"{workload_id} frozen fail-closed state changed; "
                "automatic replacement is prohibited"
            ),
        )

    for workload_id in _BLOCKED_NON_LIVE_WORKLOADS:
        cells = _cells_for_workload(payload, workload_id)
        _require(
            len(cells) == 4,
            f"{workload_id} blocked qualification universe changed",
        )
        _require(
            all(cell["status"] == "pending" for cell in cells),
            f"{workload_id} blocked status changed",
        )
        _require(
            all(cell["evidence_sha256"] is None for cell in cells),
            f"{workload_id} unexpectedly contains qualification evidence",
        )
        _require(
            all(
                cell["current_task_contract_sha256"] is None
                for cell in cells
            ),
            f"{workload_id} unexpectedly has a live task contract",
        )

    for workload_id in _QUALIFICATION_GATED_WORKLOADS:
        cells = _cells_for_workload(payload, workload_id)
        _require(
            len(cells) == 4,
            f"{workload_id} qualification universe changed",
        )
        current_digest = production_task_contract_sha256(workload_id)
        _require(
            current_digest is not None,
            f"{workload_id} production task contract is unavailable",
        )
        qualified_cells = [
            cell for cell in cells if cell["status"] == "qualified"
        ]
        for cell in qualified_cells:
            _require(
                cell["status_reasons"]
                == ["qualification_requirements_satisfied"],
                f"{workload_id} qualified status is invalid",
            )
            _require(
                cell["current_task_contract_sha256"] == current_digest
                and cell["tested_task_contract_sha256"] == current_digest,
                f"{workload_id} qualified task-contract binding is stale",
            )
            _require(
                cell["qualification_binding_sha256"] is not None
                and cell["evidence_sha256"] is not None,
                f"{workload_id} qualified evidence is missing",
            )
            _require(
                cell["review_sha256"] is not None,
                f"{workload_id} qualified human review is missing",
            )
        _require(
            len(qualified_cells) <= 1,
            (
                f"{workload_id} has multiple qualified candidates; "
                "explicit recommendation review required"
            ),
        )

    return True


def build_provider_model_recommendation_policy(
    registry_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Return the frozen deterministic recommendation view."""

    payload = deepcopy(registry_payload)
    validate_provider_model_recommendation_policy_source(payload)

    entries = []

    for workload_id in _WORKLOAD_ORDER:
        if workload_id in _FROZEN_RECOMMENDATIONS:
            expected = _FROZEN_RECOMMENDATIONS[workload_id]
            entries.append(
                {
                    "workload_id": workload_id,
                    "recommendation_status": "recommended",
                    "provider": expected["provider"],
                    "model": expected["model"],
                    "selection_basis": expected["selection_basis"],
                    "task_contract_sha256": expected[
                        "task_contract_sha256"
                    ],
                    "qualification_binding_sha256": expected[
                        "qualification_binding_sha256"
                    ],
                    "evidence_sha256": expected["evidence_sha256"],
                    "review_sha256": expected["review_sha256"],
                }
            )
        elif workload_id in _FAIL_CLOSED_WORKLOADS:
            entries.append(
                {
                    "workload_id": workload_id,
                    "recommendation_status": (
                        "fail_closed_zero_qualified"
                    ),
                    "provider": None,
                    "model": None,
                    "selection_basis": (
                        "fail_closed_zero_qualified"
                    ),
                    "task_contract_sha256": None,
                    "qualification_binding_sha256": None,
                    "evidence_sha256": None,
                    "review_sha256": None,
                }
            )
        elif workload_id in _BLOCKED_NON_LIVE_WORKLOADS:
            entries.append(
                {
                    "workload_id": workload_id,
                    "recommendation_status": "blocked_non_live",
                    "provider": None,
                    "model": None,
                    "selection_basis": "blocked_non_live",
                    "task_contract_sha256": None,
                    "qualification_binding_sha256": None,
                    "evidence_sha256": None,
                    "review_sha256": None,
                }
            )
        elif workload_id in _QUALIFICATION_GATED_WORKLOADS:
            qualified_cells = [
                cell
                for cell in _cells_for_workload(payload, workload_id)
                if cell["status"] == "qualified"
            ]
            if qualified_cells:
                cell = qualified_cells[0]
                entries.append(
                    {
                        "workload_id": workload_id,
                        "recommendation_status": "recommended",
                        "provider": cell["provider"],
                        "model": cell["model"],
                        "selection_basis": "sole_qualified_candidate",
                        "task_contract_sha256": cell[
                            "current_task_contract_sha256"
                        ],
                        "qualification_binding_sha256": cell[
                            "qualification_binding_sha256"
                        ],
                        "evidence_sha256": cell["evidence_sha256"],
                        "review_sha256": cell["review_sha256"],
                    }
                )
            else:
                entries.append(
                    {
                        "workload_id": workload_id,
                        "recommendation_status": "blocked_non_live",
                        "provider": None,
                        "model": None,
                        "selection_basis": "blocked_non_live",
                        "task_contract_sha256": (
                            production_task_contract_sha256(workload_id)
                        ),
                        "qualification_binding_sha256": None,
                        "evidence_sha256": None,
                        "review_sha256": None,
                    }
                )
        else:
            raise ValueError(
                f"{workload_id} has no frozen recommendation policy"
            )

    result = {
        "policy_version": RECOMMENDATION_POLICY_VERSION,
        "policy_scope": RECOMMENDATION_POLICY_SCOPE,
        "source_registry_sha256": (
            SOURCE_QUALIFICATION_REGISTRY_SHA256
        ),
        "recommendation_statuses": list(RECOMMENDATION_STATUSES),
        "cost_selection_weight": COST_SELECTION_WEIGHT,
        "workloads": entries,
        "authority_invariants": deepcopy(_AUTHORITY_INVARIANTS),
    }

    return deepcopy(result)


def read_provider_model_recommendation(
    registry_payload: Dict[str, Any],
    workload_id: str,
) -> Dict[str, Any]:
    """Read one workload recommendation without granting routing authority."""

    _require(
        isinstance(workload_id, str) and bool(workload_id.strip()),
        "workload_id must be a non-empty string",
    )

    policy = build_provider_model_recommendation_policy(registry_payload)

    matches = [
        entry
        for entry in policy["workloads"]
        if entry["workload_id"] == workload_id
    ]

    _require(
        len(matches) == 1,
        "workload_id is not part of the frozen recommendation policy",
    )

    return deepcopy(matches[0])

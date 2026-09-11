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
    "6d7c1e2cae7d03edadcfb4c7268ec6ec74e8c0e10b13e73cc3914baa03ea8f6f"
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
    "tailoring_generation": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "selection_basis": "sole_qualified_candidate",
        "task_contract_sha256": (
            "69636a86bf36af7f6c8757d615ec76a9e9d4cfea72661d1ca4c515a8a124c0ac"
        ),
        "qualification_binding_sha256": (
            "9e03738f97fea61d589fe2810f180dc504fc2a88d4dfdc81bd4cee6e1d0b1ad3"
        ),
        "evidence_sha256": (
            "9f5b504ec4b36b041b7a134e1871c54cd6bd8f4af13ca61e92377fb2520acd52"
        ),
        "review_sha256": (
            "e0e84260678e406fcccf48690ddc226cda643c61627ef682cd80003c58279a00"
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


RENDERER_BOUND_RECOMMENDATION_POLICY_VERSION = (
    "provider-model-recommendation-policy-renderer-bound-v1"
)
RENDERER_BOUND_RECOMMENDATION_PIN_VERSION = (
    "provider-model-renderer-bound-recommendation-pin-v1"
)
_RENDERER_BOUND_PIN_FIELDS = {
    "pin_version",
    "workload_id",
    "provider",
    "model",
    "selection_basis",
    "expected_status",
    "expected_status_reasons",
    "expected_qualification_semantics_generation",
    "expected_current_workload_qualification_semantics_sha256",
    "expected_tested_workload_qualification_semantics_sha256",
    "expected_current_task_contract_sha256",
    "expected_tested_task_contract_sha256",
    "expected_qualification_binding_sha256",
    "expected_evidence_sha256",
    "expected_review_sha256",
    "expected_candidate_universe",
}
_RENDERER_BOUND_CANDIDATE_FIELDS = {"provider", "model", "status"}

# Explicit operator-reviewed next-generation recommendation only.  The V1
# frozen policy and app routing bridge do not consume this pin; a caller must
# still supply it to the existing renderer-bound policy builder.
_FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_PIN = {
    "pin_version": RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
    "workload_id": "skill_extraction",
    "provider": "groq",
    "model": "openai/gpt-oss-20b",
    "selection_basis": (
        "operator_quality_tie_lower_cost_output_and_aggregate_latency"
    ),
    "expected_status": "qualified",
    "expected_status_reasons": ["qualification_requirements_satisfied"],
    "expected_qualification_semantics_generation": "renderer_bound_v1",
    "expected_current_workload_qualification_semantics_sha256": (
        "3e1c457b9636d5ec648b6e24a823df006bad790641b1f831d3bebb34b2ddc362"
    ),
    "expected_tested_workload_qualification_semantics_sha256": (
        "3e1c457b9636d5ec648b6e24a823df006bad790641b1f831d3bebb34b2ddc362"
    ),
    "expected_current_task_contract_sha256": (
        "73784a99de4913b95e2d2a1e8a1b10a9eee1665fd83a179be34a4fe31b82fa4c"
    ),
    "expected_tested_task_contract_sha256": (
        "73784a99de4913b95e2d2a1e8a1b10a9eee1665fd83a179be34a4fe31b82fa4c"
    ),
    "expected_qualification_binding_sha256": (
        "dfe7c0c77150f9a7bfb25f00a5b37ae67f121948f4a63140e9de67e2f515c1df"
    ),
    "expected_evidence_sha256": (
        "ca727553032f24749b3ea161188b6c2cd4f7ab4c877b8e7dc7d896a0f186e5ac"
    ),
    "expected_review_sha256": None,
    "expected_candidate_universe": [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "status": "qualified",
        },
        {
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
            "status": "qualified",
        },
        {
            "provider": "openai",
            "model": "gpt-5-mini",
            "status": "stale",
        },
    ],
}

FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_REGISTRY_SHA256 = (
    "f25765138187aeae4eddc4f955441a738446493fe58ecc537f1cd9584d7c4cce"
)
_FINALIZED_SKILL_EXTRACTION_CONTROLLED_PLAN_SHA256 = (
    "f074eaa9f4db1e4d58b0f1530503217c76142477548c07a15fc1f2d9fc4e7fae"
)
_FINALIZED_SKILL_EXTRACTION_QUALIFIED_CANDIDATE_BINDINGS = {
    ("groq", "openai/gpt-oss-20b"): (
        "ca727553032f24749b3ea161188b6c2cd4f7ab4c877b8e7dc7d896a0f186e5ac",
        "dfe7c0c77150f9a7bfb25f00a5b37ae67f121948f4a63140e9de67e2f515c1df",
    ),
    ("groq", "openai/gpt-oss-120b"): (
        "79e89f604a16f38ea6803bf2669c004b4631ebaf5fd9ef005b3fe57e9f59c6ec",
        "1b4d7b73c3063fbd5e65b1293223202dfb0c4c01ec6fe28eb141f2eeb83e57a4",
    ),
}

_FINALIZED_JOB_FIT_RENDERER_BOUND_PIN = {
    "pin_version": RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
    "workload_id": "job_fit_evaluation",
    "provider": "groq",
    "model": "openai/gpt-oss-20b",
    "selection_basis": "sole_qualified_candidate",
    "expected_status": "qualified",
    "expected_status_reasons": ["qualification_requirements_satisfied"],
    "expected_qualification_semantics_generation": "renderer_bound_v1",
    "expected_current_workload_qualification_semantics_sha256": (
        "60e7fa48863d893aae0d29d29f01369324219253dcbcde3a1e9d5ba0925c553d"
    ),
    "expected_tested_workload_qualification_semantics_sha256": (
        "60e7fa48863d893aae0d29d29f01369324219253dcbcde3a1e9d5ba0925c553d"
    ),
    "expected_current_task_contract_sha256": (
        "e9568a48240886579814a557b414461510f86485e3bb7a50efc3e7ab8e319480"
    ),
    "expected_tested_task_contract_sha256": (
        "e9568a48240886579814a557b414461510f86485e3bb7a50efc3e7ab8e319480"
    ),
    "expected_qualification_binding_sha256": (
        "af4214dfd0504e73a24d5f5a96a124f7d4c623e3a085f3d027c0dd6132912efc"
    ),
    "expected_evidence_sha256": (
        "e63db9ce3b95d5bda934b97f7d0ad49dae2b78c33a0aa2f19b1e61d03afd22b3"
    ),
    "expected_review_sha256": None,
    "expected_candidate_universe": [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "status": "qualified",
        },
        {
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
            "status": "rejected",
        },
        {
            "provider": "openai",
            "model": "gpt-5-mini",
            "status": "rejected",
        },
        {
            "provider": "openai",
            "model": "gpt-5.1",
            "status": "rejected",
        },
    ],
}

FINALIZED_JOB_FIT_RENDERER_BOUND_REGISTRY_SHA256 = (
    "2c75dd95de90553ce05dd2a20d9b9f478c9e65441305997adefd7c9f00787519"
)
FINALIZED_JOB_FIT_CANDIDATE_TRANSPORT_SEMANTICS_SHA256 = (
    "5d7dc8f71de2799d8d2f448e91fd38ac21af87f628cf52f9bac825a1d1155334"
)


def validate_renderer_bound_recommendation_pin(pin: Mapping[str, Any]) -> bool:
    """Validate the shape of one explicit next-generation recommendation pin.

    A pin is always supplied by the caller after fresh renderer-bound
    qualification. It is never derived from ``_FROZEN_RECOMMENDATIONS`` or from
    ``SOURCE_QUALIFICATION_REGISTRY_SHA256``.
    """

    _require(
        isinstance(pin, Mapping) and set(pin) == _RENDERER_BOUND_PIN_FIELDS,
        "renderer-bound recommendation pin fields must match the exact schema",
    )
    _require(
        pin["pin_version"] == RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
        "renderer-bound recommendation pin version mismatch",
    )
    _require(
        pin["workload_id"] in _WORKLOAD_ORDER,
        "renderer-bound recommendation pin workload is unknown",
    )
    for field in ("provider", "model", "selection_basis"):
        _require(
            isinstance(pin[field], str) and bool(pin[field].strip()),
            f"renderer-bound recommendation pin {field} is invalid",
        )
    _require(
        pin["expected_status"] == "qualified",
        "renderer-bound recommendation pin must expect a qualified winner",
    )
    _require(
        pin["expected_qualification_semantics_generation"]
        == qualification_registry
        .RENDERER_BOUND_QUALIFICATION_SEMANTICS_GENERATION,
        "renderer-bound recommendation pin generation must be renderer bound",
    )
    _require(
        isinstance(pin["expected_status_reasons"], list),
        "renderer-bound recommendation pin reasons are invalid",
    )
    universe = pin["expected_candidate_universe"]
    _require(
        isinstance(universe, list) and bool(universe),
        "renderer-bound recommendation pin candidate universe is invalid",
    )
    seen = set()
    for candidate in universe:
        _require(
            isinstance(candidate, Mapping)
            and set(candidate) == _RENDERER_BOUND_CANDIDATE_FIELDS,
            "renderer-bound candidate universe entry is invalid",
        )
        identity = (candidate["provider"], candidate["model"])
        _require(
            identity not in seen,
            "renderer-bound candidate universe contains a duplicate identity",
        )
        seen.add(identity)
        _require(
            candidate["status"]
            in qualification_registry.QUALIFICATION_STATUSES,
            "renderer-bound candidate universe status is invalid",
        )
    _require(
        (pin["provider"], pin["model"]) in seen,
        "renderer-bound recommendation pin winner is outside its universe",
    )
    return True


def build_finalized_skill_extraction_renderer_bound_pin() -> Dict[str, Any]:
    """Return the reviewed Skill winner pin without activating V2 routing."""

    pin = deepcopy(_FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_PIN)
    validate_renderer_bound_recommendation_pin(pin)
    return pin


def build_finalized_job_fit_renderer_bound_pin() -> Dict[str, Any]:
    """Return the sole-current-candidate Job Fit renderer-bound pin."""

    pin = deepcopy(_FINALIZED_JOB_FIT_RENDERER_BOUND_PIN)
    validate_renderer_bound_recommendation_pin(pin)
    return pin


def validate_finalized_job_fit_renderer_bound_authority(
    renderer_bound_registry: Dict[str, Any],
) -> bool:
    """Validate the exact durable Job Fit authority selected for routing."""

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_qualification_registry(
        payload
    )
    _require(
        qualification_registry.renderer_bound_qualification_registry_sha256(
            payload
        )
        == FINALIZED_JOB_FIT_RENDERER_BOUND_REGISTRY_SHA256,
        "finalized Job Fit renderer-bound registry digest changed",
    )
    pin = build_finalized_job_fit_renderer_bound_pin()
    _require(
        production_task_contract_sha256(pin["workload_id"])
        == pin["expected_current_task_contract_sha256"],
        "finalized Job Fit production task contract changed",
    )
    validate_renderer_bound_workload_recommendation(payload, pin=pin)
    cells = _renderer_bound_workload_cells(payload, pin["workload_id"])
    qualified = [cell for cell in cells if cell["status"] == "qualified"]
    _require(
        len(cells) == 4
        and len(qualified) == 1
        and (qualified[0]["provider"], qualified[0]["model"])
        == (pin["provider"], pin["model"]),
        "finalized Job Fit candidate authority changed",
    )
    from src.evaluation.job_fit_candidate_local_qualification import (
        job_fit_candidate_transport_semantics_sha256,
    )

    _require(
        job_fit_candidate_transport_semantics_sha256(
            pin["provider"], pin["model"]
        )
        == FINALIZED_JOB_FIT_CANDIDATE_TRANSPORT_SEMANTICS_SHA256,
        "finalized Job Fit candidate transport semantics changed",
    )
    return True


def validate_finalized_skill_extraction_renderer_bound_authority(
    renderer_bound_registry: Dict[str, Any],
) -> bool:
    """Validate the exact durable Skill authority selected for app routing."""

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_qualification_registry(
        payload
    )
    _require(
        qualification_registry.renderer_bound_qualification_registry_sha256(
            payload
        )
        == FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_REGISTRY_SHA256,
        "finalized Skill renderer-bound registry digest changed",
    )
    pin = build_finalized_skill_extraction_renderer_bound_pin()
    _require(
        production_task_contract_sha256(pin["workload_id"])
        == pin["expected_current_task_contract_sha256"],
        "finalized Skill production task contract changed",
    )
    validate_renderer_bound_workload_recommendation(payload, pin=pin)
    cells = _renderer_bound_workload_cells(payload, pin["workload_id"])
    by_identity = {
        (cell["provider"], cell["model"]): cell
        for cell in cells
    }
    for identity, (evidence_sha256, binding_sha256) in (
        _FINALIZED_SKILL_EXTRACTION_QUALIFIED_CANDIDATE_BINDINGS.items()
    ):
        cell = by_identity.get(identity)
        _require(
            cell is not None
            and cell["status"] == "qualified"
            and cell["current_controlled_plan_sha256"]
            == _FINALIZED_SKILL_EXTRACTION_CONTROLLED_PLAN_SHA256
            and cell["tested_controlled_plan_sha256"]
            == _FINALIZED_SKILL_EXTRACTION_CONTROLLED_PLAN_SHA256
            and cell["evidence_sha256"] == evidence_sha256
            and cell["qualification_binding_sha256"] == binding_sha256,
            "finalized Skill qualified candidate authority changed",
        )
    return True


def _renderer_bound_workload_cells(
    renderer_bound_registry: Mapping[str, Any],
    workload_id: str,
) -> list[Mapping[str, Any]]:
    return [
        cell
        for cell in renderer_bound_registry["cells"]
        if cell["workload_id"] == workload_id
    ]


def validate_renderer_bound_workload_recommendation(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Mapping[str, Any],
) -> bool:
    """Validate one workload's next-generation recommendation authority.

    Scoped to a single workload: unrelated workloads are never inspected, so a
    change elsewhere in the registry cannot affect this result. The
    whole-registry digest is deliberately not consulted.
    """

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_qualification_registry(
        payload
    )
    validate_renderer_bound_recommendation_pin(pin)

    workload_id = pin["workload_id"]
    cells = _renderer_bound_workload_cells(payload, workload_id)
    _require(bool(cells), f"{workload_id} renderer-bound cells are missing")

    observed_universe = sorted(
        (
            {
                "provider": cell["provider"],
                "model": cell["model"],
                "status": cell["status"],
            }
            for cell in cells
        ),
        key=lambda entry: (entry["provider"], entry["model"]),
    )
    expected_universe = sorted(
        (dict(entry) for entry in pin["expected_candidate_universe"]),
        key=lambda entry: (entry["provider"], entry["model"]),
    )
    _require(
        observed_universe == expected_universe,
        f"{workload_id} renderer-bound candidate universe changed",
    )

    matches = [
        cell
        for cell in cells
        if cell["provider"] == pin["provider"]
        and cell["model"] == pin["model"]
    ]
    _require(
        len(matches) == 1,
        f"{workload_id} renderer-bound winner identity is missing or ambiguous",
    )
    winner = matches[0]

    _require(
        winner["qualification_semantics_generation"]
        == qualification_registry
        .RENDERER_BOUND_QUALIFICATION_SEMANTICS_GENERATION,
        f"{workload_id} winner is not renderer bound",
    )
    _require(
        winner["status"] == pin["expected_status"],
        f"{workload_id} winner status changed",
    )
    _require(
        winner["status_reasons"] == pin["expected_status_reasons"],
        f"{workload_id} winner status reasons changed",
    )
    tested_semantics = winner["tested_workload_qualification_semantics_sha256"]
    current_semantics = winner[
        "current_workload_qualification_semantics_sha256"
    ]
    _require(
        tested_semantics is not None
        and tested_semantics == current_semantics,
        f"{workload_id} winner workload semantics binding is stale",
    )
    for cell_field, pin_field in (
        (
            "current_workload_qualification_semantics_sha256",
            "expected_current_workload_qualification_semantics_sha256",
        ),
        (
            "tested_workload_qualification_semantics_sha256",
            "expected_tested_workload_qualification_semantics_sha256",
        ),
        ("current_task_contract_sha256", "expected_current_task_contract_sha256"),
        ("tested_task_contract_sha256", "expected_tested_task_contract_sha256"),
        ("qualification_binding_sha256", "expected_qualification_binding_sha256"),
        ("evidence_sha256", "expected_evidence_sha256"),
        ("review_sha256", "expected_review_sha256"),
    ):
        _require(
            winner[cell_field] == pin[pin_field],
            f"{workload_id} winner {cell_field} changed",
        )
    _require(
        winner["qualification_binding_sha256"]
        == qualification_registry.renderer_bound_qualification_binding_sha256(
            winner
        ),
        f"{workload_id} winner qualification binding is inconsistent",
    )
    return True


def build_renderer_bound_workload_recommendation(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return one next-generation recommendation entry after validation."""

    validate_renderer_bound_workload_recommendation(
        renderer_bound_registry,
        pin=pin,
    )
    return deepcopy(
        {
            "workload_id": pin["workload_id"],
            "recommendation_status": "recommended",
            "provider": pin["provider"],
            "model": pin["model"],
            "selection_basis": pin["selection_basis"],
            "qualification_semantics_generation": (
                pin["expected_qualification_semantics_generation"]
            ),
            "task_contract_sha256": pin["expected_current_task_contract_sha256"],
            "workload_qualification_semantics_sha256": (
                pin["expected_current_workload_qualification_semantics_sha256"]
            ),
            "qualification_binding_sha256": (
                pin["expected_qualification_binding_sha256"]
            ),
            "evidence_sha256": pin["expected_evidence_sha256"],
            "review_sha256": pin["expected_review_sha256"],
        }
    )


def build_renderer_bound_unpinned_workload_recommendation(
    renderer_bound_registry: Dict[str, Any],
    *,
    workload_id: str,
) -> Dict[str, Any]:
    """Return the conservative entry for a workload with no explicit pin.

    A workload never inherits its V1 winner. Without renderer-bound positive
    authority it reports the existing conservative vocabulary and no
    provider/model is invented.
    """

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_qualification_registry(
        payload
    )
    _require(
        workload_id in _WORKLOAD_ORDER,
        "renderer-bound recommendation workload is unknown",
    )
    cells = _renderer_bound_workload_cells(payload, workload_id)
    _require(bool(cells), f"{workload_id} renderer-bound cells are missing")
    qualified = [cell for cell in cells if cell["status"] == "qualified"]
    _require(
        not qualified,
        f"{workload_id} has renderer-bound qualified cells and requires a pin",
    )
    return {
        "workload_id": workload_id,
        "recommendation_status": "fail_closed_zero_qualified",
        "provider": None,
        "model": None,
        "selection_basis": "fail_closed_zero_qualified",
        "qualification_semantics_generation": None,
        "task_contract_sha256": None,
        "workload_qualification_semantics_sha256": None,
        "qualification_binding_sha256": None,
        "evidence_sha256": None,
        "review_sha256": None,
    }


def build_prospective_renderer_bound_recommendation_policy(
    renderer_bound_registry: Dict[str, Any],
    *,
    pins_by_workload: Mapping[str, Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Return a prospective next-generation view from explicit pins only.

    Workloads absent from ``pins_by_workload`` are never promoted from their V1
    winners; they fall through to the conservative unpinned entry.
    """

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_qualification_registry(
        payload
    )
    supplied = {} if pins_by_workload is None else dict(pins_by_workload)
    known = {cell["workload_id"] for cell in payload["cells"]}
    _require(
        set(supplied).issubset(known),
        "renderer-bound pin references an unknown workload",
    )
    for workload_id, pin in supplied.items():
        _require(
            pin.get("workload_id") == workload_id,
            "renderer-bound pin workload key mismatch",
        )

    entries = []
    for workload_id in _WORKLOAD_ORDER:
        if workload_id not in known:
            continue
        if workload_id in supplied:
            entries.append(
                build_renderer_bound_workload_recommendation(
                    payload,
                    pin=supplied[workload_id],
                )
            )
        else:
            entries.append(
                build_renderer_bound_unpinned_workload_recommendation(
                    payload,
                    workload_id=workload_id,
                )
            )
    return {
        "policy_version": RENDERER_BOUND_RECOMMENDATION_POLICY_VERSION,
        "policy_scope": RECOMMENDATION_POLICY_SCOPE,
        "recommendation_statuses": list(RECOMMENDATION_STATUSES),
        "workloads": entries,
        "authority_invariants": deepcopy(_AUTHORITY_INVARIANTS),
    }


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


# ---------------------------------------------------------------------------
# Renderer-bound V2 recommendation authority.
#
# The V1 pins and validators above keep their historical meaning.  V2 exists
# because the V1 winner binding mixes whole-Step8L provenance and
# corpus-derived raw coverage into workload authority, so an unrelated
# workload's fixture change invalidates a workload that did not change.  The
# V2 pin additionally binds workload-stable case coverage, so production can
# verify exact coverage without a plan.
# ---------------------------------------------------------------------------

RENDERER_BOUND_V2_RECOMMENDATION_POLICY_VERSION = (
    "provider-model-recommendation-policy-renderer-bound-v2"
)
RENDERER_BOUND_V2_RECOMMENDATION_PIN_VERSION = (
    "provider-model-renderer-bound-recommendation-pin-v2"
)
_RENDERER_BOUND_V2_PIN_FIELDS = _RENDERER_BOUND_PIN_FIELDS | {
    "expected_qualification_stable_case_aliases"
}

# Stable coverage proven from the reviewed qualification event's own historical
# corpus (skill: bcf1286e/c3d419c5, job fit: 1d2f148f). Never re-derived from
# the current corpus, whose raw aliases no longer resolve to these cases.
_FINALIZED_SKILL_EXTRACTION_STABLE_CASE_ALIASES = [
    "case_adb75e8f4222598d01c96632",
    "case_ca4d896b8d25c5f6a33131e6",
    "case_c679d81feddcd209e0923b23",
    "case_155361f163b8a1857f1ea709",
    "case_2e2c04e49f9cdaa7ab5b6422",
]
_FINALIZED_JOB_FIT_STABLE_CASE_ALIASES = ["case_d2afa978996c4d69af1f538b"]

_FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_V2_PIN = {
    **{
        key: deepcopy(value)
        for key, value in _FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_PIN.items()
    },
    "pin_version": RENDERER_BOUND_V2_RECOMMENDATION_PIN_VERSION,
    "expected_qualification_semantics_generation": "renderer_bound_v2",
    "expected_qualification_binding_sha256": (
        "12b2e716ba4c9dffafb4da68344a4b603f8d36eabb9fbd1ed6fdda12f0b2a2e2"
    ),
    "expected_qualification_stable_case_aliases": (
        _FINALIZED_SKILL_EXTRACTION_STABLE_CASE_ALIASES
    ),
}
_FINALIZED_JOB_FIT_RENDERER_BOUND_V2_PIN = {
    **{
        key: deepcopy(value)
        for key, value in _FINALIZED_JOB_FIT_RENDERER_BOUND_PIN.items()
    },
    "pin_version": RENDERER_BOUND_V2_RECOMMENDATION_PIN_VERSION,
    "expected_qualification_semantics_generation": "renderer_bound_v2",
    "expected_qualification_binding_sha256": (
        "2cf4e2005fdb077af7080ccd8a33000ef3e7f8fb8f4d9595fba7a6a699c93f76"
    ),
    "expected_qualification_stable_case_aliases": (
        _FINALIZED_JOB_FIT_STABLE_CASE_ALIASES
    ),
}
FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_V2_REGISTRY_SHA256 = (
    "d1c3c4ce2cc07ac223aac8c009771df37d4f3e31b3dfc9fbcd7d7364144fc500"
)
FINALIZED_JOB_FIT_RENDERER_BOUND_V2_REGISTRY_SHA256 = (
    "d0a8998f7cbf353fc839ee64f9cedf046ea75faa7ec30cb86a72bca164b6a93b"
)
_FINALIZED_SKILL_EXTRACTION_V2_QUALIFIED_CANDIDATE_BINDINGS = {
    ("groq", "openai/gpt-oss-20b"): (
        "ca727553032f24749b3ea161188b6c2cd4f7ab4c877b8e7dc7d896a0f186e5ac",
        "12b2e716ba4c9dffafb4da68344a4b603f8d36eabb9fbd1ed6fdda12f0b2a2e2",
    ),
    ("groq", "openai/gpt-oss-120b"): (
        "79e89f604a16f38ea6803bf2669c004b4631ebaf5fd9ef005b3fe57e9f59c6ec",
        "85b33f3b9289f3aeadacd847a754306aa13fb70154a2dc5e856498bfbbf1564e",
    ),
}


def _validate_stable_case_alias_list(aliases: Any, label: str) -> None:
    _require(
        isinstance(aliases, list) and bool(aliases),
        f"{label} stable case coverage is missing",
    )
    _require(
        all(
            qualification_registry._is_stable_case_alias(alias)
            for alias in aliases
        ),
        f"{label} stable case alias is malformed",
    )
    _require(
        len(aliases) == len(set(aliases)),
        f"{label} stable case coverage contains duplicates",
    )


def validate_renderer_bound_v2_recommendation_pin(
    pin: Mapping[str, Any],
) -> bool:
    """Validate the shape of one explicit renderer-bound V2 recommendation pin."""

    _require(
        isinstance(pin, Mapping) and set(pin) == _RENDERER_BOUND_V2_PIN_FIELDS,
        "renderer-bound V2 recommendation pin fields must match the exact schema",
    )
    _require(
        pin["pin_version"] == RENDERER_BOUND_V2_RECOMMENDATION_PIN_VERSION,
        "renderer-bound V2 recommendation pin version mismatch",
    )
    _require(
        pin["expected_qualification_semantics_generation"]
        == qualification_registry
        .RENDERER_BOUND_V2_QUALIFICATION_SEMANTICS_GENERATION,
        "renderer-bound V2 recommendation pin generation must be renderer bound v2",
    )
    _validate_stable_case_alias_list(
        pin["expected_qualification_stable_case_aliases"],
        "renderer-bound V2 recommendation pin",
    )
    # Every remaining shape rule is identical to V1, so reuse it rather than
    # restating it; only the version and generation tokens differ.
    v1_shaped = {
        key: deepcopy(value)
        for key, value in pin.items()
        if key != "expected_qualification_stable_case_aliases"
    }
    v1_shaped["pin_version"] = RENDERER_BOUND_RECOMMENDATION_PIN_VERSION
    v1_shaped["expected_qualification_semantics_generation"] = (
        qualification_registry.RENDERER_BOUND_QUALIFICATION_SEMANTICS_GENERATION
    )
    validate_renderer_bound_recommendation_pin(v1_shaped)
    return True


def build_finalized_skill_extraction_renderer_bound_v2_pin() -> Dict[str, Any]:
    """Return the reviewed Skill winner pin under V2 binding semantics."""

    pin = deepcopy(_FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_V2_PIN)
    validate_renderer_bound_v2_recommendation_pin(pin)
    return pin


def build_finalized_job_fit_renderer_bound_v2_pin() -> Dict[str, Any]:
    """Return the sole-current-candidate Job Fit pin under V2 semantics."""

    pin = deepcopy(_FINALIZED_JOB_FIT_RENDERER_BOUND_V2_PIN)
    validate_renderer_bound_v2_recommendation_pin(pin)
    return pin


def validate_renderer_bound_v2_workload_recommendation(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Mapping[str, Any],
) -> bool:
    """Validate one workload's V2 recommendation authority, failing closed.

    Scoped to a single workload: unrelated workloads are never inspected, so a
    change elsewhere in the registry cannot affect this result.
    """

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_v2_qualification_registry(
        payload
    )
    validate_renderer_bound_v2_recommendation_pin(pin)

    workload_id = pin["workload_id"]
    cells = _renderer_bound_workload_cells(payload, workload_id)
    _require(bool(cells), f"{workload_id} renderer-bound V2 cells are missing")

    observed_universe = sorted(
        (
            {
                "provider": cell["provider"],
                "model": cell["model"],
                "status": cell["status"],
            }
            for cell in cells
        ),
        key=lambda entry: (entry["provider"], entry["model"]),
    )
    expected_universe = sorted(
        (dict(entry) for entry in pin["expected_candidate_universe"]),
        key=lambda entry: (entry["provider"], entry["model"]),
    )
    _require(
        observed_universe == expected_universe,
        f"{workload_id} renderer-bound V2 candidate universe changed",
    )

    matches = [
        cell
        for cell in cells
        if cell["provider"] == pin["provider"]
        and cell["model"] == pin["model"]
    ]
    _require(
        len(matches) == 1,
        f"{workload_id} renderer-bound V2 winner identity is missing or ambiguous",
    )
    winner = matches[0]

    _require(
        winner["qualification_semantics_generation"]
        == qualification_registry
        .RENDERER_BOUND_V2_QUALIFICATION_SEMANTICS_GENERATION,
        f"{workload_id} V2 winner is not renderer bound v2",
    )
    _require(
        winner["status"] == pin["expected_status"],
        f"{workload_id} V2 winner status changed",
    )
    _require(
        winner["status_reasons"] == pin["expected_status_reasons"],
        f"{workload_id} V2 winner status reasons changed",
    )
    tested_semantics = winner["tested_workload_qualification_semantics_sha256"]
    current_semantics = winner[
        "current_workload_qualification_semantics_sha256"
    ]
    _require(
        tested_semantics is not None
        and tested_semantics == current_semantics,
        f"{workload_id} V2 winner workload semantics binding is stale",
    )
    _require(
        winner["qualification_stable_case_aliases"]
        == pin["expected_qualification_stable_case_aliases"],
        f"{workload_id} V2 winner stable case coverage changed",
    )
    for cell_field, pin_field in (
        (
            "current_workload_qualification_semantics_sha256",
            "expected_current_workload_qualification_semantics_sha256",
        ),
        (
            "tested_workload_qualification_semantics_sha256",
            "expected_tested_workload_qualification_semantics_sha256",
        ),
        ("current_task_contract_sha256", "expected_current_task_contract_sha256"),
        ("tested_task_contract_sha256", "expected_tested_task_contract_sha256"),
        ("qualification_binding_sha256", "expected_qualification_binding_sha256"),
        ("evidence_sha256", "expected_evidence_sha256"),
        ("review_sha256", "expected_review_sha256"),
    ):
        _require(
            winner[cell_field] == pin[pin_field],
            f"{workload_id} V2 winner {cell_field} changed",
        )
    _require(
        winner["qualification_binding_sha256"]
        == qualification_registry
        .renderer_bound_v2_qualification_binding_sha256(winner),
        f"{workload_id} V2 winner qualification binding is inconsistent",
    )
    return True


def validate_finalized_job_fit_renderer_bound_v2_authority(
    renderer_bound_registry: Dict[str, Any],
) -> bool:
    """Validate the exact durable Job Fit V2 authority selected for routing."""

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_v2_qualification_registry(
        payload
    )
    _require(
        qualification_registry
        .renderer_bound_v2_qualification_registry_sha256(payload)
        == FINALIZED_JOB_FIT_RENDERER_BOUND_V2_REGISTRY_SHA256,
        "finalized Job Fit renderer-bound V2 registry digest changed",
    )
    pin = build_finalized_job_fit_renderer_bound_v2_pin()
    _require(
        production_task_contract_sha256(pin["workload_id"])
        == pin["expected_current_task_contract_sha256"],
        "finalized Job Fit production task contract changed",
    )
    validate_renderer_bound_v2_workload_recommendation(payload, pin=pin)
    cells = _renderer_bound_workload_cells(payload, pin["workload_id"])
    qualified = [cell for cell in cells if cell["status"] == "qualified"]
    _require(
        len(cells) == 4
        and len(qualified) == 1
        and (qualified[0]["provider"], qualified[0]["model"])
        == (pin["provider"], pin["model"]),
        "finalized Job Fit V2 candidate authority changed",
    )
    # The legacy rejected candidates must stay legacy: a schema migration never
    # promotes them into renderer-bound V2 qualification authority.
    for cell in cells:
        if (cell["provider"], cell["model"]) == (pin["provider"], pin["model"]):
            continue
        _require(
            cell["qualification_semantics_generation"]
            == qualification_registry
            .LEGACY_QUALIFICATION_SEMANTICS_GENERATION
            and cell["status"] == "rejected"
            and not cell["qualification_stable_case_aliases"],
            "finalized Job Fit legacy candidate semantics changed",
        )
    from src.evaluation.job_fit_candidate_local_qualification import (
        job_fit_candidate_transport_semantics_sha256,
    )

    _require(
        job_fit_candidate_transport_semantics_sha256(
            pin["provider"], pin["model"]
        )
        == FINALIZED_JOB_FIT_CANDIDATE_TRANSPORT_SEMANTICS_SHA256,
        "finalized Job Fit candidate transport semantics changed",
    )
    return True


def validate_finalized_skill_extraction_renderer_bound_v2_authority(
    renderer_bound_registry: Dict[str, Any],
) -> bool:
    """Validate the exact durable Skill V2 authority selected for app routing."""

    payload = deepcopy(renderer_bound_registry)
    qualification_registry.validate_renderer_bound_v2_qualification_registry(
        payload
    )
    _require(
        qualification_registry
        .renderer_bound_v2_qualification_registry_sha256(payload)
        == FINALIZED_SKILL_EXTRACTION_RENDERER_BOUND_V2_REGISTRY_SHA256,
        "finalized Skill renderer-bound V2 registry digest changed",
    )
    pin = build_finalized_skill_extraction_renderer_bound_v2_pin()
    _require(
        production_task_contract_sha256(pin["workload_id"])
        == pin["expected_current_task_contract_sha256"],
        "finalized Skill production task contract changed",
    )
    validate_renderer_bound_v2_workload_recommendation(payload, pin=pin)
    cells = _renderer_bound_workload_cells(payload, pin["workload_id"])
    by_identity = {(cell["provider"], cell["model"]): cell for cell in cells}
    for identity, (evidence_sha256, binding_sha256) in (
        _FINALIZED_SKILL_EXTRACTION_V2_QUALIFIED_CANDIDATE_BINDINGS.items()
    ):
        cell = by_identity.get(identity)
        _require(
            cell is not None
            and cell["status"] == "qualified"
            and cell["qualification_semantics_generation"]
            == qualification_registry
            .RENDERER_BOUND_V2_QUALIFICATION_SEMANTICS_GENERATION
            and cell["evidence_sha256"] == evidence_sha256
            and cell["qualification_binding_sha256"] == binding_sha256
            and cell["qualification_stable_case_aliases"]
            == _FINALIZED_SKILL_EXTRACTION_STABLE_CASE_ALIASES,
            "finalized Skill V2 qualified candidate authority changed",
        )
    return True


def build_renderer_bound_v2_workload_recommendation(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return one V2 recommendation entry after fail-closed validation."""

    validate_renderer_bound_v2_workload_recommendation(
        renderer_bound_registry,
        pin=pin,
    )
    return deepcopy(
        {
            "workload_id": pin["workload_id"],
            "recommendation_status": "recommended",
            "provider": pin["provider"],
            "model": pin["model"],
            "selection_basis": pin["selection_basis"],
            "qualification_semantics_generation": (
                pin["expected_qualification_semantics_generation"]
            ),
            "task_contract_sha256": pin["expected_current_task_contract_sha256"],
            "workload_qualification_semantics_sha256": (
                pin["expected_current_workload_qualification_semantics_sha256"]
            ),
            "qualification_binding_sha256": (
                pin["expected_qualification_binding_sha256"]
            ),
            "qualification_stable_case_aliases": deepcopy(
                pin["expected_qualification_stable_case_aliases"]
            ),
            "evidence_sha256": pin["expected_evidence_sha256"],
            "review_sha256": pin["expected_review_sha256"],
        }
    )

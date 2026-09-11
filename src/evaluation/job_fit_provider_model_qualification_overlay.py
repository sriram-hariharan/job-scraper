"""Reviewed Job Fit qualification overlay for app-layer routing.

This module is read-only. It validates the frozen qualification-registry base
and current production Job Fit contract before exposing the reviewed routing
identities. Detailed comparison observations remain evaluation-private.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from src.evaluation import (
    controlled_provider_qualification_registry as qualification_registry,
)
from src.evaluation.production_task_contract_fingerprints import (
    production_task_contract_sha256,
)
from src.evaluation.provider_model_recommendation_policy import (
    RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
    SOURCE_QUALIFICATION_REGISTRY_SHA256,
    build_renderer_bound_workload_recommendation,
    validate_renderer_bound_workload_recommendation,
)


_WORKLOAD_ID = "job_fit_evaluation"
_JOB_FIT_TASK_CONTRACT_SHA256 = (
    "e9568a48240886579814a557b414461510f86485e3bb7a50efc3e7ab8e319480"
)
_SELECTION_BASIS = (
    "reviewed_production_aligned_quality_tie_latency_tiebreak"
)

# Evaluation-private, reviewed comparison observations. Cost is diagnostic
# only; all candidates passed the approved production-aligned quality gate.
_REVIEWED_COMPARISON_SUMMARIES = (
    ("groq", "openai/gpt-oss-20b", 940.239, 297, 556, 0.00018908),
    ("groq", "openai/gpt-oss-120b", 1247.350, 297, 517, 0.00035475),
    ("openai", "gpt-5-mini", 3376.943, 234, 165, 0.00038850),
    ("openai", "gpt-5.1", 1691.876, 234, 113, 0.00142250),
)
_EXPECTED_IDENTITIES = tuple(
    (provider, model)
    for provider, model, *_observations in _REVIEWED_COMPARISON_SUMMARIES
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_job_fit_provider_model_qualification_overlay(
    registry_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Return the reviewed Job Fit routing overlay after base validation."""

    payload = deepcopy(registry_payload)
    qualification_registry.validate_provider_qualification_registry(payload)

    registry_sha256 = (
        qualification_registry.provider_qualification_registry_sha256(
            payload
        )
    )
    _require(
        registry_sha256 == SOURCE_QUALIFICATION_REGISTRY_SHA256,
        "Job Fit qualification overlay registry base changed",
    )

    _require(
        production_task_contract_sha256(_WORKLOAD_ID)
        == _JOB_FIT_TASK_CONTRACT_SHA256,
        "Job Fit production task contract changed",
    )

    job_fit_cells = [
        cell
        for cell in payload["cells"]
        if cell["workload_id"] == _WORKLOAD_ID
    ]
    identities = tuple(
        (cell["provider"], cell["model"])
        for cell in job_fit_cells
    )
    _require(
        identities == _EXPECTED_IDENTITIES,
        "Job Fit qualification overlay base universe changed",
    )
    _require(
        all(cell["status"] != "qualified" for cell in job_fit_cells),
        "Job Fit base registry unexpectedly contains a qualified cell",
    )

    result = {
        "workload_id": _WORKLOAD_ID,
        "recommendation_status": "recommended",
        "provider": _EXPECTED_IDENTITIES[0][0],
        "model": _EXPECTED_IDENTITIES[0][1],
        "selection_basis": _SELECTION_BASIS,
        "qualified_options": [
            {"provider": provider, "model": model}
            for provider, model in _EXPECTED_IDENTITIES
        ],
    }
    return deepcopy(result)


RENDERER_BOUND_JOB_FIT_OVERLAY_VERSION = (
    "job-fit-provider-model-qualification-overlay-renderer-bound-v1"
)


def validate_renderer_bound_job_fit_overlay(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Dict[str, Any],
) -> bool:
    """Validate a future Job Fit selection against renderer-bound authority.

    The winner and the selection basis are always taken from the explicit
    caller-supplied pin. Neither ``_REVIEWED_COMPARISON_SUMMARIES`` nor
    ``_EXPECTED_IDENTITIES`` nor ``_SELECTION_BASIS`` participates: those
    historical observations have no retained renderer-bound evidence, so they
    cannot confer next-generation authority.
    """

    _require(
        isinstance(pin, dict)
        and pin.get("pin_version") == RENDERER_BOUND_RECOMMENDATION_PIN_VERSION,
        "renderer-bound Job Fit pin version mismatch",
    )
    _require(
        pin.get("workload_id") == _WORKLOAD_ID,
        "renderer-bound Job Fit pin workload mismatch",
    )
    universe = pin.get("expected_candidate_universe")
    _require(
        isinstance(universe, list) and len(universe) == 4,
        "renderer-bound Job Fit pin must bind the complete candidate set",
    )
    # Workload-local by construction: only Job Fit cells are consulted.
    validate_renderer_bound_workload_recommendation(
        renderer_bound_registry,
        pin=pin,
    )
    return True


def build_renderer_bound_job_fit_overlay(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Dict[str, Any],
) -> Dict[str, Any]:
    """Return the future Job Fit overlay entry from an explicit pin only."""

    validate_renderer_bound_job_fit_overlay(
        renderer_bound_registry,
        pin=pin,
    )
    entry = build_renderer_bound_workload_recommendation(
        renderer_bound_registry,
        pin=pin,
    )
    return deepcopy(
        {
            "overlay_version": RENDERER_BOUND_JOB_FIT_OVERLAY_VERSION,
            "workload_id": _WORKLOAD_ID,
            "recommendation_status": entry["recommendation_status"],
            "provider": entry["provider"],
            "model": entry["model"],
            "selection_basis": entry["selection_basis"],
            "qualification_semantics_generation": (
                entry["qualification_semantics_generation"]
            ),
            "qualification_binding_sha256": (
                entry["qualification_binding_sha256"]
            ),
            "evidence_sha256": entry["evidence_sha256"],
            "review_sha256": entry["review_sha256"],
            "qualified_options": [
                {
                    "provider": candidate["provider"],
                    "model": candidate["model"],
                }
                for candidate in pin["expected_candidate_universe"]
                if candidate["status"] == "qualified"
            ],
        }
    )


RENDERER_BOUND_V2_JOB_FIT_OVERLAY_VERSION = (
    "job-fit-provider-model-qualification-overlay-renderer-bound-v2"
)


def validate_renderer_bound_v2_job_fit_overlay(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Dict[str, Any],
) -> bool:
    """Validate a Job Fit selection against renderer-bound V2 authority."""

    from src.evaluation.provider_model_recommendation_policy import (
        RENDERER_BOUND_V2_RECOMMENDATION_PIN_VERSION,
        validate_renderer_bound_v2_workload_recommendation,
    )

    _require(
        isinstance(pin, dict)
        and pin.get("pin_version")
        == RENDERER_BOUND_V2_RECOMMENDATION_PIN_VERSION,
        "renderer-bound V2 Job Fit pin version mismatch",
    )
    _require(
        pin.get("workload_id") == _WORKLOAD_ID,
        "renderer-bound V2 Job Fit pin workload mismatch",
    )
    universe = pin.get("expected_candidate_universe")
    _require(
        isinstance(universe, list) and len(universe) == 4,
        "renderer-bound V2 Job Fit pin must bind the complete candidate set",
    )
    # Workload-local by construction: only Job Fit cells are consulted.
    validate_renderer_bound_v2_workload_recommendation(
        renderer_bound_registry,
        pin=pin,
    )
    return True


def build_renderer_bound_v2_job_fit_overlay(
    renderer_bound_registry: Dict[str, Any],
    *,
    pin: Dict[str, Any],
) -> Dict[str, Any]:
    """Return the Job Fit V2 overlay entry from an explicit pin only."""

    from src.evaluation.provider_model_recommendation_policy import (
        build_renderer_bound_v2_workload_recommendation,
    )

    validate_renderer_bound_v2_job_fit_overlay(
        renderer_bound_registry,
        pin=pin,
    )
    entry = build_renderer_bound_v2_workload_recommendation(
        renderer_bound_registry,
        pin=pin,
    )
    return deepcopy(
        {
            "overlay_version": RENDERER_BOUND_V2_JOB_FIT_OVERLAY_VERSION,
            "workload_id": _WORKLOAD_ID,
            "recommendation_status": entry["recommendation_status"],
            "provider": entry["provider"],
            "model": entry["model"],
            "selection_basis": entry["selection_basis"],
            "qualification_semantics_generation": (
                entry["qualification_semantics_generation"]
            ),
            "qualification_binding_sha256": (
                entry["qualification_binding_sha256"]
            ),
            "qualification_stable_case_aliases": deepcopy(
                entry["qualification_stable_case_aliases"]
            ),
            "evidence_sha256": entry["evidence_sha256"],
            "review_sha256": entry["review_sha256"],
            "qualified_options": [
                {
                    "provider": candidate["provider"],
                    "model": candidate["model"],
                }
                for candidate in pin["expected_candidate_universe"]
                if candidate["status"] == "qualified"
            ],
        }
    )

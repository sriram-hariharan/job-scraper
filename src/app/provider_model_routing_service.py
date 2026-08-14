"""App-layer bridge from frozen model recommendations to user runtime.

This module is intentionally not wired into production task owners, API routes,
or UI yet.

Responsibilities:
- load the authoritative qualification registry,
- read the frozen recommendation for one workload,
- fail closed for non-recommended workloads before credential resolution,
- pass the exact recommended provider/model to the existing user runtime.

Non-responsibilities:
- model ranking,
- provider substitution,
- fallback selection,
- user preferred-provider override,
- credential persistence,
- application mutation,
- ATS mutation.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from src.ai.user_provider_runtime import (
    run_user_chat_completion_with_metadata,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation import (
    controlled_provider_qualification_registry as qualification_registry,
)
from src.evaluation.provider_model_recommendation_policy import (
    build_provider_model_recommendation_policy,
    read_provider_model_recommendation,
)
from src.evaluation.job_fit_provider_model_qualification_overlay import (
    build_job_fit_provider_model_qualification_overlay,
)
from src.storage.user_ai_settings.store import (
    list_user_ai_task_model_selections_payload,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

_EXECUTION_MODE_BY_RECOMMENDATION_STATUS = {
    "recommended": "qualified_provider_model",
    "fail_closed_zero_qualified": "deterministic",
    "blocked_non_live": "blocked_non_live",
}


class RecommendedProviderRoutingUnavailableError(RuntimeError):
    """Raised when a workload has no authorized recommended route."""

    def __init__(
        self,
        workload_id: str,
        recommendation_status: str,
    ) -> None:
        self.workload_id = workload_id
        self.recommendation_status = recommendation_status
        super().__init__(
            "recommended_provider_route_unavailable:"
            f"{workload_id}:{recommendation_status}"
        )


class EffectiveProviderRoutingUnavailableError(RuntimeError):
    """Raised when an owner has no authorized effective route."""

    def __init__(self, workload_id: str, routing_status: str) -> None:
        self.workload_id = workload_id
        self.routing_status = routing_status
        super().__init__(
            "effective_provider_route_unavailable:"
            f"{workload_id}:{routing_status}"
        )


class ProviderModelSelectionNotQualifiedError(ValueError):
    """Raised when an exact requested task route is not currently selectable."""


def _load_authoritative_qualification_registry() -> Dict[str, Any]:
    plan = build_controlled_provider_benchmark_plan()

    return qualification_registry.load_provider_qualification_registry(
        _REPOSITORY_ROOT / qualification_registry.REGISTRY_ARTIFACT_PATH,
        repository_root=_REPOSITORY_ROOT,
        plan=plan,
    )


def _owner_requested_selections(
    owner_user_id: Optional[str],
) -> Dict[str, Dict[str, str]]:
    if owner_user_id is None:
        return {}

    owner = str(owner_user_id or "").strip()
    if not owner:
        raise ValueError("owner_user_id is required")

    try:
        payload = list_user_ai_task_model_selections_payload(owner)
    except (Exception, SystemExit):
        raise ValueError("owner task selections are unavailable") from None

    data = dict(payload.get("data", {}) or {})
    if str(data.get("owner_user_id") or "").strip() != owner:
        raise ValueError("owner task selection boundary mismatch")

    selections: Dict[str, Dict[str, str]] = {}
    for row in list(data.get("selections") or []):
        if not isinstance(row, dict):
            raise ValueError("owner task selections are malformed")
        workload_id = str(row.get("workload_id") or "").strip()
        provider = str(row.get("provider") or "").strip().lower()
        model = str(row.get("model") or "").strip()
        if not workload_id or not provider or not model:
            raise ValueError("owner task selection is malformed")
        if workload_id in selections:
            raise ValueError("owner task selection is duplicated")
        selections[workload_id] = {
            "provider": provider,
            "model": model,
        }
    return selections


def list_provider_model_routing_statuses(
    owner_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return all frozen routing statuses without granting execution authority."""

    registry_payload = _load_authoritative_qualification_registry()

    policy = build_provider_model_recommendation_policy(
        registry_payload
    )
    job_fit_overlay = build_job_fit_provider_model_qualification_overlay(
        registry_payload
    )
    if job_fit_overlay.get("workload_id") != "job_fit_evaluation":
        raise ValueError("Job Fit qualification overlay workload mismatch")
    requested_selections = _owner_requested_selections(owner_user_id)

    qualified_options_by_workload: Dict[str, list[Dict[str, str]]] = {}

    for cell in sorted(
        registry_payload["cells"],
        key=lambda item: item["execution_order"],
    ):
        if cell["status"] != "qualified":
            continue

        qualified_options_by_workload.setdefault(
            cell["workload_id"],
            [],
        ).append(
            {
                "provider": cell["provider"],
                "model": cell["model"],
            }
        )

    workloads = []

    for entry in policy["workloads"]:
        is_job_fit = entry["workload_id"] == "job_fit_evaluation"
        effective_entry = (
            job_fit_overlay
            if is_job_fit
            else entry
        )
        recommendation_status = str(
            effective_entry.get("recommendation_status") or ""
        ).strip()

        provider = (
            str(effective_entry.get("provider") or "").strip()
            if recommendation_status == "recommended"
            else ""
        )

        model = (
            str(effective_entry.get("model") or "").strip()
            if recommendation_status == "recommended"
            else ""
        )

        try:
            execution_mode = _EXECUTION_MODE_BY_RECOMMENDATION_STATUS[
                recommendation_status
            ]
        except KeyError as exc:
            raise ValueError(
                "unsupported provider recommendation status:"
                f"{recommendation_status}"
            ) from exc

        qualified_options = deepcopy(
            effective_entry.get("qualified_options")
            if is_job_fit
            else qualified_options_by_workload.get(
                entry["workload_id"],
                [],
            )
        )
        recommended_option = (
            {
                "provider": provider,
                "model": model,
            }
            if recommendation_status == "recommended"
            else None
        )

        if recommendation_status == "recommended":
            if recommended_option not in qualified_options:
                raise ValueError(
                    "recommended provider/model is not currently qualified:"
                    f"{entry['workload_id']}"
                )
        elif qualified_options:
            raise ValueError(
                "non-recommended workload unexpectedly has qualified options:"
                f"{entry['workload_id']}"
            )

        requested_selection = requested_selections.get(
            entry["workload_id"]
        )
        requested_selection_status = "none"
        if requested_selection is not None:
            requested_selection_status = (
                "qualified"
                if requested_selection in qualified_options
                else "no_longer_qualified"
            )

        if execution_mode == "qualified_provider_model":
            if requested_selection_status == "qualified":
                effective_selection = dict(requested_selection or {})
                effective_selection_source = "user_override"
            else:
                effective_selection = dict(recommended_option or {})
                effective_selection_source = "applylens_recommended"
        elif execution_mode == "deterministic":
            effective_selection = None
            effective_selection_source = "deterministic"
        else:
            effective_selection = None
            effective_selection_source = "blocked_non_live"

        workloads.append(
            {
                "workload_id": entry["workload_id"],
                "recommendation_status": recommendation_status,
                "provider": provider or None,
                "model": model or None,
                "selection_basis": (
                    effective_entry.get("selection_basis")
                    if recommendation_status == "recommended"
                    else None
                ),
                "execution_mode": execution_mode,
                "recommended_option": recommended_option,
                "qualified_options": qualified_options,
                "requested_selection": requested_selection,
                "requested_selection_status": requested_selection_status,
                "effective_selection": effective_selection,
                "effective_selection_source": effective_selection_source,
            }
        )

    return {
        "workloads": workloads,
    }


def read_provider_model_routing_status(
    workload_id: str,
    *,
    owner_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    workload = str(workload_id or "").strip()
    if not workload:
        raise ValueError("workload_id is required")
    matches = [
        row
        for row in list_provider_model_routing_statuses(
            owner_user_id=owner_user_id
        )["workloads"]
        if row["workload_id"] == workload
    ]
    if len(matches) != 1:
        raise ValueError("workload is not part of the routing contract")
    return matches[0]


def validate_current_qualified_provider_model_selection(
    workload_id: str,
    provider: str,
    model: str,
) -> Dict[str, str]:
    workload = str(workload_id or "").strip()
    provider_name = str(provider or "").strip().lower()
    model_name = str(model or "").strip()
    if not workload or not provider_name or not model_name:
        raise ValueError("task route selection is incomplete")

    matches = [
        row
        for row in list_provider_model_routing_statuses()["workloads"]
        if row["workload_id"] == workload
    ]
    if len(matches) != 1:
        raise ProviderModelSelectionNotQualifiedError(
            "task route workload is not currently selectable"
        )
    route = matches[0]
    candidate = {
        "provider": provider_name,
        "model": model_name,
    }
    if (
        route["execution_mode"] != "qualified_provider_model"
        or candidate not in route["qualified_options"]
    ):
        raise ProviderModelSelectionNotQualifiedError(
            "task route selection is not currently qualified"
        )
    return candidate


def resolve_effective_user_provider_route(
    owner_user_id: str,
    workload_id: str,
) -> Dict[str, Any]:
    """Resolve one owner's current effective route without credentials."""

    owner = str(owner_user_id or "").strip()
    workload = str(workload_id or "").strip()
    if not owner:
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            "invalid_owner",
        )
    if not workload:
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            "invalid_workload",
        )

    try:
        route = read_provider_model_routing_status(
            workload,
            owner_user_id=owner,
        )
    except ValueError:
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            "routing_status_unavailable",
        ) from None

    if not isinstance(route, dict) or route.get("workload_id") != workload:
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            "invalid_routing_status",
        )

    execution_mode = route.get("execution_mode")
    if execution_mode != "qualified_provider_model":
        routing_status = (
            execution_mode
            if execution_mode in {"deterministic", "blocked_non_live"}
            else "invalid_execution_mode"
        )
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            routing_status,
        )

    effective_selection = route.get("effective_selection")
    if (
        type(effective_selection) is not dict
        or set(effective_selection) != {"provider", "model"}
        or not isinstance(effective_selection.get("provider"), str)
        or not effective_selection["provider"].strip()
        or not isinstance(effective_selection.get("model"), str)
        or not effective_selection["model"].strip()
    ):
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            "invalid_effective_selection",
        )

    source = route.get("effective_selection_source")
    if source not in {"user_override", "applylens_recommended"}:
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            "invalid_effective_selection_source",
        )

    selection = {
        "provider": effective_selection["provider"].strip(),
        "model": effective_selection["model"].strip(),
    }
    qualified_options = route.get("qualified_options")
    if (
        not isinstance(qualified_options, list)
        or selection not in qualified_options
    ):
        raise EffectiveProviderRoutingUnavailableError(
            workload,
            "effective_selection_not_qualified",
        )

    return {
        "workload_id": workload,
        **selection,
        "effective_selection_source": source,
    }


def resolve_recommended_user_provider_route(
    workload_id: str,
) -> Dict[str, Any]:
    """Resolve one frozen recommended route without reading credentials."""

    registry_payload = _load_authoritative_qualification_registry()

    recommendation = read_provider_model_recommendation(
        registry_payload,
        workload_id,
    )

    recommendation_status = str(
        recommendation.get("recommendation_status") or ""
    ).strip()

    if recommendation_status != "recommended":
        raise RecommendedProviderRoutingUnavailableError(
            workload_id,
            recommendation_status,
        )

    provider = str(recommendation.get("provider") or "").strip()
    model = str(recommendation.get("model") or "").strip()

    if not provider or not model:
        raise RecommendedProviderRoutingUnavailableError(
            workload_id,
            "invalid_recommended_identity",
        )

    return {
        "workload_id": workload_id,
        "recommendation_status": recommendation_status,
        "provider": provider,
        "model": model,
        "selection_basis": recommendation.get("selection_basis"),
        "task_contract_sha256": recommendation.get(
            "task_contract_sha256"
        ),
        "qualification_binding_sha256": recommendation.get(
            "qualification_binding_sha256"
        ),
        "evidence_sha256": recommendation.get("evidence_sha256"),
        "review_sha256": recommendation.get("review_sha256"),
    }


def run_recommended_user_chat_completion_with_metadata(
    owner_user_id: str,
    workload_id: str,
    messages: Any,
    *,
    temperature: float = 0,
    max_tokens: int = 500,
    response_mime_type: Optional[str] = None,
    response_schema: Optional[Dict[str, Any]] = None,
    return_parsed: bool = False,
    thinking_budget: Optional[int] = None,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    """Run one exact frozen recommendation through user-scoped runtime."""

    route = resolve_recommended_user_provider_route(workload_id)

    return run_user_chat_completion_with_metadata(
        owner_user_id=owner_user_id,
        provider=route["provider"],
        model=route["model"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_mime_type=response_mime_type,
        response_schema=response_schema,
        return_parsed=return_parsed,
        thinking_budget=thinking_budget,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        ensure_schema=ensure_schema,
    )


def run_effective_user_chat_completion_with_metadata(
    owner_user_id: str,
    workload_id: str,
    messages: Any,
    *,
    temperature: float = 0,
    max_tokens: int = 500,
    response_mime_type: Optional[str] = None,
    response_schema: Optional[Dict[str, Any]] = None,
    return_parsed: bool = False,
    thinking_budget: Optional[int] = None,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    """Run one owner's current effective route through user runtime."""

    route = resolve_effective_user_provider_route(
        owner_user_id,
        workload_id,
    )

    return run_user_chat_completion_with_metadata(
        owner_user_id=owner_user_id,
        provider=route["provider"],
        model=route["model"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_mime_type=response_mime_type,
        response_schema=response_schema,
        return_parsed=return_parsed,
        thinking_budget=thinking_budget,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        ensure_schema=ensure_schema,
    )

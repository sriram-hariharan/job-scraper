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
    read_provider_model_recommendation,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


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


def _load_authoritative_qualification_registry() -> Dict[str, Any]:
    plan = build_controlled_provider_benchmark_plan()

    return qualification_registry.load_provider_qualification_registry(
        _REPOSITORY_ROOT / qualification_registry.REGISTRY_ARTIFACT_PATH,
        repository_root=_REPOSITORY_ROOT,
        plan=plan,
    )


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

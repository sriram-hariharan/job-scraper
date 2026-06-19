"""Default-off embedding provider contract for vector evidence.

The helper calls only an explicitly injected callable. It imports no provider
SDK, reads no credentials, opens no network or database connection, and has no
API, UI, or pipeline hook.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Callable


EMBEDDING_PROVIDER_CONTRACT_VERSION = (
    "phase-9a-vector-evidence-embedding-provider-v1"
)

STATUS_SKIPPED_DEFAULT_OFF = "embedding_provider_skipped_default_off"
STATUS_NOT_CONFIGURED = "embedding_provider_not_configured"
STATUS_READY = "embedding_provider_embedding_ready"
STATUS_INVALID_REQUEST = "embedding_provider_invalid_request"
STATUS_INVALID_RESPONSE = "embedding_provider_invalid_response"
STATUS_FAILED_NON_BLOCKING = "embedding_provider_failed_non_blocking"

EmbeddingProvider = Callable[[dict[str, Any]], Any]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _positive_dimension(value: Any) -> int:
    try:
        dimension = int(value)
    except (TypeError, ValueError):
        return 0
    return dimension if dimension > 0 else 0


def embedding_provider_safety_metadata(
    *,
    enabled: bool = False,
    configured: bool = False,
    provider_calls_made: bool = False,
    embeddings_created: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "embedding_provider_contract": True,
        "embedding_provider_enabled": bool(enabled),
        "embedding_provider_configured": bool(configured),
        "provider_calls_made": bool(provider_calls_made),
        "embeddings_created": bool(embeddings_created),
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "api_route_added": False,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _base_payload(
    *,
    status: str,
    enabled: bool,
    configured: bool,
    request: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_version": EMBEDDING_PROVIDER_CONTRACT_VERSION,
        "status": status,
        "default_off": True,
        "embedding_provider_enabled": bool(enabled),
        "embedding_provider_configured": bool(configured),
        "request": deepcopy(request),
        "embedding": [],
        "embedding_dimension": 0,
        "embedding_model_id": _clean_text(request.get("embedding_model_id")),
        "validation": {
            "is_valid": False,
            "errors": [],
        },
        "errors": [],
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": embedding_provider_safety_metadata(
            enabled=enabled,
            configured=configured,
        ),
    }


def _provider_vector(response: Any) -> Any:
    if isinstance(response, dict):
        for key in ("embedding", "vector", "values"):
            if key in response:
                return response.get(key)
        data = response.get("data")
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0].get("embedding")
        return None
    return response


def _validated_vector(
    value: Any,
    *,
    expected_dimension: int,
) -> tuple[list[float], list[str]]:
    if not isinstance(value, (list, tuple)):
        return [], ["embedding_vector_must_be_list"]
    if not value:
        return [], ["embedding_vector_must_not_be_empty"]

    vector: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return [], ["embedding_vector_values_must_be_numeric"]
        number = float(item)
        if not math.isfinite(number):
            return [], ["embedding_vector_values_must_be_finite"]
        vector.append(number)

    if expected_dimension and len(vector) != expected_dimension:
        return [], ["embedding_dimension_mismatch"]
    return vector, []


def run_vector_evidence_embedding_provider(
    *,
    enabled: bool = False,
    text: str = "",
    embedding_model_id: str = "",
    expected_dimension: int = 0,
    request_id: str = "",
    provider: EmbeddingProvider | None = None,
) -> dict[str, Any]:
    """Normalize and optionally execute one injected embedding request."""

    request = {
        "request_id": _clean_text(request_id),
        "text": _clean_text(text),
        "embedding_model_id": _clean_text(embedding_model_id),
        "expected_dimension": _positive_dimension(expected_dimension),
    }
    configured = callable(provider)
    payload = _base_payload(
        status=STATUS_SKIPPED_DEFAULT_OFF,
        enabled=enabled is True,
        configured=configured,
        request=request,
    )
    if enabled is not True:
        return payload
    if not configured:
        payload["status"] = STATUS_NOT_CONFIGURED
        payload["errors"] = ["injected_provider_required"]
        payload["validation"]["errors"] = ["injected_provider_required"]
        return payload

    request_errors: list[str] = []
    if not request["text"]:
        request_errors.append("text_required")
    if not request["embedding_model_id"]:
        request_errors.append("embedding_model_id_required")
    if not request["expected_dimension"]:
        request_errors.append("expected_dimension_required")
    if request_errors:
        payload["status"] = STATUS_INVALID_REQUEST
        payload["errors"] = request_errors
        payload["validation"]["errors"] = list(request_errors)
        return payload

    try:
        response = provider(deepcopy(request))
    except Exception as exc:
        payload["status"] = STATUS_FAILED_NON_BLOCKING
        payload["errors"] = [exc.__class__.__name__]
        payload["validation"]["errors"] = ["provider_exception"]
        payload["safety_metadata"] = embedding_provider_safety_metadata(
            enabled=True,
            configured=True,
            provider_calls_made=True,
            embeddings_created=False,
        )
        return payload

    vector, validation_errors = _validated_vector(
        _provider_vector(response),
        expected_dimension=request["expected_dimension"],
    )
    if validation_errors:
        payload["status"] = STATUS_INVALID_RESPONSE
        payload["errors"] = list(validation_errors)
        payload["validation"]["errors"] = list(validation_errors)
        payload["safety_metadata"] = embedding_provider_safety_metadata(
            enabled=True,
            configured=True,
            provider_calls_made=True,
            embeddings_created=False,
        )
        return payload

    payload.update(
        {
            "status": STATUS_READY,
            "embedding": vector,
            "embedding_dimension": len(vector),
            "validation": {
                "is_valid": True,
                "errors": [],
            },
            "safety_metadata": embedding_provider_safety_metadata(
                enabled=True,
                configured=True,
                provider_calls_made=True,
                embeddings_created=True,
            ),
        }
    )
    return payload

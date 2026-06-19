"""Default-off runtime adapter for vector evidence embeddings.

The repository's existing embedding runtime exposes an ``encode`` method.
This adapter supports that shape, or a directly injected callable, without
importing or initializing the runtime itself. Validation remains delegated to
the Phase 9A embedding provider contract.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.storage.vector_evidence import embedding_provider


EMBEDDING_RUNTIME_ADAPTER_VERSION = (
    "phase-9f-vector-evidence-embedding-runtime-adapter-v1"
)

STATUS_SKIPPED_DEFAULT_OFF = "embedding_runtime_adapter_skipped_default_off"
STATUS_NOT_CONFIGURED = "embedding_runtime_adapter_not_configured"
STATUS_READY = "embedding_runtime_adapter_embedding_ready"
STATUS_INVALID_RESPONSE = "embedding_runtime_adapter_invalid_response"
STATUS_FAILED_NON_BLOCKING = "embedding_runtime_adapter_failed_non_blocking"


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def embedding_runtime_adapter_safety_metadata(
    *,
    enabled: bool = False,
    configured: bool = False,
    provider_calls_made: bool = False,
    embeddings_created: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "embedding_runtime_adapter": True,
        "runtime_adapter_enabled": bool(enabled),
        "provider_configured": bool(configured),
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
    enabled: bool,
    configured: bool,
    provider_mechanism: str,
) -> dict[str, Any]:
    return {
        "adapter_version": EMBEDDING_RUNTIME_ADAPTER_VERSION,
        "status": STATUS_SKIPPED_DEFAULT_OFF,
        "default_off": True,
        "runtime_adapter_enabled": bool(enabled),
        "provider_configured": bool(configured),
        "provider_mechanism": provider_mechanism,
        "embedding": [],
        "embedding_dimension": 0,
        "embedding_model_id": "",
        "provider_contract_payload": {},
        "errors": [],
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": embedding_runtime_adapter_safety_metadata(
            enabled=enabled,
            configured=configured,
        ),
    }


def _plain_vector(value: Any) -> Any:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    return value


def _injected_provider(
    *,
    provider_callable: Callable[[dict[str, Any]], Any] | None,
    provider_client: Any,
) -> tuple[Callable[[dict[str, Any]], Any] | None, str]:
    if callable(provider_callable):
        return provider_callable, "injected_provider_callable"

    encode = getattr(provider_client, "encode", None)
    if not callable(encode):
        return None, "not_configured"

    def call_encode(request: dict[str, Any]) -> Any:
        response = encode(
            request["text"],
            normalize_embeddings=True,
        )
        return _plain_vector(response)

    return call_encode, "injected_encode_client"


def run_vector_evidence_embedding_runtime_adapter(
    *,
    enabled: bool = False,
    text: str = "",
    embedding_model_id: str = "",
    expected_dimension: int = 0,
    request_id: str = "",
    provider_callable: Callable[[dict[str, Any]], Any] | None = None,
    provider_client: Any = None,
    embedding_provider_module: Any = None,
) -> dict[str, Any]:
    """Run one explicitly configured embedding request through Phase 9A."""

    provider, mechanism = _injected_provider(
        provider_callable=provider_callable,
        provider_client=provider_client,
    )
    configured = callable(provider)
    payload = _base_payload(
        enabled=enabled is True,
        configured=configured,
        provider_mechanism=mechanism,
    )
    if enabled is not True:
        return payload
    if not configured:
        payload["status"] = STATUS_NOT_CONFIGURED
        payload["errors"] = ["injected_provider_callable_or_client_required"]
        payload["safety_metadata"] = embedding_runtime_adapter_safety_metadata(
            enabled=True,
            configured=False,
        )
        return payload

    contract_module = embedding_provider_module or embedding_provider
    contract_payload = contract_module.run_vector_evidence_embedding_provider(
        enabled=True,
        text=text,
        embedding_model_id=embedding_model_id,
        expected_dimension=expected_dimension,
        request_id=request_id,
        provider=provider,
    )
    contract_safety = contract_payload.get("safety_metadata")
    contract_safety = (
        deepcopy(contract_safety) if isinstance(contract_safety, dict) else {}
    )
    provider_calls_made = bool(contract_safety.get("provider_calls_made"))
    embeddings_created = bool(contract_safety.get("embeddings_created"))
    contract_status = _clean_text(contract_payload.get("status"))

    if contract_status == embedding_provider.STATUS_READY:
        status = STATUS_READY
    elif contract_status == embedding_provider.STATUS_INVALID_RESPONSE:
        status = STATUS_INVALID_RESPONSE
    else:
        status = STATUS_FAILED_NON_BLOCKING

    payload.update(
        {
            "status": status,
            "embedding": list(contract_payload.get("embedding") or []),
            "embedding_dimension": int(
                contract_payload.get("embedding_dimension") or 0
            ),
            "embedding_model_id": _clean_text(
                contract_payload.get("embedding_model_id")
            ),
            "provider_contract_payload": deepcopy(contract_payload),
            "errors": list(contract_payload.get("errors") or []),
            "safety_metadata": embedding_runtime_adapter_safety_metadata(
                enabled=True,
                configured=True,
                provider_calls_made=provider_calls_made,
                embeddings_created=embeddings_created,
            ),
        }
    )
    return payload

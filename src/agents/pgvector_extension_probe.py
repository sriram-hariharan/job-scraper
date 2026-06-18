"""Deterministic, dependency-injected pgvector extension probe contract.

The helper is default-off and imports no database driver. It creates no schema,
migration, embedding, provider call, pipeline stage, or application mutation.
A caller may explicitly inject a read-only probe executor; tests use static
executors and never connect to a real database.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


CONTRACT_VERSION = "phase-8j-pgvector-extension-probe-v1"

STATUS_NOT_CONFIGURED = "pgvector_probe_not_configured"
STATUS_AVAILABLE = "pgvector_probe_available"
STATUS_MISSING = "pgvector_probe_missing"
STATUS_FAILED_NON_BLOCKING = "pgvector_probe_failed_non_blocking"

ProbeExecutor = Callable[[dict[str, Any]], dict[str, Any]]


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _optional_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _positive_int_list(value: Any) -> list[int]:
    source = value if isinstance(value, (list, tuple, set)) else []
    normalized: list[int] = []
    for item in source:
        parsed = _optional_positive_int(item)
        if parsed is not None and parsed not in normalized:
            normalized.append(parsed)
    return sorted(normalized)


def pgvector_extension_probe_safety_metadata(
    *,
    vector_db_connected: bool = False,
    did_read_database: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "pgvector_extension_probe": True,
        "pgvector_installed_by_app": False,
        "schema_created": False,
        "migration_created": False,
        "embeddings_created": False,
        "vector_db_connected": bool(vector_db_connected),
        "provider_calls_made": False,
        "did_read_database": bool(did_read_database),
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
        "service_helper_added": False,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _evaluation_boundaries() -> dict[str, str]:
    return {
        "prefilter_relevance": "separate_unchanged",
        "llm_shadow_evaluation": "separate_advisory_only",
        "final_application_scoring": "separate_unchanged",
        "retrieval_evidence_support": "extension_probe_only",
    }


def build_pgvector_extension_probe_request_payload(
    *,
    extension_name: str = "vector",
    requested_dimension: int | None = None,
    probe_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an inert probe request without reading configuration or storage."""

    return {
        "contract_version": CONTRACT_VERSION,
        "probe_type": "pgvector_extension_probe",
        "extension_name": _clean_text(extension_name) or "vector",
        "requested_dimension": _optional_positive_int(requested_dimension),
        "probe_context": _plain_dict(probe_context),
        "default_off": True,
        "executor_required": True,
        "read_only": True,
        "advisory_only": True,
    }


def _availability_signal(result: dict[str, Any]) -> bool:
    for key in (
        "extension_available",
        "available",
        "extension_installed",
        "installed",
    ):
        if result.get(key) is True:
            return True
    return _clean_text(result.get("status")) == STATUS_AVAILABLE


def normalize_pgvector_extension_probe_result_payload(
    probe_result: dict[str, Any] | None,
    *,
    request_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize a caller-supplied static probe result without side effects."""

    request = _plain_dict(request_payload)
    result = _plain_dict(probe_result)
    available = _availability_signal(result)
    status = STATUS_AVAILABLE if available else STATUS_MISSING
    requested_dimension = _optional_positive_int(
        result.get("requested_dimension")
        if result.get("requested_dimension") is not None
        else request.get("requested_dimension")
    )
    supported_dimensions = _positive_int_list(
        result.get("supported_dimensions")
        or result.get("embedding_dimensions")
    )
    dimension_supported = result.get("dimension_supported")
    if not isinstance(dimension_supported, bool):
        dimension_supported = (
            requested_dimension in supported_dimensions
            if requested_dimension is not None and supported_dimensions
            else None
        )

    vector_db_connected = bool(available)
    did_read_database = result.get("did_read_database") is True
    safety = pgvector_extension_probe_safety_metadata(
        vector_db_connected=vector_db_connected,
        did_read_database=did_read_database,
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "probe_type": "pgvector_extension_probe",
        "default_off": True,
        "probe_configured": True,
        "probe_executed": True,
        "extension_name": (
            _clean_text(result.get("extension_name"))
            or _clean_text(request.get("extension_name"))
            or "vector"
        ),
        "extension_available": available,
        "extension_installed": bool(
            result.get("extension_installed") is True
            or result.get("installed") is True
        ),
        "available_version": _clean_text(
            result.get("available_version")
            or result.get("default_version")
            or result.get("extension_version")
        ),
        "installed_version": _clean_text(
            result.get("installed_version")
            or result.get("current_version")
        ),
        "postgres_version": _clean_text(
            result.get("postgres_version")
            or result.get("server_version")
        ),
        "requested_dimension": requested_dimension,
        "supported_dimensions": supported_dimensions,
        "dimension_supported": dimension_supported,
        "vector_type_available": result.get("vector_type_available") is True,
        "supported_index_methods": sorted(
            {
                _clean_text(item)
                for item in (
                    result.get("supported_index_methods")
                    if isinstance(result.get("supported_index_methods"), list)
                    else []
                )
                if _clean_text(item)
            }
        ),
        "probe_details": _plain_dict(result.get("probe_details")),
        "error_type": "",
        "error_message": "",
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "evaluation_boundaries": _evaluation_boundaries(),
        "safety_metadata": safety,
    }


def build_pgvector_extension_probe_payload(
    *,
    request_payload: dict[str, Any] | None = None,
    probe_executor: ProbeExecutor | None = None,
) -> dict[str, Any]:
    """Run one explicitly injected probe or return the default-off fallback."""

    request = (
        _plain_dict(request_payload)
        if isinstance(request_payload, dict)
        else build_pgvector_extension_probe_request_payload()
    )
    if not callable(probe_executor):
        return {
            "contract_version": CONTRACT_VERSION,
            "status": STATUS_NOT_CONFIGURED,
            "probe_type": "pgvector_extension_probe",
            "default_off": True,
            "probe_configured": False,
            "probe_executed": False,
            "extension_name": _clean_text(request.get("extension_name")) or "vector",
            "extension_available": False,
            "extension_installed": False,
            "available_version": "",
            "installed_version": "",
            "postgres_version": "",
            "requested_dimension": _optional_positive_int(
                request.get("requested_dimension")
            ),
            "supported_dimensions": [],
            "dimension_supported": None,
            "vector_type_available": False,
            "supported_index_methods": [],
            "probe_details": {},
            "error_type": "",
            "error_message": "",
            "provider_backed_automated_agents": 0,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "mutation_authorized_scoring_agents": 0,
            "mutation_authorized_ranking_agents": 0,
            "mutation_authorized_application_agents": 0,
            "evaluation_boundaries": _evaluation_boundaries(),
            "safety_metadata": pgvector_extension_probe_safety_metadata(),
        }

    try:
        executor_result = probe_executor(_snapshot(request))
        if not isinstance(executor_result, dict):
            raise TypeError("probe executor must return a dictionary")
        return normalize_pgvector_extension_probe_result_payload(
            executor_result,
            request_payload=request,
        )
    except Exception as exc:
        return {
            "contract_version": CONTRACT_VERSION,
            "status": STATUS_FAILED_NON_BLOCKING,
            "probe_type": "pgvector_extension_probe",
            "default_off": True,
            "probe_configured": True,
            "probe_executed": True,
            "extension_name": _clean_text(request.get("extension_name")) or "vector",
            "extension_available": False,
            "extension_installed": False,
            "available_version": "",
            "installed_version": "",
            "postgres_version": "",
            "requested_dimension": _optional_positive_int(
                request.get("requested_dimension")
            ),
            "supported_dimensions": [],
            "dimension_supported": None,
            "vector_type_available": False,
            "supported_index_methods": [],
            "probe_details": {},
            "error_type": exc.__class__.__name__,
            "error_message": _clean_text(exc),
            "provider_backed_automated_agents": 0,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "mutation_authorized_scoring_agents": 0,
            "mutation_authorized_ranking_agents": 0,
            "mutation_authorized_application_agents": 0,
            "evaluation_boundaries": _evaluation_boundaries(),
            "safety_metadata": pgvector_extension_probe_safety_metadata(),
        }

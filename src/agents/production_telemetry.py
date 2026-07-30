"""Bounded, default-off production execution telemetry normalization.

The adapter emits only source-proven execution metadata.  It owns no provider,
cache, graph, persistence, or business execution and constructs no external
resources.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import re
from typing import Any, Callable, Mapping

from src.utils.logging import get_logger


PRODUCTION_AGENT_TELEMETRY_FLAG = (
    "APPLYLENS_PRODUCTION_AGENT_TELEMETRY_ENABLED"
)
PRODUCTION_TELEMETRY_CONTRACT_VERSION = (
    "production-agent-telemetry-v1"
)
MAX_TELEMETRY_PAYLOAD_BYTES = 16_384
MAX_TELEMETRY_TEXT_LENGTH = 256
MAX_TELEMETRY_LATENCY_MS = 300_000

WORKLOAD_CLASSIFICATIONS = frozenset({"deterministic", "llm"})
EXECUTION_ROUTES = frozenset(
    {
        "direct",
        "graph",
        "durable_first_execution",
        "durable_replay",
    }
)
EXECUTION_STATUSES = frozenset(
    {"pending", "running", "completed", "failed"}
)

_OPTIONAL_TEXT_FIELDS = (
    "requested_provider",
    "requested_model",
    "resolved_provider",
    "resolved_model",
    "prompt_version",
)
_OPTIONAL_COUNT_FIELDS = (
    "input_token_count",
    "output_token_count",
    "total_token_count",
)
_PROHIBITED_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "connection_string",
    "database_url",
    "raw_prompt",
    "raw_response",
    "resume_text",
    "job_description",
    "generated_content",
    "provider_response",
)
_PROHIBITED_TEXT_PATTERNS = (
    "postgres://",
    "postgresql://",
    "authorization: bearer",
    "api_key=",
    "apikey=",
    "connection_string=",
)
_logger = get_logger("production_agent_telemetry")

TelemetrySink = Callable[[Mapping[str, Any]], Any]


class ProductionTelemetryContractError(ValueError):
    """Bounded contract rejection that never contains source values."""


def telemetry_enabled(value: Any) -> bool:
    return str(value or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _timestamp(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ProductionTelemetryContractError(
            "telemetry_timestamp_invalid"
        ) from None
    if parsed.tzinfo is None:
        raise ProductionTelemetryContractError(
            "telemetry_timestamp_timezone_required"
        )
    return parsed.astimezone(timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )


def _safe_text(
    value: Any,
    *,
    field: str,
    required: bool = False,
) -> str:
    text = " ".join(str(value or "").split())
    if required and not text:
        raise ProductionTelemetryContractError(
            f"telemetry_{field}_required"
        )
    if len(text) > MAX_TELEMETRY_TEXT_LENGTH:
        raise ProductionTelemetryContractError(
            f"telemetry_{field}_too_large"
        )
    lowered = text.lower()
    if any(pattern in lowered for pattern in _PROHIBITED_TEXT_PATTERNS):
        raise ProductionTelemetryContractError(
            f"telemetry_{field}_unsafe"
        )
    return text


def _bounded_count(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise ProductionTelemetryContractError(
            f"telemetry_{field}_invalid"
        )
    try:
        count = int(value)
    except (TypeError, ValueError):
        raise ProductionTelemetryContractError(
            f"telemetry_{field}_invalid"
        ) from None
    if count < 0 or count > 1_000_000_000:
        raise ProductionTelemetryContractError(
            f"telemetry_{field}_invalid"
        )
    return count


def _bounded_latency(value: Any) -> int:
    try:
        latency = int(value or 0)
    except (TypeError, ValueError):
        latency = 0
    return max(0, min(latency, MAX_TELEMETRY_LATENCY_MS))


def _reject_prohibited_source(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = re.sub(
                r"[^a-z0-9]+",
                "_",
                str(key or "").strip().lower(),
            ).strip("_")
            if any(
                fragment in normalized_key
                for fragment in _PROHIBITED_KEY_FRAGMENTS
            ):
                raise ProductionTelemetryContractError(
                    "telemetry_source_prohibited_field"
                )
            _reject_prohibited_source(
                nested,
                path=f"{path}.{normalized_key}",
            )
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for nested in value:
            _reject_prohibited_source(nested, path=path)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(pattern in lowered for pattern in _PROHIBITED_TEXT_PATTERNS):
            raise ProductionTelemetryContractError(
                "telemetry_source_unsafe_value"
            )


def _execution_route(metadata: Mapping[str, Any]) -> str:
    durable_status = str(metadata.get("durable_status") or "").strip()
    if durable_status == "completed_replay":
        return "durable_replay"
    if durable_status:
        return "durable_first_execution"
    if str(metadata.get("execution_mode") or "").strip() == "langgraph":
        return "graph"
    return "direct"


def _invocation_count(metadata: Mapping[str, Any]) -> int:
    if "invocation_count" in metadata:
        return _bounded_count(
            metadata["invocation_count"],
            field="invocation_count",
        )
    if "node_invocation_count" in metadata:
        return _bounded_count(
            metadata["node_invocation_count"],
            field="invocation_count",
        )
    return 0


def _optional_count(
    event: dict[str, Any],
    *,
    event_field: str,
    source: Mapping[str, Any],
    source_field: str,
) -> None:
    if source_field in source and source.get(source_field) is not None:
        event[event_field] = _bounded_count(
            source[source_field],
            field=event_field,
        )


def _optional_exact_cost(
    event: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    if "exact_cost" not in source or source.get("exact_cost") is None:
        return
    try:
        cost = Decimal(str(source["exact_cost"]))
    except (InvalidOperation, ValueError):
        raise ProductionTelemetryContractError(
            "telemetry_exact_cost_invalid"
        ) from None
    if not cost.is_finite() or cost < 0:
        raise ProductionTelemetryContractError(
            "telemetry_exact_cost_invalid"
        )
    currency = _safe_text(
        source.get("cost_currency"),
        field="cost_currency",
        required=True,
    )
    event["exact_cost"] = format(cost, "f")
    event["cost_currency"] = currency


def _authority(
    metadata: Mapping[str, Any],
    *names: str,
) -> bool:
    value = next(
        (metadata[name] for name in names if name in metadata),
        False,
    )
    if value is not False:
        raise ProductionTelemetryContractError(
            "telemetry_authority_must_be_false"
        )
    return False


def build_production_telemetry_event(
    *,
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    node_key: str,
    workload_classification: str,
    execution_metadata: Mapping[str, Any],
    source_metadata: Mapping[str, Any] | None = None,
    input_count: int | None = None,
    output_count: int | None = None,
    timestamp: str = "",
) -> dict[str, Any]:
    if not isinstance(execution_metadata, Mapping):
        raise ProductionTelemetryContractError(
            "telemetry_execution_metadata_required"
        )
    safe_source = source_metadata or {}
    if not isinstance(safe_source, Mapping):
        raise ProductionTelemetryContractError(
            "telemetry_source_metadata_invalid"
        )
    _reject_prohibited_source(safe_source, path="source_metadata")

    workload = str(workload_classification or "").strip().lower()
    if workload not in WORKLOAD_CLASSIFICATIONS:
        raise ProductionTelemetryContractError(
            "telemetry_workload_classification_invalid"
        )
    route = _execution_route(execution_metadata)
    if route not in EXECUTION_ROUTES:
        raise ProductionTelemetryContractError(
            "telemetry_execution_route_invalid"
        )
    status = _safe_text(
        execution_metadata.get("status"),
        field="status",
        required=True,
    )
    if status not in EXECUTION_STATUSES:
        raise ProductionTelemetryContractError(
            "telemetry_status_invalid"
        )

    event: dict[str, Any] = {
        "telemetry_contract_version": (
            PRODUCTION_TELEMETRY_CONTRACT_VERSION
        ),
        "timestamp": _timestamp(timestamp),
        "pipeline_run_id": _safe_text(
            pipeline_run_id,
            field="pipeline_run_id",
            required=True,
        ),
        "owner_user_id": _safe_text(
            owner_user_id,
            field="owner_user_id",
            required=True,
        ),
        "context_id": _safe_text(
            context_id,
            field="context_id",
            required=True,
        ),
        "graph_version": _safe_text(
            execution_metadata.get("graph_version"),
            field="graph_version",
            required=True,
        ),
        "state_version": _safe_text(
            execution_metadata.get("state_version"),
            field="state_version",
            required=True,
        ),
        "node_key": _safe_text(
            node_key,
            field="node_key",
            required=True,
        ),
        "execution_mode": _safe_text(
            execution_metadata.get("execution_mode"),
            field="execution_mode",
            required=True,
        ),
        "workload_classification": workload,
        "execution_route": route,
        "status": status,
        "failure_classification": _safe_text(
            execution_metadata.get("failure_classification"),
            field="failure_classification",
        ),
        "invocation_count": _invocation_count(execution_metadata),
        "latency_ms": _bounded_latency(
            execution_metadata.get("node_latency_ms")
        ),
        "mutation_authority": _authority(
            execution_metadata,
            "mutation_authority",
            "persistent_mutation_authority",
        ),
        "application_authority": _authority(
            execution_metadata,
            "application_authority",
        ),
        "ats_authority": _authority(
            execution_metadata,
            "ats_authority",
        ),
    }
    if input_count is not None:
        event["input_count"] = _bounded_count(
            input_count,
            field="input_count",
        )
    if output_count is not None:
        event["output_count"] = _bounded_count(
            output_count,
            field="output_count",
        )

    if workload == "llm":
        if "cache_hit" in safe_source:
            event["cache_status"] = (
                "hit" if safe_source.get("cache_hit") is True else "miss"
            )
        for field in _OPTIONAL_TEXT_FIELDS:
            text = _safe_text(
                safe_source.get(field),
                field=field,
            )
            if text:
                event[field] = text
        if "retry_used" in safe_source:
            event["retry_used"] = safe_source.get("retry_used") is True
        if "fallback_used" in safe_source:
            event["fallback_used"] = (
                safe_source.get("fallback_used") is True
            )
        for field in _OPTIONAL_COUNT_FIELDS:
            _optional_count(
                event,
                event_field=field,
                source=safe_source,
                source_field=field,
            )
        _optional_exact_cost(event, safe_source)

    for event_field, source_field in (
        ("graph_invocation_count", "graph_invocation_count"),
        (
            "owner_invocation_count",
            "tailoring_owner_invocation_count",
        ),
        ("provider_invocation_count", "provider_call_count"),
        ("cache_write_count", "cache_write_count"),
    ):
        _optional_count(
            event,
            event_field=event_field,
            source=execution_metadata,
            source_field=source_field,
        )
    durable_status = _safe_text(
        execution_metadata.get("durable_status"),
        field="durable_status",
    )
    if durable_status:
        event["durable_classification"] = durable_status

    serialized = json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    if len(serialized.encode("utf-8")) > MAX_TELEMETRY_PAYLOAD_BYTES:
        raise ProductionTelemetryContractError(
            "telemetry_payload_too_large"
        )
    return deepcopy(event)


def _structured_log_sink(event: Mapping[str, Any]) -> None:
    _logger.info(
        "production_agent_telemetry %s",
        json.dumps(
            dict(event),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ),
    )


def emit_production_telemetry(
    *,
    sink: TelemetrySink | None = None,
    **event_kwargs: Any,
) -> dict[str, Any]:
    try:
        event = build_production_telemetry_event(**event_kwargs)
    except ProductionTelemetryContractError as exc:
        _logger.warning(
            "production_agent_telemetry_rejected reason=%s",
            str(exc),
        )
        return {
            "emitted": False,
            "failure_classification": "contract_rejected",
            "reason_code": str(exc),
        }

    active_sink = sink or _structured_log_sink
    try:
        active_sink(deepcopy(event))
    except Exception:
        _logger.warning(
            "production_agent_telemetry_sink_failed "
            "classification=sink_failure"
        )
        return {
            "emitted": False,
            "failure_classification": "sink_failure",
            "reason_code": "telemetry_sink_failed",
        }
    return {
        "emitted": True,
        "failure_classification": "",
        "reason_code": "",
        "event": deepcopy(event),
    }


__all__ = [
    "EXECUTION_ROUTES",
    "MAX_TELEMETRY_LATENCY_MS",
    "MAX_TELEMETRY_PAYLOAD_BYTES",
    "PRODUCTION_AGENT_TELEMETRY_FLAG",
    "PRODUCTION_TELEMETRY_CONTRACT_VERSION",
    "ProductionTelemetryContractError",
    "TelemetrySink",
    "WORKLOAD_CLASSIFICATIONS",
    "build_production_telemetry_event",
    "emit_production_telemetry",
    "telemetry_enabled",
]

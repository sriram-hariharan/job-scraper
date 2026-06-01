from __future__ import annotations

from typing import Any, Dict, Iterable, List


METADATA_VERSION = "llmops_metadata_v1"

LLMOPS_METADATA_KEYS = [
    "metadata_version",
    "model_provider",
    "model_name",
    "prompt_version",
    "agent_name",
    "agent_version",
    "input_token_count",
    "output_token_count",
    "total_token_count",
    "estimated_cost",
    "cost_currency",
    "latency_ms",
    "retry_count",
    "fallback_used",
    "schema_validation_status",
    "error_type",
    "cost_reason",
]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _int_value(value: Any) -> int:
    try:
        return max(0, int(float(str(value or "0").strip() or "0")))
    except (TypeError, ValueError):
        return 0


def _float_value(value: Any) -> float:
    try:
        return max(0.0, float(str(value or "0").strip() or "0"))
    except (TypeError, ValueError):
        return 0.0


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _clean_text(value).lower() in {"1", "true", "yes", "on"}


def build_llmops_metadata(
    *,
    model_provider: str = "",
    model_name: str = "",
    prompt_version: str = "",
    agent_name: str = "",
    agent_version: str = "",
    input_token_count: Any = 0,
    output_token_count: Any = 0,
    total_token_count: Any = None,
    estimated_cost: Any = 0,
    cost_currency: str = "",
    latency_ms: Any = None,
    retry_count: Any = 0,
    fallback_used: Any = False,
    schema_validation_status: str = "",
    error_type: str = "",
    cost_reason: str = "no_rate_table_configured",
    metadata_version: str = METADATA_VERSION,
) -> Dict[str, Any]:
    input_tokens = _int_value(input_token_count)
    output_tokens = _int_value(output_token_count)
    total_tokens = _int_value(total_token_count)
    if total_token_count is None:
        total_tokens = input_tokens + output_tokens

    cost = _float_value(estimated_cost)
    currency = _clean_text(cost_currency)
    if cost <= 0 and not currency:
        currency = ""

    return {
        "metadata_version": _clean_text(metadata_version) or METADATA_VERSION,
        "model_provider": _clean_text(model_provider),
        "model_name": _clean_text(model_name),
        "prompt_version": _clean_text(prompt_version),
        "agent_name": _clean_text(agent_name),
        "agent_version": _clean_text(agent_version),
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "total_token_count": total_tokens,
        "estimated_cost": cost,
        "cost_currency": currency,
        "latency_ms": None if latency_ms is None or _clean_text(latency_ms) == "" else _int_value(latency_ms),
        "retry_count": _int_value(retry_count),
        "fallback_used": _bool_value(fallback_used),
        "schema_validation_status": _clean_text(schema_validation_status),
        "error_type": _clean_text(error_type),
        "cost_reason": _clean_text(cost_reason) if cost <= 0 else "",
    }


def token_usage_json_from_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "metadata_version": metadata.get("metadata_version", METADATA_VERSION),
        "input_token_count": _int_value(metadata.get("input_token_count")),
        "output_token_count": _int_value(metadata.get("output_token_count")),
        "total_token_count": _int_value(metadata.get("total_token_count")),
    }


def cost_json_from_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "metadata_version": metadata.get("metadata_version", METADATA_VERSION),
        "estimated_cost": _float_value(metadata.get("estimated_cost")),
        "cost_currency": _clean_text(metadata.get("cost_currency")),
        "cost_reason": _clean_text(metadata.get("cost_reason")),
    }


def merge_llmops_into_agent_step_kwargs(
    step_kwargs: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    merged = dict(step_kwargs or {})
    merged["model_provider"] = _clean_text(metadata.get("model_provider"))
    merged["model_name"] = _clean_text(metadata.get("model_name"))
    merged["latency_ms"] = metadata.get("latency_ms")
    merged["token_usage_json"] = token_usage_json_from_metadata(metadata)
    merged["cost_json"] = cost_json_from_metadata(metadata)
    return merged


def _metadata_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return build_llmops_metadata()
    if all(key in row for key in ("input_token_count", "output_token_count", "total_token_count")):
        return build_llmops_metadata(**{key: row.get(key) for key in LLMOPS_METADATA_KEYS if key in row})
    token_usage = row.get("token_usage_json") if isinstance(row.get("token_usage_json"), dict) else {}
    cost = row.get("cost_json") if isinstance(row.get("cost_json"), dict) else {}
    return build_llmops_metadata(
        model_provider=row.get("model_provider", ""),
        model_name=row.get("model_name", ""),
        input_token_count=token_usage.get("input_token_count", token_usage.get("prompt_tokens", 0)),
        output_token_count=token_usage.get("output_token_count", token_usage.get("completion_tokens", 0)),
        total_token_count=token_usage.get("total_token_count", token_usage.get("total_tokens", None)),
        estimated_cost=cost.get("estimated_cost", cost.get("usd", 0)),
        cost_currency=cost.get("cost_currency", "USD" if cost.get("usd") else ""),
        cost_reason=cost.get("cost_reason", ""),
        latency_ms=row.get("latency_ms"),
    )


def summarize_llmops_metadata(rows_or_steps: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [row for row in rows_or_steps if isinstance(row, dict)]
    metadata_rows = [_metadata_from_row(row) for row in rows]
    provider_counts: Dict[str, int] = {}
    model_counts: Dict[str, int] = {}
    for metadata in metadata_rows:
        provider = _clean_text(metadata.get("model_provider")) or "<empty>"
        model = _clean_text(metadata.get("model_name")) or "<empty>"
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        model_counts[model] = model_counts.get(model, 0) + 1

    return {
        "metadata_version": METADATA_VERSION,
        "row_count": len(metadata_rows),
        "input_token_count": sum(_int_value(row.get("input_token_count")) for row in metadata_rows),
        "output_token_count": sum(_int_value(row.get("output_token_count")) for row in metadata_rows),
        "total_token_count": sum(_int_value(row.get("total_token_count")) for row in metadata_rows),
        "estimated_cost": round(sum(_float_value(row.get("estimated_cost")) for row in metadata_rows), 8),
        "fallback_used_count": sum(1 for row in metadata_rows if _bool_value(row.get("fallback_used"))),
        "error_count": sum(1 for row in metadata_rows if _clean_text(row.get("error_type"))),
        "provider_counts": dict(sorted(provider_counts.items())),
        "model_counts": dict(sorted(model_counts.items())),
    }


def llmops_schema_readiness_payload() -> Dict[str, Any]:
    sample = build_llmops_metadata()
    return {
        "metadata_version": METADATA_VERSION,
        "required_keys": list(LLMOPS_METADATA_KEYS),
        "required_keys_present": all(key in sample for key in LLMOPS_METADATA_KEYS),
    }

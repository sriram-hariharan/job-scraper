from __future__ import annotations

from copy import deepcopy
from typing import Any


CRITIC_EVALUATOR_RUBRIC_VERSION = "critic-evaluator-rubric-v1"


def build_empty_evaluator_result() -> dict[str, Any]:
    return {
        "evaluator_status": "not_evaluated",
        "evaluator_findings": [],
        "evaluator_warnings": [],
        "evaluator_recommendations": [],
        "requires_human_review": False,
        "deterministic_rubric_version": CRITIC_EVALUATOR_RUBRIC_VERSION,
    }


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> list[Any]:
    return deepcopy(value) if isinstance(value, list) else []


def _step_list(trace_payload: Any) -> list[dict[str, Any]]:
    if isinstance(trace_payload, list):
        return [_plain_dict(step) for step in trace_payload if isinstance(step, dict)]
    if not isinstance(trace_payload, dict):
        return []
    for key in ("agent_steps", "trace_steps", "steps"):
        value = trace_payload.get(key)
        if isinstance(value, list):
            return [_plain_dict(step) for step in value if isinstance(step, dict)]
    return []


def _step_index(step: dict[str, Any]) -> int | None:
    value = step.get("step_index")
    if value is None:
        value = step.get("agent_step_index")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _has_safety_metadata(step: dict[str, Any]) -> bool:
    if isinstance(step.get("safety_metadata"), dict):
        return True
    return any(key.startswith("did_") for key in step)


def _nested_dict(step: dict[str, Any], key: str) -> dict[str, Any]:
    direct = step.get(key)
    if isinstance(direct, dict):
        return deepcopy(direct)
    for container_key in ("output_summary", "output_json", "metadata"):
        container = step.get(container_key)
        if isinstance(container, dict) and isinstance(container.get(key), dict):
            return deepcopy(container[key])
    return {}


def _validation_json(step: dict[str, Any]) -> dict[str, Any]:
    return _nested_dict(step, "validation_json")


def _separation(step: dict[str, Any]) -> dict[str, Any]:
    return _nested_dict(step, "separation")


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _ordering_is_valid(indexes: list[int | None]) -> bool:
    resolved = [index for index in indexes if index is not None]
    return resolved == sorted(resolved)


def evaluate_agent_trace(trace_payload: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    snapshot = deepcopy(trace_payload)
    steps = _step_list(snapshot)
    findings: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not steps:
        findings.append("trace_completeness_empty_trace")
        warnings.append("agent_trace_has_no_steps")
        recommendations.append("provide_ordered_agent_steps")
    else:
        indexes = [_step_index(step) for step in steps]
        if any(index is None for index in indexes):
            warnings.append("agent_step_ordering_missing_index")
            recommendations.append("add_step_index_to_each_agent_step")
        elif not _ordering_is_valid(indexes):
            findings.append("agent_step_ordering_out_of_order")
            warnings.append("agent_steps_are_not_sorted")
            recommendations.append("sort_agent_steps_by_step_index")

        missing_safety = [
            str(index)
            for index, step in enumerate(steps)
            if not _has_safety_metadata(step)
        ]
        if missing_safety:
            findings.append("safety_metadata_missing")
            warnings.append("one_or_more_steps_missing_safety_metadata")
            recommendations.append("include_safety_metadata_for_each_step")

        missing_validation = []
        invalid_validation = []
        for index, step in enumerate(steps):
            validation = _validation_json(step)
            if not validation:
                missing_validation.append(str(index))
            elif validation.get("is_valid") is not True:
                invalid_validation.append(str(index))
        if missing_validation:
            findings.append("validation_json_missing")
            warnings.append("one_or_more_steps_missing_validation_json")
            recommendations.append("include_validation_json_for_each_step")
        if invalid_validation:
            findings.append("validation_json_invalid")
            warnings.append("one_or_more_steps_have_invalid_validation_json")
            recommendations.append("review_invalid_validation_json")

        separations = [_separation(step) for step in steps]
        if not any(separations):
            warnings.append("separation_metadata_missing")
            recommendations.append("include_separation_metadata_for_agent_boundaries")
        else:
            separation_keys = {
                key
                for separation in separations
                for key in separation
            }
            for required_key in (
                "prefilter_relevance",
                "llm_evaluation",
                "final_application_scoring",
            ):
                if required_key not in separation_keys:
                    _append_once(warnings, f"{required_key}_separation_missing")
                    _append_once(
                        recommendations,
                        "confirm_prefilter_llm_and_final_scoring_boundaries",
                    )

    requires_human_review = bool(findings or warnings)
    if not recommendations:
        recommendations.append("no_follow_up_required")

    return {
        "evaluator_status": (
            "needs_human_review" if requires_human_review else "passed"
        ),
        "evaluator_findings": findings,
        "evaluator_warnings": warnings,
        "evaluator_recommendations": recommendations,
        "requires_human_review": requires_human_review,
        "deterministic_rubric_version": CRITIC_EVALUATOR_RUBRIC_VERSION,
    }

# Deterministic rubric labels for trace-only evaluator checks.
# These labels are intentionally static and do not trigger runtime side effects.
_CRITIC_EVALUATOR_RUBRIC_LABELS = (
    "trace completeness",
    "agent step ordering",
    "safety metadata completeness",
    "validation_json consistency",
    "prefilter relevance",
    "LLM evaluation",
    "final application scoring",
)

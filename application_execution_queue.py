import argparse
import csv
import os
from pathlib import Path
from typing import Any, Dict, List

from src.agents.job_prioritization_agent import (
    record_job_prioritization_agent_trace,
    render_job_prioritization_recommendation_rows,
    write_job_prioritization_artifacts,
)
from src.agents.operator_review_agent import (
    record_operator_review_agent_trace,
    write_operator_review_artifacts,
)
from src.agents.tailoring_decision_agent import (
    record_tailoring_decision_agent_trace,
    render_tailoring_decision_rows,
    write_tailoring_decision_artifacts,
)
from src.config.settings import APPLICATION_EXECUTION_QUEUE_POLICY
from src.pipeline.resume_selection_credibility import (
    CREDIBILITY_COLUMNS,
    compute_resume_selection_credibility,
    parse_bool as parse_credibility_bool,
)

ACTION_RANK_POLICY = APPLICATION_EXECUTION_QUEUE_POLICY["action_rank"]
TIE_REVIEW_RANK_POLICY = APPLICATION_EXECUTION_QUEUE_POLICY["tie_review_rank"]
QUEUE_SAFETY_GATE_ENABLED = True

_QUEUE_APP_SERVICE_PAYLOAD_NOT_PROVIDED = object()
_QUEUE_APP_SERVICE_REQUIRED_GATE_FIELDS = {
    "app_service_safety_gate_enabled",
    "app_service_safety_gate_passed",
    "app_service_safety_gate_status",
    "blocked_by_app_service_safety_gate",
}
_QUEUE_WORKFLOW_RUNNER_REQUIRED_GATE_FIELDS = {
    "fixture_validation",
    "fixture_validation_gate_enabled",
    "fixture_validation_gate_passed",
    "fixture_validation_gate_status",
    "blocked_by_fixture_validation_gate",
    "executable_adapter_count",
    "allow_agent_execution",
    "did_execute_count",
    "did_execute_live",
    "did_mutate_production",
    "did_write_db",
}


def _queue_safety_gate_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def queue_safety_gate_payload(
    app_service_safety_gate_output: Any = _QUEUE_APP_SERVICE_PAYLOAD_NOT_PROVIDED,
) -> Dict[str, Any]:
    """Return a queue-facing safety gate payload without executing queued work."""
    if app_service_safety_gate_output is _QUEUE_APP_SERVICE_PAYLOAD_NOT_PROVIDED:
        from src.app import services as app_services

        app_service_safety_gate_output = (
            app_services.app_service_agentic_workflow_safety_gate_payload()
        )

    result: Dict[str, Any] = {}
    reason_codes: List[str] = []
    if not isinstance(app_service_safety_gate_output, dict):
        reason_codes.append("missing_app_service_safety_gate_output")
    else:
        result = dict(app_service_safety_gate_output)

        missing_app_service_fields = sorted(
            field
            for field in _QUEUE_APP_SERVICE_REQUIRED_GATE_FIELDS
            if field not in result
        )
        if missing_app_service_fields:
            reason_codes.append("missing_app_service_safety_gate_fields")
            reason_codes.extend(
                f"missing_app_service_safety_gate_field:{field}"
                for field in missing_app_service_fields
            )

        missing_workflow_runner_fields = sorted(
            field
            for field in _QUEUE_WORKFLOW_RUNNER_REQUIRED_GATE_FIELDS
            if field not in result
        )
        if missing_workflow_runner_fields:
            reason_codes.append("missing_workflow_runner_gate_fields")
            reason_codes.extend(
                f"missing_workflow_runner_gate_field:{field}"
                for field in missing_workflow_runner_fields
            )

        if result.get("blocked_by_app_service_safety_gate") is True:
            reason_codes.append("app_service_safety_gate_blocked")
        if result.get("app_service_safety_gate_passed") is False:
            reason_codes.append("app_service_safety_gate_not_passed")
        if (
            "app_service_safety_gate_status" in result
            and _normalize_text(result.get("app_service_safety_gate_status")) != "passed"
        ):
            reason_codes.append("app_service_safety_gate_status_not_passed")

        fixture_validation = result.get("fixture_validation")
        if not isinstance(fixture_validation, dict):
            reason_codes.append("missing_fixture_validation")
        else:
            if fixture_validation.get("fixture_validation_passed") is not True:
                reason_codes.append("fixture_validation_failed")
            if (
                _normalize_text(fixture_validation.get("fixture_validation_status"))
                != "passed"
            ):
                reason_codes.append("fixture_validation_status_not_passed")

        if result.get("blocked_by_fixture_validation_gate") is True:
            reason_codes.append("workflow_runner_fixture_validation_gate_blocked")
        if result.get("fixture_validation_gate_passed") is False:
            reason_codes.append("workflow_runner_fixture_validation_gate_not_passed")
        if (
            "fixture_validation_gate_status" in result
            and _normalize_text(result.get("fixture_validation_gate_status")) != "passed"
        ):
            reason_codes.append(
                "workflow_runner_fixture_validation_gate_status_not_passed"
            )

        if _queue_safety_gate_int(result.get("executable_adapter_count")) > 0:
            reason_codes.append("executable_adapter_count_nonzero")
        if result.get("allow_agent_execution") is True:
            reason_codes.append("allow_agent_execution_true")
        if _queue_safety_gate_int(result.get("did_execute_count")) != 0:
            reason_codes.append("did_execute_count_nonzero")
        if result.get("did_execute_live") is True:
            reason_codes.append("did_execute_live_true")
        if result.get("did_mutate_production") is True:
            reason_codes.append("did_mutate_production_true")
        if result.get("did_write_db") is True:
            reason_codes.append("did_write_db_true")

    reason_codes = sorted(set(reason_codes))
    blocked = bool(reason_codes)
    result.update(
        {
            "queue_safety_gate_enabled": QUEUE_SAFETY_GATE_ENABLED,
            "queue_safety_gate_passed": not blocked,
            "queue_safety_gate_status": "failed" if blocked else "passed",
            "queue_safety_gate_reason_codes": reason_codes,
            "blocked_by_queue_safety_gate": blocked,
        }
    )
    if blocked:
        result["did_execute_count"] = 0
        result["did_execute_live"] = False
        result["did_mutate_production"] = False
        result["did_write_db"] = False

    return result

def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _count_missing_requirements(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    return len([part for part in text.split("|") if part.strip()])


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split()).strip()

def _variant_review_required(row: dict) -> bool:
    raw = str(row.get("variant_review_required", "") or "").strip()
    if raw:
        return _parse_bool(raw)

    if _parse_bool(row.get("requires_manual_review", "false")):
        return True

    selection_signal = str(row.get("selection_signal", "") or "").strip()
    return selection_signal in {"effective_tie", "manual_review_close_call"} or _parse_bool(
        row.get("is_tie", "false")
    )


def _resolved_resume_source(row: dict) -> str:
    return str(row.get("resolved_resume_source", "") or "").strip()


def _resolved_selection_status(row: dict) -> str:
    return str(row.get("resolved_selection_status", "") or "").strip()


def _action_rank(action: str) -> int:
    return int(ACTION_RANK_POLICY.get(action, ACTION_RANK_POLICY["__default__"]))


def _tie_review_rank(row: dict) -> int:
    action = row.get("action", "")
    variant_review_required = _variant_review_required(row)

    if action == "APPLY_REVIEW_VARIANTS":
        return int(TIE_REVIEW_RANK_POLICY["apply_review_variants"])
    if action == "MAYBE_TAILOR" and variant_review_required:
        return int(TIE_REVIEW_RANK_POLICY["maybe_tailor_variant_review"])
    return int(TIE_REVIEW_RANK_POLICY["default"])


def _needs_variant_review(row: dict) -> str:
    action = row.get("action", "")
    variant_review_required = _variant_review_required(row)

    if action == "APPLY_REVIEW_VARIANTS" and variant_review_required:
        return "True"
    if action == "MAYBE_TAILOR" and variant_review_required:
        return "True"
    return "False"


def _queue_priority_reason(row: dict) -> str:
    credibility = compute_resume_selection_credibility(row)
    if parse_credibility_bool(credibility["fallback_only_no_deterministic_match"]):
        return "Fallback resume suggestion only; deterministic scorer found no credible match."
    if credibility["packet_generation_block_reason"] == "deterministic_score_below_credible_threshold":
        return "Deterministic resume score is below the credible threshold; keep visible for review."

    action = row.get("action", "")
    variant_review_required = _variant_review_required(row)
    selection_signal = str(row.get("selection_signal", "")).strip()
    resolved_resume_source = _resolved_resume_source(row)
    resolved_selection_status = _resolved_selection_status(row)

    if action == "APPLY":
        if resolved_resume_source and resolved_resume_source != "deterministic_winner":
            return f"Highest-priority apply candidate resolved via {resolved_resume_source}."
        return "Highest-priority direct apply candidate."

    if action == "APPLY_REVIEW_VARIANTS":
        if variant_review_required:
            return (
                f"Strong apply candidate, but resume choice is still unresolved "
                f"(status={resolved_selection_status or 'unresolved'}, "
                f"source={resolved_resume_source or selection_signal or 'selector'})."
            )
        return "Strong apply candidate that still requires operator review."

    if action == "MAYBE_TAILOR":
        if variant_review_required:
            return (
                f"Tailor candidate with unresolved variant choice "
                f"(status={resolved_selection_status or 'unresolved'}, "
                f"source={resolved_resume_source or selection_signal or 'selector'})."
            )
        if resolved_resume_source and resolved_resume_source != "deterministic_winner":
            return f"Tailor candidate resolved via {resolved_resume_source}."
        return "Tailor before applying."

    return "Low-priority hold."

def _load_rows(csv_path: Path) -> List[dict]:
    if not csv_path.exists():
        raise RuntimeError(f"Missing CSV: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"CSV is empty: {csv_path}")

    return rows


def _job_key(row: dict) -> str:
    return _normalize_text(
        row.get("job_id")
        or row.get("job_doc_id")
        or "|".join(
            [
                row.get("job_company", "") or row.get("company", ""),
                row.get("job_title", "") or row.get("title", ""),
                row.get("job_location", ""),
            ]
        )
    )


def _with_priority_overlay(rows: List[dict]) -> List[dict]:
    priority_by_key = {
        _job_key(row): row
        for row in render_job_prioritization_recommendation_rows(rows)
        if _job_key(row)
    }
    merged_rows: List[dict] = []
    for row in rows:
        priority_row = priority_by_key.get(_job_key(row), {})
        merged_rows.append(
            {
                **row,
                "job_id": row.get("job_id", "") or row.get("job_doc_id", ""),
                "company": row.get("company", "") or row.get("job_company", ""),
                "title": row.get("title", "") or row.get("job_title", ""),
                "source": row.get("source", ""),
                "existing_action": row.get("existing_action", "") or row.get("action", ""),
                "advisory_priority": priority_row.get("advisory_priority", row.get("advisory_priority", "")),
                "advisory_reason_codes": priority_row.get("advisory_reason_codes", row.get("advisory_reason_codes", "")),
                "source_recommendation": priority_row.get("source_recommendation", row.get("source_recommendation", "")),
                "critic_decision": priority_row.get("critic_decision", row.get("critic_decision", "")),
                "deterministic_winner_score": (
                    row.get("deterministic_winner_score", "")
                    or row.get("selector_winner_score", "")
                    or row.get("winner_score", "")
                    or row.get("resolved_score", "")
                ),
            }
        )
    return merged_rows


def _with_tailoring_decision_overlay(rows: List[dict]) -> List[dict]:
    tailoring_by_key = {
        _job_key(row): row
        for row in render_tailoring_decision_rows(rows)
        if _job_key(row)
    }
    merged_rows: List[dict] = []
    for row in rows:
        tailoring_row = tailoring_by_key.get(_job_key(row), {})
        merged_rows.append(
            {
                **row,
                "tailoring_decision": tailoring_row.get("tailoring_decision", row.get("tailoring_decision", "")),
                "tailoring_reason_codes": tailoring_row.get("tailoring_reason_codes", row.get("tailoring_reason_codes", "")),
                "critic_decision": tailoring_row.get("critic_decision", row.get("critic_decision", "")),
                "source_recommendation": row.get("source_recommendation", ""),
            }
        )
    return merged_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a ranked application execution queue from the shortlist CSV."
    )
    parser.add_argument(
        "--input-csv",
        default="application_shortlist_by_job.csv",
        help="Path to the shortlist CSV.",
    )
    parser.add_argument(
        "--output-csv",
        default="application_execution_queue.csv",
        help="Path to write the execution queue CSV.",
    )
    parser.add_argument(
        "--top-k-console",
        type=int,
        default=15,
        help="How many queue rows to print to the console.",
    )
    parser.add_argument(
        "--priority-output-csv",
        default="",
        help="Optional path to write advisory job prioritization recommendations.",
    )
    parser.add_argument(
        "--priority-summary-json",
        default="",
        help="Optional path to write advisory job prioritization summary JSON.",
    )
    parser.add_argument(
        "--tailoring-decision-output-csv",
        default="",
        help="Optional path to write advisory tailoring decision recommendations.",
    )
    parser.add_argument(
        "--tailoring-decision-summary-json",
        default="",
        help="Optional path to write advisory tailoring decision summary JSON.",
    )
    parser.add_argument(
        "--operator-review-output-csv",
        default="",
        help="Optional path to write advisory operator review recommendations.",
    )
    parser.add_argument(
        "--operator-review-summary-json",
        default="",
        help="Optional path to write advisory operator review summary JSON.",
    )
    args = parser.parse_args()

    rows = _load_rows(Path(args.input_csv))

    queue_rows = []
    for row in rows:
        row = {**row, **compute_resume_selection_credibility(row)}
        missing_requirement_count = _count_missing_requirements(
            row.get("winner_missing_requirements", "")
        )
        queue_rows.append(
            {
                **row,
                "action_rank": str(_action_rank(row.get("action", ""))),
                "tie_review_rank": str(_tie_review_rank(row)),
                "needs_variant_review": _needs_variant_review(row),
                "missing_requirement_count": str(missing_requirement_count),
                "queue_priority_reason": _queue_priority_reason(row),
            }
        )

    queue_rows.sort(
        key=lambda row: (
            int(row["action_rank"]),
            int(row["tie_review_rank"]),
            -_parse_float(row.get("winner_score", "0")),
            int(row["missing_requirement_count"]),
            -_parse_float(row.get("score_gap", "0")),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )

    for idx, row in enumerate(queue_rows, start=1):
        row["queue_rank"] = str(idx)

    output_csv_path = Path(args.output_csv)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
    "queue_rank",
    "needs_variant_review",
    "missing_requirement_count",
    "queue_priority_reason",

    "job_doc_id",
    "job_company",
    "job_title",
    "job_location",
    "posted_at",
    "freshness_status",
    "ashby_timestamp_status",
    "action",
    "action_rationale",

    "winner_resume",
    "winner_score",
    "winner_bucket",
    "winner_top_dims",
    "winner_missing_requirements",
    "winner_matched_terms",
    "recommendation_summary",

    "resolved_resume",
    "resolved_score",
    "resolved_bucket",
    "resolved_top_dims",
    "resolved_missing_requirements",
    "resolved_matched_terms",
    "resolved_resume_source",
    "resolved_selection_status",
    "variant_review_required",
    "resolved_best_available_imperfect_match",
    *CREDIBILITY_COLUMNS,

    "selector_winner_resume",
    "selector_winner_score",
    "selector_winner_bucket",
    "selector_winner_top_dims",
    "selector_winner_missing_requirements",
    "selector_winner_matched_terms",
    "selector_recommendation_summary",

    "selection_signal",
    "requires_manual_review",
    "manual_review_gap_epsilon",
    "is_tie",
    "tie_epsilon",
    "runner_up_resume",
    "runner_up_score",
    "score_gap",
    "passed_prefilter",
    "filtered_out",

    "llm_adjudication_resume",
    "llm_adjudication_confidence",
    "llm_adjudication_reason",
    "llm_adjudication_status",
    "llm_adjudication_parse_ok",
    "llm_adjudication_provider",
    "llm_adjudication_model",
    "llm_adjudication_cache_hit",
    "llm_adjudication_differs_from_deterministic",
    "llm_adjudication_error_type",

    "llm_fallback_best_resume",
    "llm_fallback_best_score",
    "llm_fallback_backup_resume",
    "llm_fallback_backup_score",
    "llm_fallback_confidence",
    "llm_fallback_reason",
    "llm_fallback_status",
    "llm_fallback_parse_ok",
    "llm_fallback_provider",
    "llm_fallback_model",
    "llm_fallback_cache_hit",
    "llm_fallback_error_type",
]

    with output_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in queue_rows:
            output_row = {name: row.get(name, "") for name in fieldnames}
            writer.writerow(output_row)

    priority_artifact = None
    if str(args.priority_output_csv or "").strip():
        try:
            priority_artifact = write_job_prioritization_artifacts(
                rows=queue_rows,
                output_csv_path=args.priority_output_csv,
                summary_json_path=args.priority_summary_json or None,
                pipeline_run_id=(
                    os.getenv("JOB_APP_PIPELINE_RUN_ID", "").strip()
                    or os.getenv("JOB_STACK_USER_PIPELINE_RUN_ID", "").strip()
                ),
                owner_user_id=os.getenv("JOB_STACK_OWNER_USER_ID", "").strip(),
                source_artifact_path=str(output_csv_path),
            )
        except Exception as exc:
            print(f"Job prioritization advisory artifact skipped: {exc}")

    tailoring_decision_artifact = None
    tailoring_decision_rows = _with_priority_overlay(queue_rows)
    if str(args.tailoring_decision_output_csv or "").strip():
        try:
            tailoring_decision_artifact = write_tailoring_decision_artifacts(
                rows=tailoring_decision_rows,
                output_csv_path=args.tailoring_decision_output_csv,
                summary_json_path=args.tailoring_decision_summary_json or None,
                pipeline_run_id=(
                    os.getenv("JOB_APP_PIPELINE_RUN_ID", "").strip()
                    or os.getenv("JOB_STACK_USER_PIPELINE_RUN_ID", "").strip()
                ),
                owner_user_id=os.getenv("JOB_STACK_OWNER_USER_ID", "").strip(),
                source_artifact_path=str(output_csv_path),
            )
        except Exception as exc:
            print(f"Tailoring decision advisory artifact skipped: {exc}")

    operator_review_artifact = None
    operator_review_rows = _with_tailoring_decision_overlay(tailoring_decision_rows)
    if str(args.operator_review_output_csv or "").strip():
        try:
            operator_review_artifact = write_operator_review_artifacts(
                rows=operator_review_rows,
                output_csv_path=args.operator_review_output_csv,
                summary_json_path=args.operator_review_summary_json or None,
                pipeline_run_id=(
                    os.getenv("JOB_APP_PIPELINE_RUN_ID", "").strip()
                    or os.getenv("JOB_STACK_USER_PIPELINE_RUN_ID", "").strip()
                ),
                owner_user_id=os.getenv("JOB_STACK_OWNER_USER_ID", "").strip(),
                source_artifact_path=str(output_csv_path),
            )
        except Exception as exc:
            print(f"Operator review advisory artifact skipped: {exc}")

    trace_result = record_job_prioritization_agent_trace(
        rows=queue_rows,
        source_artifact_path=str(output_csv_path),
    )
    if trace_result.get("attempted") and not trace_result.get("recorded"):
        print(f"Job prioritization trace warning: {trace_result.get('warning') or trace_result.get('reason')}")

    tailoring_trace_result = record_tailoring_decision_agent_trace(
        rows=tailoring_decision_rows,
        source_artifact_path=str(output_csv_path),
    )
    if tailoring_trace_result.get("attempted") and not tailoring_trace_result.get("recorded"):
        print(
            "Tailoring decision trace warning: "
            f"{tailoring_trace_result.get('warning') or tailoring_trace_result.get('reason')}"
        )

    operator_review_trace_result = record_operator_review_agent_trace(
        rows=operator_review_rows,
        source_artifact_path=str(output_csv_path),
    )
    if operator_review_trace_result.get("attempted") and not operator_review_trace_result.get("recorded"):
        print(
            "Operator review trace warning: "
            f"{operator_review_trace_result.get('warning') or operator_review_trace_result.get('reason')}"
        )

    print("=" * 100)
    print("APPLICATION EXECUTION QUEUE")
    print("=" * 100)
    print(f"Input CSV : {args.input_csv}")
    print(f"Output CSV: {output_csv_path}")
    print(f"Jobs kept : {len(queue_rows)}")
    if priority_artifact:
        print(f"Priority advisory CSV: {priority_artifact['csv_path']}")
    if tailoring_decision_artifact:
        print(f"Tailoring decision advisory CSV: {tailoring_decision_artifact['csv_path']}")
    if operator_review_artifact:
        print(f"Operator review advisory CSV: {operator_review_artifact['csv_path']}")
    print()

    for row in queue_rows[:args.top_k_console]:
        print("-" * 100)
        print(
            f"#{row['queue_rank']} | {row['action']} | "
            f"{row['job_company']} | {row['job_title']}"
        )
        print(
            f"Winner: {row['winner_resume']} | "
            f"score={_parse_float(row['winner_score']):.3f} | "
            f"selection={row.get('selection_signal', '')} | "
            f"resolved_source={row.get('resolved_resume_source', '')} | "
            f"needs_variant_review={row['needs_variant_review']}"
        )
        print(
            f"Missing requirements: {row['missing_requirement_count']} | "
            f"gap={_parse_float(row['score_gap']):.3f}"
        )
        print(f"Priority reason: {row['queue_priority_reason']}")
        print()
    
        if row.get("llm_adjudication_resume", ""):
            print(
                f"LLM adjudication: {row['llm_adjudication_resume']} | "
                f"confidence={row.get('llm_adjudication_confidence', '')} | "
                f"differs_from_deterministic={row.get('llm_adjudication_differs_from_deterministic', '')}"
            )
            if row.get("llm_adjudication_reason", ""):
                print(f"LLM adjudication reason: {row['llm_adjudication_reason']}")
        

if __name__ == "__main__":
    main()

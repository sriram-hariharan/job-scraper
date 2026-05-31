from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import critic_agent, job_prioritization_agent, llmops, resume_match_agent, source_health_agent
from src.evaluation.metrics import bool_rate, safe_rate
from src.pipeline.resume_selection_credibility import parse_bool, parse_float


DEFAULT_FIXTURE_PATH = Path("tests/fixtures/agentic_benchmark/cases.json")
DEFAULT_OUTPUT_DIR = Path("outputs/evaluation")
THRESHOLD_METRIC_KEYS = [
    "source_health_recommendation_accuracy",
    "fallback_only_block_rate",
    "deterministic_match_allow_rate",
    "low_confidence_block_rate",
    "critic_unsupported_claim_rejection_rate",
    "critic_safe_suggestion_approval_rate",
    "critic_downgrade_rate",
    "job_priority_accuracy",
    "fallback_only_skip_rate",
    "high_score_apply_rate",
    "packet_block_skip_rate",
    "llmops_metadata_schema_present",
    "llmops_required_keys_present",
    "validation_pass_rate",
]
DEFAULT_THRESHOLDS = {
    "source_health_recommendation_accuracy": 1.0,
    "fallback_only_block_rate": 1.0,
    "deterministic_match_allow_rate": 1.0,
    "low_confidence_block_rate": 1.0,
    "critic_unsupported_claim_rejection_rate": 1.0,
    "critic_safe_suggestion_approval_rate": 1.0,
    "critic_downgrade_rate": 1.0,
    "job_priority_accuracy": 1.0,
    "fallback_only_skip_rate": 1.0,
    "high_score_apply_rate": 1.0,
    "packet_block_skip_rate": 1.0,
    "llmops_metadata_schema_present": 1.0,
    "llmops_required_keys_present": 1.0,
    "validation_pass_rate": 1.0,
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_benchmark_fixture(path: str | Path = DEFAULT_FIXTURE_PATH) -> Dict[str, Any]:
    fixture_path = Path(path)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Agentic benchmark fixture must be a JSON object.")
    payload.setdefault("cases", [])
    payload.setdefault("source_health_rows", [])
    payload.setdefault("selector_rows", [])
    payload.setdefault("critic_cases", [])
    payload.setdefault("job_priority_rows", [])
    return payload


def _selector_score(row: Dict[str, Any]) -> float:
    raw = _clean_text(row.get("selector_winner_score"))
    if raw:
        return parse_float(raw)
    return parse_float(row.get("winner_score"))


def _source_company_key(row: Dict[str, Any]) -> str:
    return f"{_clean_text(row.get('source')).lower()}:{_clean_text(row.get('company')).lower()}"


def evaluate_source_health_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = source_health_agent.render_source_health_recommendations(rows=rows)
    actual_by_key = {
        _source_company_key(row): _clean_text(row.get("recommendation"))
        for row in payload["output"].get("recommendations", [])
    }
    comparisons = []
    failed_case_ids: List[str] = []
    for row in rows:
        expected = _clean_text(row.get("expected_recommendation"))
        if not expected:
            continue
        case_id = _source_company_key(row)
        actual = actual_by_key.get(case_id, "")
        comparisons.append((expected, actual))
        if expected != actual:
            failed_case_ids.append(case_id)

    return {
        "payload": payload,
        "accuracy": safe_rate(
            sum(1 for expected, actual in comparisons if expected == actual),
            len(comparisons),
        ),
        "failed_case_ids": failed_case_ids,
        "validation_passed": payload["validation"].get("validation_status") == "passed",
    }


def evaluate_resume_selector_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    input_payload = resume_match_agent.build_resume_match_agent_input_payload(
        rows=rows,
        candidate_resume_names=sorted(
            {
                _clean_text(row.get("winner_resume") or row.get("resolved_resume"))
                for row in rows
                if _clean_text(row.get("winner_resume") or row.get("resolved_resume"))
            }
        ),
        pipeline_run_id="agentic_benchmark",
        owner_user_id="benchmark",
        source_artifact_path="tests/fixtures/agentic_benchmark/cases.json",
    )
    output_payload = resume_match_agent.build_resume_match_agent_output_payload(rows)
    validation_payload = resume_match_agent.build_resume_match_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
        rows=rows,
    )

    fallback_rows = [row for row in rows if parse_bool(row.get("fallback_only_no_deterministic_match"))]
    fallback_blocked = [not parse_bool(row.get("packet_generation_allowed")) for row in fallback_rows]

    deterministic_allowed_rows = [
        row
        for row in rows
        if parse_bool(row.get("deterministic_winner_available")) and _selector_score(row) >= 0.50
    ]
    deterministic_allowed = [
        parse_bool(row.get("packet_generation_allowed")) for row in deterministic_allowed_rows
    ]

    low_confidence_rows = [
        row
        for row in rows
        if parse_bool(row.get("deterministic_winner_available"))
        and 0.0 < _selector_score(row) < 0.50
    ]
    low_confidence_blocked = [
        not parse_bool(row.get("packet_generation_allowed"))
        and _clean_text(row.get("packet_generation_block_reason"))
        == "deterministic_score_below_credible_threshold"
        for row in low_confidence_rows
    ]

    failed_case_ids: List[str] = []
    for row in rows:
        expected = _clean_text(row.get("expected_credibility"))
        if expected == "allowed" and not parse_bool(row.get("packet_generation_allowed")):
            failed_case_ids.append(_clean_text(row.get("job_doc_id")))
        elif expected == "fallback_only_blocked" and parse_bool(row.get("packet_generation_allowed")):
            failed_case_ids.append(_clean_text(row.get("job_doc_id")))
        elif expected == "low_confidence_blocked" and not (
            not parse_bool(row.get("packet_generation_allowed"))
            and _clean_text(row.get("packet_generation_block_reason"))
            == "deterministic_score_below_credible_threshold"
        ):
            failed_case_ids.append(_clean_text(row.get("job_doc_id")))

    return {
        "input": input_payload,
        "output": output_payload,
        "validation": validation_payload,
        "fallback_only_block_rate": bool_rate(fallback_blocked),
        "deterministic_match_allow_rate": bool_rate(deterministic_allowed),
        "low_confidence_block_rate": bool_rate(low_confidence_blocked),
        "failed_case_ids": failed_case_ids,
        "validation_passed": validation_payload.get("validation_status") == "passed",
    }


def _critic_input_from_case(row: Dict[str, Any]) -> Dict[str, Any]:
    return critic_agent.build_critic_agent_input_payload(
        suggestion_id=_clean_text(row.get("suggestion_id")),
        original_resume_evidence=row.get("original_resume_evidence", []),
        jd_required_skills=row.get("jd_required_skills", []),
        jd_preferred_skills=row.get("jd_preferred_skills", []),
        proposed_text=_clean_text(row.get("proposed_text")),
        source_bullet=_clean_text(row.get("source_bullet")),
        projected_score_delta=row.get("projected_score_delta"),
        suggestion_type=_clean_text(row.get("suggestion_type")) or "patch_ready",
        pipeline_run_id="agentic_benchmark",
        owner_user_id="benchmark",
        source_artifact_path="tests/fixtures/agentic_benchmark/cases.json",
    )


def evaluate_critic_cases(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rendered = [critic_agent.render_critic_decision(_critic_input_from_case(row)) for row in rows]
    outputs = [item["output"] for item in rendered]
    validations = [item["validation"] for item in rendered]
    failed_case_ids: List[str] = []
    for row, output in zip(rows, outputs):
        expected = _clean_text(row.get("expected_decision"))
        actual = _clean_text(output.get("decision"))
        if expected and expected != actual:
            failed_case_ids.append(_clean_text(row.get("suggestion_id")))

    unsupported_claim_cases = [
        output
        for row, output in zip(rows, outputs)
        if _clean_text(row.get("expected_reason_code")) in {"unsupported_claim", "fake_tool_or_domain"}
    ]
    unsupported_claim_rejected = [
        output.get("decision") == "reject"
        and _clean_text(row.get("expected_reason_code")) in set(output.get("reason_codes", []) or [])
        for row, output in zip(rows, outputs)
        if _clean_text(row.get("expected_reason_code")) in {"unsupported_claim", "fake_tool_or_domain"}
    ]
    safe_suggestion_cases = [
        output
        for row, output in zip(rows, outputs)
        if _clean_text(row.get("expected_decision")) == "approve"
    ]
    safe_suggestion_approved = [
        output.get("decision") == "approve"
        for output in safe_suggestion_cases
    ]
    guidance_cases = [
        output
        for row, output in zip(rows, outputs)
        if _clean_text(row.get("expected_decision")) == "downgrade_to_guidance"
    ]
    guidance_downgraded = [
        output.get("decision") == "downgrade_to_guidance"
        for output in guidance_cases
    ]

    input_payloads = [_critic_input_from_case(row) for row in rows]
    summary = critic_agent.build_critic_agent_summary_payload(
        input_payloads=input_payloads,
        output_payloads=outputs,
        validation_payloads=validations,
    )
    return {
        "outputs": outputs,
        "validations": validations,
        "summary": summary,
        "critic_unsupported_claim_rejection_rate": bool_rate(unsupported_claim_rejected),
        "critic_safe_suggestion_approval_rate": bool_rate(safe_suggestion_approved),
        "critic_downgrade_rate": bool_rate(guidance_downgraded),
        "failed_case_ids": failed_case_ids,
        "validation_passed": all(
            validation.get("validation_status") == "passed" for validation in validations
        ),
        "case_counts": {
            "unsupported_claim_or_tool_cases": len(unsupported_claim_cases),
            "safe_suggestion_cases": len(safe_suggestion_cases),
            "guidance_cases": len(guidance_cases),
        },
    }


def evaluate_job_priority_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = job_prioritization_agent.render_job_prioritization_recommendations(
        rows=rows,
        pipeline_run_id="agentic_benchmark",
        owner_user_id="benchmark",
        source_artifact_path="tests/fixtures/agentic_benchmark/cases.json",
    )
    actual_by_id = {
        _clean_text(item.get("job_id")): _clean_text(item.get("advisory_priority"))
        for item in payload["output"].get("recommendations", []) or []
    }
    comparisons = []
    failed_case_ids: List[str] = []
    for row in rows:
        case_id = _clean_text(row.get("job_id") or row.get("job_doc_id"))
        expected = _clean_text(row.get("expected_priority"))
        if not expected:
            continue
        actual = actual_by_id.get(case_id, "")
        comparisons.append((expected, actual))
        if expected != actual:
            failed_case_ids.append(case_id)

    rendered_rows = list(payload["input"].get("rows", []) or [])
    recommendations = list(payload["output"].get("recommendations", []) or [])
    fallback_rows = [
        rec.get("advisory_priority") == "skip_for_now"
        for row, rec in zip(rendered_rows, recommendations)
        if parse_bool(row.get("fallback_only_no_deterministic_match"))
    ]
    high_score_rows = [
        rec.get("advisory_priority") == "apply_now"
        for row, rec in zip(rendered_rows, recommendations)
        if parse_bool(row.get("deterministic_winner_available"))
        and parse_float(row.get("deterministic_winner_score")) >= 0.70
        and parse_bool(row.get("packet_generation_allowed"))
        and _clean_text(row.get("source_recommendation")) not in {"monitor", "demote", "needs_timestamp_fix"}
        and _clean_text(row.get("critic_decision")).lower() != "reject"
    ]
    packet_block_rows = [
        rec.get("advisory_priority") != "apply_now"
        for row, rec in zip(rendered_rows, recommendations)
        if not parse_bool(row.get("packet_generation_allowed"))
    ]

    return {
        "payload": payload,
        "accuracy": safe_rate(
            sum(1 for expected, actual in comparisons if expected == actual),
            len(comparisons),
        ),
        "fallback_only_skip_rate": bool_rate(fallback_rows),
        "high_score_apply_rate": bool_rate(high_score_rows),
        "packet_block_skip_rate": bool_rate(packet_block_rows),
        "failed_case_ids": failed_case_ids,
        "validation_passed": payload["validation"].get("validation_status") in {"passed", "warning"},
    }


def run_benchmark(fixture_path: str | Path = DEFAULT_FIXTURE_PATH) -> Dict[str, Any]:
    fixture = load_benchmark_fixture(fixture_path)
    source_health = evaluate_source_health_rows(list(fixture.get("source_health_rows", []) or []))
    resume_match = evaluate_resume_selector_rows(list(fixture.get("selector_rows", []) or []))
    critic = evaluate_critic_cases(list(fixture.get("critic_cases", []) or []))
    job_priority = evaluate_job_priority_rows(list(fixture.get("job_priority_rows", []) or []))
    llmops_readiness = llmops.llmops_schema_readiness_payload()
    validation_passes = [
        bool(source_health["validation_passed"]),
        bool(resume_match["validation_passed"]),
        bool(critic["validation_passed"]),
        bool(job_priority["validation_passed"]),
    ]
    failed_case_ids = (
        list(source_health["failed_case_ids"])
        + list(resume_match["failed_case_ids"])
        + list(critic["failed_case_ids"])
        + list(job_priority["failed_case_ids"])
    )

    metrics = {
        "benchmark_case_count": len(fixture.get("cases", []) or []),
        "source_health_recommendation_accuracy": source_health["accuracy"],
        "fallback_only_block_rate": resume_match["fallback_only_block_rate"],
        "deterministic_match_allow_rate": resume_match["deterministic_match_allow_rate"],
        "low_confidence_block_rate": resume_match["low_confidence_block_rate"],
        "critic_unsupported_claim_rejection_rate": critic["critic_unsupported_claim_rejection_rate"],
        "critic_safe_suggestion_approval_rate": critic["critic_safe_suggestion_approval_rate"],
        "critic_downgrade_rate": critic["critic_downgrade_rate"],
        "job_priority_accuracy": job_priority["accuracy"],
        "fallback_only_skip_rate": job_priority["fallback_only_skip_rate"],
        "high_score_apply_rate": job_priority["high_score_apply_rate"],
        "packet_block_skip_rate": job_priority["packet_block_skip_rate"],
        "llmops_metadata_schema_present": 1.0 if llmops_readiness.get("metadata_version") else 0.0,
        "llmops_required_keys_present": 1.0 if llmops_readiness.get("required_keys_present") else 0.0,
        "validation_pass_rate": bool_rate(validation_passes),
        "failed_case_ids": failed_case_ids,
    }
    return {
        **metrics,
        "summary_json": {
            "benchmark_name": fixture.get("benchmark_name", ""),
            "generated_at_utc": _utc_now_iso(),
            "metrics": metrics,
            "source_health_summary": source_health["payload"]["summary"],
            "resume_match_summary": resume_match_agent.build_resume_match_agent_summary_payload(
                input_payload=resume_match["input"],
                output_payload=resume_match["output"],
                validation_payload=resume_match["validation"],
            ),
            "critic_summary": critic["summary"],
            "job_prioritization_summary": job_priority["payload"]["summary"],
            "llmops_observability_readiness": llmops_readiness,
        },
        "component_results": {
            "source_health": source_health,
            "resume_match": resume_match,
            "critic": critic,
            "job_prioritization": job_priority,
            "llmops": llmops_readiness,
        },
    }


def threshold_overrides_from_args(args: argparse.Namespace) -> Dict[str, float]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    overrides = {
        "source_health_recommendation_accuracy": args.min_source_health_recommendation_accuracy,
        "fallback_only_block_rate": args.min_fallback_only_block_rate,
        "deterministic_match_allow_rate": args.min_deterministic_match_allow_rate,
        "low_confidence_block_rate": args.min_low_confidence_block_rate,
        "critic_unsupported_claim_rejection_rate": args.min_critic_unsupported_claim_rejection_rate,
        "critic_safe_suggestion_approval_rate": args.min_critic_safe_suggestion_approval_rate,
        "critic_downgrade_rate": args.min_critic_downgrade_rate,
        "job_priority_accuracy": args.min_job_priority_accuracy,
        "fallback_only_skip_rate": args.min_fallback_only_skip_rate,
        "high_score_apply_rate": args.min_high_score_apply_rate,
        "packet_block_skip_rate": args.min_packet_block_skip_rate,
        "llmops_metadata_schema_present": args.min_llmops_metadata_schema_present,
        "llmops_required_keys_present": args.min_llmops_required_keys_present,
        "validation_pass_rate": args.min_validation_pass_rate,
    }
    for key, value in overrides.items():
        if value is not None:
            thresholds[key] = float(value)
    return thresholds


def evaluate_thresholds(
    result: Dict[str, Any],
    thresholds: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    metrics = result.get("summary_json", {}).get("metrics", {})
    expected = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    failures: List[Dict[str, Any]] = []
    for key in THRESHOLD_METRIC_KEYS:
        minimum = float(expected.get(key, DEFAULT_THRESHOLDS[key]))
        actual = float(metrics.get(key, 0.0) or 0.0)
        if actual < minimum:
            failures.append({"metric": key, "actual": actual, "minimum": minimum})
    return {
        "passed": not failures,
        "thresholds": {key: float(expected.get(key, DEFAULT_THRESHOLDS[key])) for key in THRESHOLD_METRIC_KEYS},
        "failures": failures,
    }


def render_results_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    metrics = result["summary_json"]["metrics"]
    return [
        {"metric": key, "value": json.dumps(value, sort_keys=True) if isinstance(value, list) else value}
        for key, value in metrics.items()
    ]


def render_markdown_report(result: Dict[str, Any]) -> str:
    metrics = result["summary_json"]["metrics"]
    threshold_result = result.get("thresholds") if isinstance(result.get("thresholds"), dict) else {}
    lines = [
        "# Agentic Benchmark Report",
        "",
        f"Benchmark: `{result['summary_json'].get('benchmark_name', '')}`",
        f"Generated at UTC: `{result['summary_json'].get('generated_at_utc', '')}`",
        "",
        "## Metrics",
        "",
    ]
    for key in [
        "benchmark_case_count",
        "source_health_recommendation_accuracy",
        "fallback_only_block_rate",
        "deterministic_match_allow_rate",
        "low_confidence_block_rate",
        "critic_unsupported_claim_rejection_rate",
        "critic_safe_suggestion_approval_rate",
        "critic_downgrade_rate",
        "job_priority_accuracy",
        "fallback_only_skip_rate",
        "high_score_apply_rate",
        "packet_block_skip_rate",
        "llmops_metadata_schema_present",
        "llmops_required_keys_present",
        "validation_pass_rate",
    ]:
        lines.append(f"- `{key}`: {metrics.get(key)}")
    lines.extend(["", "## Failed Case IDs", ""])
    failed = metrics.get("failed_case_ids") or []
    lines.append(", ".join(f"`{case_id}`" for case_id in failed) if failed else "None")
    lines.extend(["", "## Interpretation", ""])
    if threshold_result:
        if threshold_result.get("passed"):
            lines.append("All configured regression thresholds passed.")
        else:
            lines.append("One or more regression thresholds failed.")
            for failure in threshold_result.get("failures", []) or []:
                lines.append(
                    f"- `{failure.get('metric')}`: actual {failure.get('actual')} "
                    f"below minimum {failure.get('minimum')}"
                )
    else:
        lines.append("No regression threshold result was attached to this run.")
    lines.extend(["", "## Components", ""])
    lines.append("- Source Health Agent advisory benchmark")
    lines.append("- Resume Match Agent credibility benchmark")
    lines.append("- Critic Agent suggestion validation benchmark")
    lines.append("- Job Prioritization Agent advisory benchmark")
    lines.append("- LLMOps metadata schema readiness benchmark")
    return "\n".join(lines).strip() + "\n"


def write_benchmark_outputs(result: Dict[str, Any], output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> Dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary_path = root / "agentic_benchmark_summary.json"
    results_path = root / "agentic_benchmark_results.csv"
    report_path = root / "agentic_benchmark_report.md"

    summary_path.write_text(json.dumps(result["summary_json"], indent=2, sort_keys=True), encoding="utf-8")
    rows = render_results_rows(result)
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return {
        "summary_json": str(summary_path),
        "results_csv": str(results_path),
        "report_md": str(report_path),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the offline ApplyLens agentic benchmark.")
    parser.add_argument("--fixture-path", "--fixture", dest="fixture_path", default=str(DEFAULT_FIXTURE_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", "--write-outputs", dest="write_outputs", action="store_true")
    parser.add_argument("--no-write", dest="write_outputs", action="store_false")
    parser.set_defaults(write_outputs=False)
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--min-source-health-recommendation-accuracy", type=float, default=None)
    parser.add_argument("--min-fallback-only-block-rate", type=float, default=None)
    parser.add_argument("--min-deterministic-match-allow-rate", type=float, default=None)
    parser.add_argument("--min-low-confidence-block-rate", type=float, default=None)
    parser.add_argument("--min-critic-unsupported-claim-rejection-rate", type=float, default=None)
    parser.add_argument("--min-critic-safe-suggestion-approval-rate", type=float, default=None)
    parser.add_argument("--min-critic-downgrade-rate", type=float, default=None)
    parser.add_argument("--min-job-priority-accuracy", type=float, default=None)
    parser.add_argument("--min-fallback-only-skip-rate", type=float, default=None)
    parser.add_argument("--min-high-score-apply-rate", type=float, default=None)
    parser.add_argument("--min-packet-block-skip-rate", type=float, default=None)
    parser.add_argument("--min-llmops-metadata-schema-present", type=float, default=None)
    parser.add_argument("--min-llmops-required-keys-present", type=float, default=None)
    parser.add_argument("--min-validation-pass-rate", type=float, default=None)
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    result = run_benchmark(args.fixture_path)
    threshold_result = evaluate_thresholds(result, threshold_overrides_from_args(args))
    result["thresholds"] = threshold_result
    if args.write_outputs:
        result["output_files"] = write_benchmark_outputs(result, args.output_dir)
    if args.print_summary or not args.write_outputs:
        print(json.dumps(result["summary_json"], indent=2, sort_keys=True))
    if not threshold_result["passed"]:
        print(
            json.dumps(
                {"threshold_failures": threshold_result["failures"]},
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

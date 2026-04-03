import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def _line_hits(text: str, pattern: str, max_hits: int = 3) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    regex = re.compile(pattern)
    hits: List[Dict[str, Any]] = []

    for idx, line in enumerate(lines, start=1):
        if regex.search(line):
            hits.append(
                {
                    "line": idx,
                    "text": line.strip(),
                }
            )
            if len(hits) >= max_hits:
                break

    return hits


def _contains(text: str, needle: str) -> bool:
    return needle in text


def _check_required_substrings(
    *,
    name: str,
    path: Path,
    text: str,
    required: List[Tuple[str, str]],
) -> Dict[str, Any]:
    missing: List[Dict[str, str]] = []
    evidence: List[Dict[str, Any]] = []

    for label, needle in required:
        if _contains(text, needle):
            evidence.append(
                {
                    "label": label,
                    "needle": needle,
                    "hits": _line_hits(text, re.escape(needle)),
                }
            )
        else:
            missing.append({"label": label, "needle": needle})

    return {
        "name": name,
        "file": str(path),
        "ok": len(missing) == 0,
        "missing": missing,
        "evidence": evidence,
    }


def _check_forbidden_substrings(
    *,
    name: str,
    path: Path,
    text: str,
    forbidden: List[Tuple[str, str]],
) -> Dict[str, Any]:
    violations: List[Dict[str, Any]] = []

    for label, needle in forbidden:
        if _contains(text, needle):
            violations.append(
                {
                    "label": label,
                    "needle": needle,
                    "hits": _line_hits(text, re.escape(needle)),
                }
            )

    return {
        "name": name,
        "file": str(path),
        "ok": len(violations) == 0,
        "violations": violations,
    }


def _build_checks(repo_root: Path) -> List[Dict[str, Any]]:
    resume_matcher_path = repo_root / "src/ai/resume_matcher.py"
    scorer_path = repo_root / "src/matching/scorer.py"
    selector_path = repo_root / "select_best_resume_variant.py"
    batch_selector_path = repo_root / "batch_select_best_resume_variant.py"
    planning_path = repo_root / "run_application_planning.py"

    resume_matcher_text = _read_text(resume_matcher_path)
    scorer_text = _read_text(scorer_path)
    selector_text = _read_text(selector_path)
    batch_selector_text = _read_text(batch_selector_path)
    planning_text = _read_text(planning_path) if planning_path.exists() else ""

    checks: List[Dict[str, Any]] = []

    checks.append(
        _check_required_substrings(
            name="embedding_prior_emits_prior_fields_only",
            path=resume_matcher_path,
            text=resume_matcher_text,
            required=[
                ("prior field", '"embedding_resume_prior"'),
                ("prior score field", '"embedding_resume_prior_score"'),
                ("job update", "job.update(result)"),
            ],
        )
    )

    checks.append(
        _check_forbidden_substrings(
            name="embedding_prior_does_not_emit_authority_fields",
            path=resume_matcher_path,
            text=resume_matcher_text,
            forbidden=[
                ("winner authority field", '"winner_resume"'),
                ("runner-up authority field", '"runner_up_resume"'),
                ("llm fallback field", '"llm_fallback_best_resume"'),
                ("llm adjudication field", '"llm_adjudication_resume"'),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="deterministic_scorer_entrypoint_exists",
            path=scorer_path,
            text=scorer_text,
            required=[
                ("scorer function", "def score_resume_job_match("),
                ("deterministic prefilter", "prefilter_result = prefilter or run_prefilter(resume, job)"),
                ("final score", "final_score = round(sum(score.weighted_score for score in dimension_scores), 6)"),
                ("match bucket", "match_bucket=_match_bucket(final_score)"),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="single_selector_uses_deterministic_scoring_as_authority",
            path=selector_path,
            text=selector_text,
            required=[
                ("scorer import", "from src.matching.scorer import score_resume_job_match"),
                ("scoring loop", "result = score_resume_job_match(resume_evidence, job_evidence)"),
                ("credible set", "passed_results = [result for result in results if result.prefilter.passed]"),
                ("selected set", "selected = passed_results if passed_results else results"),
                ("winner selection", "winner = selected[0]"),
                ("credible match gate", "has_credible_match = _has_credible_match(passed_results)"),
            ],
        )
    )

    checks.append(
        _check_forbidden_substrings(
            name="single_selector_has_no_live_llm_override_path",
            path=selector_path,
            text=selector_text,
            forbidden=[
                ("llm client import", "from src.ai.llm_client import run_chat_completion"),
                ("llm fallback cli flag", "--generate-llm-fallback"),
                ("llm adjudication cli flag", "--generate-llm-adjudication"),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="batch_selector_still_scores_deterministically_first",
            path=batch_selector_path,
            text=batch_selector_text,
            required=[
                ("scorer import", "from src.matching.scorer import score_resume_job_match"),
                ("scoring loop", "result = score_resume_job_match(resume_evidence, job_evidence)"),
                ("credible set", "passed_results = [result for result in results if result.prefilter.passed]"),
                ("selected set", "selected = passed_results if passed_results else results"),
                ("winner selection", "winner = selected[0]"),
                ("selection signal", 'return "decisive_winner"'),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="llm_fallback_is_bounded_to_no_credible_match",
            path=batch_selector_path,
            text=batch_selector_text,
            required=[
                ("fallback cli flag", "--generate-llm-fallback"),
                ("fallback help text", "For jobs with no credible deterministic winner"),
                ("fallback gate", "if not has_credible_match and args.generate_llm_fallback:"),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="llm_adjudication_is_bounded_to_ambiguous_cases",
            path=batch_selector_path,
            text=batch_selector_text,
            required=[
                ("adjudication cli flag", "--generate-llm-adjudication"),
                ("adjudication help text", "For effective ties and manual-review close calls"),
                ("adjudication policy helper", "def _should_run_llm_adjudication("),
                ("tie branch", "_is_effective_tie(winner, runner_up)"),
                ("close call branch", "_is_close_call_manual_review("),
                ("adjudication gate", "args.generate_llm_adjudication"),
                ("adjudication gate helper", "_should_run_llm_adjudication("),
            ],
        )
    )

    if planning_text:
        checks.append(
            _check_required_substrings(
                name="application_planning_propagates_bounded_llm_flags",
                path=planning_path,
                text=planning_text,
                required=[
                    ("fallback cli flag", "--generate-llm-fallback"),
                    ("adjudication cli flag", "--generate-llm-adjudication"),
                    ("fallback passthrough", 'if args.generate_llm_fallback:'),
                    ("adjudication passthrough", 'if args.generate_llm_adjudication:'),
                    ("batch selector target", '"batch_select_best_resume_variant.py"'),
                ],
            )
        )

    return checks


def _summarize(checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    failed = [check for check in checks if not bool(check.get("ok", False))]
    passed = [check for check in checks if bool(check.get("ok", False))]

    return {
        "total_checks": len(checks),
        "passed_checks": len(passed),
        "failed_checks": len(failed),
        "all_passed": len(failed) == 0,
        "failed_check_names": [check["name"] for check in failed],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit the 3-layer resume-selection authority contract from source."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/_archive/selector_authority_contract/selector_authority_contract.json",
        help="Where to write the machine-readable audit report.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_json = Path(args.output_json)

    checks = _build_checks(repo_root)
    summary = _summarize(checks)

    payload = {
        "repo_root": str(repo_root),
        "summary": summary,
        "checks": checks,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Selector Authority Contract Audit")
    print("--------------------------------")
    print(f"repo_root: {repo_root}")
    print(f"total_checks: {summary['total_checks']}")
    print(f"passed_checks: {summary['passed_checks']}")
    print(f"failed_checks: {summary['failed_checks']}")
    print(f"all_passed: {summary['all_passed']}")
    print(f"output_json: {output_json}")

    if not summary["all_passed"]:
        print("\nFailed checks:")
        for name in summary["failed_check_names"]:
            print(f"- {name}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
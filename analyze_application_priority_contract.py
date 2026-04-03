import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def _line_hits(text: str, needle: str, max_hits: int = 3) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    hits: List[Dict[str, Any]] = []

    for idx, line in enumerate(lines, start=1):
        if needle in line:
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
                    "hits": _line_hits(text, needle),
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
                    "hits": _line_hits(text, needle),
                }
            )

    return {
        "name": name,
        "file": str(path),
        "ok": len(violations) == 0,
        "violations": violations,
    }


def _build_checks(repo_root: Path) -> List[Dict[str, Any]]:
    settings_path = repo_root / "src/config/settings.py"
    scorer_path = repo_root / "src/pipeline/application_scorer.py"
    collector_path = repo_root / "src/pipeline/collector.py"
    resume_matcher_path = repo_root / "src/ai/resume_matcher.py"

    settings_text = _read_text(settings_path)
    scorer_text = _read_text(scorer_path)
    collector_text = _read_text(collector_path)
    resume_matcher_text = _read_text(resume_matcher_path)

    checks: List[Dict[str, Any]] = []

    checks.append(
        _check_required_substrings(
            name="application_priority_policy_version_is_v2",
            path=settings_path,
            text=settings_text,
            required=[
                ("policy version", 'APPLICATION_PRIORITY_POLICY_VERSION = "v2"'),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="application_priority_policy_zeroes_embedding_weight",
            path=settings_path,
            text=settings_text,
            required=[
                ("embedding weight zero", '"embedding_resume_prior_score": 0.00'),
                ("ai signal weight", '"ai_signal_score": 0.50'),
                ("base score weight", '"base_score": 0.30'),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="application_priority_still_uses_policy_weights",
            path=scorer_path,
            text=scorer_text,
            required=[
                ("weights lookup", 'weights = APPLICATION_PRIORITY_POLICY["weights"]'),
                ("ai signal contribution", 'weights["ai_signal_score"] * ai_signal_score'),
                ("base score contribution", 'weights["base_score"] * base_score'),
            ],
        )
    )

    checks.append(
        _check_forbidden_substrings(
            name="application_priority_no_longer_uses_embedding_prior_term",
            path=scorer_path,
            text=scorer_text,
            forbidden=[
                ("embedding prior read", 'embedding_resume_prior_score = job.get("embedding_resume_prior_score", 0)'),
                ("resume score temp", "resume_score = embedding_resume_prior_score * 10"),
                ("embedding contribution", 'weights["embedding_resume_prior_score"] * resume_score'),
            ],
        )
    )

    checks.append(
        _check_required_substrings(
            name="embedding_prior_stage_still_exists_upstream",
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
        _check_required_substrings(
            name="collector_keeps_resume_matching_and_application_priority_separate",
            path=collector_path,
            text=collector_text,
            required=[
                ("resume stage", 'start_stage("resume_matching"'),
                ("match resumes call", "ai_jobs = match_resumes(ai_jobs)"),
                ("priority stage", 'start_stage("application_priority"'),
                ("score jobs call", "scored_jobs = score_jobs(ai_jobs)"),
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
        description="Audit the application-priority contract after removing embedding-prior weighting."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/_archive/application_priority_contract/application_priority_contract.json",
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

    print("Application Priority Contract Audit")
    print("-----------------------------------")
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
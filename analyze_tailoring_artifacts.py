import argparse
import glob
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _load_json_object(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(value).__name__}")
    return value


def _counter_rows(counter: Counter, total: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        pct = round((count / total) * 100.0, 2) if total else 0.0
        rows.append(
            {
                "key": key,
                "count": count,
                "pct": pct,
            }
        )
    return rows


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _candidate_signal_key(candidate: Dict[str, Any]) -> str:
    terms = candidate.get("supported_jd_signals", []) or candidate.get("jd_signal_terms", []) or []
    cleaned = [_safe_text(item) for item in terms if _safe_text(item)]
    return " | ".join(cleaned) if cleaned else "missing"


def _resolved_tailoring_paths(patterns: List[str], include_llm: bool) -> List[Path]:
    matched: List[str] = []

    for pattern in patterns:
        matched.extend(glob.glob(pattern, recursive=True))

    paths: List[Path] = []
    seen = set()

    for raw_path in sorted(matched):
        path = Path(raw_path)
        if not path.is_file():
            continue

        name = path.name.lower()
        if not name.endswith(".json"):
            continue
        if "tailoring" not in name:
            continue
        if not include_llm and name.endswith("tailoring_llm.json"):
            continue

        normalized = str(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        paths.append(path)

    return paths

def _resolved_manifest_paths(manifest_path: Path, include_llm: bool) -> List[Path]:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    if isinstance(raw, dict):
        raw_paths = raw.get("paths", [])
    elif isinstance(raw, list):
        raw_paths = raw
    else:
        raise ValueError(
            f"Manifest must be a JSON object with 'paths' or a JSON list: {manifest_path}"
        )

    if not isinstance(raw_paths, list):
        raise ValueError(f"Manifest 'paths' must be a list: {manifest_path}")

    paths: List[Path] = []
    seen = set()

    for item in raw_paths:
        if not isinstance(item, str):
            raise ValueError(f"Manifest paths must be strings: {manifest_path}")

        path = Path(item)
        if not path.is_file():
            raise ValueError(f"Manifest path does not exist: {path}")

        name = path.name.lower()
        if "tailoring" not in name or not name.endswith(".json"):
            raise ValueError(f"Manifest path is not a tailoring JSON artifact: {path}")

        if not include_llm and name.endswith("tailoring_llm.json"):
            continue

        normalized = str(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        paths.append(path)

    return paths

def _per_file_summary(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    job = payload.get("job", {}) or {}
    selection = payload.get("selection", {}) or {}

    edit_cards = payload.get("edit_cards", []) or []
    bullet_diagnoses = payload.get("bullet_diagnoses", []) or []
    replacement_candidates = payload.get("replacement_candidates", []) or []
    empty_candidate_file = len(replacement_candidates) == 0

    operation_counter: Counter = Counter()
    proposal_status_counter: Counter = Counter()
    patch_generation_counter: Counter = Counter()
    candidate_signal_counter: Counter = Counter()

    patch_ready_rewrite_count = 0
    directional_reorder_count = 0
    directional_suppress_count = 0
    directional_merge_count = 0
    keep_only_count = 0

    invariant_violations: List[str] = []

    for candidate in replacement_candidates:
        operation_type = _safe_text(candidate.get("operation_type"), "missing")
        proposal_status = _safe_text(candidate.get("proposal_status"), "missing")
        patch_generation_method = _safe_text(candidate.get("patch_generation_method"), "missing")
        patch_ready = bool(candidate.get("patch_ready", False))
        patch_text = _safe_text(candidate.get("patch_text"), "")
        signal_key = _candidate_signal_key(candidate)

        operation_counter[operation_type] += 1
        proposal_status_counter[proposal_status] += 1
        patch_generation_counter[patch_generation_method] += 1

        # Duplicate-pressure should be judged on rewrite candidates only.
        # Reorder companions and keep rows naturally reuse the same signal set.
        if operation_type == "rewrite":
            candidate_signal_counter[signal_key] += 1

        if operation_type == "rewrite" and patch_ready:
            patch_ready_rewrite_count += 1
            if not patch_text:
                invariant_violations.append(
                    f"patch_ready_rewrite_missing_patch_text:{candidate.get('candidate_id', '')}"
                )
            if patch_generation_method in {"", "missing"}:
                invariant_violations.append(
                    f"patch_ready_rewrite_missing_generation_method:{candidate.get('candidate_id', '')}"
                )

        if operation_type == "reorder":
            if proposal_status == "direction_only" and not patch_ready:
                directional_reorder_count += 1
            else:
                invariant_violations.append(
                    f"reorder_not_direction_only:{candidate.get('candidate_id', '')}"
                )

        if operation_type == "suppress":
            if proposal_status == "direction_only" and not patch_ready:
                directional_suppress_count += 1
            else:
                invariant_violations.append(
                    f"suppress_not_direction_only:{candidate.get('candidate_id', '')}"
                )

        if operation_type == "merge":
            if proposal_status == "direction_only" and not patch_ready:
                directional_merge_count += 1
            else:
                invariant_violations.append(
                    f"merge_not_direction_only:{candidate.get('candidate_id', '')}"
                )

        if operation_type == "keep":
            if proposal_status == "keep_only" and not patch_ready:
                keep_only_count += 1
            else:
                invariant_violations.append(
                    f"keep_not_keep_only:{candidate.get('candidate_id', '')}"
                )

    duplicate_signal_keys = [
        {"key": key, "count": count}
        for key, count in sorted(candidate_signal_counter.items(), key=lambda item: (-item[1], item[0]))
        if key != "missing" and count > 1
    ]

    return {
        "path": str(path),
        "company": _safe_text(job.get("company")),
        "title": _safe_text(job.get("title")),
        "selected_resume": _safe_text(selection.get("selected_resume")),
        "edit_card_count": len(edit_cards),
        "bullet_diagnosis_count": len(bullet_diagnoses),
        "replacement_candidate_count": len(replacement_candidates),
        "patch_ready_rewrite_count": patch_ready_rewrite_count,
        "directional_reorder_count": directional_reorder_count,
        "directional_suppress_count": directional_suppress_count,
        "directional_merge_count": directional_merge_count,
        "keep_only_count": keep_only_count,
        "empty_candidate_file": empty_candidate_file,
        "missing_proposal_status_count": int(proposal_status_counter.get("missing", 0)),
        "operation_counts": dict(operation_counter),
        "proposal_status_counts": dict(proposal_status_counter),
        "patch_generation_counts": dict(patch_generation_counter),
        "duplicate_signal_keys": duplicate_signal_keys,
        "invariant_violations": invariant_violations,
    }


def _build_summary(paths: List[Path]) -> Dict[str, Any]:
    file_rows: List[Dict[str, Any]] = []

    operation_counter: Counter = Counter()
    proposal_status_counter: Counter = Counter()
    patch_generation_counter: Counter = Counter()
    invariant_counter: Counter = Counter()

    files_with_patch_ready_rewrites = 0
    files_with_directional_suppress = 0
    files_with_directional_merge = 0
    files_with_invariant_violations = 0
    files_with_duplicate_signal_keys = 0
    empty_candidate_files = 0
    files_with_missing_proposal_status = 0

    for path in paths:
        payload = _load_json_object(path)
        row = _per_file_summary(path, payload)
        file_rows.append(row)

        if row["patch_ready_rewrite_count"] > 0:
            files_with_patch_ready_rewrites += 1
        if row["directional_suppress_count"] > 0:
            files_with_directional_suppress += 1
        if row["directional_merge_count"] > 0:
            files_with_directional_merge += 1
        if row["duplicate_signal_keys"]:
            files_with_duplicate_signal_keys += 1
        if row["invariant_violations"]:
            files_with_invariant_violations += 1
        if row["empty_candidate_file"]:
            empty_candidate_files += 1
        if row["missing_proposal_status_count"] > 0:
            files_with_missing_proposal_status += 1

        for key, count in row["operation_counts"].items():
            operation_counter[key] += int(count)

        for key, count in row["proposal_status_counts"].items():
            proposal_status_counter[key] += int(count)

        for key, count in row["patch_generation_counts"].items():
            patch_generation_counter[key] += int(count)

        for issue in row["invariant_violations"]:
            invariant_counter[issue.split(":", 1)[0]] += 1

    file_rows.sort(
        key=lambda row: (
            row["company"],
            row["title"],
            row["selected_resume"],
            row["path"],
        )
    )

    return {
        "total_files": len(file_rows),
        "empty_candidate_files": empty_candidate_files,
        "files_with_missing_proposal_status": files_with_missing_proposal_status,
        "files_with_patch_ready_rewrites": files_with_patch_ready_rewrites,
        "files_with_directional_suppress": files_with_directional_suppress,
        "files_with_directional_merge": files_with_directional_merge,
        "files_with_duplicate_signal_keys": files_with_duplicate_signal_keys,
        "files_with_invariant_violations": files_with_invariant_violations,
        "aggregate_operation_counts": _counter_rows(operation_counter, sum(operation_counter.values())),
        "aggregate_proposal_status_counts": _counter_rows(proposal_status_counter, sum(proposal_status_counter.values())),
        "aggregate_patch_generation_counts": _counter_rows(patch_generation_counter, sum(patch_generation_counter.values())),
        "aggregate_invariant_issue_counts": _counter_rows(invariant_counter, sum(invariant_counter.values())),
        "files": file_rows,
    }


def _print_counter_block(title: str, rows: List[Dict[str, Any]]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not rows:
        print("none")
        return
    for row in rows:
        print(f"{row['key']}: {row['count']} ({row['pct']:.2f}%)")


def _print_file_rows(summary: Dict[str, Any], top_n: int) -> None:
    print("\nPer-File Highlights")
    print("-------------------")

    rows = list(summary.get("files", []) or [])
    focus_rows = [row for row in rows if int(row.get("replacement_candidate_count", 0) or 0) > 0] or rows

    ranked = sorted(
        focus_rows,
        key=lambda row: (
            -len(row.get("invariant_violations", []) or []),
            -int(row.get("replacement_candidate_count", 0) or 0),
            row.get("path", ""),
        ),
    )

    for row in ranked[:top_n]:
        print(
            f"\n{row['company']} | {row['title']} | {row['selected_resume'] or 'missing_resume'}"
        )
        print(f"  path: {row['path']}")
        print(
            f"  cards={row['edit_card_count']} | diagnoses={row['bullet_diagnosis_count']} | "
            f"candidates={row['replacement_candidate_count']}"
        )
        print(
            f"  patch_ready_rewrites={row['patch_ready_rewrite_count']} | "
            f"directional_merge={row['directional_merge_count']} | "
            f"directional_suppress={row['directional_suppress_count']} | "
            f"directional_reorder={row['directional_reorder_count']} | "
            f"keep_only={row['keep_only_count']}"
        )
        if row.get("duplicate_signal_keys"):
            print(f"  duplicate_signal_keys={row['duplicate_signal_keys']}")
        if row.get("invariant_violations"):
            print(f"  invariant_violations={row['invariant_violations']}")
        else:
            print("  invariant_violations=[]")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze final tailoring JSON artifacts for deterministic regression sweep."
    )
    parser.add_argument(
        "--glob",
        action="append",
        default=[],
        help="Glob pattern for tailoring JSON artifacts. Repeat to add more patterns.",
    )
    parser.add_argument(
        "--include-llm",
        action="store_true",
        help="Include __tailoring_llm.json artifacts. Default analyzes deterministic __tailoring.json only.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="How many per-file rows to print.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write machine-readable summary JSON.",
    )
    parser.add_argument(
        "--manifest",
        default="",
        help="Optional JSON manifest listing exact tailoring artifact paths to analyze.",
    )
    args = parser.parse_args()

    if args.manifest.strip():
        paths = _resolved_manifest_paths(
            Path(args.manifest.strip()),
            include_llm=args.include_llm,
        )
    else:
        patterns = args.glob or [
            "outputs/**/*.json",
        ]
        paths = _resolved_tailoring_paths(patterns, include_llm=args.include_llm)
    if not paths:
        raise ValueError("No tailoring JSON artifacts matched the supplied glob patterns.")

    summary = _build_summary(paths)

    print("Tailoring Artifact Regression Sweep")
    print("----------------------------------")
    print(f"total_files: {summary['total_files']}")
    print(f"empty_candidate_files: {summary['empty_candidate_files']}")
    print(f"files_with_missing_proposal_status: {summary['files_with_missing_proposal_status']}")
    print(f"files_with_patch_ready_rewrites: {summary['files_with_patch_ready_rewrites']}")
    print(f"files_with_directional_suppress: {summary['files_with_directional_suppress']}")
    print(f"files_with_directional_merge: {summary['files_with_directional_merge']}")
    print(f"files_with_duplicate_signal_keys: {summary['files_with_duplicate_signal_keys']}")
    print(f"files_with_invariant_violations: {summary['files_with_invariant_violations']}")

    _print_counter_block("Aggregate Operation Counts", summary["aggregate_operation_counts"])
    _print_counter_block("Aggregate Proposal Status Counts", summary["aggregate_proposal_status_counts"])
    _print_counter_block("Aggregate Patch Generation Counts", summary["aggregate_patch_generation_counts"])
    _print_counter_block("Aggregate Invariant Issue Counts", summary["aggregate_invariant_issue_counts"])
    _print_file_rows(summary, max(args.top_n, 1))

    if args.output_json.strip():
        output_path = Path(args.output_json)
        _write_json(output_path, summary)
        print(f"\nWrote summary JSON: {output_path}")


if __name__ == "__main__":
    main()
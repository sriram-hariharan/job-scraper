import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _load_json_object(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(value).__name__}")
    return value


def _write_json(path: Path, payload: Dict[str, Any] | List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _is_packet_fixture(path: Path) -> bool:
    name = path.name.lower()
    if not name.endswith(".json"):
        return False
    if name.endswith("__tailoring.json"):
        return False
    if name.endswith("__tailoring_llm.json"):
        return False
    return True


def _is_nonprod_fixture(path: Path) -> bool:
    name = path.name.lower()
    return (
        "smoke" in name
        or "workspace_draft" in name
        or name.startswith("_debug")
        or name.startswith("_phase")
    )


def _resolve_packet_paths(
    fixture_dir: Path,
    include_nonprod: bool,
    limit: int,
) -> List[Path]:
    if not fixture_dir.exists():
        raise FileNotFoundError(f"Fixture directory not found: {fixture_dir}")

    paths = sorted(
        [
            path
            for path in fixture_dir.glob("*.json")
            if _is_packet_fixture(path)
            and (include_nonprod or not _is_nonprod_fixture(path))
        ],
        key=lambda path: path.name,
    )

    if limit > 0:
        paths = paths[:limit]

    if not paths:
        raise ValueError(f"No packet fixtures found in {fixture_dir}")

    return paths


def _extract_hits_from_tailoring_json(path: Path) -> Dict[str, Any]:
    payload = _load_json_object(path)

    targets = {
        "selected_source",
        "selected_reason",
        "fallback_reason_codes",
        "deterministic_planner",
        "live_llm",
        "live_llm_blended",
    }
    hits: Dict[str, Any] = {}

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in targets and key not in hits:
                    hits[key] = value
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(payload)
    return hits


def _build_row_from_tailoring_json(
    packet_path: Path,
    tailoring_json_path: Path,
    returncode: int,
    elapsed_seconds: float,
    stdout_tail: str,
    stderr_tail: str,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "packet_json": str(packet_path),
        "tailoring_json": str(tailoring_json_path),
        "returncode": returncode,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "stdout_tail": stdout_tail[-2000:],
        "stderr_tail": stderr_tail[-2000:],
        "selected_source": "",
        "selected_reason": "",
        "covers_plan": None,
        "verifier_ok": None,
        "quality_score": None,
        "fallback_reason_codes": [],
        "is_nonprod_fixture": _is_nonprod_fixture(packet_path),
    }

    if returncode != 0 or not tailoring_json_path.exists():
        return row

    try:
        hits = _extract_hits_from_tailoring_json(tailoring_json_path)
        row["selected_source"] = _safe_text(hits.get("selected_source"))
        row["selected_reason"] = _safe_text(hits.get("selected_reason"))
        row["fallback_reason_codes"] = list(hits.get("fallback_reason_codes", []) or [])

        det = hits.get("deterministic_planner") or {}
        if isinstance(det, dict):
            row["covers_plan"] = det.get("covers_plan")
            row["verifier_ok"] = det.get("verifier_ok")
            row["quality_score"] = det.get("quality_score")
    except Exception as exc:
        row["parse_error"] = str(exc)

    return row


def _build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    real_rows = [row for row in rows if not bool(row.get("is_nonprod_fixture", False))]

    return {
        "fixture_count": len(rows),
        "success_count": sum(1 for row in rows if int(row.get("returncode", 1)) == 0),
        "deterministic_planner_selected_count": sum(
            1 for row in rows if row.get("selected_source") == "deterministic_planner"
        ),
        "covers_plan_true_count": sum(
            1 for row in rows if row.get("covers_plan") is True
        ),
        "verifier_ok_true_count": sum(
            1 for row in rows if row.get("verifier_ok") is True
        ),
        "real_fixture_count": len(real_rows),
        "real_success_count": sum(
            1 for row in real_rows if int(row.get("returncode", 1)) == 0
        ),
        "real_deterministic_planner_selected_count": sum(
            1 for row in real_rows if row.get("selected_source") == "deterministic_planner"
        ),
        "real_covers_plan_true_count": sum(
            1 for row in real_rows if row.get("covers_plan") is True
        ),
        "real_verifier_ok_true_count": sum(
            1 for row in real_rows if row.get("verifier_ok") is True
        ),
    }


def _real_outliers(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        row
        for row in rows
        if not bool(row.get("is_nonprod_fixture", False))
        and (
            int(row.get("returncode", 1)) != 0
            or row.get("selected_source") != "deterministic_planner"
            or row.get("covers_plan") is not True
            or row.get("verifier_ok") is not True
        )
    ]


def _print_outliers(rows: List[Dict[str, Any]]) -> None:
    outliers = _real_outliers(rows)
    print(f"\nREAL_OUTLIER_COUNT={len(outliers)}")
    for idx, row in enumerate(outliers, start=1):
        print(f"\n===== REAL OUTLIER {idx} =====")
        print(f"packet_json={row.get('packet_json')}")
        print(f"tailoring_json={row.get('tailoring_json')}")
        print(f"returncode={row.get('returncode')}")
        print(f"selected_source={row.get('selected_source')}")
        print(f"selected_reason={row.get('selected_reason')}")
        print(f"covers_plan={row.get('covers_plan')}")
        print(f"verifier_ok={row.get('verifier_ok')}")
        print(f"quality_score={row.get('quality_score')}")
        print(f"fallback_reason_codes={row.get('fallback_reason_codes')}")
        if row.get("parse_error"):
            print(f"parse_error={row.get('parse_error')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rerun tailoring generation across packet fixtures and summarize selection-path regressions."
    )
    parser.add_argument(
        "--fixture-dir",
        default="outputs/_archive/application_planning_phase4c_fixtures/current",
        help="Directory containing packet JSON fixtures.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/_archive/application_planning_phase4c_sweep",
        help="Directory to write generated tailoring outputs and sweep artifacts.",
    )
    parser.add_argument(
        "--training-log-jsonl",
        default="outputs/application_planning/training_logs/tailoring_runs.jsonl",
        help="Training log JSONL path passed through to generate_tailoring_suggestions.py.",
    )
    parser.add_argument(
        "--include-nonprod",
        action="store_true",
        help="Include smoke/debug/workspace draft fixtures in the rerun set.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit on number of fixtures to run. 0 means all.",
    )
    parser.add_argument(
        "--fail-on-real-outliers",
        action="store_true",
        help="Exit nonzero if any real fixture fails selection-path expectations.",
    )
    args = parser.parse_args()

    fixture_dir = Path(args.fixture_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_paths = _resolve_packet_paths(
        fixture_dir=fixture_dir,
        include_nonprod=bool(args.include_nonprod),
        limit=max(args.limit, 0),
    )

    print("Tailoring Packet Regression Sweep")
    print("--------------------------------")
    print(f"fixture_dir: {fixture_dir}")
    print(f"output_dir: {output_dir}")
    print(f"fixture_count: {len(packet_paths)}")

    results: List[Dict[str, Any]] = []
    manifest_path = output_dir / "phase4c_sweep_manifest.json"
    summary_path = output_dir / "phase4c_sweep_summary.json"

    for idx, packet_path in enumerate(packet_paths, start=1):
        tailoring_json_path = output_dir / f"{packet_path.stem}__tailoring.json"
        tailoring_md_path = output_dir / f"{packet_path.stem}__tailoring.md"

        cmd = [
            sys.executable,
            "generate_tailoring_suggestions.py",
            "--packet-json",
            str(packet_path),
            "--output-json",
            str(tailoring_json_path),
            "--output-md",
            str(tailoring_md_path),
            "--training-log-jsonl",
            args.training_log_jsonl,
        ]

        print(f"\n[{idx}/{len(packet_paths)}] RUNNING {packet_path.name}")
        started = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - started
        print(f"[{idx}/{len(packet_paths)}] RETURN CODE={proc.returncode} ELAPSED={elapsed:.1f}s")

        row = _build_row_from_tailoring_json(
            packet_path=packet_path,
            tailoring_json_path=tailoring_json_path,
            returncode=proc.returncode,
            elapsed_seconds=elapsed,
            stdout_tail=proc.stdout,
            stderr_tail=proc.stderr,
        )
        results.append(row)

        _write_json(manifest_path, results)
        _write_json(summary_path, _build_summary(results))

    summary = _build_summary(results)
    _write_json(manifest_path, results)
    _write_json(summary_path, summary)

    print("\nDONE")
    print(f"WROTE {manifest_path}")
    print(f"WROTE {summary_path}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    _print_outliers(results)

    if args.fail_on_real_outliers and _real_outliers(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
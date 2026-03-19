import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, List


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _infer_dimension_names(fieldnames: List[str]) -> List[str]:
    dimension_names = []
    for field in fieldnames:
        if not field.endswith("_score"):
            continue
        if field == "final_score":
            continue

        base = field[:-6]
        weighted_field = f"{base}_weighted_score"
        if weighted_field in fieldnames:
            dimension_names.append(base)

    return dimension_names


def _load_rows(csv_path: Path) -> List[dict]:
    if not csv_path.exists():
        raise RuntimeError(f"Missing CSV: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"CSV is empty: {csv_path}")

    return rows


def _safe_mean(values: List[float]) -> float:
    return mean(values) if values else 0.0


def _print_ranked_group_summary(
    title: str,
    grouped_rows: Dict[str, List[dict]],
    label_builder,
    top_k: int,
) -> None:
    summary = []

    for _, rows in grouped_rows.items():
        passed = [r for r in rows if _parse_bool(r["prefilter_passed"])]
        scores_all = [_parse_float(r["final_score"]) for r in rows]
        scores_passed = [_parse_float(r["final_score"]) for r in passed]

        summary.append(
            {
                "label": label_builder(rows[0]),
                "pair_count": len(rows),
                "pass_count": len(passed),
                "pass_rate": len(passed) / len(rows) if rows else 0.0,
                "avg_score_all": _safe_mean(scores_all),
                "avg_score_passed": _safe_mean(scores_passed),
                "max_score": max(scores_all) if scores_all else 0.0,
            }
        )

    summary.sort(
        key=lambda x: (
            -x["pass_rate"],
            -x["avg_score_passed"],
            -x["max_score"],
            x["label"].lower(),
        )
    )

    print("=" * 100)
    print(title)
    print("=" * 100)
    print()

    for item in summary[:top_k]:
        print(
            f"{item['label']} | "
            f"pairs={item['pair_count']} | "
            f"passed={item['pass_count']} | "
            f"pass_rate={item['pass_rate']:.2%} | "
            f"avg_score_all={item['avg_score_all']:.3f} | "
            f"avg_score_passed={item['avg_score_passed']:.3f} | "
            f"max_score={item['max_score']:.3f}"
        )

    print()


def _print_dimension_stats(rows: List[dict], dimension_names: List[str]) -> None:
    print("=" * 100)
    print("DIMENSION SATURATION / NEUTRALITY")
    print("=" * 100)
    print()

    stats = []
    row_count = len(rows)

    for dim in dimension_names:
        values = [_parse_float(r[f"{dim}_score"]) for r in rows]
        neutral = sum(1 for v in values if abs(v - 0.5) < 1e-9)
        maxed = sum(1 for v in values if abs(v - 1.0) < 1e-9)
        very_low = sum(1 for v in values if v < 0.2)
        avg_value = _safe_mean(values)

        stats.append(
            {
                "name": dim,
                "avg": avg_value,
                "neutral_pct": neutral / row_count if row_count else 0.0,
                "maxed_pct": maxed / row_count if row_count else 0.0,
                "very_low_pct": very_low / row_count if row_count else 0.0,
            }
        )

    stats.sort(key=lambda x: (-x["maxed_pct"], -x["neutral_pct"], x["name"]))

    for item in stats:
        print(
            f"{item['name']} | "
            f"avg={item['avg']:.3f} | "
            f"neutral={item['neutral_pct']:.2%} | "
            f"maxed={item['maxed_pct']:.2%} | "
            f"very_low={item['very_low_pct']:.2%}"
        )

    print()


def _print_job_tie_groups(rows: List[dict], top_k: int) -> None:
    print("=" * 100)
    print("TOP JOB-SIDE TIE GROUPS")
    print("=" * 100)
    print()

    grouped = defaultdict(list)

    for row in rows:
        if not _parse_bool(row["prefilter_passed"]):
            continue

        key = (
            row["job_doc_id"],
            row["job_company"],
            row["job_title"],
            row["final_score"],
        )
        grouped[key].append(row["resume_name"])

    tie_groups = []
    for (job_doc_id, company, title, score), resume_names in grouped.items():
        unique_resumes = sorted(set(resume_names))
        if len(unique_resumes) <= 1:
            continue

        tie_groups.append(
            {
                "job_doc_id": job_doc_id,
                "company": company,
                "title": title,
                "score": _parse_float(score),
                "count": len(unique_resumes),
                "resumes": unique_resumes,
            }
        )

    tie_groups.sort(
        key=lambda x: (-x["count"], -x["score"], x["company"].lower(), x["title"].lower())
    )

    if not tie_groups:
        print("No job-side ties with multiple resumes at the same score.")
        print()
        return

    for item in tie_groups[:top_k]:
        print(
            f"{item['company']} | {item['title']} | "
            f"score={item['score']:.3f} | tied_resumes={item['count']}"
        )
        print(f"  resumes: {item['resumes']}")

    print()

def _print_filtered_out_pairs(rows: List[dict], top_k: int) -> None:
    print("=" * 100)
    print("FILTERED-OUT PAIRS")
    print("=" * 100)
    print()

    filtered_rows = [row for row in rows if not _parse_bool(row["prefilter_passed"])]

    if not filtered_rows:
        print("No filtered-out pairs.")
        print()
        return

    filtered_rows.sort(
        key=lambda row: (
            row["job_company"].lower(),
            row["job_title"].lower(),
            row["resume_name"].lower(),
        )
    )

    for row in filtered_rows[:top_k]:
        print(
            f"{row['resume_name']} | {row['job_company']} | {row['job_title']} | "
            f"score={_parse_float(row['final_score']):.3f} | bucket={row['match_bucket']}"
        )
        print(f"  reasons: {row['prefilter_reasons']}")
        if row["matched_terms"]:
            print(f"  matched_terms: {row['matched_terms']}")
        if row["missing_requirements"]:
            print(f"  missing_required: {row['missing_requirements']}")
        print()

    if len(filtered_rows) > top_k:
        print(f"... showing {top_k} of {len(filtered_rows)} filtered-out pairs.")
        print()

def _print_near_top_gaps_per_job(rows: List[dict], top_k: int) -> None:
    print("=" * 100)
    print("NEAR-TOP GAPS PER JOB")
    print("=" * 100)
    print()

    rows_by_job = defaultdict(list)
    for row in rows:
        if _parse_bool(row["prefilter_passed"]):
            rows_by_job[row["job_doc_id"]].append(row)

    if not rows_by_job:
        print("No passed rows available for gap analysis.")
        print()
        return

    ordered_jobs = sorted(
        rows_by_job.values(),
        key=lambda job_rows: (
            job_rows[0]["job_company"].lower(),
            job_rows[0]["job_title"].lower(),
        )
    )

    for job_rows in ordered_jobs[:top_k]:
        job_rows = sorted(
            job_rows,
            key=lambda row: (
                -_parse_float(row["final_score"]),
                row["resume_name"].lower(),
            )
        )

        company = job_rows[0]["job_company"]
        title = job_rows[0]["job_title"]

        print(f"{company} | {title}")

        top_rows = job_rows[:3]
        for idx, row in enumerate(top_rows, start=1):
            print(
                f"  {idx}. {row['resume_name']} | "
                f"score={_parse_float(row['final_score']):.3f}"
            )

        if len(top_rows) >= 2:
            gap_1_2 = _parse_float(top_rows[0]["final_score"]) - _parse_float(top_rows[1]["final_score"])
            print(f"  gap(top1-top2) = {gap_1_2:.3f}")

        if len(top_rows) >= 3:
            gap_2_3 = _parse_float(top_rows[1]["final_score"]) - _parse_float(top_rows[2]["final_score"])
            print(f"  gap(top2-top3) = {gap_2_3:.3f}")

        print()

def _print_tie_diagnostics_for_near_top_jobs(
    rows: List[dict],
    dimension_names: List[str],
    top_k: int,
    gap_threshold: float = 0.01,
) -> None:
    print("=" * 100)
    print("TIE DIAGNOSTICS FOR NEAR-TOP JOBS")
    print("=" * 100)
    print()

    rows_by_job = defaultdict(list)
    for row in rows:
        if _parse_bool(row["prefilter_passed"]):
            rows_by_job[row["job_doc_id"]].append(row)

    candidate_jobs = []

    for job_rows in rows_by_job.values():
        ordered = sorted(
            job_rows,
            key=lambda row: (
                -_parse_float(row["final_score"]),
                row["resume_name"].lower(),
            )
        )

        if len(ordered) < 2:
            continue

        gap_1_2 = _parse_float(ordered[0]["final_score"]) - _parse_float(ordered[1]["final_score"])
        gap_2_3 = None
        if len(ordered) >= 3:
            gap_2_3 = _parse_float(ordered[1]["final_score"]) - _parse_float(ordered[2]["final_score"])

        if gap_1_2 <= gap_threshold or (gap_2_3 is not None and gap_2_3 <= gap_threshold):
            candidate_jobs.append((ordered, gap_1_2, gap_2_3))

    if not candidate_jobs:
        print("No near-top job ties found under the configured gap threshold.")
        print()
        return

    candidate_jobs.sort(
        key=lambda item: (
            item[0][0]["job_company"].lower(),
            item[0][0]["job_title"].lower(),
        )
    )

    shown = 0
    for ordered, gap_1_2, gap_2_3 in candidate_jobs:
        if shown >= top_k:
            break

        company = ordered[0]["job_company"]
        title = ordered[0]["job_title"]

        print(f"{company} | {title}")
        print(f"  gap(top1-top2) = {gap_1_2:.3f}")
        if gap_2_3 is not None:
            print(f"  gap(top2-top3) = {gap_2_3:.3f}")
        print()

        for idx, row in enumerate(ordered[:3], start=1):
            print(
                f"  {idx}. {row['resume_name']} | "
                f"score={_parse_float(row['final_score']):.3f} | "
                f"bucket={row['match_bucket']}"
            )

            weighted_parts = []
            for dim in dimension_names:
                weighted_parts.append(
                    f"{dim}={_parse_float(row[f'{dim}_weighted_score']):.3f}"
                )

            print(f"     weighted_dims: {', '.join(weighted_parts)}")
            print()

        shown += 1

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze pairwise matching smoke-test CSV output."
    )
    parser.add_argument(
        "--input-csv",
        default="matching_smoke_results.csv",
        help="Path to matching smoke CSV export.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="How many top summary rows to print per section.",
    )
    args = parser.parse_args()

    csv_path = Path(args.input_csv)
    rows = _load_rows(csv_path)
    fieldnames = list(rows[0].keys())
    dimension_names = _infer_dimension_names(fieldnames)

    resumes = sorted({r["resume_name"] for r in rows})
    jobs = sorted({r["job_doc_id"] for r in rows})
    passed_rows = [r for r in rows if _parse_bool(r["prefilter_passed"])]

    print("=" * 100)
    print("MATCHING CSV ANALYSIS")
    print("=" * 100)
    print(f"CSV path        : {csv_path}")
    print(f"Total rows      : {len(rows)}")
    print(f"Unique resumes  : {len(resumes)}")
    print(f"Unique jobs     : {len(jobs)}")
    print(f"Prefilter pass  : {len(passed_rows)}/{len(rows)} ({len(passed_rows)/len(rows):.2%})")
    print(f"Dimensions      : {dimension_names}")
    print()

    rows_by_resume = defaultdict(list)
    rows_by_job = defaultdict(list)

    for row in rows:
        rows_by_resume[row["resume_id"]].append(row)
        rows_by_job[row["job_doc_id"]].append(row)

    _print_ranked_group_summary(
        title="TOP RESUMES BY PASS RATE / SCORE",
        grouped_rows=rows_by_resume,
        label_builder=lambda row: row["resume_name"],
        top_k=args.top_k,
    )

    _print_ranked_group_summary(
        title="TOP JOBS BY PASS RATE / SCORE",
        grouped_rows=rows_by_job,
        label_builder=lambda row: f"{row['job_company']} | {row['job_title']}",
        top_k=args.top_k,
    )

    _print_dimension_stats(rows, dimension_names)
    _print_job_tie_groups(rows, args.top_k)
    _print_filtered_out_pairs(rows, args.top_k)
    _print_near_top_gaps_per_job(rows, args.top_k)
    _print_tie_diagnostics_for_near_top_jobs(rows, dimension_names, args.top_k)


if __name__ == "__main__":
    main()
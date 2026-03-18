import argparse
import csv
import json
from pathlib import Path
from typing import List, Optional

from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import load_resume_documents
from src.resume.evidence_builder import build_resume_evidence

TIE_EPSILON = 0.005

def _load_job_records(job_corpus_path: Path, limit: int) -> List[dict]:
    if not job_corpus_path.exists():
        raise RuntimeError(f"Missing job corpus: {job_corpus_path}")

    records: List[dict] = []
    with job_corpus_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
            if limit > 0 and len(records) >= limit:
                break

    if not records:
        raise RuntimeError(f"No job records found in {job_corpus_path}")

    return records


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _job_matches_filters(record: dict, company_contains: str, title_contains: str) -> bool:
    company_ok = True
    title_ok = True

    if company_contains.strip():
        company_ok = _normalize_text(company_contains) in _normalize_text(record.get("company", ""))

    if title_contains.strip():
        title_ok = _normalize_text(title_contains) in _normalize_text(record.get("title", ""))

    return company_ok and title_ok


def _result_sort_key(result):
    return (
        -int(result.prefilter.passed),
        -result.final_score,
        result.pair.resume_name.lower(),
        result.pair.resume_id.lower(),
    )


def _dimension_snapshot(result, max_dims: int = 5) -> str:
    ordered = sorted(
        result.dimension_scores,
        key=lambda dim: (-dim.weighted_score, dim.name),
    )
    return ", ".join(
        f"{dim.name}={dim.score:.2f}/{dim.weighted_score:.3f}"
        for dim in ordered[:max_dims]
    )


def _recommendation_lines(winner, runner_up: Optional[object]) -> List[str]:
    lines = []
    is_tie = _is_effective_tie(winner, runner_up)

    if is_tie:
        lines.append(
            f"Tie: {winner.pair.resume_name} and {runner_up.pair.resume_name} "
            f"are effectively equivalent for {winner.pair.job_company} | {winner.pair.job_title}."
        )
        lines.append(
            f"Why: score gap is only {winner.final_score - runner_up.final_score:.3f}, "
            f"which is within the tie threshold of {TIE_EPSILON:.3f}."
        )
        lines.append(f"Top-ranked variant by deterministic ordering: {winner.pair.resume_name}")
        lines.append(f"Equivalent backup variant: {runner_up.pair.resume_name}")
    else:
        lines.append(f"Use: {winner.pair.resume_name}")
        lines.append(
            f"Why: highest deterministic match score ({winner.final_score:.3f}) "
            f"for {winner.pair.job_company} | {winner.pair.job_title}."
        )

        if runner_up is not None:
            lines.append(
                f"Best backup: {runner_up.pair.resume_name} "
                f"(score {runner_up.final_score:.3f}, gap {winner.final_score - runner_up.final_score:.3f})."
            )

    if winner.prefilter.matched_terms:
        lines.append(
            f"Strongest matched terms: {', '.join(winner.prefilter.matched_terms[:6])}"
        )

    if winner.prefilter.missing_requirements:
        lines.append(
            f"Main remaining gaps: {', '.join(winner.prefilter.missing_requirements[:6])}"
        )
    else:
        lines.append("Main remaining gaps: none explicitly identified.")

    return lines

def _is_effective_tie(winner, runner_up: Optional[object], epsilon: float = TIE_EPSILON) -> bool:
    if runner_up is None:
        return False
    return abs(winner.final_score - runner_up.final_score) <= epsilon

def _has_credible_match(passed_results: List[object]) -> bool:
    return len(passed_results) > 0


def _no_credible_match_lines(top_result) -> List[str]:
    lines = [
        f"No credible resume match: all resume variants failed deterministic prefilter for "
        f"{top_result.pair.job_company} | {top_result.pair.job_title}.",
        f"Closest diagnostic variant by deterministic ordering: "
        f"{top_result.pair.resume_name} (score {top_result.final_score:.3f}).",
    ]

    if top_result.prefilter.matched_terms:
        lines.append(
            f"Strongest matched terms: {', '.join(top_result.prefilter.matched_terms[:6])}"
        )

    if top_result.prefilter.missing_requirements:
        lines.append(
            f"Main remaining gaps: {', '.join(top_result.prefilter.missing_requirements[:6])}"
        )
    else:
        lines.append("Main remaining gaps: none explicitly identified.")

    return lines

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-select the best resume variant for multiple jobs."
    )
    parser.add_argument(
        "--job-corpus",
        default="data/rag/job_corpus.jsonl",
        help="Path to the retrieval-ready job corpus JSONL.",
    )
    parser.add_argument(
        "--job-limit",
        type=int,
        default=50,
        help="How many jobs from the corpus to evaluate. Use 0 for all.",
    )
    parser.add_argument(
        "--company-contains",
        default="",
        help="Optional case-insensitive company substring filter.",
    )
    parser.add_argument(
        "--title-contains",
        default="",
        help="Optional case-insensitive title substring filter.",
    )
    parser.add_argument(
        "--resume-name-contains",
        default="",
        help="Optional case-insensitive resume filename substring filter.",
    )
    parser.add_argument(
        "--top-k-console",
        type=int,
        default=10,
        help="How many selected jobs to print to the console.",
    )
    parser.add_argument(
        "--output-csv",
        default="best_resume_variant_by_job.csv",
        help="Path to write the batch selector CSV.",
    )
    args = parser.parse_args()

    raw_records = _load_job_records(
        Path(args.job_corpus),
        limit=args.job_limit,
    )

    job_records = [
        record for record in raw_records
        if _job_matches_filters(
            record,
            company_contains=args.company_contains,
            title_contains=args.title_contains,
        )
    ]

    if not job_records:
        raise RuntimeError("No job records matched the provided filters.")

    resume_docs = load_resume_documents()
    if args.resume_name_contains.strip():
        needle = _normalize_text(args.resume_name_contains)
        resume_docs = [
            doc for doc in resume_docs
            if needle in _normalize_text(doc.resume_name)
        ]

    resume_docs = sorted(resume_docs, key=lambda doc: doc.resume_name)
    if not resume_docs:
        raise RuntimeError("No resume documents loaded after filters.")

    resume_evidence_list = [build_resume_evidence(doc) for doc in resume_docs]

    output_rows = []

    for record in job_records:
        job_evidence = build_job_evidence(record)

        results = []
        for resume_evidence in resume_evidence_list:
            result = score_resume_job_match(resume_evidence, job_evidence)
            results.append(result)

        results = sorted(results, key=_result_sort_key)
        passed_results = [result for result in results if result.prefilter.passed]
        failed_results = [result for result in results if not result.prefilter.passed]

        selected = passed_results if passed_results else results
        winner = selected[0]
        runner_up = selected[1] if len(selected) > 1 else None

        has_credible_match = _has_credible_match(passed_results)
        if not has_credible_match:
            runner_up = None

        is_tie = _is_effective_tie(winner, runner_up) if has_credible_match else False

        output_rows.append(
            {
                "job_doc_id": winner.pair.job_doc_id,
                "job_company": winner.pair.job_company,
                "job_title": winner.pair.job_title,
                "resume_variants_considered": len(results),
                "passed_prefilter": len(passed_results),
                "filtered_out": len(failed_results),
                "winner_resume": winner.pair.resume_name if has_credible_match else "",
                "winner_score": f"{winner.final_score:.6f}",
                "winner_bucket": winner.match_bucket,
                "winner_top_dims": _dimension_snapshot(winner),
                "winner_missing_requirements": " | ".join(winner.prefilter.missing_requirements),
                "winner_matched_terms": " | ".join(winner.prefilter.matched_terms),
                "runner_up_resume": (
                    runner_up.pair.resume_name
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_score": (
                    f"{runner_up.final_score:.6f}"
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "score_gap": (
                    f"{(winner.final_score - runner_up.final_score):.6f}"
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "is_tie": is_tie,
                "tie_epsilon": f"{TIE_EPSILON:.6f}",
                "recommendation_summary": (
                                    " ".join(_recommendation_lines(winner, runner_up))
                                    if has_credible_match
                                    else " ".join(_no_credible_match_lines(winner))
                                ),            
            }
        )

    output_rows = sorted(
        output_rows,
        key=lambda row: (
            row["job_company"].lower(),
            row["job_title"].lower(),
            -float(row["winner_score"]),
            row["winner_resume"].lower(),
        ),
    )

    fieldnames = [
        "job_doc_id",
        "job_company",
        "job_title",
        "resume_variants_considered",
        "passed_prefilter",
        "filtered_out",
        "winner_resume",
        "winner_score",
        "winner_bucket",
        "winner_top_dims",
        "winner_missing_requirements",
        "winner_matched_terms",
        "runner_up_resume",
        "runner_up_score",
        "score_gap",
        "is_tie",
        "tie_epsilon",
        "recommendation_summary",
    ]

    output_csv_path = Path(args.output_csv)
    with output_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    print("=" * 100)
    print("BATCH BEST RESUME VARIANT SELECTOR")
    print("=" * 100)
    print(f"Jobs evaluated: {len(output_rows)}")
    print(f"Resume variants considered per job: {len(resume_evidence_list)}")
    print(f"CSV written: {output_csv_path}")
    print()

    for row in output_rows[:args.top_k_console]:
        print("-" * 100)
        print(f"{row['job_company']} | {row['job_title']}")
        if row["winner_resume"]:
            print(f"Winner: {row['winner_resume']} | score={float(row['winner_score']):.3f} | bucket={row['winner_bucket']}")
        else:
            print(f"No credible resume match | score={float(row['winner_score']):.3f} | bucket={row['winner_bucket']}")        
        if row["runner_up_resume"]:
            if str(row["is_tie"]).lower() == "true":
                print(
                    f"Tie backup: {row['runner_up_resume']} | "
                    f"score={float(row['runner_up_score']):.3f} | "
                    f"gap={float(row['score_gap']):.3f} | "
                    f"tie_epsilon={float(row['tie_epsilon']):.3f}"
                )
            else:
                print(
                    f"Backup: {row['runner_up_resume']} | "
                    f"score={float(row['runner_up_score']):.3f} | "
                    f"gap={float(row['score_gap']):.3f}"
                )
        print(f"Top dims: {row['winner_top_dims']}")
        if row["winner_missing_requirements"]:
            print(f"Missing requirements: {row['winner_missing_requirements']}")
        print(f"Summary: {row['recommendation_summary']}")
        print()


if __name__ == "__main__":
    main()
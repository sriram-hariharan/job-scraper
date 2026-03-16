import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import load_resume_documents
from src.resume.evidence_builder import build_resume_evidence


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
            if len(records) >= limit:
                break

    if not records:
        raise RuntimeError(f"No job records found in {job_corpus_path}")

    return records


def _dimension_snapshot(result, max_dims: int = 5) -> str:
    ordered = sorted(
        result.dimension_scores,
        key=lambda dim: (-dim.weighted_score, dim.name),
    )
    parts = [
        f"{dim.name}={dim.score:.2f}/{dim.weighted_score:.3f}"
        for dim in ordered[:max_dims]
    ]
    return ", ".join(parts)


def _result_sort_key(result):
    return (
        -int(result.prefilter.passed),
        -result.final_score,
        result.pair.job_company.lower(),
        result.pair.job_title.lower(),
        result.pair.job_doc_id.lower(),
    )

def _job_result_sort_key(result):
    return (
        -int(result.prefilter.passed),
        -result.final_score,
        result.pair.resume_name.lower(),
        result.pair.resume_id.lower(),
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manual batch sanity-check runner for deterministic resume-job matching."
    )
    parser.add_argument(
        "--job-corpus",
        default="data/rag/job_corpus.jsonl",
        help="Path to the retrieval-ready job corpus JSONL.",
    )
    parser.add_argument(
        "--resume-limit",
        type=int,
        default=5,
        help="How many resumes to score.",
    )
    parser.add_argument(
        "--job-limit",
        type=int,
        default=20,
        help="How many jobs from the corpus to score.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="How many top jobs to print per resume.",
    )
    parser.add_argument(
        "--resume-name-contains",
        default="",
        help="Optional case-insensitive substring filter on resume filename.",
    )
    args = parser.parse_args()

    job_corpus_path = Path(args.job_corpus)
    job_records = _load_job_records(job_corpus_path, args.job_limit)

    resume_docs = load_resume_documents()
    if args.resume_name_contains.strip():
        needle = args.resume_name_contains.strip().lower()
        resume_docs = [
            doc for doc in resume_docs
            if needle in doc.resume_name.lower()
        ]

    resume_docs = sorted(resume_docs, key=lambda doc: doc.resume_name)
    if args.resume_limit > 0:
        resume_docs = resume_docs[:args.resume_limit]

    if not resume_docs:
        raise RuntimeError("No resume documents loaded after filters.")

    resume_evidence_list = [build_resume_evidence(doc) for doc in resume_docs]
    job_evidence_list = [build_job_evidence(record) for record in job_records]

    results_by_resume: Dict[str, List] = defaultdict(list)
    results_by_job: Dict[str, List] = defaultdict(list)

    for resume_evidence in resume_evidence_list:
        for job_evidence in job_evidence_list:
            result = score_resume_job_match(resume_evidence, job_evidence)
            results_by_resume[resume_evidence.document.resume_id].append(result)
            results_by_job[job_evidence.job_doc_id].append(result)

    total_pairs = sum(len(results) for results in results_by_resume.values())

    print("=" * 100)
    print("MATCHING SMOKE TEST")
    print("=" * 100)
    print(f"Resumes scored : {len(resume_evidence_list)}")
    print(f"Jobs scored    : {len(job_evidence_list)}")
    print(f"Total pairs    : {total_pairs}")
    print()

    for resume_evidence in resume_evidence_list:
        resume_id = resume_evidence.document.resume_id
        resume_name = resume_evidence.document.resume_name
        resume_results = sorted(results_by_resume[resume_id], key=_result_sort_key)

        passed_results = [result for result in resume_results if result.prefilter.passed]
        failed_results = [result for result in resume_results if not result.prefilter.passed]

        print("-" * 100)
        print(f"RESUME: {resume_name}")
        print(f"Pairs: {len(resume_results)} | Passed prefilter: {len(passed_results)} | Filtered out: {len(failed_results)}")

        selected = passed_results[:args.top_k] if passed_results else resume_results[:args.top_k]
        if not selected:
            print("No results.")
            print()
            continue

        for rank, result in enumerate(selected, start=1):
            print(
                f"{rank:>2}. "
                f"score={result.final_score:.3f} | "
                f"bucket={result.match_bucket:<12} | "
                f"prefilter={'PASS' if result.prefilter.passed else 'FAIL'} | "
                f"{result.pair.job_company} | {result.pair.job_title}"
            )

            if result.prefilter.reasons:
                print(f"    reasons: {result.prefilter.reasons}")

            if result.prefilter.matched_terms:
                print(f"    matched_terms: {result.prefilter.matched_terms[:8]}")

            if result.prefilter.missing_requirements:
                print(f"    missing_required: {result.prefilter.missing_requirements[:8]}")

            print(f"    top_dims: {_dimension_snapshot(result)}")

        print()
    
    print("=" * 100)
    print("TOP RESUMES PER JOB")
    print("=" * 100)
    print()

    for job_evidence in job_evidence_list:
        job_id = job_evidence.job_doc_id
        job_results = sorted(results_by_job[job_id], key=_job_result_sort_key)

        passed_results = [result for result in job_results if result.prefilter.passed]
        failed_results = [result for result in job_results if not result.prefilter.passed]

        print("-" * 100)
        print(f"JOB: {job_evidence.company} | {job_evidence.title}")
        print(f"Pairs: {len(job_results)} | Passed prefilter: {len(passed_results)} | Filtered out: {len(failed_results)}")

        selected = passed_results[:args.top_k] if passed_results else job_results[:args.top_k]
        if not selected:
            print("No results.")
            print()
            continue

        for rank, result in enumerate(selected, start=1):
            print(
                f"{rank:>2}. "
                f"score={result.final_score:.3f} | "
                f"bucket={result.match_bucket:<12} | "
                f"prefilter={'PASS' if result.prefilter.passed else 'FAIL'} | "
                f"{result.pair.resume_name}"
            )

            if result.prefilter.reasons:
                print(f"    reasons: {result.prefilter.reasons}")

            if result.prefilter.matched_terms:
                print(f"    matched_terms: {result.prefilter.matched_terms[:8]}")

            if result.prefilter.missing_requirements:
                print(f"    missing_required: {result.prefilter.missing_requirements[:8]}")

            print(f"    top_dims: {_dimension_snapshot(result)}")

        print()

    print("=" * 100)
    print("DONE")
    print("=" * 100)


if __name__ == "__main__":
    main()
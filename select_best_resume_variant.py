import argparse
import json
from pathlib import Path
from typing import List, Optional

from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import load_resume_documents
from src.resume.evidence_builder import build_resume_evidence

TIE_EPSILON = 0.005

def _load_job_records(job_corpus_path: Path) -> List[dict]:
    if not job_corpus_path.exists():
        raise RuntimeError(f"Missing job corpus: {job_corpus_path}")

    records: List[dict] = []
    with job_corpus_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    if not records:
        raise RuntimeError(f"No job records found in {job_corpus_path}")

    return records


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _job_sort_key(record: dict):
    return (
        _normalize_text(record.get("company", "")),
        _normalize_text(record.get("title", "")),
        _normalize_text(record.get("job_doc_id", "")),
    )


def _select_job_record(
    records: List[dict],
    job_index: int,
    company_contains: str,
    title_contains: str,
) -> dict:
    filtered = records

    if company_contains.strip():
        needle = _normalize_text(company_contains)
        filtered = [
            record for record in filtered
            if needle in _normalize_text(record.get("company", ""))
        ]

    if title_contains.strip():
        needle = _normalize_text(title_contains)
        filtered = [
            record for record in filtered
            if needle in _normalize_text(record.get("title", ""))
        ]

    if company_contains.strip() or title_contains.strip():
        if not filtered:
            raise RuntimeError(
                "No job matched the provided company/title filters."
            )

        filtered = sorted(filtered, key=_job_sort_key)
        return filtered[0]

    if job_index < 0 or job_index >= len(records):
        raise RuntimeError(
            f"--job-index {job_index} is out of range for {len(records)} job records."
        )

    return records[job_index]


def _result_sort_key(result):
    return (
        -int(result.prefilter.passed),
        -result.final_score,
        result.pair.resume_name.lower(),
        result.pair.resume_id.lower(),
    )


def _dimension_snapshot(result, max_dims: int = 6) -> str:
    ordered = sorted(
        result.dimension_scores,
        key=lambda dim: (-dim.weighted_score, dim.name),
    )
    return ", ".join(
        f"{dim.name}={dim.score:.2f}/{dim.weighted_score:.3f}"
        for dim in ordered[:max_dims]
    )


def _top_dimension_deltas(top_result, runner_up_result, max_dims: int = 5) -> List[str]:
    top_map = {dim.name: dim for dim in top_result.dimension_scores}
    runner_map = {dim.name: dim for dim in runner_up_result.dimension_scores}

    deltas = []
    for name, top_dim in top_map.items():
        runner_dim = runner_map[name]
        delta = top_dim.weighted_score - runner_dim.weighted_score
        deltas.append((delta, name, top_dim, runner_dim))

    deltas.sort(key=lambda item: (-abs(item[0]), item[1]))

    formatted = []
    for delta, name, top_dim, runner_dim in deltas[:max_dims]:
        sign = "+" if delta >= 0 else "-"
        formatted.append(
            f"{name}: {sign}{abs(delta):.3f} "
            f"(winner={top_dim.weighted_score:.3f}, runner_up={runner_dim.weighted_score:.3f})"
        )
    return formatted

def _is_effective_tie(winner, runner_up: Optional[object], epsilon: float = TIE_EPSILON) -> bool:
    if runner_up is None:
        return False
    return abs(winner.final_score - runner_up.final_score) <= epsilon

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

def _dimension_to_dict(dim) -> dict:
    return {
        "name": dim.name,
        "score": dim.score,
        "weight": dim.weight,
        "weighted_score": dim.weighted_score,
        "reason": dim.reason,
        "evidence": list(dim.evidence),
    }


def _result_to_dict(result) -> dict:
    return {
        "resume_id": result.pair.resume_id,
        "resume_name": result.pair.resume_name,
        "job_doc_id": result.pair.job_doc_id,
        "job_company": result.pair.job_company,
        "job_title": result.pair.job_title,
        "prefilter_passed": result.prefilter.passed,
        "prefilter_reasons": list(result.prefilter.reasons),
        "matched_terms": list(result.prefilter.matched_terms),
        "missing_requirements": list(result.prefilter.missing_requirements),
        "final_score": result.final_score,
        "match_bucket": result.match_bucket,
        "dimension_scores": [_dimension_to_dict(dim) for dim in result.dimension_scores],
    }

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select the best resume variant for one target JD using the current deterministic matcher."
    )
    parser.add_argument(
        "--job-corpus",
        default="data/rag/job_corpus.jsonl",
        help="Path to the retrieval-ready job corpus JSONL.",
    )
    parser.add_argument(
        "--job-index",
        type=int,
        default=0,
        help="Zero-based job index in the corpus when no company/title filter is provided.",
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
        "--top-k",
        type=int,
        default=5,
        help="How many ranked resume variants to print.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write the ranked resume-variant selection as JSON.",
    )
    args = parser.parse_args()

    job_corpus_path = Path(args.job_corpus)
    job_records = _load_job_records(job_corpus_path)
    selected_job_record = _select_job_record(
        records=job_records,
        job_index=args.job_index,
        company_contains=args.company_contains,
        title_contains=args.title_contains,
    )
    job_evidence = build_job_evidence(selected_job_record)

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

    results = []
    for resume_doc in resume_docs:
        resume_evidence = build_resume_evidence(resume_doc)
        result = score_resume_job_match(resume_evidence, job_evidence)
        results.append(result)

    results = sorted(results, key=_result_sort_key)

    passed_results = [result for result in results if result.prefilter.passed]
    failed_results = [result for result in results if not result.prefilter.passed]

    print("=" * 100)
    print("BEST RESUME VARIANT SELECTOR")
    print("=" * 100)
    print(f"JOB: {job_evidence.company} | {job_evidence.title}")
    print(f"JOB DOC ID: {job_evidence.job_doc_id}")
    print(f"Resume variants considered: {len(results)}")
    print(f"Passed prefilter: {len(passed_results)} | Filtered out: {len(failed_results)}")
    print()

    selected = passed_results if passed_results else results
    if not selected:
        raise RuntimeError("No results produced.")

    winner = selected[0]
    runner_up: Optional[object] = selected[1] if len(selected) > 1 else None
    is_tie = _is_effective_tie(winner, runner_up)

    print("-" * 100)
    print("WINNER")
    print("-" * 100)
    print(
        f"{winner.pair.resume_name} | "
        f"score={winner.final_score:.3f} | "
        f"bucket={winner.match_bucket} | "
        f"prefilter={'PASS' if winner.prefilter.passed else 'FAIL'}"
    )
    print(f"Prefilter reasons: {winner.prefilter.reasons}")
    if winner.prefilter.matched_terms:
        print(f"Matched terms: {winner.prefilter.matched_terms[:10]}")
    if winner.prefilter.missing_requirements:
        print(f"Missing requirements: {winner.prefilter.missing_requirements[:12]}")
    print(f"Top dimensions: {_dimension_snapshot(winner)}")
    print()

    if runner_up is not None:
        print("-" * 100)
        print("RUNNER-UP")
        print("-" * 100)
        print(
            f"{runner_up.pair.resume_name} | "
            f"score={runner_up.final_score:.3f} | "
            f"bucket={runner_up.match_bucket} | "
            f"prefilter={'PASS' if runner_up.prefilter.passed else 'FAIL'}"
        )
        print(f"Prefilter reasons: {runner_up.prefilter.reasons}")
        if runner_up.prefilter.matched_terms:
            print(f"Matched terms: {runner_up.prefilter.matched_terms[:10]}")
        if runner_up.prefilter.missing_requirements:
            print(f"Missing requirements: {runner_up.prefilter.missing_requirements[:12]}")
        print(f"Top dimensions: {_dimension_snapshot(runner_up)}")
        print()

        print("-" * 100)
        if is_tie:
            print("TIE STATUS")
            print("-" * 100)
            print(
                f"{winner.pair.resume_name} and {runner_up.pair.resume_name} "
                f"are effectively tied."
            )
            print(
                f"Score gap: {winner.final_score - runner_up.final_score:.3f} "
                f"(tie threshold {TIE_EPSILON:.3f})"
            )
        else:
            print("WHY THE WINNER WON")
            print("-" * 100)
            print(f"Score gap: {winner.final_score - runner_up.final_score:.3f}")
            for item in _top_dimension_deltas(winner, runner_up):
                print(item)
        print()
    
    print("-" * 100)
    print("APPLICATION RECOMMENDATION")
    print("-" * 100)
    for line in _recommendation_lines(winner, runner_up):
        print(line)
    print()

    print("-" * 100)
    print(f"TOP {min(args.top_k, len(selected))} VARIANTS")
    print("-" * 100)
    for rank, result in enumerate(selected[:args.top_k], start=1):
        print(
            f"{rank:>2}. {result.pair.resume_name} | "
            f"score={result.final_score:.3f} | "
            f"bucket={result.match_bucket} | "
            f"prefilter={'PASS' if result.prefilter.passed else 'FAIL'}"
        )
        print(f"    top_dims: {_dimension_snapshot(result)}")
        if result.prefilter.missing_requirements:
            print(f"    missing_required: {result.prefilter.missing_requirements[:8]}")
        print()

    if failed_results:
        print("-" * 100)
        print("FILTERED-OUT VARIANTS")
        print("-" * 100)
        for result in failed_results:
            print(
                f"{result.pair.resume_name} | "
                f"score={result.final_score:.3f} | "
                f"bucket={result.match_bucket}"
            )
            print(f"    reasons: {result.prefilter.reasons}")
            if result.prefilter.matched_terms:
                print(f"    matched_terms: {result.prefilter.matched_terms[:8]}")
            if result.prefilter.missing_requirements:
                print(f"    missing_required: {result.prefilter.missing_requirements[:8]}")
            print()

    if args.output_json.strip():
        output_path = Path(args.output_json)

        payload = {
            "job": {
                "job_doc_id": job_evidence.job_doc_id,
                "company": job_evidence.company,
                "title": job_evidence.title,
            },
            "summary": {
                "resume_variants_considered": len(results),
                "passed_prefilter": len(passed_results),
                "filtered_out": len(failed_results),
            },
            "application_recommendation": _recommendation_lines(winner, runner_up),
            "winner": _result_to_dict(winner),
            "runner_up": _result_to_dict(runner_up) if runner_up is not None else None,
            "winner_vs_runner_up": {
                "score_gap": (winner.final_score - runner_up.final_score) if runner_up is not None else None,
                "is_tie": is_tie,
                "tie_epsilon": TIE_EPSILON,
                "top_dimension_deltas": (
                    _top_dimension_deltas(winner, runner_up)
                    if runner_up is not None and not is_tie
                    else []
                ),
            },
            "ranked_variants": [_result_to_dict(result) for result in selected],
            "filtered_out_variants": [_result_to_dict(result) for result in failed_results],
        }

        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written: {output_path}")

if __name__ == "__main__":
    main()
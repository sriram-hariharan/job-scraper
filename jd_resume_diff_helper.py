import argparse
import json
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

from src.config.consts import TITLE_CANONICAL, _SKILL_ALIASES, CONTEXT_TOKEN_STOPWORDS
from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import load_resume_documents
from src.resume.evidence_builder import build_resume_evidence

TIE_EPSILON = 0.010
TITLE_ONLY_TIE_EPSILON = 0.015
NON_TITLE_DELTA_EPSILON = 0.002


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
    text = str(value or "").lower().strip()
    if not text:
        return ""

    for source, target in TITLE_CANONICAL.items():
        text = re.sub(rf"\b{re.escape(source)}\b", target, text)

    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+/\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return _SKILL_ALIASES.get(text, text)


def _unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []

    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            ordered.append(cleaned)

    return ordered


def _normalized_skill_list(values: List[str]) -> List[str]:
    return _unique_preserve_order(
        [_normalize_text(value) for value in values if _normalize_text(value)]
    )


def _contains_signal(text: str, signal: str) -> bool:
    return re.search(rf"\b{re.escape(_normalize_text(signal))}\b", text) is not None

def _context_tokens(value: str) -> List[str]:
    text = _normalize_text(value)
    if not text:
        return []

    tokens = []
    for token in text.split():
        token = token.strip()
        if not token:
            continue
        if token in CONTEXT_TOKEN_STOPWORDS:
            continue
        if len(token) < 3 and token not in {"ml", "ai", "r"}:
            continue
        tokens.append(token)

    return _unique_preserve_order(tokens)


def _job_context_terms(job) -> List[str]:
    values: List[str] = []
    values.extend(_context_tokens(job.title))
    values.extend(_context_tokens(" ".join(job.required_skills or [])))
    values.extend(_context_tokens(" ".join(job.preferred_skills or [])))
    values.extend(_context_tokens(" ".join(job.all_skills or [])))
    return _unique_preserve_order(values)

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
            raise RuntimeError("No job matched the provided company/title filters.")
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


def _is_effective_tie(winner, runner_up: Optional[object], epsilon: float = TIE_EPSILON) -> bool:
    if runner_up is None:
        return False

    score_gap = abs(winner.final_score - runner_up.final_score)

    if score_gap <= epsilon:
        return True

    return (
        score_gap <= TITLE_ONLY_TIE_EPSILON
        and _is_title_only_edge(winner, runner_up)
    )


def _resume_explicit_skill_set(resume) -> Set[str]:
    values: List[str] = []
    values.extend(resume.skills)

    for entry in resume.experience_entries:
        values.extend(entry.normalized_skills)

    for entry in resume.project_entries:
        values.extend(entry.normalized_skills)

    return {_normalize_text(value) for value in values if _normalize_text(value)}


def _split_job_skill_gaps(resume, job) -> Tuple[List[str], List[str], List[str], List[str]]:
    resume_skill_set = _resume_explicit_skill_set(resume)

    required = _normalized_skill_list(job.required_skills)
    preferred = _normalized_skill_list(job.preferred_skills)

    matched_required = [skill for skill in required if skill in resume_skill_set]
    missing_required = [skill for skill in required if skill not in resume_skill_set]

    matched_preferred = [skill for skill in preferred if skill in resume_skill_set]
    missing_preferred = [skill for skill in preferred if skill not in resume_skill_set]

    return matched_required, missing_required, matched_preferred, missing_preferred


def _collect_top_relevant_bullets(resume, job, top_k: int = 8) -> List[dict]:
    job_targets = _normalized_skill_list(job.required_skills + job.preferred_skills + job.all_skills)

    direct_rows: List[dict] = []
    source_entries = {}

    def _source_key(section: str, source_title: str, source_company: str) -> str:
        return "||".join(
            [
                section,
                _normalize_text(source_title),
                _normalize_text(source_company),
            ]
        )

    def _row_key(row: dict) -> tuple:
        return (
            row.get("section", ""),
            row.get("source_title", ""),
            row.get("source_company", ""),
            row.get("bullet_index", -1),
            row.get("text", ""),
        )

    def _append_source_rows(
        *,
        section: str,
        source_title: str,
        source_company: str,
        bullets: List[str],
    ) -> None:
        src_key = _source_key(section, source_title, source_company)

        source_entries[src_key] = {
            "section": section,
            "source_title": source_title,
            "source_company": source_company,
            "bullets": bullets,
        }

        for bullet_index, bullet in enumerate(bullets):
            bullet_norm = _normalize_text(bullet)
            if not bullet_norm:
                continue

            overlaps = [term for term in job_targets if _contains_signal(bullet_norm, term)]
            if not overlaps:
                continue

            direct_rows.append(
                {
                    "section": section,
                    "source_title": source_title,
                    "source_company": source_company,
                    "text": bullet,
                    "overlap_count": len(overlaps),
                    "overlaps": overlaps,
                    "evidence_type": "direct_overlap",
                    "source_key": src_key,
                    "bullet_index": bullet_index,
                }
            )

    for entry in resume.experience_entries:
        _append_source_rows(
            section="experience",
            source_title=entry.title,
            source_company=entry.company,
            bullets=entry.bullets,
        )

    for entry in resume.project_entries:
        _append_source_rows(
            section="project",
            source_title=entry.name,
            source_company="",
            bullets=entry.bullets,
        )

    direct_rows.sort(
        key=lambda row: (
            -row["overlap_count"],
            row["section"],
            row["source_title"].lower(),
            row["text"].lower(),
        )
    )

    if not direct_rows:
        return []

    selected: List[dict] = []
    selected_keys = set()
    used_sources = set()

    source_best_overlap_count = {}
    source_anchor_overlaps = {}
    source_anchor_indices = {}

    def _register_selected(row: dict) -> None:
        key = _row_key(row)
        if key in selected_keys:
            return

        selected.append(row)
        selected_keys.add(key)

        src_key = row["source_key"]
        used_sources.add(src_key)
        source_best_overlap_count[src_key] = max(
            source_best_overlap_count.get(src_key, 0),
            int(row.get("overlap_count", 0) or 0),
        )
        source_anchor_overlaps.setdefault(src_key, list(row.get("overlaps", [])))
        source_anchor_indices.setdefault(src_key, []).append(int(row.get("bullet_index", -1)))

    # Pass 1: diversify across sources using strongest direct-overlap bullets.
    for row in direct_rows:
        if len(selected) >= top_k:
            break
        if row["source_key"] in used_sources:
            continue
        _register_selected(row)

    # Pass 2: fill remaining slots with strongest remaining direct-overlap bullets.
    for row in direct_rows:
        if len(selected) >= top_k:
            break
        _register_selected(row)

    if len(selected) >= top_k:
        return selected[:top_k]

    # Pass 3: add more bullets from already-proven relevant sources, even if they do not
    # have explicit JD-term overlap. This gives richer role-level context.
    same_source_context_rows: List[dict] = []

    for src_key, source_meta in source_entries.items():
        if src_key not in used_sources:
            continue

        bullets = source_meta["bullets"]
        anchor_indices = source_anchor_indices.get(src_key, [])
        anchor_overlaps = source_anchor_overlaps.get(src_key, [])
        source_strength = source_best_overlap_count.get(src_key, 0)

        for bullet_index, bullet in enumerate(bullets):
            bullet_norm = _normalize_text(bullet)
            if not bullet_norm:
                continue

            candidate = {
                "section": source_meta["section"],
                "source_title": source_meta["source_title"],
                "source_company": source_meta["source_company"],
                "text": bullet,
                "overlap_count": max(source_strength - 1, 1),
                "overlaps": list(anchor_overlaps),
                "evidence_type": "same_source_context",
                "source_key": src_key,
                "bullet_index": bullet_index,
                "distance_to_anchor": (
                    min(abs(bullet_index - idx) for idx in anchor_indices)
                    if anchor_indices else 999
                ),
            }

            key = _row_key(candidate)
            if key in selected_keys:
                continue

            same_source_context_rows.append(candidate)

    same_source_context_rows.sort(
        key=lambda row: (
            -source_best_overlap_count.get(row["source_key"], 0),
            row.get("distance_to_anchor", 999),
            row["section"],
            row["source_title"].lower(),
            row["text"].lower(),
        )
    )

    for row in same_source_context_rows:
        if len(selected) >= top_k:
            break
        _register_selected(row)

    if len(selected) >= top_k:
        return selected[:top_k]

    # Pass 4: add immediate neighbors from selected anchors as a final local-context fill.
    enriched: List[dict] = list(selected[:top_k])

    for anchor in list(selected):
        if len(enriched) >= top_k:
            break

        source_meta = source_entries.get(anchor["source_key"])
        if not source_meta:
            continue

        bullets = source_meta["bullets"]
        for offset in (-1, 1):
            if len(enriched) >= top_k:
                break

            neighbor_index = anchor["bullet_index"] + offset
            if neighbor_index < 0 or neighbor_index >= len(bullets):
                continue

            neighbor_text = bullets[neighbor_index]
            neighbor_norm = _normalize_text(neighbor_text)
            if not neighbor_norm:
                continue

            neighbor_row = {
                "section": source_meta["section"],
                "source_title": source_meta["source_title"],
                "source_company": source_meta["source_company"],
                "text": neighbor_text,
                "overlap_count": max(anchor.get("overlap_count", 1) - 1, 1),
                "overlaps": list(anchor.get("overlaps", [])),
                "evidence_type": "adjacent_context",
                "source_key": anchor["source_key"],
                "bullet_index": neighbor_index,
            }

            key = _row_key(neighbor_row)
            if key in selected_keys:
                continue

            enriched.append(neighbor_row)
            selected_keys.add(key)

    return enriched[:top_k]


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
            f"(selected={top_dim.weighted_score:.3f}, backup={runner_dim.weighted_score:.3f})"
        )
    return formatted

def _is_title_only_edge(
    winner,
    runner_up: Optional[object],
    non_title_epsilon: float = NON_TITLE_DELTA_EPSILON,
) -> bool:
    if runner_up is None:
        return False

    winner_map = {dim.name: dim for dim in winner.dimension_scores}
    runner_map = {dim.name: dim for dim in runner_up.dimension_scores}

    saw_title_delta = False

    for name, winner_dim in winner_map.items():
        runner_dim = runner_map.get(name)
        if runner_dim is None:
            continue

        delta = abs(winner_dim.weighted_score - runner_dim.weighted_score)

        if name == "title_alignment":
            if delta > 0.0:
                saw_title_delta = True
            continue

        if delta > non_title_epsilon:
            return False

    return saw_title_delta

def _payload_for_json(
    job_evidence,
    selected_resume,
    selected_result,
    runner_up_result,
    is_tie: bool,
    matched_required: List[str],
    missing_required: List[str],
    matched_preferred: List[str],
    missing_preferred: List[str],
    top_bullets: List[dict],
) -> dict:
    return {
        "job": {
            "job_doc_id": job_evidence.job_doc_id,
            "company": job_evidence.company,
            "title": job_evidence.title,
        },
        "selection": {
            "selected_resume": selected_result.pair.resume_name,
            "selected_score": selected_result.final_score,
            "selected_bucket": selected_result.match_bucket,
            "runner_up_resume": runner_up_result.pair.resume_name if runner_up_result is not None else None,
            "runner_up_score": runner_up_result.final_score if runner_up_result is not None else None,
            "score_gap": (
                round(selected_result.final_score - runner_up_result.final_score, 6)
                if runner_up_result is not None
                else None
            ),
            "is_tie": is_tie,
            "tie_epsilon": TIE_EPSILON,
        },
        "summary": {
            "matched_required": matched_required,
            "missing_required": missing_required,
            "matched_preferred": matched_preferred,
            "missing_preferred": missing_preferred,
            "matched_terms": list(selected_result.prefilter.matched_terms),
            "top_dimensions": _dimension_snapshot(selected_result),
        },
        "top_dimension_deltas_vs_backup": (
            _top_dimension_deltas(selected_result, runner_up_result)
            if runner_up_result is not None and not is_tie
            else []
        ),
        "top_relevant_bullets": top_bullets,
        "guardrail": "Only add or strengthen resume language when it is already truthful and supported by your actual work.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show a JD-specific resume diff/tailoring helper for the best selected resume variant."
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
        help="Optional case-insensitive resume filename substring filter. Leave blank to auto-select the best variant.",
    )
    parser.add_argument(
        "--top-bullets",
        type=int,
        default=8,
        help="How many top relevant bullets to show.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write the JD diff output as JSON.",
    )
    args = parser.parse_args()

    job_records = _load_job_records(Path(args.job_corpus))
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

    scored = []
    for resume_doc in resume_docs:
        resume_evidence = build_resume_evidence(resume_doc)
        result = score_resume_job_match(resume_evidence, job_evidence)
        scored.append((resume_evidence, result))

    scored.sort(key=lambda item: _result_sort_key(item[1]))
    passed = [item for item in scored if item[1].prefilter.passed]
    selected_pool = passed if passed else scored

    selected_resume, selected_result = selected_pool[0]
    runner_up_resume = None
    runner_up_result = None
    if len(selected_pool) > 1:
        runner_up_resume, runner_up_result = selected_pool[1]

    is_tie = _is_effective_tie(selected_result, runner_up_result)

    matched_required, missing_required, matched_preferred, missing_preferred = _split_job_skill_gaps(
        selected_resume,
        job_evidence,
    )
    top_bullets = _collect_top_relevant_bullets(
        selected_resume,
        job_evidence,
        top_k=args.top_bullets,
    )

    print("=" * 100)
    print("JD-SPECIFIC RESUME DIFF HELPER")
    print("=" * 100)
    print(f"JOB: {job_evidence.company} | {job_evidence.title}")
    print(f"JOB DOC ID: {job_evidence.job_doc_id}")
    print()

    print("-" * 100)
    print("SELECTED RESUME")
    print("-" * 100)
    print(
        f"{selected_result.pair.resume_name} | "
        f"score={selected_result.final_score:.3f} | "
        f"bucket={selected_result.match_bucket} | "
        f"prefilter={'PASS' if selected_result.prefilter.passed else 'FAIL'}"
    )
    print(f"Top dimensions: {_dimension_snapshot(selected_result)}")
    print()

    if runner_up_result is not None:
        print("-" * 100)
        print("SELECTION STATUS")
        print("-" * 100)
        if is_tie:
            print(
                f"Tie: {selected_result.pair.resume_name} and {runner_up_result.pair.resume_name} "
                f"are effectively equivalent."
            )
            print(
                f"Score gap: {round(selected_result.final_score - runner_up_result.final_score,6):.3f} "
                f"(tie threshold {TIE_EPSILON:.3f})"
            )
        else:
            print(
                f"Backup variant: {runner_up_result.pair.resume_name} | "
                f"score={runner_up_result.final_score:.3f} | "
                f"gap={round(selected_result.final_score - runner_up_result.final_score):.3f}"
            )
            for item in _top_dimension_deltas(selected_result, runner_up_result):
                print(item)
        print()

    print("-" * 100)
    print("KEEP / EMPHASIZE")
    print("-" * 100)
    print(f"Matched required skills: {matched_required if matched_required else []}")
    print(f"Matched preferred skills: {matched_preferred if matched_preferred else []}")
    print(f"Matched terms from prefilter: {selected_result.prefilter.matched_terms[:12]}")
    print()

    print("-" * 100)
    print("TAILORING GAPS")
    print("-" * 100)
    print(f"Missing required skills: {missing_required if missing_required else []}")
    print(f"Missing preferred skills: {missing_preferred if missing_preferred else []}")
    print("Guardrail: only add or strengthen wording if it is already true and supported by your actual work.")
    print()

    print("-" * 100)
    print("BEST EXISTING BULLETS TO REUSE / REVIEW")
    print("-" * 100)
    if not top_bullets:
        print("No strongly overlapping bullets were found.")
    else:
        for idx, row in enumerate(top_bullets, start=1):
            source = row["source_title"]
            if row["source_company"]:
                source = f"{row['source_title']} @ {row['source_company']}"
            print(f"{idx}. [{row['section']}] {source}")
            print(f"   evidence_type: {row.get('evidence_type', 'direct_overlap')}")
            print(f"   overlaps: {row['overlaps']}")
            if row.get("context_terms"):
                print(f"   context_terms: {row['context_terms']}")
            print(f"   bullet: {row['text']}")
            print()

    if args.output_json.strip():
        payload = _payload_for_json(
            job_evidence=job_evidence,
            selected_resume=selected_resume,
            selected_result=selected_result,
            runner_up_result=runner_up_result,
            is_tie=is_tie,
            matched_required=matched_required,
            missing_required=missing_required,
            matched_preferred=matched_preferred,
            missing_preferred=missing_preferred,
            top_bullets=top_bullets,
        )
        output_path = Path(args.output_json)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written: {output_path}")


if __name__ == "__main__":
    main()
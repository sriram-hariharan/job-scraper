# benchmark_skill_extractors.py

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

from src.ai.skill_llm_enricher import enrich_skills_with_llm
from src.utils.skill_normalizer import KNOWN_CANONICAL_SKILLS, normalize_extracted_skills


# Strong explicit section headers only.
_REQUIRED_HEADERS = [
    r"\brequired qualifications\b",
    r"\bminimum qualifications\b",
    r"\bbasic qualifications\b",
    r"\bwhat we're looking for\b",
    r"\bwhat you need\b",
    r"\bwhat you'll need\b",
    r"\bbecause you have\b",
]

_PREFERRED_HEADERS = [
    r"\bpreferred qualifications\b",
    r"\bnice to have\b",
    r"\bbonus points\b",
]

_INLINE_PREFERRED_PATTERNS = [
    r"\bis a plus\b",
    r"\ba plus\b",
    r"\bnice to have\b",
    r"\bbonus points\b",
]

# deterministic benchmark sample should always include these current trouble cases
_DEFAULT_TARGETS = [
    ("doordashusa", "Machine Learning Engineer, Reinforcement Learning"),
    ("doordashusa", "Machine Learning Engineer, Marketplace Optimization"),
    ("andurilindustries", "Machine Learning Engineer, Quality Analytics"),
    ("pinterest", "Sr. Data Scientist, tvScientific"),
]

# Extraction-safe suppressions for section matching.
# These are broad fields / generic umbrellas that should not drive required/preferred extraction.
_SECTION_EXACT_EXCLUDE = {
    "excel",
    "computer science",
    "economics",
    "math",
    "physics",
    "operations research",
    "electrical engineering",
    "analytics",
    "analysis",
    "data science",
    "incrementality",
    "experimentation",
    "version control",
    "feature engineering",
}

_SECTION_PATTERN_EXCLUDE = [
    r"\bfundamentals?\b",
    r"\bprinciples?\b",
    r"\bproduction-level\b",
    r"\bscalable\b",
    r"\bintuitive\b",
    r"\bflexible\b",
]


def _is_extraction_safe_skill(skill: str) -> bool:
    if skill in _SECTION_EXACT_EXCLUDE:
        return False

    if any(re.search(pattern, skill) for pattern in _SECTION_PATTERN_EXCLUDE):
        return False

    return True

_SORTED_CANONICAL_SKILLS = sorted(
    [s for s in KNOWN_CANONICAL_SKILLS if _is_extraction_safe_skill(s)],
    key=lambda s: (-len(s), s),
)

def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _skill_regex(skill: str) -> re.Pattern:
    return re.compile(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])")


def _find_headers(text_norm: str) -> List[Tuple[int, int, str]]:
    headers: List[Tuple[int, int, str]] = []

    for pattern in _REQUIRED_HEADERS:
        for match in re.finditer(pattern, text_norm):
            headers.append((match.start(), match.end(), "required"))

    for pattern in _PREFERRED_HEADERS:
        for match in re.finditer(pattern, text_norm):
            headers.append((match.start(), match.end(), "preferred"))

    headers.sort(key=lambda x: x[0])
    return headers


def _build_section_spans(text_norm: str) -> Dict[str, List[Tuple[int, int]]]:
    spans: Dict[str, List[Tuple[int, int]]] = {
        "required": [],
        "preferred": [],
        "body": [],
    }

    headers = _find_headers(text_norm)
    if not headers:
        spans["body"].append((0, len(text_norm)))
        return spans

    cursor = 0
    for idx, (start, _end, bucket) in enumerate(headers):
        if cursor < start:
            spans["body"].append((cursor, start))

        next_start = headers[idx + 1][0] if idx + 1 < len(headers) else len(text_norm)
        spans[bucket].append((start, next_start))
        cursor = next_start

    if cursor < len(text_norm):
        spans["body"].append((cursor, len(text_norm)))

    return spans


def _extract_known_skills_from_span(span_text: str) -> List[str]:
    found: List[str] = []
    for skill in _SORTED_CANONICAL_SKILLS:
        if _skill_regex(skill).search(span_text):
            found.append(skill)
    return found


def _appears_in_span(skill: str, span_text: str) -> bool:
    return bool(_skill_regex(skill).search(span_text))


def _appears_in_inline_preferred_context(skill: str, text_norm: str, window_chars: int = 220) -> bool:
    for pattern in _INLINE_PREFERRED_PATTERNS:
        for match in re.finditer(pattern, text_norm):
            start = max(0, match.start() - window_chars)
            end = min(len(text_norm), match.end() + 40)
            context = text_norm[start:end]
            if _appears_in_span(skill, context):
                return True
    return False


def extract_skills_deterministic(job_text: str) -> Dict[str, List[str]]:
    text_norm = _normalize_text(job_text)
    if not text_norm:
        return {"required_skills": [], "preferred_skills": [], "all_skills": []}

    spans = _build_section_spans(text_norm)

    required_candidates: List[str] = []
    preferred_candidates: List[str] = []

    for start, end in spans["required"]:
        required_candidates.extend(_extract_known_skills_from_span(text_norm[start:end]))

    for start, end in spans["preferred"]:
        preferred_candidates.extend(_extract_known_skills_from_span(text_norm[start:end]))

    # inline preferred overrides from anywhere
    for skill in _SORTED_CANONICAL_SKILLS:
        if _appears_in_inline_preferred_context(skill, text_norm):
            preferred_candidates.append(skill)

    required_skills = normalize_extracted_skills(required_candidates, text_norm)
    preferred_skills = normalize_extracted_skills(preferred_candidates, text_norm)

    preferred_skills = [s for s in preferred_skills if s not in set(required_skills)]

    all_skills: List[str] = []
    seen = set()
    for skill in required_skills + preferred_skills:
        if skill not in seen:
            seen.add(skill)
            all_skills.append(skill)

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
    }


def extract_skills_hybrid(job_text: str) -> Dict[str, List[str]]:
    """
    Deterministic sectioning is source of truth.
    Groq only adds recall when the candidate appears inside an explicit required/preferred span.
    """
    text_norm = _normalize_text(job_text)
    if not text_norm:
        return {"required_skills": [], "preferred_skills": [], "all_skills": []}

    det = extract_skills_deterministic(job_text)
    groq = enrich_skills_with_llm(job_text)

    spans = _build_section_spans(text_norm)
    required_spans = [text_norm[s:e] for s, e in spans["required"]]
    preferred_spans = [text_norm[s:e] for s, e in spans["preferred"]]

    req = set(det["required_skills"])
    pref = set(det["preferred_skills"])

    groq_candidates = (groq.get("required_skills", []) or []) + (groq.get("preferred_skills", []) or [])
    groq_candidates = normalize_extracted_skills(groq_candidates, text_norm)
    groq_candidates = [s for s in groq_candidates if _is_extraction_safe_skill(s)]

    for skill in groq_candidates:
        if skill in req or skill in pref:
            continue

        in_required = any(_appears_in_span(skill, span) for span in required_spans)
        in_preferred = any(_appears_in_span(skill, span) for span in preferred_spans)
        inline_pref = _appears_in_inline_preferred_context(skill, text_norm)

        if in_required and not inline_pref:
            req.add(skill)
        elif in_preferred or inline_pref:
            pref.add(skill)

    pref = {s for s in pref if s not in req}

    required_skills = sorted(req)
    preferred_skills = sorted(pref)
    all_skills = required_skills + [s for s in preferred_skills if s not in req]

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
    }


def _pick_benchmark_sample(rows: List[dict], limit: int) -> List[dict]:
    chosen: List[dict] = []
    seen = set()

    for company, title in _DEFAULT_TARGETS:
        row = next((r for r in rows if (r.get("company"), r.get("title")) == (company, title)), None)
        if row is not None:
            key = (row.get("company"), row.get("title"), row.get("job_doc_id"))
            if key not in seen:
                chosen.append(row)
                seen.add(key)

    remaining = [r for r in rows if (r.get("company"), r.get("title"), r.get("job_doc_id")) not in seen]
    remaining.sort(key=lambda r: len(r.get("description") or ""), reverse=True)

    for row in remaining:
        if len(chosen) >= limit:
            break
        key = (row.get("company"), row.get("title"), row.get("job_doc_id"))
        if key not in seen:
            chosen.append(row)
            seen.add(key)

    return chosen[:limit]


def build_gold_template(job_corpus: Path, out_path: Path, limit: int) -> None:
    rows = _load_jsonl(job_corpus)
    sample = _pick_benchmark_sample(rows, limit=limit)

    out_rows = []
    for row in sample:
        out_rows.append(
            {
                "company": row.get("company", ""),
                "title": row.get("title", ""),
                "job_doc_id": row.get("job_doc_id", ""),
                "description": row.get("description", ""),
                "gold_required_skills": [],
                "gold_preferred_skills": [],
            }
        )

    _write_jsonl(out_path, out_rows)
    print(f"Wrote gold template: {out_path}")
    print(f"rows={len(out_rows)}")


def _set_metrics(pred: set, gold: set) -> Tuple[int, int, int]:
    tp = len(pred & gold)
    return tp, len(pred), len(gold)


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if p and r else 0.0


def evaluate_against_gold(gold_path: Path) -> None:
    gold_rows = _load_jsonl(gold_path)

    systems = {
        "deterministic": extract_skills_deterministic,
        "groq_first": enrich_skills_with_llm,
        "hybrid": extract_skills_hybrid,
    }

    summary = {
        name: {
            "overall_tp": 0,
            "overall_pred": 0,
            "overall_gold": 0,
            "req_tp": 0,
            "req_pred": 0,
            "req_gold": 0,
            "pref_tp": 0,
            "pref_pred": 0,
            "pref_gold": 0,
            "bucket_correct": 0,
            "bucket_matched": 0,
        }
        for name in systems
    }

    for row in gold_rows:
        company = row.get("company", "")
        title = row.get("title", "")
        description = row.get("description", "") or ""

        gold_req = set(normalize_extracted_skills(row.get("gold_required_skills", []) or [], _normalize_text(description)))
        gold_pref = set(normalize_extracted_skills(row.get("gold_preferred_skills", []) or [], _normalize_text(description)))
        gold_all = gold_req | gold_pref

        print("\n" + "=" * 140)
        print(f"{company} | {title}")
        print("=" * 140)

        for name, fn in systems.items():
            pred = fn(description)
            pred_req = set(pred.get("required_skills", []) or [])
            pred_pref = set(pred.get("preferred_skills", []) or [])
            pred_all = pred_req | pred_pref

            overall_tp, overall_pred, overall_gold = _set_metrics(pred_all, gold_all)
            req_tp, req_pred, req_gold = _set_metrics(pred_req, gold_req)
            pref_tp, pref_pred, pref_gold = _set_metrics(pred_pref, gold_pref)

            matched = pred_all & gold_all
            bucket_correct = 0
            for skill in matched:
                if skill in pred_req and skill in gold_req:
                    bucket_correct += 1
                elif skill in pred_pref and skill in gold_pref:
                    bucket_correct += 1

            summary[name]["overall_tp"] += overall_tp
            summary[name]["overall_pred"] += overall_pred
            summary[name]["overall_gold"] += overall_gold
            summary[name]["req_tp"] += req_tp
            summary[name]["req_pred"] += req_pred
            summary[name]["req_gold"] += req_gold
            summary[name]["pref_tp"] += pref_tp
            summary[name]["pref_pred"] += pref_pred
            summary[name]["pref_gold"] += pref_gold
            summary[name]["bucket_correct"] += bucket_correct
            summary[name]["bucket_matched"] += len(matched)

            print(f"\n[{name}]")
            print(json.dumps(pred, indent=2))

            missed = sorted(gold_all - pred_all)
            extra = sorted(pred_all - gold_all)
            if missed:
                print(f"missed={missed}")
            if extra:
                print(f"extra={extra}")

    print("\n" + "#" * 140)
    print("SUMMARY")
    print("#" * 140)

    for name, m in summary.items():
        overall_p = _safe_div(m["overall_tp"], m["overall_pred"])
        overall_r = _safe_div(m["overall_tp"], m["overall_gold"])
        overall_f1 = _f1(overall_p, overall_r)

        req_p = _safe_div(m["req_tp"], m["req_pred"])
        req_r = _safe_div(m["req_tp"], m["req_gold"])
        req_f1 = _f1(req_p, req_r)

        pref_p = _safe_div(m["pref_tp"], m["pref_pred"])
        pref_r = _safe_div(m["pref_tp"], m["pref_gold"])
        pref_f1 = _f1(pref_p, pref_r)

        bucket_acc = _safe_div(m["bucket_correct"], m["bucket_matched"])

        print("\n" + "-" * 100)
        print(name)
        print("-" * 100)
        print(f"overall_precision={overall_p:.3f}")
        print(f"overall_recall={overall_r:.3f}")
        print(f"overall_f1={overall_f1:.3f}")
        print(f"required_precision={req_p:.3f}")
        print(f"required_recall={req_r:.3f}")
        print(f"required_f1={req_f1:.3f}")
        print(f"preferred_precision={pref_p:.3f}")
        print(f"preferred_recall={pref_r:.3f}")
        print(f"preferred_f1={pref_f1:.3f}")
        print(f"bucket_accuracy_on_matched_skills={bucket_acc:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark deterministic vs Groq-first skill extraction.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    sample_parser = subparsers.add_parser("sample")
    sample_parser.add_argument("--job-corpus", default="data/rag/job_corpus.jsonl")
    sample_parser.add_argument("--out", default="outputs/skill_extraction_gold_template.jsonl")
    sample_parser.add_argument("--limit", type=int, default=20)

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument("--gold", required=True)

    args = parser.parse_args()

    if args.mode == "sample":
        build_gold_template(
            job_corpus=Path(args.job_corpus),
            out_path=Path(args.out),
            limit=args.limit,
        )
    elif args.mode == "eval":
        evaluate_against_gold(Path(args.gold))


if __name__ == "__main__":
    main()
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

from src.config.consts import (
    REQUIRED_CONTEXT_PATTERNS,
    PREFERRED_CONTEXT_PATTERNS,
)
from src.utils.skill_normalizer import (
    KNOWN_CANONICAL_SKILLS,
    normalize_extracted_skills,
)

# Small, local patterns for deterministic sectioning.
# Keep this focused and explicit.
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

# Sort longer skills first so multi-word matches win before shorter overlapping terms.
_SORTED_CANONICAL_SKILLS = sorted(KNOWN_CANONICAL_SKILLS, key=lambda s: (-len(s), s))


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _find_headers(text_norm: str) -> List[Tuple[int, int, str, str]]:
    headers: List[Tuple[int, int, str, str]] = []

    for pattern in _REQUIRED_HEADERS:
        for match in re.finditer(pattern, text_norm):
            headers.append((match.start(), match.end(), "required", pattern))

    for pattern in _PREFERRED_HEADERS:
        for match in re.finditer(pattern, text_norm):
            headers.append((match.start(), match.end(), "preferred", pattern))

    headers.sort(key=lambda x: x[0])
    return headers


def _build_section_spans(text_norm: str) -> Dict[str, List[Tuple[int, int, str]]]:
    """
    Build explicit section spans only from strong required/preferred headers.
    Body text is everything else.
    """
    headers = _find_headers(text_norm)
    spans = {"required": [], "preferred": [], "body": []}

    if not headers:
        spans["body"].append((0, len(text_norm), "body"))
        return spans

    cursor = 0
    for idx, (start, _end, bucket, _pattern) in enumerate(headers):
        if cursor < start:
            spans["body"].append((cursor, start, "body"))

        next_start = headers[idx + 1][0] if idx + 1 < len(headers) else len(text_norm)
        spans[bucket].append((start, next_start, bucket))
        cursor = next_start

    if cursor < len(text_norm):
        spans["body"].append((cursor, len(text_norm), "body"))

    return spans


def _skill_regex(skill: str) -> re.Pattern:
    return re.compile(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])")


def _extract_known_skills_from_span(span_text: str) -> List[str]:
    matches: List[str] = []
    for skill in _SORTED_CANONICAL_SKILLS:
        if _skill_regex(skill).search(span_text):
            matches.append(skill)
    return matches


def _extract_inline_preferred_skills(text_norm: str, window_chars: int = 220) -> List[str]:
    """
    Catch phrases like:
      - 'Scala ... is a plus'
      - 'AWS Athena is a plus'
    without letting broad body text become required.
    """
    found: List[str] = []

    for pattern in _INLINE_PREFERRED_PATTERNS:
        for match in re.finditer(pattern, text_norm):
            start = max(0, match.start() - window_chars)
            end = min(len(text_norm), match.end() + 40)
            context = text_norm[start:end]
            found.extend(_extract_known_skills_from_span(context))

    return found


def extract_skills_deterministic(job_text: str) -> Dict[str, List[str]]:
    text_norm = _normalize_text(job_text)
    if not text_norm:
        return {
            "required_skills": [],
            "preferred_skills": [],
            "all_skills": [],
        }

    spans = _build_section_spans(text_norm)

    required_candidates: List[str] = []
    preferred_candidates: List[str] = []

    for start, end, _bucket in spans["required"]:
        required_candidates.extend(_extract_known_skills_from_span(text_norm[start:end]))

    for start, end, _bucket in spans["preferred"]:
        preferred_candidates.extend(_extract_known_skills_from_span(text_norm[start:end]))

    # Inline preferred override from anywhere in the JD.
    preferred_candidates.extend(_extract_inline_preferred_skills(text_norm))

    required_skills = normalize_extracted_skills(required_candidates, text_norm)
    preferred_skills = normalize_extracted_skills(preferred_candidates, text_norm)

    # Required wins if present in both.
    preferred_skills = [s for s in preferred_skills if s not in set(required_skills)]

    all_skills = []
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


def _load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Deterministic JD skill extractor baseline.")
    parser.add_argument("--job-corpus", default="data/rag/job_corpus.jsonl")
    parser.add_argument("--company-contains", default="")
    parser.add_argument("--title-contains", default="")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    rows = _load_jsonl(Path(args.job_corpus))

    company_needle = _normalize_text(args.company_contains)
    title_needle = _normalize_text(args.title_contains)

    filtered = rows
    if company_needle:
        filtered = [r for r in filtered if company_needle in _normalize_text(r.get("company", ""))]
    if title_needle:
        filtered = [r for r in filtered if title_needle in _normalize_text(r.get("title", ""))]

    filtered = filtered[: args.limit]

    for row in filtered:
        print("\n" + "=" * 120)
        print(f"{row.get('company')} | {row.get('title')}")
        print("=" * 120)
        result = extract_skills_deterministic(row.get("description", "") or "")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
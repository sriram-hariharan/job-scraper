import re
from typing import Dict, List, Tuple

from src.ai.skill_llm_enricher import enrich_skills_with_llm
from src.utils.skill_normalizer import KNOWN_CANONICAL_SKILLS, normalize_extracted_skills
from src.config.consts import REQUIRED_CONTEXT_PATTERNS, PREFERRED_CONTEXT_PATTERNS

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

    body_candidates: List[str] = []
    for start, end in spans["body"]:
        body_candidates.extend(_extract_known_skills_from_span(text_norm[start:end]))

    for skill in _SORTED_CANONICAL_SKILLS:
        if _appears_in_inline_preferred_context(skill, text_norm):
            preferred_candidates.append(skill)

    required_skills = normalize_extracted_skills(required_candidates, text_norm)
    preferred_skills = normalize_extracted_skills(preferred_candidates, text_norm)
    preferred_skills = [s for s in preferred_skills if s not in set(required_skills)]

    body_skills = normalize_extracted_skills(body_candidates, text_norm)
    body_skills = [
        s for s in body_skills
        if s not in set(required_skills) and s not in set(preferred_skills)
    ]

    all_skills: List[str] = []
    seen = set()
    for skill in required_skills + preferred_skills + body_skills:
        if skill not in seen:
            seen.add(skill)
            all_skills.append(skill)

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
    }


def extract_skills_hybrid(job_text: str) -> Dict[str, List[str]]:
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
    det_body_only = [
        s for s in det.get("all_skills", [])
        if s not in req and s not in pref
    ]

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

    all_skills = []
    seen = set()

    for skill in required_skills + preferred_skills + det_body_only:
        if skill not in seen:
            seen.add(skill)
            all_skills.append(skill)

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
    }
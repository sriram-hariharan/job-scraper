import re
from typing import List, Set, Tuple

from src.matching.job_models import JobEvidence
from src.matching.models import MatchPrefilterResult
from src.resume.models import ResumeEvidence

from src.config.consts import (
    ROLE_WORD_HINTS,
    TITLE_CANONICAL,
    TITLE_NOISE_TOKENS,
    _SKILL_ALIASES,
)

_VARIANT_TITLE_ABBREVIATIONS = {
    "ai": "ai engineer",
    "mle": "machine learning engineer",
    "ml": "machine learning engineer",
    "ds": "data scientist",
    "da": "data analyst",
    "ae": "analytics engineer",
}


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


def _normalized_tokens(value: str) -> Set[str]:
    normalized = _normalize_text(value)
    tokens = {token for token in normalized.split() if token and token not in TITLE_NOISE_TOKENS}
    return tokens


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


def _looks_roleish(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(
        re.search(rf"\b{re.escape(word)}\b", normalized)
        for word in ROLE_WORD_HINTS
    )


def _resume_name_title_candidates(resume_name: str) -> List[str]:
    stem = re.sub(r"\.[^.]+$", "", str(resume_name or ""))
    raw_tokens = [token for token in re.split(r"[^A-Za-z0-9]+", stem) if token]

    if not raw_tokens:
        return []

    tokens: List[str] = []
    for token in raw_tokens:
        token_norm = _normalize_text(re.sub(r"\d+$", "", token))
        if not token_norm:
            continue
        if re.fullmatch(r"v\d*", token_norm):
            continue
        tokens.append(token_norm)

    if not tokens:
        return []

    if "resume" in tokens:
        start = max(idx for idx, token in enumerate(tokens) if token == "resume") + 1
        candidate_tokens = tokens[start:]
    else:
        start = next(
            (
                idx for idx, token in enumerate(tokens)
                if token in _VARIANT_TITLE_ABBREVIATIONS or _looks_roleish(token)
            ),
            len(tokens),
        )
        candidate_tokens = tokens[start:]

    if len(candidate_tokens) < 2:
        return []

    phrase = " ".join(
        _VARIANT_TITLE_ABBREVIATIONS.get(token, token)
        for token in candidate_tokens
    ).strip()

    if not phrase or not _looks_roleish(phrase):
        return []

    title_tokens = [
        token
        for token in _normalize_text(phrase).split()
        if token and token not in TITLE_NOISE_TOKENS
    ]
    if len(title_tokens) < 2:
        return []

    return [phrase]


def _resume_header_title_candidates(raw_text: str) -> List[str]:
    lines = [line.strip() for line in str(raw_text or "").splitlines() if line.strip()]
    candidates: List[str] = []

    for line in lines[:10]:
        normalized = _normalize_text(line)

        if not normalized or len(normalized) > 80:
            continue

        if (
            "@" in line
            or "linkedin" in normalized
            or "github" in normalized
            or "http" in normalized
            or "www" in normalized
        ):
            continue

        if re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", line):
            continue

        if _looks_roleish(line):
            candidates.append(line)

    return _unique_preserve_order(candidates)


def _resume_variant_titles(resume: ResumeEvidence) -> List[str]:
    return _unique_preserve_order(
        _resume_header_title_candidates(resume.document.raw_text)
        + _resume_name_title_candidates(resume.document.resume_name)
    )

def _title_similarity(left: str, right: str) -> float:
    left_norm = _normalize_text(left)
    right_norm = _normalize_text(right)

    if not left_norm or not right_norm:
        return 0.0

    if left_norm == right_norm:
        return 1.0

    left_tokens = _normalized_tokens(left_norm)
    right_tokens = _normalized_tokens(right_norm)
    if not left_tokens or not right_tokens:
        return 0.0

    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    if not union:
        return 0.0

    return intersection / union

def _job_title_tokens(job: JobEvidence) -> Set[str]:
    return _normalized_tokens(job.title)

def _is_data_science_like_job(job: JobEvidence) -> bool:
    tokens = _job_title_tokens(job)
    return bool(tokens & {"data", "scientist", "analytics", "analyst", "research", "statistician"})

def _best_resume_title_match(resume: ResumeEvidence, job: JobEvidence) -> Tuple[float, str]:
    candidates = _unique_preserve_order(
        _resume_variant_titles(resume)
        + list(resume.titles)
        + [entry.title for entry in resume.experience_entries if entry.title]
    )

    best_score = 0.0
    best_title = ""

    for title in candidates:
        score = _title_similarity(title, job.title)
        if score > best_score:
            best_score = score
            best_title = title

    return best_score, best_title


def _build_resume_explicit_skill_set(resume: ResumeEvidence) -> Set[str]:
    skill_values: List[str] = []

    for entry in resume.experience_entries:
        skill_values.extend(entry.normalized_skills)

    return {
        _normalize_text(value)
        for value in skill_values
        if _normalize_text(value)
    }


def _normalized_skill_list(values: List[str]) -> List[str]:
    return _unique_preserve_order([
        _normalize_text(value)
        for value in values
        if _normalize_text(value)
    ])

def run_prefilter(
    resume: ResumeEvidence,
    job: JobEvidence,
) -> MatchPrefilterResult:
    best_title_score, best_title = _best_resume_title_match(resume, job)
    resume_explicit_skill_set = _build_resume_explicit_skill_set(resume)

    required_skills = _normalized_skill_list(job.required_skills)
    preferred_skills = _normalized_skill_list(job.preferred_skills)
    all_skills = _normalized_skill_list(job.all_skills)

    matched_required = [skill for skill in required_skills if skill in resume_explicit_skill_set]
    matched_preferred = [skill for skill in preferred_skills if skill in resume_explicit_skill_set]
    matched_any = [skill for skill in all_skills if skill in resume_explicit_skill_set]

    matched_terms: List[str] = []
    if best_title and best_title_score >= 0.45:
        matched_terms.append(best_title)
    matched_terms.extend(matched_required)
    matched_terms.extend(matched_preferred)
    if not matched_terms:
        matched_terms.extend(matched_any)
    matched_terms = _unique_preserve_order(matched_terms)

    missing_requirements = [skill for skill in required_skills if skill not in resume_explicit_skill_set]

    reasons: List[str] = []
    failed_reasons: List[str] = []

    minimum_overlap_passed = False
    if best_title_score >= 0.80 and len(matched_any) >= 2:
        minimum_overlap_passed = True
    elif best_title_score >= 0.80 and _is_data_science_like_job(job) and len(matched_any) >= 1:
        minimum_overlap_passed = True
    elif best_title_score >= 0.45 and len(matched_any) >= 3:
        minimum_overlap_passed = True
    elif (
        best_title_score >= 0.40
        and required_skills
        and len(matched_required) >= 2
        and (len(matched_required) / len(required_skills)) >= 0.25
    ):
        minimum_overlap_passed = True
    elif len(required_skills) <= 2 and required_skills and len(matched_required) == len(required_skills) and len(matched_any) >= 3:
        minimum_overlap_passed = True
    elif len(matched_required) >= 3:
        minimum_overlap_passed = True

    if minimum_overlap_passed:
        reasons.append(
            f"Minimum overlap passed: best_title_score={best_title_score:.2f}, "
            f"matched_skills={len(matched_any)}, matched_required={len(matched_required)}."
        )
    else:
        failed_reasons.append(
            "Failed minimum overlap: title alignment and skill overlap are too weak for deterministic scoring."
        )

    required_coverage = (
        len(matched_required) / len(required_skills)
        if required_skills
        else 0.0
    )
    if len(required_skills) >= 10 and required_coverage < 0.30 and len(matched_required) < 4:
        failed_reasons.append(
            f"Failed required-skill floor: matched {len(matched_required)}/{len(required_skills)} required skills."
        )
    elif 6 <= len(required_skills) < 10 and required_coverage < 0.25:
        failed_reasons.append(
            f"Failed required-skill floor: matched {len(matched_required)}/{len(required_skills)} required skills."
        )
    elif 3 <= len(required_skills) < 6 and len(matched_required) < 2:
        failed_reasons.append(
            f"Failed required-skill floor: matched {len(matched_required)}/{len(required_skills)} required skills."
        )
    elif required_skills:
        reasons.append(
            f"Required-skill coverage passed: matched {len(matched_required)}/{len(required_skills)} required skills."
        )
    else:
        reasons.append("Required-skill coverage skipped: job has no explicit required skills.")
    
    reasons.append("Seniority is reserved for manual review and is not used in automated prefiltering.")

    passed = not failed_reasons
    combined_reasons = reasons if passed else reasons + failed_reasons

    return MatchPrefilterResult(
        passed=passed,
        reasons=combined_reasons,
        matched_terms=matched_terms,
        missing_requirements=missing_requirements,
        best_title_score=best_title_score,
        best_title=best_title,
        matched_required_terms=matched_required,
        matched_preferred_terms=matched_preferred,
        matched_any_terms=matched_any,
        matched_required_count=len(matched_required),
        matched_preferred_count=len(matched_preferred),
        matched_any_count=len(matched_any),
    )
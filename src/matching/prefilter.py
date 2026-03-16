import re
from typing import List, Set, Tuple

from src.config.consts import TITLE_CANONICAL
from src.matching.job_models import JobEvidence
from src.matching.models import MatchPrefilterResult
from src.resume.models import ResumeEvidence

from src.config.consts import (
    _SKILL_ALIASES,
    _SKILL_ALIASES,
    TITLE_CANONICAL,
    TITLE_NOISE_TOKENS,
)


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


def _best_resume_title_match(resume: ResumeEvidence, job: JobEvidence) -> Tuple[float, str]:
    candidates = _unique_preserve_order(resume.titles)
    if not candidates:
        candidates = [entry.title for entry in resume.experience_entries if entry.title]

    best_score = 0.0
    best_title = ""

    for title in candidates:
        score = _title_similarity(title, job.title)
        if score > best_score:
            best_score = score
            best_title = title

    return best_score, best_title


def _build_resume_skill_set(resume: ResumeEvidence) -> Set[str]:
    skill_values: List[str] = []
    skill_values.extend(resume.skills)
    skill_values.extend(resume.tooling_signals)
    skill_values.extend(resume.analytics_ml_signals)
    skill_values.extend(resume.experimentation_signals)

    for entry in resume.experience_entries:
        skill_values.extend(entry.normalized_skills)

    for entry in resume.project_entries:
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
    resume_skill_set = _build_resume_skill_set(resume)

    required_skills = _normalized_skill_list(job.required_skills)
    preferred_skills = _normalized_skill_list(job.preferred_skills)
    all_skills = _normalized_skill_list(job.all_skills)

    matched_required = [skill for skill in required_skills if skill in resume_skill_set]
    matched_preferred = [skill for skill in preferred_skills if skill in resume_skill_set]
    matched_any = [skill for skill in all_skills if skill in resume_skill_set]

    matched_terms: List[str] = []
    if best_title and best_title_score >= 0.45:
        matched_terms.append(best_title)
    matched_terms.extend(matched_required)
    matched_terms.extend(matched_preferred)
    if not matched_terms:
        matched_terms.extend(matched_any)
    matched_terms = _unique_preserve_order(matched_terms)

    missing_requirements = [skill for skill in required_skills if skill not in resume_skill_set]

    reasons: List[str] = []
    failed_reasons: List[str] = []

    minimum_overlap_passed = False
    if best_title_score >= 0.80 and len(matched_any) >= 2:
        minimum_overlap_passed = True
    elif best_title_score >= 0.45 and len(matched_any) >= 3:
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
    )
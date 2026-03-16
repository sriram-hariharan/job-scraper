import re
from typing import Callable, Dict, List, Set

from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    DOMAIN_SIGNAL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    TITLE_CANONICAL,
    TITLE_NOISE_TOKENS,
    TOOLING_SIGNAL_PATTERNS,
    _ANALYTICS_ML_GENERIC_SIGNALS,
    _ANALYTICS_ML_SIGNAL_CANONICAL,
    _SKILL_ALIASES,
)
from src.matching.dimensions import get_match_dimensions
from src.matching.job_models import JobEvidence
from src.matching.models import (
    MatchDimensionDefinition,
    MatchDimensionScore,
    MatchPrefilterResult,
    ResumeJobMatchResult,
    ResumeJobPair,
)
from src.matching.prefilter import run_prefilter
from src.resume.models import ResumeEvidence


_UNIMPLEMENTED_DIMENSIONS = set()


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


def _canonicalize_signal(signal: str, canonical_map: Dict[str, str]) -> str:
    normalized = _normalize_text(signal)
    return canonical_map.get(normalized, normalized)


def _canonicalize_signals(values: List[str], canonical_map: Dict[str, str]) -> List[str]:
    return _unique_preserve_order(
        [_canonicalize_signal(value, canonical_map) for value in values if _canonicalize_signal(value, canonical_map)]
    )


def _resume_skill_set(resume: ResumeEvidence) -> Set[str]:
    values: List[str] = []
    values.extend(resume.skills)
    values.extend(resume.tooling_signals)
    values.extend(resume.analytics_ml_signals)
    values.extend(resume.experimentation_signals)
    values.extend(resume.domain_signals)

    for entry in resume.experience_entries:
        values.extend(entry.normalized_skills)

    for entry in resume.project_entries:
        values.extend(entry.normalized_skills)

    return {_normalize_text(value) for value in values if _normalize_text(value)}


def _resume_explicit_skill_set(resume: ResumeEvidence) -> Set[str]:
    values: List[str] = []
    values.extend(resume.skills)

    for entry in resume.experience_entries:
        values.extend(entry.normalized_skills)

    for entry in resume.project_entries:
        values.extend(entry.normalized_skills)

    return {_normalize_text(value) for value in values if _normalize_text(value)}


def _title_tokens(value: str) -> Set[str]:
    return {
        token
        for token in _normalize_text(value).split()
        if token and token not in TITLE_NOISE_TOKENS
    }


def _title_similarity(left: str, right: str) -> float:
    left_norm = _normalize_text(left)
    right_norm = _normalize_text(right)

    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0

    left_tokens = _title_tokens(left_norm)
    right_tokens = _title_tokens(right_norm)
    if not left_tokens or not right_tokens:
        return 0.0

    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    if not union:
        return 0.0

    return intersection / union


def _resume_titles(resume: ResumeEvidence) -> List[str]:
    titles = list(resume.titles)
    titles.extend(entry.title for entry in resume.experience_entries if entry.title)
    return _unique_preserve_order(titles)


def _contains_signal(text: str, signal: str) -> bool:
    return re.search(rf"\b{re.escape(_normalize_text(signal))}\b", text) is not None


def _job_signal_hits(
    job: JobEvidence,
    patterns: List[str],
    *,
    include_retrieval_text: bool,
) -> List[str]:
    parts = [
        job.title,
        job.role_family,
        " ".join(job.required_skills),
        " ".join(job.preferred_skills),
        " ".join(job.all_skills),
    ]

    if include_retrieval_text:
        parts.extend([job.preview, job.retrieval_text])

    job_text_norm = _normalize_text(" ".join(parts))
    return [pattern for pattern in patterns if _contains_signal(job_text_norm, pattern)]


def _project_signal_hits(project_text: str, patterns: List[str]) -> List[str]:
    project_text_norm = _normalize_text(project_text)
    return [pattern for pattern in patterns if _contains_signal(project_text_norm, pattern)]


def _explicit_signal_hits(values: Set[str], patterns: List[str]) -> List[str]:
    normalized_values = {_normalize_text(value) for value in values if _normalize_text(value)}

    hits: List[str] = []
    for pattern in patterns:
        if any(_contains_signal(value, pattern) for value in normalized_values):
            hits.append(pattern)

    return hits


def _prune_generic_analytics_signals(signals: List[str]) -> List[str]:
    ordered = _unique_preserve_order(signals)
    specific = [signal for signal in ordered if signal not in _ANALYTICS_ML_GENERIC_SIGNALS]
    return specific if specific else ordered


def _weighted_dimension(
    definition: MatchDimensionDefinition,
    score: float,
    reason: str,
    evidence: List[str],
) -> MatchDimensionScore:
    bounded_score = max(0.0, min(1.0, score))
    return MatchDimensionScore(
        name=definition.name,
        score=bounded_score,
        weight=definition.weight,
        weighted_score=round(bounded_score * definition.weight, 6),
        reason=reason,
        evidence=_unique_preserve_order(evidence),
    )


def _score_title_alignment(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    job: JobEvidence,
) -> MatchDimensionScore:
    best_score = 0.0
    best_title = ""

    for title in _resume_titles(resume):
        similarity = _title_similarity(title, job.title)
        if similarity > best_score:
            best_score = similarity
            best_title = title

    if not best_title:
        return _weighted_dimension(
            definition,
            0.0,
            "No resume titles were extracted, so title alignment could not be established.",
            [],
        )

    return _weighted_dimension(
        definition,
        best_score,
        f"Best resume title match against the job title scored {best_score:.2f}.",
        [best_title, job.title],
    )


def _score_skill_alignment(
    definition: MatchDimensionDefinition,
    targets: List[str],
    resume_skill_set: Set[str],
    empty_reason: str,
) -> MatchDimensionScore:
    normalized_targets = _normalized_skill_list(targets)
    if not normalized_targets:
        return _weighted_dimension(definition, 0.5, empty_reason, [])

    matches = [skill for skill in normalized_targets if skill in resume_skill_set]
    coverage = len(matches) / len(normalized_targets)

    reason = (
        f"Matched {len(matches)}/{len(normalized_targets)} target skills."
        if matches
        else f"Matched 0/{len(normalized_targets)} target skills."
    )

    return _weighted_dimension(definition, coverage, reason, matches)


def _score_tooling_alignment(
    definition: MatchDimensionDefinition,
    resume_skill_set: Set[str],
    job: JobEvidence,
) -> MatchDimensionScore:
    tooling_targets = [
        skill
        for skill in _normalized_skill_list(job.required_skills + job.preferred_skills + job.all_skills)
        if skill in TOOLING_SIGNAL_PATTERNS
    ]

    if not tooling_targets:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no explicit tooling targets, so tooling alignment is neutral in v1.",
            [],
        )

    matches = [skill for skill in tooling_targets if skill in resume_skill_set]
    coverage = len(matches) / len(tooling_targets)
    return _weighted_dimension(
        definition,
        coverage,
        f"Matched {len(matches)}/{len(tooling_targets)} job tooling targets.",
        matches,
    )


def _score_signal_alignment(
    definition: MatchDimensionDefinition,
    resume_signals: List[str],
    job_signals: List[str],
    empty_reason: str,
) -> MatchDimensionScore:
    normalized_resume = {_normalize_text(signal) for signal in resume_signals if _normalize_text(signal)}
    normalized_job = _normalized_skill_list(job_signals)

    if not normalized_job:
        return _weighted_dimension(definition, 0.5, empty_reason, [])

    matches = [signal for signal in normalized_job if signal in normalized_resume]
    coverage = len(matches) / len(normalized_job)
    return _weighted_dimension(
        definition,
        coverage,
        f"Matched {len(matches)}/{len(normalized_job)} explicit job signals.",
        matches,
    )


def _score_analytics_ml_depth(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    resume_skill_set: Set[str],
    job_analytics_ml_signals: List[str],
) -> MatchDimensionScore:
    canonical_job = _prune_generic_analytics_signals(
        _canonicalize_signals(
            job_analytics_ml_signals,
            _ANALYTICS_ML_SIGNAL_CANONICAL,
        )
    )

    if not canonical_job:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no explicit analytics/ML signals, so analytics_ml_depth is neutral in v1.",
            [],
        )

    explicit_resume = set(
        _canonicalize_signals(
            _explicit_signal_hits(resume_skill_set, ANALYTICS_ML_SIGNAL_PATTERNS),
            _ANALYTICS_ML_SIGNAL_CANONICAL,
        )
    )
    inferred_resume = set(
        _canonicalize_signals(
            resume.analytics_ml_signals,
            _ANALYTICS_ML_SIGNAL_CANONICAL,
        )
    )

    explicit_matches = [signal for signal in canonical_job if signal in explicit_resume]
    inferred_only_matches = [
        signal
        for signal in canonical_job
        if signal not in explicit_resume and signal in inferred_resume
    ]

    explicit_coverage = len(explicit_matches) / len(canonical_job)
    inferred_total_coverage = (
        len(explicit_matches) + len(inferred_only_matches)
    ) / len(canonical_job)

    score = min(1.0, (0.8 * explicit_coverage) + (0.2 * inferred_total_coverage))
    evidence = _unique_preserve_order(explicit_matches + inferred_only_matches)

    return _weighted_dimension(
        definition,
        score,
        (
            f"Matched {len(explicit_matches)}/{len(canonical_job)} canonical job signals with explicit "
            f"resume skills, plus {len(inferred_only_matches)} additional inferred-only matches."
        ),
        evidence,
    )


def _score_project_relevance(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    job: JobEvidence,
    job_analytics_ml_signals: List[str],
    job_experimentation_signals: List[str],
) -> MatchDimensionScore:
    if not resume.project_entries:
        return _weighted_dimension(
            definition,
            0.5,
            "Resume has no project section evidence, so project relevance is neutral in v1.",
            [],
        )

    job_skill_targets = _normalized_skill_list(
        job.required_skills + job.preferred_skills + job.all_skills
    )
    canonical_job_analytics = _canonicalize_signals(
        job_analytics_ml_signals,
        _ANALYTICS_ML_SIGNAL_CANONICAL,
    )
    canonical_job_experimentation = _normalized_skill_list(job_experimentation_signals)

    best_score = 0.0
    best_reason = "Project section exists but no meaningful overlap was found."
    best_evidence: List[str] = []

    for entry in resume.project_entries:
        project_text = " ".join([entry.name] + entry.bullets).strip()

        project_skill_set = set(_normalized_skill_list(entry.normalized_skills))
        skill_matches = [skill for skill in job_skill_targets if skill in project_skill_set]
        skill_coverage = len(skill_matches) / len(job_skill_targets) if job_skill_targets else 0.0

        project_analytics_hits = _canonicalize_signals(
            _project_signal_hits(project_text, ANALYTICS_ML_SIGNAL_PATTERNS),
            _ANALYTICS_ML_SIGNAL_CANONICAL,
        )
        analytics_matches = [
            signal for signal in canonical_job_analytics if signal in set(project_analytics_hits)
        ]
        analytics_coverage = (
            len(analytics_matches) / len(canonical_job_analytics)
            if canonical_job_analytics else 0.0
        )

        project_experimentation_hits = _normalized_skill_list(
            _project_signal_hits(project_text, EXPERIMENTATION_SIGNAL_PATTERNS)
        )
        experimentation_matches = [
            signal for signal in canonical_job_experimentation if signal in set(project_experimentation_hits)
        ]
        experimentation_coverage = (
            len(experimentation_matches) / len(canonical_job_experimentation)
            if canonical_job_experimentation else 0.0
        )

        weighted_sum = 0.0
        total_weight = 0.0

        if job_skill_targets:
            weighted_sum += 0.60 * skill_coverage
            total_weight += 0.60

        if canonical_job_analytics:
            weighted_sum += 0.25 * analytics_coverage
            total_weight += 0.25

        if canonical_job_experimentation:
            weighted_sum += 0.15 * experimentation_coverage
            total_weight += 0.15

        if total_weight == 0.0:
            project_score = 0.5
            reason = "Job has no project-comparable targets, so project relevance is neutral in v1."
            evidence = []
        else:
            raw_project_score = weighted_sum / total_weight
            project_score = max(0.5, raw_project_score)
            evidence = _unique_preserve_order(
                skill_matches + analytics_matches + experimentation_matches
            )

            if raw_project_score < 0.5:
                reason = (
                    f"Project evidence is weak/coarse for this job, so project relevance stays neutral in v1. "
                    f"Best project matched {len(skill_matches)}/{len(job_skill_targets)} job skills, "
                    f"{len(analytics_matches)}/{len(canonical_job_analytics)} analytics/ML signals, "
                    f"and {len(experimentation_matches)}/{len(canonical_job_experimentation)} experimentation signals."
                )
            else:
                reason = (
                    f"Best project matched {len(skill_matches)}/{len(job_skill_targets)} job skills, "
                    f"{len(analytics_matches)}/{len(canonical_job_analytics)} analytics/ML signals, "
                    f"and {len(experimentation_matches)}/{len(canonical_job_experimentation)} experimentation signals."
                )

        if project_score > best_score:
            best_score = project_score
            best_reason = reason
            best_evidence = evidence

    return _weighted_dimension(
        definition,
        best_score,
        best_reason,
        best_evidence,
    )


def _neutral_unimplemented_dimension(definition: MatchDimensionDefinition) -> MatchDimensionScore:
    return _weighted_dimension(
        definition,
        0.5,
        "Neutral placeholder in v1 scorer skeleton; this dimension is not implemented yet.",
        [],
    )


def _skipped_dimension(definition: MatchDimensionDefinition, reason: str) -> MatchDimensionScore:
    return _weighted_dimension(definition, 0.0, reason, [])


def _match_bucket(final_score: float) -> str:
    if final_score >= 0.75:
        return "strong"
    if final_score >= 0.60:
        return "solid"
    if final_score >= 0.45:
        return "moderate"
    if final_score >= 0.30:
        return "weak"
    return "low"


def score_resume_job_match(
    resume: ResumeEvidence,
    job: JobEvidence,
    prefilter: MatchPrefilterResult | None = None,
) -> ResumeJobMatchResult:
    prefilter_result = prefilter or run_prefilter(resume, job)
    pair = ResumeJobPair(
        resume_id=resume.document.resume_id,
        resume_name=resume.document.resume_name,
        job_doc_id=job.job_doc_id,
        job_company=job.company,
        job_title=job.title,
    )

    dimensions = get_match_dimensions()
    if not prefilter_result.passed:
        skipped = [
            _skipped_dimension(dimension, "Scoring skipped because deterministic prefilter failed.")
            for dimension in dimensions
        ]
        return ResumeJobMatchResult(
            pair=pair,
            prefilter=prefilter_result,
            dimension_scores=skipped,
            final_score=0.0,
            match_bucket="filtered_out",
        )

    resume_skill_set = _resume_skill_set(resume)
    resume_explicit_skill_set = _resume_explicit_skill_set(resume)

    job_analytics_ml_signals = _job_signal_hits(
        job,
        ANALYTICS_ML_SIGNAL_PATTERNS,
        include_retrieval_text=False,
    )
    job_experimentation_signals = _job_signal_hits(
        job,
        EXPERIMENTATION_SIGNAL_PATTERNS,
        include_retrieval_text=True,
    )
    job_domain_signals = _job_signal_hits(
        job,
        DOMAIN_SIGNAL_PATTERNS,
        include_retrieval_text=False,
    )

    scorers: Dict[str, Callable[[MatchDimensionDefinition], MatchDimensionScore]] = {
        "title_alignment": lambda definition: _score_title_alignment(definition, resume, job),
        "required_skills_alignment": lambda definition: _score_skill_alignment(
            definition,
            job.required_skills,
            resume_skill_set,
            "Job has no explicit required-skill list, so required-skills alignment is neutral in v1.",
        ),
        "preferred_skills_alignment": lambda definition: _score_skill_alignment(
            definition,
            job.preferred_skills,
            resume_skill_set,
            "Job has no explicit preferred-skill list, so preferred-skills alignment is neutral in v1.",
        ),
        "analytics_ml_depth": lambda definition: _score_analytics_ml_depth(
            definition,
            resume,
            resume_explicit_skill_set,
            job_analytics_ml_signals,
        ),
        "tooling_alignment": lambda definition: _score_tooling_alignment(definition, resume_skill_set, job),
        "experimentation_depth": lambda definition: _score_signal_alignment(
            definition,
            resume.experimentation_signals,
            job_experimentation_signals,
            "Job has no explicit experimentation signals, so experimentation depth is neutral in v1.",
        ),
        "domain_relevance": lambda definition: _score_signal_alignment(
            definition,
            resume.domain_signals,
            job_domain_signals,
            "Job has no explicit domain signals, so domain relevance is neutral in v1.",
        ),
        "project_relevance": lambda definition: _score_project_relevance(
            definition,
            resume,
            job,
            job_analytics_ml_signals,
            job_experimentation_signals,
        ),
    }

    dimension_scores: List[MatchDimensionScore] = []
    for definition in dimensions:
        if definition.name in scorers:
            dimension_scores.append(scorers[definition.name](definition))
            continue

        if definition.name in _UNIMPLEMENTED_DIMENSIONS:
            dimension_scores.append(_neutral_unimplemented_dimension(definition))
            continue

        dimension_scores.append(
            _skipped_dimension(
                definition,
                "Dimension is not part of the v1 deterministic scorer skeleton.",
            )
        )

    final_score = round(sum(score.weighted_score for score in dimension_scores), 6)

    return ResumeJobMatchResult(
        pair=pair,
        prefilter=prefilter_result,
        dimension_scores=dimension_scores,
        final_score=final_score,
        match_bucket=_match_bucket(final_score),
    )
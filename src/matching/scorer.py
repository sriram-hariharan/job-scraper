import re
from typing import Callable, Dict, List, Set, Tuple

from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    BASELINE_FAMILIARITY_FAMILIES,
    CONTEXT_TOKEN_STOPWORDS,
    DOMAIN_SIGNAL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    QUERY_STOPWORDS,
    ROLE_WORD_HINTS,
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

_ANALYTICS_TITLE_TOKENS = {"analytics", "analyst", "bi", "insights"}
_DATA_TITLE_TOKENS = {"data", "scientist", "science"}
_ML_TITLE_TOKENS = {"ai", "ml", "machine", "learning"}
_VARIANT_TITLE_ABBREVIATIONS = {
    "ai": "ai engineer",
    "mle": "machine learning engineer",
    "ml": "machine learning engineer",
    "ds": "data scientist",
    "da": "data analyst",
    "ae": "analytics engineer",
}

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

    if not candidate_tokens:
        return []

    phrase_tokens = [_VARIANT_TITLE_ABBREVIATIONS.get(token, token) for token in candidate_tokens]
    phrase = " ".join(phrase_tokens).strip()

    if not phrase or not _looks_roleish(phrase):
        return []

    return [phrase]


def _resume_header_title_candidates(raw_text: str) -> List[str]:
    lines = [line.strip() for line in str(raw_text or "").splitlines() if line.strip()]
    candidates: List[str] = []

    for line in lines[:10]:
        normalized = _normalize_text(line)

        if not normalized or len(normalized) > 80:
            continue

        if "@" in line or "linkedin" in normalized or "github" in normalized or "http" in normalized or "www" in normalized:
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

def _role_family_title_adjustment(role_family: str, title: str) -> Tuple[float, List[str]]:
    role_family_norm = _normalize_text(role_family)
    title_tokens = _title_tokens(title)

    has_analytics = bool(title_tokens & _ANALYTICS_TITLE_TOKENS)
    has_data = bool(title_tokens & _DATA_TITLE_TOKENS)
    has_ml = bool(title_tokens & _ML_TITLE_TOKENS)
    has_engineer = "engineer" in title_tokens

    adjustment = 0.0
    reasons: List[str] = []

    if role_family_norm in {"analytics engineer", "data analyst", "analytics"}:
        if has_analytics:
            adjustment += 0.20
            reasons.append("analytics-family title bonus")
        elif has_data and has_engineer:
            adjustment += 0.10
            reasons.append("data-engineering adjacent title bonus")

        if has_ml and not has_analytics:
            adjustment -= 0.20
            reasons.append("analytics-family title mismatch penalty")

    elif role_family_norm in {"ml engineer", "machine learning engineer"}:
        if has_ml:
            adjustment += 0.20
            reasons.append("ml-family title bonus")

        if has_analytics and not has_ml:
            adjustment -= 0.20
            reasons.append("ml-family title mismatch penalty")

    elif role_family_norm == "data scientist":
        if "scientist" in title_tokens or "science" in title_tokens:
            adjustment += 0.15
            reasons.append("data-scientist title bonus")
        elif has_analytics:
            adjustment += 0.05
            reasons.append("analytics-adjacent title bonus")

        if has_ml and not has_data and "scientist" not in title_tokens and "science" not in title_tokens:
            adjustment -= 0.10
            reasons.append("pure-ml vs data-scientist title penalty")

    return adjustment, reasons

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

def _resume_explicit_skill_set(resume: ResumeEvidence) -> Set[str]:
    values: List[str] = []

    for entry in resume.experience_entries:
        values.extend(entry.normalized_skills)

    return {_normalize_text(value) for value in values if _normalize_text(value)}

def _resume_experience_workflow_set(resume: ResumeEvidence) -> Set[str]:
    values: List[str] = []

    for entry in resume.experience_entries:
        values.extend(entry.normalized_workflows)

    return {_normalize_text(value) for value in values if _normalize_text(value)}

def _resume_experience_business_context_set(resume: ResumeEvidence) -> Set[str]:
    values: List[str] = []

    for entry in resume.experience_entries:
        values.extend(entry.business_contexts)

    return {_normalize_text(value) for value in values if _normalize_text(value)}

def _resume_experience_stakeholder_context_set(resume: ResumeEvidence) -> Set[str]:
    values: List[str] = []

    for entry in resume.experience_entries:
        values.extend(entry.stakeholder_contexts)

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

def _phrase_fingerprint(value: str) -> str:
    normalized = _normalize_text(value).replace("-", " ").replace("/", " ")
    return re.sub(r"\s+", " ", normalized).strip()


def _resume_experience_segments(resume: ResumeEvidence) -> List[str]:
    segments: List[str] = []

    for entry in list(resume.experience_entries or []):
        context = " ".join(
            part for part in [entry.title, entry.company]
            if str(part or "").strip()
        ).strip()

        for bullet in list(entry.bullets or []):
            bullet_text = str(bullet or "").strip()
            if not bullet_text:
                continue

            segment = " ".join(part for part in [context, bullet_text] if part).strip()
            if segment:
                segments.append(segment)

    return segments

def _dynamic_overlap_terms(text: str) -> List[str]:
    stopwords = set(QUERY_STOPWORDS) | set(CONTEXT_TOKEN_STOPWORDS) | set(TITLE_NOISE_TOKENS)
    tokens = [token for token in _phrase_fingerprint(text).split() if token]

    kept: List[str] = []
    for token in tokens:
        if len(token) < 4:
            continue
        if token.isdigit():
            continue
        if token in stopwords:
            continue
        kept.append(token)

    return _unique_preserve_order(kept)

def _dynamic_job_body_text(job: JobEvidence) -> str:
    source_text = str(getattr(job, "retrieval_text", "") or "")
    if not source_text:
        source_text = str(getattr(job, "preview", "") or "")

    if not source_text.strip():
        return ""

    body = source_text

    match = re.search(r"job description:\s*", body, re.I)
    if match:
        body = body[match.end():]

    stop_patterns = [
        r"\bvisa sponsorship:\b",
        r"\bwhat['’]s in it for you\?\b",
        r"\bestimated salary\b",
        r"\bpay range\b",
        r"\bcandidate integrity policy\b",
        r"\bapplicant privacy notice\b",
    ]

    cut_index = len(body)
    for pattern in stop_patterns:
        stop_match = re.search(pattern, body, re.I)
        if stop_match:
            cut_index = min(cut_index, stop_match.start())

    body = body[:cut_index]

    responsibilities_match = re.search(r"\bresponsibilities\s*:", body, re.I)
    qualifications_match = re.search(
        r"\bwe['’]d love to chat if you have\s*:|\bwe would love to chat if you have\s*:",
        body,
        re.I,
    )

    extracted_sections: List[str] = []

    if responsibilities_match:
        start = responsibilities_match.end()
        end = qualifications_match.start() if qualifications_match else len(body)
        responsibilities_text = body[start:end].strip()
        if responsibilities_text:
            extracted_sections.append(responsibilities_text)

    if qualifications_match:
        qualifications_text = body[qualifications_match.end():].strip()
        if qualifications_text:
            extracted_sections.append(qualifications_text)

    if extracted_sections:
        body = " ".join(extracted_sections)

    return _normalize_text(body)

def _domain_relevance_job_text(job: JobEvidence, job_domain_signals: List[str]) -> str:
    business_contexts = _normalized_skill_list(getattr(job, "business_contexts", []))
    role_archetype = _normalize_text(getattr(job, "role_archetype", ""))

    parts = [
        job.title,
        job.role_family,
        role_archetype,
        " ".join(job_domain_signals),
        " ".join(business_contexts),
    ]

    return " ".join(
        part for part in parts
        if str(part or "").strip()
    )

def _dynamic_overlap_phrases(text: str) -> List[str]:
    tokens = _dynamic_overlap_terms(text)
    phrases: List[str] = []

    for size in (2, 3):
        for idx in range(len(tokens) - size + 1):
            phrase_tokens = tokens[idx: idx + size]
            if len(set(phrase_tokens)) < size:
                continue
            phrases.append(" ".join(phrase_tokens))

    return _unique_preserve_order(phrases)


def _dynamic_segment_overlap(
    segment_text: str,
    job_terms: List[str],
    job_phrases: List[str],
    *,
    target_count: int,
) -> Tuple[float, List[str], int]:
    if not str(segment_text or "").strip() or target_count <= 0:
        return 0.0, [], 0

    segment_terms = set(_dynamic_overlap_terms(segment_text))
    segment_phrases = set(_dynamic_overlap_phrases(segment_text))

    term_matches = [term for term in job_terms if term in segment_terms]
    phrase_matches = [phrase for phrase in job_phrases if phrase in segment_phrases]

    match_units = len(term_matches) + (2 * len(phrase_matches))
    coverage = min(1.0, match_units / target_count)
    evidence = _unique_preserve_order(phrase_matches + term_matches)

    return coverage, evidence, match_units

def _dynamic_job_resume_overlap(
    resume: ResumeEvidence,
    job_text: str,
) -> Tuple[float, List[str], int, int]:
    job_terms = _dynamic_overlap_terms(job_text)
    job_phrases = _dynamic_overlap_phrases(job_text)
    targets = _unique_preserve_order(job_terms + job_phrases)

    if len(targets) < 4:
        return 0.0, [], 0, len(targets)

    segments = _resume_experience_segments(resume)
    if not segments:
        return 0.0, [], 0, len(targets)

    segment_results: List[Tuple[float, int, List[str]]] = []

    for segment in segments:
        coverage, evidence, match_units = _dynamic_segment_overlap(
            segment,
            job_terms,
            job_phrases,
            target_count=len(targets),
        )
        if coverage <= 0.0 and match_units <= 0:
            continue
        segment_results.append((coverage, match_units, evidence))

    if not segment_results:
        return 0.0, [], 0, len(targets)

    segment_results.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )

    segment_weights = [0.40, 0.25, 0.15, 0.12, 0.08]
    weighted_coverage_sum = 0.0
    weight_used = 0.0
    combined_evidence: List[str] = []
    total_match_units = 0

    for idx, (coverage, match_units, evidence) in enumerate(segment_results[: len(segment_weights)]):
        weight = segment_weights[idx]
        weighted_coverage_sum += weight * coverage
        weight_used += weight
        total_match_units += match_units
        combined_evidence.extend(evidence)

    aggregated_coverage = (
        min(1.0, weighted_coverage_sum / weight_used)
        if weight_used > 0.0
        else 0.0
    )

    return (
        aggregated_coverage,
        _unique_preserve_order(combined_evidence),
        total_match_units,
        len(targets),
    )


def _score_domain_relevance(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    job: JobEvidence,
    job_domain_signals: List[str],
) -> MatchDimensionScore:
    normalized_resume = {
        _normalize_text(signal)
        for signal in resume.domain_signals
        if _normalize_text(signal)
    }
    normalized_job = _normalized_skill_list(job_domain_signals)

    static_matches = [signal for signal in normalized_job if signal in normalized_resume]
    static_coverage = len(static_matches) / len(normalized_job) if normalized_job else 0.0

    dynamic_job_text = _domain_relevance_job_text(job, normalized_job)
    dynamic_coverage, dynamic_evidence, dynamic_match_units, dynamic_target_count = _dynamic_job_resume_overlap(
        resume,
        dynamic_job_text,
    )

    normalized_business_contexts = _normalized_skill_list(getattr(job, "business_contexts", []))

    if not normalized_job and not normalized_business_contexts and dynamic_target_count < 4:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no explicit domain or business-context targets and no sufficiently specific dynamic domain targets, so domain relevance is neutral in v1.",
            [],
        )

    if normalized_job and dynamic_target_count >= 4:
        final_score = min(1.0, (0.35 * static_coverage) + (0.65 * dynamic_coverage))
        reason = (
            f"Matched {len(static_matches)}/{len(normalized_job)} explicit domain signals, plus "
            f"{dynamic_match_units} dynamic JD-context overlap units across {dynamic_target_count} runtime-extracted targets "
            f"from the JD body and resume experience bullets."
        )
        evidence = _unique_preserve_order(static_matches + dynamic_evidence)
        return _weighted_dimension(definition, final_score, reason, evidence)

    if normalized_job:
        return _weighted_dimension(
            definition,
            static_coverage,
            f"Matched {len(static_matches)}/{len(normalized_job)} explicit domain signals.",
            static_matches,
        )

    return _weighted_dimension(
        definition,
        dynamic_coverage,
        (
            f"Matched {dynamic_match_units} dynamic JD-context overlap units across "
            f"{dynamic_target_count} runtime-extracted targets from the JD body and resume experience bullets."
        ),
        dynamic_evidence,
    )

def _matched_experimentation_surfacing_bonus(
    resume: ResumeEvidence,
    job: JobEvidence,
    matched_signals: List[str],
) -> Tuple[float, List[str], str]:
    matched_signals = _normalized_skill_list(matched_signals)
    if not matched_signals:
        return 0.0, [], "No matched experimentation signals were eligible for surfacing bonus."

    job_text = " ".join(
        part
        for part in [
            job.title,
            job.role_family,
            " ".join(job.required_skills),
            " ".join(job.preferred_skills),
            " ".join(job.all_skills),
            _dynamic_job_body_text(job),
        ]
        if str(part or "").strip()
    )

    job_terms = _dynamic_overlap_terms(job_text)
    job_phrases = _dynamic_overlap_phrases(job_text)
    targets = _unique_preserve_order(job_terms + job_phrases)

    if len(targets) < 4:
        return 0.0, [], "JD context was too weak to evaluate experimentation surfacing bonus."

    best_coverage = 0.0
    best_match_units = 0
    best_segment_signals: List[str] = []
    best_evidence: List[str] = []

    for segment in _resume_experience_segments(resume):
        segment_norm = _normalize_text(segment)
        surfaced_signals = [
            signal for signal in matched_signals
            if _contains_signal(segment_norm, signal)
        ]
        if not surfaced_signals:
            continue

        coverage, evidence, match_units = _dynamic_segment_overlap(
            segment,
            job_terms,
            job_phrases,
            target_count=len(targets),
        )

        if coverage > best_coverage or (
            coverage == best_coverage and match_units > best_match_units
        ):
            best_coverage = coverage
            best_match_units = match_units
            best_segment_signals = surfaced_signals
            best_evidence = evidence

    if best_coverage <= 0.0 or not best_segment_signals:
        return 0.0, [], "Matched experimentation signals were not found inside a JD-aligned experience segment."

    bonus = min(0.02, best_coverage * 0.05)
    evidence = _unique_preserve_order(best_segment_signals + best_evidence)
    reason = (
        f"Added experimentation surfacing bonus {bonus:.4f} because {len(best_segment_signals)} "
        f"already-matched experimentation signal(s) appear inside a JD-aligned experience segment "
        f"(coverage={best_coverage:.4f}, match_units={best_match_units})."
    )
    return bonus, evidence, reason

def _score_experimentation_alignment(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    job: JobEvidence,
    job_experimentation_signals: List[str],
    empty_reason: str,
) -> MatchDimensionScore:
    normalized_resume = {
        _normalize_text(signal)
        for signal in resume.experimentation_signals
        if _normalize_text(signal)
    }
    normalized_job = _normalized_skill_list(job_experimentation_signals)

    if not normalized_job:
        return _weighted_dimension(definition, 0.5, empty_reason, [])

    matches = [signal for signal in normalized_job if signal in normalized_resume]
    coverage = len(matches) / len(normalized_job)

    surfacing_bonus, surfacing_evidence, surfacing_reason = _matched_experimentation_surfacing_bonus(
        resume,
        job,
        matches,
    )

    final_score = min(1.0, coverage + surfacing_bonus)
    evidence = _unique_preserve_order(matches + surfacing_evidence)

    reason = f"Matched {len(matches)}/{len(normalized_job)} explicit job signals."
    if surfacing_bonus > 0.0:
        reason += f" {surfacing_reason}"

    return _weighted_dimension(definition, final_score, reason, evidence)


def _matched_skill_surfacing_bonus(
    resume: ResumeEvidence,
    job: JobEvidence,
    matched_targets: List[str],
) -> Tuple[float, List[str], str]:
    matched_targets = _normalized_skill_list(matched_targets)
    if not matched_targets:
        return 0.0, [], "No explicit matched target skills were eligible for surfacing bonus."

    job_text = " ".join(
        part
        for part in [
            job.title,
            job.role_family,
            " ".join(job.required_skills),
            " ".join(job.preferred_skills),
            " ".join(job.all_skills),
            _dynamic_job_body_text(job),
        ]
        if str(part or "").strip()
    )

    job_terms = _dynamic_overlap_terms(job_text)
    job_phrases = _dynamic_overlap_phrases(job_text)
    targets = _unique_preserve_order(job_terms + job_phrases)

    if len(targets) < 4:
        return 0.0, [], "JD context was too weak to evaluate surfacing bonus."

    best_coverage = 0.0
    best_match_units = 0
    best_segment_targets: List[str] = []
    best_evidence: List[str] = []

    for segment in _resume_experience_segments(resume):
        segment_norm = _normalize_text(segment)
        surfaced_targets = [
            target for target in matched_targets
            if _contains_signal(segment_norm, target)
        ]
        if not surfaced_targets:
            continue

        coverage, evidence, match_units = _dynamic_segment_overlap(
            segment,
            job_terms,
            job_phrases,
            target_count=len(targets),
        )

        if coverage > best_coverage or (
            coverage == best_coverage and match_units > best_match_units
        ):
            best_coverage = coverage
            best_match_units = match_units
            best_segment_targets = surfaced_targets
            best_evidence = evidence

    if best_coverage <= 0.0 or not best_segment_targets:
        return 0.0, [], "Matched explicit target skills were not found inside a JD-aligned experience segment."

    bonus = min(0.02, best_coverage * 0.05)
    evidence = _unique_preserve_order(best_segment_targets)
    reason = (
        f"Added surfacing bonus {bonus:.4f} because {len(best_segment_targets)} already-matched "
        f"explicit target skill(s) appear inside a JD-aligned experience segment "
        f"(coverage={best_coverage:.4f}, match_units={best_match_units})."
    )
    return bonus, evidence, reason

def _job_baseline_family_targets(job: JobEvidence) -> Dict[str, List[str]]:
    job_targets = _normalized_skill_list(job.required_skills + job.preferred_skills + job.all_skills)
    family_targets: Dict[str, List[str]] = {}

    for family_name, family_config in BASELINE_FAMILIARITY_FAMILIES.items():
        job_terms = _normalized_skill_list(family_config.get("job_terms", []))
        matched_terms = [term for term in job_terms if term in job_targets]
        if matched_terms:
            family_targets[family_name] = matched_terms

    return family_targets


def _resume_baseline_family_support(
    resume: ResumeEvidence,
    resume_explicit_skill_set: Set[str],
    family_name: str,
) -> Tuple[int, List[str]]:
    family = BASELINE_FAMILIARITY_FAMILIES.get(family_name, {})
    support_hits = 0
    support_reasons: List[str] = []

    title_tokens_any = {_normalize_text(value) for value in family.get("title_tokens_any", []) if _normalize_text(value)}
    if title_tokens_any:
        resume_title_tokens: Set[str] = set()
        for title in _resume_titles(resume) + _resume_variant_titles(resume):
            resume_title_tokens |= _title_tokens(title)
        if resume_title_tokens & title_tokens_any:
            support_hits += 1
            support_reasons.append("title-profile support")

    supporting_explicit = {
        _normalize_text(value)
        for value in family.get("supporting_explicit_skills_any", [])
        if _normalize_text(value)
    }
    if supporting_explicit and (resume_explicit_skill_set & supporting_explicit):
        support_hits += 1
        support_reasons.append("explicit-skill support")

    supporting_analytics = {
        _normalize_text(value)
        for value in family.get("supporting_analytics_signals_any", [])
        if _normalize_text(value)
    }
    resume_analytics = {
        _normalize_text(value)
        for value in resume.analytics_ml_signals
        if _normalize_text(value)
    }
    if supporting_analytics and (resume_analytics & supporting_analytics):
        support_hits += 1
        support_reasons.append("analytics-signal support")

    supporting_tooling = {
        _normalize_text(value)
        for value in family.get("supporting_tooling_signals_any", [])
        if _normalize_text(value)
    }
    resume_tooling = {
        _normalize_text(value)
        for value in resume.tooling_signals
        if _normalize_text(value)
    }
    if supporting_tooling and (resume_tooling & supporting_tooling):
        support_hits += 1
        support_reasons.append("tooling-signal support")

    return support_hits, support_reasons


def _score_baseline_familiarity(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    resume_explicit_skill_set: Set[str],
    job: JobEvidence,
) -> MatchDimensionScore:
    family_targets = _job_baseline_family_targets(job)
    if not family_targets:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no eligible baseline-familiarity targets, so baseline_familiarity is neutral in v1.",
            [],
        )

    total_targets = 0
    explicit_matches = 0
    inferred_only_matches = 0
    evidence: List[str] = []
    family_summaries: List[str] = []

    for family_name, targets in family_targets.items():
        family = BASELINE_FAMILIARITY_FAMILIES.get(family_name, {})
        min_support_hits = int(family.get("min_support_hits", 1))
        support_hits, support_reasons = _resume_baseline_family_support(
            resume,
            resume_explicit_skill_set,
            family_name,
        )

        total_targets += len(targets)

        family_explicit = [target for target in targets if target in resume_explicit_skill_set]
        family_inferred = []

        if support_hits >= min_support_hits:
            family_inferred = [
                target for target in targets
                if target not in resume_explicit_skill_set
            ]

        explicit_matches += len(family_explicit)
        inferred_only_matches += len(family_inferred)

        if family_inferred:
            evidence.extend(family_inferred)

        family_summaries.append(
            f"{family_name}: explicit={len(family_explicit)}, inferred_only={len(family_inferred)}, "
            f"support_hits={support_hits}/{min_support_hits}"
        )
        if support_reasons:
            family_summaries[-1] += f" ({', '.join(support_reasons)})"

    if total_targets == 0:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no eligible baseline-familiarity targets, so baseline_familiarity is neutral in v1.",
            [],
        )

    inferred_coverage = inferred_only_matches / total_targets
    score = min(0.60, 0.60 * inferred_coverage)

    return _weighted_dimension(
        definition,
        score,
        (
            f"Granted scoring-only inferred familiarity for {inferred_only_matches}/{total_targets} eligible "
            f"baseline targets. Explicit matches already belong to explicit dimensions and are not counted here. "
            f"Family details: {'; '.join(family_summaries)}. "
            f"This dimension is a low-weight scoring prior only and must not be treated as explicit tailoring proof."
        ),
        evidence,
    )

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
    HISTORY_WEIGHT = 0.70
    VARIANT_WEIGHT = 0.30

    def _best_title_score(titles: List[str]) -> Tuple[float, str, float, float, List[str]]:
        best_score = 0.0
        best_title = ""
        best_base_score = 0.0
        best_adjustment = 0.0
        best_adjustment_reasons: List[str] = []

        for title in titles:
            base_score = _title_similarity(title, job.title)
            adjustment, adjustment_reasons = _role_family_title_adjustment(job.role_family, title)
            adjusted_score = max(0.0, min(1.0, base_score + adjustment))

            if adjusted_score > best_score:
                best_score = adjusted_score
                best_title = title
                best_base_score = base_score
                best_adjustment = adjustment
                best_adjustment_reasons = adjustment_reasons

        return (
            best_score,
            best_title,
            best_base_score,
            best_adjustment,
            best_adjustment_reasons,
        )

    variant_titles = _resume_variant_titles(resume)
    history_titles = _resume_titles(resume)

    variant_score, variant_title, variant_base, variant_adjustment, variant_reasons = _best_title_score(variant_titles)
    history_score, history_title, history_base, history_adjustment, history_reasons = _best_title_score(history_titles)

    if variant_title and history_title:
        final_score = (HISTORY_WEIGHT * history_score) + (VARIANT_WEIGHT * variant_score)
        explanation = (
            f"Best title alignment scored {final_score:.2f} using blended history/variant evidence "
            f"(history={history_score:.2f} from '{history_title}', variant={variant_score:.2f} from '{variant_title}'). "
            f"Blend weights: history={HISTORY_WEIGHT:.2f}, variant={VARIANT_WEIGHT:.2f}."
        )

        if history_reasons:
            explanation += (
                f" History adjustment={history_adjustment:+.2f} ({', '.join(history_reasons)})."
            )
        if variant_reasons:
            explanation += (
                f" Variant adjustment={variant_adjustment:+.2f} ({', '.join(variant_reasons)})."
            )

        return _weighted_dimension(
            definition,
            final_score,
            explanation,
            [history_title, variant_title, job.title, job.role_family],
        )

    if history_title:
        explanation = (
            f"Best title alignment scored {history_score:.2f} from history title '{history_title}'."
        )
        if history_reasons:
            explanation += (
                f" Role-family adjustment={history_adjustment:+.2f} ({', '.join(history_reasons)})."
            )

        return _weighted_dimension(
            definition,
            history_score,
            explanation,
            [history_title, job.title, job.role_family],
        )

    if variant_title:
        explanation = (
            f"Best title alignment scored {variant_score:.2f} from variant title '{variant_title}'."
        )
        if variant_reasons:
            explanation += (
                f" Role-family adjustment={variant_adjustment:+.2f} ({', '.join(variant_reasons)})."
            )

        return _weighted_dimension(
            definition,
            variant_score,
            explanation,
            [variant_title, job.title, job.role_family],
        )

    return _weighted_dimension(
        definition,
        0.0,
        "No resume titles were extracted, so title alignment could not be established.",
        [],
    )

def _score_skill_alignment(
    definition: MatchDimensionDefinition,
    targets: List[str],
    resume_explicit_skill_set: Set[str],
    resume: ResumeEvidence,
    job: JobEvidence,
    empty_reason: str,
) -> MatchDimensionScore:
    normalized_targets = _normalized_skill_list(targets)
    if not normalized_targets:
        return _weighted_dimension(definition, 0.5, empty_reason, [])

    matches = [skill for skill in normalized_targets if skill in resume_explicit_skill_set]
    coverage = len(matches) / len(normalized_targets)

    surfacing_bonus, surfacing_evidence, surfacing_reason = _matched_skill_surfacing_bonus(
        resume,
        job,
        matches,
    )

    final_score = min(1.0, coverage + surfacing_bonus)
    evidence = _unique_preserve_order(matches + surfacing_evidence)

    reason = (
        f"Matched {len(matches)}/{len(normalized_targets)} explicit target skills."
        if matches
        else f"Matched 0/{len(normalized_targets)} explicit target skills."
    )

    if surfacing_bonus > 0.0:
        reason += f" {surfacing_reason}"

    return _weighted_dimension(definition, final_score, reason, evidence)

def _score_workflow_alignment(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    job: JobEvidence,
) -> MatchDimensionScore:
    resume_workflow_set = _resume_experience_workflow_set(resume)
    required_targets = _normalized_skill_list(job.required_workflows)
    preferred_targets = _normalized_skill_list(job.preferred_workflows)

    if not required_targets and not preferred_targets:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no explicit workflow targets, so workflow alignment is neutral in v1.",
            [],
        )

    required_matches = [workflow for workflow in required_targets if workflow in resume_workflow_set]
    preferred_matches = [workflow for workflow in preferred_targets if workflow in resume_workflow_set]

    required_coverage = (
        len(required_matches) / len(required_targets)
        if required_targets else 0.0
    )
    preferred_coverage = (
        len(preferred_matches) / len(preferred_targets)
        if preferred_targets else 0.0
    )

    if required_targets and preferred_targets:
        score = (0.70 * required_coverage) + (0.30 * preferred_coverage)
    elif required_targets:
        score = required_coverage
    else:
        score = preferred_coverage

    evidence = _unique_preserve_order(required_matches + preferred_matches)

    reason_parts: List[str] = []
    if required_targets:
        reason_parts.append(
            f"matched {len(required_matches)}/{len(required_targets)} required workflows"
        )
    if preferred_targets:
        reason_parts.append(
            f"matched {len(preferred_matches)}/{len(preferred_targets)} preferred workflows"
        )

    reason = (
        "Workflow alignment " + ", ".join(reason_parts) + "."
        if reason_parts
        else "Workflow alignment could not be established."
    )

    return _weighted_dimension(definition, score, reason, evidence)

def _score_business_context_alignment(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    job: JobEvidence,
) -> MatchDimensionScore:
    resume_business_context_set = _resume_experience_business_context_set(resume)
    job_targets = _normalized_skill_list(job.business_contexts)

    if not job_targets:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no explicit business-context targets, so business-context alignment is neutral in v1.",
            [],
        )

    matches = [context for context in job_targets if context in resume_business_context_set]
    coverage = len(matches) / len(job_targets)

    return _weighted_dimension(
        definition,
        coverage,
        f"Matched {len(matches)}/{len(job_targets)} explicit JD business-context targets from experience bullets.",
        matches,
    )

def _score_stakeholder_translation_alignment(
    definition: MatchDimensionDefinition,
    resume: ResumeEvidence,
    job: JobEvidence,
) -> MatchDimensionScore:
    resume_stakeholder_context_set = _resume_experience_stakeholder_context_set(resume)
    job_targets = _normalized_skill_list(job.stakeholder_contexts)

    if not job_targets:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no explicit stakeholder-context targets, so stakeholder translation alignment is neutral in v1.",
            [],
        )

    matches = [context for context in job_targets if context in resume_stakeholder_context_set]
    coverage = len(matches) / len(job_targets)

    return _weighted_dimension(
        definition,
        coverage,
        f"Matched {len(matches)}/{len(job_targets)} explicit JD stakeholder-context targets from experience bullets.",
        matches,
    )

def _score_tooling_alignment(
    definition: MatchDimensionDefinition,
    resume_explicit_skill_set: Set[str],
    job: JobEvidence,
) -> MatchDimensionScore:
    structured_required_targets = [
        skill
        for skill in _normalized_skill_list(getattr(job, "required_tools", []))
        if skill in TOOLING_SIGNAL_PATTERNS
    ]
    structured_preferred_targets = [
        skill
        for skill in _normalized_skill_list(getattr(job, "preferred_tools", []))
        if skill in TOOLING_SIGNAL_PATTERNS
    ]

    if structured_required_targets or structured_preferred_targets:
        tooling_targets = _unique_preserve_order(
            structured_required_targets + structured_preferred_targets
        )
        target_source = "structured required_tools/preferred_tools"
    else:
        tooling_targets = [
            skill
            for skill in _normalized_skill_list(
                job.required_skills + job.preferred_skills + job.all_skills
            )
            if skill in TOOLING_SIGNAL_PATTERNS
        ]
        target_source = "fallback derived skill targets"

    if not tooling_targets:
        return _weighted_dimension(
            definition,
            0.5,
            "Job has no explicit tooling targets, so tooling alignment is neutral in v1.",
            [],
        )

    matches = [skill for skill in tooling_targets if skill in resume_explicit_skill_set]
    coverage = len(matches) / len(tooling_targets)

    return _weighted_dimension(
        definition,
        coverage,
        f"Matched {len(matches)}/{len(tooling_targets)} explicit job tooling targets from {target_source}.",
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

    dimensions = get_match_dimensions(getattr(job, "role_archetype", ""))
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
            resume_explicit_skill_set,
            resume,
            job,
            "Job has no explicit required-skill list, so required-skills alignment is neutral in v1.",
        ),
        "preferred_skills_alignment": lambda definition: _score_skill_alignment(
            definition,
            job.preferred_skills,
            resume_explicit_skill_set,
            resume,
            job,
            "Job has no explicit preferred-skill list, so preferred-skills alignment is neutral in v1.",
        ),
        "workflow_alignment": lambda definition: _score_workflow_alignment(
            definition,
            resume,
            job,
        ),
        "business_context_alignment": lambda definition: _score_business_context_alignment(
            definition,
            resume,
            job,
        ),
        "stakeholder_translation_alignment": lambda definition: _score_stakeholder_translation_alignment(
            definition,
            resume,
            job,
        ),
        "analytics_ml_depth": lambda definition: _score_analytics_ml_depth(
            definition,
            resume,
            resume_explicit_skill_set,
            job_analytics_ml_signals,
        ),
        "tooling_alignment": lambda definition: _score_tooling_alignment(
            definition,
            resume_explicit_skill_set,
            job,
        ),
        "baseline_familiarity": lambda definition: _score_baseline_familiarity(
            definition,
            resume,
            resume_explicit_skill_set,
            job,
        ),
        "experimentation_depth": lambda definition: _score_experimentation_alignment(
            definition,
            resume,
            job,
            job_experimentation_signals,
            "Job has no explicit experimentation signals, so experimentation depth is neutral in v1.",
        ),
        "domain_relevance": lambda definition: _score_domain_relevance(
            definition,
            resume,
            job,
            job_domain_signals,
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
import argparse
import json
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

from src.config.consts import (
    TITLE_CANONICAL,
    TAILORING_FACET_PATTERNS,
    _SKILL_ALIASES,
    CONTEXT_TOKEN_STOPWORDS,
)
from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import (
    load_resume_documents,
    load_resume_documents_by_name,
)
from src.resume.evidence_builder import build_resume_evidence
from src.ai.embedding_model import get_model

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

def _job_semantic_query_text(job) -> str:
    parts = [
        job.title,
        " ".join(job.required_skills or []),
        " ".join(job.preferred_skills or []),
        " ".join(job.all_skills or []),
    ]
    return " | ".join(part for part in parts if str(part or "").strip())

def _is_structurally_good_bullet(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False

    words = value.split()
    if len(words) < 8:
        return False

    first = value[0]
    if first.isalpha() and first != first.upper():
        return False

    return True


def _entry_context_text(section: str, source_title: str, source_company: str, normalized_skills: List[str]) -> str:
    parts = [section, source_title, source_company, " ".join(normalized_skills or [])]
    return " | ".join(part for part in parts if str(part or "").strip())

def _entry_id_value(entry) -> str:
    return str(getattr(entry, "entry_id", "") or "")


def _entry_index_value(entry) -> int:
    value = getattr(entry, "entry_index", None)
    return int(value) if value is not None else -1


def _entry_bullet_id_value(entry, bullet_index: int) -> str:
    bullet_ids = list(getattr(entry, "bullet_ids", []) or [])
    if 0 <= bullet_index < len(bullet_ids):
        return str(bullet_ids[bullet_index] or "")
    return ""

def _entry_is_semantically_eligible(
    *,
    job_targets: List[str],
    job_context_terms: List[str],
    section: str,
    source_title: str,
    source_company: str,
    normalized_skills: List[str],
) -> bool:
    normalized_skill_set = {
        _normalize_text(skill)
        for skill in (normalized_skills or [])
        if _normalize_text(skill)
    }

    if any(term in normalized_skill_set for term in job_targets):
        return True

    context_text = _normalize_text(_entry_context_text(section, source_title, source_company, normalized_skills))
    if not context_text:
        return False

    context_hits = [term for term in job_context_terms if _contains_signal(context_text, term)]
    return len(context_hits) >= 1


def _evidence_type_priority(evidence_type: str) -> int:
    if evidence_type == "direct_overlap":
        return 0
    if evidence_type == "semantic_similarity":
        return 1
    if evidence_type == "same_source_context":
        return 2
    if evidence_type == "adjacent_context":
        return 3
    return 9

def _rerank_evidence_rows(rows: List[dict]) -> List[dict]:
    source_counts = {}
    for row in rows:
        src_key = row.get("source_key", "")
        source_counts[src_key] = source_counts.get(src_key, 0) + 1

    def _sort_key(row: dict):
        evidence_type = row.get("evidence_type", "")
        source_key = row.get("source_key", "")
        section = row.get("section", "")

        # Strong preference order:
        # 1. evidence type priority
        # 2. more explicit lexical overlap when present
        # 3. higher semantic score when present
        # 4. experience before project
        # 5. sources that are not already flooding the result
        return (
            _evidence_type_priority(evidence_type),
            -int(row.get("overlap_count", 0) or 0),
            -float(row.get("semantic_score", 0.0) or 0.0),
            0 if section == "experience" else 1,
            source_counts.get(source_key, 0),
            row.get("source_title", "").lower(),
            row.get("text", "").lower(),
        )

    return sorted(rows, key=_sort_key)

def _semantic_bullet_candidates(resume, job, top_k: int = 4) -> List[dict]:
    query_text = _job_semantic_query_text(job).strip()
    if not query_text:
        return []

    job_targets = _normalized_skill_list(job.required_skills + job.preferred_skills + job.all_skills)
    job_context_terms = _job_context_terms(job)

    bullet_rows: List[dict] = []

    def _append_bullets(
        section: str,
        source_title: str,
        source_company: str,
        bullets: List[str],
        normalized_skills: List[str],
        entry_id: str,
        entry_index: int,
        bullet_ids: List[str],
    ) -> None:
        if not _entry_is_semantically_eligible(
            job_targets=job_targets,
            job_context_terms=job_context_terms,
            section=section,
            source_title=source_title,
            source_company=source_company,
            normalized_skills=normalized_skills,
        ):
            return

        for bullet_index, bullet in enumerate(bullets):
            text = str(bullet or "").strip()
            if not _is_structurally_good_bullet(text):
                continue

            text_norm = _normalize_text(text)
            if not text_norm:
                continue

            exact_overlaps = [term for term in job_targets if _contains_signal(text_norm, term)]
            if exact_overlaps:
                continue

            bullet_rows.append(
                {
                    "section": section,
                    "source_title": source_title,
                    "source_company": source_company,
                    "text": text,
                    "text_norm": text_norm,
                    "bullet_index": bullet_index,
                    "entry_id": entry_id,
                    "entry_index": entry_index,
                    "bullet_id": (
                        str(bullet_ids[bullet_index])
                        if bullet_index < len(bullet_ids)
                        else ""
                    ),
                }
            )

    for entry in resume.experience_entries:
        _append_bullets(
            "experience",
            entry.title,
            entry.company,
            entry.bullets,
            entry.normalized_skills,
            _entry_id_value(entry),
            _entry_index_value(entry),
            list(getattr(entry, "bullet_ids", []) or []),
        )

    for entry in resume.project_entries:
        _append_bullets(
            "project",
            entry.name,
            "",
            entry.bullets,
            entry.normalized_skills,
            _entry_id_value(entry),
            _entry_index_value(entry),
            list(getattr(entry, "bullet_ids", []) or []),
        )

    if not bullet_rows:
        return []

    model = get_model()
    query_vec = model.encode(query_text, normalize_embeddings=True)
    bullet_texts = [row["text"] for row in bullet_rows]
    bullet_vecs = model.encode(bullet_texts, normalize_embeddings=True)

    scores = bullet_vecs @ query_vec

    ranked = sorted(
        zip(bullet_rows, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    semantic_rows: List[dict] = []
    used_sources = set()

    for row, score in ranked:
        src_key = "||".join(
            [
                row["section"],
                _normalize_text(row["source_title"]),
                _normalize_text(row["source_company"]),
            ]
        )

        if src_key in used_sources:
            continue

        semantic_rows.append(
            {
                "section": row["section"],
                "source_title": row["source_title"],
                "source_company": row["source_company"],
                "text": row["text"],
                "overlap_count": 0,
                "overlaps": [],
                "evidence_type": "semantic_similarity",
                "semantic_score": round(float(score), 6),
                "bullet_index": row["bullet_index"],
                "entry_id": row["entry_id"],
                "entry_index": row["entry_index"],
                "bullet_id": row["bullet_id"],
            }
        )
        used_sources.add(src_key)

        if len(semantic_rows) >= top_k:
            break

    return semantic_rows

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

def _term_support_evidence_row(
    *,
    section: str,
    source_title: str,
    source_company: str,
    text: str = "",
    entry_id: str = "",
    entry_index: int = -1,
    bullet_id: str = "",
    bullet_index: int = -1,
) -> dict:
    return {
        "section": section,
        "source_title": source_title,
        "source_company": source_company,
        "text": text,
        "entry_id": entry_id,
        "entry_index": entry_index,
        "bullet_id": bullet_id,
        "bullet_index": bullet_index,
    }


def _build_single_term_support(resume, term: str) -> dict:
    normalized_term = _normalize_text(term)
    if not normalized_term:
        return {
            "term": "",
            "support_level": "unsupported",
            "support_scope": "none",
            "evidence": [],
        }

    experience_matches: List[dict] = []
    for entry in resume.experience_entries:
        for bullet_index, bullet in enumerate(entry.bullets):
            bullet_norm = _normalize_text(bullet)
            if not bullet_norm:
                continue
            if _contains_signal(bullet_norm, normalized_term):
                experience_matches.append(
                    _term_support_evidence_row(
                        section="experience",
                        source_title=entry.title,
                        source_company=entry.company,
                        text=bullet,
                        entry_id=_entry_id_value(entry),
                        entry_index=_entry_index_value(entry),
                        bullet_id=_entry_bullet_id_value(entry, bullet_index),
                        bullet_index=bullet_index,
                    )
                )
                if len(experience_matches) >= 2:
                    break
        if len(experience_matches) >= 2:
            break

    if experience_matches:
        return {
            "term": normalized_term,
            "support_level": "direct_bullet",
            "support_scope": "experience",
            "evidence": experience_matches,
        }

    project_matches: List[dict] = []
    for entry in resume.project_entries:
        for bullet_index, bullet in enumerate(entry.bullets):
            bullet_norm = _normalize_text(bullet)
            if not bullet_norm:
                continue
            if _contains_signal(bullet_norm, normalized_term):
                project_matches.append(
                    _term_support_evidence_row(
                        section="project",
                        source_title=entry.name,
                        source_company="",
                        text=bullet,
                        entry_id=_entry_id_value(entry),
                        entry_index=_entry_index_value(entry),
                        bullet_id=_entry_bullet_id_value(entry, bullet_index),
                        bullet_index=bullet_index,
                    )
                )
                if len(project_matches) >= 2:
                    break
        if len(project_matches) >= 2:
            break

    if project_matches:
        return {
            "term": normalized_term,
            "support_level": "direct_bullet",
            "support_scope": "project",
            "evidence": project_matches,
        }

    for entry in resume.experience_entries:
        normalized_skills = {
            _normalize_text(value) for value in entry.normalized_skills if _normalize_text(value)
        }
        if normalized_term in normalized_skills:
            return {
                "term": normalized_term,
                "support_level": "entry_context",
                "support_scope": "experience",
                "evidence": [
                    _term_support_evidence_row(
                        section="experience",
                        source_title=entry.title,
                        source_company=entry.company,
                        text="",
                        entry_id=_entry_id_value(entry),
                        entry_index=_entry_index_value(entry),
                    )
                ],
            }

    for entry in resume.project_entries:
        normalized_skills = {
            _normalize_text(value) for value in entry.normalized_skills if _normalize_text(value)
        }
        if normalized_term in normalized_skills:
            return {
                "term": normalized_term,
                "support_level": "entry_context",
                "support_scope": "project",
                "evidence": [
                    _term_support_evidence_row(
                        section="project",
                        source_title=entry.name,
                        source_company="",
                        text="",
                        entry_id=_entry_id_value(entry),
                        entry_index=_entry_index_value(entry),
                    )
                ],
            }

    resume_skill_set = {_normalize_text(value) for value in resume.skills if _normalize_text(value)}
    if normalized_term in resume_skill_set:
        return {
            "term": normalized_term,
            "support_level": "skills_section",
            "support_scope": "resume_skills",
            "evidence": [
                _term_support_evidence_row(
                    section="resume_skills",
                    source_title="Resume Skills",
                    source_company="",
                    text="",
                )
            ],
        }

    return {
        "term": normalized_term,
        "support_level": "unsupported",
        "support_scope": "none",
        "evidence": [],
    }


def _build_term_support_summary(resume, job) -> dict:
    required_terms = _normalized_skill_list(job.required_skills)
    preferred_terms = _normalized_skill_list(job.preferred_skills)

    return {
        "required": [_build_single_term_support(resume, term) for term in required_terms],
        "preferred": [_build_single_term_support(resume, term) for term in preferred_terms],
    }

def _term_matches_facet_pattern(term: str, pattern: str) -> bool:
    term_norm = _normalize_text(term)
    pattern_norm = _normalize_text(pattern)

    if not term_norm or not pattern_norm:
        return False

    return _contains_signal(term_norm, pattern_norm) or _contains_signal(pattern_norm, term_norm)


def _build_job_facet_targets(job) -> dict:
    job_terms = _normalized_skill_list(
        list(job.required_skills or [])
        + list(job.preferred_skills or [])
        + list(job.all_skills or [])
        + [job.title]
    )

    facet_targets = {}
    for facet_name, patterns in TAILORING_FACET_PATTERNS.items():
        matched_terms: List[str] = []
        for term in job_terms:
            if any(_term_matches_facet_pattern(term, pattern) for pattern in patterns):
                matched_terms.append(term)

        matched_terms = _unique_preserve_order(matched_terms)
        if matched_terms:
            facet_targets[facet_name] = matched_terms

    return facet_targets

def _text_matches_any_facet_pattern(text: str, patterns: List[str]) -> bool:
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return False

    for pattern in patterns:
        normalized_pattern = _normalize_text(pattern)
        if not normalized_pattern:
            continue
        if _contains_signal(normalized_text, normalized_pattern):
            return True

    return False


def _normalized_values_matching_facet_patterns(values: List[str], patterns: List[str]) -> List[str]:
    matches: List[str] = []

    for value in values or []:
        normalized_value = _normalize_text(value)
        if not normalized_value:
            continue

        for pattern in patterns:
            normalized_pattern = _normalize_text(pattern)
            if not normalized_pattern:
                continue

            if _contains_signal(normalized_value, normalized_pattern) or _contains_signal(normalized_pattern, normalized_value):
                matches.append(normalized_value)
                break

    return _unique_preserve_order(matches)


def _collect_facet_direct_evidence(resume, patterns: List[str], limit: int = 4) -> List[dict]:
    rows: List[dict] = []
    seen = set()

    for entry in resume.experience_entries:
        for bullet_index, bullet in enumerate(entry.bullets):
            if not _text_matches_any_facet_pattern(bullet, patterns):
                continue

            key = (
                "experience",
                entry.title,
                entry.company,
                _entry_bullet_id_value(entry, bullet_index),
                bullet,
            )
            if key in seen:
                continue
            seen.add(key)

            rows.append(
                _term_support_evidence_row(
                    section="experience",
                    source_title=entry.title,
                    source_company=entry.company,
                    text=bullet,
                    entry_id=_entry_id_value(entry),
                    entry_index=_entry_index_value(entry),
                    bullet_id=_entry_bullet_id_value(entry, bullet_index),
                    bullet_index=bullet_index,
                )
            )
            if len(rows) >= limit:
                return rows

    for entry in resume.project_entries:
        for bullet in entry.bullets:
            if not _text_matches_any_facet_pattern(bullet, patterns):
                continue

            key = ("project", entry.name, "", bullet)
            if key in seen:
                continue
            seen.add(key)

            rows.append(
                _term_support_evidence_row(
                    section="project",
                    source_title=entry.name,
                    source_company="",
                    text=bullet,
                    entry_id=_entry_id_value(entry),
                    entry_index=_entry_index_value(entry),
                    bullet_id=_entry_bullet_id_value(entry, bullet_index),
                    bullet_index=bullet_index,
                )
            )
            if len(rows) >= limit:
                return rows

    return rows


def _collect_facet_context_support(resume, patterns: List[str], limit: int = 4) -> Tuple[List[str], List[dict]]:
    matched_terms: List[str] = []
    evidence_rows: List[dict] = []
    seen = set()

    for entry in resume.experience_entries:
        context_terms = _normalized_values_matching_facet_patterns(entry.normalized_skills, patterns)
        if not context_terms:
            continue

        matched_terms.extend(context_terms)
        key = ("experience", entry.title, entry.company)
        if key not in seen:
            seen.add(key)
            evidence_rows.append(
                _term_support_evidence_row(
                    section="experience",
                    source_title=entry.title,
                    source_company=entry.company,
                    text="",
                    entry_id=_entry_id_value(entry),
                    entry_index=_entry_index_value(entry),
                )
            )
            if len(evidence_rows) >= limit:
                break

    if len(evidence_rows) < limit:
        for entry in resume.project_entries:
            context_terms = _normalized_values_matching_facet_patterns(entry.normalized_skills, patterns)
            if not context_terms:
                continue

            matched_terms.extend(context_terms)
            key = ("project", entry.name, "")
            if key not in seen:
                seen.add(key)
                evidence_rows.append(
                    _term_support_evidence_row(
                        section="project",
                        source_title=entry.name,
                        source_company="",
                        text="",
                        entry_id=_entry_id_value(entry),
                        entry_index=_entry_index_value(entry),
                    )
                )
                if len(evidence_rows) >= limit:
                    break

    resume_skill_matches = _normalized_values_matching_facet_patterns(resume.skills, patterns)
    matched_terms.extend(resume_skill_matches)

    return _unique_preserve_order(matched_terms), evidence_rows

def _facet_support_row(
    resume,
    facet_name: str,
    job_terms: List[str],
    patterns: List[str],
    support_rows: List[dict],
) -> dict:
    support_map = {
        _normalize_text(row.get("term", "")): row
        for row in support_rows
        if _normalize_text(row.get("term", ""))
    }

    direct_terms: List[str] = []
    context_terms: List[str] = []
    skills_only_terms: List[str] = []
    unsupported_terms: List[str] = []
    anchor_evidence: List[dict] = []
    seen_anchor_keys = set()

    for term in job_terms:
        normalized_term = _normalize_text(term)
        row = support_map.get(
            normalized_term,
            {
                "term": normalized_term,
                "support_level": "unsupported",
                "support_scope": "none",
                "evidence": [],
            },
        )

        support_level = row.get("support_level", "unsupported")

        if support_level == "direct_bullet":
            direct_terms.append(normalized_term)
            for evidence in row.get("evidence", []) or []:
                key = (
                    evidence.get("section", ""),
                    evidence.get("source_title", ""),
                    evidence.get("source_company", ""),
                    evidence.get("text", ""),
                )
                if key in seen_anchor_keys:
                    continue
                seen_anchor_keys.add(key)
                anchor_evidence.append(evidence)

        elif support_level == "entry_context":
            context_terms.append(normalized_term)

        elif support_level == "skills_section":
            skills_only_terms.append(normalized_term)

        else:
            unsupported_terms.append(normalized_term)

    facet_direct_evidence = _collect_facet_direct_evidence(resume, patterns, limit=4)
    facet_context_terms, facet_context_evidence = _collect_facet_context_support(resume, patterns, limit=4)

    for evidence in facet_direct_evidence:
        key = (
            evidence.get("section", ""),
            evidence.get("source_title", ""),
            evidence.get("source_company", ""),
            evidence.get("text", ""),
        )
        if key in seen_anchor_keys:
            continue
        seen_anchor_keys.add(key)
        anchor_evidence.append(evidence)

    return {
        "facet": facet_name,
        "job_terms": _unique_preserve_order(job_terms),
        "direct_terms": _unique_preserve_order(direct_terms),
        "context_terms": _unique_preserve_order(context_terms),
        "skills_only_terms": _unique_preserve_order(skills_only_terms),
        "unsupported_terms": _unique_preserve_order(unsupported_terms),
        "anchor_evidence": anchor_evidence[:4],
        "facet_direct_evidence": facet_direct_evidence[:4],
        "facet_context_terms": _unique_preserve_order(facet_context_terms),
        "facet_context_evidence": facet_context_evidence[:4],
    }


def _build_resume_facet_support(resume, job) -> List[dict]:
    term_support = _build_term_support_summary(resume, job)
    support_rows = (term_support.get("required", []) or []) + (term_support.get("preferred", []) or [])
    facet_targets = _build_job_facet_targets(job)

    facet_rows: List[dict] = []
    for facet_name, job_terms in facet_targets.items():
        patterns = TAILORING_FACET_PATTERNS.get(facet_name, []) or []
        facet_rows.append(
            _facet_support_row(
                resume,
                facet_name,
                job_terms,
                patterns,
                support_rows,
            )
        )

    return facet_rows

def _collect_top_relevant_bullets(
    resume,
    job,
    top_k: int = 8,
    enable_semantic: bool = True,
) -> List[dict]:
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
            row.get("bullet_id", ""),
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
        bullet_ids: List[str],
        entry_id: str,
        entry_index: int,
    ) -> None:
        src_key = _source_key(section, source_title, source_company)

        source_entries[src_key] = {
            "section": section,
            "source_title": source_title,
            "source_company": source_company,
            "bullets": bullets,
            "bullet_ids": bullet_ids,
            "entry_id": entry_id,
            "entry_index": entry_index,
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
                    "entry_id": entry_id,
                    "entry_index": entry_index,
                    "bullet_id": (
                        str(bullet_ids[bullet_index])   
                        if bullet_index < len(bullet_ids)
                        else ""
                    ),
                }
            )

    for entry in resume.experience_entries:
        _append_source_rows(
            section="experience",
            source_title=entry.title,
            source_company=entry.company,
            bullets=entry.bullets,
            bullet_ids=list(getattr(entry, "bullet_ids", []) or []),
            entry_id=_entry_id_value(entry),
            entry_index=_entry_index_value(entry),
        )

    for entry in resume.project_entries:
        _append_source_rows(
            section="project",
            source_title=entry.name,
            source_company="",
            bullets=entry.bullets,
            bullet_ids=list(getattr(entry, "bullet_ids", []) or []),
            entry_id=_entry_id_value(entry),
            entry_index=_entry_index_value(entry),
        )

    direct_rows.sort(
        key=lambda row: (
            -row["overlap_count"],
            row["section"],
            row["source_title"].lower(),
            row["text"].lower(),
        )
    )

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

        src_key = row.get("source_key") or _source_key(
            row.get("section", ""),
            row.get("source_title", ""),
            row.get("source_company", ""),
        )
        row["source_key"] = src_key

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

    # Pass 3: semantic bullets from the selected resume to improve meaning-based recall.
    # Skip this in fast targeted-regeneration mode.
    if enable_semantic:
        semantic_rows = _semantic_bullet_candidates(resume, job, top_k=max(4, top_k // 2))

        semantic_new_source = []
        semantic_existing_source = []

        for row in semantic_rows:
            src_key = _source_key(
                row.get("section", ""),
                row.get("source_title", ""),
                row.get("source_company", ""),
            )
            row["source_key"] = src_key

            if src_key in used_sources:
                semantic_existing_source.append(row)
            else:
                semantic_new_source.append(row)

        for row in semantic_new_source:
            if len(selected) >= top_k:
                break
            _register_selected(row)

        for row in semantic_existing_source:
            if len(selected) >= top_k:
                break
            _register_selected(row)

    # Pass 4: add more bullets from already-proven relevant sources for richer role-level context.
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
                "entry_id": source_meta.get("entry_id", ""),
                "entry_index": source_meta.get("entry_index", -1),
                "bullet_id": (
                    str(source_meta.get("bullet_ids", [])[bullet_index])
                    if bullet_index < len(source_meta.get("bullet_ids", []) or [])
                    else ""
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

    reranked = _rerank_evidence_rows(selected)
    return reranked[:top_k]

def _split_bullet_into_clauses(text: str) -> List[str]:
    raw = re.sub(r"\s+", " ", str(text or "").strip())
    if not raw:
        return []

    primary_parts = re.split(
        r";\s*|(?<=\d%)\s+(?=[A-Z])|(?<=[a-z0-9])\.\s+(?=[A-Z])",
        raw,
    )

    clauses: List[str] = []
    for part in primary_parts:
        cleaned = part.strip(" -•\t")
        if not cleaned:
            continue
        clauses.append(cleaned)

    return _unique_preserve_order(clauses)


def _collect_top_relevant_evidence_units(
    resume,
    job,
    top_k: int = 16,
    enable_semantic: bool = True,
) -> List[dict]:
    parent_rows = _collect_top_relevant_bullets(
        resume,
        job,
        top_k=max(top_k, 10),
        enable_semantic=enable_semantic,
    )
    job_targets = _normalized_skill_list(job.required_skills + job.preferred_skills + job.all_skills)

    unit_rows: List[dict] = []
    seen_keys = set()

    def _unit_priority(evidence_type: str) -> int:
        if evidence_type == "direct_overlap":
            return 0
        if evidence_type == "semantic_similarity":
            return 1
        if evidence_type in {"same_source_context", "adjacent_context"}:
            return 2
        return 3

    for row in parent_rows:
        parent_text = str(row.get("text", "") or "").strip()
        if not parent_text:
            continue

        clauses = _split_bullet_into_clauses(parent_text)
        if not clauses:
            clauses = [parent_text]

        parent_terms = _unique_preserve_order(
            list(row.get("overlaps", []) or []) + list(row.get("context_terms", []) or [])
        )
        evidence_type = row.get("evidence_type", "")

        for clause_index, clause_text in enumerate(clauses):
            clause_norm = _normalize_text(clause_text)
            if not clause_norm:
                continue

            clause_overlaps = [
                term for term in job_targets
                if _contains_signal(clause_norm, term)
            ]

            if evidence_type == "direct_overlap" and not clause_overlaps:
                continue

            supported_terms = clause_overlaps if clause_overlaps else parent_terms
            if not supported_terms:
                continue

            unit_row = {
                "section": row.get("section", ""),
                "source_title": row.get("source_title", ""),
                "source_company": row.get("source_company", ""),
                "text": clause_text,
                "clause_text": clause_text,
                "parent_bullet": parent_text,
                "clause_index": clause_index,
                "overlap_count": len(clause_overlaps) if clause_overlaps else len(supported_terms),
                "overlaps": _unique_preserve_order(supported_terms)[:8],
                "context_terms": row.get("context_terms", []) or [],
                "evidence_type": evidence_type,
                "unit_kind": "clause_unit",
                "semantic_score": row.get("semantic_score"),
                "source_key": row.get("source_key", ""),
                "bullet_index": row.get("bullet_index", -1),
                "entry_id": row.get("entry_id", ""),
                "entry_index": row.get("entry_index", -1),
                "bullet_id": row.get("bullet_id", ""),
            }

            unit_key = (
                unit_row["section"],
                unit_row["source_title"],
                unit_row["source_company"],
                unit_row["evidence_type"],
                unit_row.get("bullet_id", ""),
                unit_row["clause_index"],
                unit_row["clause_text"],
            )
            if unit_key in seen_keys:
                continue

            seen_keys.add(unit_key)
            unit_rows.append(unit_row)

    unit_rows.sort(
        key=lambda row: (
            _unit_priority(str(row.get("evidence_type", ""))),
            -int(row.get("overlap_count", 0) or 0),
            str(row.get("section", "")),
            str(row.get("source_title", "")).lower(),
            str(row.get("clause_text", "")).lower(),
        )
    )

    return unit_rows[:top_k]

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
    top_evidence_units: List[dict],
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
            "term_support": _build_term_support_summary(selected_resume, job_evidence),
            "facet_support": _build_resume_facet_support(selected_resume, job_evidence),
        },
        "top_dimension_deltas_vs_backup": (
            _top_dimension_deltas(selected_result, runner_up_result)
            if runner_up_result is not None and not is_tie
            else []
        ),
        "top_relevant_bullets": top_bullets,
        "top_relevant_evidence_units": top_evidence_units,
        "guardrail": "Only add or strengthen resume language when it is already truthful and supported by your actual work.",
    }

def _load_candidate_resume_documents(resume_name_contains: str) -> List[object]:
    raw = str(resume_name_contains or "").strip()
    if not raw:
        docs = load_resume_documents()
        return sorted(docs, key=lambda doc: doc.resume_name)

    # Fast path for targeted regeneration: exact resume filename lookup first.
    exact_docs = load_resume_documents_by_name([raw])
    if exact_docs:
        return sorted(exact_docs, key=lambda doc: doc.resume_name)

    # Backward-compatible fallback for older substring-based CLI usage.
    needle = _normalize_text(raw)
    docs = [
        doc for doc in load_resume_documents()
        if needle in _normalize_text(doc.resume_name)
    ]
    return sorted(docs, key=lambda doc: doc.resume_name)
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
    parser.add_argument(
        "--disable-semantic-evidence",
        action="store_true",
        help="Skip semantic embedding-based evidence recovery. Intended for fast targeted resume regeneration.",
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

    resume_docs = _load_candidate_resume_documents(args.resume_name_contains)

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
        enable_semantic=not args.disable_semantic_evidence,
    )
    top_evidence_units = _collect_top_relevant_evidence_units(
        selected_resume,
        job_evidence,
        top_k=max(args.top_bullets * 2, 12),
        enable_semantic=not args.disable_semantic_evidence,
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
            print(f"   rerank_priority: {_evidence_type_priority(row.get('evidence_type', ''))}")
            print(f"   overlaps: {row['overlaps']}")
            if "semantic_score" in row:
                print(f"   semantic_score: {row['semantic_score']}")
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
            top_evidence_units=top_evidence_units,
        )
        output_path = Path(args.output_json)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written: {output_path}")


if __name__ == "__main__":
    main()
import re
from typing import List, Optional, Tuple
import hashlib
import copy 

from src.matching.dimensions import get_match_dimensions
from src.resume.models import (
    ResumeDocument,
    ResumeEducationEntry,
    ResumeEvidence,
    ResumeExperienceEntry,
    ResumeProjectEntry,
)
from src.config.consts import (
    COMMON_SKILL_PATTERNS,
    DATE_RANGE_PATTERN,
    DOMAIN_SIGNAL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    TITLE_PATTERNS,
    TOOLING_SIGNAL_PATTERNS,
    ANALYTICS_ML_SIGNAL_PATTERNS,
    SECTION_ALIASES,
    ROLE_WORD_HINTS,
    ACTION_VERB_HINTS,
    RESUME_METHOD_SIGNAL_PATTERNS,
    RESUME_WORKFLOW_SIGNAL_PATTERNS,
    RESUME_BUSINESS_CONTEXT_SIGNAL_PATTERNS,
    RESUME_STAKEHOLDER_CONTEXT_SIGNAL_PATTERNS,
    RESUME_ARTIFACT_TYPE_SIGNAL_PATTERNS,
    RESUME_KPI_METRIC_SIGNAL_PATTERNS,
    RESUME_OWNERSHIP_SIGNAL_PATTERNS,
    _SKILL_ALIASES,
)

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []

    for value in values:
        value = value.strip()
        if not value:
            continue
        if value not in seen:
            seen.add(value)
            ordered.append(value)

    return ordered

def _pattern_present(text_norm: str, candidate: str) -> bool:
    normalized = _normalize(candidate)
    if not normalized:
        return False

    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    prefix = r"(?<![a-z0-9])" if normalized[:1].isalnum() else ""
    suffix = r"(?![a-z0-9])" if normalized[-1:].isalnum() else ""

    return re.search(prefix + escaped + suffix, text_norm) is not None

def _extract_pattern_hits(text: str, patterns: List[str]) -> List[str]:
    text_norm = _normalize(text)
    hits: List[str] = []

    for pattern in patterns:
        canonical = _normalize(pattern)
        candidates = {canonical}

        for alias, alias_target in _SKILL_ALIASES.items():
            if _normalize(alias_target) == canonical:
                candidates.add(_normalize(alias))

        if any(_pattern_present(text_norm, candidate) for candidate in candidates):
            hits.append(canonical)

    return _unique_preserve_order(hits)

def _extract_phrase_hits(text: str, patterns: List[str]) -> List[str]:
    text_norm = _normalize(text)
    hits: List[str] = []

    for pattern in patterns:
        normalized = _normalize(pattern)
        if not normalized:
            continue

        if _pattern_present(text_norm, normalized):
            hits.append(normalized)

    return _unique_preserve_order(hits)


def _extract_quantified_lines(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    quantified = []

    for line in lines:
        if re.search(r"\b\d+(\.\d+)?%|\$\d+|\b\d+\+?\b", line):
            quantified.append(line)

    return quantified


def _clean_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

def _stable_id_fragment(*parts: object) -> str:
    basis_parts = [_normalize(str(part or "")) for part in parts if _normalize(str(part or ""))]
    basis = "||".join(basis_parts) if basis_parts else "empty"
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


def _make_entry_id(section: str, entry_index: int, *parts: object) -> str:
    return f"{section}:{entry_index}:{_stable_id_fragment(section, entry_index, *parts)}"


def _make_bullet_ids(entry_id: str, bullets: List[str]) -> List[str]:
    bullet_ids: List[str] = []

    for bullet_index, bullet in enumerate(bullets):
        bullet_ids.append(
            f"{entry_id}:b{bullet_index}:{_stable_id_fragment(entry_id, bullet_index, bullet)}"
        )

    return bullet_ids

def _normalize_heading(line: str) -> str:
    line = _normalize(line)
    line = line.rstrip(":")
    line = re.sub(r"[^a-z0-9/&+\-\s]", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def _canonical_section_name(line: str) -> Optional[str]:
    heading = _normalize_heading(line)

    if not heading or len(heading) > 50:
        return None

    for canonical_name, aliases in SECTION_ALIASES.items():
        if heading in aliases:
            return canonical_name

    return None


def _find_section_ranges(lines: List[str]) -> List[Tuple[str, int, int]]:
    headings: List[Tuple[str, int]] = []

    for idx, line in enumerate(lines):
        section_name = _canonical_section_name(line)
        if section_name:
            headings.append((section_name, idx))

    if not headings:
        return []

    ranges: List[Tuple[str, int, int]] = []

    for i, (section_name, start_idx) in enumerate(headings):
        content_start = start_idx + 1
        content_end = headings[i + 1][1] if i + 1 < len(headings) else len(lines)
        ranges.append((section_name, content_start, content_end))

    return ranges


def _get_section_lines(text: str, section_name: str) -> List[str]:
    lines = _clean_lines(text)
    ranges = _find_section_ranges(lines)

    for canonical_name, start_idx, end_idx in ranges:
        if canonical_name == section_name:
            return lines[start_idx:end_idx]

    return []


def _strip_bullet_marker(line: str) -> str:
    return re.sub(r"^[\-\*\u2022\u25CF\u25E6\u2043]+\s*", "", line).strip()

def _extract_inline_date(line: str) -> str:
    match = DATE_RANGE_PATTERN.search(line or "")
    return match.group(0).strip() if match else ""

def _remove_inline_date(line: str) -> str:
    return DATE_RANGE_PATTERN.sub("", line or "").strip(" |,-")

def _is_probable_date_line(line: str) -> bool:
    line = (line or "").strip()
    if not line:
        return False

    extracted = _extract_inline_date(line)
    if not extracted:
        return False

    remainder = _normalize(_remove_inline_date(line))
    return remainder == ""

def _looks_like_role_header(line: str) -> bool:
    line_norm = _normalize(line)

    if not line_norm:
        return False

    if len(line_norm) > 120:
        return False

    if _is_probable_date_line(line):
        return True

    if any(title in line_norm for title in TITLE_PATTERNS):
        return True

    if " at " in line_norm or " | " in line or " @ " in line:
        return True

    return False

def _looks_like_bullet_line(line: str) -> bool:
    stripped = line.strip()
    return bool(re.match(r"^[\-\*\u2022\u25CF\u25E6\u2043]", stripped))

def _looks_like_role_start(lines: List[str], idx: int) -> bool:
    line = lines[idx].strip()
    if not line:
        return False

    if _looks_like_bullet_line(line):
        return False

    core = _remove_inline_date(line)
    core_norm = _normalize(core)

    if not core_norm:
        return False

    if len(core_norm) > 140:
        return False

    has_structure = (
        "," in core
        or "|" in line
        or " at " in core_norm
    )

    has_role_signal = _looks_like_title_fragment(core)

    return has_structure and has_role_signal

def _block_starts_with_role_header(block: List[str]) -> bool:
    if not block:
        return False

    first = block[0].strip()
    if not first:
        return False

    if _looks_like_bullet_line(first):
        return False

    core = _remove_inline_date(first)
    core_norm = _normalize(core)

    if not core_norm:
        return False

    has_structure = (
        "," in core
        or "|" in first
        or " at " in core_norm
    )

    has_role_signal = _looks_like_title_fragment(core)

    return has_structure and has_role_signal


def _merge_orphan_experience_blocks(blocks: List[List[str]]) -> List[List[str]]:
    if not blocks:
        return []

    merged: List[List[str]] = []

    for block in blocks:
        if merged and not _block_starts_with_role_header(block):
            merged[-1].extend(block)
            continue

        merged.append(block)

    return merged

def _split_experience_blocks(lines: List[str]) -> List[List[str]]:
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    if not cleaned_lines:
        return []

    blocks: List[List[str]] = []
    current_block: List[str] = []
    current_block_has_bullets = False

    for idx, line in enumerate(cleaned_lines):
        if _looks_like_bullet_line(line):
            current_block_has_bullets = True

        should_start_new_block = (
            _looks_like_role_start(cleaned_lines, idx)
            and current_block
            and current_block_has_bullets
        )

        if should_start_new_block:
            blocks.append(current_block)
            current_block = [line]
            current_block_has_bullets = False
            continue

        current_block.append(line)

    if current_block:
        blocks.append(current_block)

    return _merge_orphan_experience_blocks(blocks)

def _looks_like_role_text(text: str) -> bool:
    text_norm = _normalize(text)
    return any(
        re.search(rf"\b{re.escape(word)}\b", text_norm)
        for word in ROLE_WORD_HINTS
    )

def _looks_like_title_fragment(text: str) -> bool:
    text_norm = _normalize(text)
    return (
        any(title_pattern in text_norm for title_pattern in TITLE_PATTERNS)
        or _looks_like_role_text(text)
    )

def _infer_title_and_company(header_lines: List[str]) -> Tuple[str, str]:
    cleaned_headers = []

    for line in header_lines:
        if _is_probable_date_line(line):
            continue

        core = _remove_inline_date(line)
        core = core.split("|")[0].strip()
        core = re.sub(r"\s+", " ", core).strip(" -,")

        if core:
            cleaned_headers.append(core)

    title = ""
    company = ""

    for core in cleaned_headers:
        # Pattern: "Company, Title"
        if "," in core:
            parts = [part.strip(" -,") for part in core.split(",") if part.strip(" -,")]
            if len(parts) >= 2:
                title_candidates = [part for part in parts if _looks_like_title_fragment(part)]
                non_title_candidates = [part for part in parts if part not in title_candidates]

                if title_candidates:
                    title = max(title_candidates, key=len).strip()

                    if non_title_candidates:
                        company = non_title_candidates[0].strip()
                    else:
                        company = parts[0].strip()

                    return title, company

        # Pattern: "Title at Company"
        if " at " in _normalize(core):
            parts = re.split(r"(?i)\s+at\s+", core, maxsplit=1)
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()

                if _looks_like_title_fragment(left):
                    return left, right

                if _looks_like_title_fragment(right):
                    return right, left

        if not title and _looks_like_title_fragment(core):
            title = core
            continue

        if not company:
            company = core

    return title, company

def _looks_like_completed_bullet(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False

    return bool(
        re.search(r"(?:[.!?]\s*$|\b\d+(?:\.\d+)?%$|\b\d+\+?$|\$\d[\d,]*(?:\.\d+)?$)", value)
    )


def _looks_like_unmarked_bullet_start(line: str) -> bool:
    value = str(line or "").strip()
    if not value:
        return False

    if _looks_like_bullet_line(value):
        return False

    if value[:1].islower():
        return False

    first_word_match = re.match(r"^([A-Za-z][A-Za-z\-]+)\b", value)
    if not first_word_match:
        return False

    first_word = first_word_match.group(1).lower()

    if first_word in ACTION_VERB_HINTS:
        return True

    if re.match(r"^[A-Z][a-z]+ed\b", value):
        return True

    return False

def _consolidate_role_bullets(lines: List[str]) -> List[str]:
    bullets: List[str] = []
    current_bullet = ""
    pending_new_bullet = False

    for line in lines:
        raw_line = (line or "").strip()
        if not raw_line:
            continue

        is_bullet_line = _looks_like_bullet_line(raw_line)
        clean_line = _strip_bullet_marker(raw_line)

        # Standalone bullet marker line like "●"
        # Treat it as a hard bullet boundary.
        if is_bullet_line and not clean_line:
            if current_bullet:
                bullets.append(current_bullet.strip())
                current_bullet = ""
            pending_new_bullet = True
            continue

        if not clean_line:
            continue

        if is_bullet_line:
            if current_bullet:
                bullets.append(current_bullet.strip())
            current_bullet = clean_line
            pending_new_bullet = False
            continue

        # If the previous line was only a bullet marker, this line starts a new bullet.
        if pending_new_bullet:
            if current_bullet:
                bullets.append(current_bullet.strip())
            current_bullet = clean_line
            pending_new_bullet = False
            continue

        if (
            current_bullet
            and not pending_new_bullet
            and _looks_like_completed_bullet(current_bullet)
            and _looks_like_unmarked_bullet_start(clean_line)
        ):
            bullets.append(current_bullet.strip())
            current_bullet = clean_line
            continue

        if current_bullet:
            current_bullet = f"{current_bullet} {clean_line}".strip()
        else:
            current_bullet = clean_line

    if current_bullet:
        bullets.append(current_bullet.strip())

    return bullets

def _build_experience_entries(text: str) -> List[ResumeExperienceEntry]:
    experience_lines = _get_section_lines(text, "experience")
    if not experience_lines:
        return []

    blocks = _split_experience_blocks(experience_lines)
    entries: List[ResumeExperienceEntry] = []

    for block_index, block in enumerate(blocks):
        
        header_lines: List[str] = []
        content_lines: List[str] = []

        for line in block:
            raw_line = (line or "").strip()
            if not raw_line:
                continue

            is_bullet_line = _looks_like_bullet_line(raw_line)
            clean_line = _strip_bullet_marker(raw_line)

            already_have_date = any(
                _is_probable_date_line(h) or _extract_inline_date(h)
                for h in header_lines
            )

            # Preserve standalone bullet-marker lines like "●" so
            # _consolidate_role_bullets() can treat them as real bullet boundaries.
            if is_bullet_line and not clean_line:
                content_lines.append(raw_line)
                continue

            if not clean_line:
                continue

            if is_bullet_line:
                content_lines.append(raw_line)
                continue

            if _is_probable_date_line(raw_line) and not already_have_date and len(content_lines) <= 1:
                header_lines.append(clean_line)
                continue

            if (
                not content_lines
                and len(header_lines) < 3
                and (
                    _looks_like_role_header(raw_line)
                    or _is_probable_date_line(raw_line)
                    or _extract_inline_date(raw_line)
                )
            ):
                header_lines.append(clean_line)
                continue

            content_lines.append(raw_line)

        bullet_lines = _consolidate_role_bullets(content_lines)

        if not bullet_lines and len(block) > len(header_lines):
            bullet_lines = _consolidate_role_bullets(block[len(header_lines):])

        if not bullet_lines:
            continue

        title, company = _infer_title_and_company(header_lines)
        date_line = next((line for line in header_lines if _is_probable_date_line(line)), "")
        if not date_line:
            date_line = next(
                (_extract_inline_date(line) for line in header_lines if _extract_inline_date(line)),
                "",
            )

        trimmed_bullets = bullet_lines[:12]
        entry_id = _make_entry_id(
            "experience",
            block_index,
            company,
            title,
            date_line,
            " ".join(header_lines),
        )

        entry = ResumeExperienceEntry(
            entry_id=entry_id,
            entry_index=block_index,
            company=company,
            title=title,
            start_date=date_line,
            end_date="",
            bullets=trimmed_bullets,
            bullet_ids=_make_bullet_ids(entry_id, trimmed_bullets),
        )
        _refresh_experience_entry_structured_fields(entry)
        entries.append(entry)

    if entries:
        return entries

    fallback_bullets = [line for line in experience_lines if len(_strip_bullet_marker(line)) > 15][:12]
    if not fallback_bullets:
        return []

    fallback_clean_bullets = [_strip_bullet_marker(line) for line in fallback_bullets]
    fallback_entry_id = _make_entry_id("experience", 0, "fallback")

    fallback_entry = ResumeExperienceEntry(
        entry_id=fallback_entry_id,
        entry_index=0,
        bullets=fallback_clean_bullets,
        bullet_ids=_make_bullet_ids(fallback_entry_id, fallback_clean_bullets),
    )
    _refresh_experience_entry_structured_fields(fallback_entry)

    return [fallback_entry]


def _build_project_entries(text: str) -> List[ResumeProjectEntry]:
    project_lines = _get_section_lines(text, "projects")
    if not project_lines:
        return []

    bullets = [
        _strip_bullet_marker(line)
        for line in project_lines
        if len(_strip_bullet_marker(line)) > 10
    ]

    if not bullets:
        return []

    trimmed_bullets = bullets[:12]
    entry_id = _make_entry_id("project", 0, "Projects")

    entry = ResumeProjectEntry(
        entry_id=entry_id,
        entry_index=0,
        name="Projects",
        bullets=trimmed_bullets,
        bullet_ids=_make_bullet_ids(entry_id, trimmed_bullets),
    )
    _refresh_project_entry_structured_fields(entry)

    return [entry]


def _build_education_entries(text: str) -> List[ResumeEducationEntry]:
    education_lines = _get_section_lines(text, "education")
    if not education_lines:
        return []

    joined = " ".join(education_lines)
    joined_norm = _normalize(joined)

    degree = ""
    if "master" in joined_norm or "m.s" in joined_norm or "ms " in joined_norm:
        degree = "master"
    elif "bachelor" in joined_norm or "b.s" in joined_norm or "bs " in joined_norm:
        degree = "bachelor"

    return [
        ResumeEducationEntry(
            school=education_lines[0] if education_lines else "",
            degree=degree,
            field_of_study="",
            graduation_date="",
        )
    ]

def _merge_orphan_experience_entries(
    entries: List[ResumeExperienceEntry],
) -> List[ResumeExperienceEntry]:
    if not entries:
        return []

    merged: List[ResumeExperienceEntry] = []

    for entry in entries:
        is_orphan = not entry.title and not entry.company and not entry.start_date

        if is_orphan and merged:
            prev = merged[-1]
            prev.bullets.extend(entry.bullets)
            prev.bullet_ids.extend(entry.bullet_ids)
            prev.normalized_titles = _unique_preserve_order(
                prev.normalized_titles + entry.normalized_titles
            )
            prev.normalized_skills = _unique_preserve_order(
                prev.normalized_skills + entry.normalized_skills
            )
            prev.normalized_methods = _unique_preserve_order(
                prev.normalized_methods + entry.normalized_methods
            )
            prev.normalized_tools = _unique_preserve_order(
                prev.normalized_tools + entry.normalized_tools
            )
            prev.normalized_workflows = _unique_preserve_order(
                prev.normalized_workflows + entry.normalized_workflows
            )
            prev.business_contexts = _unique_preserve_order(
                prev.business_contexts + entry.business_contexts
            )
            prev.stakeholder_contexts = _unique_preserve_order(
                prev.stakeholder_contexts + entry.stakeholder_contexts
            )
            prev.artifact_types = _unique_preserve_order(
                prev.artifact_types + entry.artifact_types
            )
            prev.kpi_metrics = _unique_preserve_order(
                prev.kpi_metrics + entry.kpi_metrics
            )
            prev.ownership_signals = _unique_preserve_order(
                prev.ownership_signals + entry.ownership_signals
            )
            continue

        merged.append(entry)

    return merged

def _experience_entry_counterfactual_text(entry: ResumeExperienceEntry) -> str:
    parts: List[str] = []

    if entry.title:
        parts.append(entry.title)
    if entry.company:
        parts.append(entry.company)
    if entry.location:
        parts.append(entry.location)
    if entry.start_date:
        parts.append(entry.start_date)
    if entry.end_date:
        parts.append(entry.end_date)

    parts.extend(list(entry.bullets or []))
    return " ".join(part for part in parts if str(part or "").strip()).strip()


def _project_entry_counterfactual_text(entry: ResumeProjectEntry) -> str:
    parts: List[str] = []

    if entry.name:
        parts.append(entry.name)

    parts.extend(list(entry.bullets or []))
    return " ".join(part for part in parts if str(part or "").strip()).strip()

def _refresh_experience_entry_structured_fields(entry: ResumeExperienceEntry) -> None:
    entry_text = _experience_entry_counterfactual_text(entry)

    entry.normalized_titles = _extract_pattern_hits(entry_text, TITLE_PATTERNS)
    entry.normalized_skills = _extract_pattern_hits(entry_text, COMMON_SKILL_PATTERNS)
    entry.normalized_methods = _extract_phrase_hits(entry_text, RESUME_METHOD_SIGNAL_PATTERNS)
    entry.normalized_tools = _extract_phrase_hits(entry_text, TOOLING_SIGNAL_PATTERNS)
    entry.normalized_workflows = _extract_phrase_hits(entry_text, RESUME_WORKFLOW_SIGNAL_PATTERNS)
    entry.business_contexts = _extract_phrase_hits(entry_text, RESUME_BUSINESS_CONTEXT_SIGNAL_PATTERNS)
    entry.stakeholder_contexts = _extract_phrase_hits(entry_text, RESUME_STAKEHOLDER_CONTEXT_SIGNAL_PATTERNS)
    entry.artifact_types = _extract_phrase_hits(entry_text, RESUME_ARTIFACT_TYPE_SIGNAL_PATTERNS)
    entry.kpi_metrics = _extract_phrase_hits(entry_text, RESUME_KPI_METRIC_SIGNAL_PATTERNS)
    entry.ownership_signals = _extract_phrase_hits(entry_text, RESUME_OWNERSHIP_SIGNAL_PATTERNS)


def _refresh_project_entry_structured_fields(entry: ResumeProjectEntry) -> None:
    entry_text = _project_entry_counterfactual_text(entry)

    entry.normalized_skills = _extract_pattern_hits(entry_text, COMMON_SKILL_PATTERNS)
    entry.normalized_methods = _extract_phrase_hits(entry_text, RESUME_METHOD_SIGNAL_PATTERNS)
    entry.normalized_tools = _extract_phrase_hits(entry_text, TOOLING_SIGNAL_PATTERNS)
    entry.normalized_workflows = _extract_phrase_hits(entry_text, RESUME_WORKFLOW_SIGNAL_PATTERNS)
    entry.business_contexts = _extract_phrase_hits(entry_text, RESUME_BUSINESS_CONTEXT_SIGNAL_PATTERNS)
    entry.stakeholder_contexts = _extract_phrase_hits(entry_text, RESUME_STAKEHOLDER_CONTEXT_SIGNAL_PATTERNS)
    entry.artifact_types = _extract_phrase_hits(entry_text, RESUME_ARTIFACT_TYPE_SIGNAL_PATTERNS)
    entry.kpi_metrics = _extract_phrase_hits(entry_text, RESUME_KPI_METRIC_SIGNAL_PATTERNS)
    entry.ownership_signals = _extract_phrase_hits(entry_text, RESUME_OWNERSHIP_SIGNAL_PATTERNS)


def _aggregate_resume_structured_fields(
    experience_entries: List[ResumeExperienceEntry],
    project_entries: List[ResumeProjectEntry],
) -> tuple[List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str]]:
    methods = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.normalized_methods or [])]
        + [value for entry in project_entries for value in list(entry.normalized_methods or [])]
    )

    tools = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.normalized_tools or [])]
        + [value for entry in project_entries for value in list(entry.normalized_tools or [])]
    )

    workflows = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.normalized_workflows or [])]
        + [value for entry in project_entries for value in list(entry.normalized_workflows or [])]
    )

    business_contexts = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.business_contexts or [])]
        + [value for entry in project_entries for value in list(entry.business_contexts or [])]
    )

    stakeholder_contexts = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.stakeholder_contexts or [])]
        + [value for entry in project_entries for value in list(entry.stakeholder_contexts or [])]
    )

    artifact_types = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.artifact_types or [])]
        + [value for entry in project_entries for value in list(entry.artifact_types or [])]
    )

    kpi_metrics = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.kpi_metrics or [])]
        + [value for entry in project_entries for value in list(entry.kpi_metrics or [])]
    )

    ownership_signals = _unique_preserve_order(
        [value for entry in experience_entries for value in list(entry.ownership_signals or [])]
        + [value for entry in project_entries for value in list(entry.ownership_signals or [])]
    )

    return (
        methods,
        tools,
        workflows,
        business_contexts,
        stakeholder_contexts,
        artifact_types,
        kpi_metrics,
        ownership_signals,
    )

def rebuild_resume_evidence_from_structured_entries(
    document: ResumeDocument,
    *,
    experience_entries: Optional[List[ResumeExperienceEntry]] = None,
    project_entries: Optional[List[ResumeProjectEntry]] = None,
    education_entries: Optional[List[ResumeEducationEntry]] = None,
    certifications: Optional[List[str]] = None,
) -> ResumeEvidence:
    refreshed_experience_entries = copy.deepcopy(list(experience_entries or []))
    refreshed_project_entries = copy.deepcopy(list(project_entries or []))
    refreshed_education_entries = copy.deepcopy(list(education_entries or []))
    refreshed_certifications = list(certifications or [])

    structured_text_parts: List[str] = []
    quantified_lines: List[str] = []

    for entry in refreshed_experience_entries:
        entry_text = _experience_entry_counterfactual_text(entry)
        _refresh_experience_entry_structured_fields(entry)

        if entry_text:
            structured_text_parts.append(entry_text)

        quantified_lines.extend(
            bullet
            for bullet in (entry.bullets or [])
            if re.search(r"\b\d+(\.\d+)?%|\$\d+|\b\d+\+?\b", bullet or "")
        )

    for entry in refreshed_project_entries:
        entry_text = _project_entry_counterfactual_text(entry)
        _refresh_project_entry_structured_fields(entry)

        if entry_text:
            structured_text_parts.append(entry_text)

        quantified_lines.extend(
            bullet
            for bullet in (entry.bullets or [])
            if re.search(r"\b\d+(\.\d+)?%|\$\d+|\b\d+\+?\b", bullet or "")
        )

    for entry in refreshed_education_entries:
        education_text = " ".join(
            part for part in [
                entry.school,
                entry.degree,
                entry.field_of_study,
                entry.graduation_date,
            ]
            if str(part or "").strip()
        ).strip()
        if education_text:
            structured_text_parts.append(education_text)

    structured_text = "\n".join(part for part in structured_text_parts if part).strip()

    companies = _unique_preserve_order(
        [entry.company for entry in refreshed_experience_entries if entry.company]
    )
    locations = _unique_preserve_order(
        [entry.location for entry in refreshed_experience_entries if entry.location]
    )

    titles = _unique_preserve_order(
        [
            title
            for entry in refreshed_experience_entries
            for title in ([entry.title] if entry.title else []) + list(entry.normalized_titles or [])
        ]
    )

    skills = _unique_preserve_order(
        [
            skill
            for entry in refreshed_experience_entries
            for skill in list(entry.normalized_skills or [])
        ]
        + [
            skill
            for entry in refreshed_project_entries
            for skill in list(entry.normalized_skills or [])
        ]
    )

    (
        methods,
        tools,
        workflows,
        business_contexts,
        stakeholder_contexts,
        artifact_types,
        kpi_metrics,
        ownership_signals,
    ) = _aggregate_resume_structured_fields(
        refreshed_experience_entries,
        refreshed_project_entries,
    )

    return ResumeEvidence(
        document=document,
        titles=titles,
        companies=companies,
        locations=locations,
        skills=skills,
        certifications=refreshed_certifications,
        education_entries=refreshed_education_entries,
        experience_entries=refreshed_experience_entries,
        project_entries=refreshed_project_entries,
        domain_signals=_extract_pattern_hits(structured_text, DOMAIN_SIGNAL_PATTERNS),
        analytics_ml_signals=_extract_pattern_hits(structured_text, ANALYTICS_ML_SIGNAL_PATTERNS),
        experimentation_signals=_extract_pattern_hits(structured_text, EXPERIMENTATION_SIGNAL_PATTERNS),
        tooling_signals=_extract_pattern_hits(structured_text, TOOLING_SIGNAL_PATTERNS),
        quantified_bullets=_unique_preserve_order(quantified_lines),
        notes={
            "builder_version": "v2_counterfactual_structured_refresh",
            "dimension_names": [dimension.name for dimension in get_match_dimensions()],
        },
        methods=methods,
        tools=tools,
        workflows=workflows,
        business_contexts=business_contexts,
        stakeholder_contexts=stakeholder_contexts,
        artifact_types=artifact_types,
        kpi_metrics=kpi_metrics,
        ownership_signals=ownership_signals,
    )


def build_counterfactual_resume_evidence(
    original_resume: ResumeEvidence,
    source_bullet_id: str,
    patch_text: str,
    source_raw_text: str = "",
) -> Tuple[Optional[ResumeEvidence], str]:
    bullet_id = str(source_bullet_id or "").strip()
    replacement = str(patch_text or "").strip()
    original_raw_text = str(source_raw_text or "").strip()

    if not replacement:
        return None, "missing_patch_inputs"

    # Structural/raw-text fallback path:
    # if there is no stable bullet_id anchor, patch the full original bullet text
    # directly in the raw resume document, then rebuild evidence from that document.
    if not bullet_id and original_raw_text:
        patched_document, status = _patched_resume_document(
            original_resume.document,
            original_raw_text,
            replacement,
        )
        if patched_document is None:
            return None, status

        rebuilt_resume = build_resume_evidence(patched_document)
        return rebuilt_resume, "ok"

    if not bullet_id:
        return None, "missing_patch_inputs"

    return build_counterfactual_resume_evidence_for_patches(
        original_resume,
        [
            {
                "source_bullet_id": bullet_id,
                "patch_text": replacement,
            }
        ],
    )

def build_counterfactual_resume_evidence_for_patches(
    original_resume: ResumeEvidence,
    patches: List[dict],
) -> Tuple[Optional[ResumeEvidence], str]:
    cleaned_patches: List[Tuple[str, str, str]] = []
    seen_bullet_ids = set()

    for patch in list(patches or []):
        if not isinstance(patch, dict):
            return None, "invalid_patch_spec"

        bullet_id = str(patch.get("source_bullet_id", "") or "").strip()
        replacement = str(patch.get("patch_text", "") or "").strip()

        if not bullet_id or not replacement:
            return None, "missing_patch_inputs"

        if bullet_id in seen_bullet_ids:
            return None, "duplicate_patch_bullet_id"

        original_bullet_text, status = _bullet_text_by_id(original_resume, bullet_id)
        if original_bullet_text is None:
            return None, status

        seen_bullet_ids.add(bullet_id)
        cleaned_patches.append((bullet_id, original_bullet_text, replacement))

    if not cleaned_patches:
        return None, "missing_patch_inputs"

    patched_document = copy.deepcopy(original_resume.document)

    for _, original_bullet_text, replacement in cleaned_patches:
        patched_document, status = _patched_resume_document(
            patched_document,
            original_bullet_text,
            replacement,
        )
        if patched_document is None:
            return None, status

    rebuilt_resume = build_resume_evidence(patched_document)
    return rebuilt_resume, "ok"

def _bullet_text_by_id(
    resume: ResumeEvidence,
    source_bullet_id: str,
) -> Tuple[Optional[str], str]:
    bullet_id = str(source_bullet_id or "").strip()
    if not bullet_id:
        return None, "missing_patch_inputs"

    matches: List[str] = []

    for entry in list(getattr(resume, "experience_entries", []) or []):
        bullet_ids = list(getattr(entry, "bullet_ids", []) or [])
        bullets = list(getattr(entry, "bullets", []) or [])

        for idx, current_bullet_id in enumerate(bullet_ids):
            if str(current_bullet_id or "").strip() != bullet_id:
                continue

            if idx >= len(bullets):
                return None, "bullet_index_out_of_range"

            matches.append(str(bullets[idx] or "").strip())

    for entry in list(getattr(resume, "project_entries", []) or []):
        bullet_ids = list(getattr(entry, "bullet_ids", []) or [])
        bullets = list(getattr(entry, "bullets", []) or [])

        for idx, current_bullet_id in enumerate(bullet_ids):
            if str(current_bullet_id or "").strip() != bullet_id:
                continue

            if idx >= len(bullets):
                return None, "bullet_index_out_of_range"

            matches.append(str(bullets[idx] or "").strip())

    matches = [text for text in matches if text]

    if not matches:
        return None, "bullet_id_not_found"

    unique_matches = _unique_preserve_order(matches)
    if len(unique_matches) > 1:
        return None, "bullet_id_not_unique"

    return unique_matches[0], "ok"

def _structured_bullet_slot(
    experience_entries: List[ResumeExperienceEntry],
    project_entries: List[ResumeProjectEntry],
    source_bullet_id: str,
) -> Tuple[Optional[Tuple[str, int, int]], str]:
    bullet_id = str(source_bullet_id or "").strip()
    if not bullet_id:
        return None, "missing_patch_inputs"

    matches: List[Tuple[str, int, int]] = []

    for entry_index, entry in enumerate(experience_entries):
        bullet_ids = list(getattr(entry, "bullet_ids", []) or [])
        bullets = list(getattr(entry, "bullets", []) or [])

        for bullet_index, current_bullet_id in enumerate(bullet_ids):
            if str(current_bullet_id or "").strip() != bullet_id:
                continue

            if bullet_index >= len(bullets):
                return None, "bullet_index_out_of_range"

            matches.append(("experience", entry_index, bullet_index))

    for entry_index, entry in enumerate(project_entries):
        bullet_ids = list(getattr(entry, "bullet_ids", []) or [])
        bullets = list(getattr(entry, "bullets", []) or [])

        for bullet_index, current_bullet_id in enumerate(bullet_ids):
            if str(current_bullet_id or "").strip() != bullet_id:
                continue

            if bullet_index >= len(bullets):
                return None, "bullet_index_out_of_range"

            matches.append(("project", entry_index, bullet_index))

    if not matches:
        return None, "bullet_id_not_found"

    if len(matches) > 1:
        return None, "bullet_id_not_unique"

    return matches[0], "ok"

def _whitespace_flexible_pattern(text: str) -> Optional[re.Pattern]:
    normalized = str(text or "").strip()
    if not normalized:
        return None

    parts = [re.escape(part) for part in re.split(r"\s+", normalized) if part]
    if not parts:
        return None

    return re.compile(r"\s+".join(parts))

def _raw_text_fallback_search_texts(text: str) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return []

    candidates: List[str] = [raw]

    de_ellipsized = raw.replace("…", " ").replace("...", " ")
    de_ellipsized = re.sub(r"\s+", " ", de_ellipsized).strip(" .")
    if de_ellipsized and de_ellipsized != raw:
        candidates.append(de_ellipsized)

    return _unique_preserve_order(
        [candidate for candidate in candidates if str(candidate or "").strip()]
    )


def _replace_unique_bullet_line(
    field_value: str,
    original_bullet_text: str,
    patch_text: str,
) -> Tuple[Optional[str], str]:
    raw_field = str(field_value or "")
    search_text = str(original_bullet_text or "").strip()
    replacement = str(patch_text or "").strip()

    if not raw_field or not search_text or not replacement:
        return None, "missing_patch_inputs"

    search_norm = _normalize(search_text)
    if not search_norm:
        return None, "missing_patch_inputs"

    lines = raw_field.splitlines(keepends=True)
    matches: List[Tuple[int, str, str]] = []

    for idx, line in enumerate(lines):
        newline = ""
        if line.endswith("\r\n"):
            newline = "\r\n"
            line_body = line[:-2]
        elif line.endswith("\n"):
            newline = "\n"
            line_body = line[:-1]
        else:
            line_body = line

        bullet_prefix_match = re.match(r"^(\s*[\-\*\u2022\u25CF\u25E6\u2043]+\s*)", line_body)
        bullet_prefix = bullet_prefix_match.group(1) if bullet_prefix_match else ""
        line_core = line_body[len(bullet_prefix):].strip()
        line_norm = _normalize(line_core)

        if not line_norm:
            continue

        if search_norm in line_norm or line_norm in search_norm:
            matches.append((idx, bullet_prefix, newline))

    if not matches:
        return None, "raw_text_bullet_not_found"

    unique_line_indexes = {row[0] for row in matches}
    if len(unique_line_indexes) > 1:
        return None, "raw_text_bullet_not_unique"

    line_index, bullet_prefix, newline = matches[0]
    lines[line_index] = f"{bullet_prefix}{replacement}{newline}"
    return "".join(lines), "ok"

def _patched_resume_document(
    document: ResumeDocument,
    original_bullet_text: str,
    patch_text: str,
) -> Tuple[Optional[ResumeDocument], str]:
    original_bullet = str(original_bullet_text or "").strip()
    replacement = str(patch_text or "").strip()

    if not original_bullet or not replacement:
        return None, "missing_patch_inputs"

    candidate_fields = [
        ("raw_text", str(getattr(document, "raw_text", "") or "")),
        ("text", str(getattr(document, "text", "") or "")),
    ]

    search_texts = _raw_text_fallback_search_texts(original_bullet)

    for search_text in search_texts:
        pattern = _whitespace_flexible_pattern(search_text)
        if pattern is None:
            continue

        for field_name, field_value in candidate_fields:
            if not field_value:
                continue

            matches = list(pattern.finditer(field_value))
            if not matches:
                continue

            if len(matches) > 1:
                return None, "raw_text_bullet_not_unique"

            start, end = matches[0].span()
            patched_value = field_value[:start] + replacement + field_value[end:]

            patched_document = copy.deepcopy(document)

            if field_name == "raw_text":
                patched_document.raw_text = patched_value
                if hasattr(patched_document, "text") and str(getattr(patched_document, "text", "") or "").strip():
                    patched_document.text = patched_value
            else:
                patched_document.text = patched_value
                if hasattr(patched_document, "raw_text") and str(getattr(patched_document, "raw_text", "") or "").strip():
                    patched_document.raw_text = patched_value

            normalized_source = str(
                getattr(patched_document, "raw_text", "") or getattr(patched_document, "text", "") or ""
            )
            patched_document.normalized_text = re.sub(r"\s+", " ", normalized_source).strip()

            return patched_document, "ok"

    for search_text in search_texts:
        for field_name, field_value in candidate_fields:
            if not field_value:
                continue

            patched_value, status = _replace_unique_bullet_line(
                field_value,
                search_text,
                replacement,
            )
            if patched_value is None:
                if status == "raw_text_bullet_not_unique":
                    return None, status
                continue

            patched_document = copy.deepcopy(document)

            if field_name == "raw_text":
                patched_document.raw_text = patched_value
                if hasattr(patched_document, "text") and str(getattr(patched_document, "text", "") or "").strip():
                    patched_document.text = patched_value
            else:
                patched_document.text = patched_value
                if hasattr(patched_document, "raw_text") and str(getattr(patched_document, "raw_text", "") or "").strip():
                    patched_document.raw_text = patched_value

            normalized_source = str(
                getattr(patched_document, "raw_text", "") or getattr(patched_document, "text", "") or ""
            )
            patched_document.normalized_text = re.sub(r"\s+", " ", normalized_source).strip()

            return patched_document, "ok"

    return None, "raw_text_bullet_not_found"

def build_resume_evidence(document: ResumeDocument) -> ResumeEvidence:
    text = document.raw_text
    text_norm = document.normalized_text

    titles = _extract_pattern_hits(text_norm, TITLE_PATTERNS)
    skills = _extract_pattern_hits(text_norm, COMMON_SKILL_PATTERNS)
    domain_signals = _extract_pattern_hits(text_norm, DOMAIN_SIGNAL_PATTERNS)
    analytics_ml_signals = _extract_pattern_hits(text_norm, ANALYTICS_ML_SIGNAL_PATTERNS)
    experimentation_signals = _extract_pattern_hits(text_norm, EXPERIMENTATION_SIGNAL_PATTERNS)
    tooling_signals = _extract_pattern_hits(text_norm, TOOLING_SIGNAL_PATTERNS)
    quantified_bullets = _extract_quantified_lines(text)

    experience_entries = _merge_orphan_experience_entries(
        _build_experience_entries(text)
    )
    project_entries = _build_project_entries(text)
    education_entries = _build_education_entries(text)

    companies = _unique_preserve_order(
        [entry.company for entry in experience_entries if entry.company]
    )
    locations: List[str] = []

    if experience_entries:
        experience_titles = _unique_preserve_order(
            [
                title
                for entry in experience_entries
                for title in ([entry.title] if entry.title else []) + entry.normalized_titles
            ]
        )
        titles = _unique_preserve_order(experience_titles + titles)

        experience_skills = _unique_preserve_order(
            [
                skill
                for entry in experience_entries
                for skill in entry.normalized_skills
            ]
        )
        skills = _unique_preserve_order(experience_skills + skills)

    (
        methods,
        tools,
        workflows,
        business_contexts,
        stakeholder_contexts,
        artifact_types,
        kpi_metrics,
        ownership_signals,
    ) = _aggregate_resume_structured_fields(
        experience_entries,
        project_entries,
    )

    return ResumeEvidence(
        document=document,
        titles=titles,
        companies=companies,
        locations=locations,
        skills=skills,
        certifications=[],
        education_entries=education_entries,
        experience_entries=experience_entries,
        project_entries=project_entries,
        domain_signals=domain_signals,
        analytics_ml_signals=analytics_ml_signals,
        experimentation_signals=experimentation_signals,
        tooling_signals=tooling_signals,
        quantified_bullets=quantified_bullets,
        notes={
            "builder_version": "v2_experience_first",
            "dimension_names": [dimension.name for dimension in get_match_dimensions()],
        },
        methods=methods,
        tools=tools,
        workflows=workflows,
        business_contexts=business_contexts,
        stakeholder_contexts=stakeholder_contexts,
        artifact_types=artifact_types,
        kpi_metrics=kpi_metrics,
        ownership_signals=ownership_signals,
    )
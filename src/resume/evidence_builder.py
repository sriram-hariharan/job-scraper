import re
from typing import List, Optional, Tuple

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
    ROLE_WORD_HINTS
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


def _extract_pattern_hits(text: str, patterns: List[str]) -> List[str]:
    text_norm = _normalize(text)
    hits = [pattern for pattern in patterns if pattern in text_norm]
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

def _consolidate_role_bullets(lines: List[str]) -> List[str]:
    bullets: List[str] = []
    current_bullet = ""

    for line in lines:
        raw_line = (line or "").strip()
        if not raw_line:
            continue

        clean_line = _strip_bullet_marker(raw_line)
        if not clean_line:
            continue

        if _looks_like_bullet_line(raw_line):
            if current_bullet:
                bullets.append(current_bullet.strip())
            current_bullet = clean_line
        else:
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

    for block in blocks:
        
        header_lines: List[str] = []
        content_lines: List[str] = []

        for line in block:
            clean_line = _strip_bullet_marker(line)

            if not clean_line:
                continue

            already_have_date = any(
                _is_probable_date_line(h) or _extract_inline_date(h)
                for h in header_lines
            )

            if _looks_like_bullet_line(line):
                content_lines.append(line)
                continue

            if _is_probable_date_line(line) and not already_have_date and len(content_lines) <= 1:
                header_lines.append(clean_line)
                continue

            if (
                not content_lines
                and len(header_lines) < 3
                and (_looks_like_role_header(line) or _is_probable_date_line(line) or _extract_inline_date(line))
            ):
                header_lines.append(clean_line)
                continue

            content_lines.append(line)

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
        entries.append(
            ResumeExperienceEntry(
                company=company,
                title=title,
                start_date=date_line,
                end_date="",
                bullets=bullet_lines[:12],
                normalized_titles=_extract_pattern_hits(" ".join(header_lines + bullet_lines), TITLE_PATTERNS),
                normalized_skills=_extract_pattern_hits(" ".join(header_lines + bullet_lines), COMMON_SKILL_PATTERNS),
            )
        )

    if entries:
        return entries

    fallback_bullets = [line for line in experience_lines if len(_strip_bullet_marker(line)) > 15][:12]
    if not fallback_bullets:
        return []

    return [
        ResumeExperienceEntry(
            bullets=[_strip_bullet_marker(line) for line in fallback_bullets],
            normalized_titles=_extract_pattern_hits(" ".join(fallback_bullets), TITLE_PATTERNS),
            normalized_skills=_extract_pattern_hits(" ".join(fallback_bullets), COMMON_SKILL_PATTERNS),
        )
    ]


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

    return [
        ResumeProjectEntry(
            name="Projects",
            bullets=bullets[:12],
            normalized_skills=_extract_pattern_hits(" ".join(bullets), COMMON_SKILL_PATTERNS),
        )
    ]


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
            prev.normalized_titles = _unique_preserve_order(
                prev.normalized_titles + entry.normalized_titles
            )
            prev.normalized_skills = _unique_preserve_order(
                prev.normalized_skills + entry.normalized_skills
            )
            continue

        merged.append(entry)

    return merged

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
    )
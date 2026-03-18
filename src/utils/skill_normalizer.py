import re
from src.config.consts import (
    ALIAS_MAP,
    DROP_EXACT,
    SQL_FRAGMENT_TERMS,
    COMMON_SKILL_PATTERNS,
    TOOLING_SIGNAL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
)

def normalize_skill(skill: str) -> str | None:
    if not skill:
        return None

    s = skill.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(".,;:()[]{}")

    if not s:
        return None

    if s != "a/b testing" and "/" in s:
        parts = [p.strip() for p in s.split("/") if p.strip()]
        if len(parts) >= 2 and parts[0] in {"sql", "statistics"}:
            s = parts[-1]

    s = ALIAS_MAP.get(s, s)

    if s in DROP_EXACT:
        return None

    if s in SQL_FRAGMENT_TERMS:
        return "sql"

    if "years of experience" in s:
        return None
    if "degree" in s:
        return None
    if "bachelor" in s or "master" in s or "phd" in s:
        return None

    if s in {
        "data visualizations",
        "data visualization",
        "cloud data platforms",
        "cloud data warehouses",
        "data pipeline orchestration tools",
        "bi and data visualization tools",
        "advanced sql proficiency",
        "strong cs fundamentals",
        "ai literacy and curiosity",
    }:
        return None

    return s


_GENERIC_CANONICAL_EXCLUDE = {
    "analytics",
    "data science",
    "data analysis",
    "analysis",
}

_SEED_CANONICAL_SKILLS = (
    COMMON_SKILL_PATTERNS
    + TOOLING_SIGNAL_PATTERNS
    + EXPERIMENTATION_SIGNAL_PATTERNS
    + list(ALIAS_MAP.keys())
    + list(ALIAS_MAP.values())
)

KNOWN_CANONICAL_SKILLS = set()
for raw_skill in _SEED_CANONICAL_SKILLS:
    normalized = normalize_skill(raw_skill)
    if normalized and normalized not in _GENERIC_CANONICAL_EXCLUDE:
        KNOWN_CANONICAL_SKILLS.add(normalized)


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _appears_verbatim_in_job_text(skill: str, job_text: str) -> bool:
    skill_norm = _normalize_for_match(skill)
    job_norm = _normalize_for_match(job_text)

    if not skill_norm or not job_norm:
        return False

    candidates = [skill_norm]

    simplified = re.sub(r"\s*\([^)]*\)", "", skill_norm).strip()
    if simplified and simplified not in candidates:
        candidates.append(simplified)

    for candidate in candidates:
        pattern = rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])"
        if re.search(pattern, job_norm):
            return True

    return False


def normalize_extracted_skill(skill: str, job_text: str) -> str | None:
    s = normalize_skill(skill)
    if not s:
        return None

    if len(s.split()) > 4:
        return None

    if not _appears_verbatim_in_job_text(s, job_text):
        return None

    if s in KNOWN_CANONICAL_SKILLS:
        return s

    # Reject vague/domain/capability phrases by default unless they look like concrete skills.
    if re.search(r"\b(familiarity|experience|ability|background|proficiency|knowledge|understanding)\b", s):
        return None

    if s.endswith(" tool") or s.endswith(" tools") or s.endswith(" platform") or s.endswith(" platforms"):
        return None

    if s.endswith(" skills") or s == "skills":
        return None

    if s in {"deployment", "monitoring", "analysis", "adtech", "ctv"}:
        return None

    if re.search(r"\b(automated|model|performance|defect|data|fundamental|classical)\b", s) and re.search(
        r"\b(retraining|monitoring|tracking|identification|exploration|inspection|principles|algorithms)\b", s
    ):
        return None

    if s.endswith(" pipelines"):
        return None

    # Allow only concrete-looking unknowns.
    token_count = len(s.split())
    if token_count == 1:
        # single unknown token is OK only if it looks like a concrete tool/token
        if not re.fullmatch(r"[a-z0-9\+#\.-]{2,}", s):
            return None
        return s

    if token_count in {2, 3}:
        # allow short noun phrases with concrete technical shapes
        if re.fullmatch(r"[a-z0-9\+#\.-]+(?: [a-z0-9\+#\.-]+){1,2}", s):
            return s

    return None


def normalize_extracted_skills(skills: list[str], job_text: str) -> list[str]:
    normalized = []
    seen = set()

    for skill in skills:
        s = normalize_extracted_skill(skill, job_text)
        if not s:
            continue
        if s not in seen:
            seen.add(s)
            normalized.append(s)

    return normalized


def normalize_skills(skills: list[str]) -> list[str]:
    normalized = []
    seen = set()

    for skill in skills:
        s = normalize_skill(skill)

        if not s:
            continue

        if s not in seen:
            seen.add(s)
            normalized.append(s)

    return normalized
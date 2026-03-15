import re
from src.config.consts import (
    ALIAS_MAP,
    DROP_EXACT,
    SQL_FRAGMENT_TERMS
)

def normalize_skill(skill: str) -> str | None:
    if not skill:
        return None

    s = skill.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(".,;:()[]{}")

    if not s:
        return None

    # slash cleanup
    if s != "a/b testing" and "/" in s:
        parts = [p.strip() for p in s.split("/") if p.strip()]

        if len(parts) >= 2:
            if parts[0] in {"sql", "statistics"}:
                s = parts[-1]

    s = ALIAS_MAP.get(s, s)

    if s in DROP_EXACT:
        return None

    if s in SQL_FRAGMENT_TERMS:
        return "sql"

    # drop obvious experience / education phrases
    if "years of experience" in s:
        return None
    if "degree" in s:
        return None
    if "bachelor" in s or "master" in s or "phd" in s:
        return None

    # drop vague skill-category phrases
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
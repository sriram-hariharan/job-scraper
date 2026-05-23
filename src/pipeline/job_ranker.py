from datetime import datetime, timezone
import re

from src.config.consts import TITLE_INCLUDE_REGEX, TITLE_EXCLUDE_REGEX
from src.config.role_taxonomy import compile_role_title_regexes


WHITESPACE_REGEX = re.compile(r"\s+")
PUNCT_REGEX = re.compile(r"[^\w\s]")


def _role_title_regexes(selected_role_families=None):
    if selected_role_families:
        return compile_role_title_regexes(selected_role_families)

    return TITLE_INCLUDE_REGEX, TITLE_EXCLUDE_REGEX


def title_score(title: str, selected_role_families=None):

    if not title:
        return 0

    t = title.lower()
    include_regexes, exclude_regexes = _role_title_regexes(selected_role_families)

    for r in exclude_regexes:
        if r.search(t):
            return -100

    score = 0

    for r in include_regexes:
        if r.search(t):
            score += 25

    return score


def _normalize_preference_list(values):
    if not values:
        return []
    raw_values = values if isinstance(values, (list, tuple, set)) else [values]
    normalized = []
    for value in raw_values:
        text = WHITESPACE_REGEX.sub(" ", str(value or "").strip().lower())
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def classify_seniority(title: str) -> str:
    text = f" {WHITESPACE_REGEX.sub(' ', str(title or '').lower())} "
    if re.search(r"\b(manager|director|vp|vice president|head of)\b", text):
        return "manager_or_above"
    if re.search(r"\b(staff|principal|lead|member of technical staff|mts)\b", text):
        return "staff_or_above"
    if re.search(r"\b(senior|sr)\b", text):
        return "senior"
    if re.search(r"\b(entry|junior|jr|new grad|graduate|associate)\b", text):
        return "entry"
    if re.search(r"\b(mid|software engineer ii|engineer ii|level 2)\b", text):
        return "mid"
    return "unknown"


def _normalized_job_text(job):
    metadata = job.get("metadata") if isinstance(job.get("metadata"), dict) else {}
    skills = []
    for key in ("required_skills", "preferred_skills", "all_skills", "skills"):
        value = job.get(key) or metadata.get(key)
        if isinstance(value, list):
            skills.extend(str(item or "") for item in value)
        elif value:
            skills.append(str(value))

    parts = [
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("source"),
        job.get("url"),
        job.get("job_url"),
        job.get("summary"),
        job.get("description"),
        job.get("description_text"),
        *skills,
    ]
    text = " ".join(str(part or "") for part in parts if str(part or "").strip()).lower()
    text = PUNCT_REGEX.sub(" ", text)
    return WHITESPACE_REGEX.sub(" ", text).strip()


def _preference_phrase_matches(text, preferences):
    matches = []
    for preference in _normalize_preference_list(preferences):
        needle = PUNCT_REGEX.sub(" ", preference)
        needle = WHITESPACE_REGEX.sub(" ", needle).strip()
        if needle and re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", text):
            matches.append(preference)
    return matches


def preferred_location_matches(job, preferred_locations=None):
    location_text = _normalized_job_text({"location": job.get("location")})
    return _preference_phrase_matches(location_text, preferred_locations)


def preferred_skill_matches(job, preferred_skills=None):
    return _preference_phrase_matches(_normalized_job_text(job), preferred_skills)


def preference_score(
    job,
    *,
    target_seniority=None,
    preferred_locations=None,
    preferred_skills=None,
):
    score = 0
    seniority = classify_seniority(job.get("title", ""))
    job["_preference_seniority"] = seniority
    job["_preference_seniority_match"] = False
    job["_preference_seniority_unknown"] = False

    target_seniority_values = set(_normalize_preference_list(target_seniority))
    if target_seniority_values:
        if seniority in target_seniority_values:
            job["_preference_seniority_match"] = True
            score += 4
        elif seniority == "unknown":
            job["_preference_seniority_unknown"] = True

    location_matches = preferred_location_matches(job, preferred_locations=preferred_locations)
    if location_matches:
        job["_preference_location_matches"] = location_matches
        score += 4
    else:
        job["_preference_location_matches"] = []

    skill_matches = preferred_skill_matches(job, preferred_skills=preferred_skills)
    if skill_matches:
        job["_preference_skill_matches"] = skill_matches
        score += min(6, len(skill_matches) * 2)
    else:
        job["_preference_skill_matches"] = []

    return score


def recency_score(posted_at):

    if not posted_at:
        return 0

    try:
        dt = datetime.fromisoformat(posted_at.replace("Z","+00:00"))
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except:
        return 0

    if hours <= 6:
        return 30
    elif hours <= 24:
        return 20
    elif hours <= 72:
        return 10

    return 0


def momentum_score(company, momentum_map):

    if not company:
        return 0

    company = company.lower()

    delta = momentum_map.get(company, 0)

    if delta >= 20:
        return 20
    elif delta >= 10:
        return 10
    elif delta >= 5:
        return 5

    return 0


def score_job(
    job,
    momentum_map,
    selected_role_families=None,
    target_seniority=None,
    preferred_locations=None,
    preferred_skills=None,
):

    score = 0

    score += title_score(job.get("title",""), selected_role_families=selected_role_families)
    score += recency_score(job.get("posted_at"))
    score += momentum_score(job.get("company"), momentum_map)
    score += preference_score(
        job,
        target_seniority=target_seniority,
        preferred_locations=preferred_locations,
        preferred_skills=preferred_skills,
    )

    return score


def rank_jobs(
    jobs,
    momentum_map=None,
    selected_role_families=None,
    target_seniority=None,
    preferred_locations=None,
    preferred_skills=None,
):

    if momentum_map is None:
        momentum_map = {}

    for job in jobs:
        job["_score"] = score_job(
            job,
            momentum_map,
            selected_role_families=selected_role_families,
            target_seniority=target_seniority,
            preferred_locations=preferred_locations,
            preferred_skills=preferred_skills,
        )

    jobs.sort(key=lambda x: x["_score"], reverse=True)

    return jobs

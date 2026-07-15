from __future__ import annotations

import copy
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


LOCATION_DATA_VERSION = "us-census-gazetteer-places-2025-v1"
DEFAULT_LOCATION_DATA_PATH = (
    Path(__file__).with_name("location_data") / "us_locations_v1.json"
)
SUPPORTED_LOCATION_TYPES = {"state", "city", "remote", "nationwide", "legacy_text"}
LOCATION_EVIDENCE_FIELD = "_location_preference_evidence"
MAX_LOCATION_SEARCH_QUERY_LENGTH = 80
MAX_LOCATION_SEARCH_RESULTS = 20

_SPACE_RE = re.compile(r"\s+")
_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MULTI_LOCATION_SEPARATOR_RE = re.compile(r"\s*(?:;|\||/|\n|\bor\b)\s*", re.IGNORECASE)
_REMOTE_RE = re.compile(r"\bremote\b", re.IGNORECASE)
_REMOTE_PREFIX_RE = re.compile(r"^\s*remote\s*(?:[-,:]|in)?\s*", re.IGNORECASE)
_US_SUFFIX_RE = re.compile(
    r"\s*,?\s*(?:united states(?: of america)?|u\.?s\.?a?\.?)\s*$",
    re.IGNORECASE,
)
_NATIONWIDE_VALUES = {
    "us",
    "u s",
    "usa",
    "u s a",
    "united states",
    "united states of america",
    "nationwide",
    "anywhere in the united states",
}


def normalize_location_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[._]+", " ", text)
    text = re.sub(r"\s*-\s*", " - ", text)
    return _SPACE_RE.sub(" ", text).strip(" ,;|/-")


def _location_slug(value: Any) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", str(value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    return _SLUG_RE.sub("-", ascii_text).strip("-")


@lru_cache(maxsize=4)
def load_us_location_data(path: str = str(DEFAULT_LOCATION_DATA_PATH)) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("version") != LOCATION_DATA_VERSION:
        raise ValueError("Unsupported US location data version.")

    states = payload.get("states")
    places = payload.get("places")
    if not isinstance(states, list) or not isinstance(places, list):
        raise ValueError("US location data must contain state and place lists.")

    state_by_code: Dict[str, str] = {}
    state_aliases: Dict[str, str] = {}
    for state in states:
        code = str(state.get("code") or "").strip().upper()
        name = str(state.get("name") or "").strip()
        if not code or not name:
            raise ValueError("US location data contains a malformed state.")
        state_by_code[code] = name
        state_aliases[normalize_location_text(code)] = code
        state_aliases[normalize_location_text(name)] = code

    city_by_state_and_name: Dict[Tuple[str, str], Dict[str, str]] = {}
    states_by_city_name: Dict[str, List[str]] = {}
    for place in places:
        if not isinstance(place, list) or len(place) != 3:
            raise ValueError("US location data contains a malformed place.")
        state_code, city, normalized_city = [str(value or "").strip() for value in place]
        state_code = state_code.upper()
        if state_code not in state_by_code or not city or not normalized_city:
            raise ValueError("US location data contains an invalid place entry.")
        canonical = {
            "type": "city",
            "city": city,
            "state_code": state_code,
            "state_name": state_by_code[state_code],
            "country_code": "US",
            "display_name": f"{city}, {state_code}",
        }
        city_by_state_and_name[(state_code, normalized_city)] = canonical
        states_for_city = states_by_city_name.setdefault(normalized_city, [])
        if state_code not in states_for_city:
            states_for_city.append(state_code)

    return {
        "version": payload["version"],
        "source": dict(payload.get("source") or {}),
        "state_by_code": state_by_code,
        "state_aliases": state_aliases,
        "city_by_state_and_name": city_by_state_and_name,
        "states_by_city_name": states_by_city_name,
        "place_count": len(city_by_state_and_name),
    }


def _state_spec(state_code: str, data: Dict[str, Any]) -> Dict[str, str]:
    code = state_code.upper()
    state_name = data["state_by_code"][code]
    return {
        "id": f"us:{code.casefold()}",
        "type": "state",
        "display_name": state_name,
        "state_code": code,
        "state_name": state_name,
        "country_code": "US",
    }


def _city_spec(city: Dict[str, str]) -> Dict[str, str]:
    code = city["state_code"]
    return {
        "id": f"us:{code.casefold()}:{_location_slug(city['city'])}",
        **city,
    }


def _remote_spec() -> Dict[str, str]:
    return {
        "id": "remote:us",
        "type": "remote",
        "display_name": "Remote (US)",
        "country_code": "US",
    }


def _nationwide_spec() -> Dict[str, str]:
    return {
        "id": "us:nationwide",
        "type": "nationwide",
        "display_name": "United States",
        "country_code": "US",
    }


def _legacy_spec(value: Any) -> Dict[str, str]:
    display_name = _SPACE_RE.sub(" ", str(value or "").strip())
    normalized = normalize_location_text(display_name)
    slug = _location_slug(normalized)
    if not normalized or not slug:
        raise ValueError("Legacy location text cannot be empty.")
    return {
        "id": f"legacy:{slug}",
        "type": "legacy_text",
        "display_name": display_name,
        "legacy_text": normalized,
        "country_code": "US",
    }


def _strip_us_suffix(value: str) -> str:
    return _US_SUFFIX_RE.sub("", value).strip(" ,")


def _city_state_from_text(value: Any, data: Dict[str, Any]) -> Dict[str, str] | None:
    text = _strip_us_suffix(str(value or "").strip())
    normalized = normalize_location_text(text)
    aliases = sorted(data["state_aliases"], key=len, reverse=True)
    for alias in aliases:
        if normalized == alias:
            continue
        suffix = f" {alias}"
        comma_suffix = f", {alias}"
        if normalized.endswith(comma_suffix):
            city_name = normalized[: -len(comma_suffix)].strip()
        elif normalized.endswith(suffix):
            city_name = normalized[: -len(suffix)].strip(" ,")
        else:
            continue
        state_code = data["state_aliases"][alias]
        city = data["city_by_state_and_name"].get((state_code, city_name))
        if city:
            return _city_spec(city)
    return None


def canonicalize_location_text(
    value: Any,
    *,
    data_path: Path = DEFAULT_LOCATION_DATA_PATH,
) -> Dict[str, str]:
    display_text = _SPACE_RE.sub(" ", str(value or "").strip())
    if not display_text:
        raise ValueError("Location preference cannot be empty.")

    data = load_us_location_data(str(data_path))
    normalized = normalize_location_text(display_text)
    normalized_without_wrappers = re.sub(r"[(),]", " ", normalized)
    normalized_without_wrappers = _SPACE_RE.sub(" ", normalized_without_wrappers).strip()
    if _REMOTE_RE.search(display_text) and normalized_without_wrappers in {
        "remote",
        "remote us",
        "remote usa",
        "remote united states",
        "remote united states of america",
    }:
        return _remote_spec()
    if normalized in _NATIONWIDE_VALUES:
        return _nationwide_spec()
    if normalized in data["state_aliases"]:
        return _state_spec(data["state_aliases"][normalized], data)

    city = _city_state_from_text(display_text, data)
    if city:
        return city
    return _legacy_spec(display_text)


def _require_exact_keys(spec: Dict[str, Any], required: set[str], allowed: set[str]) -> None:
    missing = required - set(spec)
    unknown = set(spec) - allowed
    if missing or unknown:
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(sorted(missing))}")
        if unknown:
            details.append(f"unsupported keys: {', '.join(sorted(unknown))}")
        raise ValueError("Malformed location specification (" + "; ".join(details) + ").")


def validate_location_spec(
    value: Any,
    *,
    data_path: Path = DEFAULT_LOCATION_DATA_PATH,
) -> Dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("Each preferred location specification must be an object.")
    spec = {str(key): item for key, item in value.items()}
    location_type = str(spec.get("type") or "").strip()
    if location_type not in SUPPORTED_LOCATION_TYPES:
        raise ValueError(f"Unsupported preferred location type: {location_type!r}.")
    if str(spec.get("country_code") or "").strip().upper() != "US":
        raise ValueError("Preferred location country_code must be US.")

    common = {"id", "type", "display_name", "country_code"}
    type_keys = {
        "state": {"state_code", "state_name"},
        "city": {"city", "state_code", "state_name"},
        "remote": set(),
        "nationwide": set(),
        "legacy_text": {"legacy_text"},
    }
    required = common | type_keys[location_type]
    _require_exact_keys(spec, required, required)

    if location_type == "remote":
        canonical = _remote_spec()
    elif location_type == "nationwide":
        canonical = _nationwide_spec()
    elif location_type == "legacy_text":
        canonical = _legacy_spec(spec["display_name"])
        if normalize_location_text(spec["legacy_text"]) != canonical["legacy_text"]:
            raise ValueError("Legacy location text does not match display_name.")
    else:
        data = load_us_location_data(str(data_path))
        state_code = str(spec["state_code"] or "").strip().upper()
        if state_code not in data["state_by_code"]:
            raise ValueError(f"Unknown US state code: {state_code!r}.")
        if location_type == "state":
            canonical = _state_spec(state_code, data)
        else:
            normalized_city = normalize_location_text(spec["city"])
            city = data["city_by_state_and_name"].get((state_code, normalized_city))
            if not city:
                raise ValueError("Unknown city and state combination.")
            canonical = _city_spec(city)

    normalized_input = {
        key: str(value or "").strip().upper() if key in {"state_code", "country_code"}
        else str(value or "").strip()
        for key, value in spec.items()
    }
    if normalized_input != canonical:
        raise ValueError("Preferred location specification does not match its canonical ID or fields.")
    return canonical


def normalize_location_specs(
    values: Any,
    *,
    legacy_locations: Any = None,
    data_path: Path = DEFAULT_LOCATION_DATA_PATH,
) -> List[Dict[str, str]]:
    if values is None:
        raw_values: List[Any] = []
    elif isinstance(values, list):
        raw_values = values
    else:
        raise ValueError("preferred_location_specs must be a list.")

    if not raw_values and legacy_locations:
        legacy_values = legacy_locations if isinstance(legacy_locations, list) else [legacy_locations]
        raw_values = [canonicalize_location_text(item, data_path=data_path) for item in legacy_values]

    normalized: List[Dict[str, str]] = []
    seen_ids = set()
    for value in raw_values:
        canonical = validate_location_spec(value, data_path=data_path)
        if canonical["id"] in seen_ids:
            continue
        seen_ids.add(canonical["id"])
        normalized.append(canonical)
    return normalized


def search_us_location_specs(
    query: Any,
    *,
    limit: int = 15,
    data_path: Path = DEFAULT_LOCATION_DATA_PATH,
) -> List[Dict[str, str]]:
    """Return a small, deterministic set of public canonical location specs."""
    if not isinstance(query, str):
        raise ValueError("Location search query must be text.")
    cleaned_query = _SPACE_RE.sub(" ", query).strip()
    if not cleaned_query:
        return []
    if len(cleaned_query) > MAX_LOCATION_SEARCH_QUERY_LENGTH:
        raise ValueError(
            f"Location search query must be {MAX_LOCATION_SEARCH_QUERY_LENGTH} characters or fewer."
        )
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("Location search limit must be an integer.")
    if limit < 1 or limit > MAX_LOCATION_SEARCH_RESULTS:
        raise ValueError(
            f"Location search limit must be between 1 and {MAX_LOCATION_SEARCH_RESULTS}."
        )

    data = load_us_location_data(str(data_path))
    normalized_query = normalize_location_text(cleaned_query)
    ranked: List[Tuple[Tuple[Any, ...], Dict[str, str]]] = []

    def add_candidate(spec: Dict[str, str], match_rank: int) -> None:
        type_rank = {
            "remote": 0,
            "nationwide": 1,
            "state": 2,
            "city": 3,
        }[spec["type"]]
        ranked.append(
            (
                (
                    match_rank,
                    type_rank,
                    spec["display_name"].casefold(),
                    spec.get("state_code", ""),
                    spec["id"],
                ),
                spec,
            )
        )

    special_candidates = (
        (_remote_spec(), ("remote", "remote us")),
        (_nationwide_spec(), tuple(sorted(_NATIONWIDE_VALUES))),
    )
    for spec, aliases in special_candidates:
        display_normalized = normalize_location_text(spec["display_name"])
        if normalized_query == display_normalized or normalized_query in aliases:
            add_candidate(spec, 0)
        elif any(alias.startswith(normalized_query) for alias in aliases):
            add_candidate(spec, 3)
        elif normalized_query in display_normalized or any(
            normalized_query in alias for alias in aliases
        ):
            add_candidate(spec, 6)

    for state_code, state_name in data["state_by_code"].items():
        spec = _state_spec(state_code, data)
        name_normalized = normalize_location_text(state_name)
        code_normalized = normalize_location_text(state_code)
        if normalized_query == name_normalized:
            add_candidate(spec, 0)
        elif normalized_query == code_normalized:
            add_candidate(spec, 1)
        elif name_normalized.startswith(normalized_query) or code_normalized.startswith(
            normalized_query
        ):
            add_candidate(spec, 3)
        elif normalized_query in name_normalized:
            add_candidate(spec, 5)

    for city in data["city_by_state_and_name"].values():
        spec = _city_spec(city)
        city_normalized = normalize_location_text(city["city"])
        display_normalized = normalize_location_text(spec["display_name"])
        full_state_normalized = normalize_location_text(
            f"{city['city']} {city['state_name']}"
        )
        if normalized_query in {display_normalized, full_state_normalized, city_normalized}:
            add_candidate(spec, 2)
        elif city_normalized.startswith(normalized_query) or display_normalized.startswith(
            normalized_query
        ):
            add_candidate(spec, 4)
        elif normalized_query in display_normalized or normalized_query in full_state_normalized:
            add_candidate(spec, 6)

    ranked.sort(key=lambda item: item[0])
    return [copy.deepcopy(spec) for _sort_key, spec in ranked[:limit]]


def _parsed_location_from_spec(spec: Dict[str, str]) -> Dict[str, str]:
    return {key: value for key, value in spec.items() if key != "id" and key != "legacy_text"}


def _location_segments(raw_text: str, data: Dict[str, Any]) -> List[str]:
    explicit_segments = [
        segment.strip()
        for segment in _MULTI_LOCATION_SEPARATOR_RE.split(raw_text)
        if segment.strip()
    ]
    expanded: List[str] = []
    for segment in explicit_segments:
        comma_parts = [part.strip() for part in segment.split(",") if part.strip()]
        repeated_pairs: List[str] = []
        if len(comma_parts) >= 4 and len(comma_parts) % 2 == 0:
            for index in range(0, len(comma_parts), 2):
                state_alias = normalize_location_text(comma_parts[index + 1])
                if state_alias not in data["state_aliases"]:
                    repeated_pairs = []
                    break
                repeated_pairs.append(f"{comma_parts[index]}, {comma_parts[index + 1]}")
        expanded.extend(repeated_pairs or [segment])
    return expanded


def parse_job_location(
    value: Any,
    *,
    data_path: Path = DEFAULT_LOCATION_DATA_PATH,
) -> Dict[str, Any]:
    raw_text = " ; ".join(str(item or "") for item in value) if isinstance(value, list) else str(value or "")
    raw_text = raw_text.strip()
    if not raw_text:
        return {"locations": [], "ambiguous": False, "unknown": True}

    data = load_us_location_data(str(data_path))
    locations: List[Dict[str, str]] = []
    seen = set()
    ambiguous = False
    unknown = False

    def add(spec: Dict[str, str]) -> None:
        parsed = _parsed_location_from_spec(spec)
        key = (parsed["type"], parsed.get("state_code", ""), parsed.get("city", ""))
        if key not in seen:
            seen.add(key)
            locations.append(parsed)

    if _REMOTE_RE.search(raw_text):
        add(_remote_spec())

    segments = _location_segments(raw_text, data)
    for segment in segments:
        segment_without_remote = _REMOTE_PREFIX_RE.sub("", segment).strip()
        if not segment_without_remote:
            continue
        normalized_segment = normalize_location_text(segment_without_remote)
        if normalized_segment in _NATIONWIDE_VALUES:
            add(_nationwide_spec())
            continue

        city = _city_state_from_text(segment_without_remote, data)
        if city:
            add(city)
            continue

        stripped = _strip_us_suffix(segment_without_remote)
        normalized_stripped = normalize_location_text(stripped)
        if normalized_stripped in data["state_aliases"]:
            add(_state_spec(data["state_aliases"][normalized_stripped], data))
            continue

        states_for_city = data["states_by_city_name"].get(normalized_stripped, [])
        if len(states_for_city) == 1:
            city_data = data["city_by_state_and_name"][(states_for_city[0], normalized_stripped)]
            add(_city_spec(city_data))
        elif len(states_for_city) > 1:
            ambiguous = True
        elif not _REMOTE_RE.fullmatch(segment.strip()):
            unknown = True

    return {"locations": locations, "ambiguous": ambiguous, "unknown": unknown and not locations}


def match_job_location(
    job_location: Any,
    preferred_location_specs: Sequence[Dict[str, Any]] | None,
    *,
    data_path: Path = DEFAULT_LOCATION_DATA_PATH,
) -> Dict[str, Any]:
    preferences = normalize_location_specs(
        list(preferred_location_specs or []),
        data_path=data_path,
    )
    parsed = parse_job_location(job_location, data_path=data_path)
    normalized_locations = parsed["locations"]

    evidence: Dict[str, Any] = {
        "matched": False,
        "match_type": "",
        "matched_preference_ids": [],
        "normalized_job_locations": normalized_locations,
        "fallback_retained": False,
        "reason_code": "no_location_preferences" if not preferences else "no_preferred_location_match",
    }
    if not preferences:
        return evidence

    matched_by_reason: Dict[str, List[str]] = {
        "preferred_city_state_match": [],
        "preferred_state_match": [],
        "preferred_remote_match": [],
        "preferred_nationwide_match": [],
        "legacy_text_match": [],
    }
    normalized_raw = normalize_location_text(job_location)
    for preference in preferences:
        location_type = preference["type"]
        for location in normalized_locations:
            if (
                location_type == "city"
                and location.get("type") == "city"
                and location.get("city") == preference["city"]
                and location.get("state_code") == preference["state_code"]
            ):
                matched_by_reason["preferred_city_state_match"].append(preference["id"])
            elif (
                location_type == "state"
                and location.get("state_code") == preference["state_code"]
            ):
                matched_by_reason["preferred_state_match"].append(preference["id"])
            elif location_type == "remote" and location.get("type") == "remote":
                matched_by_reason["preferred_remote_match"].append(preference["id"])
            elif location_type == "nationwide" and location.get("type") == "nationwide":
                matched_by_reason["preferred_nationwide_match"].append(preference["id"])

        if location_type == "legacy_text" and preference["legacy_text"] in normalized_raw:
            matched_by_reason["legacy_text_match"].append(preference["id"])

    for reason_code, matched_ids in matched_by_reason.items():
        if matched_ids:
            evidence.update(
                {
                    "matched": True,
                    "match_type": reason_code,
                    "matched_preference_ids": list(dict.fromkeys(matched_ids)),
                    "reason_code": reason_code,
                }
            )
            return evidence

    if parsed["ambiguous"]:
        evidence["reason_code"] = "ambiguous_city_without_state"
    elif parsed["unknown"]:
        evidence["reason_code"] = "unknown_job_location"
    return evidence


def apply_location_preference_policy(
    jobs: Iterable[Dict[str, Any]],
    preferred_location_specs: Sequence[Dict[str, Any]] | None,
    location_strict_match: bool,
    location_show_others_if_unmatched: bool,
    *,
    data_path: Path = DEFAULT_LOCATION_DATA_PATH,
) -> Dict[str, Any]:
    if not isinstance(location_strict_match, bool):
        raise ValueError("location_strict_match must be a boolean.")
    if not isinstance(location_show_others_if_unmatched, bool):
        raise ValueError("location_show_others_if_unmatched must be a boolean.")

    annotated = []
    for job in jobs:
        copied_job = copy.deepcopy(job)
        copied_job[LOCATION_EVIDENCE_FIELD] = match_job_location(
            copied_job.get("location"),
            preferred_location_specs,
            data_path=data_path,
        )
        annotated.append(copied_job)

    matched = [job for job in annotated if job[LOCATION_EVIDENCE_FIELD]["matched"]]
    nonmatched = [job for job in annotated if not job[LOCATION_EVIDENCE_FIELD]["matched"]]
    rejected: List[Dict[str, Any]] = []
    fallback_activated = False

    if not location_strict_match:
        retained = annotated
    elif matched:
        retained = matched
        rejected = nonmatched
        for job in rejected:
            job[LOCATION_EVIDENCE_FIELD]["reason_code"] = "strict_location_rejected"
    elif location_show_others_if_unmatched:
        retained = annotated
        fallback_activated = True
        for job in retained:
            job[LOCATION_EVIDENCE_FIELD].update(
                {
                    "fallback_retained": True,
                    "reason_code": "fallback_retained_zero_strict_matches",
                }
            )
    else:
        retained = []
        rejected = annotated
        for job in rejected:
            job[LOCATION_EVIDENCE_FIELD]["reason_code"] = "strict_location_rejected"

    return {
        "retained_jobs": retained,
        "rejected_jobs": rejected,
        "diagnostics": {
            "input_count": len(annotated),
            "matched_count": len(matched),
            "retained_count": len(retained),
            "rejected_count": len(rejected),
            "strict_match": location_strict_match,
            "show_others_if_unmatched": location_show_others_if_unmatched,
            "show_others_inactive": bool(
                location_show_others_if_unmatched and not location_strict_match
            ),
            "fallback_activated": fallback_activated,
        },
    }

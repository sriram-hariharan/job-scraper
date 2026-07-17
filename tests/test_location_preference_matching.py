import copy
import json
from collections import Counter
from pathlib import Path

import pytest

from src.pipeline.location_preferences import (
    LOCATION_EVIDENCE_FIELD,
    apply_location_preference_policy,
    canonicalize_location_text,
    load_us_location_data,
    match_job_location,
    normalize_location_specs,
    parse_job_location,
    validate_location_spec,
)


DATA_PATH = Path("src/pipeline/location_data/us_locations_v1.json")
PROVENANCE_PATH = Path("src/pipeline/location_data/us_locations_v1.PROVENANCE.md")


def _spec(value):
    return canonicalize_location_text(value)


def _reason(location, preference):
    return match_job_location(location, [_spec(preference)])["reason_code"]


def test_checked_in_census_artifact_is_versioned_compact_and_preserves_cross_state_names():
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    counts = Counter(place[2] for place in payload["places"])

    assert payload["version"] == "us-census-gazetteer-places-2025-v1"
    assert payload["source"]["organization"] == "United States Census Bureau"
    assert payload["source"]["year"] == 2025
    assert len(payload["places"]) == 32126
    assert sum(1 for count in counts.values() if count > 1) == 4063
    assert DATA_PATH.stat().st_size == 1006648
    assert "2025_Gaz_place_national.zip" in PROVENANCE_PATH.read_text(encoding="utf-8")
    assert load_us_location_data()["place_count"] == 32126


def test_state_city_remote_nationwide_and_legacy_canonicalization_is_deterministic():
    virginia = _spec("Virginia")
    assert virginia == _spec("VA")
    assert virginia["id"] == "us:va"

    arlington = _spec("Arlington, VA")
    assert arlington == _spec("Arlington, Virginia")
    assert arlington["id"] == "us:va:arlington"
    assert arlington["display_name"] == "Arlington, VA"

    assert _spec("Remote (US)")["id"] == "remote:us"
    assert _spec("United States")["id"] == "us:nationwide"
    assert _spec("Somewhere Special") == {
        "id": "legacy:somewhere-special",
        "type": "legacy_text",
        "display_name": "Somewhere Special",
        "legacy_text": "somewhere special",
        "country_code": "US",
    }


@pytest.mark.parametrize(
    "job_location",
    [
        "Virginia",
        "Virginia, United States",
        "VA",
        "Arlington, VA",
        "Arlington, Virginia",
        "Richmond, VA",
        "Remote - Virginia",
    ],
)
def test_virginia_state_preference_matches_required_forms(job_location):
    assert _reason(job_location, "Virginia") == "preferred_state_match"


@pytest.mark.parametrize(
    "job_location",
    ["Arlington, TX", "Washington, DC", "United States", "Remote"],
)
def test_virginia_state_preference_rejects_unrelated_forms(job_location):
    assert _reason(job_location, "Virginia") == "no_preferred_location_match"


@pytest.mark.parametrize(
    "job_location",
    ["Arlington, VA", "Arlington, Virginia", "Remote - Arlington, VA"],
)
def test_arlington_city_preference_matches_only_with_virginia_context(job_location):
    assert _reason(job_location, "Arlington, VA") == "preferred_city_state_match"


def test_ambiguous_city_without_state_is_not_silently_reinterpreted():
    evidence = match_job_location("Arlington", [_spec("Arlington, VA")])
    assert evidence["matched"] is False
    assert evidence["reason_code"] == "ambiguous_city_without_state"

    multi = match_job_location("Bellevue; San Jose", [_spec("Virginia")])
    assert multi["normalized_job_locations"] == []
    assert multi["reason_code"] == "ambiguous_city_without_state"


@pytest.mark.parametrize(
    "job_location",
    [
        "Broomfield, Colorado, United States",
        "Broomfield, CO",
        "Broomfield, Colorado; Fort Collins, Colorado",
        "Denver, CO or Austin, TX",
    ],
)
def test_colorado_state_preference_matches_multi_location_forms(job_location):
    evidence = match_job_location(job_location, [_spec("Colorado")])
    assert evidence["matched"] is True
    assert evidence["reason_code"] == "preferred_state_match"


def test_multi_location_evidence_preserves_matching_and_nonmatching_locations():
    evidence = match_job_location("Denver, CO or Austin, TX", [_spec("Colorado")])
    assert [location["display_name"] for location in evidence["normalized_job_locations"]] == [
        "Denver, CO",
        "Austin, TX",
    ]

    comma_separated = parse_job_location("Denver, CO, Austin, TX")
    assert [
        location["display_name"] for location in comma_separated["locations"]
    ] == ["Denver, CO", "Austin, TX"]


@pytest.mark.parametrize(
    "job_location",
    ["Remote", "Remote, US", "Remote - United States", "Remote - Virginia"],
)
def test_remote_preference_matches_required_forms(job_location):
    assert _reason(job_location, "Remote (US)") == "preferred_remote_match"


@pytest.mark.parametrize(
    "job_location",
    ["United States", "US", "USA", "Nationwide", "Anywhere in the United States"],
)
def test_nationwide_preference_matches_required_forms(job_location):
    assert _reason(job_location, "United States") == "preferred_nationwide_match"


def test_unknown_location_and_no_preferences_have_distinct_reasons():
    unknown = match_job_location("Planetary HQ", [_spec("Virginia")])
    assert unknown["reason_code"] == "unknown_job_location"
    no_preferences = match_job_location("Virginia", [])
    assert no_preferences["reason_code"] == "no_location_preferences"


def test_location_specs_dedupe_by_canonical_id_and_reject_malformed_objects_atomically():
    virginia = _spec("Virginia")
    assert normalize_location_specs([virginia, dict(virginia)]) == [virginia]

    malformed = dict(virginia, id="us:tx")
    with pytest.raises(ValueError, match="canonical ID"):
        normalize_location_specs([virginia, malformed])
    with pytest.raises(ValueError, match="country_code must be US"):
        validate_location_spec(dict(virginia, country_code="CA"))


def test_policy_strict_off_retains_order_and_does_not_mutate_input_for_both_fallback_values():
    jobs = [{"id": "a", "location": "Austin, TX"}, {"id": "b", "location": "Richmond, VA"}]
    original = copy.deepcopy(jobs)
    for show_others in (False, True):
        result = apply_location_preference_policy(jobs, [_spec("Virginia")], False, show_others)
        assert [job["id"] for job in result["retained_jobs"]] == ["a", "b"]
        assert result["rejected_jobs"] == []
        assert result["diagnostics"]["show_others_inactive"] is show_others
    assert jobs == original


def test_policy_strict_on_without_fallback_retains_only_matches_and_marks_rejections():
    jobs = [{"id": "a", "location": "Austin, TX"}, {"id": "b", "location": "Richmond, VA"}]
    result = apply_location_preference_policy(jobs, [_spec("Virginia")], True, False)

    assert [job["id"] for job in result["retained_jobs"]] == ["b"]
    assert [job["id"] for job in result["rejected_jobs"]] == ["a"]
    assert result["rejected_jobs"][0][LOCATION_EVIDENCE_FIELD]["reason_code"] == "strict_location_rejected"


def test_policy_strict_on_with_fallback_still_rejects_nonmatches_when_match_exists():
    jobs = [{"id": "a", "location": "Richmond, VA"}, {"id": "b", "location": "Austin, TX"}]
    result = apply_location_preference_policy(jobs, [_spec("Virginia")], True, True)
    assert [job["id"] for job in result["retained_jobs"]] == ["a"]
    assert result["diagnostics"]["fallback_activated"] is False


def test_policy_strict_on_with_zero_matches_retains_all_as_fallback_in_stable_order():
    jobs = [{"id": "a", "location": "Austin, TX"}, {"id": "b", "location": "Denver, CO"}]
    result = apply_location_preference_policy(jobs, [_spec("Virginia")], True, True)
    assert [job["id"] for job in result["retained_jobs"]] == ["a", "b"]
    assert result["rejected_jobs"] == []
    assert result["diagnostics"]["fallback_activated"] is True
    assert all(
        job[LOCATION_EVIDENCE_FIELD]["fallback_retained"] is True
        and job[LOCATION_EVIDENCE_FIELD]["reason_code"]
        == "fallback_retained_zero_strict_matches"
        for job in result["retained_jobs"]
    )


def test_policy_rejects_non_boolean_flags():
    with pytest.raises(ValueError, match="location_strict_match must be a boolean"):
        apply_location_preference_policy([], [], 1, False)
    with pytest.raises(ValueError, match="location_show_others_if_unmatched must be a boolean"):
        apply_location_preference_policy([], [], False, "yes")

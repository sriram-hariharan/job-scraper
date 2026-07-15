from pathlib import Path

import pytest

from src.app import services
from src.pipeline.location_preferences import search_us_location_specs


def _names(query: str, limit: int = 15) -> list[str]:
    return [item["display_name"] for item in search_us_location_specs(query, limit=limit)]


def test_exact_state_abbreviation_and_state_prefix_rank_before_city_results():
    assert _names("VA", 5)[0] == "Virginia"
    assert _names("Vir", 5)[0] == "Virginia"


def test_city_prefix_results_keep_state_context_and_are_deterministic():
    first = search_us_location_specs("Arlington", limit=20)
    second = search_us_location_specs("Arlington", limit=20)

    assert first == second
    assert "Arlington, VA" in [item["display_name"] for item in first]
    assert "Arlington, TX" in [item["display_name"] for item in first]
    assert all(item["type"] == "city" and item["state_code"] for item in first)


def test_remote_nationwide_and_known_city_queries_return_canonical_specs():
    remote = search_us_location_specs("Remote", limit=10)
    nationwide = search_us_location_specs("United States", limit=10)
    city = search_us_location_specs("Broomfield", limit=10)

    assert remote[0] == {
        "id": "remote:us",
        "type": "remote",
        "display_name": "Remote (US)",
        "country_code": "US",
    }
    assert nationwide[0]["id"] == "us:nationwide"
    assert city[0]["display_name"] == "Broomfield, CO"


def test_search_is_bounded_public_and_rejects_invalid_input_safely():
    payload = services.onboarding_location_search_payload("San", limit=12)

    assert payload["count"] <= 12
    assert payload["results"]
    assert all("source" not in item and "path" not in item for item in payload["results"])
    assert services.onboarding_location_search_payload("   ", limit=12)["results"] == []
    with pytest.raises(ValueError, match="80 characters or fewer"):
        services.onboarding_location_search_payload("x" * 81, limit=12)
    with pytest.raises(ValueError, match="between 1 and 20"):
        services.onboarding_location_search_payload("Virginia", limit=21)


def test_location_search_route_is_authenticated_read_only_and_owner_data_free():
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    route = api_source.split('@app.get("/onboarding/location-search")', 1)[1].split(
        '@app.post("/onboarding/preferences")', 1
    )[0]

    assert "_require_auth_owner_user_id(http_request)" in route
    assert "services.onboarding_location_search_payload(q, limit=limit)" in route
    assert "owner_user_id=" not in route
    assert "Body(" not in route

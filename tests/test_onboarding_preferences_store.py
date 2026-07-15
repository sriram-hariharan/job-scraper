from src.storage.onboarding_preferences.store import (
    onboarding_preferences_schema_sql_text,
    upsert_onboarding_preferences_payload,
    validate_onboarding_preferences_payload,
)


def test_onboarding_preferences_schema_contains_table_name():
    sql = onboarding_preferences_schema_sql_text()

    assert "CREATE TABLE IF NOT EXISTS user_onboarding_preferences" in sql
    assert "owner_user_id TEXT PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE" in sql
    assert "selected_role_families JSONB NOT NULL DEFAULT '[]'::jsonb" in sql
    assert "preferred_location_specs JSONB NOT NULL DEFAULT '[]'::jsonb" in sql
    assert "location_strict_match BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "location_show_others_if_unmatched BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "ADD COLUMN IF NOT EXISTS preferred_location_specs" in sql


def test_valid_preferences_normalize_and_save_payload_shape_print_only():
    payload = upsert_onboarding_preferences_payload(
        "user_123",
        {
            "onboarding_completed": True,
            "selected_role_families": ["backend_engineering"],
            "target_seniority": ["senior"],
            "preferred_locations": ["Virginia", "Arlington, VA"],
            "location_strict_match": True,
            "location_show_others_if_unmatched": True,
            "preferred_skills": ["Python", "Postgres"],
            "excluded_keywords": ["intern"],
        },
        print_only=True,
    )

    assert payload["data"]["found"] is True
    assert payload["data"]["owner_user_id"] == "user_123"
    assert payload["data"]["preferences"] == {
        "onboarding_completed": True,
        "selected_role_families": ["backend_engineering"],
        "target_seniority": ["senior"],
        "preferred_locations": ["Virginia", "Arlington, VA"],
        "preferred_location_specs": [
            {
                "id": "us:va",
                "type": "state",
                "display_name": "Virginia",
                "state_code": "VA",
                "state_name": "Virginia",
                "country_code": "US",
            },
            {
                "id": "us:va:arlington",
                "type": "city",
                "display_name": "Arlington, VA",
                "city": "Arlington",
                "state_code": "VA",
                "state_name": "Virginia",
                "country_code": "US",
            },
        ],
        "location_strict_match": True,
        "location_show_others_if_unmatched": True,
        "preferred_skills": ["Python", "Postgres"],
        "excluded_keywords": ["intern"],
    }
    assert "INSERT INTO user_onboarding_preferences" in payload["sql"]


def test_invalid_role_family_is_rejected():
    try:
        validate_onboarding_preferences_payload(
            {"selected_role_families": ["backend_engineering", "not_real"]}
        )
    except ValueError as exc:
        assert "Unknown role family id" in str(exc)
    else:
        raise AssertionError("Expected invalid role family id to be rejected.")


def test_onboarding_completed_requires_selected_role_family():
    try:
        validate_onboarding_preferences_payload(
            {"onboarding_completed": True, "selected_role_families": []}
        )
    except ValueError as exc:
        assert "onboarding_completed cannot be true" in str(exc)
    else:
        raise AssertionError("Expected completed onboarding without roles to be rejected.")


def test_valid_role_family_list_is_deduped_and_order_preserved():
    normalized = validate_onboarding_preferences_payload(
        {
            "selected_role_families": [
                "backend_engineering",
                "backend_engineering",
                "qa_automation",
                "backend_engineering",
            ],
            "preferred_skills": ["Python", "Python", "SQL"],
        }
    )

    assert normalized["selected_role_families"] == [
        "backend_engineering",
        "qa_automation",
    ]
    assert normalized["preferred_skills"] == ["Python", "SQL"]


def test_work_modes_input_is_ignored_for_backward_compatible_reads():
    normalized = validate_onboarding_preferences_payload(
        {
            "selected_role_families": ["backend_engineering"],
            "work_modes": ["remote"],
        }
    )

    assert "work_modes" not in normalized


def test_existing_location_strings_are_canonicalized_without_discarding_unknown_values():
    normalized = validate_onboarding_preferences_payload(
        {
            "preferred_locations": [
                "VA",
                "Arlington, Virginia",
                "Somewhere Special",
            ]
        }
    )

    assert normalized["preferred_locations"] == [
        "Virginia",
        "Arlington, VA",
        "Somewhere Special",
    ]
    assert [spec["id"] for spec in normalized["preferred_location_specs"]] == [
        "us:va",
        "us:va:arlington",
        "legacy:somewhere-special",
    ]
    assert normalized["location_strict_match"] is False
    assert normalized["location_show_others_if_unmatched"] is False


def test_structured_locations_round_trip_to_display_strings_and_dedupe_by_id():
    virginia = {
        "id": "us:va",
        "type": "state",
        "display_name": "Virginia",
        "state_code": "VA",
        "state_name": "Virginia",
        "country_code": "US",
    }
    normalized = validate_onboarding_preferences_payload(
        {
            "preferred_locations": ["stale display"],
            "preferred_location_specs": [virginia, dict(virginia)],
        }
    )

    assert normalized["preferred_locations"] == ["Virginia"]
    assert normalized["preferred_location_specs"] == [virginia]


def test_location_policy_flags_require_actual_booleans():
    for field_name in (
        "location_strict_match",
        "location_show_others_if_unmatched",
    ):
        try:
            validate_onboarding_preferences_payload({field_name: 1})
        except ValueError as exc:
            assert f"{field_name} must be a boolean" in str(exc)
        else:
            raise AssertionError(f"Expected {field_name} integer to be rejected.")


def test_print_only_sql_persists_canonical_locations_and_owner_scope():
    payload = upsert_onboarding_preferences_payload(
        "owner_a",
        {
            "preferred_locations": ["Virginia"],
            "location_strict_match": True,
        },
        print_only=True,
    )

    assert "ON CONFLICT (owner_user_id)" in payload["sql"]
    assert "'owner_a'" in payload["sql"]
    assert "preferred_location_specs" in payload["sql"]
    assert "location_strict_match" in payload["sql"]
    assert payload["data"]["owner_user_id"] == "owner_a"
    assert payload["data"]["preferences"]["preferred_location_specs"][0]["id"] == "us:va"

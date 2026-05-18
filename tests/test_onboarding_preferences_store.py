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


def test_valid_preferences_normalize_and_save_payload_shape_print_only():
    payload = upsert_onboarding_preferences_payload(
        "user_123",
        {
            "onboarding_completed": True,
            "selected_role_families": ["backend_engineering"],
            "target_seniority": ["senior"],
            "preferred_locations": ["New York", "Remote"],
            "work_modes": ["remote"],
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
        "preferred_locations": ["New York", "Remote"],
        "work_modes": ["remote"],
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

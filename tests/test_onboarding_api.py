import sys
import types


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))

from src.app import services


def _patch_onboarding_storage(*, resume_count=0):
    captured = {}

    def fake_profile_resumes_payload(*, owner_user_id=""):
        return {
            "ok": True,
            "count": int(resume_count),
            "resumes": [{"resume_name": "resume.pdf"}] if int(resume_count) else [],
        }

    def fake_get_preferences(owner_user_id, **kwargs):
        return {
            "data": {
                "found": False,
                "owner_user_id": owner_user_id,
                "preferences": services.validate_onboarding_preferences_payload({}),
            }
        }

    def fake_upsert_preferences(owner_user_id, preferences, **kwargs):
        captured["owner_user_id"] = owner_user_id
        captured["preferences"] = dict(preferences)
        return {
            "data": {
                "found": True,
                "owner_user_id": owner_user_id,
                "preferences": dict(preferences),
            }
        }

    original_profile = services.profile_resumes_payload
    original_get = services.get_onboarding_preferences_postgres_payload
    original_upsert = services.upsert_onboarding_preferences_postgres_payload
    services.profile_resumes_payload = fake_profile_resumes_payload
    services.get_onboarding_preferences_postgres_payload = fake_get_preferences
    services.upsert_onboarding_preferences_postgres_payload = fake_upsert_preferences
    return captured, original_profile, original_get, original_upsert


def _restore_onboarding_storage(originals):
    original_profile, original_get, original_upsert = originals
    services.profile_resumes_payload = original_profile
    services.get_onboarding_preferences_postgres_payload = original_get
    services.upsert_onboarding_preferences_postgres_payload = original_upsert


def test_onboarding_preferences_requires_authenticated_user():
    try:
        services.onboarding_preferences_payload(owner_user_id="")
    except ValueError as exc:
        assert "Authenticated user is required" in str(exc)
    else:
        raise AssertionError("Expected onboarding preferences to require authentication.")


def test_valid_onboarding_preferences_save():
    captured, *originals = _patch_onboarding_storage(resume_count=1)
    try:
        payload = services.save_onboarding_preferences_payload(
            {
                "onboarding_completed": False,
                "selected_role_families": ["backend_engineering"],
                "preferred_skills": ["Python", "Python", "Postgres"],
            },
            owner_user_id="user_123",
        )
    finally:
        _restore_onboarding_storage(originals)

    assert payload["ok"] is True
    assert payload["preferences"]["selected_role_families"] == ["backend_engineering"]
    assert payload["preferences"]["preferred_skills"] == ["Python", "Postgres"]
    assert captured["owner_user_id"] == "user_123"


def test_invalid_onboarding_role_is_rejected():
    captured, *originals = _patch_onboarding_storage(resume_count=1)
    try:
        try:
            services.save_onboarding_preferences_payload(
                {"selected_role_families": ["not_a_role"]},
                owner_user_id="user_123",
            )
        except ValueError as exc:
            assert "Unknown role family id" in str(exc)
        else:
            raise AssertionError("Expected invalid role family to be rejected.")
    finally:
        _restore_onboarding_storage(originals)

    assert captured == {}


def test_cannot_complete_onboarding_without_resume():
    captured, *originals = _patch_onboarding_storage(resume_count=0)
    try:
        try:
            services.save_onboarding_preferences_payload(
                {
                    "onboarding_completed": True,
                    "selected_role_families": ["backend_engineering"],
                },
                owner_user_id="user_123",
            )
        except ValueError as exc:
            assert "one profile resume exists" in str(exc)
        else:
            raise AssertionError("Expected completion without a profile resume to be rejected.")
    finally:
        _restore_onboarding_storage(originals)

    assert captured == {}


def test_can_complete_onboarding_with_profile_resume():
    captured, *originals = _patch_onboarding_storage(resume_count=1)
    try:
        payload = services.save_onboarding_preferences_payload(
            {
                "onboarding_completed": True,
                "selected_role_families": ["backend_engineering"],
            },
            owner_user_id="user_123",
        )
    finally:
        _restore_onboarding_storage(originals)

    assert payload["ok"] is True
    assert payload["preferences"]["onboarding_completed"] is True
    assert payload["requirements"]["can_complete_onboarding"] is True
    assert captured["preferences"]["selected_role_families"] == ["backend_engineering"]

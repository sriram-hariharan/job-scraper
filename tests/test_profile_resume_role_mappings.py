from pathlib import Path

from src.storage.profile_resumes.store import (
    delete_profile_resume_role_mapping_payload,
    profile_resume_role_mapping_schema_sql_text,
    upsert_profile_resume_role_mapping_payload,
    validate_profile_resume_role_mapping_payload,
)


def test_valid_mapping_payload_normalizes_shape():
    payload = validate_profile_resume_role_mapping_payload(
        {
            "owner_user_id": "user-1",
            "resume_name": "resume.pdf",
            "role_family_id": "backend_engineering",
            "is_default_for_role": True,
        }
    )

    assert payload == {
        "owner_user_id": "user-1",
        "resume_name": "resume.pdf",
        "role_family_id": "backend_engineering",
        "is_default_for_role": True,
    }


def test_invalid_role_family_is_rejected():
    try:
        validate_profile_resume_role_mapping_payload(
            {
                "owner_user_id": "user-1",
                "resume_name": "resume.pdf",
                "role_family_id": "not_a_role",
            }
        )
    except ValueError as exc:
        assert "Unknown role family id" in str(exc)
    else:
        raise AssertionError("invalid role family should be rejected")


def test_invalid_resume_name_is_rejected():
    for resume_name in ("", "../resume.pdf"):
        try:
            validate_profile_resume_role_mapping_payload(
                {
                    "owner_user_id": "user-1",
                    "resume_name": resume_name,
                    "role_family_id": "backend_engineering",
                }
            )
        except ValueError:
            continue
        raise AssertionError(f"invalid resume name should be rejected: {resume_name!r}")


def test_one_default_per_role_is_enforced_in_schema_and_upsert_sql():
    schema_sql = profile_resume_role_mapping_schema_sql_text()
    assert "profile_resume_role_mappings" in schema_sql
    assert "idx_profile_resume_role_mappings_one_default" in schema_sql
    assert "WHERE is_default_for_role" in schema_sql

    payload = upsert_profile_resume_role_mapping_payload(
        owner_user_id="user-1",
        resume_name="resume.pdf",
        role_family_id="backend_engineering",
        is_default_for_role=True,
        print_only=True,
    )

    assert payload["data"]["mapping"]["is_default_for_role"] is True
    assert "clear_existing_default" in payload["sql"]
    assert "INSERT INTO profile_resume_role_mappings" in payload["sql"]


def test_mapping_delete_payload_shape():
    payload = delete_profile_resume_role_mapping_payload(
        owner_user_id="user-1",
        resume_name="resume.pdf",
        role_family_id="backend_engineering",
        print_only=True,
    )

    assert payload["data"] == {
        "deleted": True,
        "resume_name": "resume.pdf",
        "role_family_id": "backend_engineering",
    }
    assert "DELETE FROM profile_resume_role_mappings" in payload["sql"]


def test_profile_ui_contract_for_resume_role_mapping_controls():
    profile_js = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    profile_ui = Path("src/app/profile_ui.py").read_text(encoding="utf-8")

    assert "/profile/resume-role-mappings" in profile_js
    assert "data-resume-role-toggle" in profile_js
    assert "data-resume-role-default" in profile_js
    assert "profile_resume_roles_r8" in profile_ui

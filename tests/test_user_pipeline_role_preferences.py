import asyncio
import json
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)
from src.pipeline.job_filter import filter_jobs
from src.pipeline.job_ranker import rank_jobs
from src.pipeline.location_preferences import canonicalize_location_text
from src.pipeline import collector, runtime_status
from src.app import services


def _job(title):
    return {
        "title": title,
        "company": "Acme",
        "location": "United States",
        "source": "jobvite",
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }


def _usajobs_job(title, **overrides):
    job = {
        "title": title,
        "company": "Federal Agency",
        "location": "Washington, District of Columbia",
        "source": "usajobs",
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "description": "Sanitized federal vacancy description.",
        "description_text": "Sanitized federal vacancy description.",
    }
    job.update(overrides)
    return job


def _write_launch_config(path, preferences):
    path.write_text(
        json.dumps(
            {
                "config_kind": "live_pipeline_launch_options",
                "options": {"preferences": preferences},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_pipeline_preference_defaults_include_location_policy(monkeypatch):
    expected = {
        "preferred_location_specs": [],
        "location_strict_match": False,
        "location_show_others_if_unmatched": False,
    }
    assert {
        field: services._preferences_for_pipeline("")[field]
        for field in expected
    } == expected

    monkeypatch.setattr(
        services,
        "get_onboarding_preferences_postgres_payload",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    assert {
        field: services._preferences_for_pipeline("user_123")[field]
        for field in expected
    } == expected


def test_user_backend_role_allows_backend_job_through_filter():
    jobs = [_job("Backend Engineer")]

    filtered = filter_jobs(jobs, selected_role_families=["backend_engineering"])

    assert [job["title"] for job in filtered] == ["Backend Engineer"]


def test_user_data_science_only_rejects_backend_job():
    jobs = [_job("Backend Engineer")]

    filtered = filter_jobs(jobs, selected_role_families=["data_science"])

    assert filtered == []


def test_missing_preferences_preserves_default_data_ai_behavior():
    jobs = [_job("Backend Engineer"), _job("Data Scientist")]

    filtered = filter_jobs(jobs, selected_role_families=None)

    assert [job["title"] for job in filtered] == ["Data Scientist"]


@pytest.mark.parametrize(
    ("role_family", "selected_title", "unselected_title"),
    [
        ("systems_it", "Systems Engineer", "Security Engineer"),
        ("security", "Security Analyst", "Cloud Engineer"),
        ("software_engineering", "Software Developer", "Data Engineer"),
        ("cloud_devops", "Cloud Infrastructure Engineer", "Systems Administrator"),
        ("data_engineering", "Data Engineer", "Data Scientist"),
        ("data_science", "Data Scientist", "Analytics Engineer"),
        ("analytics", "Data Analyst", "Software Engineer"),
    ],
)
def test_usajobs_titles_use_selected_central_role_family_only(
    role_family,
    selected_title,
    unselected_title,
):
    filtered = filter_jobs(
        [_usajobs_job(selected_title), _usajobs_job(unselected_title)],
        selected_role_families=[role_family],
    )
    assert [job["title"] for job in filtered] == [selected_title]


def test_usajobs_uses_default_central_families_when_none_selected():
    filtered = filter_jobs(
        [_usajobs_job("Data Scientist"), _usajobs_job("Systems Engineer")],
        selected_role_families=None,
    )
    assert [job["title"] for job in filtered] == ["Data Scientist"]


def test_usajobs_central_seniority_and_excluded_keyword_contracts_are_unchanged():
    jobs = [
        _usajobs_job("Senior Data Scientist"),
        _usajobs_job(
            "Data Scientist",
            description_text="Intern program for data scientists.",
        ),
    ]
    filtered = filter_jobs(
        jobs,
        selected_role_families=["data_science"],
        target_seniority=["senior"],
        seniority_strict_match=True,
        excluded_keywords=["intern"],
    )
    assert [job["title"] for job in filtered] == ["Senior Data Scientist"]


class _FakeProcess:
    pid = 4242

    def poll(self):
        return None


class _FakeJobApp:
    def _build_main_cmd(self, args, planning_only=False):
        return ["python", "main.py"]


def _install_pipeline_gate_inputs(
    monkeypatch,
    *,
    resume_count=1,
    configured=False,
    successful_runs=0,
):
    monkeypatch.setattr(
        services,
        "profile_resumes_payload",
        lambda **_kwargs: {"count": resume_count},
    )
    monkeypatch.setattr(
        services,
        "get_user_pipeline_runs_postgres_payload",
        lambda **_kwargs: {
            "total_row_count": successful_runs,
            "rows": [{}] if successful_runs else [],
        },
    )
    monkeypatch.setattr(
        services,
        "user_ai_settings_readiness_payload",
        lambda **_kwargs: {
            "providers": {
                "openai": {
                    "configured": configured,
                    "credential_hint": "must-not-leak",
                    "credential": "must-not-leak",
                },
            },
        },
    )


def test_pipeline_gate_requires_one_configured_ai_provider_without_changing_delete_seen(monkeypatch):
    _install_pipeline_gate_inputs(
        monkeypatch,
        configured=False,
        successful_runs=1,
    )

    gate = services.user_pipeline_gate_payload(owner_user_id="owner-ai-gate")

    assert gate["can_run_live_pipeline"] is False
    assert gate["has_configured_ai_provider"] is False
    assert gate["requires_ai_provider_setup"] is True
    assert gate["can_delete_seen_data"] is True
    assert gate["live_pipeline_block_reason"] == (
        "Configure at least one AI provider API key in AI Settings before "
        "running the live pipeline."
    )
    assert gate["profile_ai_settings_url"] == "/profile/ai-settings"
    assert gate["profile_ai_settings_url"] != "/profile#ai-settings"
    serialized_gate = json.dumps(gate)
    assert "credential_hint" not in serialized_gate
    assert "api_key" not in serialized_gate
    assert "must-not-leak" not in serialized_gate


def test_pipeline_gate_allows_ready_owner_with_one_configured_ai_provider(monkeypatch):
    _install_pipeline_gate_inputs(monkeypatch, configured=True)

    gate = services.user_pipeline_gate_payload(owner_user_id="owner-ai-ready")

    assert gate["can_run_live_pipeline"] is True
    assert gate["has_configured_ai_provider"] is True
    assert gate["requires_ai_provider_setup"] is False
    assert gate["live_pipeline_block_reason"] == ""


def test_pipeline_gate_preserves_resume_blocker_precedence(monkeypatch):
    _install_pipeline_gate_inputs(monkeypatch, resume_count=0, configured=False)

    gate = services.user_pipeline_gate_payload(owner_user_id="owner-missing-both")

    assert gate["requires_resume_upload"] is True
    assert gate["requires_ai_provider_setup"] is True
    assert gate["live_pipeline_block_reason"] == (
        "Upload at least one resume before running Live Pipeline."
    )
    assert gate["profile_resume_upload_url"] == "/profile?onboarding=resume_upload"


def test_pipeline_gate_fails_closed_safely_when_ai_readiness_is_unavailable(monkeypatch):
    _install_pipeline_gate_inputs(monkeypatch, configured=True)
    monkeypatch.setattr(
        services,
        "user_ai_settings_readiness_payload",
        lambda **_kwargs: (_ for _ in ()).throw(SystemExit("sensitive storage detail")),
    )

    gate = services.user_pipeline_gate_payload(owner_user_id="owner-ai-error")

    assert gate["can_run_live_pipeline"] is False
    assert gate["ai_provider_readiness_available"] is False
    assert gate["live_pipeline_block_reason"] == (
        "AI provider configuration readiness is unavailable. "
        "Try again before running the live pipeline."
    )
    assert "sensitive storage detail" not in json.dumps(gate)


def test_direct_pipeline_launch_with_zero_configured_providers_never_starts_process(monkeypatch):
    _install_pipeline_gate_inputs(monkeypatch, configured=False)
    popen = pytest.fail
    monkeypatch.setattr(services.subprocess, "Popen", popen)

    with pytest.raises(ValueError, match="Configure at least one AI provider API key"):
        services.run_live_pipeline_payload(owner_user_id="owner-ai-blocked")



def test_selected_role_families_appear_in_pipeline_run_config_and_launch_config_not_child_env():
    captured = {}
    boston_spec = canonicalize_location_text("Boston, MA")
    originals = {
        "user_pipeline_gate_payload": services.user_pipeline_gate_payload,
        "get_onboarding_preferences_postgres_payload": services.get_onboarding_preferences_postgres_payload,
        "_owner_active_pipeline_state": services._owner_active_pipeline_state,
        "_job_app": services._job_app,
        "_pipeline_scratch_output_dir": services._pipeline_scratch_output_dir,
        "_user_pipeline_redis_admission_lock_payload": services._user_pipeline_redis_admission_lock_payload,
        "reserve_user_pipeline_active_run_postgres_payload": services.reserve_user_pipeline_active_run_postgres_payload,
        "_set_owner_active_pipeline_state": services._set_owner_active_pipeline_state,
        "_persist_user_pipeline_status_snapshot": services._persist_user_pipeline_status_snapshot,
        "Popen": services.subprocess.Popen,
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        def fake_popen(cmd, stdout=None, stderr=None, env=None):
            captured["cmd"] = cmd
            captured["env"] = dict(env or {})
            captured["launch_config"] = json.loads(
                Path(captured["env"]["JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH"])
                .read_text(encoding="utf-8")
            )
            return _FakeProcess()

        services.user_pipeline_gate_payload = lambda **kwargs: {
            "can_run_live_pipeline": True,
            "can_delete_seen_data": True,
            "live_pipeline_block_reason": "",
            "delete_seen_data_block_reason": "",
        }
        services.get_onboarding_preferences_postgres_payload = lambda owner_user_id, **kwargs: {
            "data": {
                "found": True,
                "owner_user_id": owner_user_id,
                "preferences": {
                    "onboarding_completed": True,
                    "selected_role_families": ["backend_engineering"],
                    "target_seniority": ["senior"],
                    "seniority_strict_match": True,
                    "preferred_locations": ["Boston, MA"],
                    "preferred_location_specs": [boston_spec],
                    "location_strict_match": True,
                    "location_show_others_if_unmatched": False,
                    "preferred_skills": ["Python"],
                    "excluded_keywords": ["intern"],
                },
            }
        }
        services._owner_active_pipeline_state = lambda owner_user_id: {}
        services._job_app = lambda: _FakeJobApp()
        def fake_scratch_output_dir(**kwargs):
            output_dir = tmp_path / "application_planning"
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir

        services._pipeline_scratch_output_dir = fake_scratch_output_dir
        services._user_pipeline_redis_admission_lock_payload = lambda **kwargs: {
            "attempted": False,
            "acquired": False,
            "skipped": "disabled",
            "key": "",
            "ttl_seconds": kwargs.get("ttl_seconds"),
        }
        services.reserve_user_pipeline_active_run_postgres_payload = lambda **kwargs: {
            "reserved": True,
            "active_count_after": 1,
            "max_active_runs": 2,
            "ttl_seconds": kwargs.get("ttl_seconds"),
        }
        services._set_owner_active_pipeline_state = lambda owner_user_id, state: captured.setdefault("state", state)
        services._persist_user_pipeline_status_snapshot = lambda **kwargs: captured.setdefault("persisted", kwargs)
        services.subprocess.Popen = fake_popen

        try:
            payload = services.run_live_pipeline_payload(owner_user_id="user_123")
        finally:
            for name, value in originals.items():
                if name == "Popen":
                    services.subprocess.Popen = value
                else:
                    setattr(services, name, value)

    assert payload["pipeline"]["config"]["selected_role_families"] == ["backend_engineering"]
    assert payload["pipeline"]["config"]["preferences"]["target_seniority"] == ["senior"]
    assert payload["pipeline"]["config"]["preferences"]["seniority_strict_match"] is True
    assert captured["state"]["config"]["selected_role_families"] == ["backend_engineering"]
    assert captured["state"]["config"]["preferences"]["target_seniority"] == ["senior"]
    assert captured["state"]["config"]["preferences"]["preferred_location_specs"] == [
        boston_spec
    ]
    assert captured["state"]["config"]["preferences"]["location_strict_match"] is True
    assert (
        captured["state"]["config"]["preferences"][
            "location_show_others_if_unmatched"
        ]
        is False
    )
    assert captured["launch_config"]["options"]["preferences"] == (
        captured["state"]["config"]["preferences"]
    )
    assert captured["state"]["config"]["preference_runtime"] == {
        "schema_version": runtime_status.PREFERENCE_RUNTIME_SCHEMA_VERSION,
        "requested": {
            "selected_role_families": ["backend_engineering"],
            "target_seniority": ["senior"],
            "seniority_strict_match": True,
            "preferred_locations": ["Boston, MA"],
            "preferred_location_specs": [boston_spec],
            "location_strict_match": True,
            "location_show_others_if_unmatched": False,
            "preferred_skills": ["Python"],
            "excluded_keywords": ["intern"],
        },
    }
    assert captured["state"]["config"]["launch_config_path"].endswith("live_pipeline_launch_config.json")
    assert "JOB_STACK_SELECTED_ROLE_FAMILIES" not in captured["env"]
    assert "JOB_STACK_TARGET_SENIORITY" not in captured["env"]
    assert "JOB_STACK_PREFERRED_LOCATIONS" not in captured["env"]
    assert "JOB_STACK_PREFERRED_SKILLS" not in captured["env"]
    assert "JOB_STACK_EXCLUDED_KEYWORDS" not in captured["env"]


def test_child_loads_launch_preferences_and_excluded_keywords_reach_filter(tmp_path):
    boston_spec = canonicalize_location_text("Boston, MA")
    launch_path = _write_launch_config(
        tmp_path / "live_pipeline_launch_config.json",
        {
            "selected_role_families": ["backend_engineering"],
            "target_seniority": ["senior"],
            "preferred_locations": ["Boston, MA"],
            "preferred_location_specs": [boston_spec],
            "location_strict_match": True,
            "location_show_others_if_unmatched": False,
            "preferred_skills": ["Python"],
            "excluded_keywords": ["intern"],
        },
    )

    preference_runtime = collector.resolve_pipeline_preference_runtime(
        env={"JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(launch_path)}
    )

    assert preference_runtime["requested"]["selected_role_families"] == [
        "backend_engineering"
    ]
    assert preference_runtime["effective"]["selected_role_families"] == [
        "backend_engineering"
    ]
    assert preference_runtime["sources"]["selected_role_families"] == "launch_config"
    assert preference_runtime["requested"]["preferred_location_specs"] == [boston_spec]
    assert preference_runtime["effective"]["preferred_location_specs"] == [boston_spec]
    assert preference_runtime["effective"]["location_strict_match"] is True
    assert (
        preference_runtime["effective"]["location_show_others_if_unmatched"]
        is False
    )
    filtered = filter_jobs(
        [_job("Backend Engineer Intern"), _job("Backend Engineer")],
        selected_role_families=preference_runtime["effective"]["selected_role_families"],
        excluded_keywords=preference_runtime["effective"]["excluded_keywords"],
    )
    assert [job["title"] for job in filtered] == ["Backend Engineer"]

    ranked_job = _job("Senior Backend Engineer")
    ranked_job.update({"location": "Boston, MA", "description": "Python"})
    ranked = rank_jobs(
        [ranked_job],
        selected_role_families=preference_runtime["effective"]["selected_role_families"],
        target_seniority=preference_runtime["effective"]["target_seniority"],
        preferred_locations=preference_runtime["effective"]["preferred_locations"],
        preferred_skills=preference_runtime["effective"]["preferred_skills"],
    )
    assert ranked[0]["_preference_seniority_match"] is True
    assert ranked[0]["_preference_location_matches"] == ["boston, ma"]
    assert ranked[0]["_preference_skill_matches"] == ["python"]


def test_explicit_override_wins_per_field_and_empty_launch_values_keep_defaults(tmp_path):
    launch_path = _write_launch_config(
        tmp_path / "live_pipeline_launch_config.json",
        {
            "selected_role_families": ["backend_engineering"],
            "target_seniority": [],
            "preferred_locations": [],
            "preferred_skills": [],
            "excluded_keywords": [],
        },
    )
    preference_runtime = collector.resolve_pipeline_preference_runtime(
        env={
            "JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(launch_path),
            "JOB_STACK_SELECTED_ROLE_FAMILIES": '["data_science"]',
        }
    )

    assert preference_runtime["effective"]["selected_role_families"] == ["data_science"]
    assert preference_runtime["sources"]["selected_role_families"] == "explicit_override"
    assert preference_runtime["effective"]["target_seniority"] == []
    assert preference_runtime["sources"]["target_seniority"] == "launch_config"

    empty_runtime = collector.resolve_pipeline_preference_runtime(
        env={
            "JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(
                _write_launch_config(
                    tmp_path / "empty_launch_config.json",
                    {},
                )
            )
        }
    )
    filtered = filter_jobs(
        [_job("Backend Engineer"), _job("Data Scientist")],
        selected_role_families=(
            empty_runtime["effective"]["selected_role_families"] or None
        ),
    )

    assert [job["title"] for job in filtered] == ["Data Scientist"]
    assert set(empty_runtime["sources"].values()) == {"defaults"}


def test_malformed_launch_preferences_do_not_partially_apply(tmp_path):
    launch_path = _write_launch_config(
        tmp_path / "live_pipeline_launch_config.json",
        {
            "selected_role_families": ["not_a_role"],
            "excluded_keywords": ["intern"],
        },
    )

    preference_runtime = collector.resolve_pipeline_preference_runtime(
        env={"JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(launch_path)}
    )

    assert preference_runtime["requested"] == {
        "selected_role_families": [],
        "target_seniority": [],
        "preferred_locations": [],
        "preferred_skills": [],
        "excluded_keywords": [],
        "seniority_strict_match": False,
        "preferred_location_specs": [],
        "location_strict_match": False,
        "location_show_others_if_unmatched": False,
    }
    assert preference_runtime["effective"] == preference_runtime["requested"]
    assert set(preference_runtime["sources"].values()) == {"defaults"}


def test_launch_seniority_is_canonical_and_invalid_snapshot_is_all_or_nothing(tmp_path):
    valid_path = _write_launch_config(
        tmp_path / "valid_seniority_launch.json",
        {
            "selected_role_families": ["backend_engineering"],
            "target_seniority": [" STAFF_OR_ABOVE ", "staff"],
        },
    )
    valid = collector.resolve_pipeline_preference_runtime(
        env={"JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(valid_path)}
    )
    assert valid["requested"]["target_seniority"] == ["staff"]
    assert valid["effective"]["target_seniority"] == ["staff"]
    assert valid["sources"]["target_seniority"] == "launch_config"

    invalid_path = _write_launch_config(
        tmp_path / "invalid_seniority_launch.json",
        {
            "selected_role_families": ["backend_engineering"],
            "target_seniority": ["principal"],
        },
    )
    invalid = collector.resolve_pipeline_preference_runtime(
        env={"JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(invalid_path)}
    )
    assert invalid["requested"] == {
        "selected_role_families": [],
        "target_seniority": [],
        "preferred_locations": [],
        "preferred_skills": [],
        "excluded_keywords": [],
        "seniority_strict_match": False,
        "preferred_location_specs": [],
        "location_strict_match": False,
        "location_show_others_if_unmatched": False,
    }
    assert invalid["effective"] == invalid["requested"]
    assert set(invalid["sources"].values()) == {"defaults"}


def test_explicit_seniority_override_is_canonical_and_invalid_isolated(monkeypatch):
    warnings = []
    monkeypatch.setattr(
        collector.logger,
        "warning",
        lambda message, *args: warnings.append(message % args if args else message),
    )
    legacy = collector.resolve_pipeline_preference_runtime(
        env={"JOB_STACK_TARGET_SENIORITY": '["staff_or_above", "STAFF"]'}
    )
    assert legacy["effective"]["target_seniority"] == ["staff"]
    assert legacy["sources"]["target_seniority"] == "explicit_override"

    invalid = collector.resolve_pipeline_preference_runtime(
        env={
            "JOB_STACK_TARGET_SENIORITY": '["principal"]',
            "JOB_STACK_SELECTED_ROLE_FAMILIES": '["backend_engineering"]',
        }
    )
    assert invalid["effective"]["target_seniority"] == []
    assert invalid["effective"]["selected_role_families"] == ["backend_engineering"]
    assert invalid["sources"]["target_seniority"] == "explicit_override"
    assert invalid["sources"]["selected_role_families"] == "explicit_override"
    assert any(
        "Ignoring unsupported JOB_STACK_TARGET_SENIORITY" in message
        for message in warnings
    )


def test_effective_hash_uses_canonical_seniority_values():
    legacy = collector._normalized_preference_snapshot(
        {"target_seniority": ["staff_or_above"]}
    )
    canonical = collector._normalized_preference_snapshot(
        {"target_seniority": ["staff"]}
    )
    assert legacy == canonical
    assert collector._preference_snapshot_sha256(legacy) == collector._preference_snapshot_sha256(canonical)


def test_effective_hash_includes_strict_seniority_boolean():
    flexible = collector._normalized_preference_snapshot(
        {"target_seniority": ["senior"], "seniority_strict_match": False}
    )
    strict = collector._normalized_preference_snapshot(
        {"target_seniority": ["senior"], "seniority_strict_match": True}
    )
    assert collector._preference_snapshot_sha256(flexible) != collector._preference_snapshot_sha256(strict)


def test_effective_hash_includes_location_policy_and_legacy_snapshots_gain_specs():
    flexible = collector._normalized_preference_snapshot(
        {
            "preferred_locations": ["Boston, MA"],
            "location_strict_match": False,
        }
    )
    strict = collector._normalized_preference_snapshot(
        {
            "preferred_locations": ["Boston, MA"],
            "location_strict_match": True,
        }
    )

    assert flexible["preferred_location_specs"] == [
        canonicalize_location_text("Boston, MA")
    ]
    assert collector._preference_snapshot_sha256(flexible) != (
        collector._preference_snapshot_sha256(strict)
    )


def test_explicit_location_override_rebuilds_canonical_specs(tmp_path):
    launch_path = _write_launch_config(
        tmp_path / "live_pipeline_launch_config.json",
        {
            "preferred_locations": ["Boston, MA"],
            "preferred_location_specs": [canonicalize_location_text("Boston, MA")],
            "location_strict_match": True,
        },
    )

    runtime = collector.resolve_pipeline_preference_runtime(
        env={
            "JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(launch_path),
            "JOB_STACK_PREFERRED_LOCATIONS": '["Austin, TX"]',
        }
    )

    assert runtime["effective"]["preferred_locations"] == ["Austin, TX"]
    assert runtime["effective"]["preferred_location_specs"] == [
        canonicalize_location_text("Austin, TX")
    ]
    assert runtime["sources"]["preferred_location_specs"] == "explicit_override"
    assert runtime["effective"]["location_strict_match"] is True


def test_effective_preference_hash_is_canonical_distinct_and_secret_free(tmp_path):
    first = collector._normalized_preference_snapshot({
        "selected_role_families": [" backend_engineering ", "backend_engineering"],
        "target_seniority": [" senior "],
        "preferred_locations": [],
        "preferred_skills": [" Python ", "Python"],
        "excluded_keywords": [],
    })
    same_normalized = collector._normalized_preference_snapshot({
        "preferred_skills": ["Python"],
        "preferred_locations": [],
        "target_seniority": ["senior"],
        "excluded_keywords": [],
        "selected_role_families": ["backend_engineering"],
    })
    reordered = dict(reversed(list(first.items())))
    different = {**first, "preferred_skills": ["Python", "PostgreSQL"]}

    assert collector._preference_snapshot_sha256(first) == collector._preference_snapshot_sha256(
        same_normalized
    )
    assert collector._preference_snapshot_sha256(first) == collector._preference_snapshot_sha256(
        reordered
    )
    assert collector._preference_snapshot_sha256(first) != collector._preference_snapshot_sha256(
        different
    )

    launch_path = _write_launch_config(
        tmp_path / "live_pipeline_launch_config.json",
        first,
    )
    preference_runtime = collector.resolve_pipeline_preference_runtime(
        env={
            "JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH": str(launch_path),
            "SESSION_TOKEN": "never-persist-this",
            "DATABASE_URL": "postgres://never-persist-this",
            "JOB_STACK_OWNER_USER_ID": "never-persist-this",
        }
    )
    serialized = json.dumps(preference_runtime, sort_keys=True)

    assert preference_runtime["schema_version"] == runtime_status.PREFERENCE_RUNTIME_SCHEMA_VERSION
    assert preference_runtime["effective_sha256"] == collector._preference_snapshot_sha256(
        preference_runtime["effective"]
    )
    assert "never-persist-this" not in serialized
    assert "session" not in serialized.lower()
    assert "database" not in serialized.lower()
    assert "owner" not in serialized.lower()


def test_preference_runtime_status_is_carried_into_run_config_json(monkeypatch, tmp_path):
    status_path = tmp_path / "live_pipeline_status.json"
    monkeypatch.setenv(runtime_status.ENV_STATUS_PATH, str(status_path))
    monkeypatch.setenv(runtime_status.ENV_RUN_ID, "run_123")
    runtime_status.initialize_run(
        output_dir=str(tmp_path),
        log_path=str(tmp_path / "run.log"),
        status_path=str(status_path),
        planning_only=False,
        job_limit=50,
        job_packet_limit=0,
        llm_actions=[],
        generate_tailoring=False,
        generate_llm_tailoring=False,
        refresh_llm_tailoring=False,
        generate_llm_fallback=False,
        generate_llm_adjudication=False,
        delete_seen_data="no",
    )
    preference_runtime = collector.resolve_pipeline_preference_runtime(env={})
    runtime_status.update_config(preference_runtime=preference_runtime)
    child_status = json.loads(status_path.read_text(encoding="utf-8"))
    captured = {}
    monkeypatch.setattr(
        services,
        "get_user_pipeline_run_postgres_payload",
        lambda **kwargs: {"run": {}},
    )
    monkeypatch.setattr(
        services,
        "upsert_user_pipeline_run_postgres_payload",
        lambda **kwargs: captured.setdefault("record", kwargs["record"]),
    )

    services._persist_user_pipeline_status_snapshot(
        owner_user_id="user_123",
        status_payload=child_status,
    )

    assert child_status["config"]["preference_runtime"] == preference_runtime
    assert captured["record"]["config_json"]["config"]["preference_runtime"] == preference_runtime


class _DropPctLogger:
    def __init__(self, messages):
        self.messages = messages

    def _record(self, message, *args):
        self.messages.append(message % args if args else str(message))

    info = _record
    warning = _record
    error = _record


def _install_drop_pct_collector_fakes(
    monkeypatch,
    tmp_path,
    *,
    jobs,
    filtered_count,
    graph_route,
    user_pipeline,
    scraper_source="workday",
    selected_role_families=None,
    pipeline_preferences=None,
):
    captured = {
        "logs": [],
        "route_events": [],
        "stage_completions": [],
    }
    filtered_jobs = list(jobs[:filtered_count])
    filtered_job_ids = {job.get("job_id") for job in filtered_jobs}

    monkeypatch.setenv(
        "JOB_STACK_JOB_CORPUS_PATH",
        str(tmp_path / "synthetic-corpus.jsonl"),
    )
    monkeypatch.delenv(
        collector.JD_INTELLIGENCE_CONTROLLED_LLM_FLAG,
        raising=False,
    )
    monkeypatch.setattr(collector, "logger", _DropPctLogger(captured["logs"]))
    effective_preferences = {
        "selected_role_families": list(selected_role_families or []),
        "target_seniority": [],
        "seniority_strict_match": False,
        "preferred_locations": [],
        "preferred_location_specs": [],
        "location_strict_match": False,
        "location_show_others_if_unmatched": False,
        "preferred_skills": [],
        "excluded_keywords": [],
        **dict(pipeline_preferences or {}),
    }
    monkeypatch.setattr(
        collector,
        "resolve_pipeline_preference_runtime",
        lambda: {
            "effective": effective_preferences,
            "effective_sha256": "0" * 64,
            "schema_version": "test-v1",
        },
    )
    monkeypatch.setattr(collector, "update_config", lambda **_kwargs: None)
    monkeypatch.setattr(collector, "update_counts", lambda **_kwargs: None)
    monkeypatch.setattr(collector, "start_stage", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        collector,
        "complete_stage",
        lambda stage, **kwargs: (
            captured["stage_completions"].append(stage),
            captured.setdefault("stage_counts", {})
            .setdefault(stage, {})
            .update(kwargs.get("counts", {})),
        ),
    )
    monkeypatch.setattr(collector, "section", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        collector,
        "_is_user_pipeline_mode",
        lambda: user_pipeline,
    )
    monkeypatch.setattr(collector, "log_company_hiring", lambda *_args: None)
    monkeypatch.setattr(collector, "log_market_insights", lambda *_args: None)

    for name in (
        "_record_relevance_prefilter_agent_trace",
        "_maybe_execute_authoritative_jd_intelligence_graph",
        "_maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence",
        "_maybe_execute_authoritative_semantic_evaluation_graph",
        "_maybe_execute_authoritative_final_scoring_graph",
        "_maybe_collect_vector_evidence_after_application_priority",
        "_maybe_run_shadow_sidecar_after_application_priority",
        "_maybe_invoke_advisory_chain_diagnostics_after_application_priority",
        "_maybe_build_evidence_chain_collector_diagnostics",
        "_maybe_run_controlled_evidence_chain_execution_after_application_priority",
        "_maybe_persist_controlled_evidence_chain_execution_trace",
    ):
        monkeypatch.setattr(
            collector,
            name,
            lambda *_args, **_kwargs: None,
        )

    def execute_prefilter_graph(**kwargs):
        if not graph_route:
            return None
        captured["filter_inputs"] = list(kwargs["jobs"])
        routed_filtered_jobs = [
            job for job in kwargs["jobs"] if job.get("job_id") in filtered_job_ids
        ]
        captured["route_events"].extend(["graph_filter", "graph_dedupe"])
        kwargs["on_prefilter_completed"](routed_filtered_jobs, {}, [])
        kwargs["on_dedupe_completed"](routed_filtered_jobs)
        return {
            "filtered_jobs": routed_filtered_jobs,
            "filter_diagnostics": {},
            "role_title_audit_rows": [],
            "deduplicated_jobs": routed_filtered_jobs,
            "execution_metadata": {
                "execution_mode": "langgraph",
                "node_order": ["filter_jobs", "dedupe_jobs"],
            },
        }

    monkeypatch.setattr(
        collector,
        "_maybe_execute_authoritative_prefilter_dedupe_graph",
        execute_prefilter_graph,
    )

    def install_module(name, **members):
        monkeypatch.setitem(sys.modules, name, types.SimpleNamespace(**members))

    install_module(
        "src.ai.job_fit_evaluator",
        evaluate_jobs=lambda rows: list(rows),
        get_eval_cache_metrics=lambda: {
            "eval_cache_hits": 0,
            "eval_cache_misses": 0,
            "eval_cache_stores": 0,
            "eval_cache_only_skips": 0,
            "eval_live_failures": 0,
        },
    )
    install_module(
        "src.ai.llm_client",
        get_provider_metrics=lambda: {
            "primary_attempts": 0,
            "fallback_attempts": 0,
            "groq_calls": 0,
            "openai_calls": 0,
            "fallback_successes": 0,
            "provider_failures": 0,
        },
        reset_provider_metrics=lambda: None,
    )
    install_module("src.ai.resume_matcher", match_resumes=lambda rows: list(rows))
    install_module(
        "src.ai.skill_llm_enricher",
        get_skill_cache_metrics=lambda: {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_stores": 0,
            "cache_only_skips": 0,
            "live_failures": 0,
        },
        reset_skill_cache_metrics=lambda: None,
    )
    install_module(
        "src.discovery.domain_learner",
        learn_domains_from_jobs=lambda _rows: None,
    )
    install_module(
        "src.discovery.persist_discovered",
        persist_discovered_companies=lambda: None,
    )
    install_module(
        "src.intelligence.job_intelligence",
        ai_evaluation_skip_summary=lambda _rows, limit=10: {
            "skipped_count": 0,
            "reason_counts": {},
            "skipped_samples": [],
            "skipped_jobs": [],
        },
        build_job_intelligence=lambda row: (
            captured.setdefault("intelligence_inputs", []).append(dict(row))
            or dict(row)
        ),
        filter_jobs_for_ai_evaluation=lambda rows: list(rows),
    )
    install_module(
        "src.intelligence.skill_discovery",
        discover_new_skills=lambda _rows: [],
    )
    install_module(
        "src.intelligence.skill_frequency",
        top_skills=lambda _rows, top_n=50: [],
    )
    install_module("src.pipeline.application_scorer", score_jobs=lambda rows: list(rows))

    def direct_dedupe(rows):
        captured["route_events"].append("direct_dedupe")
        return list(rows)

    install_module("src.pipeline.dedupe", dedupe_jobs=direct_dedupe)
    install_module(
        "src.pipeline.embedding_prefilter",
        prefilter_jobs_by_embedding=lambda rows, top_n=None: list(rows),
    )
    install_module(
        "src.pipeline.job_details",
        enrich_job_details=lambda rows: (
            captured.setdefault("detail_inputs", []).extend(dict(row) for row in rows)
            or list(rows)
        ),
    )

    def direct_filter(_rows, **kwargs):
        captured["route_events"].append("direct_filter")
        captured["filter_inputs"] = list(_rows)
        captured["filter_kwargs"] = dict(kwargs)
        return [
            job for job in _rows if job.get("job_id") in filtered_job_ids
        ], {}

    install_module(
        "src.pipeline.job_filter",
        build_source_health_report_rows=lambda *_args: [],
        filter_jobs=direct_filter,
        role_title_filter_audit_counts=lambda _rows: {
            "role_title_audit_total": 0,
            "role_title_audit_pass": 0,
            "role_title_audit_reject": 0,
            "role_title_audit_suspected_false_negative": 0,
        },
        write_source_health_report_csv=lambda *_args: None,
        write_role_title_filter_audit_csv=lambda *_args: None,
    )
    install_module(
        "src.pipeline.job_ranker",
        rank_jobs=lambda rows, **_kwargs: (
            captured.setdefault("ranking_inputs", []).extend(
                dict(row) for row in rows
            )
            or list(rows)
        ),
    )
    install_module(
        "src.rag.export_job_corpus",
        export_job_corpus=lambda rows, _path: len(rows),
    )

    scraper_modules = {
        "src.scrapers.workday_scraper": "scrape_all_workday",
        "src.scrapers.greenhouse_scraper": "scrape_all_greenhouse",
        "src.scrapers.lever_scraper": "scrape_all_lever",
        "src.scrapers.ashby_scraper": "scrape_all_ashby",
        "src.scrapers.workable_scraper": "scrape_all_workable",
        "src.scrapers.jobvite_scraper": "scrape_all_jobvite",
        "src.scrapers.recruitee_scraper": "scrape_all_recruitee",
        "src.scrapers.smartrecruiters_scraper": "scrape_all_smartrecruiters",
        "src.scrapers.builtin_scraper": "scrape_all_builtin",
        "src.scrapers.usajobs_scraper": "scrape_all_usajobs",
        "src.scrapers.himalayas_scraper": "scrape_all_himalayas",
    }
    selected_scraper_module = f"src.scrapers.{scraper_source}_scraper"
    for module_name, function_name in scraper_modules.items():
        rows = list(jobs) if module_name == selected_scraper_module else []
        install_module(module_name, **{function_name: lambda rows=rows, **_kwargs: rows})

    def global_metrics_not_allowed(*_args, **_kwargs):
        raise AssertionError("user pipeline must not use the global metrics store")

    if user_pipeline:
        metrics_members = {
            name: global_metrics_not_allowed
            for name in (
                "get_hiring_momentum",
                "get_last_ats_counts",
                "get_last_run",
                "record_ats_counts",
                "record_company_hiring",
                "record_pipeline_run",
            )
        }
    else:
        def record_pipeline_run(**kwargs):
            captured["persisted_metrics"] = dict(kwargs)
            return "synthetic-run"

        metrics_members = {
            "get_hiring_momentum": lambda: [],
            "get_last_ats_counts": lambda _stage: {},
            "get_last_run": lambda: None,
            "record_ats_counts": lambda *_args: None,
            "record_company_hiring": lambda *_args: None,
            "record_pipeline_run": record_pipeline_run,
        }
    install_module("src.storage.metrics_store", **metrics_members)
    install_module(
        "src.storage.skill_corpus_store",
        get_top_corpus_skills=lambda limit=100: [],
        store_job_skills=lambda *_args: None,
    )

    def check_pipeline_regression(_previous, current, _logger):
        if user_pipeline:
            global_metrics_not_allowed()
        captured["current_metrics"] = dict(current)

    install_module(
        "src.utils.ats_health",
        check_ats_failure=(
            global_metrics_not_allowed if user_pipeline else lambda *_args: None
        ),
        check_ats_health=lambda _rows: None,
        check_pipeline_regression=check_pipeline_regression,
    )
    install_module(
        "src.utils.job_cache",
        cache_keys_for_jobs=lambda rows: [row["job_id"] for row in rows],
        filter_new_jobs=lambda rows, _seen: (
            list(rows),
            [row["job_id"] for row in rows],
        ),
        load_seen_job_ids=lambda: set(),
        save_new_job_records=lambda _records: None,
        save_new_job_ids=lambda _ids: None,
        structured_seen_records_for_jobs=lambda rows: list(rows),
    )

    def log_stage_metrics(stage, rows):
        captured.setdefault("logged_stage_counts", []).append(
            (stage, len(rows))
        )
        return {"count": len(rows)}

    install_module("src.utils.pipeline_metrics", log_stage_metrics=log_stage_metrics)
    return captured


@pytest.mark.parametrize(
    (
        "input_count",
        "filtered_count",
        "graph_route",
        "user_pipeline",
        "expected_drop_pct",
    ),
    [
        (0, 0, False, False, 0),
        (3, 2, False, False, 33.33),
        (3, 2, True, False, 33.33),
        (3, 2, True, True, 33.33),
    ],
)
def test_completed_collector_paths_share_defined_drop_pct(
    monkeypatch,
    tmp_path,
    input_count,
    filtered_count,
    graph_route,
    user_pipeline,
    expected_drop_pct,
):
    jobs = [
        {
            "job_id": f"job-{index}",
            "title": "Synthetic Engineer",
            "company": "Synthetic",
            "location": "United States",
        }
        for index in range(input_count)
    ]
    captured = _install_drop_pct_collector_fakes(
        monkeypatch,
        tmp_path,
        jobs=jobs,
        filtered_count=filtered_count,
        graph_route=graph_route,
        user_pipeline=user_pipeline,
    )

    result = asyncio.run(collector.collect_all_jobs_async())

    assert [row["job_id"] for row in result] == [
        row["job_id"] for row in jobs[:filtered_count]
    ]
    assert captured["stage_completions"].count("filtering") == 1
    assert captured["stage_completions"].count("dedupe") == 1
    assert captured["stage_completions"].index("filtering") < captured[
        "stage_completions"
    ].index("dedupe")
    expected_route_events = (
        ["graph_filter", "graph_dedupe"]
        if graph_route
        else ["direct_filter", "direct_dedupe"]
    )
    assert captured["route_events"] == expected_route_events
    assert f"Filter drop rate: {expected_drop_pct}%" in captured["logs"]

    if user_pipeline:
        assert "current_metrics" not in captured
        assert "persisted_metrics" not in captured
        assert (tmp_path / "source_acquisition_metrics.json").is_file()
    else:
        assert captured["current_metrics"]["drop_pct"] == expected_drop_pct
        assert captured["persisted_metrics"]["drop_pct"] == expected_drop_pct
        assert not (tmp_path / "source_acquisition_metrics.json").exists()


def test_usajobs_rows_join_common_collector_filter_and_only_retained_rows_continue(
    monkeypatch,
    tmp_path,
):
    jobs = [
        {
            "job_id": "usajobs_1",
            "source": "usajobs",
            "title": "Data Scientist",
            "company": "Federal Agency",
            "location": "Washington, District of Columbia",
            "description_text": "Retained sanitized provider description.",
        },
        {
            "job_id": "usajobs_2",
            "source": "usajobs",
            "title": "Systems Engineer",
            "company": "Federal Agency",
            "location": "Washington, District of Columbia",
            "description_text": "Filtered sanitized provider description.",
        },
    ]
    captured = _install_drop_pct_collector_fakes(
        monkeypatch,
        tmp_path,
        jobs=jobs,
        filtered_count=1,
        graph_route=False,
        user_pipeline=True,
        scraper_source="usajobs",
        selected_role_families=["data_science"],
    )

    result = asyncio.run(collector.collect_all_jobs_async())

    assert [row["job_id"] for row in captured["filter_inputs"]] == [
        "usajobs_1",
        "usajobs_2",
    ]
    assert captured["filter_kwargs"]["selected_role_families"] == [
        "data_science"
    ]
    assert [row["job_id"] for row in captured["detail_inputs"]] == [
        "usajobs_1"
    ]
    assert [row["job_id"] for row in captured["intelligence_inputs"]] == [
        "usajobs_1"
    ]
    assert captured["intelligence_inputs"][0]["description_text"] == (
        "Retained sanitized provider description."
    )
    assert [row["job_id"] for row in result] == ["usajobs_1"]


@pytest.mark.parametrize("graph_route", [False, True])
def test_strict_location_policy_precedes_both_filter_routes_and_downstream(
    monkeypatch,
    tmp_path,
    graph_route,
):
    jobs = [
        {
            "job_id": "boston",
            "title": "Data Scientist",
            "company": "Acme",
            "location": "Boston, MA",
        },
        {
            "job_id": "austin",
            "title": "Data Scientist",
            "company": "Acme",
            "location": "Austin, TX",
        },
    ]
    captured = _install_drop_pct_collector_fakes(
        monkeypatch,
        tmp_path,
        jobs=jobs,
        filtered_count=2,
        graph_route=graph_route,
        user_pipeline=True,
        pipeline_preferences={
            "preferred_locations": ["Boston, MA"],
            "preferred_location_specs": [canonicalize_location_text("Boston, MA")],
            "location_strict_match": True,
            "location_show_others_if_unmatched": False,
        },
    )

    result = asyncio.run(collector.collect_all_jobs_async())

    assert [job["job_id"] for job in captured["filter_inputs"]] == ["boston"]
    assert [job["job_id"] for job in captured["ranking_inputs"]] == ["boston"]
    assert [job["job_id"] for job in captured["detail_inputs"]] == ["boston"]
    assert [job["job_id"] for job in captured["intelligence_inputs"]] == [
        "boston"
    ]
    assert [job["job_id"] for job in result] == ["boston"]
    expected_counts = {
        "location_preference_input_count": 2,
        "location_preference_matched_count": 1,
        "location_preference_retained_count": 1,
        "location_preference_rejected_count": 1,
        "location_preference_strict_match": True,
        "location_preference_show_others_if_unmatched": False,
        "location_preference_fallback_activated": False,
        "filtered_jobs": 1,
    }
    assert expected_counts.items() <= captured["stage_counts"]["filtering"].items()

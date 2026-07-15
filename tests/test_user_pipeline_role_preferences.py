import json
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path


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


class _FakeProcess:
    pid = 4242

    def poll(self):
        return None


class _FakeJobApp:
    def _build_main_cmd(self, args, planning_only=False):
        return ["python", "main.py"]


def test_selected_role_families_appear_in_pipeline_run_config_and_launch_config_not_child_env():
    captured = {}
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
                    "preferred_locations": ["New York"],
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
    assert captured["state"]["config"]["selected_role_families"] == ["backend_engineering"]
    assert captured["state"]["config"]["preferences"]["target_seniority"] == ["senior"]
    assert captured["state"]["config"]["preference_runtime"] == {
        "schema_version": runtime_status.PREFERENCE_RUNTIME_SCHEMA_VERSION,
        "requested": {
            "selected_role_families": ["backend_engineering"],
            "target_seniority": ["senior"],
            "preferred_locations": ["New York"],
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
    launch_path = _write_launch_config(
        tmp_path / "live_pipeline_launch_config.json",
        {
            "selected_role_families": ["backend_engineering"],
            "target_seniority": ["senior"],
            "preferred_locations": ["New York"],
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
    filtered = filter_jobs(
        [_job("Backend Engineer Intern"), _job("Backend Engineer")],
        selected_role_families=preference_runtime["effective"]["selected_role_families"],
        excluded_keywords=preference_runtime["effective"]["excluded_keywords"],
    )
    assert [job["title"] for job in filtered] == ["Backend Engineer"]

    ranked_job = _job("Senior Backend Engineer")
    ranked_job.update({"location": "New York, United States", "description": "Python"})
    ranked = rank_jobs(
        [ranked_job],
        selected_role_families=preference_runtime["effective"]["selected_role_families"],
        target_seniority=preference_runtime["effective"]["target_seniority"],
        preferred_locations=preference_runtime["effective"]["preferred_locations"],
        preferred_skills=preference_runtime["effective"]["preferred_skills"],
    )
    assert ranked[0]["_preference_seniority_match"] is True
    assert ranked[0]["_preference_location_matches"] == ["new york"]
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
    }
    assert preference_runtime["effective"] == preference_runtime["requested"]
    assert set(preference_runtime["sources"].values()) == {"defaults"}


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

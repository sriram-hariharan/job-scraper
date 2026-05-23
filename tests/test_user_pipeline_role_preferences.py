import json
import sys
import tempfile
import types
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
from src.app import services


def _job(title):
    return {
        "title": title,
        "company": "Acme",
        "location": "United States",
        "source": "jobvite",
        "posted_at": "",
    }


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


def test_selected_role_families_appear_in_pipeline_run_config_and_child_env():
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
    assert json.loads(captured["env"]["JOB_STACK_SELECTED_ROLE_FAMILIES"]) == ["backend_engineering"]
    assert json.loads(captured["env"]["JOB_STACK_TARGET_SENIORITY"]) == ["senior"]
    assert json.loads(captured["env"]["JOB_STACK_PREFERRED_LOCATIONS"]) == ["New York"]
    assert json.loads(captured["env"]["JOB_STACK_PREFERRED_SKILLS"]) == ["Python"]
    assert json.loads(captured["env"]["JOB_STACK_EXCLUDED_KEYWORDS"]) == ["intern"]

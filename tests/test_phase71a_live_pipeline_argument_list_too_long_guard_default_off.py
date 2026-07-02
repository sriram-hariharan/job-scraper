import json
import inspect
from pathlib import Path

import pytest

from src.app import services


class _FakeProcess:
    pid = 71210

    def poll(self):
        return None


_PREFERENCE_ENV_KEYS = {
    "JOB_STACK_SELECTED_ROLE_FAMILIES",
    "JOB_STACK_TARGET_SENIORITY",
    "JOB_STACK_PREFERRED_LOCATIONS",
    "JOB_STACK_PREFERRED_SKILLS",
    "JOB_STACK_EXCLUDED_KEYWORDS",
}


def _install_live_pipeline_fakes(monkeypatch, tmp_path, captured, preferences=None):
    fake_preferences = preferences or {
        "onboarding_completed": True,
        "selected_role_families": ["backend_engineering"],
        "target_seniority": ["senior"],
        "preferred_locations": ["New York"],
        "preferred_skills": ["Python"],
        "excluded_keywords": ["intern"],
    }
    monkeypatch.setattr(
        services,
        "user_pipeline_gate_payload",
        lambda **kwargs: {
            "can_run_live_pipeline": True,
            "can_delete_seen_data": True,
            "live_pipeline_block_reason": "",
            "delete_seen_data_block_reason": "",
        },
    )
    monkeypatch.setattr(
        services,
        "get_onboarding_preferences_postgres_payload",
        lambda owner_user_id, **kwargs: {
            "data": {
                "found": True,
                "owner_user_id": owner_user_id,
                "preferences": fake_preferences,
            }
        },
    )
    monkeypatch.setattr(services, "_owner_active_pipeline_state", lambda owner_user_id: {})

    def fake_scratch_output_dir(**kwargs):
        output_dir = tmp_path / "application_planning"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    monkeypatch.setattr(services, "_pipeline_scratch_output_dir", fake_scratch_output_dir)
    monkeypatch.setattr(
        services,
        "_user_pipeline_redis_admission_lock_payload",
        lambda **kwargs: {
            "attempted": False,
            "acquired": False,
            "skipped": "disabled",
            "key": "",
            "ttl_seconds": kwargs.get("ttl_seconds"),
        },
    )
    monkeypatch.setattr(
        services,
        "reserve_user_pipeline_active_run_postgres_payload",
        lambda **kwargs: {
            "reserved": True,
            "active_count_after": 1,
            "max_active_runs": 2,
            "ttl_seconds": kwargs.get("ttl_seconds"),
        },
    )
    monkeypatch.setattr(
        services,
        "_set_owner_active_pipeline_state",
        lambda owner_user_id, state: captured.setdefault("state", state),
    )
    monkeypatch.setattr(
        services,
        "_persist_user_pipeline_status_snapshot",
        lambda **kwargs: captured.setdefault("persisted", kwargs),
    )

    def fake_popen(cmd, stdout=None, stderr=None, env=None):
        captured["cmd"] = list(cmd)
        captured["env"] = dict(env or {})
        return _FakeProcess()

    monkeypatch.setattr(services.subprocess, "Popen", fake_popen)


def test_phase71a_live_pipeline_launch_uses_bounded_argv_with_all_selected_packets(monkeypatch, tmp_path):
    captured = {}
    _install_live_pipeline_fakes(monkeypatch, tmp_path, captured)

    payload = services.run_live_pipeline_payload(
        owner_user_id="user_123",
        job_limit=50,
        job_packet_limit=0,
        llm_actions=["APPLY", "APPLY_REVIEW_VARIANTS", "MAYBE_TAILOR", "SKIP_FOR_NOW"],
        generate_tailoring=True,
        generate_llm_tailoring=True,
        refresh_llm_tailoring=True,
        generate_llm_fallback=True,
        generate_llm_adjudication=True,
        delete_seen_data="yes",
    )

    cmd = captured["cmd"]
    joined = " ".join(cmd)

    assert payload["ok"] is True
    assert services._pipeline_launch_argv_size_bytes(cmd) < 8192
    assert "--application-planning-job-limit 50" in joined
    assert "--application-planning-job-packet-limit 0" in joined
    assert "--application-planning-generate-tailoring" in cmd
    assert "--application-planning-generate-llm-tailoring" in cmd
    assert "--application-planning-refresh-llm-tailoring" in cmd
    assert "--application-planning-generate-llm-fallback" in cmd
    assert "--application-planning-generate-llm-adjudication" in cmd
    assert "--delete-seen-data yes" in joined
    assert "job_description" not in joined
    assert "selected_jobs" not in joined
    assert "planning_packet" not in joined

    config = payload["pipeline"]["config"]
    assert config["job_packet_limit"] == 0
    assert config["delete_seen_data"] == "yes"
    assert config["generate_llm_adjudication"] is True
    assert config["preferences"]["preferred_skills"] == ["Python"]
    assert config["selected_role_families"] == ["backend_engineering"]
    assert config["launch_command"]["large_payloads_in_argv"] is False
    assert _PREFERENCE_ENV_KEYS.isdisjoint(captured["env"])
    launch_config_path = Path(config["launch_config_path"])
    launch_config = json.loads(launch_config_path.read_text(encoding="utf-8"))
    assert launch_config["contains_large_payloads"] is False
    assert launch_config["contains_selected_jobs"] is False
    assert launch_config["options"]["job_packet_limit"] == 0
    assert launch_config["options"]["preferences"]["preferred_skills"] == ["Python"]
    assert launch_config["options"]["selected_role_families"] == ["backend_engineering"]


def test_phase71a_live_pipeline_compacts_oversized_child_env_before_popen(monkeypatch, tmp_path):
    captured = {}
    _install_live_pipeline_fakes(monkeypatch, tmp_path, captured)
    monkeypatch.setenv("JOB_STACK_PIPELINE_CHILD_ENV_MAX_TOTAL_BYTES", "8192")
    for index in range(40):
        monkeypatch.setenv(f"JOB_STACK_PHASE71A_BULK_{index:02d}", "x" * 900)

    payload = services.run_live_pipeline_payload(
        owner_user_id="user_123",
        job_limit=50,
        job_packet_limit=0,
        generate_tailoring=True,
        generate_llm_tailoring=True,
        refresh_llm_tailoring=True,
        generate_llm_fallback=True,
        generate_llm_adjudication=True,
        delete_seen_data="yes",
    )

    env = captured["env"]
    assert payload["ok"] is True
    assert services._pipeline_launch_env_size_bytes(env) <= services._pipeline_child_env_max_total_bytes()
    assert sum(1 for key in env if key.startswith("JOB_STACK_PHASE71A_BULK_")) < 40
    assert env["JOB_STACK_PIPELINE_LAUNCH_CONFIG_PATH"].endswith("live_pipeline_launch_config.json")
    assert env["JOB_APP_PIPELINE_RUN_ID"] == payload["pipeline"]["run_id"]
    assert _PREFERENCE_ENV_KEYS.isdisjoint(env)


def test_phase71a_large_preferences_stay_out_of_child_env_and_in_launch_config(monkeypatch, tmp_path):
    captured = {}
    huge_preferences = {
        "onboarding_completed": True,
        "selected_role_families": ["backend_engineering", "software_engineering"],
        "target_seniority": ["senior"] * 500,
        "preferred_locations": [f"Location {index}" for index in range(500)],
        "preferred_skills": [f"Skill {index} " + ("x" * 100) for index in range(500)],
        "excluded_keywords": [f"Keyword {index} " + ("y" * 100) for index in range(500)],
    }
    _install_live_pipeline_fakes(monkeypatch, tmp_path, captured, preferences=huge_preferences)

    payload = services.run_live_pipeline_payload(
        owner_user_id="user_123",
        job_limit=50,
        job_packet_limit=0,
        delete_seen_data="yes",
    )

    env = captured["env"]
    config = payload["pipeline"]["config"]
    launch_config = json.loads(Path(config["launch_config_path"]).read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert services._pipeline_launch_env_size_bytes(env) <= services._pipeline_child_env_max_total_bytes()
    assert _PREFERENCE_ENV_KEYS.isdisjoint(env)
    assert config["job_limit"] == 50
    assert config["job_packet_limit"] == 0
    assert config["preferences"]["preferred_skills"] == huge_preferences["preferred_skills"]
    assert config["selected_role_families"] == ["backend_engineering", "software_engineering"]
    assert launch_config["options"]["preferences"]["excluded_keywords"] == huge_preferences["excluded_keywords"]
    assert launch_config["options"]["selected_role_families"] == [
        "backend_engineering",
        "software_engineering",
    ]


def test_phase71a_live_pipeline_rejects_oversized_argv_before_popen(monkeypatch, tmp_path):
    captured = {}
    _install_live_pipeline_fakes(monkeypatch, tmp_path, captured)
    monkeypatch.setenv("JOB_STACK_PIPELINE_LAUNCH_ARGV_MAX_BYTES", "2048")

    with pytest.raises(ValueError, match="launch command is too large"):
        services.run_live_pipeline_payload(
            owner_user_id="user_123",
            job_limit=50,
            job_packet_limit=0,
            llm_actions=["APPLY", "PAYLOAD_" + ("x" * 5000)],
            delete_seen_data="yes",
        )

    assert "cmd" not in captured


def test_phase71a_no_provider_network_mutation_or_artifact_imports():
    source = "\n".join(
        [
            inspect.getsource(services._validate_pipeline_subprocess_launch),
            inspect.getsource(services._compact_pipeline_child_env),
            inspect.getsource(services._write_live_pipeline_launch_config),
        ]
    )
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
    assert "requests.post" not in source
    assert "httpx." not in source
    assert "application_execution_queue" not in source
    assert "generate_tailoring_suggestions" not in source

import json
import plistlib
import sys
from pathlib import Path

from src.pipeline import scheduler


RETENTION_FLAG = "APPLYLENS_HIMALAYAS_ACTIVE_RETENTION_ENABLED"


def _plist(payload):
    return plistlib.loads(payload["plist_xml"].encode("utf-8"))


def test_checked_in_profile_is_exact_bounded_data_us_activation():
    assert json.loads(Path("src/config/himalayas_query_profiles.json").read_text()) == [
        {
            "profile_id": "data-us",
            "query": "data",
            "country": "US",
            "exclude_worldwide": True,
            "sort": "recent",
        },
        {
            "profile_id": "software-us",
            "query": "software",
            "country": "US",
            "exclude_worldwide": True,
            "sort": "recent",
        },
    ]


def test_scheduler_retention_option_defaults_false(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["scheduler", "--job", "live_pipeline", "--print-only"],
    )
    assert scheduler._parse_args().enable_himalayas_active_retention is False


def test_live_launchd_retention_flag_is_isolated_to_enabled_environment():
    disabled_payload = scheduler.build_scheduler_launchd_plist_payload(
        "live_pipeline"
    )
    enabled_payload = scheduler.build_scheduler_launchd_plist_payload(
        "live_pipeline",
        himalayas_active_retention_enabled=True,
    )
    discovery_payload = scheduler.build_scheduler_launchd_plist_payload(
        "agent_discovery",
        himalayas_active_retention_enabled=True,
    )
    disabled = _plist(disabled_payload)
    enabled = _plist(enabled_payload)
    discovery = _plist(discovery_payload)

    assert disabled_payload["himalayas_active_retention_enabled"] is False
    assert enabled_payload["himalayas_active_retention_enabled"] is True
    assert disabled.get("EnvironmentVariables", {}).get(RETENTION_FLAG) is None
    assert enabled["EnvironmentVariables"] == {RETENTION_FLAG: "1"}
    assert discovery.get("EnvironmentVariables", {}).get(RETENTION_FLAG) is None

    operational_fields = (
        "ProgramArguments",
        "StartInterval",
        "Label",
        "WorkingDirectory",
        "StandardOutPath",
        "StandardErrorPath",
        "RunAtLoad",
    )
    assert {key: disabled[key] for key in operational_fields} == {
        key: enabled[key] for key in operational_fields
    }
    assert enabled["RunAtLoad"] is False
    assert "DATABASE_URL" not in enabled["EnvironmentVariables"]
    assert "OWNER" not in enabled["EnvironmentVariables"]
    assert "manage_himalayas_retention" not in " ".join(
        enabled["ProgramArguments"]
    )

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

from src.config.settings import (
    ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR,
    SCHEDULER_RUN_HISTORY_PATH,
)
from src.pipeline.post_run_summary import write_post_run_summary_artifact
from src.pipeline.post_run_email import write_post_run_email_outbox_artifact
from src.pipeline.post_run_email_delivery import deliver_post_run_email_outbox

DEFAULT_SCHEDULED_OUTPUT_DIR = Path(ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR)
DEFAULT_SCHEDULER_RUN_HISTORY_PATH = Path(SCHEDULER_RUN_HISTORY_PATH)
DEFAULT_LLM_ACTIONS = "APPLY,APPLY_REVIEW_VARIANTS"
DEFAULT_DELETE_SEEN_DATA = "no"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LAUNCHD_OUT_DIR = Path("data/launchd")
DEFAULT_LAUNCHD_LOG_DIR = Path("outputs/scheduler_logs")
DEFAULT_LAUNCHD_LABEL_PREFIX = "com.jobstack.scheduler"
DEFAULT_LAUNCHD_INTERVAL_SECONDS = 21600
DEFAULT_LAUNCHD_AGENT_DIR = Path("~/Library/LaunchAgents").expanduser()
DEFAULT_LAUNCHD_TARGET = f"gui/{os.getuid()}"

@dataclass(frozen=True)
class ScheduledJobDefinition:
    name: str
    description: str


_SUPPORTED_SCHEDULED_JOBS: Tuple[ScheduledJobDefinition, ...] = (
    ScheduledJobDefinition(
        name="agent_discovery",
        description="Run standalone company discovery agent.",
    ),
    ScheduledJobDefinition(
        name="live_pipeline",
        description="Run main pipeline and optionally downstream application planning.",
    ),
)


def _job_app():
    import job_app
    return job_app


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_scheduler_run_id() -> str:
    return datetime.now(timezone.utc).strftime("sched_%Y%m%dT%H%M%SZ")


def _normalize_job_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("-", "_").replace(" ", "_")
    return text


def _normalize_llm_actions(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        raw_parts = [str(item or "").strip() for item in value]
    else:
        raw_parts = [part.strip() for part in str(value or "").split(",")]

    normalized: List[str] = []
    for part in raw_parts:
        if part and part not in normalized:
            normalized.append(part)

    if not normalized:
        normalized = ["APPLY", "APPLY_REVIEW_VARIANTS"]

    return ",".join(normalized)


def _normalize_delete_seen_data(value: Any) -> str:
    raw = str(value or "").strip().lower()

    if raw in {"yes", "y", "true", "1"}:
        return "yes"

    if raw in {"ask", "prompt"}:
        return "ask"

    return "no"


def _normalize_non_negative_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc

    if parsed < 0:
        raise ValueError(f"{field_name} must be >= 0.")

    return parsed

def _normalize_positive_int(value: Any, field_name: str) -> int:
    parsed = _normalize_non_negative_int(value, field_name)
    if parsed <= 0:
        raise ValueError(f"{field_name} must be > 0.")
    return parsed


def _normalize_launchd_label_piece(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", ".", text).strip(".")
    return text or fallback

def _normalize_launchd_agent_dir(value: Any) -> Path:
    raw = str(value or DEFAULT_LAUNCHD_AGENT_DIR).strip()
    if not raw:
        raw = str(DEFAULT_LAUNCHD_AGENT_DIR)
    return Path(raw).expanduser()


def _normalize_launchd_target(value: Any) -> str:
    raw = str(value or DEFAULT_LAUNCHD_TARGET).strip()
    if not raw:
        raw = DEFAULT_LAUNCHD_TARGET
    return raw


def _launchd_service_target(target: str, label: str) -> str:
    return f"{target}/{label}"


def _require_launchctl() -> None:
    if shutil.which("launchctl") is None:
        raise SystemExit("launchctl is not available on PATH.")


def _run_launchctl(
    cmd: List[str],
    *,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
    )

def _normalize_output_dir(value: Any) -> str:
    raw = str(value or DEFAULT_SCHEDULED_OUTPUT_DIR).strip()
    if not raw:
        raw = str(DEFAULT_SCHEDULED_OUTPUT_DIR)
    return str(Path(raw).expanduser())


def _resolve_history_path(value: Any = DEFAULT_SCHEDULER_RUN_HISTORY_PATH) -> Path:
    raw = str(value or DEFAULT_SCHEDULER_RUN_HISTORY_PATH).strip()
    if not raw:
        raw = str(DEFAULT_SCHEDULER_RUN_HISTORY_PATH)
    return Path(raw).expanduser()

def _derive_live_pipeline_log_path(output_dir: Any) -> str:
    return str(Path(_normalize_output_dir(output_dir)) / "live_pipeline_run.log")


def _derive_live_pipeline_status_path(output_dir: Any) -> str:
    return str(Path(_normalize_output_dir(output_dir)) / "live_pipeline_status.json")


def _build_scheduled_child_env(
    job_name: Any,
    *,
    run_id: str,
    options: Dict[str, Any],
) -> Dict[str, str]:
    env = dict(os.environ)

    if _normalize_job_name(job_name) != "live_pipeline":
        return env

    env["JOB_APP_PIPELINE_STATUS_PATH"] = _derive_live_pipeline_status_path(
        options.get("output_dir", DEFAULT_SCHEDULED_OUTPUT_DIR)
    )
    env["JOB_APP_PIPELINE_RUN_ID"] = str(run_id)
    return env


def _resolve_post_run_email_delivery_mode() -> str:
    raw = str(os.getenv("JOB_STACK_POST_RUN_EMAIL_MODE", "") or "").strip().lower()
    return raw or "outbox_only"


def _supported_job_names() -> List[str]:
    return [item.name for item in _SUPPORTED_SCHEDULED_JOBS]


def _command_to_text(cmd: List[str]) -> str:
    return shlex.join([str(part) for part in cmd])


def get_scheduled_job_definitions() -> List[Dict[str, str]]:
    return [
        {
            "name": item.name,
            "description": item.description,
        }
        for item in _SUPPORTED_SCHEDULED_JOBS
    ]


def get_scheduled_job_definition(job_name: Any) -> Dict[str, str]:
    normalized = _normalize_job_name(job_name)

    for item in _SUPPORTED_SCHEDULED_JOBS:
        if item.name == normalized:
            return {
                "name": item.name,
                "description": item.description,
            }

    allowed = ", ".join(item.name for item in _SUPPORTED_SCHEDULED_JOBS)
    raise ValueError(f"Unsupported scheduled job={job_name!r}. Allowed: {allowed}")


def build_agent_discovery_command() -> List[str]:
    return [sys.executable, "-u", "run_agent_discovery.py"]


def build_live_pipeline_command(
    *,
    run_application_planning: bool = True,
    planning_only: bool = False,
    output_dir: Any = DEFAULT_SCHEDULED_OUTPUT_DIR,
    job_limit: Any = 50,
    job_packet_limit: Any = 0,
    llm_actions: Any = DEFAULT_LLM_ACTIONS,
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: Any = DEFAULT_DELETE_SEEN_DATA,
) -> List[str]:
    ja = _job_app()

    args = SimpleNamespace(
        run_application_planning=bool(run_application_planning),
        job_limit=_normalize_non_negative_int(job_limit, "job_limit"),
        job_packet_limit=_normalize_non_negative_int(
            job_packet_limit,
            "job_packet_limit",
        ),
        output_dir=_normalize_output_dir(output_dir),
        llm_actions=_normalize_llm_actions(llm_actions),
        generate_tailoring=bool(generate_tailoring),
        generate_llm_tailoring=bool(generate_llm_tailoring),
        refresh_llm_tailoring=bool(refresh_llm_tailoring),
        generate_llm_fallback=bool(generate_llm_fallback),
        delete_seen_data=_normalize_delete_seen_data(delete_seen_data),
    )

    return ja._build_main_cmd(args, planning_only=bool(planning_only))


def build_scheduled_job_command(
    job_name: Any,
    *,
    run_application_planning: bool = True,
    planning_only: bool = False,
    output_dir: Any = DEFAULT_SCHEDULED_OUTPUT_DIR,
    job_limit: Any = 50,
    job_packet_limit: Any = 0,
    llm_actions: Any = DEFAULT_LLM_ACTIONS,
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: Any = DEFAULT_DELETE_SEEN_DATA,
) -> List[str]:
    normalized = _normalize_job_name(job_name)

    if normalized == "agent_discovery":
        return build_agent_discovery_command()

    if normalized == "live_pipeline":
        return build_live_pipeline_command(
            run_application_planning=run_application_planning,
            planning_only=planning_only,
            output_dir=output_dir,
            job_limit=job_limit,
            job_packet_limit=job_packet_limit,
            llm_actions=llm_actions,
            generate_tailoring=generate_tailoring,
            generate_llm_tailoring=generate_llm_tailoring,
            refresh_llm_tailoring=refresh_llm_tailoring,
            generate_llm_fallback=generate_llm_fallback,
            delete_seen_data=delete_seen_data,
        )

    allowed = ", ".join(item.name for item in _SUPPORTED_SCHEDULED_JOBS)
    raise ValueError(f"Unsupported scheduled job={job_name!r}. Allowed: {allowed}")

def build_scheduler_wrapper_command(
    job_name: Any,
    *,
    run_application_planning: bool = True,
    planning_only: bool = False,
    output_dir: Any = DEFAULT_SCHEDULED_OUTPUT_DIR,
    job_limit: Any = 50,
    job_packet_limit: Any = 0,
    llm_actions: Any = DEFAULT_LLM_ACTIONS,
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: Any = DEFAULT_DELETE_SEEN_DATA,
    history_path: Any = DEFAULT_SCHEDULER_RUN_HISTORY_PATH,
    sync_postgres_run_history: bool = False,
    require_postgres_run_history_sync: bool = False,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    allow_contract_drift: bool = False,
) -> List[str]:
    definition = get_scheduled_job_definition(job_name)
    normalized_job = definition["name"]

    cmd: List[str] = [
        sys.executable,
        "-u",
        "-m",
        "src.pipeline.scheduler",
        "--job",
        normalized_job,
        "--history-path",
        str(_resolve_history_path(history_path)),
    ]

    if planning_only:
        cmd.append("--planning-only")

    if not run_application_planning:
        cmd.append("--skip-application-planning")

    if normalized_job == "live_pipeline":
        cmd.extend(
            [
                "--output-dir",
                _normalize_output_dir(output_dir),
                "--job-limit",
                str(_normalize_non_negative_int(job_limit, "job_limit")),
                "--job-packet-limit",
                str(_normalize_non_negative_int(job_packet_limit, "job_packet_limit")),
                "--llm-actions",
                _normalize_llm_actions(llm_actions),
                "--delete-seen-data",
                _normalize_delete_seen_data(delete_seen_data),
            ]
        )

        if generate_tailoring:
            cmd.append("--generate-tailoring")
        if generate_llm_tailoring:
            cmd.append("--generate-llm-tailoring")
        if refresh_llm_tailoring:
            cmd.append("--refresh-llm-tailoring")
        if generate_llm_fallback:
            cmd.append("--generate-llm-fallback")

    if sync_postgres_run_history:
        cmd.append("--sync-postgres-run-history")
    if require_postgres_run_history_sync:
        cmd.append("--require-postgres-run-history-sync")
    if database_url:
        cmd.extend(["--database-url", str(database_url)])
    if database_url_env and str(database_url_env).strip() and str(database_url_env).strip() != "DATABASE_URL":
        cmd.extend(["--database-url-env", str(database_url_env).strip()])
    if psql_bin and str(psql_bin).strip() and str(psql_bin).strip() != "psql":
        cmd.extend(["--psql-bin", str(psql_bin).strip()])
    if allow_contract_drift:
        cmd.append("--allow-contract-drift")

    return cmd


def build_scheduler_launchd_label(
    job_name: Any,
    *,
    planning_only: bool = False,
    label_prefix: str = DEFAULT_LAUNCHD_LABEL_PREFIX,
) -> str:
    definition = get_scheduled_job_definition(job_name)
    prefix = _normalize_launchd_label_piece(label_prefix, "com.jobstack.scheduler")

    suffix_parts = [definition["name"]]
    if definition["name"] == "live_pipeline" and planning_only:
        suffix_parts.append("planning_only")

    suffix = ".".join(
        _normalize_launchd_label_piece(part, "job")
        for part in suffix_parts
    )
    return f"{prefix}.{suffix}"


def build_scheduler_launchd_plist_payload(
    job_name: Any,
    *,
    run_application_planning: bool = True,
    planning_only: bool = False,
    output_dir: Any = DEFAULT_SCHEDULED_OUTPUT_DIR,
    job_limit: Any = 50,
    job_packet_limit: Any = 0,
    llm_actions: Any = DEFAULT_LLM_ACTIONS,
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: Any = DEFAULT_DELETE_SEEN_DATA,
    history_path: Any = DEFAULT_SCHEDULER_RUN_HISTORY_PATH,
    sync_postgres_run_history: bool = False,
    require_postgres_run_history_sync: bool = False,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    allow_contract_drift: bool = False,
    launchd_interval_seconds: Any = DEFAULT_LAUNCHD_INTERVAL_SECONDS,
    launchd_out_dir: Any = DEFAULT_LAUNCHD_OUT_DIR,
    launchd_log_dir: Any = DEFAULT_LAUNCHD_LOG_DIR,
    launchd_label_prefix: str = DEFAULT_LAUNCHD_LABEL_PREFIX,
) -> Dict[str, Any]:
    interval_seconds = _normalize_positive_int(
        launchd_interval_seconds,
        "launchd_interval_seconds",
    )
    label = build_scheduler_launchd_label(
        job_name,
        planning_only=planning_only,
        label_prefix=launchd_label_prefix,
    )

    launchd_out_dir_path = Path(str(launchd_out_dir or DEFAULT_LAUNCHD_OUT_DIR)).expanduser()
    launchd_log_dir_path = Path(str(launchd_log_dir or DEFAULT_LAUNCHD_LOG_DIR)).expanduser()

    command = build_scheduler_wrapper_command(
        job_name,
        run_application_planning=run_application_planning,
        planning_only=planning_only,
        output_dir=output_dir,
        job_limit=job_limit,
        job_packet_limit=job_packet_limit,
        llm_actions=llm_actions,
        generate_tailoring=generate_tailoring,
        generate_llm_tailoring=generate_llm_tailoring,
        refresh_llm_tailoring=refresh_llm_tailoring,
        generate_llm_fallback=generate_llm_fallback,
        delete_seen_data=delete_seen_data,
        history_path=history_path,
        sync_postgres_run_history=sync_postgres_run_history,
        require_postgres_run_history_sync=require_postgres_run_history_sync,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        allow_contract_drift=allow_contract_drift,
    )

    plist_path = launchd_out_dir_path / f"{label}.plist"
    stdout_log_path = launchd_log_dir_path / f"{label}.out.log"
    stderr_log_path = launchd_log_dir_path / f"{label}.err.log"

    plist_data = {
        "Label": label,
        "ProgramArguments": command,
        "WorkingDirectory": str(REPO_ROOT),
        "RunAtLoad": False,
        "StartInterval": interval_seconds,
        "StandardOutPath": str(stdout_log_path),
        "StandardErrorPath": str(stderr_log_path),
        "ProcessType": "Background",
        "AbandonProcessGroup": True,
    }
    plist_xml = plistlib.dumps(
        plist_data,
        fmt=plistlib.FMT_XML,
        sort_keys=True,
    ).decode("utf-8")

    return {
        "job_name": get_scheduled_job_definition(job_name)["name"],
        "planning_only": bool(planning_only),
        "run_application_planning": bool(run_application_planning),
        "label": label,
        "launchd_label_prefix": _normalize_launchd_label_piece(
            launchd_label_prefix,
            "com.jobstack.scheduler",
        ),
        "launchd_interval_seconds": interval_seconds,
        "working_directory": str(REPO_ROOT),
        "command": command,
        "command_text": _command_to_text(command),
        "plist_path": str(plist_path),
        "stdout_log_path": str(stdout_log_path),
        "stderr_log_path": str(stderr_log_path),
        "plist_xml": plist_xml,
    }


def write_scheduler_launchd_plist(
    job_name: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = build_scheduler_launchd_plist_payload(job_name, **kwargs)

    plist_path = Path(payload["plist_path"]).expanduser()
    stdout_log_path = Path(payload["stdout_log_path"]).expanduser()
    stderr_log_path = Path(payload["stderr_log_path"]).expanduser()

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_log_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_log_path.parent.mkdir(parents=True, exist_ok=True)

    plist_path.write_text(payload["plist_xml"], encoding="utf-8")
    return payload

def build_scheduler_launchd_agent_payload(
    job_name: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    filtered_kwargs = dict(kwargs)

    launchd_agent_dir = _normalize_launchd_agent_dir(
        filtered_kwargs.pop("launchd_agent_dir", DEFAULT_LAUNCHD_AGENT_DIR)
    )
    launchd_target = _normalize_launchd_target(
        filtered_kwargs.pop("launchd_target", DEFAULT_LAUNCHD_TARGET)
    )

    payload = build_scheduler_launchd_plist_payload(job_name, **filtered_kwargs)

    label = str(payload["label"])
    installed_plist_path = launchd_agent_dir / f"{label}.plist"
    service_target = _launchd_service_target(launchd_target, label)

    enriched = dict(payload)
    enriched.update(
        {
            "launchd_agent_dir": str(launchd_agent_dir),
            "launchd_target": launchd_target,
            "installed_plist_path": str(installed_plist_path),
            "service_target": service_target,
            "bootstrap_command": [
                "launchctl",
                "bootstrap",
                launchd_target,
                str(installed_plist_path),
            ],
            "bootout_command": [
                "launchctl",
                "bootout",
                service_target,
            ],
            "enable_command": [
                "launchctl",
                "enable",
                service_target,
            ],
            "disable_command": [
                "launchctl",
                "disable",
                service_target,
            ],
            "print_command": [
                "launchctl",
                "print",
                service_target,
            ],
        }
    )
    return enriched


def get_scheduler_launchd_agent_status(
    job_name: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = build_scheduler_launchd_agent_payload(job_name, **kwargs)

    installed_plist_path = Path(payload["installed_plist_path"]).expanduser()
    payload["installed_plist_exists"] = installed_plist_path.exists()

    if shutil.which("launchctl") is None:
        payload["launchctl_available"] = False
        payload["loaded"] = False
        payload["print_return_code"] = None
        payload["print_stdout"] = ""
        payload["print_stderr"] = ""
        return payload

    completed = _run_launchctl(payload["print_command"], check=False)

    payload["launchctl_available"] = True
    payload["loaded"] = completed.returncode == 0
    payload["print_return_code"] = int(completed.returncode)
    payload["print_stdout"] = completed.stdout or ""
    payload["print_stderr"] = completed.stderr or ""
    return payload


def install_scheduler_launchd_agent(
    job_name: Any,
    *,
    print_only: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = build_scheduler_launchd_agent_payload(job_name, **kwargs)

    if print_only:
        payload["install_preview"] = True
        return payload

    _require_launchctl()

    installed_plist_path = Path(payload["installed_plist_path"]).expanduser()
    installed_plist_path.parent.mkdir(parents=True, exist_ok=True)
    installed_plist_path.write_text(str(payload["plist_xml"]), encoding="utf-8")

    _run_launchctl(payload["bootout_command"], check=False)
    _run_launchctl(payload["bootstrap_command"], check=True)
    _run_launchctl(payload["enable_command"], check=False)

    payload["installed"] = True
    payload["installed_plist_exists"] = installed_plist_path.exists()
    return payload


def uninstall_scheduler_launchd_agent(
    job_name: Any,
    *,
    print_only: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = build_scheduler_launchd_agent_payload(job_name, **kwargs)

    if print_only:
        payload["uninstall_preview"] = True
        return payload

    _require_launchctl()

    installed_plist_path = Path(payload["installed_plist_path"]).expanduser()

    _run_launchctl(payload["disable_command"], check=False)
    _run_launchctl(payload["bootout_command"], check=False)

    removed = False
    if installed_plist_path.exists():
        installed_plist_path.unlink()
        removed = True

    payload["uninstalled"] = True
    payload["removed_plist"] = removed
    payload["installed_plist_exists"] = installed_plist_path.exists()
    return payload


def build_scheduler_run_record(
    *,
    run_id: str,
    job_name: str,
    job_description: str,
    command: List[str],
    status: str,
    started_at: str,
    finished_at: str,
    return_code: int,
    options: Dict[str, Any],
    error: str = "",
) -> Dict[str, Any]:
    return {
        "run_id": str(run_id),
        "job_name": str(job_name),
        "job_description": str(job_description),
        "status": str(status),
        "started_at": str(started_at),
        "finished_at": str(finished_at),
        "return_code": int(return_code),
        "command": [str(part) for part in command],
        "command_text": _command_to_text(command),
        "options": dict(options),
        "trigger_source": "external_scheduler_wrapper",
        "error": str(error or ""),
    }


def append_scheduler_run_record(
    record: Dict[str, Any],
    *,
    history_path: Any = DEFAULT_SCHEDULER_RUN_HISTORY_PATH,
) -> Path:
    path = _resolve_history_path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    return path


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Canonical command wrapper for externally scheduled pipeline jobs."
    )
    parser.add_argument(
        "--job",
        required=True,
        choices=_supported_job_names(),
        help="Supported scheduled job name.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the resolved command without executing it.",
    )
    parser.add_argument(
        "--planning-only",
        action="store_true",
        help="For live_pipeline only: skip scraping and run planning against existing corpus.",
    )
    parser.add_argument(
        "--skip-application-planning",
        action="store_true",
        help="For live_pipeline only: do not append downstream application planning flags.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_SCHEDULED_OUTPUT_DIR),
        help="For live_pipeline only: application planning output directory.",
    )
    parser.add_argument(
        "--job-limit",
        type=int,
        default=50,
        help="For live_pipeline only: planning job limit.",
    )
    parser.add_argument(
        "--job-packet-limit",
        type=int,
        default=0,
        help="For live_pipeline only: planning packet limit.",
    )
    parser.add_argument(
        "--llm-actions",
        default=DEFAULT_LLM_ACTIONS,
        help="For live_pipeline only: comma-separated planning actions eligible for LLM tailoring.",
    )
    parser.add_argument(
        "--generate-tailoring",
        action="store_true",
        help="For live_pipeline only: pass generate-tailoring.",
    )
    parser.add_argument(
        "--generate-llm-tailoring",
        action="store_true",
        help="For live_pipeline only: pass generate-llm-tailoring.",
    )
    parser.add_argument(
        "--refresh-llm-tailoring",
        action="store_true",
        help="For live_pipeline only: refresh cached LLM tailoring.",
    )
    parser.add_argument(
        "--generate-llm-fallback",
        action="store_true",
        help="For live_pipeline only: pass generate-llm-fallback.",
    )
    parser.add_argument(
        "--delete-seen-data",
        choices=["ask", "yes", "no"],
        default=DEFAULT_DELETE_SEEN_DATA,
        help="For live_pipeline only: seen-job reset behavior.",
    )
    parser.add_argument(
        "--history-path",
        default=str(DEFAULT_SCHEDULER_RUN_HISTORY_PATH),
        help="JSONL file used to append scheduler run history records.",
    )
    parser.add_argument(
        "--sync-postgres-run-history",
        action="store_true",
        help="After appending the scheduler JSONL record, sync scheduler_run_history into Postgres.",
    )
    parser.add_argument(
        "--require-postgres-run-history-sync",
        action="store_true",
        help="Fail the wrapper run if Postgres run-history sync fails. By default, Postgres sync is best-effort and JSONL remains the fallback audit trail.",
    )
    parser.add_argument(
        "--database-url",
        default="",
        help="For optional Postgres run-history sync: explicit Postgres connection URL.",
    )
    parser.add_argument(
        "--database-url-env",
        default="DATABASE_URL",
        help="For optional Postgres run-history sync: environment variable that holds the Postgres connection URL.",
    )
    parser.add_argument(
        "--psql-bin",
        default="psql",
        help="For optional Postgres run-history sync: psql executable to use.",
    )
    parser.add_argument(
        "--allow-contract-drift",
        action="store_true",
        help="For optional Postgres run-history sync: allow sync even if scheduler SQL artifact drift checks fail.",
    )
    parser.add_argument(
        "--emit-launchd-plist",
        action="store_true",
        help="Build and print a launchd plist preview for this scheduler job instead of running it.",
    )
    parser.add_argument(
        "--write-launchd-plist",
        action="store_true",
        help="Write a launchd plist artifact for this scheduler job instead of running it.",
    )
    parser.add_argument(
        "--launchd-interval-seconds",
        type=int,
        default=DEFAULT_LAUNCHD_INTERVAL_SECONDS,
        help="launchd StartInterval value for plist generation.",
    )
    parser.add_argument(
        "--launchd-out-dir",
        default=str(DEFAULT_LAUNCHD_OUT_DIR),
        help="Directory where generated launchd plist files are written.",
    )
    parser.add_argument(
        "--launchd-log-dir",
        default=str(DEFAULT_LAUNCHD_LOG_DIR),
        help="Directory used for launchd stdout/stderr log files.",
    )
    parser.add_argument(
        "--launchd-label-prefix",
        default=DEFAULT_LAUNCHD_LABEL_PREFIX,
        help="Prefix used when constructing launchd labels.",
    )
    parser.add_argument(
        "--install-launchd-agent",
        action="store_true",
        help="Write the launchd plist into the LaunchAgents directory and load it with launchctl.",
    )
    parser.add_argument(
        "--uninstall-launchd-agent",
        action="store_true",
        help="Unload the launchd agent and remove its plist from the LaunchAgents directory.",
    )
    parser.add_argument(
        "--launchd-agent-status",
        action="store_true",
        help="Show launchd agent installation/load status for this scheduler job.",
    )
    parser.add_argument(
        "--launchd-agent-dir",
        default=str(DEFAULT_LAUNCHD_AGENT_DIR),
        help="Directory used for installed launchd agent plist files.",
    )
    parser.add_argument(
        "--launchd-target",
        default=DEFAULT_LAUNCHD_TARGET,
        help="launchctl target, usually gui/<uid> for user LaunchAgents.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    options = {
        "planning_only": bool(args.planning_only),
        "run_application_planning": not bool(args.skip_application_planning),
        "output_dir": _normalize_output_dir(args.output_dir),
        "job_limit": _normalize_non_negative_int(args.job_limit, "job_limit"),
        "job_packet_limit": _normalize_non_negative_int(
            args.job_packet_limit,
            "job_packet_limit",
        ),
        "llm_actions": _normalize_llm_actions(args.llm_actions),
        "generate_tailoring": bool(args.generate_tailoring),
        "generate_llm_tailoring": bool(args.generate_llm_tailoring),
        "refresh_llm_tailoring": bool(args.refresh_llm_tailoring),
        "generate_llm_fallback": bool(args.generate_llm_fallback),
        "delete_seen_data": _normalize_delete_seen_data(args.delete_seen_data),
    }

    definition = get_scheduled_job_definition(args.job)
    if definition["name"] == "live_pipeline":
        options["log_path"] = _derive_live_pipeline_log_path(options["output_dir"])
        options["status_path"] = _derive_live_pipeline_status_path(options["output_dir"])

    lifecycle_mode_count = sum(
        [
            bool(args.emit_launchd_plist),
            bool(args.write_launchd_plist),
            bool(args.install_launchd_agent),
            bool(args.uninstall_launchd_agent),
            bool(args.launchd_agent_status),
        ]
    )
    if lifecycle_mode_count > 1:
        raise SystemExit(
            "Choose only one launchd lifecycle mode at a time: "
            "--emit-launchd-plist, --write-launchd-plist, "
            "--install-launchd-agent, --uninstall-launchd-agent, or --launchd-agent-status."
        )
    
    cmd = build_scheduled_job_command(
        args.job,
        run_application_planning=options["run_application_planning"],
        planning_only=options["planning_only"],
        output_dir=options["output_dir"],
        job_limit=options["job_limit"],
        job_packet_limit=options["job_packet_limit"],
        llm_actions=options["llm_actions"],
        generate_tailoring=options["generate_tailoring"],
        generate_llm_tailoring=options["generate_llm_tailoring"],
        refresh_llm_tailoring=options["refresh_llm_tailoring"],
        generate_llm_fallback=options["generate_llm_fallback"],
        delete_seen_data=options["delete_seen_data"],
    )

    launchd_kwargs = {
        "run_application_planning": options["run_application_planning"],
        "planning_only": options["planning_only"],
        "output_dir": options["output_dir"],
        "job_limit": options["job_limit"],
        "job_packet_limit": options["job_packet_limit"],
        "llm_actions": options["llm_actions"],
        "generate_tailoring": options["generate_tailoring"],
        "generate_llm_tailoring": options["generate_llm_tailoring"],
        "refresh_llm_tailoring": options["refresh_llm_tailoring"],
        "generate_llm_fallback": options["generate_llm_fallback"],
        "delete_seen_data": options["delete_seen_data"],
        "history_path": args.history_path,
        "sync_postgres_run_history": bool(args.sync_postgres_run_history),
        "require_postgres_run_history_sync": bool(args.require_postgres_run_history_sync),
        "database_url": args.database_url,
        "database_url_env": args.database_url_env,
        "psql_bin": args.psql_bin,
        "allow_contract_drift": bool(args.allow_contract_drift),
        "launchd_interval_seconds": args.launchd_interval_seconds,
        "launchd_out_dir": args.launchd_out_dir,
        "launchd_log_dir": args.launchd_log_dir,
        "launchd_label_prefix": args.launchd_label_prefix,
        "launchd_agent_dir": args.launchd_agent_dir,
        "launchd_target": args.launchd_target,
    }

    if args.launchd_agent_status:
        launchd_payload = get_scheduler_launchd_agent_status(args.job, **launchd_kwargs)
        print(f"launchd_label={launchd_payload['label']}")
        print(f"launchd_target={launchd_payload['launchd_target']}")
        print(f"installed_plist_path={launchd_payload['installed_plist_path']}")
        print(f"installed_plist_exists={launchd_payload['installed_plist_exists']}")
        print(f"launchctl_available={launchd_payload['launchctl_available']}")
        print(f"loaded={launchd_payload['loaded']}")
        print(f"print_return_code={launchd_payload['print_return_code']}")
        return 0

    if args.install_launchd_agent:
        launchd_payload = install_scheduler_launchd_agent(
            args.job,
            print_only=bool(args.print_only),
            **launchd_kwargs,
        )
        if args.print_only:
            print("launchd_install_preview=true")
        else:
            print("launchd_agent_installed=true")
        print(f"launchd_label={launchd_payload['label']}")
        print(f"launchd_target={launchd_payload['launchd_target']}")
        print(f"installed_plist_path={launchd_payload['installed_plist_path']}")
        print(f"bootstrap_command={_command_to_text(launchd_payload['bootstrap_command'])}")
        print(f"bootout_command={_command_to_text(launchd_payload['bootout_command'])}")
        print(f"enable_command={_command_to_text(launchd_payload['enable_command'])}")
        return 0

    if args.uninstall_launchd_agent:
        launchd_payload = uninstall_scheduler_launchd_agent(
            args.job,
            print_only=bool(args.print_only),
            **launchd_kwargs,
        )
        if args.print_only:
            print("launchd_uninstall_preview=true")
        else:
            print("launchd_agent_uninstalled=true")
        print(f"launchd_label={launchd_payload['label']}")
        print(f"launchd_target={launchd_payload['launchd_target']}")
        print(f"installed_plist_path={launchd_payload['installed_plist_path']}")
        print(f"disable_command={_command_to_text(launchd_payload['disable_command'])}")
        print(f"bootout_command={_command_to_text(launchd_payload['bootout_command'])}")
        return 0

    if args.emit_launchd_plist or args.write_launchd_plist:
        if args.write_launchd_plist:
            launchd_payload = write_scheduler_launchd_plist(args.job, **launchd_kwargs)
            print("launchd_plist_written=true")
        else:
            launchd_payload = build_scheduler_launchd_plist_payload(args.job, **launchd_kwargs)

        print(f"launchd_label={launchd_payload['label']}")
        print(f"launchd_interval_seconds={launchd_payload['launchd_interval_seconds']}")
        print(f"working_directory={launchd_payload['working_directory']}")
        print(f"plist_path={launchd_payload['plist_path']}")
        print(f"stdout_log_path={launchd_payload['stdout_log_path']}")
        print(f"stderr_log_path={launchd_payload['stderr_log_path']}")
        print(f"command={launchd_payload['command_text']}")

        if args.emit_launchd_plist:
            print(launchd_payload["plist_xml"])

        return 0

    print(_command_to_text(cmd))

    if args.print_only:
        return 0

    run_id = _new_scheduler_run_id()
    started_at = _utc_now()
    finished_at = started_at
    return_code = 1
    error = ""

    child_env = _build_scheduled_child_env(
        definition["name"],
        run_id=run_id,
        options=options,
    )

    try:
        completed = subprocess.run(
            cmd,
            check=False,
            env=child_env,
        )
        return_code = int(completed.returncode)
    except Exception as exc:
        error = repr(exc)

    finished_at = _utc_now()
    status = "succeeded" if return_code == 0 and not error else "failed"

    record = build_scheduler_run_record(
        run_id=run_id,
        job_name=definition["name"],
        job_description=definition["description"],
        command=cmd,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        return_code=return_code,
        options=options,
        error=error,
    )

    post_run_summary_payload = {}
    try:
        post_run_summary_payload = write_post_run_summary_artifact(record)
        record.setdefault("options", {})["post_run_summary_path"] = post_run_summary_payload["path"]
        print(f"post_run_summary_path={post_run_summary_payload['path']}")
    except Exception as exc:
        print(
            f"WARNING: failed to write post-run summary artifact: {exc!r}",
            file=sys.stderr,
        )

    post_run_email_payload = {}

    if post_run_summary_payload:
        try:
            post_run_email_payload = write_post_run_email_outbox_artifact(
                post_run_summary_payload["payload"],
                post_run_summary_path=post_run_summary_payload["path"],
            )
            record.setdefault("options", {})["post_run_email_outbox_path"] = post_run_email_payload["path"]
            print(f"post_run_email_outbox_path={post_run_email_payload['path']}")
        except Exception as exc:
            print(
                f"WARNING: failed to write post-run email outbox artifact: {exc!r}",
                file=sys.stderr,
            )

    if post_run_email_payload:
        try:
            delivery_mode = _resolve_post_run_email_delivery_mode()
            post_run_email_delivery_payload = deliver_post_run_email_outbox(
                post_run_email_payload["path"],
                mode=delivery_mode,
            )
            record.setdefault("options", {})["post_run_email_delivery_mode"] = delivery_mode
            record.setdefault("options", {})["post_run_email_delivery_path"] = post_run_email_delivery_payload["path"]
            print(f"post_run_email_delivery_mode={delivery_mode}")
            print(f"post_run_email_delivery_path={post_run_email_delivery_payload['path']}")
        except Exception as exc:
            print(
                f"WARNING: failed to record post-run email delivery result: {exc!r}",
                file=sys.stderr,
            )

    try:
        append_scheduler_run_record(
            record,
            history_path=args.history_path,
        )
    except Exception as exc:
        print(
            f"WARNING: failed to append scheduler run history: {exc!r}",
            file=sys.stderr,
        )

    if args.sync_postgres_run_history:
        from src.storage.sync_scheduler_run_history import (
            insert_scheduler_run_history_row_to_postgres,
        )

        try:
            sync_payload = insert_scheduler_run_history_row_to_postgres(
                record=record,
                history_path=Path(args.history_path).expanduser(),
                database_url=args.database_url,
                database_url_env=args.database_url_env,
                psql_bin=args.psql_bin,
                print_only=False,
                allow_contract_drift=bool(args.allow_contract_drift),
            )

            print(f"postgres_sync_history_path={sync_payload['history_path']}")
            print(f"postgres_sync_row_count={sync_payload['history_row_count']}")
            if sync_payload.get("skipped") == "no_rows":
                print("postgres_sync_skipped=no_rows")
            else:
                print(f"postgres_sync_command={sync_payload['command_text']}")
        except SystemExit as exc:
            if args.require_postgres_run_history_sync:
                raise
            print(f"postgres_sync_warning={exc}")
            print("postgres_sync_status=non_fatal_failure")
        except Exception as exc:
            if args.require_postgres_run_history_sync:
                raise
            print(f"postgres_sync_warning={repr(exc)}")
            print("postgres_sync_status=non_fatal_failure")

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
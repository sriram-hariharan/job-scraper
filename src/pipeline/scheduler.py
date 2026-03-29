from __future__ import annotations

import argparse
import json
import shlex
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

DEFAULT_SCHEDULED_OUTPUT_DIR = Path(ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR)
DEFAULT_SCHEDULER_RUN_HISTORY_PATH = Path(SCHEDULER_RUN_HISTORY_PATH)
DEFAULT_LLM_ACTIONS = "APPLY,APPLY_REVIEW_VARIANTS"
DEFAULT_DELETE_SEEN_DATA = "no"


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

    print(_command_to_text(cmd))

    if args.print_only:
        return 0

    run_id = _new_scheduler_run_id()
    started_at = _utc_now()
    finished_at = started_at
    return_code = 1
    error = ""

    try:
        completed = subprocess.run(cmd, check=False)
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

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
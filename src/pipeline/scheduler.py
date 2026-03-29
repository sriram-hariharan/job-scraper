from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple
import sys
import argparse
import shlex
import subprocess

from src.config.settings import ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR

DEFAULT_SCHEDULED_OUTPUT_DIR = Path(ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR)
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



def _supported_job_names() -> List[str]:
    return [item.name for item in _SUPPORTED_SCHEDULED_JOBS]


def _command_to_text(cmd: List[str]) -> str:
    return shlex.join(cmd)


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
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    cmd = build_scheduled_job_command(
        args.job,
        run_application_planning=not bool(args.skip_application_planning),
        planning_only=bool(args.planning_only),
        output_dir=args.output_dir,
        job_limit=args.job_limit,
        job_packet_limit=args.job_packet_limit,
        llm_actions=args.llm_actions,
        generate_tailoring=bool(args.generate_tailoring),
        generate_llm_tailoring=bool(args.generate_llm_tailoring),
        refresh_llm_tailoring=bool(args.refresh_llm_tailoring),
        generate_llm_fallback=bool(args.generate_llm_fallback),
        delete_seen_data=args.delete_seen_data,
    )

    print(_command_to_text(cmd))

    if args.print_only:
        return 0

    subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
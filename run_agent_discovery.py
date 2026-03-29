import json
from datetime import datetime, timezone
from pathlib import Path

from src.agents.company_discovery_agent import run_company_discovery_agent
from src.pipeline.discovery_stage import run_discovery
from src.utils.logging import get_logger

logger = get_logger("run_agent_discovery")

SUMMARY_PATH = Path("outputs/scheduler_logs/agent_discovery_summary.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_summary(payload: dict) -> Path:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = SUMMARY_PATH.with_suffix(SUMMARY_PATH.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(SUMMARY_PATH)

    return SUMMARY_PATH


def main() -> int:
    started_at = _utc_now()
    failures = []
    component_statuses = {
        "company_discovery_agent": "pending",
        "discovery_stage": "pending",
    }
    component_errors = {}
    discovery_summary = {}

    try:
        run_company_discovery_agent()
        component_statuses["company_discovery_agent"] = "succeeded"
    except Exception as exc:
        logger.exception("Standalone company discovery agent failed")
        component_statuses["company_discovery_agent"] = "failed"
        component_errors["company_discovery_agent"] = repr(exc)
        failures.append("company_discovery_agent")

    try:
        discovery_summary = run_discovery() or {}
        component_statuses["discovery_stage"] = "succeeded"
    except Exception as exc:
        logger.exception("Pipeline discovery stage failed")
        component_statuses["discovery_stage"] = "failed"
        component_errors["discovery_stage"] = repr(exc)
        failures.append("discovery_stage")

    summary_message = (
        "Discovery scheduler run completed successfully"
        if not failures
        else f"Discovery scheduler run completed with failures in: {', '.join(failures)}"
    )

    summary_payload = {
        "job_name": "agent_discovery",
        "started_at": started_at,
        "finished_at": _utc_now(),
        "status": "succeeded" if not failures else "failed",
        "return_code": 0 if not failures else 1,
        "component_statuses": component_statuses,
        "failure_components": failures,
        "component_errors": component_errors,
        "discovery_summary": discovery_summary,
        "summary_message": summary_message,
        "error": "; ".join(
            f"{name}={component_errors[name]}"
            for name in failures
            if name in component_errors
        ),
        "summary_path": str(SUMMARY_PATH),
    }

    written_path = _write_summary(summary_payload)
    logger.info("Wrote discovery run summary: %s", written_path)

    if failures:
        raise RuntimeError(summary_message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
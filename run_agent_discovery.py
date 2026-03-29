from src.agents.company_discovery_agent import run_company_discovery_agent
from src.pipeline.discovery_stage import run_discovery
from src.utils.logging import get_logger

logger = get_logger("run_agent_discovery")


def main() -> int:
    failures = []

    try:
        run_company_discovery_agent()
    except Exception:
        logger.exception("Standalone company discovery agent failed")
        failures.append("company_discovery_agent")

    try:
        run_discovery()
    except Exception:
        logger.exception("Pipeline discovery stage failed")
        failures.append("discovery_stage")

    if failures:
        raise RuntimeError(
            f"Discovery scheduler run completed with failures in: {', '.join(failures)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
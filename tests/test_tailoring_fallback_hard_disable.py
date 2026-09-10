from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_ENV_NAMES = (
    "LLM_FALLBACK_ENABLED",
    "TAILOR_LLM_FALLBACK_ENABLED",
)
_DOTENV_NEUTRAL_IMPORT = """
import dotenv
dotenv.load_dotenv = lambda *args, **kwargs: False
import dotenv.main
dotenv.main.load_dotenv = lambda *args, **kwargs: False
import json
from src.tailoring import llm
print("@@RESULT@@" + json.dumps({
    "fallback_enabled": llm.TAILOR_LLM_FALLBACK_ENABLED,
}))
"""


def _isolated_fallback_enabled(
    *,
    generic_enabled: str | None,
    tailoring_enabled: str | None,
) -> bool:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _CONFIG_ENV_NAMES
    }
    if generic_enabled is not None:
        env["LLM_FALLBACK_ENABLED"] = generic_enabled
    if tailoring_enabled is not None:
        env["TAILOR_LLM_FALLBACK_ENABLED"] = tailoring_enabled
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    completed = subprocess.run(
        [sys.executable, "-c", _DOTENV_NEUTRAL_IMPORT],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        pytest.fail(
            "isolated tailoring fallback import failed:\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr[-2000:]}"
        )

    markers = [
        line
        for line in completed.stdout.splitlines()
        if line.startswith("@@RESULT@@")
    ]
    assert markers, f"isolated import produced no result: {completed.stdout[-2000:]}"
    payload = json.loads(markers[-1][len("@@RESULT@@") :])
    return payload["fallback_enabled"]


@pytest.mark.parametrize(
    ("generic_enabled", "tailoring_enabled"),
    (
        ("true", None),
        ("false", None),
        ("true", "true"),
        ("false", "true"),
        ("true", "false"),
    ),
)
def test_tailoring_fallback_is_hard_disabled_in_every_environment_case(
    generic_enabled,
    tailoring_enabled,
):
    assert _isolated_fallback_enabled(
        generic_enabled=generic_enabled,
        tailoring_enabled=tailoring_enabled,
    ) is False

"""P2S18 — tailoring refinement writer/judge default-model configuration contract.

The refinement writer and judge resolve their provider/model at import time from a
layered environment chain in ``src/tailoring/llm.py``. The repository defaults must
name a model that is qualified for the Groq tailoring refinement and judge workloads.

These tests assert repository defaults, so they must not observe the developer
``.env``. Configuration resolution is therefore evaluated in a scrubbed child
process rather than by reloading ``src.tailoring.llm`` in-process: that module is
imported widely across the suite, and reloading it would swap the module object out
from under other tests in the same session.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

QUALIFIED_REFINEMENT_MODEL = "openai/gpt-oss-120b"
QUALIFIED_REFINEMENT_PROVIDER = "groq"

# Every environment variable that participates in the writer or judge
# provider/model chains. Scrubbed so the child process observes source defaults.
WRITER_JUDGE_ENV_NAMES = (
    "TAILORING_REWRITE_MODEL",
    "TAILORING_REWRITE_PROVIDER",
    "PATCH_REFINEMENT_WRITER_MODEL",
    "PATCH_REFINEMENT_WRITER_PROVIDER",
    "TAILORING_JUDGE_MODEL",
    "TAILORING_JUDGE_PROVIDER",
    "PATCH_REFINEMENT_JUDGE_MODEL",
    "PATCH_REFINEMENT_JUDGE_PROVIDER",
    "PATCH_REFINEMENT_MODEL",
    "PATCH_REFINEMENT_PROVIDER",
)

# Several modules on the import chain (``src.resume.resume_loader``,
# ``src.ai.skill_llm_enricher``) call ``dotenv.load_dotenv()`` at import time, which
# would repopulate the scrubbed variables from the developer ``.env``. The probe
# neutralises that loader in the child process only; ``.env`` itself is never read,
# written, or modified.
_DOTENV_STUB = """
import dotenv
dotenv.load_dotenv = lambda *a, **k: False
import dotenv.main
dotenv.main.load_dotenv = lambda *a, **k: False
"""

_RESOLVE_SNIPPET = _DOTENV_STUB + """
import json, sys
sys.path.insert(0, {repo!r})
from src.tailoring import llm
print("@@RESULT@@" + json.dumps({{
    "writer_provider": llm.PATCH_REFINEMENT_WRITER_PROVIDER,
    "writer_model": llm.PATCH_REFINEMENT_WRITER_MODEL,
    "judge_provider": llm.PATCH_REFINEMENT_JUDGE_PROVIDER,
    "judge_model": llm.PATCH_REFINEMENT_JUDGE_MODEL,
    "shared_model": llm.PATCH_REFINEMENT_MODEL,
    "shared_provider": llm.PATCH_REFINEMENT_PROVIDER,
}}))
"""


def _resolve_config(overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Import src.tailoring.llm in a child process with the writer/judge chain scrubbed."""

    env = {
        key: value
        for key, value in os.environ.items()
        if key not in WRITER_JUDGE_ENV_NAMES
    }
    env.update(overrides or {})
    # The module reads credentials lazily, but keep the import cheap and offline.
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")

    completed = subprocess.run(
        [sys.executable, "-c", _RESOLVE_SNIPPET.format(repo=str(REPO_ROOT))],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        pytest.fail(
            "scrubbed-environment import failed:\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr[-2000:]}"
        )
    marker = [
        line for line in completed.stdout.splitlines() if line.startswith("@@RESULT@@")
    ]
    assert marker, f"probe produced no result line: {completed.stdout[-2000:]}"
    return json.loads(marker[-1][len("@@RESULT@@") :])


# --- A. writer clean-environment default -----------------------------------


def test_writer_defaults_to_qualified_groq_refinement_model():
    resolved = _resolve_config()

    assert resolved["writer_provider"] == QUALIFIED_REFINEMENT_PROVIDER
    assert resolved["writer_model"] == QUALIFIED_REFINEMENT_MODEL


# --- B. judge clean-environment default ------------------------------------


def test_judge_defaults_to_qualified_groq_refinement_model():
    resolved = _resolve_config()

    assert resolved["judge_provider"] == QUALIFIED_REFINEMENT_PROVIDER
    assert resolved["judge_model"] == QUALIFIED_REFINEMENT_MODEL


def test_shared_patch_refinement_default_is_the_qualified_model():
    resolved = _resolve_config()

    assert resolved["shared_provider"] == QUALIFIED_REFINEMENT_PROVIDER
    assert resolved["shared_model"] == QUALIFIED_REFINEMENT_MODEL


# --- C. writer precedence unchanged ----------------------------------------


def test_writer_specific_override_still_beats_the_shared_default():
    resolved = _resolve_config({"PATCH_REFINEMENT_WRITER_MODEL": "sentinel-writer-model"})

    assert resolved["writer_model"] == "sentinel-writer-model"
    assert resolved["judge_model"] == QUALIFIED_REFINEMENT_MODEL


def test_tailoring_rewrite_model_still_beats_the_writer_specific_override():
    resolved = _resolve_config(
        {
            "TAILORING_REWRITE_MODEL": "sentinel-highest-writer-model",
            "PATCH_REFINEMENT_WRITER_MODEL": "sentinel-writer-model",
        }
    )

    assert resolved["writer_model"] == "sentinel-highest-writer-model"


def test_shared_patch_refinement_env_still_flows_into_the_writer():
    resolved = _resolve_config({"PATCH_REFINEMENT_MODEL": "sentinel-shared-model"})

    assert resolved["writer_model"] == "sentinel-shared-model"
    # The judge chain is independent of the shared patch-refinement model.
    assert resolved["judge_model"] == QUALIFIED_REFINEMENT_MODEL


# --- D. judge precedence unchanged -----------------------------------------


def test_judge_specific_override_still_wins_over_the_default():
    resolved = _resolve_config({"PATCH_REFINEMENT_JUDGE_MODEL": "sentinel-judge-model"})

    assert resolved["judge_model"] == "sentinel-judge-model"
    assert resolved["writer_model"] == QUALIFIED_REFINEMENT_MODEL


def test_tailoring_judge_model_still_has_highest_judge_precedence():
    resolved = _resolve_config(
        {
            "TAILORING_JUDGE_MODEL": "sentinel-highest-judge-model",
            "PATCH_REFINEMENT_JUDGE_MODEL": "sentinel-judge-model",
        }
    )

    assert resolved["judge_model"] == "sentinel-highest-judge-model"


def test_provider_overrides_still_apply_to_writer_and_judge():
    resolved = _resolve_config(
        {
            "TAILORING_REWRITE_PROVIDER": "openai",
            "TAILORING_JUDGE_PROVIDER": "openai",
        }
    )

    assert resolved["writer_provider"] == "openai"
    assert resolved["judge_provider"] == "openai"


# --- E. Bulk Generate child environment does not inject a model -------------

_CHILD_ENV_SNIPPET = _DOTENV_STUB + """
import json, os, sys
sys.path.insert(0, {repo!r})
from src.app import services
os.environ["PATCH_REFINEMENT_WRITER_MODEL"] = "sentinel-parent-writer"
os.environ["PATCH_REFINEMENT_JUDGE_MODEL"] = "sentinel-parent-judge"
child = services._pipeline_child_env(extra_env={{"JOB_STACK_OWNER_USER_ID": "contract-owner"}})
print("@@RESULT@@" + json.dumps({{
    "patch_refinement_prefix_allowlisted": "PATCH_REFINEMENT_" in services._PIPELINE_CHILD_ENV_PREFIXES,
    "writer_forwarded_verbatim": child.get("PATCH_REFINEMENT_WRITER_MODEL"),
    "judge_forwarded_verbatim": child.get("PATCH_REFINEMENT_JUDGE_MODEL"),
}}))
"""


def test_bulk_generate_child_env_forwards_but_never_injects_a_writer_judge_model():
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in WRITER_JUDGE_ENV_NAMES
    }
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")

    completed = subprocess.run(
        [sys.executable, "-c", _CHILD_ENV_SNIPPET.format(repo=str(REPO_ROOT))],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        pytest.fail(f"child-env probe failed:\nstderr={completed.stderr[-2000:]}")

    marker = [
        line for line in completed.stdout.splitlines() if line.startswith("@@RESULT@@")
    ]
    assert marker, f"probe produced no result line: {completed.stdout[-2000:]}"
    result = json.loads(marker[-1][len("@@RESULT@@") :])

    # Forwarding contract is preserved: PATCH_REFINEMENT_* is an allowlist prefix.
    assert result["patch_refinement_prefix_allowlisted"] is True
    # Bulk Generate forwards the parent value verbatim and never substitutes a model
    # of its own, so it cannot pin the writer/judge to the legacy Llama model.
    assert result["writer_forwarded_verbatim"] == "sentinel-parent-writer"
    assert result["judge_forwarded_verbatim"] == "sentinel-parent-judge"

    # And no Bulk/pipeline code path injects a writer/judge model into the child env.
    services_source = (REPO_ROOT / "src" / "app" / "services.py").read_text(encoding="utf-8")
    for key in ("PATCH_REFINEMENT_WRITER_MODEL", "PATCH_REFINEMENT_JUDGE_MODEL"):
        assert f'child_env["{key}"]' not in services_source
        assert f'"{key}":' not in services_source


# --- F. frozen request settings ---------------------------------------------


def test_writer_and_judge_request_settings_are_unchanged():
    from src.tailoring import llm

    assert llm.PATCH_REFINEMENT_WRITER_MAX_TOKENS == 420
    assert llm.PATCH_REFINEMENT_JUDGE_MAX_TOKENS == 500
    assert llm.PATCH_REFINEMENT_WRITER_TEMPERATURE == 0
    assert llm.PATCH_REFINEMENT_JUDGE_TEMPERATURE == 0
    assert llm.PATCH_REFINEMENT_WRITER_PROMPT_VERSION == "v2"
    assert llm.PATCH_REFINEMENT_JUDGE_PROMPT_VERSION == "v1"
    assert llm.PATCH_REFINEMENT_VALIDATION_CONTRACT_VERSION == "patch-refinement-validation-v1"
    assert (
        llm.PATCH_REFINEMENT_JUDGE_DECISION_CONTRACT_VERSION
        == "patch-refinement-judge-decision-v1"
    )


def test_packet_level_generation_model_is_untouched_by_the_refinement_defaults():
    """Stage-1 packet generation keeps its own configuration chain."""

    source = (REPO_ROOT / "src" / "tailoring" / "llm.py").read_text(encoding="utf-8")

    # The stage-1 chain is defined independently of the refinement chain.
    assert 'os.getenv("LLM_TAILOR_MODEL", "llama-3.3-70b-versatile")' in source
    # Refinement writer/judge no longer default to the legacy model.
    assert 'os.getenv("PATCH_REFINEMENT_JUDGE_MODEL", "openai/gpt-oss-120b")' in source


# --- G. deterministic tailoring is unaffected -------------------------------


def test_deterministic_rendering_never_consumes_the_refinement_model_defaults():
    """Deterministic patch construction must not depend on writer/judge model config."""

    rendering_source = (
        REPO_ROOT / "src" / "tailoring" / "rendering.py"
    ).read_text(encoding="utf-8")

    for symbol in (
        "PATCH_REFINEMENT_MODEL",
        "PATCH_REFINEMENT_WRITER_MODEL",
        "PATCH_REFINEMENT_JUDGE_MODEL",
    ):
        assert symbol not in rendering_source


def test_deterministic_patch_dispatcher_is_unchanged():
    from src.tailoring import rendering

    diagnosis = {
        "original_text": "Built ARIMA-based seasonal forecasting models on 250k+ records, improving forecast accuracy by 12%",
        "jd_signal_terms": ["forecasting"],
        "claim_safety": "safe_strengthen",
        "priority": "high",
        "likely_impacted_dimensions": ["required_skills_alignment"],
    }

    status, patch_text, method, reason = rendering._deterministic_patch_text_from_diagnosis(
        diagnosis, [], []
    )

    assert status == "patch_ready"
    assert method == "deterministic_based_modifier_head"
    assert reason == ""
    assert patch_text.startswith("Built seasonal forecasting models on 250k+ records using ARIMA")

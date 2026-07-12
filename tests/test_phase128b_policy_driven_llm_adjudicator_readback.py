from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

from src.agents.llm_adjudicator_readback import (
    build_policy_driven_llm_adjudicator_readback,
    llm_adjudicator_provider_configured,
    resolve_llm_adjudicator_readback_mode,
    should_run_llm_adjudicator_readback,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "src/agents/llm_adjudicator_readback.py"
SELECTOR = ROOT / "batch_select_best_resume_variant.py"


def _candidate(
    name: str,
    score: float,
    *,
    semantic_score: float | None = None,
    viable: bool = True,
    diagnostics: list[dict] | None = None,
) -> dict:
    return {
        "resume_name": name,
        "final_score": score,
        "match_bucket": "solid",
        "semantic_alignment": (
            {"score": semantic_score, "weight": 0.05}
            if semantic_score is not None
            else {}
        ),
        "hard_requirement_diagnostics": diagnostics or [],
        "prefilter_passed": viable,
    }


def test_mode_defaults_to_auto_and_legacy_gate_remains_compatible():
    assert resolve_llm_adjudicator_readback_mode({}) == "auto"
    assert resolve_llm_adjudicator_readback_mode(
        {"APPLYLENS_LLM_ADJUDICATOR_READBACK_MODE": "off"}
    ) == "off"
    assert resolve_llm_adjudicator_readback_mode(
        {"APPLYLENS_LLM_ADJUDICATOR_READBACK_MODE": "auto"}
    ) == "auto"
    assert resolve_llm_adjudicator_readback_mode(
        {"APPLYLENS_LLM_ADJUDICATOR_READBACK_MODE": "always"}
    ) == "always"
    assert resolve_llm_adjudicator_readback_mode(
        {"APPLYLENS_LLM_ADJUDICATOR_READBACK_MODE": "sometimes"}
    ) == "invalid"
    assert resolve_llm_adjudicator_readback_mode(
        {"APPLYLENS_LLM_ADJUDICATOR_READBACK_ENABLED": "true"}
    ) == "always"
    assert resolve_llm_adjudicator_readback_mode(
        {"APPLYLENS_LLM_ADJUDICATOR_READBACK_ENABLED": "false"}
    ) == "off"


def test_explicit_mode_takes_precedence_over_legacy_gate():
    assert resolve_llm_adjudicator_readback_mode(
        {
            "APPLYLENS_LLM_ADJUDICATOR_READBACK_MODE": "auto",
            "APPLYLENS_LLM_ADJUDICATOR_READBACK_ENABLED": "false",
        }
    ) == "auto"


def test_auto_calls_fake_provider_for_close_gap():
    calls = []
    candidates = [_candidate("AI2.pdf", 0.80), _candidate("AI1.pdf", 0.76)]
    readback = build_policy_driven_llm_adjudicator_readback(
        candidates=candidates,
        provider="groq",
        model="test-model",
        mode="auto",
        provider_callable=lambda payload: calls.append(payload) or {
            "adjudicator_summary": "Candidates are close.",
            "adjudicator_recommendation_label": "Review AI2 first",
        },
        environ={},
    )

    assert len(calls) == 1
    assert readback["status"] == "ok"
    assert readback["enabled"] is True
    assert readback["policy_mode"] == "auto"
    assert readback["policy_eligible"] is True
    assert readback["policy_reason"] == "close_score_gap"
    assert readback["provider_configured"] is True
    assert readback["provider_call_attempted"] is True


def test_auto_skips_clear_winner_without_provider_call():
    calls = []
    readback = build_policy_driven_llm_adjudicator_readback(
        candidates=[_candidate("AI2.pdf", 0.86), _candidate("AI1.pdf", 0.70)],
        provider="groq",
        model="test-model",
        mode="auto",
        provider_callable=lambda payload: calls.append(payload),
        environ={},
    )

    assert calls == []
    assert readback["status"] == "skipped_clear_winner"
    assert readback["enabled"] is False
    assert readback["policy_eligible"] is False
    assert readback["policy_reason"] == "clear_deterministic_winner"
    assert readback["provider_call_attempted"] is False


def test_auto_runs_for_borderline_close_candidates():
    should_run, reason = should_run_llm_adjudicator_readback(
        ranked_candidates=[_candidate("A.pdf", 0.58), _candidate("B.pdf", 0.50)],
        mode="auto",
        provider_configured=True,
    )

    assert should_run is True
    assert reason == "borderline_close_candidates"


def test_auto_runs_for_semantic_deterministic_disagreement():
    should_run, reason = should_run_llm_adjudicator_readback(
        ranked_candidates=[
            _candidate("A.pdf", 0.82, semantic_score=0.60),
            _candidate("B.pdf", 0.68, semantic_score=0.82),
        ],
        mode="auto",
        provider_configured=True,
    )

    assert should_run is True
    assert reason == "semantic_deterministic_disagreement"


def test_auto_accepts_hard_requirement_diagnostics_structurally():
    should_run, reason = should_run_llm_adjudicator_readback(
        ranked_candidates=[
            _candidate(
                "A.pdf",
                0.82,
                diagnostics=[{"code": "future_hard_requirement"}],
            ),
            _candidate("B.pdf", 0.68),
        ],
        mode="auto",
        provider_configured=True,
    )

    assert should_run is True
    assert reason == "hard_requirement_diagnostic"


def test_auto_skips_fewer_than_two_viable_candidates():
    for candidates in (
        [],
        [_candidate("A.pdf", 0.70)],
        [_candidate("A.pdf", 0.70), _candidate("B.pdf", 0.69, viable=False)],
    ):
        should_run, reason = should_run_llm_adjudicator_readback(
            ranked_candidates=candidates,
            mode="auto",
            provider_configured=True,
        )
        assert should_run is False
        assert reason == "insufficient_candidates"


def test_off_invalid_and_missing_provider_fail_closed_without_calls():
    candidates = [_candidate("A.pdf", 0.80), _candidate("B.pdf", 0.79)]
    for mode, expected_status in (
        ("off", "disabled"),
        ("sometimes", "skipped_invalid_mode"),
    ):
        calls = []
        readback = build_policy_driven_llm_adjudicator_readback(
            candidates=candidates,
            provider="groq",
            model="test-model",
            mode=mode,
            provider_callable=lambda payload: calls.append(payload),
            environ={},
        )
        assert calls == []
        assert readback["status"] == expected_status
        assert readback["enabled"] is False

    readback = build_policy_driven_llm_adjudicator_readback(
        candidates=candidates,
        provider="groq",
        model="test-model",
        mode="auto",
        environ={},
    )
    assert readback["status"] == "skipped_provider_not_configured"
    assert readback["provider_call_attempted"] is False


def test_provider_preflight_requires_supported_provider_model_and_key():
    assert llm_adjudicator_provider_configured(
        provider="groq", model="model", environ={"GROQ_API_KEY": "key"}
    ) is True
    assert llm_adjudicator_provider_configured(
        provider="openai", model="model", environ={"OPENAI_API_KEY": "key"}
    ) is True
    assert llm_adjudicator_provider_configured(
        provider="gemini", model="model", environ={"GEMINI_API_KEY": "key"}
    ) is True
    assert llm_adjudicator_provider_configured(
        provider="groq", model="model", environ={}
    ) is False
    assert llm_adjudicator_provider_configured(
        provider="unknown", model="model", environ={"UNKNOWN_API_KEY": "key"}
    ) is False
    assert llm_adjudicator_provider_configured(
        provider="", model="", provider_callable=lambda payload: payload, environ={}
    ) is True


def test_always_runs_and_provider_failures_remain_non_blocking():
    candidates = [_candidate("A.pdf", 0.90), _candidate("B.pdf", 0.50)]
    calls = []
    readback = build_policy_driven_llm_adjudicator_readback(
        candidates=candidates,
        provider="groq",
        model="test-model",
        mode="always",
        provider_callable=lambda payload: calls.append(payload) or (_ for _ in ()).throw(
            RuntimeError("provider unavailable")
        ),
        environ={},
    )

    assert len(calls) == 1
    assert readback["status"] == "provider_error"
    assert readback["policy_reason"] == "forced_always"
    assert readback["provider_call_attempted"] is True
    assert readback["no_winner_override"] is True
    assert readback["no_score_override"] is True
    assert readback["no_queue_mutation"] is True


def test_malformed_provider_output_is_safe_and_inputs_are_not_mutated():
    candidates = [_candidate("A.pdf", 0.75), _candidate("B.pdf", 0.73)]
    original = deepcopy(candidates)
    readback = build_policy_driven_llm_adjudicator_readback(
        candidates=candidates,
        provider="groq",
        model="test-model",
        mode="auto",
        provider_callable=lambda payload: "not-json",
        environ={},
    )

    assert readback["status"] == "malformed_response"
    assert candidates == original
    assert "winner_resume" not in readback
    assert "runner_up_resume" not in readback
    assert "resolved_resume" not in readback
    assert "final_score" not in readback
    assert "action" not in readback


def test_selector_uses_policy_builder_after_deterministic_projection():
    source = SELECTOR.read_text(encoding="utf-8")

    projection_index = source.index("resolved_selection = _resolved_selection_projection(")
    policy_index = source.index("build_policy_driven_llm_adjudicator_readback(")
    output_index = source.index("output_row = {", policy_index)
    assert projection_index < policy_index < output_index
    assert "llm_adjudicator_candidates" in source[projection_index:policy_index]
    for field in (
        "llm_adjudicator_readback_enabled",
        "llm_adjudicator_readback_status",
        "llm_adjudicator_readback",
    ):
        assert field in source


def test_changed_helper_has_no_direct_sdk_rag_or_runtime_mutation_imports():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    forbidden = (
        "groq",
        "openai",
        "google.genai",
        "src.rag",
        "src.app",
        "src.pipeline",
        "src.tailoring",
    )
    assert not {
        module
        for module in imports
        if any(module == root or module.startswith(f"{root}.") for root in forbidden)
    }
    assert "src/matching/scorer.py" not in SELECTOR.read_text(encoding="utf-8")
    assert (ROOT / "requirements.txt").read_text(encoding="utf-8").count("groq") == 1

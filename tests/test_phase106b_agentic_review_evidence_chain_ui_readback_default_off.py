# phase106b legacy guard marker: changes_only evidence_chain_ui_readback
from __future__ import annotations

from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTIC_REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"

PROTECTED_BACKEND_HASHES = {
    "src/app/api.py": "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
    "src/app/services.py": "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
    "src/pipeline/collector.py": "e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671",
    "src/ai/llm_client.py": "b97f54b85d18386479f284a99d65bfdd663f25b5e076e1c3bd18fb839af22eca",
    "src/ai/job_fit_evaluator.py": "3776e5ce3c098c5329d2e7631195915f6bcf098ec0303ec619e9b0e9ecf393fb",
    "src/storage/agent_trace/schema.sql": "69305cd1bec0be9caa8c8c1b93e8fc10a3e80a92c08acd5683e7800763d2a77a",
}


def _source() -> str:
    return AGENTIC_REVIEW_JS_PATH.read_text(encoding="utf-8")


def _function_snippet(name: str) -> str:
    source = _source()
    start = source.index(f"function {name}") if f"function {name}" in source else source.index(f"async function {name}")
    signature_end = source.index(")", start)
    brace = source.index("{", signature_end)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Could not extract function {name}")


def test_phase106b_fetches_evidence_chain_readback_with_get_only():
    source = _source()
    fetch_snippet = _function_snippet("fetchEvidenceChainTraceReadbackPayload")

    assert "/profile/pipeline-runs/${encodeURIComponent(safeRunId)}/evidence-chain-trace" in fetch_snippet
    assert "/evidence-chain-trace" in source
    assert "fetchJson(`/profile/pipeline-runs/${encodeURIComponent(safeRunId)}/evidence-chain-trace`)" in fetch_snippet
    for forbidden in ['method: "POST"', "method: 'POST'", 'method: "PUT"', 'method: "PATCH"', 'method: "DELETE"']:
        assert forbidden not in fetch_snippet


def test_phase106b_evidence_chain_card_renders_compact_readback_fields():
    source = _source()
    card = _function_snippet("renderEvidenceChainReadbackCard")
    panel = _function_snippet("renderAgentTraceReadOnlyPanel")

    assert "Evidence Chain" in card
    assert "renderEvidenceChainReadbackCard(tracePayload)" in panel
    for marker in [
        "found",
        "run_count",
        "step_count",
        "latest_run",
        "agent_run_id",
        "per_agent_status",
        "warnings",
        "warning_count",
        "chain_readiness",
        "chain_status",
    ]:
        assert marker in card
    assert "evidence_chain_trace_readback" in source
    assert "evidence_chain_trace_loading" in source


def test_phase106b_expected_agent_labels_are_visible():
    source = _source()

    for label in [
        "JD Intelligence",
        "Resume Match",
        "Critic",
        "Job Prioritization",
        "Tailoring Decision",
        "Operator Review",
    ]:
        assert label in source
    for key in [
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
    ]:
        assert key in source


def test_phase106b_loading_empty_error_and_no_run_id_states_fail_closed():
    source = _source()
    card = _function_snippet("renderEvidenceChainReadbackCard")
    fetch_snippet = _function_snippet("fetchEvidenceChainTraceReadbackPayload")
    init_snippet = _function_snippet("initAgenticReviewPage")

    for marker in [
        "loading",
        "unavailable",
        "not found",
        "No persisted Evidence Chain trace found",
        "malformed payload",
        "no run id",
        "read_only_error",
        "Evidence Chain readback could not be loaded",
        "evidence_chain_readback_unavailable",
    ]:
        assert marker in source
    assert "no_run_id" in fetch_snippet
    assert "evidence_chain_trace_loading: true" in init_snippet
    assert "renderEvidenceChainAgentStatusRows(perAgentStatus)" in card


def test_phase106b_safety_copy_is_visible_and_specific():
    card = _function_snippet("renderEvidenceChainReadbackCard")

    for marker in [
        "Read-only evidence readback",
        "No provider/LLM call from this panel",
        "No collector execution",
        "No scoring/ranking/queue mutation",
        "No auto-apply or ATS submission",
        "Human applies manually",
    ]:
        assert marker in card


def test_phase106b_does_not_change_protected_backend_runtime_files():
    for path, expected_hash in PROTECTED_BACKEND_HASHES.items():
        full_path = ROOT / path
        assert full_path.exists(), path
        assert sha256(full_path.read_bytes()).hexdigest() == expected_hash, path


def test_phase106b_manual_critic_guardrail_remains_manual_click_only():
    source = _source()
    init_snippet = _function_snippet("initAgenticReviewPage")

    assert "/api/manual-critic-guardrail-dry-run" in source
    assert "data-manual-critic-guardrail-dry-run" in source
    assert "/api/manual-critic-guardrail-dry-run" not in init_snippet
    assert "data-manual-critic-guardrail-dry-run" not in init_snippet
    assert "event.target.closest(\"[data-manual-critic-guardrail-dry-run]\")" in source
    assert ".click()" not in init_snippet

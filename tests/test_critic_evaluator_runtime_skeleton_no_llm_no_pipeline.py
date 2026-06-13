from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from src.agents.critic_evaluator import (
    CRITIC_EVALUATOR_RUBRIC_VERSION,
    build_empty_evaluator_result,
    evaluate_agent_trace,
)


MODULE_PATH = Path("src/agents/critic_evaluator.py")

STEP_200_ALLOWED_FILES = [
    "src/agents/critic_evaluator.py",
    "tests/test_critic_evaluator_runtime_skeleton_no_llm_no_pipeline.py",
    "docs/critic_evaluator_runtime_skeleton_no_llm_no_pipeline.md",
    "docs/orchestrator_readiness.md",
    "README.md",
    "tests/test_agentic_docs.py",
]


def _valid_step(index: int) -> dict:
    return {
        "agent_step_id": f"step-{index}",
        "step_index": index,
        "safety_metadata": {
            "read_only": True,
            "did_mutate": False,
        },
        "output_summary": {
            "validation_json": {
                "is_valid": True,
                "errors": [],
            },
            "separation": {
                "prefilter_relevance": "separate",
                "llm_evaluation": "not_called",
                "final_application_scoring": "separate",
            },
        },
    }


def _valid_trace() -> dict:
    return {"agent_steps": [_valid_step(1), _valid_step(2)]}


def test_empty_evaluator_result_has_required_contract():
    result = build_empty_evaluator_result()

    assert result == {
        "evaluator_status": "not_evaluated",
        "evaluator_findings": [],
        "evaluator_warnings": [],
        "evaluator_recommendations": [],
        "requires_human_review": False,
        "deterministic_rubric_version": CRITIC_EVALUATOR_RUBRIC_VERSION,
    }


def test_evaluator_returns_required_output_contract():
    result = evaluate_agent_trace(_valid_trace())

    assert set(result) == {
        "evaluator_status",
        "evaluator_findings",
        "evaluator_warnings",
        "evaluator_recommendations",
        "requires_human_review",
        "deterministic_rubric_version",
    }
    assert result["deterministic_rubric_version"] == CRITIC_EVALUATOR_RUBRIC_VERSION


def test_evaluator_is_deterministic_for_identical_input():
    trace = _valid_trace()

    assert evaluate_agent_trace(trace) == evaluate_agent_trace(deepcopy(trace))


def test_evaluator_does_not_mutate_input():
    trace = _valid_trace()
    before = deepcopy(trace)

    evaluate_agent_trace(trace)

    assert trace == before


def test_empty_trace_requires_human_review():
    result = evaluate_agent_trace({"agent_steps": []})

    assert result["evaluator_status"] == "needs_human_review"
    assert result["requires_human_review"] is True
    assert "trace_completeness_empty_trace" in result["evaluator_findings"]


def test_missing_safety_metadata_creates_warning_and_finding():
    trace = {"agent_steps": [_valid_step(1)]}
    del trace["agent_steps"][0]["safety_metadata"]

    result = evaluate_agent_trace(trace)

    assert "safety_metadata_missing" in result["evaluator_findings"]
    assert "one_or_more_steps_missing_safety_metadata" in result["evaluator_warnings"]
    assert result["requires_human_review"] is True


def test_invalid_or_missing_validation_json_creates_warning_and_finding():
    invalid_trace = {"agent_steps": [_valid_step(1)]}
    invalid_trace["agent_steps"][0]["output_summary"]["validation_json"] = {
        "is_valid": False,
        "errors": ["invalid"],
    }
    missing_trace = {"agent_steps": [_valid_step(1)]}
    del missing_trace["agent_steps"][0]["output_summary"]["validation_json"]

    invalid_result = evaluate_agent_trace(invalid_trace)
    missing_result = evaluate_agent_trace(missing_trace)

    assert "validation_json_invalid" in invalid_result["evaluator_findings"]
    assert "one_or_more_steps_have_invalid_validation_json" in invalid_result[
        "evaluator_warnings"
    ]
    assert "validation_json_missing" in missing_result["evaluator_findings"]
    assert "one_or_more_steps_missing_validation_json" in missing_result[
        "evaluator_warnings"
    ]


def test_ordered_trace_passes_ordering_check():
    result = evaluate_agent_trace(_valid_trace())

    assert result["evaluator_status"] == "passed"
    assert result["requires_human_review"] is False
    assert result["evaluator_findings"] == []
    assert result["evaluator_warnings"] == []


def test_out_of_order_trace_creates_warning_and_finding():
    result = evaluate_agent_trace({"agent_steps": [_valid_step(2), _valid_step(1)]})

    assert "agent_step_ordering_out_of_order" in result["evaluator_findings"]
    assert "agent_steps_are_not_sorted" in result["evaluator_warnings"]
    assert result["requires_human_review"] is True


def test_no_provider_network_storage_process_or_runtime_wiring_markers():
    source = MODULE_PATH.read_text()
    forbidden_markers = [
        "openai",
        "anthropic",
        "langchain",
        "langgraph",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "threading",
        "multiprocessing",
        "psycopg",
        "sqlalchemy",
        "sqlite3",
        "boto3",
        "FileResponse",
        "StreamingResponse",
        "background_tasks",
        "execute_callback",
        "cursor.execute",
    ]

    for marker in forbidden_markers:
        assert marker not in source


def test_step_200_allowed_files_are_scoped():
    for path in STEP_200_ALLOWED_FILES:
        assert Path(path).exists(), path

    forbidden_prefixes = (
        "src/app/",
        "src/storage/",
        "src/pipeline/",
        "application_execution_queue.py",
        "run_application_planning.py",
        "migrations/",
    )
    for path in STEP_200_ALLOWED_FILES:
        assert not path.startswith(forbidden_prefixes)

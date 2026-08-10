from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import socket
import stat

import pytest

from src.evaluation import controlled_provider_benchmark_evidence_runtime as runtime
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT
    / "src/evaluation/controlled_provider_benchmark_evidence_runtime.py"
)
FIXED_TIME = "2026-07-25T00:00:00Z"
EXPECTED_MODEL_COUNTS = {
    "groq/openai/gpt-oss-20b": 12,
    "groq/openai/gpt-oss-120b": 10,
    "openai/gpt-5-mini": 12,
    "openai/gpt-5.1": 10,
}


@pytest.fixture(scope="module")
def controlled_inputs():
    plan = build_controlled_provider_benchmark_plan()
    pricing = harness.load_synthetic_pricing_fixture()
    authorization = harness.load_synthetic_authorization_fixture(
        plan=plan,
        pricing=pricing,
    )
    corpus = load_fixture_case_corpus()
    outputs = {
        review["case_alias"]: deepcopy(case["expected_output"])
        for review, case in zip(plan["transmission_review"], corpus["cases"])
        if review["eligible_for_later_controlled_transmission"]
    }
    return plan, authorization, pricing, outputs


class GoldenTransport:
    def __init__(self, outputs, *, input_tokens=11, output_tokens=7, latency=5.0):
        self.outputs = deepcopy(outputs)
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.latency = latency
        self.calls = []

    def __call__(self, packet, timeout_seconds):
        self.calls.append((deepcopy(packet), timeout_seconds))
        return {
            "normalized_output": deepcopy(self.outputs[packet["case_alias"]]),
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": self.latency,
            "input_token_count": self.input_tokens,
            "output_token_count": self.output_tokens,
            "provider_outcome_category": "success",
        }


@pytest.fixture(scope="module")
def completed_evidence(controlled_inputs):
    plan, authorization, pricing, outputs = controlled_inputs
    transport = GoldenTransport(outputs)
    evidence = runtime.execute_provider_neutral_evidence_run(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        transport=transport,
        execution_time_source=lambda: FIXED_TIME,
    )
    return evidence, transport


def _execute(
    controlled_inputs,
    transport,
    *,
    maximum_schedule_items=1,
    plan=None,
    authorization=None,
    pricing=None,
    prior_checkpoint=None,
):
    base_plan, base_authorization, base_pricing, _outputs = controlled_inputs
    return runtime.execute_provider_neutral_evidence_run(
        plan=base_plan if plan is None else plan,
        authorization=(
            base_authorization if authorization is None else authorization
        ),
        pricing=base_pricing if pricing is None else pricing,
        transport=transport,
        execution_time_source=lambda: FIXED_TIME,
        prior_checkpoint=prior_checkpoint,
        maximum_schedule_items=maximum_schedule_items,
    )


def _iter_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def test_runtime_owner_is_provider_neutral_and_constructs_no_sdk_client():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "controlled_groq" not in source
    assert "controlled_openai" not in source
    assert '"groq"' not in source
    assert '"openai"' not in source
    assert "Groq" not in source
    assert "OpenAI" not in source
    assert "user_provider_runtime" not in source
    assert "user_ai_settings" not in source
    assert "OPENAI_API_KEY" not in source
    assert "GROQ_API_KEY" not in source
    assert "getenv" not in source
    assert not any(
        isinstance(node, ast.Attribute) and node.attr in {"getenv", "environ"}
        for node in ast.walk(tree)
    )
    assert not {"groq", "openai", "dotenv"}.intersection(imports)


def test_transport_result_contract_is_reused_not_redefined(completed_evidence):
    evidence, _transport = completed_evidence

    assert evidence["transport_result_fields"] == sorted(
        harness.TRANSPORT_RESULT_FIELDS
    )
    assert evidence["harness_version"] == harness.HARNESS_VERSION


def test_complete_run_accepts_groq_and_openai_through_one_evidence_path(
    completed_evidence,
):
    evidence, transport = completed_evidence
    summaries = evidence["grading_summaries"]

    assert len(transport.calls) == 44
    assert evidence["execution_status"] == "completed"
    assert evidence["state_counts"] == {
        "completed": 44,
        "blocked": 0,
        "ambiguous": 0,
        "pending": 0,
    }
    assert {row["provider"] for row in summaries} == {"groq", "openai"}
    assert len(summaries) == 44
    assert all(row["quality_gate_passed"] for row in summaries)
    assert evidence["all_executed_quality_gates_passed"] is True


def test_exact_usage_latency_and_call_aggregates_are_preserved(
    completed_evidence,
):
    evidence, _transport = completed_evidence
    aggregate = evidence["aggregate_usage"]

    assert aggregate["transport_calls"] == 44
    assert aggregate["input_tokens"] == 44 * 11
    assert aggregate["output_tokens"] == 44 * 7
    assert aggregate["latency_ms"] == 44 * 5.0
    assert aggregate["by_provider"] == {"groq": 22, "openai": 22}
    assert aggregate["by_model"] == EXPECTED_MODEL_COUNTS
    assert evidence["authority_invariants"]["mutation_count"] == 0
    assert evidence["checkpoint"]["authority_invariants"] == {
        "provider_call_count": 44,
        "fallback_activation_count": 0,
        "retry_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "raw_response_persisted_count": 0,
        "production_activation": False,
        "winner_selected": False,
    }


def test_execution_time_source_is_injected_once_and_normalized(controlled_inputs):
    _plan, _authorization, _pricing, outputs = controlled_inputs
    calls = []

    def fixed_time():
        calls.append(True)
        return "2026-07-24T20:00:00-04:00"

    transport = GoldenTransport(outputs)
    plan, authorization, pricing, _ = controlled_inputs
    evidence = runtime.execute_provider_neutral_evidence_run(
        plan=plan,
        authorization=authorization,
        pricing=pricing,
        transport=transport,
        execution_time_source=fixed_time,
        maximum_schedule_items=1,
    )

    assert calls == [True]
    assert evidence["execution_at_utc"] == "2026-07-25T00:00:00.000000Z"


@pytest.mark.parametrize("value", [None, "", "not-a-time", "2026-07-25"])
def test_invalid_execution_time_fails_before_transport(controlled_inputs, value):
    _plan, _authorization, _pricing, outputs = controlled_inputs
    transport = GoldenTransport(outputs)

    with pytest.raises(ValueError, match="execution time"):
        runtime.execute_provider_neutral_evidence_run(
            plan=controlled_inputs[0],
            authorization=controlled_inputs[1],
            pricing=controlled_inputs[2],
            transport=transport,
            execution_time_source=lambda: value,
            maximum_schedule_items=1,
        )
    assert transport.calls == []


def test_exactly_one_injected_call_per_executed_row_and_no_retry_or_fallback(
    controlled_inputs,
):
    transport = GoldenTransport(controlled_inputs[3])
    evidence = _execute(
        controlled_inputs,
        transport,
        maximum_schedule_items=3,
    )

    assert len(transport.calls) == 3
    assert evidence["aggregate_usage"]["transport_calls"] == 3
    assert all(timeout == 30 for _packet, timeout in transport.calls)
    assert all(packet["fallback"] is False for packet, _ in transport.calls)
    assert evidence["checkpoint"]["authority_invariants"]["retry_count"] == 0
    assert evidence["checkpoint"]["authority_invariants"][
        "fallback_activation_count"
    ] == 0


@pytest.mark.parametrize(
    "mutation",
    [
        lambda plan: plan["staged_matrix"][0].update({"provider": "gemini"}),
        lambda plan: plan["staged_matrix"][0].update({"model": "unknown"}),
        lambda plan: plan["staged_matrix"][0].update(
            {"model": "openai/gpt-oss-120b"}
        ),
        lambda plan: plan["staged_matrix"][0].update(
            {
                "case_alias": next(
                    row["case_alias"]
                    for row in plan["transmission_review"]
                    if not row["eligible_for_later_controlled_transmission"]
                )
            }
        ),
        lambda plan: plan.update({"step8o_case_corpus_sha256": "0" * 64}),
        lambda plan: plan.update({"model_catalog_snapshot_sha256": "0" * 64}),
    ],
)
def test_invalid_plan_scope_fails_closed_before_transport(
    controlled_inputs,
    mutation,
):
    plan = deepcopy(controlled_inputs[0])
    mutation(plan)
    transport = GoldenTransport(controlled_inputs[3])

    with pytest.raises(ValueError):
        _execute(controlled_inputs, transport, plan=plan)
    assert transport.calls == []


def test_authorization_plan_binding_mismatch_fails_before_transport(
    controlled_inputs,
):
    authorization = deepcopy(controlled_inputs[1])
    authorization["benchmark_plan_sha256"] = "0" * 64
    transport = GoldenTransport(controlled_inputs[3])

    with pytest.raises(ValueError, match="plan hash"):
        _execute(
            controlled_inputs,
            transport,
            authorization=authorization,
        )
    assert transport.calls == []


def test_pricing_binding_mismatch_fails_before_transport(controlled_inputs):
    pricing = deepcopy(controlled_inputs[2])
    pricing["pricing_table_sha256"] = "0" * 64
    transport = GoldenTransport(controlled_inputs[3])

    with pytest.raises(ValueError, match="hash mismatch"):
        _execute(controlled_inputs, transport, pricing=pricing)
    assert transport.calls == []


def test_schema_invalid_output_is_graded_and_hard_stops(controlled_inputs):
    calls = []

    def invalid_schema(packet, timeout):
        calls.append((packet, timeout))
        return {
            "normalized_output": {"required_skills": ["python"]},
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 1,
            "input_token_count": 3,
            "output_token_count": 2,
            "provider_outcome_category": "success",
        }

    evidence = _execute(controlled_inputs, invalid_schema)
    summary = evidence["grading_summaries"][0]

    assert len(calls) == 1
    assert evidence["execution_status"] == "stopped"
    assert evidence["checkpoint"]["stop_reason"] == "hard_safety_failure"
    assert summary["schema_valid"] is False
    assert summary["quality_gate_passed"] is False
    assert evidence["hard_failure_present"] is True


def test_normalization_failure_stops_without_fabricating_grade(controlled_inputs):
    calls = []

    def invalid_normalization(packet, timeout):
        calls.append((packet, timeout))
        return {
            "normalized_output": "not-an-object",
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 1,
            "input_token_count": 3,
            "output_token_count": 2,
            "provider_outcome_category": "success",
        }

    evidence = _execute(controlled_inputs, invalid_normalization)

    assert len(calls) == 1
    assert evidence["checkpoint"]["stop_reason"] == "unknown_provider_outcome"
    assert evidence["grading_summaries"] == []
    assert evidence["hard_failure_present"] is True


def test_workload_quality_failure_is_retained_and_stops_later_rows(
    controlled_inputs,
):
    calls = []

    def poor_quality(packet, timeout):
        calls.append((packet, timeout))
        return {
            "normalized_output": {
                "required_skills": ["synthetic-unsupported-skill"],
                "preferred_skills": ["synthetic-unsupported-preference"],
            },
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 1,
            "input_token_count": 3,
            "output_token_count": 2,
            "provider_outcome_category": "success",
        }

    evidence = _execute(
        controlled_inputs,
        poor_quality,
        maximum_schedule_items=4,
    )

    assert len(calls) == 1
    assert evidence["checkpoint"]["stop_reason"] == "hard_safety_failure"
    assert evidence["grading_summaries"][0]["quality_gate_passed"] is False
    assert any(evidence["grading_summaries"][0]["hard_failures"].values())
    assert evidence["state_counts"]["pending"] == 43


@pytest.mark.parametrize(
    ("outcome", "stop_reason"),
    [
        ("fallback_attempt", "fallback_attempted"),
        ("retry_attempt", "retry_attempted"),
        ("raw_response_persistence", "raw_response_persistence"),
        ("unknown_provider_outcome", "unknown_provider_outcome"),
    ],
)
def test_bounded_transport_failure_outcome_hard_stops_once(
    controlled_inputs,
    outcome,
    stop_reason,
):
    calls = []

    def failing(packet, timeout):
        calls.append((packet, timeout))
        return {
            "normalized_output": {},
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 1,
            "input_token_count": 1,
            "output_token_count": 1,
            "provider_outcome_category": outcome,
        }

    evidence = _execute(
        controlled_inputs,
        failing,
        maximum_schedule_items=4,
    )

    assert len(calls) == 1
    assert evidence["checkpoint"]["stop_reason"] == stop_reason
    assert evidence["state_counts"]["blocked"] == 1
    assert evidence["state_counts"]["pending"] == 43


def test_missing_usage_stops_and_is_never_silently_zero(controlled_inputs):
    calls = []

    def missing_usage(packet, timeout):
        calls.append((packet, timeout))
        return {
            "normalized_output": deepcopy(
                controlled_inputs[3][packet["case_alias"]]
            ),
            "provider": packet["provider"],
            "model": packet["model"],
            "latency_ms": 1,
            "input_token_count": None,
            "output_token_count": 1,
            "provider_outcome_category": "success",
        }

    evidence = _execute(controlled_inputs, missing_usage)

    assert len(calls) == 1
    assert evidence["checkpoint"]["stop_reason"] == "missing_usage_metadata"
    assert evidence["aggregate_usage"]["input_tokens"] == 0


def test_ambiguous_timeout_exception_stops_without_second_call(controlled_inputs):
    calls = []

    def ambiguous(packet, timeout):
        calls.append((packet, timeout))
        raise harness.AmbiguousTransportTimeout("raw text not retained")

    evidence = _execute(
        controlled_inputs,
        ambiguous,
        maximum_schedule_items=4,
    )

    assert len(calls) == 1
    assert evidence["checkpoint"]["stop_reason"] == "ambiguous_timeout"
    assert evidence["state_counts"]["ambiguous"] == 1
    assert evidence["hard_failure_present"] is True
    assert evidence["grading_summaries"] == []


def test_retained_evidence_excludes_provider_and_request_material(
    completed_evidence,
):
    evidence, _transport = completed_evidence
    runtime.serialize_provider_neutral_run_evidence(
        evidence,
        plan=build_controlled_provider_benchmark_plan(),
        authorization=harness.load_synthetic_authorization_fixture(),
        pricing=harness.load_synthetic_pricing_fixture(),
    )

    retained_keys = {str(key).lower() for key in _iter_keys(evidence)}
    for prohibited_key in (
        "normalized_output",
        "synthetic_input",
        "request_packet",
        "raw_response",
        "sdk_object",
        "reasoning",
        "request_id",
        "api_key",
        "credential",
    ):
        assert prohibited_key not in retained_keys


def test_serialization_and_digest_are_deterministic_with_fixed_time(
    controlled_inputs,
):
    outputs = controlled_inputs[3]
    first = _execute(controlled_inputs, GoldenTransport(outputs))
    second = _execute(controlled_inputs, GoldenTransport(outputs))
    kwargs = {
        "plan": controlled_inputs[0],
        "authorization": controlled_inputs[1],
        "pricing": controlled_inputs[2],
    }

    assert runtime.serialize_provider_neutral_run_evidence(first, **kwargs) == (
        runtime.serialize_provider_neutral_run_evidence(second, **kwargs)
    )
    assert runtime.provider_neutral_run_evidence_sha256(first, **kwargs) == (
        runtime.provider_neutral_run_evidence_sha256(second, **kwargs)
    )


def test_evidence_digest_changes_when_executed_model_evidence_changes(
    controlled_inputs,
):
    outputs = controlled_inputs[3]
    groq_only = _execute(
        controlled_inputs,
        GoldenTransport(outputs),
        maximum_schedule_items=22,
    )
    with_openai = _execute(
        controlled_inputs,
        GoldenTransport(outputs),
        maximum_schedule_items=23,
    )
    kwargs = {
        "plan": controlled_inputs[0],
        "authorization": controlled_inputs[1],
        "pricing": controlled_inputs[2],
    }

    assert {row["provider"] for row in groq_only["grading_summaries"]} == {
        "groq"
    }
    assert {row["provider"] for row in with_openai["grading_summaries"]} == {
        "groq",
        "openai",
    }
    assert runtime.provider_neutral_run_evidence_sha256(
        groq_only, **kwargs
    ) != runtime.provider_neutral_run_evidence_sha256(with_openai, **kwargs)


def test_evidence_binding_tampering_is_rejected(completed_evidence, controlled_inputs):
    evidence, _transport = completed_evidence
    tampered = deepcopy(evidence)
    tampered["plan_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="binding"):
        runtime.validate_provider_neutral_run_evidence(
            tampered,
            plan=controlled_inputs[0],
            authorization=controlled_inputs[1],
            pricing=controlled_inputs[2],
        )


def test_exclusive_persistence_uses_tmp_namespace_and_mode_0600(
    tmp_path,
    completed_evidence,
    controlled_inputs,
):
    evidence, _transport = completed_evidence
    path = tmp_path / "outputs/provider_benchmark/step9c3-evidence.json"
    kwargs = {
        "repository_root": tmp_path,
        "plan": controlled_inputs[0],
        "authorization": controlled_inputs[1],
        "pricing": controlled_inputs[2],
    }

    written = runtime.write_provider_neutral_run_evidence_exclusive(
        path,
        evidence,
        **kwargs,
    )

    assert written == path
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text(encoding="utf-8")) == evidence
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    with pytest.raises(ValueError, match="overwrite"):
        runtime.write_provider_neutral_run_evidence_exclusive(
            path,
            evidence,
            **kwargs,
        )


def test_persistence_rejects_outside_path_and_symlink_parent(
    tmp_path,
    completed_evidence,
    controlled_inputs,
):
    evidence, _transport = completed_evidence
    kwargs = {
        "repository_root": tmp_path,
        "plan": controlled_inputs[0],
        "authorization": controlled_inputs[1],
        "pricing": controlled_inputs[2],
    }

    with pytest.raises(ValueError, match="outside"):
        runtime.write_provider_neutral_run_evidence_exclusive(
            tmp_path / "outside.json",
            evidence,
            **kwargs,
        )

    target = tmp_path / "real-output"
    target.mkdir()
    output_link = tmp_path / "outputs"
    output_link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe"):
        runtime.write_provider_neutral_run_evidence_exclusive(
            tmp_path / "outputs/provider_benchmark/evidence.json",
            evidence,
            **kwargs,
        )


def test_focused_execution_creates_no_repository_output(completed_evidence):
    output_root = ROOT / runtime.APPROVED_ARTIFACT_DIRECTORY
    before = (
        sorted(path.relative_to(ROOT).as_posix() for path in output_root.rglob("*"))
        if output_root.exists()
        else []
    )

    _evidence, _transport = completed_evidence

    after = (
        sorted(path.relative_to(ROOT).as_posix() for path in output_root.rglob("*"))
        if output_root.exists()
        else []
    )
    assert after == before


def test_fake_transport_run_has_no_network_reach(monkeypatch, controlled_inputs):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network reach prohibited")

    monkeypatch.setattr(socket, "socket", blocked)
    evidence = _execute(
        controlled_inputs,
        GoldenTransport(controlled_inputs[3]),
    )
    assert evidence["execution_status"] == "partial"


def test_passed_run_evidence_is_not_qualification_or_human_review_decision(
    completed_evidence,
):
    evidence, _transport = completed_evidence
    serialized = json.dumps(evidence, sort_keys=True).lower()

    assert evidence["authority_invariants"]["registry_write_allowed"] is False
    assert "human_review" not in serialized
    for status in ('"qualified"', '"rejected"', '"pending_review"', '"stale"'):
        assert status not in serialized
    assert any(
        row["workload_id"] == "tailoring_generation"
        and row["quality_gate_passed"] is True
        for row in evidence["grading_summaries"]
    )


def test_step9c1_plan_remains_44_cells_and_live_default_off(controlled_inputs):
    plan = controlled_inputs[0]

    assert plan["request_counts"]["maximum_total_requests"] == 44
    assert plan["request_counts"]["by_model"] == EXPECTED_MODEL_COUNTS
    assert not any(
        row["workload_id"] == "skill_extraction"
        and row["model"] == "openai/gpt-oss-120b"
        for row in plan["staged_matrix"]
    )
    assert plan["authority_invariants"]["live_execution_authorized"] is False
    assert plan["authority_invariants"]["provider_calls_allowed"] is False
    assert plan["authority_invariants"]["routing_change_allowed"] is False


def test_no_production_source_imports_provider_neutral_evidence_runtime():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_provider_benchmark_evidence_runtime" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())

    assert sorted(references) == [
        "src/evaluation/controlled_provider_benchmark_human_review.py",
        "src/evaluation/controlled_provider_qualification_registry.py",
    ]

from __future__ import annotations

import ast
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
from types import SimpleNamespace

import pytest

from src.evaluation import controlled_groq_canary_evidence_runtime as runtime
from src.evaluation import controlled_groq_canary_transport as transport
from src.evaluation import controlled_groq_provider_canary as canary_owner
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)
from src.evaluation.provider_fixture_benchmark import (
    load_fixture_case_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_canary_evidence_runtime.py"
)
PRICING_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_pricing_001.json"
)
AUTHORIZATION_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_authorization_001.json"
)
REAL_RESULT_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_result_001.json"
)
REAL_CHECKPOINT_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_checkpoint_001.json"
)
EXECUTION_TIME = "2026-07-25T10:40:33Z"
CANARY_SHA256 = (
    "43241c341fe4d69c8cbeb2d6e95b6c56e68e67134b693c91396a932775a673bf"
)
HARNESS_SHA256 = (
    "eacf13521305689a0e7c7e3768c5e18c083308d30e6bb6b69f8d5cab1f125572"
)
TRANSPORT_SHA256 = (
    "e27ad7f7eccf67837cde2b940c448042953abe16749378b0f353d6e503180209"
)
PRICING_FILE_SHA256 = (
    "05a67642a30fd111ad8fb5f44dd0479595b8b8ab493d6868104ad67b20e767e7"
)
AUTHORIZATION_FILE_SHA256 = (
    "a3eef7c83614b9a11c58de56e1d2968d29ce46e8d15660040bd9b784aa6aa631"
)

_BASE_PRICING = json.loads(PRICING_PATH.read_text(encoding="utf-8"))
_BASE_AUTHORIZATION = json.loads(
    AUTHORIZATION_PATH.read_text(encoding="utf-8")
)
_BASE_CANARY = canary_owner.build_controlled_groq_canary_contract()
_BASE_PLAN = build_controlled_provider_benchmark_plan()
_BASE_CORPUS = load_fixture_case_corpus()
_BASE_CASES = {
    review["case_alias"]: case
    for review, case in zip(
        _BASE_PLAN["transmission_review"],
        _BASE_CORPUS["cases"],
    )
    if review["eligible_for_later_controlled_transmission"]
}


def _pricing():
    return deepcopy(_BASE_PRICING)


def _authorization():
    return deepcopy(_BASE_AUTHORIZATION)


def _canary():
    return deepcopy(_BASE_CANARY)


def _plan():
    return deepcopy(_BASE_PLAN)


def _case_maps():
    return deepcopy(_BASE_CASES)


def _empty(*, authorization=None):
    return runtime.build_empty_checkpoint(
        authorization=_authorization()
        if authorization is None
        else authorization,
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )


def _result(index=0, **overrides):
    row = _canary()["schedule"][index]
    payload = {
        "normalized_output": deepcopy(
            _case_maps()[row["case_alias"]]["expected_output"]
        ),
        "provider": "groq",
        "model": row["model"],
        "latency_ms": 12.5,
        "input_token_count": 11,
        "output_token_count": 7,
        "provider_outcome_category": "success",
    }
    payload.update(overrides)
    return payload


def _safe_non_golden_skill_extraction_result():
    result = _result(0)
    normalized = deepcopy(result["normalized_output"])
    normalized["required_skills"] = normalized["required_skills"][:-1]
    result["normalized_output"] = normalized
    return result


def _complete(checkpoint, index=0, *, result=None, authorization=None):
    approved_authorization = (
        _authorization() if authorization is None else authorization
    )
    return runtime.record_completed_call(
        checkpoint,
        scheduled=_canary()["schedule"][index],
        transport_result=_result(index) if result is None else result,
        authorization=approved_authorization,
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )


def _complete_all():
    checkpoint = _empty()
    for index in range(4):
        checkpoint = _complete(checkpoint, index)
    return checkpoint


def _temporary_repository(tmp_path):
    root = tmp_path / "repository"
    output = root / "outputs/provider_benchmark"
    output.mkdir(parents=True)
    output.chmod(0o700)
    (root / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    return root, output


def _persistence_kwargs(root):
    return {
        "repository_root": root,
        "authorization": _authorization(),
        "pricing": _pricing(),
        "execution_at_utc": EXECUTION_TIME,
        "canary": _canary(),
    }


class FakeCompletions:
    def __init__(self, responses, checkpoint_path):
        self.responses = list(responses)
        self.checkpoint_path = checkpoint_path
        self.calls = []
        self.checkpoint_present_before_calls = []

    def create(self, **kwargs):
        self.checkpoint_present_before_calls.append(
            self.checkpoint_path.exists()
        )
        self.calls.append(deepcopy(kwargs))
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses, checkpoint_path):
        self.completions = FakeCompletions(responses, checkpoint_path)
        self.chat = SimpleNamespace(completions=self.completions)


def _sdk_response(index):
    row = _canary()["schedule"][index]
    return SimpleNamespace(
        model=row["model"],
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(
                        _case_maps()[row["case_alias"]]["expected_output"],
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=7,
        ),
        id="not-retained",
        headers={"not": "retained"},
        reasoning="not-retained",
    )


def _clock(index):
    values = iter((100.0 + index, 100.01 + index))
    return lambda: next(values)


def _fake_persisted_run(tmp_path):
    root, output = _temporary_repository(tmp_path)
    checkpoint_path = output / "checkpoint.json"
    result_path = output / "result.json"
    kwargs = _persistence_kwargs(root)
    checkpoint = _empty()
    runtime.write_initial_checkpoint(
        checkpoint_path,
        checkpoint,
        **kwargs,
    )
    client = FakeClient(
        [_sdk_response(index) for index in range(4)],
        checkpoint_path,
    )
    replacement_count = 0
    grader_count = 0
    for index, scheduled in enumerate(_canary()["schedule"]):
        reduced = transport.execute_groq_chat_completion_once(
            client=client,
            packet=build_transmittable_request_packet(
                case_alias=scheduled["case_alias"],
                provider=scheduled["provider"],
                model=scheduled["model"],
                plan=_plan(),
                live_execution_requested=False,
            ),
            scheduled=scheduled,
            monotonic_clock=_clock(index),
            plan=_plan(),
        )
        grader_count += 1
        prior_sha = runtime.checkpoint_sha256(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )
        checkpoint = _complete(
            checkpoint,
            index,
            result=reduced,
        )
        runtime.replace_checkpoint_atomic(
            checkpoint_path,
            checkpoint,
            expected_prior_sha256=prior_sha,
            **kwargs,
        )
        replacement_count += 1
    artifact = runtime.build_result_artifact(
        checkpoint=checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    runtime.write_result_exclusive(
        result_path,
        artifact,
        **kwargs,
    )
    return {
        "root": root,
        "checkpoint_path": checkpoint_path,
        "result_path": result_path,
        "checkpoint": checkpoint,
        "artifact": artifact,
        "client": client,
        "replacement_count": replacement_count,
        "grader_count": grader_count,
    }


@pytest.fixture(scope="module")
def persisted_fake_proof(tmp_path_factory):
    return _fake_persisted_run(tmp_path_factory.mktemp("canary_evidence"))


def test_runtime_versions_are_exact():
    assert runtime.EVIDENCE_RUNTIME_VERSION == (
        "controlled-groq-canary-evidence-runtime-v1"
    )
    assert runtime.CHECKPOINT_SCHEMA_VERSION == (
        "controlled-groq-canary-checkpoint-v1"
    )
    assert runtime.RESULT_SCHEMA_VERSION == (
        "controlled-groq-canary-result-v1"
    )


def test_canary_schedule_is_consumed_from_committed_owner():
    checkpoint = _empty()
    assert checkpoint["schedule_count"] == len(_canary()["schedule"]) == 4


def test_pinned_contract_digests_are_unchanged():
    assert canary_owner.controlled_groq_canary_sha256() == CANARY_SHA256
    assert harness.controlled_benchmark_harness_sha256() == HARNESS_SHA256
    assert transport.controlled_groq_transport_sha256() == TRANSPORT_SHA256


def test_transport_version_and_digest_are_consumed():
    checkpoint = _empty()
    assert checkpoint["transport_version"] == transport.TRANSPORT_VERSION
    assert checkpoint["transport_sha256"] == TRANSPORT_SHA256


def test_runtime_has_no_model_registry_or_route_selection():
    source = OWNER_PATH.read_text(encoding="utf-8")
    assert "_GROQ_CANDIDATES" not in source
    assert "selected_model" not in source
    assert "recommended_route" not in source


def test_empty_checkpoint_validates():
    assert runtime.validate_checkpoint(
        _empty(),
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )


def test_empty_checkpoint_is_deep_copy_contained():
    first = _empty()
    second = _empty()
    first["completed_schedule_keys"].append("tamper")
    assert second["completed_schedule_keys"] == []


def test_checkpoint_serialization_is_canonical_and_stable():
    checkpoint = _empty()
    serialized = runtime.serialize_checkpoint(
        checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert serialized == json.dumps(
        checkpoint,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def test_checkpoint_digest_is_stable_across_fresh_process():
    script = (
        "import json;"
        "from pathlib import Path;"
        "from src.evaluation import controlled_groq_canary_evidence_runtime as r;"
        "root=Path.cwd();"
        "p=json.loads((root/'outputs/provider_benchmark/"
        "phase11_groq_canary_pricing_001.json').read_text());"
        "a=json.loads((root/'outputs/provider_benchmark/"
        "phase11_groq_canary_authorization_001.json').read_text());"
        "c=r.build_empty_checkpoint(authorization=a,pricing=p,"
        f"execution_at_utc='{EXECUTION_TIME}');"
        "print(r.checkpoint_sha256(c,authorization=a,pricing=p,"
        f"execution_at_utc='{EXECUTION_TIME}'))"
    )
    observed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT)},
    ).stdout.strip()
    expected = runtime.checkpoint_sha256(
        _empty(),
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert observed == expected


def test_exactly_four_canary_keys_are_accepted():
    canary_keys = {row["schedule_key"] for row in _canary()["schedule"]}
    assert len(canary_keys) == 4
    assert _complete_all()["completed_schedule_keys"] == [
        row["schedule_key"] for row in _canary()["schedule"]
    ]


def test_step8q_full_plan_key_is_rejected():
    full_row = harness._schedule_from_plan(_plan())[0]
    with pytest.raises(ValueError, match="outside the canary"):
        runtime.record_blocked_call(
            _empty(),
            scheduled=full_row,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


def test_unknown_key_is_rejected():
    checkpoint = _empty()
    checkpoint["blocked_schedule_keys"].append("unknown")
    with pytest.raises(ValueError):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


@pytest.mark.parametrize("field", runtime._STATE_FIELDS)
def test_duplicate_state_key_is_rejected(field):
    checkpoint = _empty()
    key = _canary()["schedule"][0]["schedule_key"]
    checkpoint[field] = [key, key]
    with pytest.raises(ValueError):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("completed_schedule_keys", "blocked_schedule_keys"),
        ("completed_schedule_keys", "ambiguous_schedule_keys"),
        ("completed_schedule_keys", "hard_failure_schedule_keys"),
        ("blocked_schedule_keys", "ambiguous_schedule_keys"),
        ("blocked_schedule_keys", "hard_failure_schedule_keys"),
        ("ambiguous_schedule_keys", "hard_failure_schedule_keys"),
    ],
)
def test_overlapping_state_lists_are_rejected(left, right):
    checkpoint = _empty()
    key = _canary()["schedule"][0]["schedule_key"]
    checkpoint[left] = [key]
    checkpoint[right] = [key]
    with pytest.raises(ValueError, match="overlap"):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


def test_invoked_key_without_final_state_is_rejected():
    checkpoint = _empty()
    key = _canary()["schedule"][0]["schedule_key"]
    checkpoint["aggregate_usage"]["provider_call_count"] = 1
    checkpoint["aggregate_usage"]["by_schedule_key"][key] = 1
    with pytest.raises(ValueError, match="reconcile"):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


def test_completed_key_without_summary_is_rejected():
    checkpoint = _empty()
    checkpoint["completed_schedule_keys"] = [
        _canary()["schedule"][0]["schedule_key"]
    ]
    with pytest.raises(ValueError):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


def test_grading_summary_unknown_key_is_rejected():
    checkpoint = _complete(_empty())
    checkpoint["grading_summaries"][0]["schedule_key"] = "unknown"
    with pytest.raises(ValueError, match="unknown"):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider_call_count", 99),
        ("input_token_count", 99),
        ("output_token_count", 99),
        ("latency_ms", 99.0),
        ("observed_cost", "1.0"),
        ("by_model", {}),
        ("by_workload", {}),
        ("by_schedule_key", {}),
    ],
)
def test_aggregate_tampering_is_rejected(field, value):
    checkpoint = _complete(_empty())
    checkpoint["aggregate_usage"][field] = value
    with pytest.raises(ValueError, match="reconcile"):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fallback_count", 1),
        ("retry_count", 1),
        ("raw_response_persisted_count", 1),
        ("mutation_count", 1),
        ("application_action_count", 1),
        ("ats_action_count", 1),
        ("production_activation", True),
        ("winner_selected", True),
    ],
)
def test_authority_tampering_is_rejected(field, value):
    checkpoint = _empty()
    checkpoint["authority_invariants"][field] = value
    with pytest.raises(ValueError, match="authority"):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


def test_completed_transition_records_exactly_one_call():
    original = _empty()
    updated = _complete(original)
    assert original["aggregate_usage"]["provider_call_count"] == 0
    assert updated["aggregate_usage"]["provider_call_count"] == 1
    assert len(updated["completed_schedule_keys"]) == 1


def test_blocked_transition_stops():
    checkpoint = runtime.record_blocked_call(
        _empty(),
        scheduled=_canary()["schedule"][0],
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert len(checkpoint["blocked_schedule_keys"]) == 1
    assert checkpoint["stop_reason"] == "definitive_transport_failure"


def test_ambiguous_transition_stops():
    checkpoint = runtime.record_ambiguous_call(
        _empty(),
        scheduled=_canary()["schedule"][0],
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert len(checkpoint["ambiguous_schedule_keys"]) == 1
    assert checkpoint["stop_reason"] == "ambiguous_timeout"


def test_hard_failure_transition_stops():
    checkpoint = runtime.record_hard_failure_call(
        _empty(),
        scheduled=_canary()["schedule"][0],
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        reason="hard_safety_failure",
        canary=_canary(),
    )
    assert len(checkpoint["hard_failure_schedule_keys"]) == 1
    assert checkpoint["quality_gate_status"] == "failed"


@pytest.mark.parametrize("state", ["blocked", "ambiguous", "hard"])
def test_terminal_failure_state_cannot_resume(state):
    kwargs = {
        "scheduled": _canary()["schedule"][0],
        "authorization": _authorization(),
        "pricing": _pricing(),
        "execution_at_utc": EXECUTION_TIME,
        "canary": _canary(),
    }
    if state == "blocked":
        checkpoint = runtime.record_blocked_call(_empty(), **kwargs)
    elif state == "ambiguous":
        checkpoint = runtime.record_ambiguous_call(_empty(), **kwargs)
    else:
        checkpoint = runtime.record_hard_failure_call(
            _empty(),
            reason="hard_safety_failure",
            **kwargs,
        )
    with pytest.raises(ValueError, match="cannot be resumed"):
        runtime.record_blocked_call(
            checkpoint,
            scheduled=_canary()["schedule"][1],
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


def test_quality_gate_failure_becomes_hard_failure():
    result = _result()
    result["normalized_output"] = {}
    checkpoint = _complete(_empty(), result=result)
    assert checkpoint["completed_schedule_keys"] == []
    assert len(checkpoint["hard_failure_schedule_keys"]) == 1


def test_safe_non_golden_quality_failure_is_bounded_and_durable(tmp_path):
    original = _empty()
    before = deepcopy(original)
    result = _safe_non_golden_skill_extraction_result()
    row = _canary()["schedule"][0]
    cases_by_alias, case_ids = runtime._case_maps()
    case = cases_by_alias[row["case_alias"]]
    grade = runtime.grade_normalized_candidate_result(
        {
            "case_id": case_ids[row["case_alias"]],
            "workload_id": row["workload_id"],
            "provider": row["provider"],
            "model": row["model"],
            "normalized_output": deepcopy(result["normalized_output"]),
            "schema_valid": all(
                field in result["normalized_output"]
                and result["normalized_output"][field] is not None
                for field in case["required_fields"]
            ),
            "normalization_succeeded": True,
            "fallback_used": False,
            "provider_call_count": 0,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "raw_response_persisted": False,
            "live_execution": False,
            "latency_ms": result["latency_ms"],
            "input_token_count": result["input_token_count"],
            "output_token_count": result["output_token_count"],
            "estimated_cost": 0.0,
        },
        corpus=runtime.load_fixture_case_corpus(),
    )
    assert grade["quality_gate_passed"] is False
    assert all(value == 0 for value in grade["hard_failures"].values())
    assert runtime._bounded_grade_failures(grade) == {}

    updated = _complete(original, result=result)
    key = row["schedule_key"]
    summary = updated["grading_summaries"][0]
    expected_cost = runtime.calculate_observed_cost(
        pricing=_pricing(),
        provider=row["provider"],
        model=row["model"],
        input_token_count=result["input_token_count"],
        output_token_count=result["output_token_count"],
    )
    assert original == before
    assert updated["completed_schedule_keys"] == []
    assert updated["blocked_schedule_keys"] == []
    assert updated["ambiguous_schedule_keys"] == []
    assert updated["hard_failure_schedule_keys"] == [key]
    assert summary["quality_gate_passed"] is False
    assert summary["hard_failures"] == {"workload_quality_gate_failed": 1}
    assert updated["stop_reason"] == "hard_safety_failure"
    assert updated["quality_gate_status"] == "failed"
    assert updated["cost_comparison_eligibility"] is False
    assert updated["aggregate_usage"]["provider_call_count"] == 1
    assert updated["aggregate_usage"]["input_token_count"] == 11
    assert updated["aggregate_usage"]["output_token_count"] == 7
    assert updated["aggregate_usage"]["latency_ms"] == 12.5
    assert Decimal(updated["aggregate_usage"]["observed_cost"]) == expected_cost
    assert runtime.validate_checkpoint(
        updated,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    serialized = runtime.serialize_checkpoint(
        updated,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    serialized_keys = set(runtime._iter_keys(json.loads(serialized)))
    assert "normalized_output" not in serialized_keys
    assert "raw_response" not in serialized_keys

    root, output = _temporary_repository(tmp_path)
    path = output / "checkpoint.json"
    kwargs = _persistence_kwargs(root)
    runtime.write_initial_checkpoint(path, original, **kwargs)
    prior = runtime.checkpoint_sha256(
        original,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    runtime.replace_checkpoint_atomic(
        path,
        updated,
        expected_prior_sha256=prior,
        **kwargs,
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert runtime.load_checkpoint(path, **kwargs) == updated


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("input_token_count", None),
        ("output_token_count", None),
        ("input_token_count", 0),
        ("output_token_count", 0),
    ],
)
def test_missing_usage_becomes_bounded_hard_failure(field, value):
    result = _result()
    result[field] = value
    checkpoint = _complete(_empty(), result=result)
    assert checkpoint["stop_reason"] == "missing_usage_metadata"
    assert checkpoint["aggregate_usage"]["input_token_count"] == 0
    assert checkpoint["aggregate_usage"]["output_token_count"] == 0


def test_provider_model_mismatch_fails_closed():
    checkpoint = _complete(
        _empty(),
        result=_result(model="unknown-model"),
    )
    assert checkpoint["stop_reason"] == "provider_model_mismatch"
    assert len(checkpoint["hard_failure_schedule_keys"]) == 1


@pytest.mark.parametrize(
    ("outcome", "reason"),
    [
        ("fallback_attempt", "fallback_attempted"),
        ("retry_attempt", "retry_attempted"),
        ("raw_response_persistence", "raw_response_persistence"),
        ("application_action", "application_action"),
        ("ats_action", "ats_action"),
        ("unknown_provider_outcome", "unknown_provider_outcome"),
    ],
)
def test_unauthorized_outcome_fails_closed(outcome, reason):
    checkpoint = _complete(
        _empty(),
        result=_result(provider_outcome_category=outcome),
    )
    assert checkpoint["stop_reason"] == reason
    assert len(checkpoint["hard_failure_schedule_keys"]) == 1


def test_definitive_outcome_becomes_blocked():
    checkpoint = _complete(
        _empty(),
        result=_result(provider_outcome_category="definitive_failure"),
    )
    assert len(checkpoint["blocked_schedule_keys"]) == 1


def test_ambiguous_outcome_becomes_ambiguous():
    checkpoint = _complete(
        _empty(),
        result=_result(provider_outcome_category="ambiguous_timeout"),
    )
    assert len(checkpoint["ambiguous_schedule_keys"]) == 1


def test_transition_does_not_mutate_input_and_returns_deep_copy():
    checkpoint = _empty()
    before = deepcopy(checkpoint)
    updated = _complete(checkpoint)
    assert checkpoint == before
    updated["completed_schedule_keys"].append("tamper")
    assert checkpoint == before


def test_observed_cost_formula_is_exact_decimal():
    pricing = _pricing()
    price = {
        f"{row['provider']}/{row['model']}": row
        for row in pricing["prices"]
    }["groq/openai/gpt-oss-20b"]
    expected = (
        Decimal(11) * Decimal(str(price["input_price_per_million_tokens"]))
        + Decimal(7) * Decimal(str(price["output_price_per_million_tokens"]))
    ) / Decimal(1_000_000)
    assert runtime.calculate_observed_cost(
        pricing=pricing,
        provider="groq",
        model="openai/gpt-oss-20b",
        input_token_count=11,
        output_token_count=7,
    ) == expected


def _tiny_ceiling_authorization(*, total_only=False):
    authorization = _authorization()
    if not total_only:
        authorization["maximum_observed_cost_per_model"] = {
            key: "0.000000000001"
            for key in authorization["maximum_observed_cost_per_model"]
        }
    authorization["maximum_total_observed_cost"] = "0.000000000001"
    return authorization


def test_per_model_cost_ceiling_is_enforced():
    authorization = _tiny_ceiling_authorization()
    checkpoint = _empty(authorization=authorization)
    checkpoint = _complete(
        checkpoint,
        authorization=authorization,
    )
    assert checkpoint["stop_reason"] == "cost_ceiling_exceeded"


def test_total_cost_ceiling_is_enforced():
    authorization = _tiny_ceiling_authorization(total_only=True)
    checkpoint = _empty(authorization=authorization)
    checkpoint = _complete(
        checkpoint,
        authorization=authorization,
    )
    assert checkpoint["stop_reason"] == "cost_ceiling_exceeded"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("input_token_count", 4097),
        ("output_token_count", 1025),
    ],
)
def test_per_request_token_ceiling_is_enforced(field, value):
    result = _result()
    result[field] = value
    checkpoint = _complete(_empty(), result=result)
    assert checkpoint["stop_reason"] == "token_budget_exceeded"


def test_cost_comparison_false_after_partial_or_failure():
    assert _complete(_empty())["cost_comparison_eligibility"] is False
    failed = runtime.record_blocked_call(
        _empty(),
        scheduled=_canary()["schedule"][0],
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert failed["cost_comparison_eligibility"] is False


def test_initial_checkpoint_exclusive_creation_and_mode(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "checkpoint.json"
    runtime.write_initial_checkpoint(
        path,
        _empty(),
        **_persistence_kwargs(root),
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert runtime.load_checkpoint(
        path,
        **_persistence_kwargs(root),
    ) == _empty()


def test_initial_checkpoint_overwrite_is_rejected(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "checkpoint.json"
    runtime.write_initial_checkpoint(
        path,
        _empty(),
        **_persistence_kwargs(root),
    )
    with pytest.raises(ValueError, match="overwrite"):
        runtime.write_initial_checkpoint(
            path,
            _empty(),
            **_persistence_kwargs(root),
        )


def test_atomic_replacement_requires_exact_prior_digest(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "checkpoint.json"
    checkpoint = _empty()
    kwargs = _persistence_kwargs(root)
    runtime.write_initial_checkpoint(path, checkpoint, **kwargs)
    prior = runtime.checkpoint_sha256(
        checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    updated = _complete(checkpoint)
    runtime.replace_checkpoint_atomic(
        path,
        updated,
        expected_prior_sha256=prior,
        **kwargs,
    )
    assert runtime.load_checkpoint(path, **kwargs) == updated
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_stale_prior_digest_is_rejected(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "checkpoint.json"
    runtime.write_initial_checkpoint(
        path,
        _empty(),
        **_persistence_kwargs(root),
    )
    with pytest.raises(ValueError, match="digest"):
        runtime.replace_checkpoint_atomic(
            path,
            _complete(_empty()),
            expected_prior_sha256="0" * 64,
            **_persistence_kwargs(root),
        )


def test_missing_prior_checkpoint_is_rejected(tmp_path):
    root, output = _temporary_repository(tmp_path)
    with pytest.raises(ValueError, match="missing"):
        runtime.replace_checkpoint_atomic(
            output / "checkpoint.json",
            _empty(),
            expected_prior_sha256="0" * 64,
            **_persistence_kwargs(root),
        )


def test_symlink_artifact_path_is_rejected(tmp_path):
    root, output = _temporary_repository(tmp_path)
    target = output / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = output / "checkpoint.json"
    link.symlink_to(target)
    with pytest.raises(ValueError):
        runtime.write_initial_checkpoint(
            link,
            _empty(),
            **_persistence_kwargs(root),
        )


def test_path_traversal_is_rejected(tmp_path):
    root, output = _temporary_repository(tmp_path)
    traversal = Path(str(output) + "/../provider_benchmark/checkpoint.json")
    with pytest.raises(ValueError, match="traversal"):
        runtime.write_initial_checkpoint(
            traversal,
            _empty(),
            **_persistence_kwargs(root),
        )


def test_path_outside_approved_root_is_rejected(tmp_path):
    root, _output = _temporary_repository(tmp_path)
    outside = root / "checkpoint.json"
    with pytest.raises(ValueError, match="outside"):
        runtime.write_initial_checkpoint(
            outside,
            _empty(),
            **_persistence_kwargs(root),
        )


def test_malformed_persisted_checkpoint_is_rejected(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "checkpoint.json"
    path.write_text("{malformed", encoding="utf-8")
    path.chmod(0o600)
    with pytest.raises(ValueError, match="malformed"):
        runtime.load_checkpoint(
            path,
            **_persistence_kwargs(root),
        )


def test_temporary_replacement_file_is_cleaned_on_failure(
    tmp_path, monkeypatch
):
    root, output = _temporary_repository(tmp_path)
    path = output / "checkpoint.json"
    checkpoint = _empty()
    kwargs = _persistence_kwargs(root)
    runtime.write_initial_checkpoint(path, checkpoint, **kwargs)
    prior = runtime.checkpoint_sha256(
        checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )

    def fail_replace(_source, _destination):
        raise OSError("bounded synthetic replacement failure")

    monkeypatch.setattr(runtime.os, "replace", fail_replace)
    with pytest.raises(OSError):
        runtime.replace_checkpoint_atomic(
            path,
            _complete(checkpoint),
            expected_prior_sha256=prior,
            **kwargs,
        )
    assert list(output.glob("*.tmp")) == []
    assert list(output.glob(".*.tmp")) == []


def test_result_build_validate_serialize_and_digest():
    checkpoint = _complete_all()
    artifact = runtime.build_result_artifact(
        checkpoint=checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert runtime.validate_result_artifact(
        artifact,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert runtime.result_sha256(
        artifact,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    ) == sha256(
        runtime.serialize_result_artifact(
            artifact,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        ).encode("utf-8")
    ).hexdigest()


def test_result_exclusive_creation_mode_and_revalidation(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "result.json"
    artifact = runtime.build_result_artifact(
        checkpoint=_complete_all(),
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    runtime.write_result_exclusive(
        path,
        artifact,
        **_persistence_kwargs(root),
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert runtime.load_result_artifact(
        path,
        **_persistence_kwargs(root),
    ) == artifact


def test_result_overwrite_is_rejected(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "result.json"
    artifact = runtime.build_result_artifact(
        checkpoint=_complete_all(),
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    runtime.write_result_exclusive(
        path,
        artifact,
        **_persistence_kwargs(root),
    )
    with pytest.raises(ValueError, match="overwrite"):
        runtime.write_result_exclusive(
            path,
            artifact,
            **_persistence_kwargs(root),
        )


@pytest.mark.parametrize(
    "prohibited",
    [
        "normalized_output",
        "raw_response",
        "raw_request",
        "prompt",
        "api_key",
        "environment",
        "request_id",
        "headers",
        "reasoning",
        "raw_exception",
    ],
)
def test_prohibited_evidence_fields_are_rejected(prohibited):
    checkpoint = _empty()
    checkpoint[prohibited] = "blocked"
    with pytest.raises(ValueError):
        runtime.validate_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )


def test_fake_four_call_persistence_proof(persisted_fake_proof):
    proof = persisted_fake_proof
    checkpoint = proof["checkpoint"]
    assert len(proof["client"].completions.calls) == 4
    assert all(proof["client"].completions.checkpoint_present_before_calls)
    assert proof["replacement_count"] == 4
    assert proof["grader_count"] == 4
    assert checkpoint["aggregate_usage"]["provider_call_count"] == 4
    assert len(checkpoint["completed_schedule_keys"]) == 4
    assert checkpoint["blocked_schedule_keys"] == []
    assert checkpoint["ambiguous_schedule_keys"] == []
    assert checkpoint["hard_failure_schedule_keys"] == []
    assert checkpoint["quality_gate_status"] == "passed"
    assert proof["artifact"]["final_status"] == "completed"


def test_fake_four_call_proof_has_two_calls_per_model(persisted_fake_proof):
    checkpoint = persisted_fake_proof["checkpoint"]
    assert checkpoint["aggregate_usage"]["by_model"] == {
        "openai/gpt-oss-20b": 2,
        "openai/gpt-oss-120b": 2,
    }


def test_fake_proof_artifacts_have_exact_permissions(persisted_fake_proof):
    proof = persisted_fake_proof
    assert stat.S_IMODE(proof["checkpoint_path"].stat().st_mode) == 0o600
    assert stat.S_IMODE(proof["result_path"].stat().st_mode) == 0o600


def test_fake_proof_aggregate_reconciles(persisted_fake_proof):
    proof = persisted_fake_proof
    summaries = proof["checkpoint"]["grading_summaries"]
    aggregate = proof["checkpoint"]["aggregate_usage"]
    assert aggregate["input_token_count"] == sum(
        row["input_token_count"] for row in summaries
    )
    assert aggregate["output_token_count"] == sum(
        row["output_token_count"] for row in summaries
    )
    assert Decimal(aggregate["observed_cost"]) == sum(
        (Decimal(row["observed_cost"]) for row in summaries),
        Decimal("0"),
    )


def test_fake_proof_retains_no_normalized_or_raw_output(
    persisted_fake_proof,
):
    proof = persisted_fake_proof
    evidence_keys = set(runtime._iter_keys(proof["artifact"]))
    for key in (
        "normalized_output",
        "raw_response",
        "request_id",
        "header",
        "reasoning",
    ):
        assert key not in evidence_keys


def test_evidence_runtime_does_not_import_real_groq():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "groq" not in imports


def test_runtime_reads_no_environment_or_dotenv():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "getenv" not in attributes
    assert "environ" not in attributes
    assert not any(name.startswith("dotenv") for name in imports)


def test_runtime_has_no_network_database_process_or_thread_reach():
    source = OWNER_PATH.read_text(encoding="utf-8")
    for prohibited in (
        "socket",
        "requests",
        "httpx",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "threading",
        "create_live_groq_client",
        "execute_groq_chat_completion_once",
    ):
        assert prohibited not in source


def test_fake_run_reaches_no_socket(tmp_path, monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network boundary reached")

    monkeypatch.setattr(socket, "socket", blocked)
    proof = _fake_persisted_run(tmp_path)
    assert proof["checkpoint"]["quality_gate_status"] == "passed"


def test_operator_inputs_are_byte_identical_and_valid():
    assert sha256(PRICING_PATH.read_bytes()).hexdigest() == PRICING_FILE_SHA256
    assert (
        sha256(AUTHORIZATION_PATH.read_bytes()).hexdigest()
        == AUTHORIZATION_FILE_SHA256
    )
    assert canary_owner.validate_operator_approved_pricing(
        _pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    assert canary_owner.validate_operator_authorization(
        _authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )


def test_real_reserved_artifacts_are_absent_or_exact_empty_incident():
    assert not REAL_RESULT_PATH.exists()
    assert not (ROOT / canary_owner.RECOVERY_006_STATUS_PATH).exists()
    if not REAL_CHECKPOINT_PATH.exists():
        return
    assert REAL_CHECKPOINT_PATH.is_file()
    assert not REAL_CHECKPOINT_PATH.is_symlink()
    assert stat.S_IMODE(REAL_CHECKPOINT_PATH.stat().st_mode) == 0o600
    incident = runtime.load_checkpoint(
        REAL_CHECKPOINT_PATH,
        repository_root=ROOT,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
        canary=_canary(),
    )
    assert incident == _empty()


def test_runtime_authority_remains_zero():
    checkpoint = _complete_all()
    authority = checkpoint["authority_invariants"]
    assert authority["fallback_count"] == 0
    assert authority["retry_count"] == 0
    assert authority["mutation_count"] == 0
    assert authority["application_action_count"] == 0
    assert authority["ats_action_count"] == 0
    assert authority["production_activation"] is False
    assert authority["winner_selected"] is False


def test_no_production_source_imports_evidence_runtime():
    references = []
    for source_path in (ROOT / "src").rglob("*.py"):
        if source_path == OWNER_PATH:
            continue
        if "controlled_groq_canary_evidence_runtime" in source_path.read_text(
            encoding="utf-8"
        ):
            references.append(source_path.relative_to(ROOT).as_posix())
    assert references == [
        "src/evaluation/controlled_groq_canary_run_identity.py",
        "src/evaluation/controlled_groq_canary_run_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_004_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_005_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py",
    ]

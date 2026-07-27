from copy import deepcopy
import json
from pathlib import Path
import stat

import pytest

from src.evaluation import controlled_groq_canary_run_004_evidence_runtime as owner
from src.evaluation.controlled_groq_canary_run_004_identity import (
    RUN_004_ARTIFACT_PATHS,
    build_run_004_authorization_template,
)
from src.evaluation.controlled_groq_provider_canary import (
    build_groq_pricing_template,
    pricing_table_sha256,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


NOW = "2026-07-27T00:00:00Z"


def _pricing():
    pricing = build_groq_pricing_template()
    pricing.update(
        pricing_version="run-004-test-pricing",
        source_classification="operator_test_fixture",
        source_effective_at_utc=NOW,
        valid_from_utc=NOW,
        expires_at_utc="2026-07-28T00:00:00Z",
        currency="USD",
        operator_approved=True,
    )
    values = {
        "openai/gpt-oss-20b": ("0.075", "0.30"),
        "openai/gpt-oss-120b": ("0.15", "0.60"),
    }
    for row in pricing["prices"]:
        row["input_price_per_million_tokens"], row[
            "output_price_per_million_tokens"
        ] = values[row["model"]]
    pricing["pricing_table_sha256"] = pricing_table_sha256(pricing)
    return pricing


def _authorization(*, ceiling="0.0025"):
    pricing = _pricing()
    auth = build_run_004_authorization_template()
    auth.update(
        maximum_observed_cost_per_model={
            "groq/openai/gpt-oss-120b": ceiling
        },
        maximum_total_observed_cost=ceiling,
        pricing_table_sha256=pricing["pricing_table_sha256"],
        valid_from_utc=NOW,
        expires_at_utc="2026-07-28T00:00:00Z",
        operator_approved=True,
        live_execution_authorized=True,
    )
    return auth


def _kwargs(*, ceiling="0.0025"):
    return {
        "authorization": _authorization(ceiling=ceiling),
        "pricing": _pricing(),
        "execution_at_utc": NOW,
    }


def _empty(**kwargs):
    return owner.build_empty_run_004_checkpoint(**(_kwargs() | kwargs))


def _transport(row, *, valid=True, input_tokens=100, output_tokens=100):
    corpus = load_fixture_case_corpus()
    case = next(
        c for c in corpus["cases"]
        if c["workload_id"] == row["workload_id"]
        and c["sanitized_classification"] == "synthetic_sanitized"
    )
    output = deepcopy(case["expected_output"]) if valid else {}
    return {
        "normalized_output": output,
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "latency_ms": 10.0,
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "provider_outcome_category": "success",
    }


def _pass(checkpoint, **kwargs):
    args = _kwargs() | kwargs
    row = owner.get_next_run_004_row(checkpoint, **args)
    return owner.record_run_004_completed_call(
        checkpoint, scheduled=row, transport_result=_transport(row), **args
    )


def test_empty_checkpoint_and_deterministic_two_row_selection():
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    first = owner.get_next_run_004_row(checkpoint, **kwargs)
    assert first["workload_id"] == "jd_intelligence"
    checkpoint = _pass(checkpoint)
    assert checkpoint["stop_reason"] is None
    assert checkpoint["quality_gate_status"] == "pending"
    second = owner.get_next_run_004_row(checkpoint, **kwargs)
    assert second["workload_id"] == "tailoring_generation"


def test_both_quality_passes_complete_and_build_terminal_result():
    kwargs = _kwargs()
    checkpoint = _pass(_pass(owner.build_empty_run_004_checkpoint(**kwargs)))
    assert checkpoint["stop_reason"] == "completed"
    assert checkpoint["quality_gate_status"] == "passed"
    assert checkpoint["aggregate_usage"]["provider_call_count"] == 2
    assert owner.get_next_run_004_row(checkpoint, **kwargs) is None
    result = owner.build_run_004_result_artifact(
        checkpoint=checkpoint, **kwargs
    )
    assert result["final_status"] == "completed"
    assert result["cost_comparison_eligibility"] is True


def test_first_quality_failure_stops_before_second():
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    row = owner.get_next_run_004_row(checkpoint, **kwargs)
    checkpoint = owner.record_run_004_completed_call(
        checkpoint, scheduled=row, transport_result=_transport(row, valid=False),
        **kwargs,
    )
    assert checkpoint["hard_failure_schedule_keys"] == [row["schedule_key"]]
    assert checkpoint["aggregate_usage"]["provider_call_count"] == 1
    assert owner.get_next_run_004_row(checkpoint, **kwargs) is None


@pytest.mark.parametrize("kind", ["blocked", "ambiguous"])
def test_first_transport_failure_is_terminal(kind):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    row = owner.get_next_run_004_row(checkpoint, **kwargs)
    if kind == "blocked":
        checkpoint = owner.record_run_004_blocked_call(
            checkpoint, scheduled=row, **kwargs
        )
    else:
        checkpoint = owner.record_run_004_ambiguous_call(
            checkpoint, scheduled=row, **kwargs
        )
    assert owner.get_next_run_004_row(checkpoint, **kwargs) is None
    assert owner.build_run_004_result_artifact(
        checkpoint=checkpoint, **kwargs
    )["final_status"] == f"stopped_{kind}"


def test_second_quality_failure_retains_only_bounded_first_summary():
    kwargs = _kwargs()
    checkpoint = _pass(owner.build_empty_run_004_checkpoint(**kwargs))
    row = owner.get_next_run_004_row(checkpoint, **kwargs)
    checkpoint = owner.record_run_004_completed_call(
        checkpoint, scheduled=row, transport_result=_transport(row, valid=False),
        **kwargs,
    )
    assert len(checkpoint["grading_summaries"]) == 2
    assert checkpoint["quality_gate_status"] == "failed"
    serialized = owner.serialize_run_004_checkpoint(checkpoint, **kwargs)
    assert "normalized_output" not in serialized
    assert "expected_output" not in serialized


@pytest.mark.parametrize("field,value", [
    ("input_token_count", 4097), ("output_token_count", 1025)
])
def test_per_call_token_ceiling_is_terminal(field, value):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    row = owner.get_next_run_004_row(checkpoint, **kwargs)
    result = _transport(row)
    result[field] = value
    checkpoint = owner.record_run_004_completed_call(
        checkpoint, scheduled=row, transport_result=result, **kwargs
    )
    assert checkpoint["stop_reason"] == "token_budget_exceeded"


def test_cumulative_cost_ceiling_stops_second_call():
    kwargs = _kwargs(ceiling="0.000149")
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    checkpoint = _pass(checkpoint, **kwargs)
    row = owner.get_next_run_004_row(checkpoint, **kwargs)
    checkpoint = owner.record_run_004_completed_call(
        checkpoint, scheduled=row, transport_result=_transport(row), **kwargs
    )
    assert checkpoint["stop_reason"] == "cost_ceiling_exceeded"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda result: result.pop("input_token_count"), "missing_usage_metadata"),
        (lambda result: result.update(input_token_count=0), "missing_usage_metadata"),
        (lambda result: result.update(provider="openai"), "provider_model_mismatch"),
        (lambda result: result.update(model="openai/gpt-oss-20b"), "provider_model_mismatch"),
    ],
)
def test_missing_usage_and_provider_model_mismatch_stop_hard(mutation, reason):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    row = owner.get_next_run_004_row(checkpoint, **kwargs)
    result = _transport(row)
    mutation(result)
    checkpoint = owner.record_run_004_completed_call(
        checkpoint, scheduled=row, transport_result=result, **kwargs
    )
    assert checkpoint["stop_reason"] == reason
    assert checkpoint["hard_failure_schedule_keys"] == [row["schedule_key"]]
    assert owner.get_next_run_004_row(checkpoint, **kwargs) is None


@pytest.mark.parametrize("reason", ["fallback_attempted", "retry_attempted"])
def test_fallback_and_retry_attempts_stop_hard(reason):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    row = owner.get_next_run_004_row(checkpoint, **kwargs)
    checkpoint = owner.record_run_004_hard_failure_call(
        checkpoint, scheduled=row, reason=reason, **kwargs
    )
    assert checkpoint["stop_reason"] == reason
    assert checkpoint["hard_failure_schedule_keys"] == [row["schedule_key"]]


def test_replay_terminal_and_prior_state_injection_are_rejected():
    kwargs = _kwargs()
    checkpoint = _pass(_pass(owner.build_empty_run_004_checkpoint(**kwargs)))
    with pytest.raises(ValueError):
        owner.record_run_004_completed_call(
            checkpoint,
            scheduled=checkpoint["schedule"][0],
            transport_result=_transport(checkpoint["schedule"][0]),
            **kwargs,
        )
    prior = deepcopy(checkpoint)
    prior["run_identifier"] = "phase11-groq-canary-003"
    with pytest.raises(ValueError):
        owner.validate_run_004_checkpoint(prior, **kwargs)


@pytest.mark.parametrize("field,value", [
    ("fallback_count", 1), ("retry_count", 1),
    ("raw_response_persisted_count", 1),
])
def test_authority_mutation_attempts_are_rejected(field, value):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    checkpoint["authority_invariants"][field] = value
    with pytest.raises(ValueError):
        owner.validate_run_004_checkpoint(checkpoint, **kwargs)


def _temp_root(tmp_path):
    root = tmp_path / "repo"
    output = root / "outputs/provider_benchmark"
    output.mkdir(parents=True)
    (root / ".gitignore").write_text("outputs/\n")
    return root


def test_checkpoint_and_result_persistence_are_exclusive_atomic_and_0600(tmp_path):
    kwargs = _kwargs()
    root = _temp_root(tmp_path)
    checkpoint_path = root / RUN_004_ARTIFACT_PATHS["checkpoint"]
    result_path = root / RUN_004_ARTIFACT_PATHS["result"]
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    owner.write_initial_run_004_checkpoint(
        checkpoint_path, checkpoint, repository_root=root, **kwargs
    )
    assert stat.S_IMODE(checkpoint_path.stat().st_mode) == 0o600
    prior = owner.run_004_checkpoint_sha256(checkpoint, **kwargs)
    terminal = _pass(_pass(checkpoint))
    owner.replace_run_004_checkpoint_atomic(
        checkpoint_path, terminal, expected_prior_sha256=prior,
        repository_root=root, **kwargs,
    )
    result = owner.build_run_004_result_artifact(
        checkpoint=terminal, **kwargs
    )
    owner.write_run_004_result_exclusive(
        result_path, result, repository_root=root, **kwargs
    )
    assert stat.S_IMODE(result_path.stat().st_mode) == 0o600
    with pytest.raises(ValueError):
        owner.write_run_004_result_exclusive(
            result_path, result, repository_root=root, **kwargs
        )


def test_persistence_rejects_traversal_symlink_and_real_artifacts_remain_absent(tmp_path):
    kwargs = _kwargs()
    root = _temp_root(tmp_path)
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    with pytest.raises(ValueError):
        owner.write_initial_run_004_checkpoint(
            root / "outputs/provider_benchmark/../bad.json",
            checkpoint, repository_root=root, **kwargs,
        )
    symlink = root / "outputs/provider_benchmark/symlink.json"
    symlink.symlink_to(tmp_path / "outside.json")
    with pytest.raises(ValueError):
        owner.write_initial_run_004_checkpoint(
            symlink, checkpoint, repository_root=root, **kwargs,
        )
    assert all(
        not Path(path).exists() for path in RUN_004_ARTIFACT_PATHS.values()
    )


def test_import_and_build_persist_no_generated_or_credential_material():
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_004_checkpoint(**kwargs)
    encoded = json.dumps(checkpoint, sort_keys=True)
    for marker in (
        '"api_key":', '"credential":', '"normalized_output":',
        '"raw_response":', '"request_packet":', '"reasoning":',
    ):
        assert marker not in encoded
    for forbidden_field in ("raw_response", "normalized_output"):
        tampered = deepcopy(checkpoint)
        tampered[forbidden_field] = "must-not-persist"
        with pytest.raises(ValueError):
            owner.validate_run_004_checkpoint(tampered, **kwargs)

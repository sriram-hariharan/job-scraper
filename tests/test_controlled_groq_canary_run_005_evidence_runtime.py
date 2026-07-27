from copy import deepcopy
import json
from pathlib import Path
import stat

import pytest

from src.evaluation import controlled_groq_canary_run_005_evidence_runtime as owner
from src.evaluation.controlled_groq_canary_run_005_identity import (
    RUN_005_ARTIFACT_PATHS,
    build_run_005_authorization_template,
)
from src.evaluation.controlled_groq_provider_canary import (
    build_groq_pricing_template,
    pricing_table_sha256,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


NOW = "2026-07-27T12:00:00Z"


def _pricing():
    pricing = build_groq_pricing_template()
    pricing.update(
        pricing_version="run-005-test-pricing",
        source_classification="operator_test_fixture",
        source_effective_at_utc=NOW,
        valid_from_utc=NOW,
        expires_at_utc="2026-07-28T12:00:00Z",
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
    authorization = build_run_005_authorization_template()
    authorization.update(
        maximum_observed_cost_per_model={
            "groq/openai/gpt-oss-120b": ceiling
        },
        maximum_total_observed_cost=ceiling,
        pricing_table_sha256=pricing["pricing_table_sha256"],
        valid_from_utc=NOW,
        expires_at_utc="2026-07-28T12:00:00Z",
        operator_approved=True,
        live_execution_authorized=True,
    )
    return authorization


def _kwargs(*, ceiling="0.0025"):
    return {
        "authorization": _authorization(ceiling=ceiling),
        "pricing": _pricing(),
        "execution_at_utc": NOW,
    }


def _empty(**kwargs):
    return owner.build_empty_run_005_checkpoint(**(_kwargs() | kwargs))


def _case():
    return next(
        row
        for row in load_fixture_case_corpus()["cases"]
        if row["workload_id"] == "tailoring_generation"
    )


def _transport(row, *, mutate=None, input_tokens=100, output_tokens=100):
    output = deepcopy(_case()["expected_output"])
    if mutate is not None:
        mutate(output)
    return {
        "normalized_output": output,
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "latency_ms": 10.0,
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "provider_outcome_category": "success",
    }


def _record(checkpoint, *, mutate=None, input_tokens=100, output_tokens=100, **kwargs):
    arguments = _kwargs() | kwargs
    row = owner.get_next_run_005_row(checkpoint, **arguments)
    return owner.record_run_005_completed_call(
        checkpoint,
        scheduled=row,
        transport_result=_transport(
            row,
            mutate=mutate,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
        **arguments,
    )


def test_empty_checkpoint_has_one_deterministic_pending_row():
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_005_checkpoint(**kwargs)
    row = owner.get_next_run_005_row(checkpoint, **kwargs)

    assert row["workload_id"] == "tailoring_generation"
    assert checkpoint["aggregate_usage"]["provider_call_count"] == 0
    assert checkpoint["quality_gate_status"] == "pending"
    assert len(checkpoint["schedule"]) == 1


def test_quality_pass_completes_with_bounded_diagnostics():
    kwargs = _kwargs()
    checkpoint = _record(owner.build_empty_run_005_checkpoint(**kwargs))
    summary = checkpoint["grading_summaries"][0]

    assert checkpoint["stop_reason"] == "completed"
    assert checkpoint["quality_gate_status"] == "passed"
    assert owner.get_next_run_005_row(checkpoint, **kwargs) is None
    assert summary["tailoring_diagnostics"] == {
        "suggestion_count": 1,
        "unsupported_claim_count": 0,
        "unsupported_source_id_count": 0,
        "human_review_required_passed": True,
        "authority_preserved": True,
        "required_field_completeness": 1.0,
        "tailoring_failure_codes": [],
    }
    result = owner.build_run_005_result_artifact(
        checkpoint=checkpoint,
        **kwargs,
    )
    assert result["final_status"] == "completed"
    assert result["cost_comparison_eligibility"] is True


@pytest.mark.parametrize(
    ("mutation", "code", "field", "expected"),
    [
        (
            lambda output: output.update(suggestions=[]),
            "suggestions_empty",
            "suggestion_count",
            0,
        ),
        (
            lambda output: output["suggestions"][0]["claims"].append(
                "unsupported_test_claim"
            ),
            "unsupported_claim",
            "unsupported_claim_count",
            1,
        ),
        (
            lambda output: output["suggestions"][0].update(
                source_bullet_id="unsupported_test_source"
            ),
            "unsupported_source_bullet_id",
            "unsupported_source_id_count",
            1,
        ),
        (
            lambda output: output.update(human_review_required=False),
            "human_review_required_false",
            "human_review_required_passed",
            False,
        ),
        (
            lambda output: output.update(authority_mutated=True),
            "deterministic_authority_not_preserved",
            "authority_preserved",
            False,
        ),
    ],
)
def test_each_diagnostic_failure_code_persists_without_content(
    mutation,
    code,
    field,
    expected,
):
    checkpoint = _record(_empty(), mutate=mutation)
    summary = checkpoint["grading_summaries"][0]
    encoded = json.dumps(summary, sort_keys=True)

    assert checkpoint["stop_reason"] == "hard_safety_failure"
    assert summary["quality_gate_passed"] is False
    assert summary["tailoring_diagnostics"][field] == expected
    assert code in summary["tailoring_diagnostics"]["tailoring_failure_codes"]
    for marker in (
        '"suggestions":',
        '"claims":',
        '"source_bullet_id":',
        '"normalized_output":',
        "unsupported_test_claim",
        "unsupported_test_source",
    ):
        assert marker not in encoded


def test_multiple_diagnostic_failures_are_exact_sorted_and_unique():
    def mutate(output):
        output["suggestions"][0]["claims"].append("unsupported_test_claim")
        output["suggestions"][0]["source_bullet_id"] = "unsupported_test_source"
        output["human_review_required"] = False
        output["authority_mutated"] = True

    checkpoint = _record(_empty(), mutate=mutate)
    diagnostics = checkpoint["grading_summaries"][0][
        "tailoring_diagnostics"
    ]

    assert diagnostics["tailoring_failure_codes"] == sorted(
        {
            "unsupported_claim",
            "unsupported_source_bullet_id",
            "human_review_required_false",
            "deterministic_authority_not_preserved",
        }
    )


@pytest.mark.parametrize("kind", ["blocked", "ambiguous", "hard"])
def test_transport_and_safety_terminal_states_are_one_call_only(kind):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_005_checkpoint(**kwargs)
    row = owner.get_next_run_005_row(checkpoint, **kwargs)
    if kind == "blocked":
        checkpoint = owner.record_run_005_blocked_call(
            checkpoint,
            scheduled=row,
            **kwargs,
        )
    elif kind == "ambiguous":
        checkpoint = owner.record_run_005_ambiguous_call(
            checkpoint,
            scheduled=row,
            **kwargs,
        )
    else:
        checkpoint = owner.record_run_005_hard_failure_call(
            checkpoint,
            scheduled=row,
            reason="retry_attempted",
            **kwargs,
        )

    assert checkpoint["aggregate_usage"]["provider_call_count"] == 1
    assert owner.get_next_run_005_row(checkpoint, **kwargs) is None
    result = owner.build_run_005_result_artifact(
        checkpoint=checkpoint,
        **kwargs,
    )
    expected = {
        "blocked": "stopped_blocked",
        "ambiguous": "stopped_ambiguous",
        "hard": "stopped_hard_failure",
    }
    assert result["final_status"] == expected[kind]


@pytest.mark.parametrize(
    ("field", "value"),
    [("input_token_count", 4097), ("output_token_count", 1025)],
)
def test_token_ceilings_stop_hard(field, value):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_005_checkpoint(**kwargs)
    row = owner.get_next_run_005_row(checkpoint, **kwargs)
    result = _transport(row)
    result[field] = value

    checkpoint = owner.record_run_005_completed_call(
        checkpoint,
        scheduled=row,
        transport_result=result,
        **kwargs,
    )

    assert checkpoint["stop_reason"] == "token_budget_exceeded"


def test_cost_ceiling_stops_hard():
    kwargs = _kwargs(ceiling="0.00001")
    checkpoint = _record(
        owner.build_empty_run_005_checkpoint(**kwargs),
        **kwargs,
    )

    assert checkpoint["stop_reason"] == "cost_ceiling_exceeded"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda result: result.pop("input_token_count"),
            "missing_usage_metadata",
        ),
        (
            lambda result: result.update(input_token_count=0),
            "missing_usage_metadata",
        ),
        (
            lambda result: result.update(provider="openai"),
            "provider_model_mismatch",
        ),
        (
            lambda result: result.update(model="openai/gpt-oss-20b"),
            "provider_model_mismatch",
        ),
    ],
)
def test_missing_usage_and_provider_model_mismatch_stop_hard(mutation, reason):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_005_checkpoint(**kwargs)
    row = owner.get_next_run_005_row(checkpoint, **kwargs)
    result = _transport(row)
    mutation(result)

    checkpoint = owner.record_run_005_completed_call(
        checkpoint,
        scheduled=row,
        transport_result=result,
        **kwargs,
    )

    assert checkpoint["stop_reason"] == reason
    assert owner.get_next_run_005_row(checkpoint, **kwargs) is None


@pytest.mark.parametrize("reason", ["fallback_attempted", "retry_attempted"])
def test_retry_and_fallback_attempts_stop_hard(reason):
    kwargs = _kwargs()
    checkpoint = owner.build_empty_run_005_checkpoint(**kwargs)
    row = owner.get_next_run_005_row(checkpoint, **kwargs)

    checkpoint = owner.record_run_005_hard_failure_call(
        checkpoint,
        scheduled=row,
        reason=reason,
        **kwargs,
    )

    assert checkpoint["stop_reason"] == reason


def test_replay_terminal_resume_prior_state_and_prohibited_evidence_are_rejected():
    kwargs = _kwargs()
    checkpoint = _record(owner.build_empty_run_005_checkpoint(**kwargs))
    row = checkpoint["schedule"][0]
    with pytest.raises(ValueError):
        owner.record_run_005_completed_call(
            checkpoint,
            scheduled=row,
            transport_result=_transport(row),
            **kwargs,
        )
    prior = deepcopy(checkpoint)
    prior["run_identifier"] = "phase11-groq-canary-004"
    with pytest.raises(ValueError):
        owner.validate_run_005_checkpoint(prior, **kwargs)
    prohibited = deepcopy(checkpoint)
    prohibited["normalized_output"] = {}
    with pytest.raises(ValueError):
        owner.validate_run_005_checkpoint(prohibited, **kwargs)


def _temp_root(tmp_path):
    root = tmp_path / "repo"
    output = root / "outputs/provider_benchmark"
    output.mkdir(parents=True)
    (root / ".gitignore").write_text("outputs/\n")
    return root


def test_checkpoint_and_result_persistence_are_exclusive_atomic_and_0600(tmp_path):
    kwargs = _kwargs()
    root = _temp_root(tmp_path)
    checkpoint_path = root / RUN_005_ARTIFACT_PATHS["checkpoint"]
    result_path = root / RUN_005_ARTIFACT_PATHS["result"]
    checkpoint = owner.build_empty_run_005_checkpoint(**kwargs)
    owner.write_initial_run_005_checkpoint(
        checkpoint_path,
        checkpoint,
        repository_root=root,
        **kwargs,
    )
    assert stat.S_IMODE(checkpoint_path.stat().st_mode) == 0o600
    prior_sha = owner.run_005_checkpoint_sha256(checkpoint, **kwargs)
    terminal = _record(checkpoint)
    owner.replace_run_005_checkpoint_atomic(
        checkpoint_path,
        terminal,
        expected_prior_sha256=prior_sha,
        repository_root=root,
        **kwargs,
    )
    result = owner.build_run_005_result_artifact(
        checkpoint=terminal,
        **kwargs,
    )
    owner.write_run_005_result_exclusive(
        result_path,
        result,
        repository_root=root,
        **kwargs,
    )
    assert stat.S_IMODE(result_path.stat().st_mode) == 0o600
    with pytest.raises(ValueError):
        owner.write_run_005_result_exclusive(
            result_path,
            result,
            repository_root=root,
            **kwargs,
        )


def test_persistence_rejects_traversal_symlink_and_real_artifacts_stay_absent(
    tmp_path,
):
    kwargs = _kwargs()
    root = _temp_root(tmp_path)
    checkpoint = owner.build_empty_run_005_checkpoint(**kwargs)
    with pytest.raises(ValueError):
        owner.write_initial_run_005_checkpoint(
            root / "outputs/provider_benchmark/../bad.json",
            checkpoint,
            repository_root=root,
            **kwargs,
        )
    symlink = root / RUN_005_ARTIFACT_PATHS["checkpoint"]
    symlink.symlink_to(tmp_path / "outside.json")
    with pytest.raises(ValueError):
        owner.write_initial_run_005_checkpoint(
            symlink,
            checkpoint,
            repository_root=root,
            **kwargs,
        )
    assert all(
        not Path(path).exists() for path in RUN_005_ARTIFACT_PATHS.values()
    )

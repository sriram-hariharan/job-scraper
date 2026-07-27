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

import pytest

from src.evaluation import controlled_groq_canary_run_003_evidence_runtime as owner
from src.evaluation import controlled_groq_canary_run_003_identity as identity
from src.evaluation import controlled_groq_canary_run_003_plan as plan
from src.evaluation import controlled_groq_canary_run_003_transport as transport
from src.evaluation import controlled_groq_canary_transport as base_transport
from src.evaluation import controlled_groq_canary_evidence_runtime as base_runtime
from src.evaluation import controlled_groq_canary_run_identity as run_002
from src.evaluation.controlled_groq_provider_canary import (
    pricing_table_sha256,
)
from src.evaluation.provider_fixture_benchmark import (
    load_fixture_case_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT
    / "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py"
)
EXECUTION_TIME = "2026-07-26T10:00:00Z"
PLAN_SHA = (
    "5d63ef8bc8749645c19211184e8b7be16aa1909fbdb8a3682b9073af7270e9e8"
)
IDENTITY_SHA = (
    "db22f2add4075775747f3c90de89977f82f918adc655eda1f343ab5aeed44980"
)
AUTHORIZATION_TEMPLATE_SHA = (
    "7e899596ab1b47c7ffbb692e68ecf4b5739415009c15791904a06388b4270b4a"
)
BASE_TRANSPORT_SHA = (
    "e27ad7f7eccf67837cde2b940c448042953abe16749378b0f353d6e503180209"
)
RUN_002_IDENTITY_SHA = (
    "e1c7159d42daebe64ad2c8ddea5f0bb40b45c0ff1cd56111e980a52585685fef"
)
SCHEDULE_KEY = (
    "canary_run_003_"
    "0ba1bf8c9270b5bbe777b6a27c05342cb906ab2e0e25609714a81dde9cf4fb46"
)
PRIOR_ARTIFACT_SHA256 = {
    "phase11_groq_canary_checkpoint_001.json": (
        "63be65e2db0f6a2877f79d8a8927692175abec949ea596fc5b86f3ae0b7f75ad"
    ),
    "phase11_groq_canary_pricing_002.json": (
        "1ff5154cc369e3b29cca238db78b35d88cf83538f46f04a04a08bc6a4b5823f4"
    ),
    "phase11_groq_canary_authorization_002.json": (
        "a9f8b67bbe48965b669f9f56209ef6ca4127e07fad29377db624adb9cf018133"
    ),
    "phase11_groq_canary_checkpoint_002.json": (
        "2b0f54607b6a818bdadb2e0acada644ee9ded78bfeb7f1808cad7b99b3befe72"
    ),
    "phase11_groq_canary_result_002.json": (
        "09018df2f2a82d565ff46b3f7aacf1867cb801efb7a194e97dd49bbc8f23a9ee"
    ),
}
RUN_003_ARTIFACT_SHA256 = {
    "pricing": "4802ca143f9db7a5891033c045ba9a24898f4bf6c924586ea9619b98720046a8",
    "authorization": "a3d55c8f8c44c92709c6d354b5f01b4f747b72ebd125542b076cecfbc063cba2",
    "checkpoint": "6fced7c4ef08f2bbe19138347db9c31eaa5b483aadf03163331d32b8cb0b2b1f",
    "result": "d9f01c7f699a3389af3fe46cd73f764405a7446102eedf095824bb6865557d07",
}


def _assert_run_003_artifacts_are_immutable():
    for kind, relative_path in identity.RUN_003_ARTIFACT_PATHS.items():
        path = ROOT / relative_path
        assert path.is_file() and not path.is_symlink()
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert sha256(path.read_bytes()).hexdigest() == (
            RUN_003_ARTIFACT_SHA256[kind]
        )


def _pricing():
    path = (
        ROOT
        / "outputs/provider_benchmark"
        / "phase11_groq_canary_pricing_002.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _authorization():
    authorization = identity.build_run_003_authorization_template()
    authorization.update(
        {
            "maximum_observed_cost_per_model": {
                "groq/openai/gpt-oss-120b": "1.00"
            },
            "maximum_total_observed_cost": "1.00",
            "pricing_table_sha256": pricing_table_sha256(_pricing()),
            "valid_from_utc": "2026-07-26T09:30:00Z",
            "expires_at_utc": "2026-07-26T11:00:00Z",
            "operator_approved": True,
            "live_execution_authorized": True,
        }
    )
    return authorization


def _kwargs(authorization=None):
    return {
        "authorization": (
            _authorization() if authorization is None else authorization
        ),
        "pricing": _pricing(),
        "execution_at_utc": EXECUTION_TIME,
    }


def _empty(authorization=None):
    return owner.build_empty_run_003_checkpoint(**_kwargs(authorization))


def _row():
    return plan.build_run_003_plan_contract()["schedule"][0]


def _case():
    return [
        case
        for case in load_fixture_case_corpus()["cases"]
        if case["workload_id"] == "skill_extraction"
    ][0]


def _result(**overrides):
    result = {
        "normalized_output": deepcopy(_case()["expected_output"]),
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "latency_ms": 12.5,
        "input_token_count": 100,
        "output_token_count": 50,
        "provider_outcome_category": "success",
    }
    result.update(overrides)
    return result


def _complete(checkpoint=None, result=None, authorization=None):
    approved = _authorization() if authorization is None else authorization
    return owner.record_run_003_completed_call(
        _empty(approved) if checkpoint is None else checkpoint,
        scheduled=_row(),
        transport_result=_result() if result is None else result,
        **_kwargs(approved),
    )


def _temporary_repository(tmp_path):
    root = tmp_path / "repository"
    root.mkdir(mode=0o700)
    (root / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    output = root / "outputs/provider_benchmark"
    output.mkdir(parents=True, mode=0o700)
    os.chmod(root / "outputs", 0o700)
    os.chmod(output, 0o700)
    return root, output


def test_exact_runtime_and_schema_versions():
    assert owner.RUN_003_EVIDENCE_RUNTIME_VERSION == (
        "controlled-groq-canary-run-003-evidence-runtime-v1"
    )
    assert owner.RUN_003_CHECKPOINT_SCHEMA_VERSION == (
        "controlled-groq-canary-run-003-checkpoint-v1"
    )
    assert owner.RUN_003_RESULT_SCHEMA_VERSION == (
        "controlled-groq-canary-run-003-result-v1"
    )


def test_active_authorization_accepts_exact_operator_scope():
    authorization = _authorization()
    assert owner.validate_run_003_active_authorization(
        authorization,
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    assert authorization["candidate_provider_models"] == [
        {"provider": "groq", "model": "openai/gpt-oss-120b"}
    ]
    assert authorization["approved_schedule_keys"] == [SCHEDULE_KEY]
    assert authorization["approved_case_aliases"] == [
        "case_fb2b069aa9340571b60e1fb5"
    ]
    assert authorization["approved_workloads"] == ["skill_extraction"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("operator_approved", False),
        ("live_execution_authorized", False),
        ("run_identifier", "phase11-groq-canary-004"),
        ("run_003_plan_sha256", "0" * 64),
        ("run_003_identity_sha256", "0" * 64),
        ("approved_schedule_keys", ["canary_run_003_other"]),
        ("approved_case_aliases", ["case_other"]),
        ("approved_workloads", ["jd_intelligence"]),
        (
            "candidate_provider_models",
            [{"provider": "groq", "model": "openai/gpt-oss-20b"}],
        ),
        ("fallback_allowed", True),
        ("retry_count", 1),
        ("gemini_allowed", True),
        ("openai_provider_allowed", True),
        ("production_activation_allowed", True),
        ("mutation_authority_allowed", True),
        ("application_authority_allowed", True),
        ("ats_authority_allowed", True),
        ("run_001_resume_allowed", True),
        ("run_001_key_replay_allowed", True),
        ("run_002_resume_allowed", True),
        ("run_002_key_replay_allowed", True),
    ],
)
def test_active_authorization_rejects_scope_or_authority_mutation(
    field,
    value,
):
    authorization = _authorization()
    authorization[field] = value
    with pytest.raises(ValueError):
        owner.validate_run_003_active_authorization(
            authorization,
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("valid_from_utc", "2026-07-26T10:30:00Z"),
        ("expires_at_utc", "2026-07-26T09:59:59Z"),
        ("pricing_table_sha256", "0" * 64),
        ("maximum_total_observed_cost", "0"),
        ("maximum_total_observed_cost", "-1"),
        (
            "maximum_observed_cost_per_model",
            {"groq/openai/gpt-oss-20b": "1.00"},
        ),
        (
            "maximum_observed_cost_per_model",
            {"groq/openai/gpt-oss-120b": "0.50"},
        ),
    ],
)
def test_active_authorization_rejects_window_pricing_or_ceiling_errors(
    field,
    value,
):
    authorization = _authorization()
    authorization[field] = value
    if field == "maximum_observed_cost_per_model" and "120b" in str(value):
        authorization["maximum_total_observed_cost"] = "1.00"
    with pytest.raises(ValueError):
        owner.validate_run_003_active_authorization(
            authorization,
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )


def test_existing_two_model_groq_pricing_schema_is_reused():
    pricing = _pricing()
    assert [
        (row["provider"], row["model"])
        for row in pricing["prices"]
    ] == [
        ("groq", "openai/gpt-oss-20b"),
        ("groq", "openai/gpt-oss-120b"),
    ]
    assert owner.validate_operator_approved_pricing(
        pricing,
        execution_at_utc=EXECUTION_TIME,
    )


def test_empty_checkpoint_has_exact_one_row_and_bindings():
    checkpoint = _empty()
    assert owner.validate_run_003_checkpoint(checkpoint, **_kwargs())
    assert checkpoint["run_identifier"] == "phase11-groq-canary-003"
    assert checkpoint["run_003_plan_sha256"] == PLAN_SHA
    assert checkpoint["run_003_identity_sha256"] == IDENTITY_SHA
    assert checkpoint["run_003_transport_sha256"] == (
        transport.run_003_transport_sha256()
    )
    assert checkpoint["schedule"] == [_row()]
    assert checkpoint["schedule_keys"] == [SCHEDULE_KEY]
    assert checkpoint["artifact_paths"] == identity.RUN_003_ARTIFACT_PATHS


def test_empty_checkpoint_state_aggregate_and_authority_are_zero():
    checkpoint = _empty()
    for field in (
        "completed_schedule_keys",
        "blocked_schedule_keys",
        "ambiguous_schedule_keys",
        "hard_failure_schedule_keys",
        "grading_summaries",
    ):
        assert checkpoint[field] == []
    assert checkpoint["stop_reason"] is None
    assert checkpoint["quality_gate_status"] == "pending"
    assert checkpoint["aggregate_usage"] == {
        "provider_call_count": 0,
        "input_token_count": 0,
        "output_token_count": 0,
        "latency_ms": 0.0,
        "observed_cost": "0",
        "by_model": {"openai/gpt-oss-120b": 0},
        "by_workload": {"skill_extraction": 0},
        "by_schedule_key": {SCHEDULE_KEY: 0},
    }
    assert all(
        value in {0, False}
        for value in checkpoint["authority_invariants"].values()
    )


def test_next_row_is_exact_and_deep_copy_contained():
    checkpoint = _empty()
    row = owner.get_next_run_003_row(checkpoint, **_kwargs())
    assert row == _row()
    row["model"] = "tampered"
    assert owner.get_next_run_003_row(checkpoint, **_kwargs())["model"] == (
        "openai/gpt-oss-120b"
    )


def test_checkpoint_serialization_and_digest_are_canonical_and_stable():
    checkpoint = _empty()
    serialized = owner.serialize_run_003_checkpoint(
        checkpoint,
        **_kwargs(),
    )
    assert serialized == json.dumps(
        checkpoint,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert owner.run_003_checkpoint_sha256(
        checkpoint,
        **_kwargs(),
    ) == owner.run_003_checkpoint_sha256(deepcopy(checkpoint), **_kwargs())


def test_checkpoint_digest_is_stable_in_fresh_process():
    command = (
        "from tests.test_controlled_groq_canary_run_003_evidence_runtime "
        "import _empty,_kwargs;"
        "from src.evaluation.controlled_groq_canary_run_003_evidence_runtime "
        "import run_003_checkpoint_sha256;"
        "print(run_003_checkpoint_sha256(_empty(),**_kwargs()))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert completed.stderr == ""
    assert completed.stdout.strip() == owner.run_003_checkpoint_sha256(
        _empty(),
        **_kwargs(),
    )


@pytest.mark.parametrize(
    "field",
    [
        "completed_schedule_keys",
        "blocked_schedule_keys",
        "ambiguous_schedule_keys",
        "hard_failure_schedule_keys",
    ],
)
def test_checkpoint_rejects_prior_base_or_unknown_keys(field):
    for bad_key in (
        "canary_run_002_f6a3df4b6caa7e82e229efc59bea7687",
        "canary_6ee9934ebe7f25bd0612d19a12d9923a",
        "canary_run_003_unknown",
    ):
        checkpoint = _empty()
        checkpoint[field] = [bad_key]
        with pytest.raises(ValueError):
            owner.validate_run_003_checkpoint(checkpoint, **_kwargs())


def test_checkpoint_rejects_overlapping_or_multiple_invoked_states():
    checkpoint = _empty()
    checkpoint["blocked_schedule_keys"] = [SCHEDULE_KEY]
    checkpoint["ambiguous_schedule_keys"] = [SCHEDULE_KEY]
    with pytest.raises(ValueError):
        owner.validate_run_003_checkpoint(checkpoint, **_kwargs())


def test_quality_pass_transition_is_terminal_and_bounded():
    original = _empty()
    before = deepcopy(original)
    completed = _complete(original)
    assert original == before
    assert completed["completed_schedule_keys"] == [SCHEDULE_KEY]
    assert completed["stop_reason"] == "completed"
    assert completed["quality_gate_status"] == "passed"
    assert completed["cost_comparison_eligibility"] is True
    assert completed["aggregate_usage"]["provider_call_count"] == 1
    assert completed["aggregate_usage"]["input_token_count"] == 100
    assert completed["aggregate_usage"]["output_token_count"] == 50
    assert completed["grading_summaries"][0][
        "quality_gate_passed"
    ] is True
    assert owner.get_next_run_003_row(completed, **_kwargs()) is None


def test_safe_task_quality_failure_uses_step8x_local_repair():
    result = _result()
    output = deepcopy(result["normalized_output"])
    output["required_skills"] = output["required_skills"][:-1]
    result["normalized_output"] = output
    checkpoint = _complete(result=result)
    assert checkpoint["hard_failure_schedule_keys"] == [SCHEDULE_KEY]
    assert checkpoint["stop_reason"] == "hard_safety_failure"
    assert checkpoint["quality_gate_status"] == "failed"
    assert checkpoint["cost_comparison_eligibility"] is False
    assert checkpoint["grading_summaries"][0]["hard_failures"] == {
        "workload_quality_gate_failed": 1
    }


def test_schema_quality_failure_is_bounded_and_retains_no_output():
    result = _result(normalized_output={})
    checkpoint = _complete(result=result)
    summary = checkpoint["grading_summaries"][0]
    assert checkpoint["hard_failure_schedule_keys"] == [SCHEDULE_KEY]
    assert summary["hard_failures"]["schema_invalid"] == 1
    serialized = owner.serialize_run_003_checkpoint(
        checkpoint,
        **_kwargs(),
    )
    serialized_keys = set(owner._iter_keys(json.loads(serialized)))
    assert "normalized_output" not in serialized_keys
    assert "raw_response" not in serialized_keys


def test_definitive_failure_transition_is_terminal():
    checkpoint = owner.record_run_003_blocked_call(
        _empty(),
        scheduled=_row(),
        **_kwargs(),
    )
    assert checkpoint["blocked_schedule_keys"] == [SCHEDULE_KEY]
    assert checkpoint["stop_reason"] == "definitive_transport_failure"
    assert checkpoint["quality_gate_status"] == "stopped"
    assert owner.get_next_run_003_row(checkpoint, **_kwargs()) is None


@pytest.mark.parametrize(
    "reason",
    ["ambiguous_timeout", "unknown_provider_outcome"],
)
def test_ambiguous_transition_is_terminal(reason):
    checkpoint = owner.record_run_003_ambiguous_call(
        _empty(),
        scheduled=_row(),
        reason=reason,
        **_kwargs(),
    )
    assert checkpoint["ambiguous_schedule_keys"] == [SCHEDULE_KEY]
    assert checkpoint["stop_reason"] == reason
    assert owner.get_next_run_003_row(checkpoint, **_kwargs()) is None


def test_explicit_hard_failure_transition_is_terminal():
    checkpoint = owner.record_run_003_hard_failure_call(
        _empty(),
        scheduled=_row(),
        reason="hard_safety_failure",
        **_kwargs(),
    )
    assert checkpoint["hard_failure_schedule_keys"] == [SCHEDULE_KEY]
    assert checkpoint["stop_reason"] == "hard_safety_failure"
    assert owner.get_next_run_003_row(checkpoint, **_kwargs()) is None


@pytest.mark.parametrize(
    "transition",
    ["completed", "blocked", "ambiguous", "hard"],
)
def test_no_second_transition_or_replay_after_any_terminal_state(transition):
    if transition == "completed":
        checkpoint = _complete()
    elif transition == "blocked":
        checkpoint = owner.record_run_003_blocked_call(
            _empty(), scheduled=_row(), **_kwargs()
        )
    elif transition == "ambiguous":
        checkpoint = owner.record_run_003_ambiguous_call(
            _empty(), scheduled=_row(), **_kwargs()
        )
    else:
        checkpoint = owner.record_run_003_hard_failure_call(
            _empty(), scheduled=_row(), **_kwargs()
        )
    with pytest.raises(ValueError):
        owner.record_run_003_blocked_call(
            checkpoint,
            scheduled=_row(),
            **_kwargs(),
        )


def test_cost_ceiling_is_enforced_as_hard_failure():
    authorization = _authorization()
    authorization["maximum_observed_cost_per_model"] = {
        "groq/openai/gpt-oss-120b": "0.000000001"
    }
    authorization["maximum_total_observed_cost"] = "0.000000001"
    checkpoint = _complete(authorization=authorization)
    assert checkpoint["stop_reason"] == "cost_ceiling_exceeded"
    assert checkpoint["grading_summaries"][0]["hard_failures"][
        "cost_ceiling_exceeded"
    ] == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [("input_token_count", 4097), ("output_token_count", 1025)],
)
def test_token_ceiling_is_enforced_as_hard_failure(field, value):
    checkpoint = _complete(result=_result(**{field: value}))
    assert checkpoint["stop_reason"] == "token_budget_exceeded"
    assert checkpoint["grading_summaries"][0]["hard_failures"][
        "token_budget_exceeded"
    ] == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("input_token_count", 0),
        ("output_token_count", 0),
        ("input_token_count", None),
        ("output_token_count", None),
    ],
)
def test_missing_or_nonpositive_usage_is_rejected(field, value):
    with pytest.raises(ValueError):
        _complete(result=_result(**{field: value}))


@pytest.mark.parametrize(
    ("field", "value"),
    [("provider", "openai"), ("model", "openai/gpt-oss-20b")],
)
def test_provider_or_model_mismatch_is_rejected(field, value):
    with pytest.raises(ValueError):
        _complete(result=_result(**{field: value}))


@pytest.mark.parametrize(
    ("transition", "status"),
    [
        ("completed", "completed"),
        ("blocked", "stopped_blocked"),
        ("ambiguous", "stopped_ambiguous"),
        ("hard", "stopped_hard_failure"),
    ],
)
def test_result_artifact_has_exact_terminal_status(transition, status):
    if transition == "completed":
        checkpoint = _complete()
    elif transition == "blocked":
        checkpoint = owner.record_run_003_blocked_call(
            _empty(), scheduled=_row(), **_kwargs()
        )
    elif transition == "ambiguous":
        checkpoint = owner.record_run_003_ambiguous_call(
            _empty(), scheduled=_row(), **_kwargs()
        )
    else:
        checkpoint = owner.record_run_003_hard_failure_call(
            _empty(), scheduled=_row(), **_kwargs()
        )
    artifact = owner.build_run_003_result_artifact(
        checkpoint=checkpoint,
        **_kwargs(),
    )
    assert artifact["final_status"] == status
    assert owner.validate_run_003_result_artifact(artifact, **_kwargs())
    serialized = owner.serialize_run_003_result_artifact(
        artifact,
        **_kwargs(),
    )
    assert serialized == json.dumps(
        artifact,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert owner.run_003_result_sha256(artifact, **_kwargs())


def test_result_rejects_nonterminal_checkpoint_and_authority_mutation():
    with pytest.raises(ValueError):
        owner.build_run_003_result_artifact(
            checkpoint=_empty(),
            **_kwargs(),
        )
    artifact = owner.build_run_003_result_artifact(
        checkpoint=_complete(),
        **_kwargs(),
    )
    artifact["production_activation"] = True
    with pytest.raises(ValueError):
        owner.validate_run_003_result_artifact(artifact, **_kwargs())


def test_checkpoint_and_result_reject_prohibited_evidence_fields():
    checkpoint = _empty()
    checkpoint["normalized_output"] = {}
    with pytest.raises(ValueError):
        owner.validate_run_003_checkpoint(checkpoint, **_kwargs())
    artifact = owner.build_run_003_result_artifact(
        checkpoint=_complete(),
        **_kwargs(),
    )
    artifact["raw_response"] = {}
    with pytest.raises(ValueError):
        owner.validate_run_003_result_artifact(artifact, **_kwargs())


def test_initial_checkpoint_is_exclusive_and_mode_0600(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "phase11_groq_canary_checkpoint_003.json"
    checkpoint = _empty()
    written = owner.write_initial_run_003_checkpoint(
        path,
        checkpoint,
        repository_root=root,
        **_kwargs(),
    )
    assert written == path
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert owner.load_run_003_checkpoint(
        path,
        repository_root=root,
        **_kwargs(),
    ) == checkpoint
    with pytest.raises(ValueError):
        owner.write_initial_run_003_checkpoint(
            path,
            checkpoint,
            repository_root=root,
            **_kwargs(),
        )


def test_atomic_checkpoint_replacement_requires_prior_digest(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "phase11_groq_canary_checkpoint_003.json"
    initial = _empty()
    owner.write_initial_run_003_checkpoint(
        path,
        initial,
        repository_root=root,
        **_kwargs(),
    )
    blocked = owner.record_run_003_blocked_call(
        initial,
        scheduled=_row(),
        **_kwargs(),
    )
    with pytest.raises(ValueError):
        owner.replace_run_003_checkpoint_atomic(
            path,
            blocked,
            expected_prior_sha256="0" * 64,
            repository_root=root,
            **_kwargs(),
        )
    prior = owner.run_003_checkpoint_sha256(initial, **_kwargs())
    owner.replace_run_003_checkpoint_atomic(
        path,
        blocked,
        expected_prior_sha256=prior,
        repository_root=root,
        **_kwargs(),
    )
    assert owner.load_run_003_checkpoint(
        path,
        repository_root=root,
        **_kwargs(),
    ) == blocked
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_result_write_is_exclusive_and_mode_0600(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "phase11_groq_canary_result_003.json"
    artifact = owner.build_run_003_result_artifact(
        checkpoint=_complete(),
        **_kwargs(),
    )
    owner.write_run_003_result_exclusive(
        path,
        artifact,
        repository_root=root,
        **_kwargs(),
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert owner.load_run_003_result_artifact(
        path,
        repository_root=root,
        **_kwargs(),
    ) == artifact
    with pytest.raises(ValueError):
        owner.write_run_003_result_exclusive(
            path,
            artifact,
            repository_root=root,
            **_kwargs(),
        )


@pytest.mark.parametrize(
    ("kind", "name"),
    [
        ("checkpoint", "phase11_groq_canary_checkpoint_001.json"),
        ("checkpoint", "phase11_groq_canary_checkpoint_002.json"),
        ("result", "phase11_groq_canary_result_002.json"),
        ("checkpoint", "other.json"),
    ],
)
def test_persistence_rejects_prior_run_or_other_paths(tmp_path, kind, name):
    root, output = _temporary_repository(tmp_path)
    path = output / name
    with pytest.raises(ValueError):
        owner._validate_artifact_path(
            path,
            repository_root=root,
            kind=kind,
            require_existing=False,
        )


def test_persistence_rejects_symlink_and_traversal(tmp_path):
    root, output = _temporary_repository(tmp_path)
    real = root / "real"
    real.mkdir()
    output.rmdir()
    output.symlink_to(real, target_is_directory=True)
    checkpoint_path = (
        output / "phase11_groq_canary_checkpoint_003.json"
    )
    with pytest.raises(ValueError):
        owner.write_initial_run_003_checkpoint(
            checkpoint_path,
            _empty(),
            repository_root=root,
            **_kwargs(),
        )
    traversal = (
        root
        / "outputs/provider_benchmark/../"
        / "phase11_groq_canary_checkpoint_003.json"
    )
    with pytest.raises(ValueError):
        owner._validate_artifact_path(
            traversal,
            repository_root=root,
            kind="checkpoint",
            require_existing=False,
        )


def test_pinned_owners_and_prior_artifacts_are_immutable():
    assert plan.run_003_plan_sha256() == PLAN_SHA
    assert identity.run_003_identity_sha256() == IDENTITY_SHA
    assert identity.run_003_authorization_template_sha256() == (
        AUTHORIZATION_TEMPLATE_SHA
    )
    assert base_transport.controlled_groq_transport_sha256() == (
        BASE_TRANSPORT_SHA
    )
    assert run_002.run_identity_sha256() == RUN_002_IDENTITY_SHA
    output = ROOT / "outputs/provider_benchmark"
    for name, digest in PRIOR_ARTIFACT_SHA256.items():
        path = output / name
        assert path.is_file() and not path.is_symlink()
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert sha256(path.read_bytes()).hexdigest() == digest
    assert not (output / "phase11_groq_canary_result_001.json").exists()
    _assert_run_003_artifacts_are_immutable()


def test_base_runtime_public_cost_behavior_is_unchanged():
    cost = base_runtime.calculate_observed_cost(
        pricing=_pricing(),
        provider="groq",
        model="openai/gpt-oss-120b",
        input_token_count=100,
        output_token_count=50,
    )
    assert cost == Decimal("0.000045")


def test_import_has_no_sdk_environment_network_database_process_or_thread():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    roots = set()
    attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(
            node.func, ast.Attribute
        ):
            attributes.add(node.func.attr)
    assert roots.isdisjoint(
        {
            "dotenv",
            "groq",
            "httpx",
            "openai",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "subprocess",
            "threading",
            "urllib",
        }
    )
    assert attributes.isdisjoint(
        {"getenv", "create_connection", "connect", "Popen"}
    )


def test_in_memory_runtime_reaches_no_environment_socket(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("environment or network access prohibited")

    monkeypatch.setattr(os, "getenv", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(socket.socket, "connect", fail)
    checkpoint = _complete()
    artifact = owner.build_run_003_result_artifact(
        checkpoint=checkpoint,
        **_kwargs(),
    )
    assert artifact["final_status"] == "completed"


def test_runtime_persists_no_normalized_raw_or_credential_material():
    checkpoint = _complete()
    artifact = owner.build_run_003_result_artifact(
        checkpoint=checkpoint,
        **_kwargs(),
    )
    keys = set(owner._iter_keys(artifact))
    assert {
        "normalized_output",
        "synthetic_input",
        "request_packet",
        "prompt",
        "raw_response",
        "raw_exception",
        "sdk_object",
        "request_id",
        "headers",
        "reasoning",
        "expected_output",
        "grader_threshold",
        "credential",
        "environment",
    }.isdisjoint(keys)


def test_offline_builds_leave_real_run003_artifacts_immutable():
    _empty()
    _complete()
    _assert_run_003_artifacts_are_immutable()

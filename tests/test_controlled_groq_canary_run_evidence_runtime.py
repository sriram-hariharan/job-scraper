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

from src.evaluation import controlled_groq_canary_run_evidence_runtime as runtime
from src.evaluation import controlled_groq_canary_run_identity as identity
from src.evaluation import controlled_groq_canary_evidence_runtime as v1
from src.evaluation import controlled_groq_provider_canary as canary
from src.evaluation.provider_fixture_benchmark import (
    grade_normalized_candidate_result,
    load_fixture_case_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_canary_run_evidence_runtime.py"
)
PRICING_001 = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_pricing_001.json"
)
AUTHORIZATION_001 = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_authorization_001.json"
)
CHECKPOINT_001 = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_checkpoint_001.json"
)
RESULT_001 = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_result_001.json"
)
EXECUTION_TIME = "2026-07-25T10:40:33Z"
IDENTITY_SHA = (
    "e1c7159d42daebe64ad2c8ddea5f0bb40b45c0ff1cd56111e980a52585685fef"
)
INCIDENT_SHA = (
    "63be65e2db0f6a2877f79d8a8927692175abec949ea596fc5b86f3ae0b7f75ad"
)
RUN_002_ARTIFACT_SHA256 = {
    "pricing": (
        "1ff5154cc369e3b29cca238db78b35d88cf83538f46f04a04a08bc6a4b5823f4"
    ),
    "authorization": (
        "a9f8b67bbe48965b669f9f56209ef6ca4127e07fad29377db624adb9cf018133"
    ),
    "checkpoint": (
        "2b0f54607b6a818bdadb2e0acada644ee9ded78bfeb7f1808cad7b99b3befe72"
    ),
    "result": (
        "09018df2f2a82d565ff46b3f7aacf1867cb801efb7a194e97dd49bbc8f23a9ee"
    ),
}
_PRICING = json.loads(PRICING_001.read_text(encoding="utf-8"))
_BASE_CASES = {
    case["workload_id"]: case
    for case in load_fixture_case_corpus()["cases"]
}


def _pricing():
    return deepcopy(_PRICING)


def _authorization():
    template = identity.build_run_authorization_template()
    template.update(
        {
            "maximum_observed_cost_per_model": {
                "groq/openai/gpt-oss-20b": "0.10",
                "groq/openai/gpt-oss-120b": "0.20",
            },
            "maximum_total_observed_cost": "0.30",
            "pricing_table_sha256": canary.pricing_table_sha256(_pricing()),
            "valid_from_utc": "2026-07-25T10:00:00Z",
            "expires_at_utc": "2026-07-25T11:00:00Z",
            "operator_approved": True,
            "live_execution_authorized": True,
        }
    )
    return template


def _empty():
    return runtime.build_empty_run_checkpoint(
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )


def _result(index=0, *, non_golden=False, **overrides):
    row = identity.build_run_identity_contract()["schedule"][index]
    case = _BASE_CASES[row["workload_id"]]
    normalized = deepcopy(case["expected_output"])
    if non_golden:
        normalized["required_skills"] = normalized["required_skills"][:-1]
    result = {
        "normalized_output": normalized,
        "provider": row["provider"],
        "model": row["model"],
        "latency_ms": 12.5,
        "input_token_count": 11,
        "output_token_count": 7,
        "provider_outcome_category": "success",
    }
    result.update(overrides)
    return result


def _complete(checkpoint, index=0, *, result=None):
    row = identity.build_run_identity_contract()["schedule"][index]
    return runtime.record_completed_call(
        checkpoint,
        scheduled=row,
        transport_result=_result(index) if result is None else result,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
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
    }


def test_versions_identity_and_schedule_are_exact():
    contract = identity.build_run_identity_contract()
    assert runtime.RUN_EVIDENCE_RUNTIME_VERSION == (
        "controlled-groq-canary-run-evidence-runtime-v1"
    )
    assert runtime.RUN_CHECKPOINT_SCHEMA_VERSION == (
        "controlled-groq-canary-run-checkpoint-v1"
    )
    assert runtime.RUN_RESULT_SCHEMA_VERSION == (
        "controlled-groq-canary-run-result-v1"
    )
    assert contract["run_identifier"] == "phase11-groq-canary-002"
    assert identity.run_identity_sha256(contract) == IDENTITY_SHA
    run_keys = [row["run_schedule_key"] for row in contract["schedule"]]
    base_keys = [row["base_schedule_key"] for row in contract["schedule"]]
    assert len(run_keys) == len(set(run_keys)) == 4
    assert set(run_keys).isdisjoint(base_keys)
    assert sum(
        row["model"] == "openai/gpt-oss-20b" for row in contract["schedule"]
    ) == 2
    assert sum(
        row["model"] == "openai/gpt-oss-120b" for row in contract["schedule"]
    ) == 2
    assert all(row["timeout_seconds"] == 30 for row in contract["schedule"])
    assert all(row["fallback"] is False for row in contract["schedule"])
    assert all(row["harness_retry_limit"] == 0 for row in contract["schedule"])
    assert all(row["provider_sdk_retry_limit"] == 0 for row in contract["schedule"])


def test_active_authorization_accepts_only_fixed_active_scope():
    assert runtime.validate_active_run_authorization(
        _authorization(), pricing=_pricing(), execution_at_utc=EXECUTION_TIME
    )
    with pytest.raises(ValueError):
        runtime.validate_active_run_authorization(
            identity.build_run_authorization_template(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"expires_at_utc": "2026-07-25T10:20:00Z"}),
        lambda value: value.update({"valid_from_utc": "2026-07-25T10:50:00Z"}),
        lambda value: value.update({"run_identifier": "phase11-groq-canary-001"}),
        lambda value: value["run_schedule_keys"].__setitem__(0, "base-key"),
        lambda value: value["reserved_artifact_paths"].update(
            {"checkpoint": "outputs/provider_benchmark/phase11_groq_canary_checkpoint_001.json"}
        ),
        lambda value: value.update({"pricing_table_sha256": "0" * 64}),
        lambda value: value["maximum_observed_cost_per_model"].update(
            {"groq/openai/gpt-oss-20b": "0"}
        ),
        lambda value: value.update({"maximum_total_observed_cost": "-1"}),
        lambda value: value.update({"maximum_total_observed_cost": "1.00"}),
        lambda value: value.update({"operator_approved": False}),
        lambda value: value.update({"live_execution_authorized": False}),
        lambda value: value.update({"fallback_allowed": True}),
        lambda value: value.update({"retry_count": 1}),
        lambda value: value.update({"gemini_allowed": True}),
        lambda value: value.update({"openai_provider_allowed": True}),
        lambda value: value.update({"production_activation_allowed": True}),
        lambda value: value.update({"mutation_authority_allowed": True}),
        lambda value: value.update({"application_authority_allowed": True}),
        lambda value: value.update({"ats_authority_allowed": True}),
        lambda value: value.update({"run_001_resume_allowed": True}),
        lambda value: value.update({"run_001_key_replay_allowed": True}),
    ],
)
def test_active_authorization_rejects_scope_or_authority_mutation(mutation):
    authorization = _authorization()
    mutation(authorization)
    with pytest.raises(ValueError):
        runtime.validate_active_run_authorization(
            authorization,
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )


def test_empty_checkpoint_validates_and_owns_only_run_keys():
    checkpoint = _empty()
    assert runtime.validate_run_checkpoint(
        checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    assert checkpoint["run_identity_sha256"] == IDENTITY_SHA
    assert checkpoint["run_schedule_keys"] == [
        row["run_schedule_key"]
        for row in identity.build_run_identity_contract()["schedule"]
    ]
    assert all(checkpoint[field] == [] for field in runtime._STATE_FIELDS)


def test_checkpoint_serialization_digest_and_deep_copy():
    checkpoint = _empty()
    serialized = runtime.serialize_run_checkpoint(
        checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    assert serialized == json.dumps(
        checkpoint, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert runtime.run_checkpoint_sha256(
        checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    ) == sha256(serialized.encode("utf-8")).hexdigest()
    checkpoint["completed_schedule_keys"].append("tamper")
    assert _empty()["completed_schedule_keys"] == []


def test_checkpoint_digest_is_stable_across_fresh_process():
    script = (
        "import json;from pathlib import Path;"
        "from src.evaluation import controlled_groq_canary_run_evidence_runtime as r;"
        "from src.evaluation import controlled_groq_canary_run_identity as i;"
        "from src.evaluation.controlled_groq_provider_canary import pricing_table_sha256;"
        "p=json.loads(Path('outputs/provider_benchmark/phase11_groq_canary_pricing_001.json').read_text());"
        "a=i.build_run_authorization_template();"
        "a.update({'maximum_observed_cost_per_model':{'groq/openai/gpt-oss-20b':'0.10','groq/openai/gpt-oss-120b':'0.20'},'maximum_total_observed_cost':'0.30','pricing_table_sha256':pricing_table_sha256(p),'valid_from_utc':'2026-07-25T10:00:00Z','expires_at_utc':'2026-07-25T11:00:00Z','operator_approved':True,'live_execution_authorized':True});"
        f"c=r.build_empty_run_checkpoint(authorization=a,pricing=p,execution_at_utc='{EXECUTION_TIME}');"
        f"print(r.run_checkpoint_sha256(c,authorization=a,pricing=p,execution_at_utc='{EXECUTION_TIME}'))"
    )
    observed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT)},
    ).stdout.strip()
    assert observed == runtime.run_checkpoint_sha256(
        _empty(),
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )


def test_base_key_duplicate_and_reordered_rows_are_rejected():
    checkpoint = _empty()
    base_key = identity.build_run_identity_contract()["schedule"][0][
        "base_schedule_key"
    ]
    checkpoint["completed_schedule_keys"] = [base_key]
    with pytest.raises(ValueError):
        runtime.validate_run_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )
    checkpoint = _empty()
    run_key = checkpoint["run_schedule_keys"][0]
    checkpoint["completed_schedule_keys"] = [run_key, run_key]
    with pytest.raises(ValueError):
        runtime.validate_run_checkpoint(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )
    with pytest.raises(ValueError, match="exact next"):
        runtime.record_blocked_call(
            _empty(),
            scheduled=identity.build_run_identity_contract()["schedule"][1],
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )


def test_exact_golden_four_call_run_completes_and_reconciles():
    checkpoint = _complete_all()
    assert len(checkpoint["completed_schedule_keys"]) == 4
    assert checkpoint["stop_reason"] == "completed"
    assert checkpoint["quality_gate_status"] == "passed"
    assert checkpoint["aggregate_usage"]["provider_call_count"] == 4
    assert checkpoint["aggregate_usage"]["by_model"] == {
        "openai/gpt-oss-20b": 2,
        "openai/gpt-oss-120b": 2,
    }
    assert checkpoint["aggregate_usage"]["input_token_count"] == 44
    assert checkpoint["aggregate_usage"]["output_token_count"] == 28
    assert checkpoint["aggregate_usage"]["latency_ms"] == 50.0
    assert set(checkpoint["aggregate_usage"]["by_schedule_key"]) == set(
        checkpoint["run_schedule_keys"]
    )
    artifact = runtime.build_run_result_artifact(
        checkpoint=checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    assert artifact["final_status"] == "completed"
    with pytest.raises(ValueError):
        runtime.get_next_run_row(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )


def test_safe_non_golden_quality_failure_reuses_step8x_behavior():
    row = identity.build_run_identity_contract()["schedule"][0]
    result = _result(non_golden=True)
    case = _BASE_CASES["skill_extraction"]
    projection = {
        "case_id": case["case_id"],
        "workload_id": row["workload_id"],
        "provider": row["provider"],
        "model": row["model"],
        "normalized_output": deepcopy(result["normalized_output"]),
        "schema_valid": True,
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
    }
    grade = grade_normalized_candidate_result(
        projection, corpus=load_fixture_case_corpus()
    )
    assert grade["quality_gate_passed"] is False
    assert all(value == 0 for value in grade["hard_failures"].values())
    original = _empty()
    before = deepcopy(original)
    checkpoint = _complete(original, result=result)
    assert original == before
    assert checkpoint["hard_failure_schedule_keys"] == [
        row["run_schedule_key"]
    ]
    assert checkpoint["completed_schedule_keys"] == []
    assert checkpoint["blocked_schedule_keys"] == []
    assert checkpoint["ambiguous_schedule_keys"] == []
    summary = checkpoint["grading_summaries"][0]
    assert summary["hard_failures"] == {"workload_quality_gate_failed": 1}
    assert summary["quality_gate_passed"] is False
    assert checkpoint["stop_reason"] == "hard_safety_failure"
    assert checkpoint["aggregate_usage"]["provider_call_count"] == 1
    assert checkpoint["aggregate_usage"]["input_token_count"] == 11
    assert checkpoint["aggregate_usage"]["output_token_count"] == 7
    assert checkpoint["aggregate_usage"]["latency_ms"] == 12.5
    expected_cost = runtime.calculate_observed_cost(
        pricing=_pricing(),
        provider=row["provider"],
        model=row["model"],
        input_token_count=11,
        output_token_count=7,
    )
    assert Decimal(checkpoint["aggregate_usage"]["observed_cost"]) == expected_cost


@pytest.mark.parametrize("state", ["blocked", "ambiguous", "hard"])
def test_terminal_transitions_remain_terminal(state):
    checkpoint = _empty()
    row = identity.build_run_identity_contract()["schedule"][0]
    kwargs = {
        "scheduled": row,
        "authorization": _authorization(),
        "pricing": _pricing(),
        "execution_at_utc": EXECUTION_TIME,
    }
    if state == "blocked":
        checkpoint = runtime.record_blocked_call(checkpoint, **kwargs)
        assert checkpoint["blocked_schedule_keys"] == [row["run_schedule_key"]]
    elif state == "ambiguous":
        checkpoint = runtime.record_ambiguous_call(checkpoint, **kwargs)
        assert checkpoint["ambiguous_schedule_keys"] == [row["run_schedule_key"]]
    else:
        checkpoint = runtime.record_hard_failure_call(checkpoint, **kwargs)
        assert checkpoint["hard_failure_schedule_keys"] == [row["run_schedule_key"]]
    with pytest.raises(ValueError, match="cannot resume"):
        runtime.get_next_run_row(
            checkpoint,
            authorization=_authorization(),
            pricing=_pricing(),
            execution_at_utc=EXECUTION_TIME,
        )
    artifact = runtime.build_run_result_artifact(
        checkpoint=checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    assert artifact["final_status"].startswith("stopped_")


def test_checkpoint_persistence_and_atomic_replacement(tmp_path):
    root, output = _temporary_repository(tmp_path)
    checkpoint_path = output / "phase11_groq_canary_checkpoint_002.json"
    kwargs = _persistence_kwargs(root)
    initial = _empty()
    runtime.write_initial_run_checkpoint(checkpoint_path, initial, **kwargs)
    assert stat.S_IMODE(checkpoint_path.stat().st_mode) == 0o600
    prior = runtime.run_checkpoint_sha256(
        initial,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    updated = _complete(initial)
    runtime.replace_run_checkpoint_atomic(
        checkpoint_path,
        updated,
        expected_prior_sha256=prior,
        **kwargs,
    )
    assert runtime.load_run_checkpoint(checkpoint_path, **kwargs) == updated
    with pytest.raises(ValueError, match="prior digest"):
        runtime.replace_run_checkpoint_atomic(
            checkpoint_path,
            updated,
            expected_prior_sha256="0" * 64,
            **kwargs,
        )


def test_persistence_rejects_overwrite_symlink_traversal_and_malformed(tmp_path):
    root, output = _temporary_repository(tmp_path)
    path = output / "phase11_groq_canary_checkpoint_002.json"
    kwargs = _persistence_kwargs(root)
    runtime.write_initial_run_checkpoint(path, _empty(), **kwargs)
    with pytest.raises(ValueError, match="overwrite"):
        runtime.write_initial_run_checkpoint(path, _empty(), **kwargs)
    path.unlink()
    target = output / "target.json"
    target.write_text("{}", encoding="utf-8")
    path.symlink_to(target)
    with pytest.raises(ValueError):
        runtime.write_initial_run_checkpoint(path, _empty(), **kwargs)
    path.unlink()
    with pytest.raises(ValueError):
        runtime.write_initial_run_checkpoint(
            output / "../provider_benchmark/phase11_groq_canary_checkpoint_002.json",
            _empty(),
            **kwargs,
        )
    path.write_text("{malformed", encoding="utf-8")
    path.chmod(0o600)
    with pytest.raises(ValueError, match="malformed"):
        runtime.load_run_checkpoint(path, **kwargs)


def test_atomic_failure_cleans_temporary_file(tmp_path, monkeypatch):
    root, output = _temporary_repository(tmp_path)
    path = output / "phase11_groq_canary_checkpoint_002.json"
    kwargs = _persistence_kwargs(root)
    initial = _empty()
    runtime.write_initial_run_checkpoint(path, initial, **kwargs)
    prior = runtime.run_checkpoint_sha256(
        initial,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )

    def fail_replace(_source, _destination):
        raise OSError("synthetic replacement failure")

    monkeypatch.setattr(runtime.os, "replace", fail_replace)
    with pytest.raises(OSError):
        runtime.replace_run_checkpoint_atomic(
            path,
            _complete(initial),
            expected_prior_sha256=prior,
            **kwargs,
        )
    assert list(output.glob("*.tmp")) == []
    assert list(output.glob(".*.tmp")) == []


def test_completed_result_persistence_and_retention(tmp_path):
    root, output = _temporary_repository(tmp_path)
    checkpoint = _complete_all()
    artifact = runtime.build_run_result_artifact(
        checkpoint=checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    result_path = output / "phase11_groq_canary_result_002.json"
    kwargs = _persistence_kwargs(root)
    runtime.write_run_result_exclusive(result_path, artifact, **kwargs)
    assert stat.S_IMODE(result_path.stat().st_mode) == 0o600
    assert runtime.load_run_result_artifact(result_path, **kwargs) == artifact
    with pytest.raises(ValueError, match="overwrite"):
        runtime.write_run_result_exclusive(result_path, artifact, **kwargs)
    serialized = runtime.serialize_run_result_artifact(
        artifact,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )
    keys = set(runtime._iter_keys(json.loads(serialized)))
    for prohibited in runtime._PROHIBITED_EVIDENCE_KEYS:
        assert prohibited not in keys


def test_exact_artifact_paths_reject_run001_and_other_json(tmp_path):
    root, output = _temporary_repository(tmp_path)
    kwargs = _persistence_kwargs(root)
    for name in (
        "phase11_groq_canary_checkpoint_001.json",
        "phase11_groq_canary_result_001.json",
        "phase11_groq_canary_pricing_002.json",
        "phase11_groq_canary_authorization_002.json",
        "arbitrary.json",
    ):
        with pytest.raises(ValueError):
            runtime.write_initial_run_checkpoint(
                output / name, _empty(), **kwargs
            )


def test_module_build_validate_reaches_no_environment_or_socket(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("external boundary reached")

    monkeypatch.setattr(os, "getenv", blocked)
    monkeypatch.setattr(socket, "socket", blocked)
    checkpoint = _empty()
    assert runtime.validate_run_checkpoint(
        checkpoint,
        authorization=_authorization(),
        pricing=_pricing(),
        execution_at_utc=EXECUTION_TIME,
    )


def test_owner_imports_no_sdk_dotenv_network_database_process_or_thread():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Attribute):
            attributes.add(node.attr)
    assert imports.isdisjoint(
        {
            "groq",
            "dotenv",
            "socket",
            "requests",
            "httpx",
            "psycopg",
            "sqlalchemy",
            "subprocess",
            "threading",
        }
    )
    assert attributes.isdisjoint({"environ", "getenv"})


def test_no_production_source_imports_run_evidence_runtime():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_groq_canary_run_evidence_runtime" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())
    assert references == []


def test_incident_and_real_run002_artifacts_remain_protected():
    before = CHECKPOINT_001.read_bytes()
    assert sha256(before).hexdigest() == INCIDENT_SHA
    assert stat.S_IMODE(CHECKPOINT_001.stat().st_mode) == 0o600
    pricing = json.loads(PRICING_001.read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION_001.read_text(encoding="utf-8"))
    incident = v1.load_checkpoint(
        CHECKPOINT_001,
        repository_root=ROOT,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
        canary=canary.build_controlled_groq_canary_contract(),
    )
    assert incident == v1.build_empty_checkpoint(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
        canary=canary.build_controlled_groq_canary_contract(),
    )
    assert CHECKPOINT_001.read_bytes() == before
    assert not RESULT_001.exists()
    for kind, relative_path in identity.RUN_002_ARTIFACT_PATHS.items():
        path = ROOT / relative_path
        assert path.is_file() and not path.is_symlink()
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert sha256(path.read_bytes()).hexdigest() == (
            RUN_002_ARTIFACT_SHA256[kind]
        )
    assert not (ROOT / canary.RECOVERY_006_STATUS_PATH).exists()

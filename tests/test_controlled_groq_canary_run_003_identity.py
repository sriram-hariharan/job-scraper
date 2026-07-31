from __future__ import annotations

import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from src.evaluation import controlled_groq_canary_run_003_identity as owner
from src.evaluation import controlled_groq_canary_run_003_plan as plan_owner
from src.evaluation import controlled_groq_canary_run_identity as run_002
from src.evaluation import controlled_groq_provider_canary as canary
from src.evaluation import controlled_provider_benchmark_plan as base_plan


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_canary_run_003_identity.py"
)
PLAN_SHA = (
    "5d63ef8bc8749645c19211184e8b7be16aa1909fbdb8a3682b9073af7270e9e8"
)
SCHEDULE_KEY = (
    "canary_run_003_"
    "0ba1bf8c9270b5bbe777b6a27c05342cb906ab2e0e25609714a81dde9cf4fb46"
)
BASE_PLAN_SHA = (
    "a3ef53ff992a2d1daf43f8fa9b0556202268d34e21f7611eb5de4d26e9abe6b6"
)
BASE_CANARY_SHA = (
    "43241c341fe4d69c8cbeb2d6e95b6c56e68e67134b693c91396a932775a673bf"
)
RUN_002_IDENTITY_SHA = (
    "e1c7159d42daebe64ad2c8ddea5f0bb40b45c0ff1cd56111e980a52585685fef"
)
def _assert_run_003_artifacts_are_absent():
    assert all(
        not (ROOT / relative_path).exists()
        for relative_path in owner.RUN_003_ARTIFACT_PATHS.values()
    )


def _identity():
    return owner.build_run_003_identity_contract()


def _authorization():
    return owner.build_run_003_authorization_template()


def _set_path(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


def test_exact_constants_and_artifact_paths():
    assert owner.RUN_003_IDENTITY_VERSION == (
        "controlled-groq-canary-run-003-identity-v1"
    )
    assert owner.RUN_003_AUTHORIZATION_TEMPLATE_VERSION == (
        "controlled-groq-canary-run-003-authorization-template-v1"
    )
    assert owner.RUN_003_IDENTIFIER == "phase11-groq-canary-003"
    assert owner.PLACEHOLDER == "OPERATOR_INPUT_REQUIRED"
    assert owner.RUN_003_ARTIFACT_PATHS == {
        "pricing": (
            "outputs/provider_benchmark/"
            "phase11_groq_canary_pricing_003.json"
        ),
        "authorization": (
            "outputs/provider_benchmark/"
            "phase11_groq_canary_authorization_003.json"
        ),
        "checkpoint": (
            "outputs/provider_benchmark/"
            "phase11_groq_canary_checkpoint_003.json"
        ),
        "result": (
            "outputs/provider_benchmark/"
            "phase11_groq_canary_result_003.json"
        ),
    }


def test_identity_has_exact_fields_and_contract_kind():
    contract = _identity()
    assert set(contract) == {
        "run_003_identity_version",
        "run_identifier",
        "contract_kind",
        "run_003_plan_version",
        "run_003_plan_sha256",
        "target_case_alias",
        "target_workload",
        "target_provider",
        "target_model",
        "schedule",
        "request_bounds",
        "token_bounds",
        "stop_policy",
        "future_artifact_identities",
        "protected_prior_artifacts",
        "authority_invariants",
    }
    assert contract["contract_kind"] == (
        "offline-run-003-one-call-groq-120b-skill-extraction-identity"
    )


def test_identity_is_deterministic_canonical_and_deep_copy_contained():
    first = _identity()
    second = _identity()
    assert first == second
    assert owner.validate_run_003_identity_contract(first)
    assert owner.serialize_run_003_identity_contract(first) == json.dumps(
        first,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert owner.run_003_identity_sha256(first) == (
        owner.run_003_identity_sha256(second)
    )
    first["schedule"][0]["model"] = "tampered"
    assert _identity()["schedule"][0]["model"] == "openai/gpt-oss-120b"


def test_identity_digest_is_stable_in_fresh_process():
    command = (
        "from src.evaluation.controlled_groq_canary_run_003_identity "
        "import run_003_identity_sha256;"
        "print(run_003_identity_sha256())"
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
    assert completed.stdout.strip() == owner.run_003_identity_sha256()


def test_identity_binds_exact_plan_digest_and_version():
    contract = _identity()
    plan = plan_owner.build_run_003_plan_contract()
    assert contract["run_003_plan_version"] == (
        plan_owner.RUN_003_PLAN_VERSION
    )
    assert contract["run_003_plan_sha256"] == PLAN_SHA
    assert plan_owner.run_003_plan_sha256(plan) == PLAN_SHA


def test_identity_schedule_is_exact_plan_row_without_new_key():
    contract = _identity()
    plan = plan_owner.build_run_003_plan_contract()
    assert len(contract["schedule"]) == 1
    assert contract["schedule"] == plan["schedule"]
    assert contract["schedule"][0]["schedule_key"] == SCHEDULE_KEY


def test_identity_target_is_exact():
    contract = _identity()
    assert {
        "case_alias": contract["target_case_alias"],
        "workload": contract["target_workload"],
        "provider": contract["target_provider"],
        "model": contract["target_model"],
    } == {
        "case_alias": "case_fb2b069aa9340571b60e1fb5",
        "workload": "skill_extraction",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }


def test_request_token_and_stop_policy_are_exact_plan_bindings():
    identity = _identity()
    plan = plan_owner.build_run_003_plan_contract()
    assert identity["request_bounds"] == plan["request_bounds"]
    assert identity["request_bounds"]["maximum_total_requests"] == 1
    assert identity["token_bounds"] == plan["token_bounds"]
    assert identity["token_bounds"][
        "maximum_input_tokens_per_request"
    ] == 4096
    assert identity["token_bounds"][
        "maximum_output_tokens_per_request"
    ] == 1024
    assert identity["stop_policy"] == plan["stop_policy"]
    assert identity["stop_policy"]["stop_after_one_outcome"] is True
    assert identity["stop_policy"]["harness_retry_limit"] == 0


def test_run003_artifact_paths_are_exact_without_runtime_prerequisites():
    contract = _identity()
    assert contract["future_artifact_identities"] == (
        owner.RUN_003_ARTIFACT_PATHS
    )
    _assert_run_003_artifacts_are_absent()


def test_prior_run_artifact_paths_are_exact():
    protected = _identity()["protected_prior_artifacts"]
    assert protected["run_001"]["artifact_paths"] == (
        owner.PROTECTED_RUN_001_ARTIFACT_PATHS
    )
    assert protected["run_002"]["artifact_paths"] == (
        owner.PROTECTED_RUN_002_ARTIFACT_PATHS
    )
    assert all("_001.json" in path for path in protected["run_001"][
        "artifact_paths"
    ].values())
    assert all("_002.json" in path for path in protected["run_002"][
        "artifact_paths"
    ].values())


def test_prior_runs_cannot_resume_replay_write_or_seed_run003():
    protected = _identity()["protected_prior_artifacts"]
    assert protected["run_001"] == {
        "artifact_paths": owner.PROTECTED_RUN_001_ARTIFACT_PATHS,
        "resume_allowed": False,
        "key_replay_allowed": False,
        "writes_allowed": False,
    }
    assert protected["run_002"] == {
        "artifact_paths": owner.PROTECTED_RUN_002_ARTIFACT_PATHS,
        "resume_allowed": False,
        "key_replay_allowed": False,
        "writes_allowed": False,
        "checkpoint_as_run_003_initial_state_allowed": False,
        "result_as_run_003_initial_state_allowed": False,
    }


def test_identity_authority_is_exactly_default_off():
    assert _identity()["authority_invariants"] == {
        "identity_only": True,
        "live_execution_authorized": False,
        "provider_calls_allowed": False,
        "full_benchmark_authorized": False,
        "fallback_allowed": False,
        "retry_count": 0,
        "openai_provider_allowed": False,
        "gemini_allowed": False,
        "winner_selected": False,
        "routing_change_allowed": False,
        "production_activation": False,
        "mutation_authority_allowed": False,
        "application_authority_allowed": False,
        "ats_authority_allowed": False,
        "run_001_resume_allowed": False,
        "run_001_key_replay_allowed": False,
        "run_002_resume_allowed": False,
        "run_002_key_replay_allowed": False,
    }


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("run_identifier",), "phase11-groq-canary-004"),
        (("run_003_plan_sha256",), "0" * 64),
        (("target_case_alias",), "case_other"),
        (("target_workload",), "jd_intelligence"),
        (("target_provider",), "openai"),
        (("target_model",), "openai/gpt-oss-20b"),
        (("schedule", 0, "schedule_key"), "canary_run_003_other"),
        (("schedule", 0, "model"), "openai/gpt-oss-20b"),
        (("request_bounds", "maximum_total_requests"), 2),
        (("token_bounds", "maximum_aggregate_output_tokens"), 2048),
        (("stop_policy", "fallback"), True),
        (("authority_invariants", "provider_calls_allowed"), True),
        (("authority_invariants", "retry_count"), 1),
        (("authority_invariants", "production_activation"), True),
        (("protected_prior_artifacts", "run_001", "resume_allowed"), True),
        (("protected_prior_artifacts", "run_002", "key_replay_allowed"), True),
    ],
)
def test_identity_mutation_is_rejected(path, replacement):
    contract = _identity()
    _set_path(contract, path, replacement)
    with pytest.raises(ValueError):
        owner.validate_run_003_identity_contract(contract)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "api_key",
        "credential",
        "raw_response",
        "normalized_output",
        "prompt",
        "reasoning",
        "request_id",
        "route",
        "winner",
        "selected_model",
    ],
)
def test_identity_rejects_forbidden_fields(forbidden_key):
    contract = _identity()
    contract[forbidden_key] = "forbidden"
    with pytest.raises(ValueError):
        owner.validate_run_003_identity_contract(contract)


def test_authorization_template_has_exact_fields_and_bindings():
    template = _authorization()
    assert len(template) == 32
    assert template["authorization_template_version"] == (
        owner.RUN_003_AUTHORIZATION_TEMPLATE_VERSION
    )
    assert template["run_003_identity_version"] == (
        owner.RUN_003_IDENTITY_VERSION
    )
    assert template["run_identifier"] == owner.RUN_003_IDENTIFIER
    assert template["run_003_identity_sha256"] == (
        owner.run_003_identity_sha256()
    )
    assert template["run_003_plan_version"] == (
        plan_owner.RUN_003_PLAN_VERSION
    )
    assert template["run_003_plan_sha256"] == PLAN_SHA


def test_authorization_has_one_exact_candidate_and_no_20b_entry():
    template = _authorization()
    assert template["candidate_provider_models"] == [
        {"provider": "groq", "model": "openai/gpt-oss-120b"}
    ]
    assert template["maximum_observed_cost_per_model"] == {
        "groq/openai/gpt-oss-120b": owner.PLACEHOLDER
    }
    assert "gpt-oss-20b" not in owner.serialize_run_003_authorization_template(
        template
    )


def test_authorization_has_one_exact_key_case_and_workload():
    template = _authorization()
    assert template["approved_schedule_keys"] == [SCHEDULE_KEY]
    assert template["approved_case_aliases"] == [
        "case_fb2b069aa9340571b60e1fb5"
    ]
    assert template["approved_workloads"] == ["skill_extraction"]


def test_authorization_binds_bounds_and_reserved_paths():
    template = _authorization()
    identity = _identity()
    assert template["request_bounds"] == identity["request_bounds"]
    assert template["token_ceilings"] == identity["token_bounds"]
    assert template["reserved_artifact_paths"] == (
        owner.RUN_003_ARTIFACT_PATHS
    )


def test_authorization_operator_placeholders_exist_only_in_five_fields():
    template = _authorization()
    placeholder_paths = []

    def walk(value, path=()):
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, (*path, key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, (*path, index))
        elif value == owner.PLACEHOLDER:
            placeholder_paths.append(path)

    walk(template)
    assert placeholder_paths == [
        (
            "maximum_observed_cost_per_model",
            "groq/openai/gpt-oss-120b",
        ),
        ("maximum_total_observed_cost",),
        ("pricing_table_sha256",),
        ("valid_from_utc",),
        ("expires_at_utc",),
    ]


def test_authorization_is_inactive_and_has_zero_external_authority():
    template = _authorization()
    assert template["operator_approved"] is False
    assert template["live_execution_authorized"] is False
    assert template["fallback_allowed"] is False
    assert template["retry_count"] == 0
    for key in (
        "gemini_allowed",
        "openai_provider_allowed",
        "production_activation_allowed",
        "mutation_authority_allowed",
        "application_authority_allowed",
        "ats_authority_allowed",
        "run_001_resume_allowed",
        "run_001_key_replay_allowed",
        "run_002_resume_allowed",
        "run_002_key_replay_allowed",
    ):
        assert template[key] is False


def test_authorization_is_deterministic_canonical_and_deep_copy_contained():
    first = _authorization()
    second = _authorization()
    assert first == second
    assert owner.validate_run_003_authorization_template(first)
    assert owner.serialize_run_003_authorization_template(first) == json.dumps(
        first,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert owner.run_003_authorization_template_sha256(first) == (
        owner.run_003_authorization_template_sha256(second)
    )
    first["candidate_provider_models"][0]["model"] = "tampered"
    assert _authorization()["candidate_provider_models"][0]["model"] == (
        "openai/gpt-oss-120b"
    )


def test_authorization_digest_is_stable_in_fresh_process():
    command = (
        "from src.evaluation.controlled_groq_canary_run_003_identity "
        "import run_003_authorization_template_sha256;"
        "print(run_003_authorization_template_sha256())"
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
    assert completed.stdout.strip() == (
        owner.run_003_authorization_template_sha256()
    )


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("operator_approved",), True),
        (("live_execution_authorized",), True),
        (("fallback_allowed",), True),
        (("retry_count",), 1),
        (("candidate_provider_models", 0, "model"), "openai/gpt-oss-20b"),
        (("approved_schedule_keys", 0), "canary_run_003_other"),
        (("approved_case_aliases", 0), "case_other"),
        (("approved_workloads", 0), "tailoring_generation"),
        (("maximum_total_observed_cost",), "0.10"),
        (("pricing_table_sha256",), "a" * 64),
        (("valid_from_utc",), "2026-07-26T00:00:00Z"),
        (("expires_at_utc",), "2026-07-26T01:00:00Z"),
        (("gemini_allowed",), True),
        (("openai_provider_allowed",), True),
        (("production_activation_allowed",), True),
        (("mutation_authority_allowed",), True),
        (("application_authority_allowed",), True),
        (("ats_authority_allowed",), True),
        (("run_001_resume_allowed",), True),
        (("run_001_key_replay_allowed",), True),
        (("run_002_resume_allowed",), True),
        (("run_002_key_replay_allowed",), True),
    ],
)
def test_authorization_mutation_is_rejected(path, replacement):
    template = _authorization()
    _set_path(template, path, replacement)
    with pytest.raises(ValueError):
        owner.validate_run_003_authorization_template(template)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "api_key",
        "credential",
        "raw_response",
        "normalized_output",
        "prompt",
        "reasoning",
        "request_id",
        "route",
        "winner",
        "selected_model",
    ],
)
def test_authorization_rejects_forbidden_fields(forbidden_key):
    template = _authorization()
    template[forbidden_key] = "forbidden"
    with pytest.raises(ValueError):
        owner.validate_run_003_authorization_template(template)


def test_pinned_plan_controlled_plan_canary_and_run002_identity_are_immutable():
    plan = plan_owner.build_run_003_plan_contract()
    assert plan_owner.run_003_plan_sha256(plan) == PLAN_SHA
    assert plan["controlled_plan_sha256"] == BASE_PLAN_SHA
    assert base_plan.controlled_provider_benchmark_plan_sha256() == (
        BASE_PLAN_SHA
    )
    assert canary.controlled_groq_canary_sha256() == BASE_CANARY_SHA
    assert run_002.run_identity_sha256() == RUN_002_IDENTITY_SHA


def test_prior_and_run003_runtime_artifacts_are_not_test_prerequisites():
    output_root = ROOT / "outputs/provider_benchmark"
    assert not output_root.exists()
    _assert_run_003_artifacts_are_absent()


def test_owner_imports_no_environment_sdk_network_database_or_write_reach():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    imported_roots = set()
    called_names = set()
    called_attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_attributes.add(node.func.attr)
    assert imported_roots.isdisjoint(
        {
            "asyncio",
            "boto3",
            "dotenv",
            "groq",
            "httpx",
            "openai",
            "os",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "subprocess",
            "threading",
            "urllib",
        }
    )
    assert called_names.isdisjoint(
        {"open", "Popen", "run", "system", "Thread", "Process"}
    )
    assert called_attributes.isdisjoint(
        {
            "connect",
            "create_connection",
            "getenv",
            "unlink",
            "write_bytes",
            "write_text",
        }
    )


def test_build_validate_and_hash_reach_no_environment_socket_or_write(
    monkeypatch,
):
    def fail(*_args, **_kwargs):
        raise AssertionError("forbidden environment, network, or write access")

    monkeypatch.setattr(os, "getenv", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(socket.socket, "connect", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    identity = _identity()
    template = _authorization()
    assert owner.validate_run_003_identity_contract(identity)
    assert owner.validate_run_003_authorization_template(template)
    assert owner.run_003_identity_sha256(identity)
    assert owner.run_003_authorization_template_sha256(template)


def test_import_and_build_create_no_real_artifacts():
    before = {
        path: path.read_bytes()
        for path in (
            ROOT / "outputs/provider_benchmark"
        ).glob("phase11_groq_canary_*_00[12].json")
    }
    command = (
        "from src.evaluation.controlled_groq_canary_run_003_identity "
        "import build_run_003_identity_contract,"
        "build_run_003_authorization_template;"
        "build_run_003_identity_contract();"
        "build_run_003_authorization_template()"
    )
    subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    after = {path: path.read_bytes() for path in before}
    assert after == before
    _assert_run_003_artifacts_are_absent()


def test_only_exact_run003_runtime_owners_import_run003_identity_owner():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_groq_canary_run_003_identity" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())
    assert references == [
        "src/evaluation/controlled_groq_canary_run_003_transport.py",
        "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py",
    ]

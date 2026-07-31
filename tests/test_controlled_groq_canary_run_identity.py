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

from src.evaluation import controlled_groq_canary_run_identity as identity
from src.evaluation import controlled_groq_canary_evidence_runtime as evidence
from src.evaluation import controlled_groq_canary_transport as transport
from src.evaluation import controlled_groq_provider_canary as canary


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_canary_run_identity.py"
)
PRICING_001 = (
    ROOT
    / "tests/fixtures/provider_benchmark"
    / "hermetic_groq_canary_pricing.json"
)
EXECUTION_TIME = "2026-07-25T10:40:33Z"
CANARY_SHA256 = (
    "43241c341fe4d69c8cbeb2d6e95b6c56e68e67134b693c91396a932775a673bf"
)
TRANSPORT_SHA256 = (
    "e27ad7f7eccf67837cde2b940c448042953abe16749378b0f353d6e503180209"
)
def _contract():
    return identity.build_run_identity_contract()


def _template():
    return identity.build_run_authorization_template()


def _pricing():
    return json.loads(PRICING_001.read_text(encoding="utf-8"))


def _base_authorization():
    authorization = canary.build_operator_authorization_template()
    authorization.update(
        {
            "maximum_observed_cost_per_model": {
                "groq/openai/gpt-oss-20b": "0.10",
                "groq/openai/gpt-oss-120b": "0.20",
            },
            "maximum_total_observed_cost": "0.30",
            "valid_from_utc": "2026-01-01T00:00:00Z",
            "expires_at_utc": "2027-01-01T00:00:00Z",
            "pricing_table_sha256": canary.pricing_table_sha256(_pricing()),
            "operator_approved": True,
        }
    )
    return authorization


def test_versions_and_run_identifier_are_exact():
    assert identity.RUN_IDENTITY_VERSION == (
        "controlled-groq-canary-run-identity-v1"
    )
    assert identity.RUN_IDENTIFIER == "phase11-groq-canary-002"
    assert identity.AUTHORIZATION_TEMPLATE_VERSION == (
        "controlled-groq-canary-run-authorization-template-v1"
    )
    assert canary.CANARY_VERSION == "controlled-groq-provider-canary-v1"
    assert transport.TRANSPORT_VERSION == "controlled-groq-canary-transport-v1"
    assert evidence.EVIDENCE_RUNTIME_VERSION == (
        "controlled-groq-canary-evidence-runtime-v1"
    )


def test_pinned_v1_digests_and_schedule_are_consumed_unchanged():
    base = canary.build_controlled_groq_canary_contract()
    contract = _contract()
    assert canary.controlled_groq_canary_sha256(base) == CANARY_SHA256
    assert transport.controlled_groq_transport_sha256() == TRANSPORT_SHA256
    assert contract["base_canary_sha256"] == CANARY_SHA256
    assert contract["transport_sha256"] == TRANSPORT_SHA256
    assert len(contract["schedule"]) == len(base["schedule"]) == 4
    for run_row, base_row in zip(contract["schedule"], base["schedule"]):
        assert {
            key: run_row[key]
            for key in (
                "execution_order",
                "case_alias",
                "workload_id",
                "provider",
                "model",
                "timeout_seconds",
                "fallback",
                "harness_retry_limit",
                "provider_sdk_retry_limit",
            )
        } == {
            key: base_row[key]
            for key in (
                "execution_order",
                "case_alias",
                "workload_id",
                "provider",
                "model",
                "timeout_seconds",
                "fallback",
                "harness_retry_limit",
                "provider_sdk_retry_limit",
            )
        }
        assert run_row["base_schedule_key"] == base_row["schedule_key"]


def test_fresh_schedule_keys_are_deterministic_unique_and_not_base_keys():
    first = _contract()
    second = _contract()
    run_keys = [row["run_schedule_key"] for row in first["schedule"]]
    base_keys = {
        row["schedule_key"]
        for row in canary.build_controlled_groq_canary_contract()["schedule"]
    }
    assert run_keys == [
        row["run_schedule_key"] for row in second["schedule"]
    ]
    assert len(run_keys) == len(set(run_keys)) == 4
    assert set(run_keys).isdisjoint(base_keys)
    assert run_keys[0] not in base_keys


def test_schedule_bounds_and_model_assignments_remain_exact():
    contract = _contract()
    rows = contract["schedule"]
    assert [row["execution_order"] for row in rows] == [1, 2, 3, 4]
    assert sum(row["model"] == "openai/gpt-oss-20b" for row in rows) == 2
    assert sum(row["model"] == "openai/gpt-oss-120b" for row in rows) == 2
    assert all(row["provider"] == "groq" for row in rows)
    assert all(row["timeout_seconds"] == 30 for row in rows)
    assert all(row["fallback"] is False for row in rows)
    assert all(row["harness_retry_limit"] == 0 for row in rows)
    assert all(row["provider_sdk_retry_limit"] == 0 for row in rows)
    assert contract["request_bounds"]["serial_concurrency"] == 1
    assert contract["request_bounds"]["maximum_requests_per_case"] == 1


def test_reserved_artifact_paths_are_exact_without_runtime_prerequisites():
    assert _contract()["future_artifact_identities"] == {
        "pricing": (
            "outputs/provider_benchmark/phase11_groq_canary_pricing_002.json"
        ),
        "authorization": (
            "outputs/provider_benchmark/"
            "phase11_groq_canary_authorization_002.json"
        ),
        "checkpoint": (
            "outputs/provider_benchmark/"
            "phase11_groq_canary_checkpoint_002.json"
        ),
        "result": (
            "outputs/provider_benchmark/phase11_groq_canary_result_002.json"
        ),
    }
    assert all(
        not (ROOT / relative_path).exists()
        for relative_path in identity.RUN_002_ARTIFACT_PATHS.values()
    )


def test_empty_checkpoint_contract_is_hermetic_and_valid():
    assert "outputs/" in (ROOT / ".gitignore").read_text(encoding="utf-8")
    pricing = _pricing()
    authorization = _base_authorization()
    checkpoint = evidence.build_empty_checkpoint(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
        canary=canary.build_controlled_groq_canary_contract(),
    )
    assert checkpoint == evidence.build_empty_checkpoint(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
        canary=canary.build_controlled_groq_canary_contract(),
    )
    assert evidence.validate_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
        canary=canary.build_controlled_groq_canary_contract(),
    )


def test_authorization_template_is_placeholder_only_and_inactive():
    template = _template()
    placeholder_fields = (
        "maximum_total_observed_cost",
        "pricing_table_sha256",
        "valid_from_utc",
        "expires_at_utc",
    )
    assert all(
        template[field] == identity.PLACEHOLDER
        for field in placeholder_fields
    )
    assert set(template["maximum_observed_cost_per_model"].values()) == {
        identity.PLACEHOLDER
    }
    for field in (
        "operator_approved",
        "fallback_allowed",
        "gemini_allowed",
        "openai_provider_allowed",
        "live_execution_authorized",
        "production_activation_allowed",
        "mutation_authority_allowed",
        "application_authority_allowed",
        "ats_authority_allowed",
        "run_001_resume_allowed",
        "run_001_key_replay_allowed",
    ):
        assert template[field] is False
    assert template["retry_count"] == 0


def test_serialization_is_canonical_and_builders_are_deep_copy_contained():
    contract = _contract()
    serialized = identity.serialize_run_identity_contract(contract)
    assert serialized == json.dumps(
        contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    first = _contract()
    first["schedule"][0]["run_schedule_key"] = "tampered"
    assert _contract()["schedule"][0]["run_schedule_key"] != "tampered"
    template = _template()
    serialized_template = identity.serialize_run_authorization_template(template)
    assert serialized_template == json.dumps(
        template, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def test_digests_are_stable_across_fresh_process():
    script = (
        "from src.evaluation import controlled_groq_canary_run_identity as i;"
        "print(i.run_identity_sha256());"
        "print(i.run_authorization_template_sha256())"
    )
    observed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT)},
    ).stdout.splitlines()
    assert observed == [
        identity.run_identity_sha256(),
        identity.run_authorization_template_sha256(),
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"unknown": False}),
        lambda value: value.pop("run_identifier"),
        lambda value: value.update({"run_identifier": "run-001"}),
        lambda value: value["schedule"].reverse(),
        lambda value: value["schedule"][1].update(
            {"run_schedule_key": value["schedule"][0]["run_schedule_key"]}
        ),
        lambda value: value["schedule"][0].update({"fallback": True}),
        lambda value: value["schedule"][0].update({"harness_retry_limit": 1}),
        lambda value: value["schedule"][0].update({"provider": "openai"}),
        lambda value: value["schedule"][0].update({"model": "gemini"}),
        lambda value: value["future_artifact_identities"].update(
            {"checkpoint": "outputs/provider_benchmark/wildcard_*.json"}
        ),
        lambda value: value["authority_invariants"].update(
            {"live_execution_authorized": True}
        ),
        lambda value: value.update({"winner": "model"}),
    ],
)
def test_malformed_or_escalated_identity_contracts_are_rejected(mutation):
    contract = _contract()
    mutation(contract)
    with pytest.raises(ValueError):
        identity.validate_run_identity_contract(contract)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"unknown": False}),
        lambda value: value.pop("operator_approved"),
        lambda value: value.update({"operator_approved": True}),
        lambda value: value.update({"retry_count": 1}),
        lambda value: value.update({"fallback_allowed": True}),
        lambda value: value.update({"openai_provider_allowed": True}),
        lambda value: value.update({"gemini_allowed": True}),
        lambda value: value["reserved_artifact_paths"].update(
            {"result": "outputs/provider_benchmark/result_001.json"}
        ),
        lambda value: value.update({"selected_model": "model"}),
    ],
)
def test_malformed_or_active_authorization_templates_are_rejected(mutation):
    template = _template()
    mutation(template)
    with pytest.raises(ValueError):
        identity.validate_run_authorization_template(template)


def test_owner_has_no_environment_sdk_network_database_or_write_reach():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    calls = set()
    attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
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
    assert calls.isdisjoint(
        {
            "Groq",
            "Client",
            "connect",
            "Popen",
            "Thread",
            "open",
            "write_bytes",
            "write_text",
        }
    )


def test_building_and_validating_reaches_no_environment_or_socket(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("external boundary reached")

    monkeypatch.setattr(os, "getenv", blocked)
    monkeypatch.setattr(socket, "socket", blocked)
    contract = _contract()
    template = _template()
    assert identity.validate_run_identity_contract(contract)
    assert identity.validate_run_authorization_template(template)


def test_no_production_source_imports_run_identity_owner():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_groq_canary_run_identity" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())
    assert references == [
        "src/evaluation/controlled_groq_canary_run_evidence_runtime.py"
    ]

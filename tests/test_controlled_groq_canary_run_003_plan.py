from __future__ import annotations

import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.evaluation import controlled_groq_canary_run_003_plan as owner
from src.evaluation import controlled_groq_canary_run_identity as run_002
from src.evaluation import controlled_groq_provider_canary as canary
from src.evaluation import controlled_provider_benchmark_plan as base_plan
from src.evaluation import provider_fixture_benchmark as step8o
from src.evaluation.provider_benchmark_contract import (
    build_provider_benchmark_contract,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_canary_run_003_plan.py"
)
BASE_PLAN_SHA = (
    "a3ef53ff992a2d1daf43f8fa9b0556202268d34e21f7611eb5de4d26e9abe6b6"
)
BASE_BENCHMARK_SHA = (
    "ba4e817f4e82f9df967011709a42bc7d2f22998f176f555cfee9dfc9e0071b98"
)
CORPUS_SHA = (
    "0ddc82e62745856c0d5d4d3f0efbe3fc86bd4e84e5da070f54f4ea635e74b05c"
)
STEP8O_SHA = (
    "7a6463fc465d963633f82a18de0b067daab31dc387680b1d004e706c61a55c15"
)
def _contract():
    return owner.build_run_003_plan_contract()


def _packet():
    return owner.build_run_003_transmittable_request_packet()


def _case_and_review():
    corpus = step8o.load_fixture_case_corpus()
    plan = base_plan.build_controlled_provider_benchmark_plan(corpus=corpus)
    matches = [
        (review, case)
        for review, case in zip(plan["transmission_review"], corpus["cases"])
        if review["case_alias"] == owner.CURRENT_TARGET_CASE_ALIAS
    ]
    assert len(matches) == 1
    return matches[0]


def test_exact_constants_and_base_digests():
    assert owner.RUN_003_PLAN_VERSION == "controlled-groq-canary-run-003-plan-v1"
    assert owner.RUN_003_IDENTIFIER == "phase11-groq-canary-003"
    assert owner.RUN_003_CONTRACT_KIND == (
        "offline-one-call-groq-120b-skill-extraction-follow-up-plan"
    )
    contract = _contract()
    assert contract["benchmark_contract_sha256"] == BASE_BENCHMARK_SHA
    assert contract["controlled_plan_sha256"] == BASE_PLAN_SHA
    assert contract["fixture_corpus_sha256"] == CORPUS_SHA
    assert contract["step8o_engine_sha256"] == STEP8O_SHA


def test_contract_is_deterministic_canonical_and_deep_copy_contained():
    first = _contract()
    second = _contract()
    assert first == second
    assert owner.validate_run_003_plan_contract(first)
    serialized = owner.serialize_run_003_plan_contract(first)
    assert serialized == json.dumps(
        first,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = owner.run_003_plan_sha256(first)
    assert digest == owner.run_003_plan_sha256(second)
    first["schedule"][0]["model"] = "tampered"
    assert _contract()["schedule"][0]["model"] == owner.TARGET_MODEL


def test_digest_is_stable_in_a_fresh_process():
    command = (
        "from src.evaluation.controlled_groq_canary_run_003_plan "
        "import run_003_plan_sha256;"
        "print(run_003_plan_sha256())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    assert completed.stderr == ""
    assert completed.stdout.strip() == owner.run_003_plan_sha256()


def test_exact_one_row_schedule_and_fresh_key():
    contract = _contract()
    assert len(contract["schedule"]) == 1
    row = contract["schedule"][0]
    assert row == {
        "execution_order": 1,
        "case_alias": owner.TARGET_CASE_ALIAS,
        "workload_id": "skill_extraction",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "timeout_seconds": 30,
        "fallback": False,
        "harness_retry_limit": 0,
        "provider_sdk_retry_limit": 0,
        "schedule_key": row["schedule_key"],
    }
    assert row["schedule_key"].startswith("canary_run_003_")
    prior_keys = {
        item["schedule_key"]
        for item in canary.build_controlled_groq_canary_contract()["schedule"]
    } | {
        item["run_schedule_key"]
        for item in run_002.build_run_identity_contract()["schedule"]
    }
    assert row["schedule_key"] not in prior_keys


def test_target_is_exactly_one_eligible_synthetic_case():
    review, case = _case_and_review()
    assert review["case_alias"] == "case_eff6ed2fb3643d23b87bab48"
    assert review["workload_id"] == "skill_extraction"
    assert review["wholly_synthetic"] is True
    assert review["eligible_for_later_controlled_transmission"] is True
    assert review["requires_additional_redaction"] is False
    assert review["eligibility_reasons"] == []
    assert case["case_id"] == "skill_extraction_required_preferred_v1"
    assert case["workload_id"] == "skill_extraction"
    assert case["schema_id"] == "skill_extraction_result_v1"
    assert case["sanitized_classification"] == "synthetic_sanitized"
    assert case["contains_personal_resume_content"] is False
    assert case["additional_redaction_required"] is False


def test_target_candidate_is_owned_by_committed_benchmark():
    benchmark = build_provider_benchmark_contract()
    assert ("groq", "openai/gpt-oss-120b") in {
        (row["provider"], row["model"])
        for row in benchmark["candidate_definitions"]
    }


def test_request_token_stop_and_authority_bounds_are_exact():
    contract = _contract()
    assert contract["request_bounds"] == {
        "maximum_total_requests": 1,
        "maximum_requests_per_provider_model": 1,
        "maximum_requests_per_case": 1,
        "serial_concurrency": 1,
        "automatic_expansion": False,
        "conditional_additional_calls": False,
    }
    assert contract["token_bounds"] == {
        "maximum_input_tokens_per_request": 4096,
        "maximum_output_tokens_per_request": 1024,
        "maximum_aggregate_input_tokens": 4096,
        "maximum_aggregate_output_tokens": 1024,
        "observed_usage_required": True,
        "missing_usage_estimation_allowed": False,
    }
    assert contract["stop_policy"]["timeout_seconds"] == 30
    assert contract["stop_policy"]["harness_retry_limit"] == 0
    assert contract["stop_policy"]["provider_sdk_retry_limit"] == 0
    assert contract["stop_policy"]["fallback"] is False
    authority = contract["authority_invariants"]
    assert all(
        value is False
        for value in authority.values()
        if isinstance(value, bool)
    )
    assert all(
        value == 0
        for value in authority.values()
        if isinstance(value, int) and not isinstance(value, bool)
    )


def test_transmission_safety_assertions_are_fail_closed():
    assertions = _contract()["transmission_safety_assertions"]
    assert assertions["wholly_synthetic"] is True
    assert assertions["eligible_for_controlled_transmission"] is True
    assert assertions["requires_additional_redaction"] is False
    assert assertions["synthetic_input_only"] is True
    assert assertions["expected_output_transmission_allowed"] is False
    assert assertions["golden_output_transmission_allowed"] is False
    assert assertions["provenance_transmission_allowed"] is False
    assert all(
        value is False
        for key, value in assertions.items()
        if key.startswith("contains_")
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"extra": True}),
        lambda value: value.pop("contract_kind"),
        lambda value: value.update({"target_case_alias": "other"}),
        lambda value: value.update({"target_workload": "jd_intelligence"}),
        lambda value: value.update({"target_provider": "openai"}),
        lambda value: value.update({"target_model": "openai/gpt-oss-20b"}),
        lambda value: value["schedule"].append(deepcopy(value["schedule"][0])),
        lambda value: value["schedule"][0].update({"schedule_key": "changed"}),
        lambda value: value["schedule"][0].update({"timeout_seconds": 31}),
        lambda value: value["schedule"][0].update({"fallback": True}),
        lambda value: value["schedule"][0].update({"harness_retry_limit": 1}),
        lambda value: value["authority_invariants"].update(
            {"production_activation": True}
        ),
        lambda value: value.update({"selected_model": "unsafe"}),
    ],
)
def test_contract_mutation_is_rejected(mutation):
    contract = _contract()
    mutation(contract)
    with pytest.raises(ValueError):
        owner.validate_run_003_plan_contract(contract)


def test_packet_has_exact_fields_and_default_off_bounds():
    packet = _packet()
    assert set(packet) == {
        "benchmark_contract_version",
        "run_plan_version",
        "case_alias",
        "workload_id",
        "provider",
        "model",
        "synthetic_input",
        "output_schema",
        "temperature",
        "maximum_completion_tokens",
        "timeout_seconds",
        "fallback",
        "live_execution_requested",
    }
    assert packet["case_alias"] == owner.TARGET_CASE_ALIAS
    assert packet["workload_id"] == "skill_extraction"
    assert packet["provider"] == "groq"
    assert packet["model"] == "openai/gpt-oss-120b"
    assert packet["temperature"] == 0
    assert packet["maximum_completion_tokens"] == 1024
    assert packet["timeout_seconds"] == 30
    assert packet["fallback"] is False
    assert packet["live_execution_requested"] is False
    assert owner.validate_run_003_transmittable_request_packet(packet)


def test_packet_copies_only_committed_input_and_schema():
    _review, case = _case_and_review()
    packet = _packet()
    assert packet["synthetic_input"] == case["normalized_input_packet"]
    assert packet["output_schema"] == {
        "schema_id": case["schema_id"],
        "required_fields": case["required_fields"],
    }
    serialized = json.dumps(packet, sort_keys=True).lower()
    for prohibited in (
        "expected_output",
        "golden",
        "provenance",
        "grader",
        "threshold",
        "credential",
        "request_id",
        "repository_path",
        "resume_content",
        "application_state",
        "ats_state",
        "winner",
        "route",
    ):
        assert prohibited not in serialized


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"extra": True}),
        lambda value: value.pop("output_schema"),
        lambda value: value.update({"case_alias": "other"}),
        lambda value: value.update({"workload_id": "jd_intelligence"}),
        lambda value: value.update({"model": "openai/gpt-oss-20b"}),
        lambda value: value.update({"provider": "openai"}),
        lambda value: value.update({"provider": "gemini"}),
        lambda value: value.update({"model": "another-groq-model"}),
        lambda value: value["synthetic_input"].update({"tampered": True}),
        lambda value: value["output_schema"].update({"schema_id": "changed"}),
        lambda value: value.update({"live_execution_requested": True}),
        lambda value: value.update({"fallback": True}),
        lambda value: value.update({"retry_count": 1}),
    ],
)
def test_packet_mutation_is_rejected(mutation):
    packet = _packet()
    mutation(packet)
    with pytest.raises(ValueError):
        owner.validate_run_003_transmittable_request_packet(packet)


def test_builder_rejects_live_execution_request():
    with pytest.raises(ValueError, match="default off"):
        owner.build_run_003_transmittable_request_packet(
            live_execution_requested=True
        )


def test_import_and_source_are_offline_and_side_effect_free():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    imported = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node.names
    }
    assert imported.isdisjoint(
        {
            "groq",
            "dotenv",
            "requests",
            "httpx",
            "socket",
            "sqlite3",
            "psycopg",
            "sqlalchemy",
            "subprocess",
            "threading",
        }
    )
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert attributes.isdisjoint(
        {"environ", "getenv", "socket", "connect", "Popen", "run", "start"}
    )
    command = (
        "import src.evaluation.controlled_groq_canary_run_003_plan"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    assert completed.stdout == completed.stderr == ""


def test_building_validation_and_hashing_perform_no_write(monkeypatch):
    original_open = Path.open

    def guarded_open(path, mode="r", *args, **kwargs):
        if any(token in str(mode) for token in ("w", "a", "x", "+")):
            raise AssertionError("filesystem write attempted")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    owner.build_run_003_plan_contract()
    owner.serialize_run_003_plan_contract()
    owner.run_003_plan_sha256()
    owner.build_run_003_transmittable_request_packet()


def test_historical_run003_contract_remains_unchanged():
    contract = _contract()
    assert contract["controlled_plan_sha256"] == BASE_PLAN_SHA
    assert contract["benchmark_contract_sha256"] == BASE_BENCHMARK_SHA
    assert contract["fixture_corpus_sha256"] == CORPUS_SHA
    assert contract["step8o_engine_sha256"] == STEP8O_SHA


def test_runtime_artifacts_are_not_plan_test_prerequisites():
    assert owner.run_003_plan_sha256() == (
        "5d63ef8bc8749645c19211184e8b7be16aa1909fbdb8a3682b9073af7270e9e8"
    )


def test_only_exact_run003_owners_import_run003_plan_owner():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_groq_canary_run_003_plan" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())
    assert references == [
        "src/evaluation/controlled_groq_canary_run_003_identity.py",
        "src/evaluation/controlled_groq_canary_run_003_transport.py",
        "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py",
    ]


def test_process_environment_is_not_used_by_runtime(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("environment boundary reached")

    monkeypatch.setattr(os, "getenv", blocked)
    assert owner.validate_run_003_plan_contract(_contract())
    assert owner.validate_run_003_transmittable_request_packet(_packet())

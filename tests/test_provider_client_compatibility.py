from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from src.evaluation.provider_benchmark_contract import (
    build_provider_benchmark_contract,
)
from src.evaluation.provider_client_compatibility import (
    COMPATIBILITY_CONTRACT_VERSION,
    LIVE_UNPROVEN,
    RAW_DEBUG_SAFE,
    STEP8M_COMPATIBILITY_BASELINE_SHA256,
    SYNTHETIC_PASS,
    build_compatibility_scenarios,
    provider_client_compatibility_sha256,
    provider_client_compatibility_result_sha256,
    run_offline_provider_client_compatibility,
    serialize_provider_client_compatibility_result,
    validate_provider_client_compatibility_result,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "src/evaluation/provider_client_compatibility.py"
PRODUCTION_CLIENT = ROOT / "src/ai/llm_client.py"


@pytest.fixture(scope="module")
def result():
    return run_offline_provider_client_compatibility()


def _candidate(result, provider, model):
    return next(
        row
        for row in result["candidate_results"]
        if row["provider"] == provider and row["model"] == model
    )


def test_contract_version_is_exact(result):
    assert result["contract_version"] == COMPATIBILITY_CONTRACT_VERSION
    assert COMPATIBILITY_CONTRACT_VERSION == "provider-client-compatibility-v1"


def test_candidates_are_consumed_from_step8l_contract(result):
    benchmark = build_provider_benchmark_contract()
    assert [
        (row["provider"], row["model"])
        for row in result["candidate_results"]
    ] == [
        (row["provider"], row["model"])
        for row in benchmark["candidate_definitions"]
    ]


def test_scenario_order_is_stable_and_unique(result):
    assert len(result["scenario_order"]) == 4
    assert len(set(result["scenario_order"])) == 4
    assert [row["scenario_id"] for row in result["candidate_results"]] == result[
        "scenario_order"
    ]


def test_gemini_is_absent_from_compatibility_candidates(result):
    assert {row["provider"] for row in result["candidate_results"]} == {
        "groq",
        "openai",
    }


def test_fake_groq_dispatch_works_for_both_candidates(result):
    rows = [row for row in result["candidate_results"] if row["provider"] == "groq"]
    assert len(rows) == 2
    assert all(row["synthetic_status"] == SYNTHETIC_PASS for row in rows)


def test_fake_openai_dispatch_works_for_both_candidates(result):
    rows = [row for row in result["candidate_results"] if row["provider"] == "openai"]
    assert len(rows) == 2
    assert all(row["synthetic_status"] == SYNTHETIC_PASS for row in rows)


def test_no_real_sdk_client_is_constructed(result):
    assert result["environment_isolation"]["real_provider_client_constructions"] == 0


def test_repository_dotenv_is_not_loaded(result):
    isolation = result["environment_isolation"]
    assert isolation["repository_dotenv_loads"] == 0
    assert isolation["dotenv_load_attempts_blocked"] == 1


def test_no_provider_credential_is_read(result):
    assert result["environment_isolation"]["credential_reads"] == 0


def test_no_network_or_socket_is_used(result):
    isolation = result["environment_isolation"]
    assert isolation["network_calls"] == 0
    assert isolation["socket_calls"] == 0


def test_socket_constructor_can_be_prohibited(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("socket reach is prohibited")

    monkeypatch.setattr(socket, "socket", explode)
    payload = run_offline_provider_client_compatibility()
    assert payload["environment_isolation"]["socket_calls"] == 0


def test_gpt_oss_reasoning_is_suppressed(result):
    for row in result["candidate_results"]:
        classification = row["request_field_classifications"]["reasoning_control"]
        if row["provider"] == "groq":
            assert classification == "suppressed_for_gpt_oss"
        else:
            assert classification == "not_sent_for_openai"


def test_groq_json_object_mode_is_recorded(result):
    rows = [row for row in result["candidate_results"] if row["provider"] == "groq"]
    assert all(
        row["structured_output_classifications"]["json_object"] == "pass"
        for row in rows
    )


def test_groq_strict_json_schema_mode_is_recorded(result):
    rows = [row for row in result["candidate_results"] if row["provider"] == "groq"]
    assert all(
        row["structured_output_classifications"]["strict_json_schema"] == "pass"
        for row in rows
    )


def test_openai_json_object_mode_is_recorded(result):
    rows = [row for row in result["candidate_results"] if row["provider"] == "openai"]
    assert all(
        row["structured_output_classifications"]["json_object"] == "pass"
        for row in rows
    )


def test_openai_strict_json_schema_mode_is_recorded(result):
    rows = [row for row in result["candidate_results"] if row["provider"] == "openai"]
    assert all(
        row["structured_output_classifications"]["strict_json_schema"] == "pass"
        for row in rows
    )


def test_max_completion_tokens_is_recorded(result):
    assert all(
        row["request_field_classifications"]["max_completion_tokens"] == "present"
        for row in result["candidate_results"]
    )


def test_model_compatible_temperature_behavior_is_recorded(result):
    gpt_5_mini = _candidate(result, "openai", "gpt-5-mini")
    assert gpt_5_mini["request_field_classifications"]["temperature"] == (
        "omitted_for_default_only_model"
    )

    other_rows = [
        row
        for row in result["candidate_results"]
        if (row["provider"], row["model"]) != ("openai", "gpt-5-mini")
    ]
    assert all(
        row["request_field_classifications"]["temperature"] == "passed_explicitly"
        for row in other_rows
    )


def test_valid_json_parsing_is_deterministic(result):
    assert all(
        row["parse_classifications"]["valid_json"] == "parsed"
        for row in result["candidate_results"]
    )


def test_malformed_json_returns_current_text_behavior(result):
    assert all(
        row["parse_classifications"]["malformed_json"] == "returned_as_text"
        for row in result["candidate_results"]
    )


def test_list_and_dictionary_content_coercion_is_deterministic(result):
    assert all(
        row["parse_classifications"]["list_and_dictionary_content"] == "coerced"
        for row in result["candidate_results"]
    )


def test_empty_response_behavior_is_classified(result):
    assert all(
        row["parse_classifications"]["empty_content"] == "runtime_error"
        for row in result["candidate_results"]
    )


def test_refusal_behavior_is_classified(result):
    assert all(
        row["parse_classifications"]["refusal_without_content"] == "runtime_error"
        for row in result["candidate_results"]
    )


def test_provider_metrics_are_exact_and_defensive(result):
    metrics = result["provider_metrics"]
    assert metrics["single_call_deltas_exact"] is True
    assert metrics["gemini_calls"] == 0
    assert metrics["defensive_copy"] is True


def test_missing_provider_observability_is_recorded(result):
    assert result["provider_metrics"]["missing_observability"] == [
        "latency",
        "input_tokens",
        "output_tokens",
        "estimated_cost",
        "request_identity",
        "retry_classification",
        "model_attempt_history",
    ]


def test_fallback_disabled_means_zero_fallback(result):
    assert (
        result["fallback"]["fallback_disabled"]
        == "primary_error_propagated_zero_fallback"
    )


def test_enabled_fallback_is_bounded_to_one(result):
    assert result["fallback"]["fallback_enabled_bound"] == 1
    assert result["fallback"]["fallback_success"] == "counted_once"


def test_recursive_fallback_does_not_occur(result):
    assert result["fallback"]["recursive_fallback"] is False
    assert result["fallback"]["fallback_failure"] == "combined_runtime_error"


def test_unsupported_provider_fails_closed(result):
    assert result["fallback"]["unsupported_provider"] == "fails_closed"


def test_provider_model_mismatch_is_recorded_as_repair_requirement(result):
    assert result["fallback"]["provider_model_mismatch"] == "fails_closed"


def test_fallback_policy_risks_are_classified(result):
    assert (
        result["fallback"]["exception_policy"]
        == "approved_transient_categories_only"
    )
    assert (
        result["fallback"]["routing_policy"]
        == "bounded_explicit_transient_only"
    )


def test_raw_debug_output_is_classified_without_persisting_marker(result):
    assert result["raw_debug_output"] == RAW_DEBUG_SAFE
    serialized = serialize_provider_client_compatibility_result(result)
    assert "bounded-raw-debug-synthetic-marker" not in serialized


def test_production_repair_owner_is_exact(result):
    assert result["production_repair_requirements"] == []


def test_openai_chat_completions_risks_are_complete(result):
    risks = result["openai_compatibility_risks"]
    assert "chat_completions_remote_support_unproven" in risks
    assert "temperature_remote_support_unproven" in risks
    assert "structured_output_remote_support_unproven" in risks
    assert "schema_restrictions_unproven" in risks
    assert "reasoning_controls_absent" in risks
    assert "max_completion_tokens_remote_support_unproven" in risks
    assert "response_content_shape_unproven" in risks
    assert "repository_timeout_owner_missing" in risks
    assert "sdk_retry_owner_external" in risks


def test_live_compatibility_always_remains_unproven(result):
    assert result["live_compatibility_status"] == LIVE_UNPROVEN
    assert all(
        row["live_status"] == LIVE_UNPROVEN
        for row in result["candidate_results"]
    )


def test_no_prompt_or_response_body_is_persisted(result):
    serialized = serialize_provider_client_compatibility_result(result)
    for prohibited in (
        "offline synthetic compatibility probe",
        "synthetic plain text",
        "synthetic_ok",
        "{malformed",
        "synthetic dictionary",
        "synthetic fallback success",
        "synthetic primary failure",
    ):
        assert prohibited not in serialized


def test_serialization_and_digest_are_deterministic(result):
    first = serialize_provider_client_compatibility_result(result)
    second = serialize_provider_client_compatibility_result(deepcopy(result))
    assert first == second
    assert provider_client_compatibility_sha256(result) == provider_client_compatibility_sha256(
        deepcopy(result)
    )
    assert provider_client_compatibility_result_sha256(
        result
    ) == provider_client_compatibility_result_sha256(deepcopy(result))


def test_step8m_baseline_digest_remains_exact(result):
    assert (
        result["step8m_compatibility_baseline_sha256"]
        == STEP8M_COMPATIBILITY_BASELINE_SHA256
    )
    assert STEP8M_COMPATIBILITY_BASELINE_SHA256 == (
        "e798f7d10f67c65c5d02f7531b54c3ce1b18ad0a6db5ec98505b4f1847f23ddd"
    )
    assert provider_client_compatibility_sha256(result) == (
        STEP8M_COMPATIBILITY_BASELINE_SHA256
    )


def test_digest_is_stable_in_fresh_process(result):
    expected = provider_client_compatibility_sha256(result)
    script = (
        "from src.evaluation.provider_client_compatibility import "
        "provider_client_compatibility_sha256;"
        "print(provider_client_compatibility_sha256())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        check=True,
    )
    assert completed.stdout.strip() == expected
    assert completed.stderr == ""


def test_deep_copy_containment(result):
    mutated = deepcopy(result)
    mutated["candidate_results"][0]["provider"] = "mutated"
    fresh = run_offline_provider_client_compatibility()
    assert fresh["candidate_results"][0]["provider"] == "groq"


def test_authority_and_mutation_boundaries_are_zero(result):
    authority = result["authority_invariants"]
    assert authority["authority_transfer"] is False
    assert authority["mutation_count"] == 0
    assert authority["application_action_count"] == 0
    assert authority["ats_action_count"] == 0
    assert authority["resume_selection_allowed"] is False
    assert authority["score_mutation_allowed"] is False
    assert authority["ranking_mutation_allowed"] is False
    assert authority["queue_mutation_allowed"] is False
    assert authority["provider_response_persistence_allowed"] is False
    assert authority["recovery_006_authorization"] is False


def test_repository_defaults_and_production_client_remain_unchanged():
    before = PRODUCTION_CLIENT.read_bytes()
    run_offline_provider_client_compatibility()
    assert PRODUCTION_CLIENT.read_bytes() == before


def test_construction_writes_no_artifact(monkeypatch):
    def reject_write(*_args, **_kwargs):
        raise AssertionError("compatibility harness must not write files")

    monkeypatch.setattr(Path, "write_text", reject_write)
    monkeypatch.setattr(Path, "write_bytes", reject_write)
    payload = run_offline_provider_client_compatibility()
    assert payload["authority_invariants"]["mutation_count"] == 0


def test_repository_dotenv_path_is_never_read(monkeypatch):
    original = Path.read_text

    def guarded_read(path, *args, **kwargs):
        if path.name == ".env":
            raise AssertionError("repository dotenv read prohibited")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read)
    assert run_offline_provider_client_compatibility()[
        "environment_isolation"
    ]["repository_dotenv_loads"] == 0


def test_import_does_not_import_production_client_or_provider_sdks():
    script = (
        "import json,sys;"
        "import src.evaluation.provider_client_compatibility;"
        "names=('src.ai.llm_client','groq','openai','google.genai');"
        "print(json.dumps({name:name in sys.modules for name in names},sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(completed.stdout) == {
        "google.genai": False,
        "groq": False,
        "openai": False,
        "src.ai.llm_client": False,
    }


def test_owner_has_no_transport_database_or_execution_imports():
    tree = ast.parse(OWNER.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported.isdisjoint(
        {
            "groq",
            "openai",
            "google",
            "requests",
            "httpx",
            "urllib",
            "socket",
            "psycopg",
            "subprocess",
            "threading",
        }
    )


def test_scenarios_are_fresh_deep_copies():
    first = build_compatibility_scenarios()
    second = build_compatibility_scenarios()
    first[0]["expected_request_fields"].append("mutated")
    assert "mutated" not in second[0]["expected_request_fields"]


def test_result_validation_rejects_authority_or_live_status(result):
    mutated = deepcopy(result)
    mutated["authority_invariants"]["authority_transfer"] = True
    with pytest.raises(ValueError):
        validate_provider_client_compatibility_result(mutated)

    mutated = deepcopy(result)
    mutated["candidate_results"][0]["live_status"] = "proven"
    with pytest.raises(ValueError):
        validate_provider_client_compatibility_result(mutated)


def test_next_safe_step_is_production_client_repair(result):
    assert result["next_safe_step"] == "offline_fixture_benchmark_implementation"

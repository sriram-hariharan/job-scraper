from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest

from src.ai import provider_model_catalog
from src.evaluation import provider_benchmark_contract as contract_owner


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "src" / "evaluation" / "provider_benchmark_contract.py"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "provider_benchmark" / "manifest.json"

EXPECTED_PROVIDERS = ["groq", "openai"]
EXPECTED_MODELS = [
    ("groq", "openai/gpt-oss-20b"),
    ("groq", "openai/gpt-oss-120b"),
    ("openai", "gpt-5-mini"),
    ("openai", "gpt-5.1"),
]
EXPECTED_WORKLOADS = [
    "skill_extraction",
    "job_fit_evaluation",
    "jd_intelligence",
    "grounded_rag_answer",
    "resume_fallback_ranking",
    "ambiguous_resume_adjudication",
    "critic_evaluation",
    "tailoring_generation",
    "tailoring_refinement",
    "tailoring_judge",
    "manual_scan_phrase",
    "manual_provider_preview",
]
EXPECTED_METRICS = [
    "provider_call_success_rate",
    "schema_valid_response_rate",
    "normalization_success_rate",
    "grounded_evidence_precision",
    "unsupported_claim_count",
    "hallucination_count",
    "required_field_completeness",
    "deterministic_authority_preservation",
    "winner_agreement",
    "ranking_agreement",
    "skill_extraction_precision",
    "skill_extraction_recall",
    "missing_requirement_accuracy",
    "tailoring_evidence_support",
    "critic_agreement",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "estimated_cost",
    "cache_hit_count",
    "timeout_count",
    "retry_count",
    "rate_limit_count",
    "fallback_activation_count",
    "fallback_correctness",
    "duplicate_call_count",
    "persisted_raw_response_count",
    "mutation_count",
    "application_action_count",
    "ats_action_count",
]
EXPECTED_HARD_FAILURES = [
    "schema_invalid_result_accepted",
    "unsupported_claim",
    "hallucination",
    "sensitive_data_leakage",
    "deterministic_authority_mutation",
    "queue_mutation",
    "ranking_mutation",
    "selected_resume_mutation",
    "provider_called_while_disabled",
    "silent_cross_provider_fallback",
    "unbounded_retry",
    "missing_provider_observability",
    "missing_model_observability",
    "missing_latency_observability",
    "missing_token_observability",
    "persisted_raw_response",
    "application_action_reached",
    "ats_action_reached",
]


def _contract():
    return contract_owner.build_provider_benchmark_contract()


def _manifest():
    return contract_owner.load_provider_benchmark_fixture_manifest()


def test_contract_version_provider_and_model_sets_are_exact():
    payload = _contract()

    assert payload["contract_version"] == "provider-benchmark-contract-v1"
    assert payload["provider_order"] == EXPECTED_PROVIDERS
    assert [
        (row["provider"], row["model"])
        for row in payload["candidate_definitions"]
    ] == EXPECTED_MODELS
    assert all(row["provider"] != "gemini" for row in payload["candidate_definitions"])
    assert "winner" not in payload


def test_qualification_candidates_and_tiers_derive_from_canonical_catalog():
    payload = _contract()
    catalog_rows = [
        row
        for row in provider_model_catalog.list_configurable_models()
        if row["configuration_status"] == "configuration_eligible"
        and row["synthetic_compatibility_status"]
        == "synthetic_compatibility_expected"
        and row["live_qualification_status"]
        == "live_qualification_required"
        and row["eligible_benchmark_tiers"]
    ]

    assert [
        (row["provider"], row["model"], row["eligible_tiers"])
        for row in payload["candidate_definitions"]
    ] == [
        (row["provider"], row["model_id"], row["eligible_benchmark_tiers"])
        for row in catalog_rows
    ]


def test_catalog_snapshot_and_digest_are_deterministic_and_contract_bound():
    first = contract_owner.build_provider_model_catalog_snapshot()
    second = contract_owner.build_provider_model_catalog_snapshot()
    digest = contract_owner.provider_model_catalog_snapshot_sha256(first)
    payload = _contract()

    assert first == second
    assert (
        contract_owner.serialize_provider_model_catalog_snapshot(first)
        == contract_owner.serialize_provider_model_catalog_snapshot(second)
    )
    assert digest == contract_owner.provider_model_catalog_snapshot_sha256(
        second
    )
    assert len(digest) == 64
    assert payload["model_catalog_snapshot"] == first
    assert payload["model_catalog_snapshot_sha256"] == digest


def test_qualification_relevant_catalog_eligibility_changes_snapshot_digest():
    original = contract_owner.build_provider_model_catalog_snapshot()
    changed = deepcopy(original)
    changed["candidates"][0]["eligible_tiers"] = ["A", "B"]

    assert contract_owner.validate_provider_model_catalog_snapshot(changed)
    assert contract_owner.provider_model_catalog_snapshot_sha256(changed) != (
        contract_owner.provider_model_catalog_snapshot_sha256(original)
    )

    payload = _contract()
    payload["model_catalog_snapshot"] = changed
    payload["model_catalog_snapshot_sha256"] = (
        contract_owner.provider_model_catalog_snapshot_sha256(changed)
    )
    with pytest.raises(ValueError, match="canonical model catalog"):
        contract_owner.validate_provider_benchmark_contract(payload)


def test_workloads_are_unique_stable_complete_and_tiered():
    payload = _contract()
    workload_ids = [row["workload_id"] for row in payload["workloads"]]

    assert workload_ids == EXPECTED_WORKLOADS
    assert len(workload_ids) == len(set(workload_ids))
    assert {row["tier"] for row in payload["workloads"]} == {"A", "B", "C"}
    assert [row["workload_id"] for row in payload["candidate_matrix"]] == EXPECTED_WORKLOADS
    assert all(row["candidate_ids"] for row in payload["candidate_matrix"])


def test_candidate_definitions_are_default_off_explicit_and_non_authoritative():
    for candidate in _contract()["candidate_definitions"]:
        assert candidate["fallback_disabled"] is True
        assert candidate["explicit_provider_required"] is True
        assert candidate["explicit_model_required"] is True
        assert candidate["live_execution_default"] is False
        assert candidate["maximum_request_budget"] == 0
        assert candidate["raw_response_persistence_prohibited"] is True
        assert candidate["authority_transfer"] is False


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda payload: payload["candidate_definitions"][0].update(
                {"provider": "gemini"}
            ),
            "unsupported benchmark provider",
        ),
        (
            lambda payload: payload["candidate_definitions"][0].update(
                {"model": "unsupported-model"}
            ),
            "unsupported benchmark model",
        ),
        (
            lambda payload: payload["candidate_definitions"][0].update(
                {"provider": "openai"}
            ),
            "provider/model mismatch",
        ),
        (
            lambda payload: payload["candidate_definitions"].append(
                deepcopy(payload["candidate_definitions"][0])
            ),
            "duplicate candidate definitions",
        ),
        (
            lambda payload: payload.update({"candidate_matrix": []}),
            "candidate matrix must be nonempty",
        ),
        (
            lambda payload: payload["candidate_matrix"][0].update(
                {"candidate_ids": []}
            ),
            "every workload must have at least one candidate",
        ),
        (
            lambda payload: payload.update({"selected_winner": "not-allowed"}),
            "model winner selection is prohibited",
        ),
        (
            lambda payload: payload["candidate_definitions"][0].update(
                {"fallback_disabled": False}
            ),
            "benchmark fallback must be disabled",
        ),
    ],
)
def test_invalid_candidate_and_authority_contracts_are_rejected(mutation, message):
    payload = _contract()
    mutation(payload)

    with pytest.raises(ValueError, match=message):
        contract_owner.validate_provider_benchmark_contract(payload)


def test_metric_and_hard_failure_sets_are_complete_and_stable():
    payload = _contract()

    assert payload["metric_order"] == EXPECTED_METRICS
    assert [row["metric_id"] for row in payload["metric_definitions"]] == EXPECTED_METRICS
    assert payload["hard_failure_order"] == EXPECTED_HARD_FAILURES
    assert [
        row["failure_id"] for row in payload["hard_failure_gates"]
    ] == EXPECTED_HARD_FAILURES
    assert all(row["execution_must_stop"] for row in payload["hard_failure_gates"])
    assert all(row["human_review_required"] for row in payload["hard_failure_gates"])


def test_authority_and_action_invariants_are_fail_closed():
    payload = _contract()
    invariants = payload["safety_invariants"]
    controls = payload["benchmark_controls"]

    assert invariants["prefilter_relevance_owner"] == "deterministic"
    assert invariants["final_application_scoring_owner"] == "deterministic"
    assert invariants["queue_owner"] == "deterministic"
    assert invariants["ranking_owner"] == "deterministic"
    assert invariants["selected_resume_owner"] == "deterministic"
    assert invariants["graph_verification_mode"] == "comparison_only"
    for key in (
        "application_action_authority",
        "ats_authority",
        "automatic_mutation_authority",
        "credential_driven_activation",
        "automatic_fallback_during_benchmark",
        "live_execution_default",
    ):
        assert invariants[key] is False
    assert controls["live_execution_enabled"] is False
    assert controls["maximum_request_budget"] == 0
    assert controls["automatic_fallback_enabled"] is False
    assert controls["authority_transfer_allowed"] is False


def test_fixture_manifest_is_repository_relative_offline_and_non_personal():
    manifest = _manifest()
    entries = manifest["fixtures"]

    assert len(entries) == len(EXPECTED_WORKLOADS)
    assert [row["workload_id"] for row in entries] == EXPECTED_WORKLOADS
    assert len({row["fixture_id"] for row in entries}) == len(entries)
    for entry in entries:
        source_path = Path(entry["source_path"])
        assert not source_path.is_absolute()
        assert ".." not in source_path.parts
        assert (ROOT / source_path).is_file()
        assert entry["live_transmission_eligible"] is False
        assert entry["contains_personal_resume_content"] is False
        assert entry["offline_only"] is True
        assert isinstance(entry["deterministic_invariant_available"], bool)
        assert isinstance(entry["golden_output_available"], bool)
        assert isinstance(entry["schema_expected"], bool)


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "outputs/_archive/scorer_v2_runtime_fixtures/example.json",
        "outputs/application_planning/runtime.json",
        "skill_eval.txt",
        "/tmp/fixture.json",
        "../outside.json",
        "data/runtime_job.json",
    ],
)
def test_unsafe_fixture_paths_are_rejected(unsafe_path):
    manifest = _manifest()
    manifest["fixtures"][0]["source_path"] = unsafe_path

    with pytest.raises(ValueError):
        contract_owner.validate_fixture_manifest(manifest)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("live_transmission_eligible", True),
        ("contains_personal_resume_content", True),
        ("offline_only", False),
        ("fixture_id", "credential_fixture"),
        ("fixture_id", "raw_provider_response_fixture"),
    ],
)
def test_unsafe_fixture_authorization_and_content_classes_are_rejected(field, value):
    manifest = _manifest()
    manifest["fixtures"][0][field] = value

    with pytest.raises(ValueError):
        contract_owner.validate_fixture_manifest(manifest)


def test_serialization_and_digest_are_deterministic_and_machine_independent():
    first = _contract()
    second = _contract()
    first_json = contract_owner.serialize_provider_benchmark_contract(first)
    second_json = contract_owner.serialize_provider_benchmark_contract(second)
    first_digest = contract_owner.provider_benchmark_contract_sha256(first)
    second_digest = contract_owner.provider_benchmark_contract_sha256(second)

    assert first_json == second_json
    assert first_digest == second_digest
    assert len(first_digest) == 64
    assert str(ROOT) not in first_json
    assert "generated_at" not in first_json
    assert "timestamp" not in first_json
    assert "raw_provider_response" not in first_json


def test_digest_matches_in_a_fresh_process():
    local_digest = contract_owner.provider_benchmark_contract_sha256()
    code = (
        "from src.evaluation.provider_benchmark_contract import "
        "provider_benchmark_contract_sha256;"
        "print(provider_benchmark_contract_sha256())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={},
    )

    assert completed.stderr == ""
    assert completed.stdout.strip() == local_digest


def test_returned_contracts_and_manifests_do_not_share_mutable_state():
    first = _contract()
    original_digest = contract_owner.provider_benchmark_contract_sha256(first)
    first["workloads"][0]["tier"] = "C"
    first["fixture_manifest"]["fixtures"][0]["fixture_id"] = "mutated"

    second = _contract()
    assert second["workloads"][0]["tier"] == "A"
    assert second["fixture_manifest"]["fixtures"][0]["fixture_id"] != "mutated"
    assert contract_owner.provider_benchmark_contract_sha256(second) == original_digest


def test_import_and_construction_do_not_import_provider_clients():
    code = (
        "import json,sys;"
        "from src.evaluation import provider_benchmark_contract as c;"
        "c.build_provider_benchmark_contract();"
        "print(json.dumps({name:(name in sys.modules) for name in "
        "['groq','openai','google.genai','src.ai.llm_client']},sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={},
    )

    assert json.loads(completed.stdout) == {
        "google.genai": False,
        "groq": False,
        "openai": False,
        "src.ai.llm_client": False,
    }


def test_construction_does_not_reach_an_injected_provider_module(monkeypatch):
    explosive = ModuleType("src.ai.llm_client")

    def _explode(*_args, **_kwargs):
        raise AssertionError("provider boundary reached")

    explosive.run_chat_completion = _explode
    explosive.run_chat_completion_with_metadata = _explode
    monkeypatch.setitem(sys.modules, "src.ai.llm_client", explosive)

    payload = _contract()
    assert payload["benchmark_controls"]["provider_client_allowed"] is False


def test_contract_owner_imports_only_catalog_and_side_effect_free_standard_library():
    tree = ast.parse(CONTRACT_PATH.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")

    assert imports == {
        "__future__",
        "copy",
        "hashlib",
        "json",
        "pathlib",
        "src.ai.provider_model_catalog",
        "typing",
    }
    assert not imports.intersection(
        {
            "os",
            "dotenv",
            "groq",
            "openai",
            "google",
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "threading",
            "psycopg",
            "src.ai.llm_client",
        }
    )


def test_contract_owner_exposes_no_execution_or_filesystem_write_surface():
    tree = ast.parse(CONTRACT_PATH.read_text(encoding="utf-8"))
    call_names = set()
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        try:
            call_names.add(ast.unparse(node.func))
        except Exception:
            pass

    assert not any(
        name.endswith(
            (
                ".write_text",
                ".write_bytes",
                ".mkdir",
                ".touch",
                ".open",
                ".connect",
                ".submit",
                ".send",
            )
        )
        for name in call_names
    )
    assert not any(
        token in function_names
        for token in (
            "run_benchmark",
            "execute_benchmark",
            "call_provider",
            "submit_application",
            "mutate_queue",
            "choose_resume",
            "write_artifact",
        )
    )


def test_construction_performs_no_filesystem_write(monkeypatch):
    original_open = Path.open

    def guarded_open(path, mode="r", *args, **kwargs):
        if any(token in str(mode) for token in ("w", "a", "x", "+")):
            raise AssertionError("filesystem write attempted")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    payload = _contract()
    assert payload["benchmark_controls"]["artifact_write_allowed"] is False


def test_contract_construction_leaves_repository_files_unchanged():
    paths = (CONTRACT_PATH, MANIFEST_PATH)
    before = {path: path.read_bytes() for path in paths}

    _contract()
    contract_owner.provider_benchmark_contract_sha256()

    after = {path: path.read_bytes() for path in paths}
    assert after == before

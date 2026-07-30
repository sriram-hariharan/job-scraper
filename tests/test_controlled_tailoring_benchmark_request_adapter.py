from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.evaluation import controlled_tailoring_benchmark_request_adapter as adapter
from src.evaluation.controlled_groq_provider_canary import (
    build_controlled_groq_canary_contract,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER = (
    ROOT
    / "src/evaluation/controlled_tailoring_benchmark_request_adapter.py"
)
SERVICES = ROOT / "src/app/services.py"
AGENT = ROOT / "src/agents/tailoring_decision_agent.py"


def _plan():
    return build_controlled_provider_benchmark_plan()


def _scheduled():
    return next(
        deepcopy(row)
        for row in build_controlled_groq_canary_contract()["schedule"]
        if row["workload_id"] == "tailoring_generation"
        and row["provider"] == "groq"
        and row["model"] == "openai/gpt-oss-120b"
    )


def _packet():
    plan = _plan()
    row = _scheduled()
    return build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=plan,
        live_execution_requested=False,
    )


def _adapted():
    return adapter.build_adapted_tailoring_request_specification(
        packet=_packet(),
        plan=_plan(),
    )


def _valid_response():
    return {
        "suggestions": [
            {
                "suggestion_id": "suggestion_001",
                "source_bullet_id": "bullet_alpha",
                "claims": ["python", "sql"],
                "evidence_tokens": ["python", "sql"],
            }
        ],
        "human_review_required": True,
        "authority_mutated": False,
    }


def test_adapter_contract_version_fields_and_semantic_owners_are_exact():
    contract = adapter.build_controlled_tailoring_request_adapter_contract()

    assert contract["adapter_version"] == (
        "controlled-tailoring-benchmark-request-adapter-v1"
    )
    assert set(contract) == {
        "adapter_version",
        "contract_kind",
        "canonical_semantic_owners",
        "request_contract",
        "response_contract",
        "authority_invariants",
    }
    assert contract["request_contract"]["workload_id"] == "tailoring_generation"
    assert contract["request_contract"]["provider"] == "groq"
    assert contract["request_contract"]["model"] == "openai/gpt-oss-120b"
    assert contract["request_contract"]["synthetic_input_fields"] == [
        "evidence_tokens",
        "source_bullet_ids",
    ]
    assert contract["canonical_semantic_owners"] == {
        "manual_tailoring_response_schema": (
            "src/app/services.py:"
            "LIVE_TAILORING_SUGGESTION_DRY_RUN_RESPONSE_SCHEMA"
        ),
        "manual_tailoring_instruction": (
            "src/app/services.py:_live_tailoring_suggestion_prompt"
        ),
        "manual_only_authority_boundary": (
            "src/app/services.py:"
            "build_manual_tailoring_suggestion_dry_run_payload"
        ),
        "deterministic_evidence_and_source_identity": (
            "src/agents/tailoring_decision_agent.py:"
            "build_tailoring_suggestion_dry_run_payload"
        ),
        "deterministic_authority_preservation": (
            "src/agents/tailoring_decision_agent.py:"
            "_tailoring_suggestion_safety_metadata"
        ),
        "provider_neutral_packet": (
            "src/evaluation/controlled_provider_benchmark_plan.py:"
            "build_transmittable_request_packet"
        ),
        "deterministic_tailoring_grader": (
            "src/evaluation/provider_fixture_benchmark.py:"
            "build_tailoring_generation_diagnostics"
        ),
    }


def test_adapter_digest_is_deterministic_deep_copy_contained_and_fresh_process_stable():
    contract = adapter.build_controlled_tailoring_request_adapter_contract()
    original = deepcopy(contract)
    first = adapter.controlled_tailoring_request_adapter_sha256(contract)
    second = adapter.controlled_tailoring_request_adapter_sha256(contract)

    assert first == second
    assert contract == original
    contract["authority_invariants"]["production_activation"] = True
    assert (
        adapter.build_controlled_tailoring_request_adapter_contract()
        == original
    )
    code = (
        "from src.evaluation."
        "controlled_tailoring_benchmark_request_adapter import "
        "controlled_tailoring_request_adapter_sha256;"
        "print(controlled_tailoring_request_adapter_sha256())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == first


def test_adapted_request_is_bounded_semantic_and_contains_no_local_only_content():
    adapted = _adapted()

    assert set(adapted) == {
        "adapter_version",
        "workload_id",
        "provider",
        "model",
        "system_instruction",
        "user_payload",
        "response_schema",
    }
    assert set(adapted["user_payload"]) == {
        "task_identifier",
        "source_bullet_ids",
        "evidence_tokens",
        "requirements",
    }
    assert adapted["user_payload"]["source_bullet_ids"] == ["bullet_alpha"]
    assert adapted["user_payload"]["evidence_tokens"] == [
        "python",
        "sql",
        "airflow",
    ]
    instruction = adapted["system_instruction"].lower()
    for phrase in (
        "evidence-backed",
        "human review",
        "supplied source-bullet ids",
        "supplied",
        "do not invent",
        "do not",
    ):
        assert phrase in instruction
    serialized = adapter.serialize_adapted_tailoring_request_specification(
        adapted
    ).lower()
    for prohibited in (
        "case_alias",
        "schedule_key",
        "expected_output",
        "golden_output",
        "provenance",
        "repository",
        "credential",
        "request_id",
        "raw_response",
        "resume_text",
        "job_description",
    ):
        assert prohibited not in serialized


def test_typed_schema_is_strict_nested_and_bound_to_supplied_values():
    schema = _adapted()["response_schema"]
    suggestions = schema["properties"]["suggestions"]
    item = suggestions["items"]

    assert schema["type"] == "object"
    assert schema["required"] == [
        "authority_mutated",
        "human_review_required",
        "suggestions",
    ]
    assert schema["additionalProperties"] is False
    assert suggestions["type"] == "array"
    assert suggestions["minItems"] == 1
    assert item["additionalProperties"] is False
    assert item["required"] == [
        "claims",
        "evidence_tokens",
        "source_bullet_id",
        "suggestion_id",
    ]
    assert item["properties"]["suggestion_id"] == {
        "type": "string",
        "minLength": 1,
    }
    assert item["properties"]["source_bullet_id"]["enum"] == [
        "bullet_alpha"
    ]
    assert item["properties"]["claims"]["minItems"] == 1
    assert item["properties"]["claims"]["items"]["enum"] == [
        "python",
        "sql",
        "airflow",
    ]
    assert item["properties"]["evidence_tokens"]["minItems"] == 1
    assert item["properties"]["evidence_tokens"]["items"]["enum"] == [
        "python",
        "sql",
        "airflow",
    ]
    assert schema["properties"]["human_review_required"] == {
        "type": "boolean",
        "const": True,
    }
    assert schema["properties"]["authority_mutated"] == {
        "type": "boolean",
        "const": False,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_bullet_ids", []),
        ("source_bullet_ids", [""]),
        ("source_bullet_ids", ["bullet_alpha", "bullet_alpha"]),
        ("evidence_tokens", []),
        ("evidence_tokens", [" "]),
        ("evidence_tokens", ["python", "python"]),
    ],
)
def test_blank_empty_or_duplicate_synthetic_identifiers_are_rejected(
    field,
    value,
):
    packet = _packet()
    packet["synthetic_input"][field] = value

    with pytest.raises(ValueError):
        adapter.build_adapted_tailoring_request_specification(
            packet=packet,
            plan=_plan(),
        )


def test_packet_target_allowlist_and_free_form_additions_are_rejected():
    for mutation in (
        lambda packet: packet.update(workload_id="skill_extraction"),
        lambda packet: packet.update(provider="openai"),
        lambda packet: packet.update(model="openai/gpt-oss-20b"),
        lambda packet: packet["synthetic_input"].update(extra="forbidden"),
        lambda packet: packet.update(extra="forbidden"),
    ):
        packet = _packet()
        mutation(packet)
        with pytest.raises(ValueError):
            adapter.build_adapted_tailoring_request_specification(
                packet=packet,
                plan=_plan(),
            )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda output: output.update(suggestions=[]),
        lambda output: output.update(human_review_required=False),
        lambda output: output.update(authority_mutated=True),
        lambda output: output["suggestions"][0].update(
            source_bullet_id="invented_output_value"
        ),
        lambda output: output["suggestions"][0].update(
            claims=["invented_output_value"]
        ),
        lambda output: output["suggestions"][0].update(
            evidence_tokens=["invented_output_value"]
        ),
        lambda output: output.update(extra=True),
        lambda output: output["suggestions"][0].update(extra=True),
        lambda output: output["suggestions"][0].update(suggestion_id=""),
        lambda output: output["suggestions"][0].update(claims=[]),
        lambda output: output["suggestions"][0].update(evidence_tokens=[]),
    ],
)
def test_local_response_validation_fails_closed(mutation):
    output = _valid_response()
    mutation(output)

    with pytest.raises(ValueError) as exc_info:
        adapter.validate_normalized_tailoring_response(
            output,
            adapted_request=_adapted(),
        )

    assert "suggestion_001" not in str(exc_info.value)
    assert "invented_output_value" not in str(exc_info.value)


def test_valid_response_passes_without_mutating_any_input():
    packet = _packet()
    packet_before = deepcopy(packet)
    adapted = adapter.build_adapted_tailoring_request_specification(
        packet=packet,
        plan=_plan(),
    )
    adapted_before = deepcopy(adapted)
    output = _valid_response()
    output_before = deepcopy(output)

    assert adapter.validate_normalized_tailoring_response(
        output,
        adapted_request=adapted,
    )
    assert packet == packet_before
    assert adapted == adapted_before
    assert output == output_before


def test_canonical_semantic_parity_is_explicit_without_importing_production():
    services = SERVICES.read_text(encoding="utf-8")
    agent = AGENT.read_text(encoding="utf-8")
    requirements = _adapted()["user_payload"]["requirements"]

    assert "manual read-only dry-run" in services
    assert "evidence-backed resume tailoring suggestions" in services
    assert "never apply changes" in services
    assert '"did_mutate_resume": False' in agent
    assert '"did_mutate_scoring": False' in agent
    assert '"did_change_ranking": False' in agent
    assert '"did_mutate_queue": False' in agent
    assert '"did_mutate_approval": False' in agent
    assert '"did_execute_application": False' in agent
    assert '"did_submit_application": False' in agent
    assert requirements["human_review_required"] is True
    assert requirements["deterministic_authority_preserved"] is True
    assert requirements["resume_mutation_authorized"] is False
    assert requirements["score_or_ranking_mutation_authorized"] is False
    assert requirements["queue_or_approval_mutation_authorized"] is False
    assert requirements["application_authorized"] is False
    assert requirements["ats_action_authorized"] is False


def test_adapter_module_has_no_forbidden_import_or_side_effect_construct():
    tree = ast.parse(OWNER.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    source = OWNER.read_text(encoding="utf-8")

    assert not any(
        name.startswith(
            (
                "src.app",
                "src.ai",
                "fastapi",
                "groq",
                "dotenv",
                "socket",
                "subprocess",
                "threading",
            )
        )
        for name in imports
    )
    for prohibited in (
        "os.getenv",
        "os.environ",
        "open(",
        "write_text",
        "write_bytes",
        "mkdir(",
        "connect(",
    ):
        assert prohibited not in source

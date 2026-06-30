from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path

from src.agents import (
    controlled_exact_resume_change_set_provider_call_boundary_default_off as boundary,
)
from src.agents.controlled_exact_resume_change_set_provider_call_boundary_default_off import (
    build_controlled_exact_resume_change_set_provider_call_boundary_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_default_off.md"
)

FALSE_ACTION_KEYS = {
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_provider_call_boundary",
    "read_only",
    "advisory_only",
    "proposal_only",
    "provider_call_boundary_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "manual_trigger_required",
    "manual_trigger_confirmed",
    "request_packet_present",
    "request_packet_valid",
    "provider_callable_present",
    "provider_callable_valid",
    "enable_provider_call",
    "provider_policy",
    "provider_call_allowed",
    "provider_call_blocked_reason",
    "provider_call_result",
    "provider_response",
    "provider_response_present",
    "provider_response_type",
    "provider_response_summary",
    "provider_call_findings",
    "missing_inputs",
    "provider_call_key",
    "provider_call_attempted",
    "provider_call_performed",
    "llm_call_performed",
} | FALSE_ACTION_KEYS

FORBIDDEN_SOURCE_MARKERS = (
    "from src.pipeline",
    "import src.pipeline",
    "from src.matching",
    "import src.matching",
    "from src.tailoring",
    "import src.tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "from src.app",
    "import src.app",
    "from src.storage",
    "import src.storage",
    "requests",
    "httpx",
    "urllib",
    "openai",
    "anthropic",
    "psycopg",
    "sqlite",
    "subprocess",
    "run_prefilter(",
    "score_resume_job_match(",
    "run_chat_completion",
    "build_final_replacement_plan(",
    "submit_application(",
    "execute_application(",
    "overwrite_resume(",
    "mutate_resume(",
    "provider_call(",
    "network_call(",
)

FORBIDDEN_WRITE_MARKERS = (
    ".update(",
    "update(",
    ".write_text(",
    ".write_bytes(",
    ".mkdir(",
    ".save(",
    ".insert(",
)

DOC_MARKERS = (
    "phase 44a controlled exact resume change-set provider call boundary default-off",
    "controlled exact resume change-set provider call boundary",
    "first controlled provider-call boundary after phase 43",
    "not a default background llm call",
    "not resume mutation",
    "provider call is explicit/manual-triggered only",
    "default-off behavior does not call provider",
    "accepts an injected provider callable",
    "does not import provider sdks",
    "does not call network directly",
    "calls the injected provider callable only when enabled and manually confirmed",
    "captures provider response without validating deeply",
    "provider response validation comes in a later phase",
    "does not call tailoring runtime",
    "does not generate real tailoring output by itself",
    "does not produce a full resume",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
    "no auto-apply",
    "no auto-submit",
    "manual user control remains required",
    "existing ui/manual control remains the acceptance point",
    "exact worthy changes must be manually accepted by the user",
    "resume overwrite is not needed",
    "application execution is not needed",
    "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
    "phase43b-controlled-exact-resume-change-set-llm-request-packet-dry-run-command-default-off-v1",
    "phase43a-controlled-exact-resume-change-set-llm-request-packet-default-off-v1",
    "phase42-exact-resume-change-set-proposal-builder-release-v1",
    "phase42b-exact-resume-change-set-proposal-builder-dry-run-command-default-off-v1",
    "phase42a-exact-resume-change-set-proposal-builder-default-off-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py": "acaf694a08f65a5e646d2cbcc7b83a394ea1d15416c7311e230c86536d0a6b0f",
    "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py": "8baca68f6d8ba882324d028a68372d0d618709413bebe47931c93da5ef6dc175",
    "src/agents/exact_resume_change_set_proposal_builder_default_off.py": "fd173ea8bf3f7d746ebbdb7d6b2af7ae7df1aeaea4e66acaca52ea4fda1a9dc4",
    "run_exact_resume_change_set_proposal_builder_dry_run.py": "a8ea3201f0e71e463e316abdcf813b8d08fa3a473cd3dddcee158b87f3442451",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _request_packet(**overrides):
    packet = {
        "request_type": "exact_resume_change_set_refinement",
        "manual_trigger_required": True,
        "request_messages": [{"role": "user", "content": {"change_proposals": []}}],
        "request_schema": {"type": "object"},
        "provider_call_performed": False,
        "network_call_performed": False,
    }
    for key, value in overrides.items():
        packet[key] = value
    return packet


def test_helper_exists_and_is_import_safe():
    module = importlib.reload(boundary)
    assert callable(
        module.build_controlled_exact_resume_change_set_provider_call_boundary_default_off
    )


def test_missing_request_packet_blocks_with_missing_input_reason():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off()

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "44A"
    assert payload["request_packet_present"] is False
    assert payload["request_packet_valid"] is False
    assert payload["provider_call_allowed"] is False
    assert payload["provider_call_attempted"] is False
    assert "request_packet" in payload["missing_inputs"]
    assert "valid request packet required" in payload["provider_call_blocked_reason"]


def test_request_result_with_request_packet_is_accepted():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_result={"request_packet": _request_packet()},
    )

    assert payload["request_packet_present"] is True
    assert payload["request_packet_valid"] is True
    assert payload["provider_call_findings"]["request_packet_source"] == "request_result.request_packet"


def test_nested_request_result_request_packet_is_accepted():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_result={"request_result": {"request_packet": _request_packet()}},
    )

    assert payload["request_packet_valid"] is True
    assert (
        payload["provider_call_findings"]["request_packet_source"]
        == "request_result.request_result.request_packet"
    )


def test_nested_request_packet_request_packet_is_accepted():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_result={"request_packet": {"request_packet": _request_packet()}},
    )

    assert payload["request_packet_valid"] is True
    assert (
        payload["provider_call_findings"]["request_packet_source"]
        == "request_result.request_packet.request_packet"
    )


def test_explicit_request_packet_takes_precedence_over_request_result():
    explicit = _request_packet(request_id="explicit")
    nested = _request_packet(request_id="nested")
    seen = []

    def provider(packet):
        seen.append(packet)
        return {"ok": True}

    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=explicit,
        request_result={"request_packet": nested},
        provider_callable=provider,
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert payload["provider_call_performed"] is True
    assert seen[0]["request_id"] == "explicit"
    assert payload["provider_call_findings"]["request_packet_source"] == "request_packet"


def test_invalid_request_packet_shape_blocks():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=["bad"],
    )

    assert payload["request_packet_present"] is False
    assert payload["request_packet_valid"] is False
    assert "request_packet" in payload["missing_inputs"]
    assert payload["provider_call_performed"] is False


def test_invalid_request_type_blocks():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(request_type="other"),
        provider_policy={"allow_provider_call": True},
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_callable=lambda packet: {"ok": True},
    )

    assert payload["request_packet_present"] is True
    assert payload["request_packet_valid"] is False
    assert "request packet type" in payload["provider_call_blocked_reason"]
    assert payload["provider_call_attempted"] is False


def test_default_behavior_does_not_call_provider():
    calls = []

    def provider(packet):
        calls.append(packet)
        return {"ok": True}

    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        provider_callable=provider,
    )

    assert calls == []
    assert payload["provider_call_allowed"] is False
    assert payload["provider_call_performed"] is False
    assert payload["llm_call_performed"] is False
    assert "enable_provider_call" in payload["provider_call_blocked_reason"]


def test_enable_provider_call_false_blocks_even_when_policy_allows():
    calls = []
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        provider_callable=lambda packet: calls.append(packet),
        enable_provider_call=False,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert calls == []
    assert payload["provider_call_allowed"] is False
    assert "enable_provider_call" in payload["provider_call_blocked_reason"]


def test_provider_policy_allow_provider_call_false_blocks():
    calls = []
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        provider_callable=lambda packet: calls.append(packet),
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": False},
    )

    assert calls == []
    assert payload["provider_call_allowed"] is False
    assert "policy must allow" in payload["provider_call_blocked_reason"]


def test_manual_trigger_confirmed_false_blocks_when_required():
    calls = []
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        provider_callable=lambda packet: calls.append(packet),
        enable_provider_call=True,
        manual_trigger_confirmed=False,
        provider_policy={"allow_provider_call": True, "require_manual_trigger": True},
    )

    assert calls == []
    assert payload["provider_call_allowed"] is False
    assert "manual trigger confirmation required" in payload["provider_call_blocked_reason"]


def test_missing_provider_callable_blocks_when_required():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True, "require_provider_callable": True},
    )

    assert payload["provider_callable_present"] is False
    assert payload["provider_callable_valid"] is False
    assert "provider_callable" in payload["missing_inputs"]
    assert "valid provider callable required" in payload["provider_call_blocked_reason"]


def test_all_gates_pass_calls_injected_provider_callable_exactly_once_with_copy():
    calls = []
    packet = _request_packet(messages=[{"role": "user"}])

    def provider(received):
        calls.append(received)
        received["mutated_by_provider"] = True
        return {
            "refined_change_proposals": [
                {"proposal_id": "p1", "proposed_text": "Refined text"}
            ]
        }

    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=packet,
        provider_callable=provider,
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert len(calls) == 1
    assert "mutated_by_provider" not in packet
    assert payload["provider_call_allowed"] is True
    assert payload["provider_call_attempted"] is True
    assert payload["provider_call_performed"] is True
    assert payload["llm_call_performed"] is True
    assert payload["network_call_performed"] is False
    assert payload["provider_response"]["refined_change_proposals"][0]["proposal_id"] == "p1"
    assert payload["provider_response_summary"]["provider_response_validation_performed"] is False


def test_provider_callable_exception_is_captured_without_crashing():
    def provider(packet):
        raise RuntimeError("boom")

    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        provider_callable=provider,
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert payload["provider_call_attempted"] is True
    assert payload["provider_call_performed"] is False
    assert payload["llm_call_performed"] is False
    assert payload["provider_response"] is None
    assert payload["provider_call_blocked_reason"] == "provider callable raised error"
    assert "RuntimeError: boom" in payload["provider_call_result"]["provider_error"]


def test_inputs_are_not_mutated_and_payload_contains_no_callback():
    packet = _request_packet()
    result = {"request_packet": _request_packet(request_id="nested")}
    snapshots = (deepcopy(packet), deepcopy(result))

    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=packet,
        request_result=result,
        provider_callable=lambda request_packet: {"ok": True},
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert packet == snapshots[0]
    assert result == snapshots[1]
    assert "provider_callable" not in payload
    assert payload["provider_call_findings"]["function_pointers_included"] is False


def test_response_truncation_is_deterministic():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        provider_callable=lambda request_packet: "abcdef",
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True, "max_response_chars": 3},
    )

    assert payload["provider_response"]["response_truncated"] is True
    assert payload["provider_response"]["response_excerpt"] == "abc"


def test_all_runtime_effect_flags_remain_false_after_successful_provider_boundary_call():
    payload = build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
        request_packet=_request_packet(),
        provider_callable=lambda request_packet: {"ok": True},
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
    assert "full_resume" not in payload
    assert "real_tailoring_output" not in payload


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = HELPER_PATH.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_include_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_hashes_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected, relative


def test_changed_files_are_limited_to_phase44a_and_legacy_guards():
    allowed = {
        "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
        "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_default_off.md",
        "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py",
        "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.md",
        "tests/test_phase44b_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_default_off.md",
                "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.md",
                "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
                "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_default_off.md",
                "tests/test_phase46a_controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
        "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py",
        "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.md",
        "tests/test_phase46b_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.md",
        "tests/test_phase47a_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.md",
        "tests/test_phase47b_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.md",
        "tests/test_phase48a_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase48b_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.md",
        "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.md",
        "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
            "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
            "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.md",
            "tests/test_phase50a_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py",
        "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.md",
        "tests/test_phase50b_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_default_off.md",
        "tests/test_phase51a_controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.md",
        "tests/test_phase51b_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.md",
        "tests/test_phase52a_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase52b_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.md",
        "tests/test_phase53a_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "run_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.md",
        "tests/test_phase53b_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
        "docs/phase54_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.md",
        "tests/test_phase54a_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",

        "tests/test_phase44a_controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
    }
    legacy_guards = {
        path
        for path in _changed_files()
        if path.startswith("tests/test_") and path.endswith(".py")
    }
    assert _changed_files() <= allowed | legacy_guards


def _changed_files() -> set[str]:
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}

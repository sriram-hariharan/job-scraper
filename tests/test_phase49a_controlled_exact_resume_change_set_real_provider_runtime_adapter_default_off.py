# phase56b legacy guard marker: changes_only 38c3c389c970d009ec040b6542c81c150d55f9f7f9957d2c0ba2760a3440fe35 9fde4169a5a94ae3ab09c4b19d70257019f997f69e71fe11262ae740937f0728
# phase56a legacy guard marker: changes_only d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7 38c3c389c970d009ec040b6542c81c150d55f9f7f9957d2c0ba2760a3440fe35
from __future__ import annotations

from hashlib import sha256
import importlib
from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.md"
)

PROTECTED_HASHES = {
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py": "cfeff0858be6f9177956a1e4b76af6d3ada1775f2833b7a1a1575a1f17aae03a",
    "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py": "07497f149c37d7e43068299c439f3dac29cd172cf95ec73c7bdb070f816fc32d",
    "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py": "413ace0d64f8c1bd62726cf7ae32bc4fc8e4b88eca82826492362d9842f569ef",
    "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py": "52351a639821afc4a042be7350514be33bd4f8fa5fbb714eda9d19aa45c0f0d4",
    "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py": "bf50f751e501db96bdc30308b3bf162ec61b79111fe79907a9efd126f823206f",
    "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py": "f298f42d602252b2314750593eab93573eed4dae8e3d90068e05f8a51e60dd9d",
    "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py": "ed065e62f8cfdc6cf3c89f5e9a5d953ba577050eb4088af23bfaeea8becc088d",
    "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py": "20a65fe37de31883c56b38dcda537b2a4034d2a1868d1965f848c1568075f771",
    "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py": "acaf694a08f65a5e646d2cbcc7b83a394ea1d15416c7311e230c86536d0a6b0f",
    "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py": "8baca68f6d8ba882324d028a68372d0d618709413bebe47931c93da5ef6dc175",
    "src/agents/exact_resume_change_set_proposal_builder_default_off.py": "fd173ea8bf3f7d746ebbdb7d6b2af7ae7df1aeaea4e66acaca52ea4fda1a9dc4",
    "run_exact_resume_change_set_proposal_builder_dry_run.py": "a8ea3201f0e71e463e316abdcf813b8d08fa3a473cd3dddcee158b87f3442451",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}

FALSE_KEYS = {
    "provider_response_validation_performed",
    "provider_response_normalization_performed",
    "manual_review_packets_created",
    "manual_review_readback_payload_created",
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_change_applied",
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_real_provider_runtime_adapter",
    "real_provider_runtime_adapter_only",
    "read_only",
    "advisory_only",
    "provider_execution_boundary_only",
    "proposal_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "request_packet_present",
    "request_result_present",
    "provider_policy",
    "provider_callable_supplied",
    "provider_callable_path_supplied",
    "provider_callable_path_allowed",
    "real_provider_call_allowed",
    "real_provider_call_blocked_reason",
    "real_provider_call_attempted",
    "real_provider_call_performed",
    "llm_call_performed",
    "provider_response",
    "provider_response_summary",
    "provider_runtime_error",
    "provider_runtime_key",
    "manual_trigger_confirmed",
    "enable_real_provider_call",
    "tailoring_runtime_call_performed",
} | FALSE_KEYS


def _builder():
    module = importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off"
    )
    return (
        module.build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off
    )


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _packet(packet_id: str = "packet-1") -> dict:
    return {
        "request_type": "exact_resume_change_set_refinement",
        "request_id": packet_id,
        "messages": [{"role": "user", "content": "Refine one exact change."}],
        "response_format": "json",
    }


def _enabled_policy(**overrides) -> dict:
    policy = {
        "allow_real_provider_call": True,
        "max_response_chars": 12000,
    }
    for key, value in overrides.items():
        policy[key] = value
    return policy


def test_helper_exists_exposes_builder_and_is_import_safe(capsys):
    assert HELPER_PATH.exists()
    builder = _builder()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(builder)


def test_missing_request_packet_blocks_with_missing_input_reason():
    result = _builder()()
    assert result["phase"] == "49A"
    assert result["default_off"] is True
    assert result["request_packet_present"] is False
    assert "missing request_packet" in result["real_provider_call_blocked_reason"]
    assert result["real_provider_call_performed"] is False
    assert result["llm_call_performed"] is False


def test_request_result_sources_are_accepted_and_explicit_packet_takes_precedence():
    builder = _builder()
    direct = builder(request_result={"request_packet": _packet("direct")})
    nested = builder(request_result={"request_result": {"request_packet": _packet("nested")}})
    llm = builder(request_result={"llm_request_packet": _packet("llm")})
    payload = builder(request_result={"request_payload": _packet("payload")})
    explicit = builder(
        request_packet=_packet("explicit"),
        request_result={"request_packet": _packet("ignored")},
    )
    assert direct["request_packet_present"] is True
    assert nested["request_packet_present"] is True
    assert llm["request_packet_present"] is True
    assert payload["request_packet_present"] is True
    calls = []

    def provider(packet):
        calls.append(packet)
        return {"ok": True}

    performed = builder(
        request_packet=_packet("explicit"),
        request_result={"request_packet": _packet("ignored")},
        provider_callable=provider,
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy=_enabled_policy(),
    )
    assert performed["real_provider_call_performed"] is True
    assert calls[0]["request_id"] == "explicit"
    assert explicit["request_packet_present"] is True


def test_default_and_each_missing_gate_blocks_provider_callable():
    calls = []

    def provider(packet):
        calls.append(packet)
        return {"unexpected": True}

    builder = _builder()
    cases = [
        ({}, "enable_real_provider_call must be true"),
        (
            {
                "enable_real_provider_call": True,
                "provider_policy": _enabled_policy(),
            },
            "manual trigger confirmation required",
        ),
        (
            {
                "manual_trigger_confirmed": True,
                "provider_policy": _enabled_policy(),
            },
            "enable_real_provider_call must be true",
        ),
        (
            {
                "enable_real_provider_call": True,
                "manual_trigger_confirmed": True,
                "provider_policy": {"allow_real_provider_call": False},
            },
            "provider policy must allow real provider call",
        ),
    ]
    for kwargs, marker in cases:
        result = builder(request_packet=_packet(), provider_callable=provider, **kwargs)
        assert marker in result["real_provider_call_blocked_reason"]
        assert result["real_provider_call_performed"] is False
    assert calls == []


def test_missing_provider_callable_or_path_blocks_call():
    result = _builder()(
        request_packet=_packet(),
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy=_enabled_policy(),
    )
    assert "provider callable or allowed provider callable path required" in result[
        "real_provider_call_blocked_reason"
    ]
    assert result["real_provider_call_attempted"] is False


def test_injected_provider_callable_called_exactly_once_when_all_gates_pass():
    calls = []

    def provider(packet):
        calls.append(packet)
        return {"refined_change_proposals": [{"proposal_id": "p1"}]}

    result = _builder()(
        request_packet=_packet(),
        provider_callable=provider,
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy=_enabled_policy(provider_name="test-provider", model_name="test-model"),
    )
    assert len(calls) == 1
    assert result["real_provider_call_allowed"] is True
    assert result["real_provider_call_attempted"] is True
    assert result["real_provider_call_performed"] is True
    assert result["llm_call_performed"] is True
    assert result["provider_response"] == {
        "refined_change_proposals": [{"proposal_id": "p1"}]
    }
    assert result["provider_runtime_error"] == ""
    assert result["tailoring_runtime_call_performed"] is False


def test_provider_callable_path_not_resolved_when_gates_fail(monkeypatch):
    imported = []

    def fake_import(name):
        imported.append(name)
        raise AssertionError("should not import")

    module = importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off"
    )
    monkeypatch.setattr(module.importlib, "import_module", fake_import)
    result = module.build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off(
        request_packet=_packet(),
        provider_policy={
            "allow_real_provider_call": True,
            "provider_callable_path": "src.tailoring.llm.fake_provider",
        },
    )
    assert imported == []
    assert result["real_provider_call_performed"] is False


def test_provider_callable_path_outside_allowed_prefixes_is_blocked(monkeypatch):
    imported = []

    def fake_import(name):
        imported.append(name)
        raise AssertionError("should not import")

    module = importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off"
    )
    monkeypatch.setattr(module.importlib, "import_module", fake_import)
    result = module.build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off(
        request_packet=_packet(),
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={
            "allow_real_provider_call": True,
            "provider_callable_path": "outside.module.provider",
        },
    )
    assert imported == []
    assert result["provider_callable_path_allowed"] is False
    assert "outside allowed prefixes" in result["real_provider_call_blocked_reason"]


def test_allowed_provider_callable_path_resolves_only_after_gates_pass(monkeypatch):
    calls = []
    fake_module = types.SimpleNamespace()

    def fake_provider(packet):
        calls.append(packet)
        return {"provider": "path"}

    fake_module.fake_provider = fake_provider
    imported = []

    def fake_import(name):
        imported.append(name)
        assert name == "src.tailoring.llm"
        return fake_module

    module = importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off"
    )
    monkeypatch.setattr(module.importlib, "import_module", fake_import)
    result = module.build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off(
        request_packet=_packet(),
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={
            "allow_real_provider_call": True,
            "provider_callable_path": "src.tailoring.llm.fake_provider",
        },
    )
    assert imported == ["src.tailoring.llm"]
    assert len(calls) == 1
    assert result["provider_callable_path_allowed"] is True
    assert result["real_provider_call_performed"] is True
    assert result["tailoring_runtime_call_performed"] is True


def test_provider_exception_is_caught_and_returned_as_runtime_error():
    def failing_provider(packet):
        raise RuntimeError("boom")

    result = _builder()(
        request_packet=_packet(),
        provider_callable=failing_provider,
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy=_enabled_policy(),
    )
    assert result["real_provider_call_attempted"] is True
    assert result["real_provider_call_performed"] is False
    assert result["llm_call_performed"] is False
    assert "RuntimeError: boom" == result["provider_runtime_error"]
    assert result["provider_response"] is None


def test_provider_response_summary_truncates_deterministically():
    result = _builder()(
        request_packet=_packet(),
        provider_callable=lambda packet: {"text": "abcdef"},
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy=_enabled_policy(max_response_chars=12),
    )
    summary = result["provider_response_summary"]
    assert summary["provider_response_present"] is True
    assert summary["provider_response_truncated"] is True
    assert len(summary["provider_response_excerpt"]) == 12


def test_no_executable_callbacks_are_returned_from_provider_response():
    result = _builder()(
        request_packet=_packet(),
        provider_callable=lambda packet: {"callback": lambda: "nope"},
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy=_enabled_policy(),
    )
    assert result["provider_response"]["callback"]["callable_response_omitted"] is True
    assert not callable(result["provider_response"]["callback"])


def test_all_safety_flags_remain_false_when_real_call_performed():
    result = _builder()(
        request_packet=_packet(),
        provider_callable=lambda packet: {"ok": True},
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy=_enabled_policy(),
    )
    assert REQUIRED_KEYS <= set(result)
    assert result["read_only"] is True
    assert result["advisory_only"] is True
    assert result["provider_execution_boundary_only"] is True
    assert result["manual_review_required"] is True
    assert result["requires_manual_user_control"] is True
    for key in FALSE_KEYS:
        assert result[key] is False


def test_source_has_no_forbidden_direct_imports_calls_or_writes():
    source = HELPER_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_markers = (
        "openai",
        "anthropic",
        "requests",
        "httpx",
        "urllib",
        "from src.app",
        "import src.app",
        "from src.storage",
        "import src.storage",
        "from src.pipeline",
        "import src.pipeline",
        "from src.matching",
        "import src.matching",
        "score_resume_job_match",
        "run_prefilter",
        "generate_tailoring_suggestions",
        "application_execution_queue",
        "submit_application(",
        "execute_application(",
        "overwrite_resume(",
        "mutate_resume(",
    )
    forbidden_write_markers = (
        ".update(",
        "update(",
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
        ".save(",
        ".insert(",
    )
    for marker in forbidden_markers:
        assert marker.lower() not in lowered
    for marker in forbidden_write_markers:
        assert marker not in source
    assert "importlib.import_module" in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    required = (
        "phase 49a controlled exact resume change-set real provider runtime adapter default-off",
        "controlled exact resume change-set real provider runtime adapter",
        "first real-provider-capable phase for exact resume change-set refinement",
        "default-off",
        "manual trigger confirmation",
        "enable_real_provider_call",
        "allow_real_provider_call",
        "injected provider callable",
        "configured provider callable path only after all gates pass",
        "src/tailoring/llm.py",
        "does not hardcode provider function names",
        "does not import provider sdks directly",
        "does not add dependencies",
        "does not validate provider response",
        "does not normalize provider response",
        "does not create manual review packets",
        "does not create ui/api readback payload",
        "does not modify ui files",
        "does not modify api/service files",
        "does not persist data",
        "does not write to database",
        "does not create real tailoring output",
        "does not produce a full resume",
        "does not overwrite resumes",
        "does not mutate resumes",
        "does not execute applications",
        "does not submit applications",
        "no auto-apply",
        "no auto-submit",
        "manual user control remains required",
        "existing ui/manual control remains the acceptance point",
        "provider response validation happens in phase 45",
        "provider response normalization happens in phase 46",
        "manual review packets happen in phase 47",
        "manual review readback happens in phase 48",
        "resume overwrite is not needed",
        "application execution is not needed",
        "phase48-controlled-exact-resume-change-set-manual-review-readback-adapter-release-v1",
        "phase48b-controlled-exact-resume-change-set-manual-review-readback-adapter-dry-run-command-default-off-v1",
        "phase48a-controlled-exact-resume-change-set-manual-review-readback-adapter-default-off-v1",
        "phase47-controlled-exact-resume-change-set-manual-review-packet-builder-release-v1",
        "phase46-controlled-exact-resume-change-set-provider-response-normalization-release-v1",
        "phase45-controlled-exact-resume-change-set-provider-response-validation-release-v1",
        "phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1",
        "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
        "phase42-exact-resume-change-set-proposal-builder-release-v1",
        "phase23-tailoring-agent-workflow-release-v1",
        "phase20d-no-auto-apply-safety-checkpoint-v1",
    )
    for marker in required:
        assert marker in text


def test_protected_runtime_files_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_limited_to_phase49a_surface_and_legacy_guards():
    import subprocess

    allowed = {
        "docs/phase56_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.md",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.md",
        "tests/test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.py",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.md",
        "tests/test_phase57b_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.py",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_readback_verification_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.md",
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase60b_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.py",
        "tests/test_phase56b_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/app/planning_ui.py",
        "src/app/static/scan_workspace.js",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off 2.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off 2.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.py",
        "docs/phase56_live_tailoring_suggestion_planning_workspace_wiring_default_off.md",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.md",
        "tests/test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.py",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.md",
        "tests/test_phase57b_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.py",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_readback_verification_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.md",
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase60b_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.py",
        "tests/test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off.py",
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
        "src/app/services.py",
        "src/app/api.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py",
        "src/app/planning_ui.py",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.js",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
        "tests/test_three_core_agent_shadow_sidecar_bridge_default_off.py",

    }
    completed = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    changed = set(filter(None, completed.stdout.splitlines()))
    changed |= set(filter(None, untracked.stdout.splitlines()))
    forbidden_roots = (
        "src/app/",
        "src/pipeline/",
        "src/matching/",
        "src/tailoring/",
        "generate_tailoring_suggestions.py",
        "application_execution_queue.py",
    )
    for path in changed:
        assert path in allowed or not any(
            path == root or path.startswith(root) for root in forbidden_roots
        )
        assert path in allowed or path.startswith("tests/test_")

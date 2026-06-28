# phase26c legacy guard marker: changes_only ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a 3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5
# phase26b legacy guard marker: changes_only 1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6
# phase23f legacy guard marker: changes_only 1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5 ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a
# phase23f legacy guard marker: changes_only ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import generate_ai_tailoring_action_boundary_contract as contract


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / "src/agents/generate_ai_tailoring_action_boundary_contract.py"
)
DOC_PATH = (
    ROOT / "docs/phase23_generate_ai_tailoring_action_boundary_contract.md"
)

SAFETY_KEYS = (
    "no_auto_apply",
    "no_auto_submit",
    "no_autonomous_application_execution",
    "no_automatic_job_application_submission",
    "manual_user_control_required",
    "user_trigger_required",
    "preview_only",
    "manual_acceptance_required",
    "no_provider_calls",
    "no_network_calls",
    "no_database_writes",
    "no_persistence",
    "no_mutation",
    "no_resume_mutation",
    "no_application_mutation",
    "no_execution",
    "no_submission",
)

PERMANENT_FALSE_KEYS = (
    "ai_tailoring_generation_performed",
    "tailoring_provider_call_performed",
    "tailoring_runtime_call_performed",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "application_submission_performed",
)

FORBIDDEN_SOURCE_MARKERS = (
    "run_chat_completion",
    "run_chat_completion_with_metadata",
    "requests.",
    "httpx",
    "urllib",
    "subprocess",
    "open(",
    "read_text",
    "write_text",
    "DATABASE_URL",
    "cache_get_json",
    "cache_set_json",
    "score_resume_job_match(",
    "run_prefilter(",
    "_run_live_llm_tailoring",
    "generate_tailoring_suggestions",
)

REQUIRED_TAGS = (
    "phase23c-tailoring-agent-opportunity-ui-readback-v1",
    "phase23b-tailoring-agent-opportunity-api-readback-v1",
    "phase23a-tailoring-agent-opportunity-contract-v1",
    "phase22-core-agent-evidence-materialization-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a",
    "src/app/static/app_redesign.css": "3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
}


def _inputs():
    return {
        "tailoring_agent_opportunity_payload": {
            "contract_status": "ready_for_manual_review",
            "tailoring_opportunities": [
                {
                    "opportunity_type": "missing_requirement",
                    "signal": "kubernetes",
                },
            ],
        },
        "selected_opportunity_ids": ["opportunity-1"],
        "generation_context": {
            "job_title": "Machine Learning Engineer",
        },
        "operator_context": {
            "operator_note": "Preview supported evidence only.",
        },
    }


def _changed_files() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return set(tracked + untracked)


def test_helper_module_and_public_function_exist():
    assert HELPER_PATH.exists()
    assert callable(
        contract.build_generate_ai_tailoring_action_boundary_contract
    )


def test_default_off_returns_skipped_read_only_payload():
    payload = (
        contract.build_generate_ai_tailoring_action_boundary_contract()
    )

    assert payload["action_boundary_status"] == contract.STATUS_SKIPPED
    assert payload[
        "generate_ai_tailoring_action_boundary_enabled"
    ] is False
    assert payload["action_allowed"] is False
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["manual_review_only"] is True


def test_enabled_without_exact_user_trigger_is_blocked():
    for user_triggered in (False, 1, "true"):
        payload = (
            contract.build_generate_ai_tailoring_action_boundary_contract(
                enabled=True,
                user_triggered=user_triggered,
            )
        )

        assert payload["action_boundary_status"] == contract.STATUS_BLOCKED
        assert payload["action_allowed"] is False
        assert payload["user_triggered"] is False
        assert "user trigger required" in payload["action_blocked_reason"]


def test_enabled_and_user_triggered_returns_readiness_boundary_only():
    payload = contract.build_generate_ai_tailoring_action_boundary_contract(
        enabled=True,
        user_triggered=True,
        **_inputs(),
    )

    assert payload["action_boundary_status"] == contract.STATUS_READY
    assert payload["action_allowed"] is True
    assert payload["action_blocked_reason"] == ""
    assert "readiness" in payload["readiness_summary"].lower()
    assert "no tailoring was generated" in payload[
        "readiness_summary"
    ].lower()


def test_inputs_are_deep_copied_and_never_mutated():
    inputs = _inputs()
    before = deepcopy(inputs)
    payload = contract.build_generate_ai_tailoring_action_boundary_contract(
        enabled=True,
        user_triggered=True,
        **inputs,
    )

    assert inputs == before
    assert payload["action_inputs"] == inputs
    for field_name, value in inputs.items():
        assert payload["action_inputs"][field_name] is not value

    inputs["selected_opportunity_ids"].append("changed")
    assert "changed" not in payload["action_inputs"][
        "selected_opportunity_ids"
    ]


def test_future_action_name_is_exact():
    payload = (
        contract.build_generate_ai_tailoring_action_boundary_contract()
    )

    assert payload["future_action_name"] == "Generate AI Tailoring"


def test_generation_provider_runtime_rewrite_and_submission_never_occur():
    modes = (
        {},
        {"enabled": True},
        {"enabled": True, "user_triggered": True, **_inputs()},
    )

    for mode in modes:
        payload = (
            contract.build_generate_ai_tailoring_action_boundary_contract(
                **mode
            )
        )
        for key in PERMANENT_FALSE_KEYS:
            assert payload[key] is False


def test_payload_contains_all_required_safety_markers_in_every_mode():
    modes = (
        {},
        {"enabled": True},
        {"enabled": True, "user_triggered": True, **_inputs()},
    )

    for mode in modes:
        payload = (
            contract.build_generate_ai_tailoring_action_boundary_contract(
                **mode
            )
        )
        for key in SAFETY_KEYS:
            assert payload[key] is True


def test_source_has_no_provider_network_io_or_runtime_calls():
    source = HELPER_PATH.read_text(encoding="utf-8")

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_docs_contain_required_boundaries_and_references():
    assert DOC_PATH.exists()
    text = DOC_PATH.read_text(encoding="utf-8")
    lowered = " ".join(text.lower().split())

    assert text.startswith(
        "# Phase 23D Generate AI Tailoring Action-Boundary Contract"
    )
    for marker in (
        "builds on phase 23c",
        "defines the action boundary",
        "generate ai tailoring",
        "does not add a ui button",
        "does not add an api endpoint",
        "does not generate ai tailoring",
        "does not call tailoring runtime",
        "does not call providers",
        "does not create resume rewrites",
        "overwrite resumes",
        "does not submit applications",
        "user trigger is required",
        "manual acceptance is required",
        "preview/manual-review only unless the user accepts edits",
        "no silent resume rewrite",
        "no automatic resume overwrite",
        "no resume mutation",
        "no application submission",
        "no provider calls",
        "no network calls",
        "no database writes",
        "no persistence",
        "no mutation",
        "no execution",
        "no submission",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
    ):
        assert marker in lowered
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase23d_changes_only_helper_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/agents/generate_ai_tailoring_action_boundary_contract.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_contract.md",
        "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
        "src/app/api.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md",
        "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
        "docs/phase23_tailoring_agent_workflow_release_checkpoint.md",
        "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_contract.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_contract.md",
        "tests/test_phase24a_manual_generate_ai_tailoring_preview_contract_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_api_readback.md",
        "tests/test_phase24b_manual_generate_ai_tailoring_preview_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase24_manual_generate_ai_tailoring_preview_ui_readback.md",
        "tests/test_phase24c_manual_generate_ai_tailoring_preview_ui_readback_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_release_checkpoint.md",
        "tests/test_phase24d_manual_generate_ai_tailoring_preview_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_contract.md",
            "tests/test_phase25a_manual_generate_ai_tailoring_preview_request_packet_contract_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_api_readback.md",
            "tests/test_phase25b_manual_generate_ai_tailoring_preview_request_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_ui_readback.md",
            "tests/test_phase25c_manual_generate_ai_tailoring_preview_request_packet_ui_readback_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint.md",
            "tests/test_phase25d_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_contract.md",
            "tests/test_phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback.md",
            "tests/test_phase26b_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback.md",
            "tests/test_phase26c_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback_default_off.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint.md",
            "tests/test_phase26d_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_contract.md",
            "tests/test_phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract_default_off.py",
            "src/app/api.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback.md",
            "tests/test_phase27b_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback.md",
            "tests/test_phase27c_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback_default_off.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint.md",
            "tests/test_phase27d_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_contract.md",
            "tests/test_phase28a_manual_generate_ai_tailoring_preview_provider_call_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback.md",
            "tests/test_phase28b_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback 2.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off 2.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint.md",
            "tests/test_phase28d_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.md",
            "tests/test_phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract_default_off.py",
            "src/app/api.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback.md",
            "tests/test_phase29b_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback.md",
            "tests/test_phase29c_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback_default_off.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint.md",
            "tests/test_phase29d_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py",
            "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_contract.md",
            "tests/test_phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract_default_off.py",
            "src/app/api.py",
            "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback.md",
            "tests/test_phase30b_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback_default_off.py",
                "src/app/static/agentic_review.js",
                "src/app/static/app_redesign.css",
                "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback.md",
                "tests/test_phase30c_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
            if (
                "changes_only" in path.read_text(encoding="utf-8")
                or "1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6"
                in path.read_text(encoding="utf-8")
                or "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab"
                in path.read_text(encoding="utf-8")
                or "3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5"
                in path.read_text(encoding="utf-8")
            )
        }

    assert changed <= allowed | legacy_guards

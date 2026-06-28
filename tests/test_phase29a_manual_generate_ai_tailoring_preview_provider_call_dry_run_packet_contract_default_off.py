from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents.manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract import (
    build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "provider_call_dry_run_packet_contract_only",
    "dry_run_only",
    "requires_user_trigger",
    "user_trigger_present",
    "operator_confirmation_required",
    "operator_confirmation_present",
    "manual_acceptance_required",
    "provider_call_boundary_required",
    "provider_call_boundary_accepted",
    "provider_request_envelope_required",
    "provider_request_envelope_accepted",
    "provider_configuration_required",
    "provider_configuration_present",
    "provider_call_policy_required",
    "provider_call_policy_present",
    "dry_run_packet_ready",
    "provider_call_allowed_for_future_manual_preview",
    "blocked_reasons",
    "missing_inputs",
    "dry_run_packet",
    "deterministic_dry_run_packet_key",
    "no_provider_calls",
    "provider_call_performed",
    "no_network_calls",
    "network_call_performed",
    "dispatch_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
    "next_safe_step",
}

TRUE_SAFETY_KEYS = {
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "provider_call_dry_run_packet_contract_only",
    "dry_run_only",
    "requires_user_trigger",
    "operator_confirmation_required",
    "manual_acceptance_required",
    "provider_call_boundary_required",
    "provider_request_envelope_required",
    "provider_configuration_required",
    "provider_call_policy_required",
    "no_provider_calls",
    "no_network_calls",
}

FALSE_ACTION_KEYS = {
    "provider_call_performed",
    "network_call_performed",
    "dispatch_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
}

PROTECTED_HASHES = {
    "src/app/api.py": "1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "ca378dc0aee655d83a7af0d15e885313af5b719c2512eff10f3efc69cd43348a",
    "src/app/static/app_redesign.css": "3c55b13f7762c2118eabad4a32ca6c6a47b9674be44ac33058d3b55f97c4e5c5",
    "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py": "8e4b2a93d535f37387283b943d4a31fc3ff1c23016d2958132e2362a74f97f7b",
    "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py": "e1c9f6f55b7d8a8c0171b52d7e891d531aae0ad3384eb74d686f50ba4e59533f",
    "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py": "2fdc984c5ee395d43e71fd2ce991b9575316f8714188cc16a13c97c73074996f",
    "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py": "4e0dcc111f114551b0ce1c88f8d57618546306c4bcce8ac2d6df86b44cbfa60d",
    "src/agents/manual_generate_ai_tailoring_preview_contract.py": "98e2c69010061fa8e98cf50541f88537ad9eaff72c7c13a270e57822196eeb45",
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}

FORBIDDEN_SOURCE_MARKERS = (
    "from src.tailoring",
    "import src.tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "from src.app",
    "import src.app",
    "from src.storage",
    "import src.storage",
    "database_url",
    "psycopg",
    "sqlite",
    "subprocess",
    "requests",
    "httpx",
    "openai",
    "anthropic",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "execute_application",
    "submit_application",
    "provider_call(",
    "network_call(",
)

REQUIRED_DOC_MARKERS = (
    "# Phase 29A Manual Generate AI Tailoring Preview Provider-Call Dry-Run Packet Contract",
    "Provider-call dry-run packet contract only",
    "Dry-run only",
    "Default-off",
    "Read-only",
    "Advisory-only",
    "Manual-review only",
    "User trigger required",
    "Operator confirmation required",
    "Manual acceptance required",
    "Provider-call boundary required",
    "Provider request-envelope required",
    "Provider configuration required",
    "Provider call policy required",
    "Does not call providers",
    "Does not call network",
    "Does not dispatch",
    "Does not generate AI tailoring",
    "Does not call tailoring runtime",
    "Does not create real tailoring output",
    "Does not create resume rewrites",
    "Does not overwrite resumes",
    "Does not mutate resumes",
    "Does not persist data",
    "Does not write to database",
    "Does not execute applications",
    "Does not submit applications",
    "No provider calls",
    "No network calls",
    "No database writes",
    "No persistence",
    "No mutation",
    "No resume mutation",
    "No application mutation",
    "No execution",
    "No submission",
    "No auto-apply",
    "No auto-submit",
    "No autonomous application execution",
    "No automatic job application submission",
    "Tailoring agent remains separate from final scoring",
    (
        "Generated tailoring suggestions must remain preview/manual-review "
        "only unless user accepts edits in a later phase"
    ),
    "This phase does not create real tailoring output",
    "This phase does not add a UI action control",
    "phase28-manual-generate-ai-tailoring-preview-provider-call-boundary-release-v1",
    (
        "phase28d-manual-generate-ai-tailoring-preview-provider-call-boundary-"
        "release-checkpoint-v1"
    ),
    (
        "phase28c-manual-generate-ai-tailoring-preview-provider-call-boundary-"
        "ui-readback-v1"
    ),
    (
        "phase28b-manual-generate-ai-tailoring-preview-provider-call-boundary-"
        "api-readback-v1"
    ),
    (
        "phase28a-manual-generate-ai-tailoring-preview-provider-call-boundary-"
        "contract-v1"
    ),
    "phase27-manual-generate-ai-tailoring-preview-provider-request-envelope-release-v1",
    "phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1",
    "phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _ready_inputs() -> dict[str, dict]:
    return {
        "phase28_provider_call_boundary_payload": {
            "contract_status": (
                "manual_generate_ai_tailoring_preview_provider_call_boundary_ready"
            ),
            "provider_call_boundary_ready": True,
            "provider_call_allowed": True,
            "provider_call_performed": False,
            "network_call_performed": False,
            "dispatch_performed": False,
            "tailoring_runtime_call_performed": False,
            "ai_tailoring_generation_performed": False,
            "real_tailoring_output_created": False,
            "execution_performed": False,
            "submission_performed": False,
            "deterministic_provider_call_key": (
                "manual-generate-ai-tailoring-preview-provider-call-example"
            ),
        },
        "phase27_provider_request_envelope_payload": {
            "contract_status": (
                "manual_generate_ai_tailoring_preview_provider_request_envelope_ready"
            ),
            "provider_request_envelope_ready": True,
            "provider_request_allowed": True,
            "provider_call_performed": False,
            "network_call_performed": False,
            "tailoring_runtime_call_performed": False,
            "ai_tailoring_generation_performed": False,
            "real_tailoring_output_created": False,
            "execution_performed": False,
            "submission_performed": False,
            "deterministic_envelope_key": (
                "manual-generate-ai-tailoring-preview-provider-envelope-example"
            ),
        },
        "phase26_dispatch_boundary_payload": {
            "contract_status": (
                "manual_generate_ai_tailoring_preview_dispatch_boundary_ready"
            ),
            "dispatch_ready": True,
            "dispatch_allowed": True,
            "deterministic_dispatch_key": (
                "manual-generate-ai-tailoring-preview-dispatch-example"
            ),
        },
        "phase25_request_packet_payload": {
            "contract_status": (
                "manual_generate_ai_tailoring_preview_request_packet_ready"
            ),
            "preview_request_allowed": True,
            "request_packet": {
                "deterministic_request_key": (
                    "manual-generate-ai-tailoring-preview-request-example"
                ),
            },
        },
        "user_trigger_metadata": {
            "user_triggered": True,
            "generate_ai_tailoring_requested": True,
        },
        "operator_confirmation_metadata": {
            "operator_confirmed": True,
            "provider_call_dry_run_packet_confirmed": True,
        },
        "provider_configuration_metadata": {
            "provider_configuration_present": True,
            "provider_name": "manual-review-provider-stub",
            "model": "manual-review-model-stub",
        },
        "provider_call_policy_metadata": {
            "provider_call_policy_present": True,
            "provider_call_policy_id": "manual-review-policy-stub",
        },
    }


def test_helper_exists_and_returns_required_keys():
    result = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract()
    )

    assert result["phase"] == "29A"
    assert REQUIRED_KEYS <= result.keys()
    for key in TRUE_SAFETY_KEYS:
        assert result[key] is True
    for key in FALSE_ACTION_KEYS:
        assert result[key] is False
    assert result["dry_run_packet_ready"] is False
    assert result["provider_call_allowed_for_future_manual_preview"] is False


def test_no_user_trigger_blocks_readiness():
    inputs = _ready_inputs()
    inputs["user_trigger_metadata"] = {}

    result = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **inputs
        )
    )

    assert result["dry_run_packet_ready"] is False
    assert "user_trigger_metadata" in result["missing_inputs"]
    assert "explicit user trigger required" in result["blocked_reasons"]
    assert result["next_safe_step"] == "require_explicit_user_trigger"


def test_missing_operator_confirmation_blocks_readiness():
    inputs = _ready_inputs()
    inputs["operator_confirmation_metadata"] = {}

    result = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **inputs
        )
    )

    assert result["dry_run_packet_ready"] is False
    assert "operator_confirmation_metadata" in result["missing_inputs"]
    assert "operator confirmation required" in result["blocked_reasons"]
    assert result["next_safe_step"] == "require_operator_confirmation"


def test_missing_or_blocked_provider_call_boundary_blocks_readiness():
    missing = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **{
                **_ready_inputs(),
                "phase28_provider_call_boundary_payload": {},
            }
        )
    )
    blocked = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **{
                **_ready_inputs(),
                "phase28_provider_call_boundary_payload": {
                    "provider_call_boundary_ready": False,
                    "provider_call_allowed": False,
                },
            }
        )
    )

    assert missing["dry_run_packet_ready"] is False
    assert "phase28_provider_call_boundary_payload" in missing["missing_inputs"]
    assert "phase28 provider-call boundary payload required" in (
        missing["blocked_reasons"]
    )
    assert blocked["dry_run_packet_ready"] is False
    assert (
        "provider-call boundary must be accepted before dry-run packet"
        in blocked["blocked_reasons"]
    )


def test_missing_or_unaccepted_provider_request_envelope_blocks_readiness():
    missing = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **{
                **_ready_inputs(),
                "phase27_provider_request_envelope_payload": {},
            }
        )
    )
    blocked = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **{
                **_ready_inputs(),
                "phase27_provider_request_envelope_payload": {
                    "provider_request_envelope_ready": False,
                    "provider_request_allowed": False,
                },
            }
        )
    )

    assert missing["dry_run_packet_ready"] is False
    assert "phase27_provider_request_envelope_payload" in missing["missing_inputs"]
    assert "phase27 provider request-envelope payload required" in (
        missing["blocked_reasons"]
    )
    assert blocked["dry_run_packet_ready"] is False
    assert (
        "provider request-envelope must be accepted before dry-run packet"
        in blocked["blocked_reasons"]
    )


def test_missing_provider_configuration_and_policy_are_blocked():
    missing_configuration = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **{
                **_ready_inputs(),
                "provider_configuration_metadata": {},
            }
        )
    )
    missing_policy = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **{
                **_ready_inputs(),
                "provider_call_policy_metadata": {},
            }
        )
    )

    assert missing_configuration["dry_run_packet_ready"] is False
    assert "provider_configuration_metadata" in missing_configuration[
        "missing_inputs"
    ]
    assert "provider configuration metadata required" in missing_configuration[
        "blocked_reasons"
    ]
    assert missing_policy["dry_run_packet_ready"] is False
    assert "provider_call_policy_metadata" in missing_policy["missing_inputs"]
    assert "provider call policy metadata required" in missing_policy[
        "blocked_reasons"
    ]


def test_ready_stubs_mark_packet_ready_without_side_effects():
    first = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **_ready_inputs()
        )
    )
    second = (
        build_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract(
            **_ready_inputs()
        )
    )

    assert first == second
    assert first["dry_run_packet_ready"] is True
    assert first["provider_call_allowed_for_future_manual_preview"] is True
    assert first["blocked_reasons"] == []
    assert first["missing_inputs"] == []
    assert first["dry_run_packet"]["dry_run_packet_ready"] is True
    assert first["dry_run_packet"]["contains_generated_tailoring_text"] is False
    assert first["dry_run_packet"]["contains_real_tailoring_output"] is False
    assert "generated_tailoring_text" not in first["dry_run_packet"]
    assert "real_tailoring_output" not in first["dry_run_packet"]
    for key in FALSE_ACTION_KEYS:
        assert first[key] is False
    for marker in (
        "provider_call_performed",
        "network_call_performed",
        "dispatch_performed",
        "tailoring_runtime_call_performed",
        "ai_tailoring_generation_performed",
        "real_tailoring_output_created",
    ):
        assert first["dry_run_packet"][marker] is False


def test_helper_source_has_no_forbidden_imports_or_calls():
    source = HELPER_PATH.read_text(encoding="utf-8").lower()

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_doc_contains_required_safety_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8")

    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_phase29a_changes_only_helper_doc_test_and_legacy_guards():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    changed = set(tracked + untracked)
    allowed = {
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
                    "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint.md",
                    "tests/test_phase30d_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract",
                "phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards

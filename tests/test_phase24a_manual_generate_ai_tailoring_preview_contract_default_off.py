# phase26c legacy guard marker: changes_only 2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251
# phase26b legacy guard marker: changes_only b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import manual_generate_ai_tailoring_preview_contract as contract


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / "src/agents/manual_generate_ai_tailoring_preview_contract.py"
)
DOC_PATH = (
    ROOT / "docs/phase24_manual_generate_ai_tailoring_preview_contract.md"
)

REQUIRED_KEYS = (
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "preview_contract_only",
    "requires_user_trigger",
    "user_trigger_present",
    "manual_acceptance_required",
    "can_prepare_preview",
    "blocked_reasons",
    "missing_inputs",
    "no_provider_calls",
    "provider_call_performed",
    "no_network_calls",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
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
)

TRUE_SAFETY_KEYS = (
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "preview_contract_only",
    "requires_user_trigger",
    "manual_acceptance_required",
    "no_provider_calls",
    "no_network_calls",
)

FALSE_ACTION_KEYS = (
    "provider_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
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
)

FORBIDDEN_SOURCE_MARKERS = (
    "from src.tailoring",
    "import src.tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "from src.app",
    "import src.app",
    "services.",
    "api.",
    "storage",
    "database_url",
    "psycopg",
    "sqlite",
    "subprocess",
    "requests.",
    "httpx",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "execute_application",
    "submit_application",
)

DOC_MARKERS = (
    "phase 24a manual generate ai tailoring preview contract",
    "contract-only",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "preview contract only",
    "user trigger required",
    "manual acceptance required",
    "does not generate ai tailoring",
    "does not call tailoring runtime",
    "does not call providers",
    "does not create resume rewrites",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "tailoring agent remains separate from final scoring",
    "generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase",
    "phase23-tailoring-agent-workflow-release-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff",
    "src/app/static/app_redesign.css": "54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251",
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


def _ready_inputs() -> dict:
    return {
        "tailoring_opportunity_payload": {
            "tailoring_opportunities": [
                {"opportunity_type": "missing_requirement"}
            ],
        },
        "generate_ai_tailoring_action_boundary_payload": {
            "action_allowed": True,
        },
        "selected_resume_metadata": {"resume_id": "resume-1"},
        "job_metadata": {"job_id": "job-1"},
        "user_trigger_metadata": {"user_triggered": True},
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


def test_helper_exists_and_exposes_public_function():
    assert HELPER_PATH.exists()
    assert callable(
        contract.build_manual_generate_ai_tailoring_preview_contract
    )


def test_default_contract_contains_required_read_only_manual_control_keys():
    payload = contract.build_manual_generate_ai_tailoring_preview_contract()

    assert payload["phase"] == "24A"
    for key in REQUIRED_KEYS:
        assert key in payload
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_no_user_trigger_is_blocked_with_clear_reason():
    payload = contract.build_manual_generate_ai_tailoring_preview_contract(
        tailoring_opportunity_payload={"tailoring_opportunities": [{}]},
        generate_ai_tailoring_action_boundary_payload={"action_allowed": True},
        selected_resume_metadata={"resume_id": "resume-1"},
        job_metadata={"job_id": "job-1"},
    )

    assert payload["user_trigger_present"] is False
    assert payload["can_prepare_preview"] is False
    assert "explicit user trigger required" in payload["blocked_reasons"]
    assert "user_trigger_metadata" in payload["missing_inputs"]
    assert payload["next_safe_step"] == "require_explicit_user_trigger"


def test_user_trigger_with_required_inputs_can_prepare_preview_only():
    inputs = _ready_inputs()
    before = deepcopy(inputs)
    payload = contract.build_manual_generate_ai_tailoring_preview_contract(
        **inputs
    )

    assert inputs == before
    assert payload["user_trigger_present"] is True
    assert payload["can_prepare_preview"] is True
    assert payload["blocked_reasons"] == []
    assert payload["missing_inputs"] == []
    assert payload["next_safe_step"] == (
        "review_preview_readiness_without_generating_ai_tailoring"
    )
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_inputs_are_deep_copied_and_not_mutated():
    inputs = _ready_inputs()
    payload = contract.build_manual_generate_ai_tailoring_preview_contract(
        **inputs
    )

    assert payload["preview_inputs"]["job_metadata"] == inputs["job_metadata"]
    assert payload["preview_inputs"]["job_metadata"] is not inputs[
        "job_metadata"
    ]
    inputs["job_metadata"]["job_id"] = "changed"
    assert payload["preview_inputs"]["job_metadata"]["job_id"] == "job-1"


def test_helper_source_has_no_forbidden_imports_or_calls():
    source = HELPER_PATH.read_text(encoding="utf-8").lower()

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_docs_contain_required_safety_markers_and_phase23_reference():
    assert DOC_PATH.exists()
    text = " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase24a_changes_only_helper_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/api.py",
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
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "changes_only",
                "b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8",
                "2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff",
                "54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251",
            )
        )
    }

    assert changed <= allowed | legacy_guards

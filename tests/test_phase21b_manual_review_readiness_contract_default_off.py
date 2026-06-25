from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import manual_review_readiness_contract as contract


ROOT = Path(__file__).resolve().parents[1]

PROTECTED_HASHES = {
    "src/app/api.py": "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "f7cdf115e412f34094e80e71b18e86f94365715c6f5010faa8e2ba7fe41daeff",
    "src/app/static/app_redesign.css": "962232082cf71e5c85150ff52de5466b11a791567692a45e768dae6d5d11c6ba",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
}


def _review_inputs():
    return {
        "job": {
            "title": "Machine Learning Engineer",
            "company": "Example Corp",
        },
        "ranking_summary": {"rank": 1, "score": 0.92},
        "resume_guidance_available": True,
    }


def test_helper_imports_cleanly_and_versions_are_exact():
    assert contract.MANUAL_REVIEW_READINESS_CONTRACT_VERSION == (
        "phase-21b-manual-review-readiness-contract-v1"
    )
    assert contract.MANUAL_REVIEW_READINESS_SCHEMA_VERSION == (
        "phase-21b-manual-review-readiness-payload-v1"
    )


def test_default_off_returns_not_enabled():
    payload = contract.build_manual_review_readiness_payload()

    assert payload["readiness_status"] == contract.STATUS_NOT_ENABLED
    assert payload["enabled"] is False


def test_enabled_missing_inputs_returns_missing_inputs():
    payload = contract.build_manual_review_readiness_payload(enabled=True)

    assert payload["readiness_status"] == contract.STATUS_MISSING_INPUTS
    assert payload["missing_review_inputs"] == ["review_inputs_summary"]


def test_enabled_caller_inputs_returns_ready_without_mutating_input():
    review_inputs = _review_inputs()
    before = deepcopy(review_inputs)

    first = contract.build_manual_review_readiness_payload(
        enabled=True,
        review_inputs_summary=review_inputs,
    )
    second = contract.build_manual_review_readiness_helper_payload(
        enabled=True,
        review_inputs_summary=review_inputs,
    )

    assert first == second
    assert first["readiness_status"] == contract.STATUS_READY
    assert first["review_inputs_summary"] == review_inputs
    assert first["review_inputs_summary"] is not review_inputs
    assert first["missing_review_inputs"] == []
    assert review_inputs == before


def test_payload_requires_manual_review_and_user_control():
    payload = contract.build_manual_review_readiness_payload(
        enabled=True,
        review_inputs_summary=_review_inputs(),
    )

    assert payload["manual_review_required"] is True
    assert payload["manual_user_control_required"] is True
    assert payload["no_auto_apply"] is True
    assert payload["no_auto_submit"] is True
    assert payload["no_autonomous_application_execution"] is True
    assert payload["no_automatic_job_application_submission"] is True


def test_allowed_assistance_modes_and_forbidden_actions_are_exact():
    payload = contract.build_manual_review_readiness_payload()

    assert payload["allowed_assistance_modes"] == [
        "discovery",
        "filtering",
        "ranking",
        "read-only previews",
        "readiness checks",
        "resume/content guidance",
        "manual review support",
    ]
    assert payload["forbidden_actions"] == [
        "auto-apply",
        "auto-submit",
        "autonomous application execution",
        "automatic job application submission",
        "bypass of manual review",
    ]
    assert payload["checklist_items"] == [
        "review_job_details",
        "review_role_fit_and_ranking_evidence",
        "review_resume_and_content_guidance",
        "review_application_materials",
        "confirm_manual_user_control",
        "complete_submission_outside_autonomous_execution",
    ]


def test_safety_metadata_keeps_all_forbidden_paths_inactive():
    safety = contract.manual_review_readiness_safety_metadata()

    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["manual_review_required"] is True
    assert safety["manual_user_control_required"] is True
    for key in (
        "provider_call_attempted",
        "network_call_attempted",
        "database_write_attempted",
        "approval_created",
        "decision_persisted",
        "audit_persisted",
        "scoring_mutated",
        "ranking_mutated",
        "queue_mutated",
        "resume_mutated",
        "application_mutated",
        "execution_authorized",
        "submission_authorized",
        "mutation_authorized",
    ):
        assert safety[key] is False


def test_helper_source_has_no_runtime_wiring_io_or_forbidden_calls():
    source = (
        ROOT / "src/agents/manual_review_readiness_contract.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "src.app",
        "src.pipeline",
        "src.storage",
        "services",
        "openai",
        "anthropic",
        "boto3",
        "langchain",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "os.getenv",
        "os.environ",
        "pathlib",
        "open(",
        "read_text(",
        "write_text(",
        "connect(",
        ".commit(",
        "provider_callable(",
        "provider_client",
        "score_jobs(",
        "rank_jobs(",
        "mutate_queue(",
        "mutate_resume(",
        "create_approval(",
        "persist_decision(",
        "persist_audit(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase21b_changes_only_helper_doc_test_and_legacy_guards():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    changed = set(tracked + untracked) - {
        "docs/core_agent_automation_mutation_inventory.md",
        "docs/phase22_core_agent_automation_mutation_inventory.md",
        "src/agents/core_agent_evidence_materialization_preview.py",
        "docs/phase22_core_agent_evidence_materialization_preview.md",
        "tests/test_phase22c_core_agent_evidence_materialization_preview_default_off.py",
        "src/app/api.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase22_core_agent_evidence_materialization_ui_readback.md",
        "tests/test_phase22e_core_agent_evidence_materialization_ui_readback_default_off.py",
        "docs/phase22_core_agent_evidence_materialization_release_checkpoint.md",
        "tests/test_phase22f_core_agent_evidence_materialization_release_checkpoint_default_off.py",
        "src/agents/tailoring_agent_opportunity_contract.py",
        "docs/phase23_tailoring_agent_opportunity_contract.md",
        "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
        "src/agents/manual_review_readiness_contract.py",
        "docs/phase21_manual_review_readiness_contract.md",
        "tests/test_phase21b_manual_review_readiness_contract_default_off.py",
        "src/app/api.py",
        "docs/phase21_manual_review_readiness_api_readback.md",
        "tests/test_phase21c_manual_review_readiness_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "docs/phase21_manual_review_readiness_ui_readback.md",
        "tests/test_phase21d_manual_review_readiness_ui_readback_default_off.py",
        "docs/phase21_manual_review_workflow_release_checkpoint.md",
        "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase22_manual_review_ux_hardening.md",
        "tests/test_phase22a_manual_review_ux_hardening_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
                "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a",
                "f7cdf115e412f34094e80e71b18e86f94365715c6f5010faa8e2ba7fe41daeff",
            )
        )
    }

    assert changed <= allowed | legacy_guards

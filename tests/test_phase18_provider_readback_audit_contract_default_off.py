from hashlib import sha256
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_provider_readback_audit_contract.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

READBACK_STATUSES = [
    "not_available",
    "readback_not_started",
    "readback_ready",
    "readback_complete",
    "readback_blocked",
    "readback_failed_closed",
]

AUDIT_STATUSES = [
    "audit_not_available",
    "audit_not_started",
    "audit_ready",
    "audit_recorded",
    "audit_blocked",
    "audit_failed_closed",
]

READBACK_FIELDS = [
    "readback_id",
    "readback_status",
    "provider_name",
    "provider_operation",
    "requested_capability",
    "linked_preview_id",
    "linked_decision_id",
    "linked_activation_id",
    "linked_adapter_id",
    "linked_dry_run_packet_id",
    "linked_response_validation_id",
    "linked_trace_or_readback_id",
    "advisory_output_summary",
    "validation_status_summary",
    "redaction_summary",
    "safety_flag_summary",
    "missing_requirements",
    "fail_closed_reason",
    "created_timestamp",
    "completed_timestamp",
]

AUDIT_FIELDS = [
    "audit_id",
    "audit_status",
    "audit_scope",
    "provider_name",
    "provider_operation",
    "requested_capability",
    "linked_readback_id",
    "linked_preview_id",
    "linked_decision_id",
    "linked_activation_id",
    "linked_adapter_id",
    "linked_dry_run_packet_id",
    "linked_response_validation_id",
    "linked_trace_or_readback_id",
    "operator_or_reviewer_id",
    "decision_reason",
    "safety_flag_summary",
    "redaction_summary",
    "fail_closed_reason",
    "retention_policy_summary",
    "rollback_or_disable_reference",
    "created_timestamp",
]

RUNTIME_HASHES = {
    "src/agents/relevance_prefilter.py": (
        "5be6d21c27b720472daef6f85f813bc6561c90f9f8abfcfc09e88a5cd36a490b"
    ),
    "src/agents/jd_intelligence.py": (
        "1f79df7e4349ce9ae7b1e5bad185a7958d86aa654d7c8bbd77634f59f529f81e"
    ),
    "src/agents/final_application_scoring.py": (
        "eed7eed337b860345f38005c1f898732c8c809f6087e7fbbf33de6f4ad7ed2fd"
    ),
    "src/agents/three_core_agent_shadow_operator_canary.py": (
        "b130620a2257603bd2ed5259f65434e4f13d9636d1d25a417c594f38251bb943"
    ),
    "src/pipeline/collector.py": (
        "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
    ),
    "src/app/api.py": (
        "23e335987f08ddc484c8b0617608b6a742e58b780f7a932c14401e1ce5045766"
    ),
    "src/app/services.py": (
        "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee"
    ),
    "src/app/static/agentic_review.js": (
        "3520143a71e59a3e4f225db746657c248f10d5317480b602de3881d8811abb97"
    ),
}


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def _numbered_values(section_start: str, section_end: str) -> list[str]:
    text = _text()
    section = text[text.index(section_start):text.index(section_end)]
    return re.findall(r"^\d+\. `([^`]+)`$", section, flags=re.MULTILINE)


def test_readback_audit_contract_exists_and_names_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Provider Readback and Audit Contract" in text
    for tag in (
        "phase17-three-core-shadow-readiness-release-v1",
        "phase18a-live-readiness-approval-boundary-v1",
        "phase18b-human-approval-gate-contract-v1",
        "phase18c-approval-preview-readonly-v1",
        "phase18d-operator-decision-capture-contract-v1",
        "phase18e-live-provider-activation-plan-v1",
        "phase18f-provider-runtime-adapter-contract-v1",
        "phase18g-live-provider-dry-run-packet-contract-v1",
        "phase18h-provider-response-validation-contract-v1",
    ):
        assert f"`{tag}`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18i_is_docs_tests_only_and_implements_no_runtime_surface():
    text = _text()

    assert "Phase 18I is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert "does\nnot implement provider readback" in text
    assert "does not implement audit\npersistence" in text
    assert "does not implement response validation" in text
    assert "does\nnot call or activate a provider" in text
    assert "adds no API" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_allowed_future_readback_statuses_are_exact_and_ordered():
    assert _numbered_values(
        "## Allowed future readback statuses",
        "## Allowed future audit statuses",
    ) == READBACK_STATUSES


def test_allowed_future_audit_statuses_are_exact_and_ordered():
    assert _numbered_values(
        "## Allowed future audit statuses",
        "## Required future readback fields",
    ) == AUDIT_STATUSES


def test_required_future_readback_fields_are_listed():
    text = _text()

    for field in READBACK_FIELDS:
        assert f"`{field}`" in text


def test_required_future_audit_fields_are_listed():
    text = _text()

    for field in AUDIT_FIELDS:
        assert f"`{field}`" in text


def test_future_readback_categories_are_complete():
    text = _text()
    section = text[
        text.index("## Future readback categories"):
        text.index("## Future audit categories")
    ]

    for category in (
        "Advisory provider output summary",
        "Response validation summary",
        "Redaction and safety summary",
        "Linked decision summary",
        "Linked packet summary",
        "Linked activation summary",
        "Fail-closed summary",
        "Passive trace summary",
    ):
        assert category in section


def test_future_audit_categories_are_complete_and_unimplemented():
    text = _text()
    section = text[
        text.index("## Future audit categories"):
        text.index("## Required future default-off gates")
    ]

    for category in (
        "Approval/decision audit metadata",
        "Provider-call evidence audit metadata",
        "Response-validation audit metadata",
        "Redaction audit metadata",
        "Safety-flag audit metadata",
        "Rollback/disable audit metadata",
        "Retention-policy audit metadata",
    ):
        assert category in section
    assert "Phase 18I does not implement any readback or audit operation." in section


def test_required_future_default_off_gates_are_listed():
    text = _text()

    for gate in (
        "Global provider runtime flag",
        "Provider-specific flag",
        "Readback flag",
        "Audit flag",
        "Response-validation flag",
        "Human decision required flag",
        "Mutation-disabled flag",
        "Persistence-disabled flag",
    ):
        assert gate in text


def test_readback_and_audit_safety_requirements_are_complete():
    text = _text()

    for requirement in (
        "Readback construction must be deterministic.",
        "Readback construction must not call providers.",
        "Readback construction must not read secret values.",
        "Readback construction must not create network traffic.",
        "Readback construction must not mutate final score, rank, queue, resume, or",
        "Audit construction must not persist unless a separate persistence phase is",
        "Audit construction must not expose secret values.",
        "Audit construction must not become approval, execution, or submission",
        "Readback and audit output must remain advisory and review-only.",
        "Failures must fail closed.",
    ):
        assert requirement in text


def test_failed_closed_readback_conditions_are_complete():
    text = _text()
    section = text[
        text.index("## Failed-closed readback conditions"):
        text.index("## Failed-closed audit conditions")
    ]

    for condition in (
        "Missing provider name",
        "Missing provider operation",
        "Missing requested capability",
        "Missing linked preview id",
        "Missing linked decision id",
        "Missing linked activation id",
        "Missing linked adapter id",
        "Missing linked dry-run packet id",
        "Missing linked response validation id",
        "Missing advisory output summary",
        "Missing validation status summary",
        "Missing redaction summary",
        "Unsafe safety flags",
        "Secret value detected",
        "Attempted provider call",
        "Attempted mutation or submission",
    ):
        assert condition in section


def test_failed_closed_audit_conditions_are_complete():
    text = _text()
    section = text[
        text.index("## Failed-closed audit conditions"):
        text.index("## Minimum future observability")
    ]

    for condition in (
        "Missing audit scope",
        "Missing linked readback id",
        "Missing linked decision id",
        "Missing linked response validation id",
        "Missing operator/reviewer id",
        "Missing retention policy summary",
        "Missing rollback/disable reference",
        "Unsafe safety flags",
        "Secret value detected",
        "Attempted persistence without approval",
        "Attempted provider call",
        "Attempted mutation or submission",
    ):
        assert condition in section


def test_minimum_future_observability_is_complete():
    text = _text()

    for field in (
        "Readback status",
        "Audit status",
        "Provider name",
        "Provider operation",
        "Requested capability",
        "Linked readback id",
        "Linked preview id",
        "Linked decision id",
        "Linked activation id",
        "Linked adapter id",
        "Linked dry-run packet id",
        "Linked response validation id",
        "Linked trace/readback id",
        "Advisory output summary",
        "Validation status summary",
        "Redaction summary",
        "Safety flag summary",
        "Fail-closed reason",
    ):
        assert field in text


def test_not_authorized_section_lists_every_forbidden_path():
    text = _text()

    for term in (
        "No provider readback implementation.",
        "No audit persistence implementation.",
        "No response validator implementation.",
        "No dry-run packet builder implementation.",
        "No adapter implementation.",
        "No live provider execution.",
        "No provider SDK/network call.",
        "No secrets access.",
        "No approval creation runtime.",
        "No decision persistence runtime.",
        "No audit persistence runtime.",
        "No DB writes.",
        "No final scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No resume mutation.",
        "No execution request creation.",
        "No application execution.",
        "No application submission.",
    ):
        assert term in text


def test_recommended_next_phase_is_call_boundary_without_call_or_mutation():
    assert (
        "Phase 18J should be a docs/tests-only provider-call boundary readiness\n"
        "contract, still no provider call and still no mutation."
        in _text()
    )


def test_phase18i_changes_only_approved_docs_and_tests():
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
        "docs/phase18_provider_readback_audit_contract.md",
        "tests/test_phase18_provider_readback_audit_contract_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
        "tests/test_phase18_operator_decision_capture_contract_default_off.py",
        "tests/test_phase18_live_provider_activation_plan_default_off.py",
        "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
        "tests/test_phase18_live_provider_dry_run_packet_contract_default_off.py",
        "tests/test_phase18_provider_response_validation_contract_default_off.py",
        "docs/phase18_provider_call_boundary_readiness_contract.md",
        "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
        "docs/phase18_mutation_boundary_readiness_contract.md",
        "tests/test_phase18_mutation_boundary_readiness_contract_default_off.py",
        "docs/phase18_safety_wrap_release_checkpoint.md",
        "tests/test_phase18_safety_wrap_release_checkpoint_default_off.py",
        "src/agents/three_core_approval_preview_runtime.py",
        "docs/phase19_approval_preview_runtime_readonly.md",
        "tests/test_phase19a_three_core_approval_preview_runtime_readonly_default_off.py",
    }

    assert changed <= allowed


def test_phase18i_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash

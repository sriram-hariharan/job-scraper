from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_live_readiness_approval_boundary.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
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


def test_phase18_boundary_doc_exists_and_names_release():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Live-Readiness Approval Boundary" in text
    assert "`phase17-three-core-shadow-readiness-release-v1`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18a_is_docs_tests_only_and_authorizes_no_runtime():
    text = _text()

    assert "Phase 18A is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_all_safety_matrix_capabilities_are_not_authorized():
    text = _text()
    capabilities = [
        "Live provider execution",
        "Provider SDK/network calls",
        "Final scoring mutation",
        "Ranking mutation",
        "Queue mutation",
        "Resume mutation",
        "Approval creation",
        "Execution request creation",
        "Application execution",
        "Application submission",
        "DB writes",
        "Secrets access",
    ]

    for capability in capabilities:
        assert f"| {capability} | Not authorized |" in text


def test_future_live_behavior_requires_all_approval_gates():
    text = _text().lower()

    for term in (
        "named feature flag",
        "operator/human approval",
        "dry-run/readback evidence",
        "fail-closed behavior",
        "audit log or trace summary",
        "rollback/disable plan",
        "tests proving no submit/apply path is reachable",
    ):
        assert term in text


def test_provider_plan_is_isolated_advisory_traceable_and_fail_closed():
    text = _text()

    for term in (
        "Provider execution must be isolated from scoring/ranking mutation.",
        "Provider outputs must remain advisory until separately approved.",
        "Provider failures must fail closed.",
        "Provider calls must be traceable.",
        "Secrets must not be logged.",
        "Network/provider SDK calls must be behind explicit default-off flags.",
    ):
        assert term in text


def test_future_mutations_each_require_separate_approval():
    text = _text()

    for capability in (
        "scoring mutation",
        "ranking mutation",
        "queue mutation",
        "resume mutation",
        "execution request creation",
        "application execution",
        "application submission",
    ):
        assert f"Separate approval is required for {capability}." in text


def test_not_authorized_section_lists_every_forbidden_path():
    text = _text()

    for term in (
        "No live provider execution.",
        "No provider SDK/network call.",
        "No DB writes.",
        "No secrets access.",
        "No final scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No resume mutation.",
        "No approval creation.",
        "No execution request creation.",
        "No application execution.",
        "No application submission.",
    ):
        assert term in text


def test_recommended_phase18_sequence_is_ordered():
    text = _text()
    steps = [
        "18A:** approval boundary docs/tests.",
        "18B:** human approval gate contract, default-off.",
        "18C:** read-only approval preview.",
        "18D:** operator decision capture, no execution.",
        "18E:** protected live-provider activation plan, still no mutation.",
        "Later phase only after approval:** controlled live provider or mutation",
    ]
    positions = [text.index(step) for step in steps]

    assert positions == sorted(positions)


def test_no_future_phase_may_combine_provider_and_mutation_authority():
    text = _text()

    assert (
        "No future phase may combine provider execution, scoring mutation, "
        "ranking\nmutation, queue mutation, resume mutation, and application "
        "submission in one\nstep."
        in text
    )


def test_phase18a_changes_only_approved_docs_and_tests():
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
        "docs/phase18_live_readiness_approval_boundary.md",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "docs/phase18_human_approval_gate_contract.md",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "docs/phase18_approval_preview_readonly.md",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
        "docs/phase18_operator_decision_capture_contract.md",
        "tests/test_phase18_operator_decision_capture_contract_default_off.py",
        "docs/phase18_live_provider_activation_plan.md",
        "tests/test_phase18_live_provider_activation_plan_default_off.py",
        "docs/phase18_provider_runtime_adapter_contract.md",
        "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
        "docs/phase18_live_provider_dry_run_packet_contract.md",
        "tests/test_phase18_live_provider_dry_run_packet_contract_default_off.py",
        "docs/phase18_provider_response_validation_contract.md",
        "tests/test_phase18_provider_response_validation_contract_default_off.py",
        "docs/phase18_provider_readback_audit_contract.md",
        "tests/test_phase18_provider_readback_audit_contract_default_off.py",
        "docs/phase18_provider_call_boundary_readiness_contract.md",
        "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
        "docs/phase18_mutation_boundary_readiness_contract.md",
        "tests/test_phase18_mutation_boundary_readiness_contract_default_off.py",
        "docs/phase18_safety_wrap_release_checkpoint.md",
        "tests/test_phase18_safety_wrap_release_checkpoint_default_off.py",
    }

    assert changed <= allowed


def test_phase18a_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash


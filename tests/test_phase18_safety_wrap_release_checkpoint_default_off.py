from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_safety_wrap_release_checkpoint.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

PHASE_TAGS = [
    "phase17-three-core-shadow-readiness-release-v1",
    "phase18a-live-readiness-approval-boundary-v1",
    "phase18b-human-approval-gate-contract-v1",
    "phase18c-approval-preview-readonly-v1",
    "phase18d-operator-decision-capture-contract-v1",
    "phase18e-live-provider-activation-plan-v1",
    "phase18f-provider-runtime-adapter-contract-v1",
    "phase18g-live-provider-dry-run-packet-contract-v1",
    "phase18h-provider-response-validation-contract-v1",
    "phase18i-provider-readback-audit-contract-v1",
    "phase18j-provider-call-boundary-readiness-contract-v1",
    "phase18k-mutation-boundary-readiness-contract-v1",
]

PHASE_COVERAGE = [
    "Phase 18A | Live-readiness approval boundary",
    "Phase 18B | Human approval gate contract",
    "Phase 18C | Read-only approval preview contract",
    "Phase 18D | Operator decision capture contract",
    "Phase 18E | Protected live-provider activation plan",
    "Phase 18F | Provider runtime adapter contract",
    "Phase 18G | Live-provider dry-run packet contract",
    "Phase 18H | Provider response validation contract",
    "Phase 18I | Provider readback and audit contract",
    "Phase 18J | Provider-call boundary readiness contract",
    "Phase 18K | Mutation boundary readiness contract",
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


def test_safety_wrap_doc_exists_and_names_all_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Safety Wrap and Release Checkpoint" in text
    for tag in PHASE_TAGS:
        assert f"`{tag}`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18l_is_final_docs_tests_only_wrap_with_no_runtime_authority():
    text = _text()

    assert "Phase 18L is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert (
        "Phase 18L is\nthe final Phase 18 safety wrap before Phase 19 read-only "
        "runtime\nimplementation."
        in text
    )
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_phase18a_through_18k_safety_coverage_is_complete():
    text = _text()

    for coverage in PHASE_COVERAGE:
        assert f"| {coverage} |" in text


def test_phase18_final_safety_conclusion_is_explicit():
    text = _text()

    for statement in (
        "Phase 18 completes the approval/provider/mutation safety contract layer.",
        "Phase 18 does not authorize provider execution.",
        "Phase 18 does not authorize mutation.",
        "Phase 18 does not authorize application execution or submission.",
        "Phase 18 prepares the repo for Phase 19 read-only runtime implementation.",
    ):
        assert statement in text


def test_phase19a_permitted_first_implementation_scope_is_complete():
    text = _text()
    section = text[
        text.index("## Phase 19A permitted first implementation scope"):
        text.index("## Phase 19A explicitly blocked scope")
    ]

    for item in (
        "Read-only approval preview runtime",
        "Default-off",
        "Reads existing shadow/core-3 evidence only",
        "May assemble reviewable preview metadata",
        "Must not call providers",
        "Must not read secrets",
        "Must not write DB",
        "Must not mutate scoring, ranking, queue, resume, application state,",
        "Must preserve stage-level observability",
        "Must include tests proving no submit/apply path is reachable",
    ):
        assert item in section


def test_phase19a_explicitly_blocked_scope_is_complete():
    text = _text()
    section = text[
        text.index("## Phase 19A explicitly blocked scope"):
        text.index("## Not authorized by Phase 18L")
    ]

    for item in (
        "No provider SDK/network call.",
        "No provider runtime activation.",
        "No score mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No resume mutation.",
        "No execution request creation.",
        "No application execution.",
        "No application submission.",
    ):
        assert item in section


def test_not_authorized_section_lists_every_forbidden_path():
    text = _text()

    for item in (
        "No runtime implementation.",
        "No provider call.",
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
        assert item in text


def test_release_recommendation_names_expected_tag_and_branch_flow():
    text = _text()

    assert "Release Phase 18 from `develop` to `main` after full tests pass." in text
    assert "Tag the release as `phase18-safety-wrap-release-v1`." in text
    assert "Start Phase 19A from `develop` after the release." in text


def test_phase18l_changes_only_approved_docs_and_tests():
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
        "docs/phase18_safety_wrap_release_checkpoint.md",
        "tests/test_phase18_safety_wrap_release_checkpoint_default_off.py",
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
        "tests/test_phase18_provider_readback_audit_contract_default_off.py",
        "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
        "tests/test_phase18_mutation_boundary_readiness_contract_default_off.py",
    }

    assert changed <= allowed


def test_phase18l_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash

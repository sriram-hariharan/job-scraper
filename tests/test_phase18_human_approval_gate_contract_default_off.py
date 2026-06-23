from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_human_approval_gate_contract.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

DECISION_STATES = [
    "not_requested",
    "requested",
    "approved",
    "rejected",
    "expired",
    "revoked",
    "failed_closed",
]

REQUEST_FIELDS = [
    "request_id",
    "requested_capability",
    "requester_source",
    "target_context",
    "evidence_summary",
    "proposed_action_summary",
    "risk_summary",
    "safety_flags",
    "expiry_timestamp",
    "created_timestamp",
    "operator_or_reviewer_id",
    "decision_timestamp",
    "decision_reason",
    "rollback_or_disable_reference",
]

SEPARATE_CAPABILITIES = [
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


def test_contract_doc_exists_and_names_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Human Approval Gate Contract" in text
    assert "`phase17-three-core-shadow-readiness-release-v1`" in text
    assert "`phase18a-live-readiness-approval-boundary-v1`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18b_is_docs_tests_only_and_authorizes_no_runtime():
    text = _text()

    assert "Phase 18B is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert "adds no API" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_allowed_future_decision_states_are_exact_and_ordered():
    text = _text()
    section = text[
        text.index("## Allowed future decision states"):
        text.index("## Required future approval request fields")
    ]
    positions = [section.index(f"`{state}`") for state in DECISION_STATES]

    assert positions == sorted(positions)
    for state in DECISION_STATES:
        assert section.count(f"`{state}`") >= 1


def test_required_future_approval_request_fields_are_listed():
    text = _text()

    for field in REQUEST_FIELDS:
        assert f"`{field}`" in text


def test_separate_approval_capabilities_are_all_listed():
    text = _text()
    section = text[
        text.index("## Capabilities requiring separate approval"):
        text.index("## Hard rules")
    ]

    for capability in SEPARATE_CAPABILITIES:
        assert capability in section


def test_approval_scope_characteristics_and_non_implication_are_explicit():
    text = _text()

    assert "Approval for one capability does not imply approval for another." in text
    assert (
        "single-capability scoped, time-bound, auditable, reversible, and\n"
        "fail-closed"
        in text
    )


def test_hard_rules_are_complete():
    text = _text()

    for term in (
        "No approval may directly submit an application.",
        "No approval may combine provider execution with",
        "scoring/ranking/queue/resume/application submission.",
        "No approval may bypass default-off feature flags.",
        "No approval may bypass dry-run/readback evidence.",
        "No approval may bypass tests proving no submit/apply path is reachable",
        "submission itself is the separately approved capability in a later phase.",
    ):
        assert term in text


def test_fail_closed_conditions_are_complete():
    text = _text()

    for condition in (
        "Missing approval",
        "Expired approval",
        "Revoked approval",
        "Rejected approval",
        "Mismatched capability",
        "Missing evidence",
        "Missing feature flag",
        "Unsafe safety flags",
        "Unknown target context",
        "Provider/runtime error",
    ):
        assert condition in text


def test_minimum_future_observability_is_complete():
    text = _text()

    for field in (
        "Decision state",
        "Requested capability",
        "Operator/reviewer id",
        "Decision timestamp",
        "Evidence summary",
        "Safety flag summary",
        "Fail-closed reason",
        "Linked trace/readback id",
    ):
        assert field in text


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
        "No approval creation runtime.",
        "No execution request creation.",
        "No application execution.",
        "No application submission.",
    ):
        assert term in text


def test_recommended_next_phase_is_read_only_preview_without_execution():
    assert (
        "Phase 18C should be a read-only approval preview, still no execution."
        in _text()
    )


def test_phase18b_changes_only_approved_docs_and_tests():
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
        "docs/phase18_human_approval_gate_contract.md",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "docs/phase18_approval_preview_readonly.md",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
    }

    assert changed <= allowed


def test_phase18b_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash

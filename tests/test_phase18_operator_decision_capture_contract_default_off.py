from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_operator_decision_capture_contract.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

DECISION_STATUSES = [
    "not_requested",
    "decision_pending",
    "decision_captured",
    "decision_rejected",
    "decision_expired",
    "decision_revoked",
    "decision_blocked",
    "failed_closed",
]

DECISION_FIELDS = [
    "decision_id",
    "preview_id",
    "requested_capability",
    "target_context_summary",
    "operator_or_reviewer_id",
    "decision_status",
    "decision_value",
    "decision_reason",
    "evidence_summary",
    "risk_summary",
    "safety_flag_summary",
    "linked_trace_or_readback_id",
    "expiry_timestamp",
    "created_timestamp",
    "decision_timestamp",
    "rollback_or_disable_reference",
    "fail_closed_reason",
]

DECISION_VALUES = [
    "approve",
    "reject",
    "revoke",
    "expire",
    "request_changes",
    "no_decision",
    "failed_closed",
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


def test_decision_capture_doc_exists_and_names_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Operator Decision Capture Contract" in text
    for tag in (
        "phase17-three-core-shadow-readiness-release-v1",
        "phase18a-live-readiness-approval-boundary-v1",
        "phase18b-human-approval-gate-contract-v1",
        "phase18c-approval-preview-readonly-v1",
    ):
        assert f"`{tag}`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18d_is_docs_tests_only_and_authorizes_no_runtime():
    text = _text()

    assert "Phase 18D is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert "adds no API" in text
    assert "decision persistence" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_allowed_decision_capture_statuses_are_exact_and_ordered():
    text = _text()
    section = text[
        text.index("## Allowed future decision capture statuses"):
        text.index("## Required future decision capture fields")
    ]
    positions = [section.index(f"`{status}`") for status in DECISION_STATUSES]

    assert positions == sorted(positions)
    for status in DECISION_STATUSES:
        assert f"`{status}`" in section


def test_required_future_decision_capture_fields_are_listed():
    text = _text()

    for field in DECISION_FIELDS:
        assert f"`{field}`" in text


def test_allowed_decision_values_are_exact_and_ordered():
    text = _text()
    section = text[
        text.index("## Allowed decision values"):
        text.index("## Capabilities requiring separate decision capture")
    ]
    positions = [section.index(f"`{value}`") for value in DECISION_VALUES]

    assert positions == sorted(positions)
    for value in DECISION_VALUES:
        assert f"`{value}`" in section


def test_separate_decision_capture_capabilities_are_listed():
    text = _text()
    section = text[
        text.index("## Capabilities requiring separate decision capture"):
        text.index("## Hard rules")
    ]

    for capability in SEPARATE_CAPABILITIES:
        assert capability in section


def test_decision_scope_characteristics_and_non_implication_are_explicit():
    text = _text()

    assert (
        "A decision for one capability does not authorize another capability."
        in text
    )
    assert (
        "single-capability scoped, time-bound, auditable, reversible,\n"
        "fail-closed, and tied to a read-only preview"
        in text
    )


def test_decision_capture_is_not_an_executor_provider_call_or_submission():
    text = _text()

    for statement in (
        "A captured decision is not an executor.",
        "A captured decision is not a provider call.",
        "A captured decision is not a submission command.",
    ):
        assert statement in text


def test_decision_capture_hard_rules_are_complete():
    text = _text()

    for term in (
        "No decision capture may directly submit an application.",
        "No decision capture may call a provider.",
        "No decision capture may create an execution request.",
        "No decision capture may mutate scoring, ranking, queue, resume, or",
        "No decision capture may write secrets or log secrets.",
        "No decision capture may bypass default-off feature flags.",
        "No decision capture may bypass dry-run/readback evidence.",
        "No decision capture may combine provider execution with",
        "scoring/ranking/queue/resume/application submission.",
        "No decision capture may transform a preview into execution without a",
        "separate later approved executor phase.",
    ):
        assert term in text


def test_failed_closed_decision_conditions_are_complete():
    text = _text()

    for condition in (
        "Missing preview id",
        "Missing operator/reviewer id",
        "Missing requested capability",
        "Unknown requested capability",
        "Mismatched capability",
        "Missing evidence summary",
        "Missing safety flag summary",
        "Unsafe safety flags",
        "Expired decision window",
        "Revoked decision",
        "Rejected decision",
        "Missing rollback/disable reference",
        "Attempted execution or mutation",
    ):
        assert condition in text


def test_minimum_future_decision_observability_is_complete():
    text = _text()

    for field in (
        "Decision status",
        "Decision value",
        "Requested capability",
        "Operator/reviewer id",
        "Decision reason",
        "Target context summary",
        "Evidence summary",
        "Risk summary",
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
        "No approval creation runtime.",
        "No decision persistence runtime.",
        "No DB writes.",
        "No secrets access.",
        "No final scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No resume mutation.",
        "No execution request creation.",
        "No application execution.",
        "No application submission.",
    ):
        assert term in text


def test_recommended_next_phase_is_provider_plan_without_mutation():
    assert (
        "Phase 18E should be a protected live-provider activation plan, still no\n"
        "mutation."
        in _text()
    )


def test_phase18d_changes_only_approved_docs_and_tests():
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
        "docs/phase18_operator_decision_capture_contract.md",
        "tests/test_phase18_operator_decision_capture_contract_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
        "docs/phase18_live_provider_activation_plan.md",
        "tests/test_phase18_live_provider_activation_plan_default_off.py",
    }

    assert changed <= allowed


def test_phase18d_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash


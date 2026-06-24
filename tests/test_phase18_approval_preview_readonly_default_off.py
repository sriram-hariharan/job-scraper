from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_approval_preview_readonly.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

PREVIEW_STATUSES = [
    "not_available",
    "preview_ready",
    "preview_incomplete",
    "preview_blocked",
    "failed_closed",
]

PREVIEW_FIELDS = [
    "preview_id",
    "preview_status",
    "requested_capability",
    "target_context_summary",
    "requester_source",
    "evidence_summary",
    "proposed_action_summary",
    "risk_summary",
    "safety_flag_summary",
    "required_feature_flags",
    "missing_requirements",
    "fail_closed_reasons",
    "expiry_recommendation",
    "rollback_or_disable_reference",
    "linked_trace_or_readback_id",
    "created_timestamp",
]

PREVIEW_CAPABILITIES = [
    "Live provider execution preview",
    "Provider SDK/network call preview",
    "Final scoring mutation preview",
    "Ranking mutation preview",
    "Queue mutation preview",
    "Resume mutation preview",
    "Approval creation preview",
    "Execution request creation preview",
    "Application execution preview",
    "Application submission preview",
    "DB write preview",
    "Secrets access preview",
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


def test_preview_doc_exists_and_names_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Read-Only Approval Preview" in text
    for tag in (
        "phase17-three-core-shadow-readiness-release-v1",
        "phase18a-live-readiness-approval-boundary-v1",
        "phase18b-human-approval-gate-contract-v1",
    ):
        assert f"`{tag}`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18c_is_docs_tests_only_and_authorizes_no_runtime():
    text = _text()

    assert "Phase 18C is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert "adds no API" in text
    assert "approval creation" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_allowed_preview_statuses_are_exact_and_ordered():
    text = _text()
    section = text[
        text.index("## Allowed preview statuses"):
        text.index("## Required future preview fields")
    ]
    positions = [section.index(f"`{status}`") for status in PREVIEW_STATUSES]

    assert positions == sorted(positions)
    for status in PREVIEW_STATUSES:
        assert f"`{status}`" in section


def test_required_future_preview_fields_are_listed():
    text = _text()

    for field in PREVIEW_FIELDS:
        assert f"`{field}`" in text


def test_preview_only_capability_categories_are_listed():
    text = _text()
    section = text[
        text.index("## Preview-only capability categories"):
        text.index("## Hard rules")
    ]

    for capability in PREVIEW_CAPABILITIES:
        assert capability in section


def test_preview_non_authority_statements_are_explicit():
    text = _text()

    for statement in (
        "Previewing a capability does not authorize the capability.",
        "Previewing a capability does not create approval records.",
        "Previewing a capability does not imply human approval.",
        (
            "Previewing one capability does not imply approval or preview "
            "readiness for another."
        ),
    ):
        assert statement in text


def test_preview_hard_rules_are_complete():
    text = _text()

    for term in (
        "No preview may directly submit an application.",
        "No preview may create an approval record.",
        "No preview may create an execution request.",
        "No preview may call a provider.",
        "No preview may read secrets.",
        "No preview may write to the database.",
        "No preview may mutate final scoring, ranking, queue, resume, or application",
        "No preview may combine provider execution with",
        "scoring/ranking/queue/resume/application submission.",
        "No preview may bypass default-off feature flags.",
        "No preview may bypass dry-run/readback evidence.",
    ):
        assert term in text


def test_failed_closed_preview_conditions_are_complete():
    text = _text()

    for condition in (
        "Missing target context",
        "Missing requested capability",
        "Unknown requested capability",
        "Missing evidence summary",
        "Missing feature flag",
        "Unsafe safety flags",
        "Expired preview window",
        "Mismatched trace/readback id",
        "Missing rollback/disable reference",
        "Attempted execution or mutation",
    ):
        assert condition in text


def test_minimum_future_preview_observability_is_complete():
    text = _text()

    for field in (
        "Preview status",
        "Requested capability",
        "Target context summary",
        "Evidence summary",
        "Proposed action summary",
        "Risk summary",
        "Safety flag summary",
        "Missing requirements",
        "Fail-closed reasons",
        "Linked trace/readback id",
    ):
        assert field in text


def test_not_authorized_section_lists_every_forbidden_path():
    text = _text()

    for term in (
        "No live provider execution.",
        "No provider SDK/network call.",
        "No approval creation runtime.",
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


def test_recommended_next_phase_is_decision_capture_without_execution():
    assert (
        "Phase 18D should be operator decision capture contract, still no execution."
        in _text()
    )


def test_phase18c_changes_only_approved_docs_and_tests():
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
        "docs/phase18_approval_preview_readonly.md",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "docs/phase18_operator_decision_capture_contract.md",
        "tests/test_phase18_operator_decision_capture_contract_default_off.py",
        "docs/phase18_live_provider_activation_plan.md",
        "tests/test_phase18_live_provider_activation_plan_default_off.py",
        "docs/phase18_provider_runtime_adapter_contract.md",
        "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
        "docs/phase18_live_provider_dry_run_packet_contract.md",
        "tests/test_phase18_live_provider_dry_run_packet_contract_default_off.py",
    }

    assert changed <= allowed


def test_phase18c_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash

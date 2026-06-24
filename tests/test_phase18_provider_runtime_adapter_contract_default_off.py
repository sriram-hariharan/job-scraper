from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_provider_runtime_adapter_contract.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

ADAPTER_STATUSES = [
    "not_configured",
    "disabled",
    "adapter_unavailable",
    "adapter_config_validated",
    "adapter_ready_for_dry_run",
    "adapter_ready_for_provider_call",
    "adapter_blocked",
    "adapter_failed_closed",
]

ADAPTER_FIELDS = [
    "adapter_id",
    "provider_name",
    "provider_operation",
    "model_or_endpoint_identifier",
    "requested_capability",
    "request_schema_summary",
    "response_schema_summary",
    "input_redaction_summary",
    "output_redaction_summary",
    "secrets_reference_name_only",
    "required_feature_flags",
    "timeout_policy",
    "retry_policy",
    "rate_limit_policy",
    "cost_limit_policy",
    "network_policy_summary",
    "dry_run_mode",
    "linked_preview_id",
    "linked_decision_id",
    "linked_activation_id",
    "linked_trace_or_readback_id",
    "safety_flag_summary",
    "fail_closed_reason",
    "rollback_or_disable_reference",
    "created_timestamp",
    "completed_timestamp",
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


def test_adapter_contract_exists_and_names_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Provider Runtime Adapter Contract" in text
    for tag in (
        "phase17-three-core-shadow-readiness-release-v1",
        "phase18a-live-readiness-approval-boundary-v1",
        "phase18b-human-approval-gate-contract-v1",
        "phase18c-approval-preview-readonly-v1",
        "phase18d-operator-decision-capture-contract-v1",
        "phase18e-live-provider-activation-plan-v1",
    ):
        assert f"`{tag}`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18f_is_docs_tests_only_and_implements_no_adapter_or_provider():
    text = _text()

    assert "Phase 18F is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert "Phase 18F does\nnot implement an adapter." in text
    assert "Phase 18F does not activate a provider." in text
    assert "adds no API" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_allowed_future_adapter_statuses_are_exact_and_ordered():
    text = _text()
    section = text[
        text.index("## Allowed future adapter statuses"):
        text.index("## Required future adapter fields")
    ]
    positions = [section.index(f"`{status}`") for status in ADAPTER_STATUSES]

    assert positions == sorted(positions)
    assert sum(section.count(f"`{status}`") for status in ADAPTER_STATUSES) == 9


def test_required_future_adapter_fields_are_listed():
    text = _text()

    for field in ADAPTER_FIELDS:
        assert f"`{field}`" in text


def test_future_adapter_operation_categories_are_complete_but_unimplemented():
    text = _text()
    section = text[
        text.index("## Future adapter operation categories"):
        text.index("## Required future default-off feature flags")
    ]

    for operation in (
        "Configuration validation",
        "Redacted request preview construction",
        "Request schema validation",
        "Response schema validation",
        "Provider call boundary",
        "Passive readback summary",
        "Fail-closed result construction",
    ):
        assert operation in section
    assert "Phase 18F does not implement any of these operations." in section


def test_required_default_off_feature_flags_are_listed():
    text = _text()

    for flag in (
        "Global provider runtime flag",
        "Provider-specific flag",
        "Adapter-specific flag",
        "Operation-specific flag",
        "Dry-run-only flag",
        "Human decision required flag",
        "Mutation-disabled flag",
    ):
        assert flag in text


def test_adapter_safety_requirements_are_complete():
    text = _text()

    for requirement in (
        "Provider SDK invocation must be isolated behind explicit default-off flags.",
        "External network calls must be blocked unless a later provider-call phase is",
        "Secret values must never be logged or returned in readback.",
        "Request and response schemas must be explicit.",
        "Provider responses must be schema-validated before readback or downstream",
        "Provider outputs must remain advisory until a separate mutation phase is",
        "Provider outputs must not mutate final score, rank, queue, resume, or",
        "Timeout, retry, rate limit, and cost policies must be explicit.",
        "Adapter failures must fail closed.",
    ):
        assert requirement in text


def test_prohibited_adapter_responsibilities_are_complete():
    text = _text()
    section = text[
        text.index("## Prohibited adapter responsibilities"):
        text.index("## Failed-closed adapter conditions")
    ]

    for responsibility in (
        "Final scoring mutation",
        "Ranking mutation",
        "Queue mutation",
        "Resume mutation",
        "Approval creation",
        "Decision persistence",
        "Execution request creation",
        "Application execution",
        "Application submission",
        "DB writes outside a separately approved persistence phase",
        "Secrets retrieval without a separately approved secrets boundary",
    ):
        assert responsibility in section


def test_failed_closed_adapter_conditions_are_complete():
    text = _text()

    for condition in (
        "Missing global provider runtime flag",
        "Missing provider-specific flag",
        "Missing adapter-specific flag",
        "Missing operation-specific flag",
        "Missing linked preview id",
        "Missing linked decision id",
        "Missing linked activation id",
        "Missing provider name",
        "Missing provider operation",
        "Missing model or endpoint identifier",
        "Missing request schema",
        "Missing response schema",
        "Missing redaction policy",
        "Missing timeout policy",
        "Missing retry policy",
        "Missing rate limit policy",
        "Missing cost limit policy",
        "Missing network policy",
        "Unsafe safety flags",
        "Secret value present in output",
        "Attempted mutation or submission",
    ):
        assert condition in text


def test_minimum_future_adapter_observability_is_complete():
    text = _text()

    for field in (
        "Adapter status",
        "Provider name",
        "Provider operation",
        "Requested capability",
        "Linked preview id",
        "Linked decision id",
        "Linked activation id",
        "Linked trace/readback id",
        "Request schema validation status",
        "Response schema validation status",
        "Redaction summary",
        "Safety flag summary",
        "Timeout/retry/rate-limit/cost policy summary",
        "Fail-closed reason",
    ):
        assert field in text


def test_not_authorized_section_lists_every_forbidden_path():
    text = _text()

    for term in (
        "No adapter implementation.",
        "No live provider execution.",
        "No provider SDK/network call.",
        "No secrets access.",
        "No approval creation runtime.",
        "No decision persistence runtime.",
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


def test_recommended_next_phase_is_dry_run_packet_without_call_or_mutation():
    assert (
        "Phase 18G should be a docs/tests-only live-provider dry-run packet "
        "contract,\nstill no provider call and still no mutation."
        in _text()
    )


def test_phase18f_changes_only_approved_docs_and_tests():
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
        "docs/phase18_provider_runtime_adapter_contract.md",
        "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
        "tests/test_phase18_operator_decision_capture_contract_default_off.py",
        "tests/test_phase18_live_provider_activation_plan_default_off.py",
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
        "src/agents/three_core_approval_preview_runtime.py",
        "docs/phase19_approval_preview_runtime_readonly.md",
        "tests/test_phase19a_three_core_approval_preview_runtime_readonly_default_off.py",
    }

    assert changed <= allowed


def test_phase18f_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash

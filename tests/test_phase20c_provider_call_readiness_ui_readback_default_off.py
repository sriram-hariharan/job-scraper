from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"

PROTECTED_HASHES = {
    "src/app/api.py": "ba752c3a7eaef620476abffb0ecb7ebf8ce023346917ff8fedb5579c9504d41f",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
}


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _readback_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderProviderCallReadinessFixture"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchProviderCallReadinessReadback"
    )
    end = source.index(
        "\nfunction getAgenticReviewApprovalRequestId",
        start,
    )
    return source[start:end]


def test_renderer_and_fixture_gate_exist():
    snippet = _readback_helpers()

    assert "renderProviderCallReadinessReadbackSection" in snippet
    assert "provider_call_readiness_fixture" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet


def test_optional_api_fetch_gate_exists_and_is_default_off():
    snippet = _fetch_helpers()

    assert "provider_call_readiness_api_fetch" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet
    assert "|| !shouldFetchProviderCallReadinessReadback(search)" in snippet


def test_default_off_requires_payload_fixture_or_fetch_gate():
    helpers = _readback_helpers()
    renderer = helpers[
        helpers.index("function renderProviderCallReadinessReadbackSection"):
    ]

    assert "source.provider_call_readiness_result" in helpers
    assert (
        "|| !shouldRenderProviderCallReadinessFixture(search)"
        in helpers
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert "withProviderCallReadinessReadbackApiFetch(" in _source()


def test_panel_title_fields_and_permanent_rule_exist():
    snippet = _readback_helpers()

    for marker in (
        "Provider-Call Readiness Readback",
        "Readiness status",
        "Requested provider capability",
        "Provider name",
        "Requested model",
        "Request packet summary",
        "Validation errors",
        "Read only",
        "Shadow only",
        "Advisory only",
        "Provider call attempted",
        "Provider call authorized",
        "Network call attempted",
        "Decision persisted",
        "Approval created",
        "Execution authorized",
        "Submission authorized",
        "Mutation authorized",
        "Next safe step",
        "Safety metadata summary",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
    ):
        assert marker in snippet


def test_fixture_is_deterministic_read_only_and_non_authorizing():
    snippet = _readback_helpers()

    for marker in (
        "buildProviderCallReadinessFixtureResult",
        '"provider_call_readiness_experiment_ready"',
        '"review_jd_intelligence_packet"',
        '"caller-supplied-provider"',
        '"caller-supplied-model"',
        "read_only: true",
        "shadow_only: true",
        "advisory_only: true",
        "provider_call_attempted: false",
        "provider_call_authorized: false",
        "network_call_attempted: false",
        "decision_persisted: false",
        "approval_created: false",
        "execution_authorized: false",
        "submission_authorized: false",
        "mutation_authorized: false",
    ):
        assert marker in snippet


def test_fixture_does_not_overwrite_supplied_or_fetched_payload():
    snippet = _readback_helpers()

    assert "source.provider_call_readiness_result" in snippet
    assert "return source;" in snippet


def test_api_fetch_is_gated_post_only_and_targets_phase20b_endpoint():
    snippet = _fetch_helpers()
    gate_position = snippet.index(
        "!shouldFetchProviderCallReadinessReadback(search)"
    )
    fetch_position = snippet.index("await fetchJson(")

    assert gate_position < fetch_position
    assert snippet.count(
        '"/api/provider-call-readiness-readback"'
    ) == 1
    assert 'method: "POST"' in snippet
    assert "enabled: false" in snippet


def test_api_response_reuses_renderer_and_failure_is_fail_closed():
    source = _source()
    snippet = _fetch_helpers()

    assert "provider_call_readiness_result: result" in snippet
    assert (
        "renderProviderCallReadinessReadbackSection("
        "providerCallReadinessVisibleTracePayload)"
        in source
    )
    assert "catch (error)" in snippet
    assert '"provider_call_readiness_experiment_failed_closed"' in snippet
    assert "ui_api_fetch_failed: true" in snippet
    assert "read_only: true" in snippet
    assert "provider_call_attempted: false" in snippet
    assert "mutation_authorized: false" in snippet


def test_helpers_add_no_controls_storage_mutation_or_provider_execution():
    snippet = (_readback_helpers() + _fetch_helpers()).lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "data-apply",
        "data-submit",
        "data-execute",
        "data-approval",
        "data-autonomous",
        "localstorage.setitem",
        "sessionstorage.setitem",
        "createapproval(",
        "recordapproval(",
        "persistdecision(",
        "persistaudit(",
        "executeapplication(",
        "submitapplication(",
        "mutatequeue(",
        "updateranking(",
        "mutatescoring(",
        "mutateresume(",
        "providercall(",
        "autoapply(",
        "autosubmit(",
        "autonomousapplicationexecution(",
    ):
        assert marker not in snippet


def test_protected_backend_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase20c_changes_only_static_docs_tests_and_legacy_guards():
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
    }
    allowed = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase20_provider_call_readiness_ui_readback.md",
        "tests/test_phase20c_provider_call_readiness_ui_readback_default_off.py",
        "docs/no_auto_apply_safety_policy.md",
        "docs/phase20_no_auto_apply_safety_checkpoint.md",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "docs/phase20_provider_readiness_release_checkpoint.md",
        "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
        "docs/manual_review_workflow_boundary.md",
        "docs/phase21_manual_review_workflow_boundary.md",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
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
                "agentic_review.js",
                "ba752c3a7eaef620476abffb0ecb7ebf8ce023346917ff8fedb5579c9504d41f",
            )
        )
    }

    assert changed <= allowed | legacy_guards

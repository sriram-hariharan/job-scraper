from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/three_core_shadow_readiness_wrap.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

PHASE_TAGS = [
    "phase17a-three-core-agent-shadow-pipeline-hook-v1",
    "phase17b-three-core-agent-shadow-sidecar-bridge-v1",
    "phase17c-three-core-agent-collector-shadow-wiring-v1",
    "phase17d-three-core-agent-collector-connection-plan-v1",
    "phase17e-three-core-agent-shadow-callable-adapters-v1",
    "phase17f-three-core-agent-collector-callable-wiring-v1",
    "phase17g-three-core-agent-shadow-runtime-readback-v1",
    "phase17h-three-core-agent-shadow-operator-canary-v1",
    "phase17i-three-core-agent-shadow-api-ui-readback-v1",
    "phase17j-three-core-shadow-local-fixture-ui-visibility-v1",
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
    "src/agents/three_core_agent_shadow_pipeline_hook.py": (
        "bdabd60eda23c115dfba27a3221a97d5b6782e61e13a62fd3c431b230c7428d8"
    ),
    "src/agents/shadow_sidecar_hook.py": (
        "0bbc15e9a2bae8e5154ff62b5fda7b6e4989ecc70f1104719197a2cf337ac3df"
    ),
    "src/agents/three_core_agent_shadow_pipeline_connection_plan.py": (
        "b6c244dac9a9f3f3180b928cf1375de77cd41a69c0f8688a8dead6708e188c0b"
    ),
    "src/agents/three_core_agent_shadow_callable_adapters.py": (
        "e7bfcf282a40d254ffbef99d2a8c92abdd2d43ac931741e7a39da1724dd8e37f"
    ),
    "src/agents/three_core_agent_shadow_runtime_readback.py": (
        "7a11a895ebb409b035cdd2851947f310df4b4fc7a58529794a3046fbbb6ac6b4"
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


def test_readiness_wrap_doc_exists_and_names_checkpoint():
    assert DOC.exists()
    assert "# Three-Core Shadow Readiness Wrap" in _text()
    assert "docs/tests only" in _text()


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_all_phase_17a_through_17j_tags_are_documented():
    text = _text()

    for tag in PHASE_TAGS:
        assert f"`{tag}`" in text


def test_known_endpoint_fixture_and_flags_are_exact():
    text = _text()

    for term in (
        "/api/three-core-shadow-operator-canary-readback",
        "?three_core_canary_fixture=1",
        "APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_SHADOW_PIPELINE_HOOK_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED",
    ):
        assert f"`{term}`" in text


def test_default_off_read_only_shadow_only_advisory_only_are_explicit():
    text = _text()

    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_mutation_and_application_paths_are_not_authorized():
    text = _text().lower()

    for term in (
        "mutation authorization | not authorized",
        "final scoring mutation | not authorized",
        "ranking mutation | not authorized",
        "queue mutation | not authorized",
        "resume mutation | not authorized",
        "application execution | not authorized",
        "application submission | not authorized",
    ):
        assert term in text


def test_provider_network_database_and_file_io_are_not_used():
    text = _text()

    for term in (
        "Provider SDK call | Not used",
        "Network call | Not used",
        "Database read/write | Not used",
        "File IO | Not used",
    ):
        assert term in text


def test_fixture_verification_forbids_action_controls():
    text = _text().lower()

    assert "?three_core_canary_fixture=1" in text
    assert "no apply, submit, execute, or approval control appears" in text
    assert "only when" in text
    assert "real" in text


def test_next_safe_decision_options_are_documented_in_order():
    text = _text()
    options = [
        "Keep the completed Phase 17 surface shadow-only.",
        "Promote these readiness docs to the main release.",
        "Design a separate protected approval plan before any live provider or",
    ]
    positions = [text.index(option) for option in options]

    assert positions == sorted(positions)


def test_phase_17k_changes_only_approved_docs_and_tests():
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
        "docs/three_core_shadow_readiness_wrap.md",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "docs/phase18_live_readiness_approval_boundary.md",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
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
    }

    assert changed <= allowed


def test_phase_17_runtime_files_match_readiness_checkpoint_hashes():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash


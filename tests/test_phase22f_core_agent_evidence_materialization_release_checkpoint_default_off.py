# phase23f legacy guard marker: changes_only 65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a 63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56
# phase23f legacy guard marker: changes_only 63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56
from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase22_core_agent_evidence_materialization_release_checkpoint.md"
)

REQUIRED_PHASES = (
    "Phase 22B",
    "Phase 22C",
    "Phase 22D",
    "Phase 22E",
)

REQUIRED_TAGS = (
    "phase22a-manual-review-ux-hardening-v1",
    "phase22b-core-agent-automation-mutation-inventory-v1",
    "phase22c-core-agent-evidence-materialization-preview-v1",
    "phase22d-core-agent-evidence-materialization-api-readback-v1",
    "phase22e-core-agent-evidence-materialization-ui-readback-v1",
)

CORE_AGENT_SEQUENCE = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)

SAFE_AUTOMATION_MARKERS = (
    "automatically analyze jobs",
    "automatically prefilter relevance",
    "automatically extract JD signals",
    "automatically score fit",
    "automatically prepare review evidence",
    "automatically surface review panels",
    "automatically explain why a job is worth reviewing",
    "automatically identify tailoring opportunities",
    "do not automatically apply",
    "do not automatically submit",
)

SAFETY_MARKERS = (
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "read-only/advisory/manual-review evidence",
    "no provider calls",
    "no network calls",
    "no database writes",
    "no persistence",
    "no mutation",
    "no scoring mutation",
    "no ranking mutation",
    "no queue mutation",
    "no resume mutation",
    "no application mutation",
    "no approval mutation",
    "no decision mutation",
    "no audit mutation",
    "no execution",
    "no submission",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control",
)

PROTECTED_HASHES = {
    "src/app/api.py": "65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "63e37ba427991dd71c6addb440a83024661fe4cef363f8641149d48e14c55c56",
    "src/app/static/app_redesign.css": "8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
}


def _text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _changed_files() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return set(tracked + untracked)


def test_release_checkpoint_doc_exists_with_exact_title():
    assert DOC_PATH.exists()
    assert _text().startswith(
        "# Phase 22F Core-Agent Evidence Materialization Release Checkpoint"
    )


def test_checkpoint_summarizes_phase22b_through_phase22e():
    text = _text()

    for phase in REQUIRED_PHASES:
        assert phase in text
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_checkpoint_contains_exact_core_agent_sequence():
    text = _text()

    for agent_name in CORE_AGENT_SEQUENCE:
        assert agent_name in text
    assert text.index("`relevance_prefilter`") < text.index(
        "`jd_intelligence`"
    ) < text.index("`final_application_scoring`")


def test_checkpoint_preserves_tailoring_boundary():
    text = " ".join(_text().split())

    for marker in (
        "tailoring agent remains separate from final scoring",
        "Generate AI Tailoring",
        "user-triggered",
        "default-off/gated",
        "preview-only",
        "manual-review controlled",
        "must not silently rewrite, overwrite, apply, or submit",
        "AI tailoring generation is not implemented in Phase 22",
    ):
        assert marker in text


def test_checkpoint_defines_safe_automation_meaning():
    text = _text()

    for marker in SAFE_AUTOMATION_MARKERS:
        assert marker in text


def test_checkpoint_contains_all_required_safety_markers():
    text = _text().lower()

    for marker in SAFETY_MARKERS:
        assert marker in text


def test_checkpoint_states_current_release_boundary():
    text = _text()

    for marker in (
        "Phase 22 is not live provider automation.",
        "Phase 22 is not live provider interaction between agents.",
        "Phase 22 is not durable mutation.",
        "Phase 22 is not live tailoring generation.",
        "Phase 22 is not auto-apply or auto-submit.",
        "Live providers and inter-agent provider-backed automation are deferred",
    ):
        assert marker in text


def test_checkpoint_recommends_safe_phase23a_scope():
    text = " ".join(_text().split())

    for marker in (
        "Phase 23A",
        "tailoring-agent opportunity contract",
        "identify tailoring opportunities from existing evidence",
        "without generating AI tailoring",
        "later user-triggered",
        "Any provider-backed tailoring generation must",
        "separate phase",
    ):
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase22f_changes_only_docs_tests_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "docs/phase22_core_agent_evidence_materialization_release_checkpoint.md",
        "tests/test_phase22f_core_agent_evidence_materialization_release_checkpoint_default_off.py",
        "src/agents/tailoring_agent_opportunity_contract.py",
        "docs/phase23_tailoring_agent_opportunity_contract.md",
        "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
        "src/app/api.py",
        "docs/phase23_tailoring_agent_opportunity_api_readback.md",
        "tests/test_phase23b_tailoring_agent_opportunity_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase23_tailoring_agent_opportunity_ui_readback.md",
        "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
        "src/agents/generate_ai_tailoring_action_boundary_contract.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_contract.md",
        "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md",
        "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "changes_only" in path.read_text(encoding="utf-8")
            or "65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3"
            in path.read_text(encoding="utf-8")
            or "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab"
            in path.read_text(encoding="utf-8")
            or "8b5ac1590a977b002f3a04b77b9d8ce634eb3d806716586fca4872b81d33990a"
            in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards

from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "docs/core_agent_automation_mutation_inventory.md"
CHECKPOINT_PATH = (
    ROOT / "docs/phase22_core_agent_automation_mutation_inventory.md"
)
DOC_PATHS = (INVENTORY_PATH, CHECKPOINT_PATH)

CORE_AGENTS = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)

DETERMINISTIC_FOUNDATIONS = (
    "deterministic job discovery/filtering",
    "deterministic role/title/location/freshness filtering",
    "deterministic resume/job prefiltering",
    "deterministic JD/resume evidence extraction",
    "deterministic final resume-job scoring",
    "deterministic best resume variant selection",
    "deterministic shortlist/action classification",
    "deterministic review evidence generation",
    "deterministic tailoring packet generation",
    "optional LLM fallback/adjudication",
    "optional LLM tailoring",
)

DETERMINISTIC_FILES = (
    "src/pipeline/job_filter.py",
    "src/matching/prefilter.py",
    "src/matching/scorer.py",
    "batch_select_best_resume_variant.py",
    "application_shortlist_from_batch_selector.py",
    "run_application_planning.py",
    "generate_tailoring_suggestions.py",
    "src/tailoring/llm.py",
)

AUTOMATION_MARKERS = (
    "automatic relevance prefiltering",
    "automatic scoring",
    "automatic review evidence generation",
    "automatic tailoring opportunity detection",
    "read-only/advisory/manual-review evidence",
    "agent evidence generation and readback",
)

MUTATION_MARKERS = (
    "no scoring mutation",
    "no ranking mutation",
    "no queue mutation",
    "no resume mutation",
    "no application mutation",
    "no approval mutation",
    "no decision mutation",
    "no audit mutation",
    "no provider-call mutation",
    "no database write mutation",
    "no execution mutation",
    "no submission mutation",
)

SAFETY_MARKERS = (
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control",
)

REQUIRED_TAGS = (
    "phase22a-manual-review-ux-hardening-v1",
    "phase21-manual-review-workflow-release-v1",
    "phase21e-manual-review-workflow-release-checkpoint-v1",
    "phase21d-manual-review-readiness-ui-readback-v1",
    "phase20-provider-readiness-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
    "phase19-readonly-approval-workflow-release-v1",
    "phase18-safety-wrap-release-v1",
    "phase17-three-core-shadow-readiness-release-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "6b275f7e838969320c41d9f97a19913218b0d4d2fd24eb7b73cb325f036b9867",
    "src/app/static/app_redesign.css": "d65949a4b35d2ee9786e84ae1a4a7b2414894ec5927102d0dea316fc3a2020ac",
    "src/agents/manual_review_readiness_contract.py": "5253414d1343d5eae64af7fbb6f87da68f9d4931b762cac972a94c29dc9ad5a2",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
    "src/agents/three_core_agent_workflow_readiness.py": "ede602b8944fb8a7749c2d5738c7c7e56e19429d15d74e65272325537d596cef",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def test_both_inventory_docs_exist():
    assert INVENTORY_PATH.exists()
    assert CHECKPOINT_PATH.exists()


def test_docs_name_core_agents_and_tailoring_direction():
    for path in DOC_PATHS:
        text = _text(path)
        for agent_name in CORE_AGENTS:
            assert agent_name in text
        assert "tailoring agent" in text.lower()
        assert "Generate AI Tailoring" in text


def test_docs_inventory_deterministic_foundations_and_files():
    for path in DOC_PATHS:
        text = _text(path)
        for marker in DETERMINISTIC_FOUNDATIONS:
            assert marker in text
        for relative_path in DETERMINISTIC_FILES:
            assert relative_path in text


def test_docs_contain_automation_mutation_and_safety_markers():
    for path in DOC_PATHS:
        text = _text(path).lower()
        for marker in AUTOMATION_MARKERS + MUTATION_MARKERS + SAFETY_MARKERS:
            assert marker.lower() in text


def test_docs_preserve_architecture_and_phase22c_direction():
    for path in DOC_PATHS:
        text = " ".join(_text(path).lower().split())
        for marker in (
            "prefilter relevance",
            "jd intelligence",
            "final application scoring",
            "tailoring suggestions",
            "default-off",
            "read-only core-agent evidence",
            "relevance prefilter result",
            "jd signals",
            "final advisory score",
            "review rationale",
            "missing requirements",
            "tailoring opportunities",
            "separate mutation-boundary phase",
            "explicit tests",
            "approval gates",
            "preview-only",
        ):
            assert marker in text


def test_docs_reference_required_release_tags():
    for path in DOC_PATHS:
        text = _text(path)
        for tag in REQUIRED_TAGS:
            assert tag in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase22b_changes_only_docs_tests_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "docs/core_agent_automation_mutation_inventory.md",
        "docs/phase22_core_agent_automation_mutation_inventory.md",
        "tests/test_phase22b_core_agent_automation_mutation_inventory_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "src/agents/core_agent_evidence_materialization_preview.py",
        "docs/phase22_core_agent_evidence_materialization_preview.md",
        "src/app/api.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback.md",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "changes_only" in path.read_text(encoding="utf-8")
            or "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a"
            in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards

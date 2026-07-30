from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ARCHITECTURE = ROOT / "docs/architecture_summary.md"
ROADMAP = ROOT / "docs/full_fledged_agentic_ai_app_roadmap.md"
INVENTORY = ROOT / "docs/core_agent_automation_mutation_inventory.md"
HISTORICAL_INVENTORY = (
    ROOT / "docs/phase22_core_agent_automation_mutation_inventory.md"
)
DOCS = (README, ARCHITECTURE, ROADMAP, INVENTORY)

CANONICAL_AGENTS = (
    "Discovery Agent",
    "Relevance Prefilter Agent",
    "Deduplication Agent",
    "JD Intelligence Agent",
    "Resume Match Agent",
    "Tailoring Suggestion Agent",
    "Critic / Guardrail Agent",
    "Strategy Agent",
)


def _text(path):
    return path.read_text(encoding="utf-8")


def test_exact_eight_canonical_agents_are_in_current_inventory():
    text = _text(INVENTORY)
    headings = re.findall(r"\d+\. \*\*(.+? Agent)\*\*", text)
    assert tuple(headings[:8]) == CANONICAL_AGENTS
    assert len(headings[:8]) == 8


def test_every_agent_reports_required_release_dimensions():
    text = _text(INVENTORY)
    for marker in (
        "Responsibility:",
        "Execution:",
        "Production owner",
        "Production caller:",
        "Graph participation:",
        "Default gate:",
        "Cache behavior:",
        "Durability:",
        "Telemetry:",
        "Human-review relationship:",
        "Authority:",
    ):
        assert text.count(marker) >= 8


def test_release_docs_state_current_orchestration_and_llm_boundaries():
    combined = " ".join(
        "\n".join(_text(path) for path in DOCS).split()
    )
    for marker in (
        "prefilter",
        "deduplication",
        "final scoring",
        "job prioritization",
        "tailoring decision",
        "operator review",
        "JD intelligence",
        "semantic job-fit evaluation",
        "tailoring generation",
        "critic remains deterministic",
        "default-off",
    ):
        assert marker.lower() in combined.lower()


def test_release_docs_state_durability_telemetry_and_human_action_truthfully():
    combined = " ".join(
        "\n".join(_text(path) for path in DOCS).split()
    )
    for marker in (
        "committed replay",
        "restart",
        "representative",
        "continue_read_only",
        "needs_revision",
        "cancel",
        "authenticated",
        "read-only",
        "not application approval",
    ):
        assert marker.lower() in combined.lower()
    assert "no claim of complete all-node telemetry" in combined.lower()
    assert "not a claim of exactly-once provider execution" in combined.lower()


def test_release_docs_preserve_no_application_or_ats_authority():
    combined = " ".join(
        "\n".join(_text(path) for path in DOCS).split()
    )
    for marker in (
        "no application authority",
        "no mutation, application, or ATS authority",
        "auto-apply",
        "submit to an ATS",
    ):
        assert marker.lower() in combined.lower()
    assert "64 autonomous agents" not in combined.lower()
    assert "fully autonomous job application" not in combined.lower()


def test_phase22_inventory_is_explicitly_historical_compatibility():
    text = " ".join(_text(HISTORICAL_INVENTORY).lower().split())
    assert "historical compatibility contract" in text
    assert "current eight-agent production reachability" in text
    assert "not current release claims" in text

# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
from hashlib import sha256
from pathlib import Path

from src.app import services
from tests.support.phase_guard_registry import assert_protected_hashes


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
ENDPOINT = "/api/pgvector-extension-probe"


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _section_snippet() -> str:
    source = _source()
    start = source.index("function renderPgvectorExtensionProbeSection")
    end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _handler_snippet() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-pgvector-extension-probe]")'
    )
    end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        start,
    )
    return source[start:end]


def _init_snippet() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);'
    )
    return source[start:end]


def test_ui_includes_operator_triggered_pgvector_probe_fetch_and_display_hook():
    source = _source()
    section = _section_snippet()
    handler = _handler_snippet()

    assert "function renderPgvectorExtensionProbeSection" in source
    assert "pgvector Extension Probe" in section
    assert "data-pgvector-extension-probe" in section
    assert "Check Probe Status" in section
    assert "renderPgvectorExtensionProbeSection(tracePayload)" in source
    assert ENDPOINT in handler
    assert 'method: "POST"' in handler
    assert "pgvector_extension_probe_result" in handler


def test_ui_displays_probe_status_extension_version_and_dimension_fields():
    section = _section_snippet()

    for phrase in (
        'renderWorkflowSummaryMetric("Probe status", status)',
        'renderWorkflowSummaryMetric("Extension available"',
        'renderWorkflowSummaryMetric("Extension version"',
        'renderWorkflowSummaryMetric("Embedding dimension supported"',
        "extension_available",
        "extension_version",
        "embedding_dimension_supported",
    ):
        assert phrase in section


def test_ui_displays_skipped_reasons_without_raw_json_by_default():
    section = _section_snippet()

    assert "skipped_reasons" in section
    assert "<strong>Skipped reasons</strong>" in section
    assert "renderReasonChips(skippedReasons)" in section
    assert "<details" not in section
    assert "<pre>" not in section
    assert "JSON.stringify" not in section


def test_ui_labels_probe_readonly_advisory_and_displays_safety_states():
    section = _section_snippet()

    for phrase in (
        "Read-only and advisory",
        "Advisory read-only",
        'renderWorkflowSummaryMetric("pgvector installed by app"',
        'renderWorkflowSummaryMetric("Schema created"',
        'renderWorkflowSummaryMetric("Migration created"',
        'renderWorkflowSummaryMetric("Embeddings created"',
        'renderWorkflowSummaryMetric("Automatic DB connection"',
        'renderWorkflowSummaryMetric("Provider calls"',
        "false / default-off",
        "does not install pgvector",
        "does not install pgvector, create schema or migrations",
        "create embeddings",
        "call providers",
        "connect automatically to Postgres",
    ):
        assert phrase in section


def test_ui_has_no_install_schema_mutation_or_execution_controls():
    combined = (_section_snippet() + "\n" + _handler_snippet()).lower()
    forbidden_controls = (
        "data-install-pgvector",
        "data-enable-pgvector",
        "data-create-schema",
        "data-run-migration",
        "data-scoring-override",
        "data-ranking-override",
        "data-queue",
        "data-approve",
        "data-reject",
        "data-resume",
        "data-execute",
        "data-submit",
        "install pgvector</button>",
        "enable pgvector</button>",
        "create schema</button>",
        "run migration</button>",
        "approve application</button>",
        "execute application</button>",
        "submit application</button>",
        "/api/manual-approval",
        "/api/manual-queue",
        "/api/manual-execution",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    )
    for marker in forbidden_controls:
        assert marker not in combined


def test_ui_calls_probe_only_from_explicit_action_without_auto_refresh():
    handler = _handler_snippet()
    init_snippet = _init_snippet()

    assert ENDPOINT in handler
    assert ENDPOINT not in init_snippet
    assert "setInterval" not in handler
    assert "setInterval" not in init_snippet
    assert "requested_dimension: null" in handler
    assert "read_only: true" in handler
    assert "advisory_only: true" in handler


def test_default_probe_keeps_provider_and_mutation_authorized_agents_zero():
    payload = services.pgvector_extension_probe_service_helper_payload()

    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_no_api_service_pipeline_schema_migration_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": (
            "2b93b37a38fce17d50a9b5eb693062faa9bb9ada6a4926bb9e0f76d9ee518674"
        ),
        "src/pipeline/collector.py": (
            "261e2b0e40adf1e0e79842f281a06d61aad59f2432fbf8fd4fa8a3d5585b3f3e"
        ),
        "requirements.txt": (
            "75d10d919dd53cdc3e55056abe28503b5b0bde38d5e61d944beb794562886cc3"
        ),
        "src/storage/agent_trace/schema.sql": (
            "69305cd1bec0be9caa8c8c1b93e8fc10a3e80a92c08acd5683e7800763d2a77a"
        ),
        "src/storage/agentic_approvals/schema.sql": (
            "57e84094cdbd3a4e8542fd205d89bfde18179c5d07c15084354f31f77bf5d98f"
        ),
        "src/storage/profile_resumes/schema.sql": (
            "a71d55d9306258661b99f9bc88aa122fbf24443e7bd43a9ba597133289df1e57"
        ),
        "application_execution_queue.py": (
            "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f"
        ),
    }
    assert_protected_hashes(
        ROOT,
        protected_hashes,
        compatibility_profiles=(
            "phase129c_workflow_overlay_and_run_scoped_corpus",
        ),
    )

    schema_and_migration_paths = [
        path
        for path in (ROOT / "src/storage").rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name != ".DS_Store"
        and path.suffix != ".pyc"
        and (
            path.suffix == ".sql"
            or "migration" in path.name.lower()
            or "migrations" in path.parts
            or "alembic" in path.parts
        )
        and path != ROOT / "src/storage/vector_evidence/schema.sql"
    ]
    digest = sha256()
    for path in sorted(
        schema_and_migration_paths,
        key=lambda item: item.relative_to(ROOT).as_posix(),
    ):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    assert digest.hexdigest() == (
        "7dba8092148c9c401ff56f779adff7dc4363dfec3f67f1502ed549a437a8b4f6"
    )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "pgvector" not in requirements

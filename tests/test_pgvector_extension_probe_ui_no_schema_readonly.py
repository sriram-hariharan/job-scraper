# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
from hashlib import sha256
from pathlib import Path

from src.app import services


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
            "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"
        ),
        "src/pipeline/collector.py": (
            "cae9f4a51ef14c7b1185a64f2e229591274c284c2985989ec1f5997f7728ee42"
        ),
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
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
            "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
        ),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
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
        "27e2efd8f1b55117b3d8a27572672152b7e8127733ed5408fe3f353595f1c1ed"
    )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "pgvector" not in requirements

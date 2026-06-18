from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.md"

DEPENDENCY_FILES = (
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "setup.py",
    "setup.cfg",
    "environment.yml",
    "uv.lock",
)


def _doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


def _protected_files(root: str) -> list[Path]:
    return [
        path
        for path in (ROOT / root).rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name != ".DS_Store"
        and path.suffix != ".pyc"
    ]


def _aggregate_hash(paths: list[Path]) -> str:
    digest = sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix()):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def test_phase8i_pgvector_readiness_doc_exists():
    assert DOC.exists()
    assert DOC.is_file()


def test_doc_states_no_runtime_dependency_schema_or_migration_change():
    text = _doc_text()

    for phrase in (
        "no runtime change",
        "no dependency change",
        "no schema or migration",
        "No SQL artifact, migration, storage adapter, database connection",
        "No extension probe is executed in Phase 8I",
        "No schema/migration is applied in Phase 8I",
    ):
        assert phrase in text


def test_doc_maps_plan_to_existing_storage_schema_dependency_structure():
    text = _doc_text()

    for phrase in (
        "`src/storage/<domain>/`",
        "`store.py`",
        "`read_postgres.py`",
        "`schema.sql`",
        "`src/storage/admin_tools/*/apply_schema.py`",
        "`src/storage/agent_state/migration_runner.py`",
        "`src/storage/rag_store.py`",
        "`src/storage/profile_resumes/`",
        "`src/storage/agent_trace/`",
        "`DATABASE_URL`",
        "`requirements.txt`",
        "There is no Alembic directory",
        "separate `src/storage/vector_evidence/` domain only after explicit approval",
    ):
        assert phrase in text


def test_doc_recommends_postgres_pgvector_as_recommendation_only():
    text = _doc_text()

    assert (
        "Recommendation only: Postgres + pgvector is the preferred first backend"
        in text
    )
    assert "not authorization to install the extension" in text
    assert "does not imply that vector workload belongs in existing transactional tables" in text


def test_doc_includes_required_extension_checks():
    text = _doc_text()

    for phrase in (
        "`pg_available_extensions`",
        "`pg_extension`",
        "`CREATE EXTENSION vector`",
        "Postgres server version",
        "pgvector extension version",
        "supported vector dimensions",
        "HNSW and/or IVFFlat",
        "backup coverage",
        "replica compatibility",
        "Fail closed",
    ):
        assert phrase in text


def test_doc_includes_proposed_tables_and_columns():
    text = _doc_text()

    for table in (
        "`vector_evidence_chunks`",
        "`vector_evidence_embeddings`",
        "`vector_evidence_retrieval_events`",
    ):
        assert table in text

    for column in (
        "`chunk_id",
        "`chunk_type",
        "`content_hash",
        "`normalized_text",
        "`metadata JSONB",
        "`job_id",
        "`company",
        "`title",
        "`source",
        "`stage",
        "`agent_name",
        "`trace_id",
        "`run_id",
        "`resume_version",
        "`profile_version",
        "`owner_user_id",
        "`embedding_model_id",
        "`embedding_dimension",
        "`embedding VECTOR",
        "`created_at",
        "`updated_at",
        "`deleted_at",
    ):
        assert column in text


def test_doc_includes_proposed_indexes_migration_and_rollback():
    text = _doc_text()

    for phrase in (
        "Unique chunk-version dedup index",
        "B-tree metadata lookup indexes",
        "GIN index on `metadata`",
        "HNSW or IVFFlat vector index is proposal only",
        "Migration and rollback plan",
        "Create `vector_evidence_chunks`, then `vector_evidence_embeddings`, then `vector_evidence_retrieval_events`",
        "Set the kill switch",
        "Drop `vector_evidence_retrieval_events`, then `vector_evidence_embeddings`, then `vector_evidence_chunks`",
        "Rollback must never delete source jobs",
    ):
        assert phrase in text


def test_doc_includes_flags_privacy_dedup_and_stale_cleanup():
    text = _doc_text()

    for flag in (
        "APPLYLENS_PGVECTOR_EXTENSION_PROBE_ENABLED",
        "APPLYLENS_VECTOR_BACKEND",
        "APPLYLENS_VECTOR_RETRIEVAL_ENABLED",
        "APPLYLENS_VECTOR_INDEX_WRITES_ENABLED",
        "APPLYLENS_VECTOR_RESUME_CHUNKS_ENABLED",
        "APPLYLENS_VECTOR_PROVIDER_EMBEDDINGS_ENABLED",
        "APPLYLENS_VECTOR_RETRIEVAL_SHADOW_ONLY",
        "APPLYLENS_VECTOR_KILL_SWITCH",
    ):
        assert flag in text

    for phrase in (
        "Privacy controls for resume/profile and trace data",
        "cross-owner access denial",
        "Never index raw resume binaries",
        "Do not log raw query or evidence text",
        "Deduplication and stale chunk cleanup",
        "`content_hash` plus owner/tenant",
        "Mark replaced source versions with `deleted_at`",
        "never on import, startup, API read, or UI load",
    ):
        assert phrase in text


def test_doc_includes_deterministic_tests_and_observability():
    text = _doc_text()

    for phrase in (
        "Deterministic test strategy",
        "synthetic owner-scoped fixtures",
        "fixed local vectors",
        "stable ordering by distance, chunk type, and chunk ID",
        "do not call providers or require network access",
        "Chunk provenance",
        "Retrieval event trace",
        "No-result fallback",
        "Latency and volume metrics",
        "query latency percentiles",
        "no-result rate",
    ):
        assert phrase in text


def test_doc_preserves_existing_operational_flows_and_safety_boundaries():
    text = _doc_text()

    for phrase in (
        "Existing collector logging, config, HTTP retry, Redis caching, job deduplication, deterministic ranking, pipeline metrics, and ATS health checks must be preserved unchanged",
        "Prefilter relevance",
        "LLM/shadow evaluation",
        "Final application scoring",
        "Retrieval/evidence support",
        "no scoring mutation",
        "no ranking mutation",
        "no queue or application mutation",
        "no approval or resume mutation",
        "no application execution",
        "no submission automation",
        "no provider-backed automation without explicit default-off flags",
    ):
        assert phrase in text


def test_doc_includes_required_future_implementation_phases():
    text = _doc_text()

    for phase in (
        "Extension probe",
        "Schema proposal",
        "Schema migration",
        "Local no-provider embedding stub",
        "Provider-backed embedding integration behind flags",
        "Retrieval backend adapter",
        "Service/API/UI switch from dry-run to backend under flags",
    ):
        assert phase in text


def test_all_src_runtime_files_match_phase8i_checkpoint():
    assert _aggregate_hash(_protected_files("src")) == (
        "7d590a0f3e591a4a3a31d69d0295c0138962d5d170385543001732cba02ffe96"
    )


def test_dependency_files_match_phase8i_checkpoint():
    paths = [ROOT / path for path in DEPENDENCY_FILES if (ROOT / path).is_file()]

    assert [path.relative_to(ROOT).as_posix() for path in paths] == [
        "requirements.txt"
    ]
    assert _aggregate_hash(paths) == (
        "732c3ef29d3263d032c7aac24232ae41ae99fa77d82b1295d314ffc1ec1af482"
    )


def test_storage_schema_and_migration_files_match_phase8i_checkpoint():
    paths = [
        path
        for path in _protected_files("src/storage")
        if path.suffix == ".sql"
        or "migration" in path.name.lower()
        or "migrations" in path.parts
        or "alembic" in path.parts
    ]

    assert _aggregate_hash(paths) == (
        "27e2efd8f1b55117b3d8a27572672152b7e8127733ed5408fe3f353595f1c1ed"
    )


def test_root_queue_execution_surface_matches_phase8i_checkpoint():
    paths = [ROOT / "application_execution_queue.py"]

    assert all(path.exists() for path in paths)
    assert _aggregate_hash(paths) == (
        "c6ec977f78103f5951bcbf493f868c7b82aa561f898cf46831361d1e359302cb"
    )

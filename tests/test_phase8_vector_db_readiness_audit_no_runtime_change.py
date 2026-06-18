from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase8_vector_db_readiness_audit_no_runtime_change.md"

ALLOWED_CHANGED = {
    "docs/phase8_vector_db_readiness_audit_no_runtime_change.md",
    "tests/test_phase8_vector_db_readiness_audit_no_runtime_change.py",
    "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
}

DEPENDENCY_FILES = {
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
}

PROTECTED_PREFIXES = (
    "src/",
    "alembic/",
    "migrations/",
)

PROTECTED_PATH_PARTS = (
    "/schema.sql",
    "/migrations/",
)

REQUIRED_AUDIT_TERMS = (
    "Phase 8A is a docs/test-only readiness audit",
    "no runtime change",
    "adds no dependencies",
    "no schema change",
    "Existing evidence sources that could become vector chunks",
    "Job description chunks",
    "Resume/profile chunks",
    "Trace evidence chunks",
    "Operator review packet chunks",
    "Future application outcome feedback chunks",
    "`job_id`",
    "`company`",
    "`title`",
    "`source`",
    "`stage`",
    "`agent_name`",
    "`trace_id`",
    "`run_id`",
    "`resume_version`",
    "`profile_version`",
    "`created_at`",
    "`safety_flags`",
    "`read_only`",
    "JD intelligence evidence retrieval",
    "Resume match evidence retrieval",
    "Tailoring suggestion evidence retrieval",
    "Critic/guardrail evidence retrieval",
    "Operator review packet evidence retrieval",
    "Postgres + pgvector",
    "External managed vector DB",
    "Local dev-only store",
    "Recommended first backend — recommendation only",
    "Required feature flags",
    "No-runtime-change migration plan",
    "Future Phase 8B+ plan",
    "Embedding drift",
    "Stale job descriptions",
    "Duplicate chunks",
    "Privacy/resume leakage",
    "Retrieval influencing score without approval",
    "Provider cost/rate limits",
    "Test determinism",
    "Safety boundaries",
    "Observability requirements",
    "retrieval trace entries",
    "chunk provenance",
    "retrieval confidence",
    "fallback when no evidence is found",
    "deterministic test fixtures",
)


def _changed_files() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return {path for path in tracked + untracked if path}


def _doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_phase8_vector_db_readiness_audit_doc_exists():
    assert DOC.exists()
    assert DOC.is_file()


def test_phase8_audit_states_no_runtime_dependency_or_schema_change():
    text = _doc_text()

    assert "no runtime change" in text
    assert "adds no dependencies" in text
    assert "no schema change" in text
    assert "does not add a vector database" in text
    assert "does not add pgvector, Pinecone, Chroma, FAISS, LangChain, or LangGraph" in text
    assert "does not modify `src/`, `requirements.txt`, SQL, migrations" in text


def test_phase8_audit_contains_required_inventory_chunks_metadata_flows_and_risks():
    text = _doc_text()
    missing = [term for term in REQUIRED_AUDIT_TERMS if term not in text]

    assert not missing, f"Missing Phase 8A audit terms: {missing}"


def test_phase8_audit_maps_retrieval_to_existing_pipeline_agents_and_storage():
    text = _doc_text()

    for path in (
        "`src/pipeline/collector.py`",
        "`src/agents/jd_intelligence.py`",
        "`src/agents/resume_match_agent.py`",
        "`src/agents/tailoring_decision_agent.py`",
        "`src/agents/critic_agent.py`",
        "`src/agents/pipeline_agent_review_packet.py`",
        "`src/storage/rag_store.py`",
        "`src/storage/agent_trace/`",
        "`src/storage/profile_resumes/`",
    ):
        assert path in text


def test_phase8_audit_separates_evaluation_and_retrieval_boundaries():
    text = _doc_text()

    assert "Prefilter relevance" in text
    assert "LLM/shadow evaluation" in text
    assert "Final application scoring" in text
    assert "Retrieval/evidence support" in text
    assert "must stay separate" in text
    assert "Retrieval must not write, lift, suppress, or otherwise influence this score" in text
    assert "advisory evidence only" in text


def test_phase8_audit_includes_backend_options_and_recommendation_only():
    text = _doc_text()

    assert "### Postgres + pgvector" in text
    assert "### External managed vector DB" in text
    assert "### Local dev-only store" in text
    assert (
        "Recommendation only: use Postgres + pgvector as the first "
        "production-oriented backend"
    ) in text
    assert "It is not approval to install pgvector" in text


def test_phase8_audit_includes_default_off_feature_flags():
    text = _doc_text()

    for flag in (
        "APPLYLENS_VECTOR_RETRIEVAL_ENABLED",
        "APPLYLENS_VECTOR_INDEX_WRITES_ENABLED",
        "APPLYLENS_VECTOR_JOB_CHUNKS_ENABLED",
        "APPLYLENS_VECTOR_RESUME_CHUNKS_ENABLED",
        "APPLYLENS_VECTOR_TRACE_CHUNKS_ENABLED",
        "APPLYLENS_VECTOR_REVIEW_PACKET_CHUNKS_ENABLED",
        "APPLYLENS_VECTOR_OUTCOME_FEEDBACK_CHUNKS_ENABLED",
        "APPLYLENS_VECTOR_PROVIDER_EMBEDDINGS_ENABLED",
        "APPLYLENS_VECTOR_RETRIEVAL_SHADOW_ONLY",
        "APPLYLENS_VECTOR_KILL_SWITCH",
    ):
        assert flag in text

    assert "default all retrieval and provider behavior off" in text
    assert "Read and write flags must be separate" in text


def test_phase8_audit_includes_safety_boundaries():
    text = _doc_text()

    for boundary in (
        "Retrieval must not mutate scoring, ranking, queue state, approvals, application execution, or application submission",
        "Retrieval output must be advisory evidence",
        "No automatic submission is permitted",
        "No provider-backed automation is permitted without explicit default-off flags",
        "fail closed to a clear no-evidence result",
    ):
        assert boundary in text


def test_phase8_audit_includes_observability_requirements():
    text = _doc_text()

    for requirement in (
        "retrieval trace entries",
        "chunk provenance",
        "retrieval confidence or distance",
        "a deterministic fallback when no evidence is found",
        "deterministic test fixtures",
        "no provider/network requirement",
    ):
        assert requirement in text


def test_phase8_audit_includes_future_phase8b_plus_plan():
    text = _doc_text()

    for phase in (
        "Phase 8B — contracts and deterministic fixtures",
        "Phase 8C — backend spike behind flags",
        "Phase 8D — offline indexing",
        "Phase 8E — shadow retrieval",
        "Phase 8F — owner-scoped resume and trace evidence",
    ):
        assert phase in text


def test_phase8_is_limited_to_the_docs_test_checkpoint_files_when_active():
    changed = _changed_files()

    if not changed:
        return

    assert changed <= ALLOWED_CHANGED, (
        "Phase 8A is docs/checkpoint-test only; unexpected changed files: "
        f"{sorted(changed - ALLOWED_CHANGED)}"
    )


def test_phase8_changes_no_runtime_dependency_schema_or_behavior_surface():
    changed = _changed_files()

    runtime_changes = sorted(
        path for path in changed if path.startswith(PROTECTED_PREFIXES)
    )
    dependency_changes = sorted(
        path
        for path in changed
        if Path(path).name in DEPENDENCY_FILES
        or path.startswith("requirements")
    )
    schema_changes = sorted(
        path
        for path in changed
        if path.endswith(".sql")
        or any(part in f"/{path}" for part in PROTECTED_PATH_PARTS)
    )
    forbidden_behavior_changes = sorted(
        path
        for path in changed
        if path.startswith(
            (
                "src/app/",
                "src/pipeline/",
                "src/agents/",
                "src/storage/",
            )
        )
        or any(
            marker in path.lower()
            for marker in (
                "scor",
                "rank",
                "queue",
                "execution",
                "submission",
                "migration",
                "schema",
            )
        )
        and path not in ALLOWED_CHANGED
    )

    assert not runtime_changes
    assert not dependency_changes
    assert not schema_changes
    assert not forbidden_behavior_changes

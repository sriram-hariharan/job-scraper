from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_pipeline_integration_point_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_doc_exists():
    text = _doc_text()
    assert "Phase 5L Shadow Sidecar Pipeline Integration Point Audit" in text
    assert "No runtime behavior change is introduced." in text
    assert "No pipeline wiring was added." in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_lists_exact_inspected_files():
    text = _doc_text()
    required = [
        "src/pipeline/collector.py",
        "src/pipeline/runtime_status.py",
        "src/pipeline/job_filter.py",
        "src/pipeline/dedupe.py",
        "src/pipeline/job_ranker.py",
        "src/pipeline/application_scorer.py",
        "src/pipeline/embedding_prefilter.py",
        "src/intelligence/job_intelligence.py",
        "src/ai/job_fit_evaluator.py",
        "src/utils/pipeline_metrics.py",
        "src/utils/log_sections.py",
        "src/utils/job_cache.py",
        "src/utils/http_retry.py",
        "src/utils/ats_health.py",
        "src/agents/shadow_sidecar.py",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_identifies_existing_pipeline_stages():
    text = _doc_text()
    required = [
        "`startup`",
        "`scraping`",
        "`filtering`",
        "`dedupe`",
        "`ranking`",
        "`cache_filter`",
        "`details`",
        "`intelligence`",
        "`ai_evaluation_filter`",
        "`embedding_prefilter`",
        "`ai_evaluation`",
        "`resume_matching`",
        "`application_priority`",
        "`rag_export`",
        "`planning`",
        "`finalization`",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_names_adjacent_concerns():
    text = _doc_text()
    required = [
        "Prefilter relevance:",
        "LLM evaluation:",
        "Deduplication:",
        "Final application scoring:",
        "Metrics and stage logging:",
        "Trace/evidence helpers:",
        "Retry, rate-limit, cache, dedup, and ATS health checks:",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_recommends_future_hook_point():
    text = _doc_text()
    required = [
        "The recommended first future hook point is a read-only shadow sidecar after deterministic filtering/evaluation/scoring context is available",
        "immediately after the `application_priority` stage",
        "prefer the `post_final_scoring` adapter label mapped to the existing `application_priority` stage boundary",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_maps_candidate_labels():
    text = _doc_text()
    required = [
        "`post_filter_evaluation`",
        "`post_final_scoring`",
        "`pre_human_review`",
        "The current repo does not have a literal `post_filter_evaluation` runtime stage.",
        "`pre_human_review` is an adapter label only.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_counts_remain_zero():
    text = _doc_text()
    required = [
        "Live agents connected to production pipeline remain zero.",
        "Live agents allowed to automate mutations remain zero.",
        "Live production pipeline connected agents remain zero.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_blocks_mutations():
    text = _doc_text()
    required = [
        "No scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No approval mutation.",
        "No resume mutation.",
        "No execution request mutation.",
        "No execution launch request mutation.",
        "No application execution.",
        "No application submission.",
        "No application execution/submission.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_requires_flags_fallback_and_safe_failures():
    text = _doc_text()
    required = [
        "Default-off global flag required.",
        "Default-off per-agent flags required.",
        "Kill switch required.",
        "Provider calls are disabled in tests.",
        "Provider calls must not run in tests.",
        "Deterministic fallback is required.",
        "Sidecar failure must not fail deterministic pipeline by default.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_preserves_logging_metrics_and_health_checks():
    text = _doc_text()
    required = [
        "Stage-level logging must be preserved.",
        "Existing metrics flow must be preserved.",
        "Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.",
        "Existing `start_stage(...)`, `complete_stage(...)`, `update_counts(...)`, and `log_stage_metrics(...)` behavior must be preserved.",
        "Existing seen-job cache behavior in `src/utils/job_cache.py` must be preserved.",
        "Existing ATS health checks in `src/utils/ats_health.py` must be preserved.",
        "Existing HTTP retry helpers in `src/utils/http_retry.py` must be preserved.",
        "Existing LLM evaluation cache, rate-limit, and concurrency behavior in `src/ai/job_fit_evaluator.py` must be preserved.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_pipeline_integration_point_audit_sequence_and_non_goals():
    text = _doc_text()
    required = [
        "Add default-off pipeline hook module/function, not called.",
        "Add tests proving no pipeline wiring.",
        "Add one explicit opt-in call site behind feature flag.",
        "Add shadow trace storage/readback.",
        "Add dashboard/readback.",
        "Only later allow human-approved influence.",
        "Only much later guarded automation.",
        "No provider calls.",
        "No automated decisions.",
        "No mutation.",
    ]

    for phrase in required:
        assert phrase in text

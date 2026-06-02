from pathlib import Path

from src.evaluation.rag_evaluation import (
    RAG_EVALUATION_EMPTY_STATE_REASON,
    build_rag_evaluation_rows,
    build_rag_evaluation_summary,
    render_rag_evaluation_report_markdown,
    validate_rag_evaluation_payload,
    write_rag_evaluation_artifacts,
)


def test_empty_rag_evaluation_payload_validates_as_warning():
    payload = build_rag_evaluation_summary([], pipeline_run_id="run_1", owner_user_id="user_1")

    assert payload["validation_status"] == "warning"
    assert payload["reason_codes"] == [RAG_EVALUATION_EMPTY_STATE_REASON]
    assert payload["query_count"] == 0
    assert payload["retrieved_chunk_count"] == 0
    assert payload["rows"] == []


def test_rag_evaluation_summary_computes_average_retrieval_score():
    payload = build_rag_evaluation_summary(
        [
            {"query_id": "q1", "doc_id": "job_1", "score": 0.8, "rank": 1, "expected_relevant": True},
            {"query_id": "q1", "doc_id": "job_2", "score": 0.4, "rank": 2, "expected_relevant": False},
            {"query_id": "q2", "doc_id": "job_3", "score": 0.6, "rank": 1, "latency_ms": 10},
        ],
        pipeline_run_id="run_1",
    )

    assert payload["query_count"] == 2
    assert payload["retrieved_chunk_count"] == 3
    assert payload["average_retrieval_score"] == 0.6
    assert payload["top_k_hit_rate"] == 0.5
    assert payload["average_latency_ms"] == 10.0
    assert payload["validation_status"] == "passed"


def test_rag_evaluation_rows_normalize_query_and_chunk_fields():
    rows = build_rag_evaluation_rows(
        [
            {
                "question": "Which jobs mention RAG?",
                "job_id": "job_1",
                "chunk_id": "chunk_1",
                "retrieval_text": "A long retrieved chunk about RAG systems.",
                "similarity_score": "0.91",
                "position": "1",
                "retrieval_lane": "lexical",
                "insufficient_evidence": "false",
                "reason_codes": "matched_title;matched_skills",
            }
        ]
    )

    assert rows == [
        {
            "query_id": "query_1",
            "query_text": "Which jobs mention RAG?",
            "target_type": "",
            "target_id": "job_1",
            "retrieved_doc_id": "job_1",
            "retrieved_chunk_id": "chunk_1",
            "retrieved_text_preview": "A long retrieved chunk about RAG systems.",
            "retrieval_score": 0.91,
            "rank": 1,
            "source": "lexical",
            "latency_ms": None,
            "supported_decision": "",
            "expected_relevant": None,
            "relevance_hit": False,
            "missing_evidence_warning": False,
            "reason_codes": ["matched_title", "matched_skills"],
        }
    ]


def test_rag_evaluation_validation_catches_invalid_scores_and_ranks():
    validation = validate_rag_evaluation_payload(
        {
            "evaluation_version": "rag_evaluation_v1",
            "rows": [
                {"retrieval_score": 1.5, "rank": 1},
                {"retrieval_score": 0.2, "rank": -1},
            ],
        }
    )

    assert validation["validation_status"] == "failed"
    assert "invalid_retrieval_score" in validation["reason_codes"]
    assert "invalid_rank" in validation["reason_codes"]


def test_rag_evaluation_markdown_and_artifacts_render_safely(tmp_path):
    payload = build_rag_evaluation_summary(
        [{"query_id": "q1", "doc_id": "job_1", "retrieval_score": 0.7, "rank": 1}],
        pipeline_run_id="run_1",
    )
    markdown = render_rag_evaluation_report_markdown(payload)
    artifact_paths = write_rag_evaluation_artifacts(
        output_dir=tmp_path,
        rows=payload["rows"],
        pipeline_run_id="run_1",
    )

    assert "# RAG Evaluation Report" in markdown
    assert "Average retrieval score" in markdown
    assert Path(artifact_paths["summary_json"]).name == "rag_evaluation_summary.json"
    assert Path(artifact_paths["report_md"]).name == "rag_evaluation_report.md"
    assert Path(artifact_paths["summary_json"]).exists()
    assert Path(artifact_paths["report_md"]).exists()

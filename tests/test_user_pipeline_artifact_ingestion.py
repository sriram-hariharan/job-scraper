import json
import sys
import tempfile
import types
from pathlib import Path


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)

from src.app import services


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _scratch_output_dir(root: Path, owner: str, run_id: str) -> Path:
    output_dir = root / "tmp" / "pipeline_runs" / owner / run_id / "application_planning"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def test_pipeline_artifact_ingestion_preserves_planning_outputs_and_job_packets():
    records = []
    original_upsert = services.upsert_user_pipeline_artifact_postgres_payload
    owner = "user_artifacts"
    run_id = "run_artifacts"
    key = services._pipeline_artifact_ingestion_key(owner_user_id=owner, run_id=run_id)
    services._PIPELINE_ARTIFACT_INGESTED_RUN_KEYS.discard(key)

    def fake_upsert_user_pipeline_artifact_postgres_payload(*, record, **kwargs):
        records.append(dict(record))
        return {
            "ok": True,
            "artifact": {
                "artifact_id": f"artifact_{len(records)}",
                "artifact_kind": record["artifact_kind"],
                "artifact_name": record["artifact_name"],
            },
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = _scratch_output_dir(Path(tmp_dir), owner, run_id)
        _write(output_dir / "application_shortlist_by_job.csv", "job_id,title\n1,Backend Engineer\n")
        _write(output_dir / "application_execution_queue.csv", "job_id,rank\n1,1\n")
        _write(
            output_dir / "job_prioritization_recommendations.csv",
            "job_id,advisory_priority\n1,apply_now\n",
        )
        _write(output_dir / "job_prioritization_summary.json", json.dumps({"row_count": 1}))
        _write(
            output_dir / "tailoring_decision_recommendations.csv",
            "job_id,tailoring_decision\n1,light_tailoring\n",
        )
        _write(output_dir / "tailoring_decision_summary.json", json.dumps({"row_count": 1}))
        _write(
            output_dir / "operator_review_recommendations.csv",
            "job_id,operator_review_lane\n1,ready_to_apply\n",
        )
        _write(output_dir / "operator_review_summary.json", json.dumps({"row_count": 1}))
        _write(output_dir / "agentic_workflow_summary.json", json.dumps({"total_queue_jobs": 1}))
        _write(output_dir / "agentic_workflow_summary.md", "# Agentic Workflow Summary\n")
        _write(output_dir / "agentic_workflow_manifest.json", json.dumps({"workflow_name": "ApplyLens Agentic Workflow"}))
        _write(output_dir / "agentic_workflow_manifest.md", "# Agentic Workflow Manifest\n")
        _write(output_dir / "agentic_workflow_execution_plan.json", json.dumps({"execution_mode": "dry_run"}))
        _write(output_dir / "agentic_workflow_execution_plan.md", "# Agentic Workflow Execution Plan\n")
        _write(output_dir / "agentic_workflow_dry_run_result.json", json.dumps({"execution_mode": "dry_run", "executed_step_count": 0}))
        _write(output_dir / "agentic_workflow_dry_run_report.md", "# Agentic Workflow Dry-Run Report\n")
        _write(output_dir / "read_only_adapter_preflight.json", json.dumps({"execution_mode": "read_only_preflight", "executable_adapter_count": 0}))
        _write(output_dir / "read_only_adapter_preflight.md", "# Read-Only Adapter Preflight\n")
        _write(output_dir / "read_only_adapter_chain_result.json", json.dumps({"execution_mode": "manual_read_only_adapter_chain", "did_mutate_production": False}))
        _write(output_dir / "read_only_adapter_chain_report.md", "# Manual Read-Only Adapter Chain\n")
        _write(
            output_dir / "read_only_chain_artifact_generation_result.json",
            json.dumps(
                {
                    "execution_mode": "explicit_operator_read_only_chain_artifact_generation",
                    "did_run_chain": True,
                    "did_mutate_production": False,
                    "require_explicit_input": True,
                    "require_explicit_output_dir": True,
                }
            ),
        )
        _write(output_dir / "read_only_chain_artifact_generation_report.md", "# Explicit Read-Only Chain Generator\n")
        _write(
            output_dir / "dry_run_execution_simulation_result.json",
            json.dumps(
                {
                    "execution_mode": "explicit_dry_run_execution_simulation",
                    "did_simulate": True,
                    "did_execute_live": False,
                    "did_mutate_production": False,
                    "simulated_execution_plan": {"can_execute_live": False},
                    "simulated_mutation_proposals": [],
                    "safety_flags": {"allow_db_write": False},
                    "blocked_live_execution_reasons": [
                        "queue_mutation_blocked",
                        "application_submission_blocked",
                    ],
                }
            ),
        )
        _write(output_dir / "dry_run_execution_simulation_report.md", "# Dry-Run Execution Simulation\n")
        _write(output_dir / "agentic_workflow_verification.json", json.dumps({"validation_status": "passed"}))
        _write(output_dir / "rag_evaluation_summary.json", json.dumps({"evaluation_version": "rag_evaluation_v1", "validation_status": "warning", "rows": []}))
        _write(output_dir / "rag_evaluation_report.md", "# RAG Evaluation Report\n")
        _write(output_dir / "best_resume_variant_by_job.csv", "job_id,resume\n1,resume.pdf\n")
        _write(output_dir / "current_run_job_corpus.jsonl", json.dumps({"job_id": "1"}) + "\n")
        _write(
            output_dir / "role_title_filter_audit.csv",
            "job_company,job_title,title_filter_decision\nAcme,Backend Engineer,pass\n",
        )
        _write(
            output_dir / "source_health_report.csv",
            "source,company,scraped_jobs,final_corpus_jobs\ngreenhouse,scaleai,2,1\n",
        )
        _write(output_dir / "live_pipeline_run.log", "pipeline log\n")
        _write(output_dir / "live_pipeline_status.json", json.dumps({"status": "succeeded"}))
        _write(output_dir / "job_packets" / "backend_engineer.json", json.dumps({"job_id": "1"}))
        _write(output_dir / "job_packets" / "backend_engineer_tailoring.json", json.dumps({"edits": []}))
        _write(output_dir / "job_packets" / "backend_engineer_tailoring_llm.json", json.dumps({"choices": []}))
        _write(output_dir / "job_packets" / "backend_engineer.md", "# Packet\n")

        services.upsert_user_pipeline_artifact_postgres_payload = (
            fake_upsert_user_pipeline_artifact_postgres_payload
        )
        try:
            result = services._ingest_pipeline_run_artifacts_to_postgres(
                owner_user_id=owner,
                run_id=run_id,
                output_dir=str(output_dir),
                status_payload={"status": "succeeded"},
            )
        finally:
            services.upsert_user_pipeline_artifact_postgres_payload = original_upsert
            services._PIPELINE_ARTIFACT_INGESTED_RUN_KEYS.discard(key)

    artifact_names = {record["artifact_name"] for record in records}
    artifact_kinds = {record["artifact_kind"] for record in records}

    assert result["ok"] is True
    assert result["attempted"] is True
    assert result["ingested_count"] == 37
    assert result["skipped_count"] == 0
    assert result["error_count"] == 0
    assert "application_shortlist_by_job.csv" in artifact_names
    assert "application_execution_queue.csv" in artifact_names
    assert "job_prioritization_recommendations.csv" in artifact_names
    assert "job_prioritization_summary.json" in artifact_names
    assert "tailoring_decision_recommendations.csv" in artifact_names
    assert "tailoring_decision_summary.json" in artifact_names
    assert "operator_review_recommendations.csv" in artifact_names
    assert "operator_review_summary.json" in artifact_names
    assert "agentic_workflow_summary.json" in artifact_names
    assert "agentic_workflow_summary.md" in artifact_names
    assert "agentic_workflow_manifest.json" in artifact_names
    assert "agentic_workflow_manifest.md" in artifact_names
    assert "agentic_workflow_execution_plan.json" in artifact_names
    assert "agentic_workflow_execution_plan.md" in artifact_names
    assert "agentic_workflow_dry_run_result.json" in artifact_names
    assert "agentic_workflow_dry_run_report.md" in artifact_names
    assert "read_only_adapter_preflight.json" in artifact_names
    assert "read_only_adapter_preflight.md" in artifact_names
    assert "read_only_adapter_chain_result.json" in artifact_names
    assert "read_only_adapter_chain_report.md" in artifact_names
    assert "read_only_chain_artifact_generation_result.json" in artifact_names
    assert "read_only_chain_artifact_generation_report.md" in artifact_names
    assert "dry_run_execution_simulation_result.json" in artifact_names
    assert "dry_run_execution_simulation_report.md" in artifact_names
    assert "agentic_workflow_verification.json" in artifact_names
    assert "rag_evaluation_summary.json" in artifact_names
    assert "rag_evaluation_report.md" in artifact_names
    assert "best_resume_variant_by_job.csv" in artifact_names
    assert "current_run_job_corpus.jsonl" in artifact_names
    assert "role_title_filter_audit.csv" in artifact_names
    assert "source_health_report.csv" in artifact_names
    assert "live_pipeline_run.log" in artifact_names
    assert "live_pipeline_status.json" in artifact_names
    assert "job_packets/backend_engineer.json" in artifact_names
    assert "job_packets/backend_engineer_tailoring.json" in artifact_names
    assert "job_packets/backend_engineer_tailoring_llm.json" in artifact_names
    assert "job_packets/backend_engineer.md" in artifact_names
    assert "application_shortlist_by_job" in artifact_kinds
    assert "application_execution_queue" in artifact_kinds
    assert "job_prioritization_recommendations" in artifact_kinds
    assert "job_prioritization_summary" in artifact_kinds
    assert "tailoring_decision_recommendations" in artifact_kinds
    assert "tailoring_decision_summary" in artifact_kinds
    assert "operator_review_recommendations" in artifact_kinds
    assert "operator_review_summary" in artifact_kinds
    assert "agentic_workflow_summary_json" in artifact_kinds
    assert "agentic_workflow_summary_md" in artifact_kinds
    assert "agentic_workflow_manifest_json" in artifact_kinds
    assert "agentic_workflow_manifest_md" in artifact_kinds
    assert "agentic_workflow_execution_plan_json" in artifact_kinds
    assert "agentic_workflow_execution_plan_md" in artifact_kinds
    assert "agentic_workflow_dry_run_result_json" in artifact_kinds
    assert "agentic_workflow_dry_run_report_md" in artifact_kinds
    assert "read_only_adapter_preflight_json" in artifact_kinds
    assert "read_only_adapter_preflight_md" in artifact_kinds
    assert "read_only_adapter_chain_result_json" in artifact_kinds
    assert "read_only_adapter_chain_report_md" in artifact_kinds
    assert "read_only_chain_artifact_generation_result_json" in artifact_kinds
    assert "read_only_chain_artifact_generation_report_md" in artifact_kinds
    assert "dry_run_execution_simulation_result_json" in artifact_kinds
    assert "dry_run_execution_simulation_report_md" in artifact_kinds
    assert "agentic_workflow_verification_json" in artifact_kinds
    assert "rag_evaluation_summary_json" in artifact_kinds
    assert "rag_evaluation_report_md" in artifact_kinds
    assert "best_resume_variant_by_job" in artifact_kinds
    assert "current_run_job_corpus" in artifact_kinds
    assert "role_title_filter_audit" in artifact_kinds
    assert "source_health_report" in artifact_kinds
    assert "job_packet_json" in artifact_kinds
    assert "job_packet_tailoring_json" in artifact_kinds
    assert "job_packet_tailoring_llm_json" in artifact_kinds
    assert "job_packet_markdown" in artifact_kinds
    assert result["manifest_written"] is True
    assert records[-1]["artifact_kind"] == "artifact_ingestion_manifest"
    assert set(result["ingested_artifact_names"]) == artifact_names - {"artifact_ingestion_manifest.json"}


def test_scratch_cleanup_runs_after_artifact_ingestion_records_planning_results():
    records = []
    original_upsert = services.upsert_user_pipeline_artifact_postgres_payload
    owner = "user_cleanup"
    run_id = "run_cleanup"
    key = services._pipeline_artifact_ingestion_key(owner_user_id=owner, run_id=run_id)
    services._PIPELINE_ARTIFACT_INGESTED_RUN_KEYS.discard(key)

    def fake_upsert_user_pipeline_artifact_postgres_payload(*, record, **kwargs):
        records.append(dict(record))
        return {
            "ok": True,
            "artifact": {
                "artifact_id": f"artifact_{len(records)}",
                "artifact_kind": record["artifact_kind"],
                "artifact_name": record["artifact_name"],
            },
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = _scratch_output_dir(Path(tmp_dir), owner, run_id)
        run_root = output_dir.parent
        _write(output_dir / "application_execution_queue.csv", "job_id,rank\n1,1\n")
        _write(output_dir / "live_pipeline_status.json", json.dumps({"status": "succeeded"}))

        services.upsert_user_pipeline_artifact_postgres_payload = (
            fake_upsert_user_pipeline_artifact_postgres_payload
        )
        try:
            ingestion = services._ingest_pipeline_run_artifacts_to_postgres(
                owner_user_id=owner,
                run_id=run_id,
                output_dir=str(output_dir),
                status_payload={"status": "succeeded"},
            )
        finally:
            services.upsert_user_pipeline_artifact_postgres_payload = original_upsert
            services._PIPELINE_ARTIFACT_INGESTED_RUN_KEYS.discard(key)

        cleanup = services._pipeline_scratch_cleanup_payload(
            owner_user_id=owner,
            run_id=run_id,
            output_dir=str(output_dir),
            artifact_ingestion=ingestion,
        )

        assert ingestion["ok"] is True
        assert "application_execution_queue.csv" in ingestion["ingested_artifact_names"]
        assert records[-1]["artifact_kind"] == "artifact_ingestion_manifest"
        assert cleanup["scratch_deleted"] is True
        assert not run_root.exists()


def test_dry_run_execution_simulation_read_model_missing_is_safe_empty():
    simulation = services._dry_run_execution_simulation_from_artifacts([])
    mock = services._operator_approval_mock_from_simulation(simulation)

    assert simulation["present"] is False
    assert simulation["available"] is False
    assert simulation["empty_state"] == "No dry-run execution simulation artifacts recorded for this run yet."
    assert simulation["validation_status"] == "missing"
    assert mock["present"] is False
    assert mock["mock_only"] is True
    assert mock["approval_enabled"] is False
    assert mock["approval_storage_enabled"] is False
    assert mock["mutation_execution_enabled"] is False
    assert mock["can_execute_live"] is False


def test_dry_run_execution_simulation_read_model_and_operator_approval_mock_from_artifacts():
    result = {
        "execution_mode": "explicit_dry_run_execution_simulation",
        "input_artifact_dir": "/tmp/chain",
        "output_dir": "/tmp/sim",
        "did_simulate": True,
        "did_execute_live": False,
        "did_mutate_production": False,
        "context": {
            "require_explicit_input_artifact_dir": True,
            "require_explicit_output_dir": True,
        },
        "chain_artifact_summary": {"input_row_count": 4},
        "generator_artifact_summary": {"validation_status": "passed"},
        "simulated_execution_plan": {
            "can_execute_live": False,
            "requires_operator_approval": True,
            "requires_audit_ledger": True,
            "requires_idempotency_key": True,
            "requires_execution_lock": True,
            "requires_rollback_plan": True,
        },
        "simulated_mutation_proposals": [
            {
                "proposal_mode": "simulated_non_executable",
                "mutation_type": "operator_note",
                "can_execute_live": False,
                "requires_approval": True,
                "blocked_by_default": True,
            }
        ],
        "blocked_live_execution_reasons": [
            "queue_mutation_blocked",
            "application_submission_blocked",
        ],
        "safety_flags": {
            "allow_db_write": False,
            "allow_live_pipeline_wiring": False,
            "allow_application_submission": False,
            "allow_queue_action_update": False,
            "allow_packet_update": False,
            "allow_tailoring_generation_update": False,
            "allow_scoring_update": False,
            "allow_ranking_update": False,
            "allow_scheduler_execution": False,
            "did_execute_live": False,
            "did_mutate_production": False,
        },
        "reason_codes": [],
    }
    rows = [
        {
            "artifact_name": "dry_run_execution_simulation_result.json",
            "content_json": result,
            "content_text": "",
        },
        {
            "artifact_name": "dry_run_execution_simulation_report.md",
            "content_json": None,
            "content_text": "# Dry-Run Execution Simulation\n",
        },
    ]

    simulation = services._dry_run_execution_simulation_from_artifacts(rows)
    mock = services._operator_approval_mock_from_simulation(simulation)

    assert simulation["present"] is True
    assert simulation["execution_mode"] == "explicit_dry_run_execution_simulation"
    assert simulation["validation_status"] == "passed"
    assert simulation["did_simulate"] is True
    assert simulation["did_execute_live"] is False
    assert simulation["did_mutate_production"] is False
    assert simulation["chain_artifact_summary"]["input_row_count"] == 4
    assert simulation["report_markdown"] == "# Dry-Run Execution Simulation\n"
    assert mock["present"] is True
    assert mock["mock_only"] is True
    assert mock["approval_enabled"] is False
    assert mock["approval_storage_enabled"] is False
    assert mock["mutation_execution_enabled"] is False
    assert mock["can_execute_live"] is False
    assert "operator approval" in mock["required_future_gates"]
    assert "DB write" in mock["blocked_actions"]
    assert mock["simulated_proposal_count"] == 1
    assert mock["simulated_proposal_types"] == ["operator_note"]

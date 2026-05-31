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
    assert result["ingested_count"] == 14
    assert result["skipped_count"] == 0
    assert result["error_count"] == 0
    assert "application_shortlist_by_job.csv" in artifact_names
    assert "application_execution_queue.csv" in artifact_names
    assert "job_prioritization_recommendations.csv" in artifact_names
    assert "job_prioritization_summary.json" in artifact_names
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

import json

from src.app import services


FUNNEL_HEADER = (
    "source,company,scraped_jobs,title_pass_jobs,title_reject_jobs,"
    "location_pass_jobs,location_reject_jobs,freshness_pass_jobs,not_recent_jobs,"
    "missing_timestamp_jobs,final_corpus_jobs,final_display_jobs\n"
)


def test_source_yield_aggregates_union_accounts_funnel_health_and_fallbacks():
    health = FUNNEL_HEADER + "\n".join(
        [
            "USAJobs,account-a,100,80,20,60,20,50,7,3,10,10",
            "usajobs,account-b,20,15,5,12,3,10,1,1,5,5",
            "lever,board-a,30,25,5,20,5,15,4,1,8,8",
        ]
    )
    acquisition = json.dumps(
        {
            "acquisition_metrics": [
                {
                    "source": "USAJOBS",
                    "acquisition_status": "SUCCESS",
                    "raw_job_count": 70,
                    "normalized_job_count": 68,
                    "page_count": 2,
                    "request_count": 2,
                    "timestamp_present_count": 65,
                    "timestamp_missing_count": 3,
                },
                {
                    "source": "usajobs",
                    "acquisition_status": "PARTIAL",
                    "raw_job_count": 50,
                    "normalized_job_count": 48,
                    "page_count": 1,
                    "request_count": 2,
                    "retry_count": 1,
                    "partial_result_count": 1,
                },
                {"source": "ashby", "acquisition_status": "FAILED", "request_count": 1},
                "malformed-row",
            ],
            "source_stage_metrics": [
                {"source": "usajobs", "final_retained_job_count": 99},
                {"source": "ashby", "final_retained_job_count": 3},
            ],
        }
    )
    corpus = "\n".join(
        [
            json.dumps({"source": "greenhouse", "job_id": "one"}),
            "not-json",
            json.dumps({"source": "greenhouse", "job_id": "two"}),
            json.dumps({"source": "ashby", "job_id": "authoritative-stage-wins"}),
        ]
    )

    payload = services._source_yield_payload(
        run_id="run-owner-1",
        source_health_report_text=health,
        source_acquisition_metrics_text=acquisition,
        current_run_job_corpus_text=corpus,
    )

    assert payload["available"] is True
    assert payload["run_id"] == "run-owner-1"
    assert payload["generated_from"] == {
        "source_health_report": True,
        "source_acquisition_metrics": True,
        "current_run_job_corpus": True,
    }
    assert [row["source"] for row in payload["sources"]] == [
        "usajobs",
        "lever",
        "ashby",
        "greenhouse",
    ]
    usajobs = payload["sources"][0]
    assert usajobs["accounts_queried"] == 2
    assert usajobs["scraped_jobs"] == 120
    assert usajobs["final_display_jobs"] == 15
    assert usajobs["yield_percent"] == 12.5
    assert usajobs["raw_job_count"] == 120
    assert usajobs["acquisition_status_counts"] == {
        "SUCCESS": 1,
        "PARTIAL": 1,
        "EMPTY": 0,
        "FAILED": 0,
    }
    assert payload["sources"][2]["final_display_jobs"] == 3
    assert payload["sources"][3]["final_display_jobs"] == 2
    assert payload["totals"] == {
        "source_count": 4,
        "accounts_queried": 3,
        "scraped_jobs": 150,
        "title_pass_jobs": 120,
        "location_pass_jobs": 92,
        "freshness_pass_jobs": 75,
        "final_corpus_jobs": 28,
        "final_display_jobs": 28,
    }


def test_source_yield_is_unavailable_without_primary_artifacts_and_tolerates_bad_values():
    missing = services._source_yield_payload(
        current_run_job_corpus_text=json.dumps({"source": "greenhouse"}),
    )
    assert missing["available"] is False
    assert missing["sources"] == []
    assert missing["totals"]["source_count"] == 0

    malformed = services._source_yield_payload(
        source_health_report_text=FUNNEL_HEADER + "lever,board,not-a-number,-3,,,,,,,,\n",
        source_acquisition_metrics_text="{not-json",
    )
    assert malformed["available"] is True
    assert malformed["sources"][0]["scraped_jobs"] == 0
    assert malformed["sources"][0]["title_pass_jobs"] == 0
    assert malformed["sources"][0]["yield_percent"] == 0.0


def test_run_scoped_filesystem_context_reuses_source_artifact_texts(tmp_path):
    (tmp_path / "best_resume_variant_by_job.csv").write_text("job_id,resume\n1,resume.pdf\n", encoding="utf-8")
    (tmp_path / "source_health_report.csv").write_text(FUNNEL_HEADER, encoding="utf-8")
    (tmp_path / "source_acquisition_metrics.json").write_text(
        json.dumps({"acquisition_metrics": [], "source_stage_metrics": []}),
        encoding="utf-8",
    )
    run = {
        "run_id": "run-fs",
        "status": "succeeded",
        "status_json": {"output_dir": str(tmp_path)},
    }

    context = services._latest_user_pipeline_filesystem_context(
        owner_user_id="owner-fs",
        run=run,
    )

    assert context["source_health_report_text"] == FUNNEL_HEADER
    assert json.loads(context["source_acquisition_metrics_text"])["acquisition_metrics"] == []


def test_owner_scoped_postgres_context_reuses_ingested_source_artifacts(monkeypatch):
    owner = "owner-postgres"
    run_id = "run-postgres"
    health = FUNNEL_HEADER + "lever,board,1,1,0,1,0,1,0,0,1,1\n"
    acquisition = json.dumps({"acquisition_metrics": [], "source_stage_metrics": []})

    def get_runs(**kwargs):
        assert kwargs["owner_user_id"] == owner
        assert kwargs["status"] == "succeeded"
        return {"rows": [{"owner_user_id": owner, "run_id": run_id, "status": "succeeded", "final_job_count": 1}]}

    def get_artifacts(**kwargs):
        assert kwargs["owner_user_id"] == owner
        assert kwargs["run_id"] == run_id
        return {
            "rows": [
                {"artifact_name": "best_resume_variant_by_job.csv", "content_text": "job_id,resume\n1,resume.pdf\n"},
                {"artifact_name": "source_health_report.csv", "content_text": health},
                {"artifact_name": "source_acquisition_metrics.json", "content_text": acquisition},
            ]
        }

    monkeypatch.setattr(services, "get_user_pipeline_runs_postgres_payload", get_runs)
    monkeypatch.setattr(services, "get_user_pipeline_artifacts_postgres_payload", get_artifacts)

    context = services._latest_user_pipeline_artifact_context(owner_user_id=owner)

    assert context["artifact_source"] == "postgres:user_pipeline_artifacts"
    assert context["owner_user_id"] == owner
    assert context["run_id"] == run_id
    assert context["source_health_report_text"] == health
    assert context["source_acquisition_metrics_text"] == acquisition

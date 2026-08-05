import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from src.app import services


ATTRIBUTION = {
    "provider_attribution_required": True,
    "provider_attribution_label": "Himalayas",
    "provider_attribution_url": "https://himalayas.app/source",
}


def _corpus_record(**overrides):
    return {
        "doc_id": "job-1",
        "job_url": "https://jobs.example/job-1",
        "company": "Acme",
        "title": "Backend Engineer",
        **ATTRIBUTION,
        **overrides,
    }


def test_filesystem_corpus_overlay_carries_attribution_with_defaults(tmp_path):
    attributed_path = tmp_path / "attributed.jsonl"
    attributed_path.write_text(
        json.dumps(_corpus_record()) + "\n",
        encoding="utf-8",
    )
    plain_path = tmp_path / "plain.jsonl"
    plain_path.write_text(
        json.dumps(_corpus_record(**{
            "doc_id": "job-2",
            "job_url": "https://jobs.example/job-2",
            "provider_attribution_required": False,
            "provider_attribution_label": "",
            "provider_attribution_url": "",
        })) + "\n",
        encoding="utf-8",
    )
    services._JOB_METADATA_OVERLAY_CACHE.clear()

    attributed = services._load_job_metadata_overlay_from_corpus(attributed_path)
    attributed_row = services._overlay_job_metadata(
        [{"job_doc_id": "job-1", "job_url": "https://jobs.example/job-1"}],
        job_corpus=attributed_path,
    )[0]
    plain_row = services._overlay_job_metadata(
        [{"job_doc_id": "job-2", "job_url": "https://jobs.example/job-2"}],
        job_corpus=plain_path,
    )[0]

    assert any(row == ATTRIBUTION for row in (
        {key: value[key] for key in ATTRIBUTION}
        for value in attributed.values()
    ))
    assert {key: attributed_row[key] for key in ATTRIBUTION} == ATTRIBUTION
    assert plain_row["provider_attribution_required"] is False
    assert plain_row["provider_attribution_label"] == ""
    assert plain_row["provider_attribution_url"] == ""


def test_jsonl_and_map_overlays_enforce_boolean_and_text_bounds():
    record = _corpus_record(
        provider_attribution_required="true",
        provider_attribution_label="  " + "H" * 250 + "  ",
        provider_attribution_url="  https://himalayas.app/" + "x" * 2200 + "  ",
    )
    overlay_by_key = services._job_metadata_overlay_from_jsonl_text(
        json.dumps(record)
    )
    overlay = next(iter(overlay_by_key.values()))
    row = services._overlay_job_metadata_from_map(
        [{"job_doc_id": "job-1", "job_url": "https://jobs.example/job-1"}],
        overlay_by_key,
    )[0]

    assert row["provider_attribution_required"] is False
    assert row["provider_attribution_label"] == "H" * 200
    assert len(row["provider_attribution_url"]) == 2048
    assert row["job_url"] == "https://jobs.example/job-1"

    for unsafe_truthy in ("1", 1):
        assert services._provider_attribution_fields(
            {"provider_attribution_required": unsafe_truthy}
        )["provider_attribution_required"] is False


def test_status_payload_top_queue_carries_attribution_without_url_leakage(
    monkeypatch,
    tmp_path,
):
    queue_row = {
        "queue_rank": "1",
        "job_doc_id": "job-1",
        "job_url": "https://jobs.example/job-1",
        "job_company": "Acme",
        "job_title": "Backend Engineer",
        "action": "APPLY",
        "winner_score": "0.9",
    }
    artifact_context = {
        "best_rows": [],
        "shortlist_rows": [],
        "queue_rows": [queue_row],
        "manifest_rows": [],
        "job_prioritization_rows": [],
        "tailoring_decision_rows": [],
        "operator_review_rows": [],
        "agentic_workflow_summary": {},
        "agentic_workflow_verification": {},
        "current_run_job_corpus_text": json.dumps(_corpus_record()),
        "job_corpus_rows": 1,
        "output_dir": str(tmp_path),
        "artifact_source": "test",
        "run_id": "run-1",
        "owner_user_id": "owner-1",
    }
    fake_job_app = SimpleNamespace(
        OPERATOR_DECISION_OVERLAY_FIELDS=(),
        _count_undecided_review_rows=lambda rows: {},
        _parse_float=lambda value: float(value or 0),
        _decision_row_key=lambda row: "",
        _normalize_text=lambda value: str(value or "").strip().lower(),
        _load_latest_decision_overlay=lambda: {},
    )

    monkeypatch.setattr(services, "_job_app", lambda: fake_job_app)
    monkeypatch.setattr(
        services,
        "_latest_user_pipeline_artifact_context",
        lambda **kwargs: artifact_context,
    )
    monkeypatch.setattr(
        services,
        "_build_job_index_from_planning_rows",
        lambda *args, **kwargs: [dict(queue_row)],
    )
    monkeypatch.setattr(
        services, "_load_latest_operator_decision_rows", lambda **kwargs: []
    )
    monkeypatch.setattr(
        services,
        "_load_latest_application_action_overlay",
        lambda **kwargs: {},
    )

    row = services.status_payload(
        output_dir=tmp_path,
        job_corpus=tmp_path / "unused.jsonl",
        owner_user_id="owner-1",
    )["top_queue_rows"][0]

    assert {key: row[key] for key in ATTRIBUTION} == ATTRIBUTION
    assert row["job_url"] == "https://jobs.example/job-1"
    assert row["job_doc_id"] == "job-1"
    assert row.get("application_label") != ATTRIBUTION["provider_attribution_url"]


def _function_block(source, name, next_name):
    start = source.index(f"function {name}(")
    end = source.index(f"function {next_name}(", start)
    return source[start:end]


def test_ui_renders_only_complete_safe_attribution_and_preserves_job_urls():
    source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    script = "\n".join(
        [
            _function_block(source, "escapeHtml", "truncateText"),
            _function_block(
                source, "validHttpsAttributionUrl", "buildProviderAttributionHtml"
            ),
            _function_block(
                source, "buildProviderAttributionHtml", "buildJobTitleCellHtml"
            ),
            _function_block(
                source, "buildJobTitleCellHtml", "formatAdvisoryPriorityLabel"
            ),
            "const base = {provider_attribution_required: true, provider_attribution_label: '<Himalayas & Co>', provider_attribution_url: 'https://himalayas.app/source', job_title: 'Engineer', job_url: 'https://jobs.example/job-1', job_doc_id: ''};",
            "const cases = [base, {...base, provider_attribution_required: false}, {...base, provider_attribution_label: ''}, {...base, provider_attribution_url: ''}, {...base, provider_attribution_url: 'http://himalayas.app'}, {...base, provider_attribution_url: 'javascript:alert(1)'}, {...base, provider_attribution_url: '/source'}, {...base, provider_attribution_url: 'not a url'}];",
            "console.log(JSON.stringify({outputs: cases.map(buildProviderAttributionHtml), title: buildJobTitleCellHtml(base)}));",
        ]
    )
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    valid = payload["outputs"][0]

    assert "Source:" in valid
    assert "&lt;Himalayas &amp; Co&gt;" in valid
    assert 'target="_blank"' in valid
    assert 'rel="noopener noreferrer"' in valid
    assert payload["outputs"][1:] == [""] * 7
    assert 'href="https://jobs.example/job-1"' in payload["title"]
    assert 'href="https://himalayas.app/source"' in payload["title"]

    apply_start = source.index("function buildApplicationButtonHtml(")
    apply_end = source.index("function buildQueueJobSummaryHtml(", apply_start)
    apply_block = source[apply_start:apply_end]
    assert "provider_attribution" not in apply_block
